from datetime import datetime
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

# ==========================
# ELT Pipeline
# ==========================


def send_pipeline_report() -> None:
    """Build and send the latest pipeline report."""
    from report_sender.email_sender import format_report, send_email
    from report_sender.log_parsing import generate_report

    report = generate_report()
    send_email(body=format_report(report))


def orchestrate() -> None:
    """Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time: datetime = datetime.now()

        from src.elt_lakehouse.generators.build_pool import build_pool
        from src.elt_lakehouse.generators.build_dataset import build_dataset
        from src.elt_lakehouse.ingestion.bronze.bronze_runner import bronze_runner

        # Generate synthetic data
        build_pool()

        # Generate datasets from the synthetic data
        build_dataset()

        # Ingest data into Bronze Delta tables
        bronze_runner()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "ELT pipeline completed successfully in durations_s=%.2f.",duration,
        )
        send_pipeline_report()
    except Exception:
        logger.exception("Pipeline failed with an critical error.")
        try:
            send_pipeline_report()
        except Exception:
            logger.exception("Failed to send pipeline failure report.")
        raise


def main() -> None:
    """Main function to run the ELT pipeline."""
    orchestrate()


if __name__ == "__main__":
    main()
