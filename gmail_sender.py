"""
gmail_sender.py
================
Authenticates with Gmail API (OAuth2) and sends emails with resume attachment.

Requires:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import base64
import logging
import mimetypes
from email.mime.multipart  import MIMEMultipart
from email.mime.text       import MIMEText
from email.mime.base       import MIMEBase
from email.mime.application import MIMEApplication
from email                 import encoders

from google.oauth2.credentials       import Credentials
from google_auth_oauthlib.flow       import InstalledAppFlow
from google.auth.transport.requests  import Request
from googleapiclient.discovery       import build
from googleapiclient.errors          import HttpError

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailSender:
    def __init__(self, credentials_file: str = "credentials.json",
                 token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file       = token_file
        self._service         = None

    # ── Step 3: Authenticate ───────────────────────────────────────
    def authenticate(self):
        """
        First run: opens browser to complete OAuth2 flow.
        Saves token.json so subsequent runs skip the browser step.
        """
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log.info("  Refreshing Gmail token...")
                creds.refresh(Request())
            else:
                log.info("  Starting Gmail OAuth2 flow (browser will open)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as f:
                f.write(creds.to_json())
            log.info("  Token saved to %s", self.token_file)

        self._service = build("gmail", "v1", credentials=creds)
        log.info("  Gmail API service ready.")

    # ── Step 4: Send application email ────────────────────────────
    def send_application(
        self,
        to_email:         str,
        recruiter_name:   str,
        job_title:        str,
        company:          str,
        candidate:        dict,
        resume_path:      str,
        subject_template: str,
        body_template:    str,
    ) -> bool:
        """
        Compose and send one application email with resume attached.
        Returns True on success, False on failure.
        """
        # Fill in templates
        placeholders = {
            "RecruiterName": recruiter_name,
            "JobTitle":      job_title,
            "Company":       company,
            "Name":          candidate.get("name", ""),
            "Phone":         candidate.get("phone", ""),
            "LinkedIn":      candidate.get("linkedin", ""),
            "Visa":          candidate.get("visa", ""),
            "Rate":          candidate.get("rate", ""),
            "Available":     candidate.get("available", ""),
            "Location":      candidate.get("location", ""),
        }
        subject = subject_template.format(**placeholders)
        body    = body_template.format(**placeholders)

        # Build MIME message
        msg = MIMEMultipart()
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Attach resume
        if resume_path and os.path.exists(resume_path):
            msg = _attach_file(msg, resume_path)
            log.debug("  Resume attached: %s", resume_path)
        else:
            log.warning("  Resume not found at '%s' — sending without attachment.", resume_path)

        # Encode and send
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            self._service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            return True
        except HttpError as e:
            log.error("  Gmail API error: %s", e)
            return False
        except Exception as e:
            log.error("  Unexpected error sending email: %s", e)
            return False


# ── Helper ─────────────────────────────────────────────────────────
def _attach_file(msg: MIMEMultipart, path: str) -> MIMEMultipart:
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type == "application/pdf":
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
        filename = os.path.basename(path)
        part.add_header("Content-Disposition", "attachment", filename=filename)
    else:
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"',
        )
    msg.attach(part)
    return msg
