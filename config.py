import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LINKEDIN_EMAIL    = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    SEARCH_KEYWORDS = ["Java Developer", "Contract"]
    HOURS_BACK      = 24
    MAX_POSTS       = 50
    HEADLESS        = False

    GMAIL_CREDENTIALS_FILE = "credentials.json"
    GMAIL_TOKEN_FILE       = "token.json"

    CANDIDATE = {
        "name":      os.getenv("CANDIDATE_NAME"),
        "phone":     os.getenv("CANDIDATE_PHONE"),
        "linkedin":  os.getenv("CANDIDATE_LINKEDIN"),
        "visa":      os.getenv("CANDIDATE_VISA"),
        "rate":      os.getenv("CANDIDATE_RATE"),
        "available": os.getenv("CANDIDATE_AVAILABLE"),
        "location":  os.getenv("CANDIDATE_LOCATION"),
    }

    RESUME_PATH         = "resume.pdf"
    EMAIL_DELAY_SECONDS = 5

    EMAIL_SUBJECT_TEMPLATE = (
        "Application for {JobTitle} | {Name} | {Visa} | Available {Available}"
    )

    EMAIL_BODY_TEMPLATE = """Dear {RecruiterName},

I came across your recent LinkedIn post regarding a {JobTitle} opportunity \
at {Company} and would like to submit my candidacy.

--- SUBMISSION DETAILS ---
Candidate Name    : {Name}
Contact Number    : {Phone}
LinkedIn Profile  : {LinkedIn}
Work Authorization: {Visa}
Current Location  : {Location}
Availability      : {Available}
Expected Rate     : {Rate}
--------------------------

Please find my resume attached. I am available for a call at your convenience.

Best regards,
{Name}
{Phone}
{LinkedIn}
"""