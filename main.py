"""
LinkedIn → Gmail Job Application Automation Pipeline
=====================================================
Run: python main.py
"""

import time
import logging
from config import Config
from linkedin_scraper import LinkedInScraper
from gmail_sender import GmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


def main():
    cfg = Config()

    log.info("=" * 60)
    log.info("  LinkedIn -> Gmail Job Application Bot")
    log.info("=" * 60)

    log.info("STEP 1: Logging into LinkedIn...")
    scraper = LinkedInScraper(
        email=cfg.LINKEDIN_EMAIL,
        password=cfg.LINKEDIN_PASSWORD,
        headless=cfg.HEADLESS,
    )

    try:
        scraper.login()
        log.info("LinkedIn login successful.")

        log.info("STEP 2: Searching posts (last %s hours)...", cfg.HOURS_BACK)
        recruiters = scraper.search_posts(
            keywords=cfg.SEARCH_KEYWORDS,
            hours_back=cfg.HOURS_BACK,
            max_posts=cfg.MAX_POSTS,
        )
        log.info("Found %d recruiter contact(s).", len(recruiters))
    finally:
        scraper.close()

    if not recruiters:
        log.warning("No recruiter emails found. Exiting.")
        return

    log.info("STEP 3: Authenticating Gmail...")
    sender = GmailSender(
        credentials_file=cfg.GMAIL_CREDENTIALS_FILE,
        token_file=cfg.GMAIL_TOKEN_FILE,
    )
    sender.authenticate()
    log.info("Gmail authenticated.")

    log.info("STEP 4: Sending %d application email(s)...", len(recruiters))
    results = {"sent": 0, "failed": 0}

    for rec in recruiters:
        log.info("  -> Sending to %s (%s)...", rec["email"], rec["name"])
        success = sender.send_application(
            to_email=rec["email"],
            recruiter_name=rec.get("name", "Hiring Manager"),
            job_title=rec.get("job_title", cfg.SEARCH_KEYWORDS[0]),
            company=rec.get("company", "your company"),
            candidate=cfg.CANDIDATE,
            resume_path=cfg.RESUME_PATH,
            subject_template=cfg.EMAIL_SUBJECT_TEMPLATE,
            body_template=cfg.EMAIL_BODY_TEMPLATE,
        )
        if success:
            results["sent"] += 1
            log.info("    OK Sent successfully.")
        else:
            results["failed"] += 1
            log.error("    FAIL Failed to send.")

        time.sleep(cfg.EMAIL_DELAY_SECONDS)

    log.info("=" * 60)
    log.info("  Done. Sent: %d | Failed: %d", results["sent"], results["failed"])
    log.info("=" * 60)


if __name__ == "__main__":
    main()
