import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from report_sender.report_render import _format_html_report, format_report
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def email_configured() -> bool:
    return all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL])


def send_email(body: str) -> bool:
    if not email_configured():
        logger.warning("Email reporting skipped: SMTP credentials are not configured.")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = "ELT Pipeline Report"
        msg["Reply-To"] = EMAIL_ADDRESS

        html_body = _format_html_report(body)

        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        logger.info("Email sent successfully")
        return True

    except Exception:
        logger.exception("Failed to send email.")
        return False
