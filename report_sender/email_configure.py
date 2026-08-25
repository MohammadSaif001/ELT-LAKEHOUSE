import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from report_sender.log_parsing import generate_report
from email.mime.multipart import MIMEMultipart
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


def format_report(report: dict) -> str:
    """Create a readable plain-text email from the pipeline report."""
    lines = [
        "ELT PIPELINE REPORT",
        "=" * 20,
        f"Status: {report.get('status', 'UNKNOWN')}",
        f"Start time: {report.get('start_time') or 'N/A'}",
        f"End time: {report.get('end_time') or 'N/A'}",
        f"Duration: {report.get('duration', 'N/A')} seconds",
        "",
        "DATASETS",
        "--------",
    ]

    datasets = report.get("datasets", {})
    if datasets:
        for dataset, records in datasets.items():
            lines.append(f"{dataset.replace('_', ' ').title()}: {records:,} records")
    else:
        lines.append("No dataset information available.")

    lines.extend(["", "ERRORS", "------"])
    errors = report.get("errors", [])
    if errors:
        for error in errors:
            lines.extend(
                [
                    f"[{error.get('timestamp', 'N/A')}] {error.get('level', 'ERROR')}",
                    error.get("message", "Unknown error"),
                    "",
                ]
            )
    else:
        lines.append("No errors reported.")

    return "\n".join(lines)


def email_configured() -> bool:
    return all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL])


def send_email(body: str) -> bool:
    if not email_configured():
        logger.warning("Email reporting skipped: SMTP credentials are not configured.")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = "ELT Pipeline Report"
        msg["Reply-To"] = EMAIL_ADDRESS

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:

            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        logger.info("Email sent successfully")
        return True

    except Exception:
        logger.exception("Failed to send email.")
        return False
