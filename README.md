# LinkedIn → Gmail Job Application Bot — Setup Guide

## Project Structure

```
linkedin_gmail_bot/
├── main.py              ← Run this to start the pipeline
├── config.py            ← All your settings go here
├── linkedin_scraper.py  ← LinkedIn login + post scraper (Playwright)
├── gmail_sender.py      ← Gmail API email sender
├── requirements.txt     ← Python dependencies
├── credentials.json     ← Download from Google Cloud Console (Step 3 below)
├── token.json           ← Auto-created after first Gmail auth
└── resume.pdf           ← Your resume (put it here)
```

---

## STEP 1 — Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## STEP 2 — Edit config.py

Open `config.py` and fill in:

| Field | What to set |
|---|---|
| `LINKEDIN_EMAIL` | Your LinkedIn login email |
| `LINKEDIN_PASSWORD` | Your LinkedIn password |
| `SEARCH_KEYWORDS` | e.g. `["Java Developer", "Contract"]` |
| `HOURS_BACK` | `24` = last 24 hours |
| `GMAIL_CREDENTIALS_FILE` | `"credentials.json"` (downloaded in Step 3) |
| `CANDIDATE` dict | Your name, phone, LinkedIn, visa status, rate |
| `RESUME_PATH` | `"resume.pdf"` — place your resume in the folder |

---

## STEP 3 — Set up Gmail API (one-time)

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Go to **APIs & Services → Library**
4. Search for **Gmail API** → Enable it
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → OAuth 2.0 Client ID**
7. Application type: **Desktop app**
8. Download the JSON file → rename it to `credentials.json`
9. Place it in the `linkedin_gmail_bot/` folder

> First run will open your browser to authorize Gmail access.
> After that, `token.json` is saved and you won't need to authorize again.

---

## STEP 4 — Add your resume

Place your resume PDF in the `linkedin_gmail_bot/` folder as `resume.pdf`
(or update `RESUME_PATH` in config.py to point to your file).

---

## STEP 5 — Run the bot

```bash
python main.py
```

Output is logged to both the terminal and `pipeline.log`.

---

## Tips & Troubleshooting

### LinkedIn blocks the bot / CAPTCHA
- Set `HEADLESS = False` in config.py — this shows the browser window
- Complete the CAPTCHA/2FA manually, then the script continues
- Use a **secondary LinkedIn account** to reduce ban risk
- Keep `MAX_POSTS` low (20–30) and add delays

### No recruiter emails found
- Not all recruiters post their email in the post body
- Try broader keywords like just `"Java"` or `"Contract"`
- Some emails are hidden behind "See more" — the scraper tries to expand these

### Gmail "Daily sending limit" error
- Free Gmail accounts have a 500 emails/day limit
- Increase `EMAIL_DELAY_SECONDS` to avoid rate limiting
- Google Workspace accounts have higher limits

### Test mode (don't actually send)
Comment out the `sender.send_application(...)` call in `main.py`
and add `log.info("TEST: Would send to %s", rec["email"])` instead.

---

## Legal / Ethical Notes

- LinkedIn scraping violates their Terms of Service (Section 8.2)
- Use responsibly — low volume, respectful delays
- Sending unsolicited mass emails may violate CAN-SPAM / GDPR
- Always include an unsubscribe option for bulk sending
- Consider using LinkedIn's official **Easy Apply** feature for safer alternatives
