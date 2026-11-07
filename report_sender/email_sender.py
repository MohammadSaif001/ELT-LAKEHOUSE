from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

def send_pipeline_report() -> None:
    """Build and send the latest pipeline report."""
    try:
        from report_sender.email_configure import send_email
        from report_sender.log_parsing import generate_report
        from report_sender.report_render import format_report

        report = generate_report()
        send_email(body=format_report(report))
    except Exception:
        logger.exception("Failed to generate or send the pipeline report.")