"""
linkedin_scraper.py
====================
Logs into LinkedIn and scrapes Posts section for recruiter emails.

Requires:
    pip install playwright
    playwright install chromium
"""

import re
import time
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)

# Regex to find email addresses in post text
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com"

    def __init__(self, email: str, password: str, headless: bool = True):
        self.email    = email
        self.password = password
        self.headless = headless
        self._pw      = None
        self._browser = None
        self._page    = None

    # ── Browser lifecycle ──────────────────────────────────────────
    def _start(self):
        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        self._page = ctx.new_page()
        # Hide webdriver flag
        self._page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

    def close(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    # ── Step 1: Login ──────────────────────────────────────────────
    def login(self):
        self._start()
        page = self._page
        log.info("  Navigating to LinkedIn login page...")
        page.goto(f"{self.BASE_URL}/login", wait_until="networkidle")
        time.sleep(1)

        page.fill("#username", self.email)
        time.sleep(0.5)
        page.fill("#password", self.password)
        time.sleep(0.5)
        page.click("[data-litms-control-urn='login-submit']")

        try:
            page.wait_for_url("**/feed**", timeout=15_000)
            log.info("  Logged in successfully.")
        except PWTimeout:
            # May require CAPTCHA / 2FA — handle manually if headless=False
            log.warning("  Login redirect not detected. May need CAPTCHA / 2FA.")
            if not self.headless:
                log.info("  Browser visible — complete 2FA manually then press Enter.")
                input("  Press Enter after completing login in the browser...")
            else:
                raise RuntimeError("LinkedIn login failed (try headless=False to debug).")

    # ── Step 2: Search Posts ───────────────────────────────────────
    def search_posts(
        self,
        keywords: list[str],
        hours_back: int = 24,
        max_posts: int = 50,
    ) -> list[dict]:
        """
        Search LinkedIn Posts for all keywords and return a list of dicts:
          { name, email, company, job_title, post_url }
        """
        query = " ".join(f'"{k}"' for k in keywords)
        search_url = (
            f"{self.BASE_URL}/search/results/content/"
            f"?keywords={query.replace(' ', '%20')}"
            f"&datePosted=past-24h"
            f"&sortBy=date_posted"
        )
        log.info("  Search URL: %s", search_url)
        self._page.goto(search_url, wait_until="networkidle")
        time.sleep(2)

        cutoff = datetime.now() - timedelta(hours=hours_back)
        recruiters = []
        seen_emails = set()
        posts_checked = 0

        while posts_checked < max_posts:
            # Collect all post cards currently on page
            cards = self._page.query_selector_all(
                "div.feed-shared-update-v2, div[data-urn]"
            )
            log.info("  Found %d post cards on page.", len(cards))

            for card in cards:
                if posts_checked >= max_posts:
                    break
                posts_checked += 1

                try:
                    result = self._parse_card(card, cutoff)
                    if result:
                        for email in result["emails"]:
                            if email not in seen_emails:
                                seen_emails.add(email)
                                recruiters.append({
                                    "name":      result["name"],
                                    "email":     email,
                                    "company":   result["company"],
                                    "job_title": result["job_title"],
                                    "post_url":  result["post_url"],
                                })
                                log.info(
                                    "    ✓ Found: %s <%s> @ %s",
                                    result["name"], email, result["company"],
                                )
                except Exception as e:
                    log.debug("  Error parsing card: %s", e)

            # Scroll down to load more posts
            prev_height = self._page.evaluate("document.body.scrollHeight")
            self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            new_height = self._page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                log.info("  Reached end of results.")
                break

        return recruiters

    # ── Card parser ────────────────────────────────────────────────
    def _parse_card(self, card, cutoff: datetime) -> dict | None:
        # Get post text
        try:
            text_el = card.query_selector(
                "span.break-words, div.feed-shared-update-v2__description"
            )
            text = text_el.inner_text() if text_el else ""
        except Exception:
            text = ""

        # Must contain at least one keyword
        if not text:
            return None

        # Extract emails from post text
        emails = EMAIL_RE.findall(text)
        # Filter out common non-recruiter emails
        emails = [
            e for e in emails
            if not any(
                skip in e.lower()
                for skip in ["noreply", "no-reply", "support@linkedin", "linkedin.com"]
            )
        ]
        if not emails:
            return None

        # Author name
        try:
            name_el = card.query_selector(
                "span.feed-shared-actor__name, "
                "span.update-components-actor__name"
            )
            name = name_el.inner_text().strip() if name_el else "Unknown"
        except Exception:
            name = "Unknown"

        # Company / headline
        try:
            headline_el = card.query_selector(
                "span.feed-shared-actor__description, "
                "span.update-components-actor__description"
            )
            headline = headline_el.inner_text().strip() if headline_el else ""
        except Exception:
            headline = ""

        # Try to extract job title from post text
        job_title = _extract_job_title(text)

        # Post URL
        try:
            link_el = card.query_selector("a[href*='/posts/'], a[href*='/feed/update/']")
            post_url = link_el.get_attribute("href") if link_el else ""
        except Exception:
            post_url = ""

        return {
            "name":      name,
            "company":   headline,
            "job_title": job_title,
            "emails":    emails,
            "post_url":  post_url,
        }


def _extract_job_title(text: str) -> str:
    """Heuristic: look for common patterns like 'Role: X' or 'Position: X'."""
    patterns = [
        r"(?:role|position|title|opening|hiring for)[:\s]+([A-Za-z ]+Developer[A-Za-z ]*)",
        r"(?:role|position|title|opening|hiring for)[:\s]+([A-Za-z ]+Engineer[A-Za-z ]*)",
        r"(Java\s+(?:Developer|Engineer|Architect)[A-Za-z\s]*)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Java Developer – Contract"
