import argparse
from datetime import datetime
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

# ==========================
# ELT Pipeline
# ==========================


def send_pipeline_report() -> None:
    """Build and send the latest pipeline report."""
    try:
        from report_sender.email_configure import format_report, send_email
        from report_sender.log_parsing import generate_report

        report = generate_report()
        send_email(body=format_report(report))
    except Exception:
        logger.exception("Failed to generate or send the pipeline report.")


def orchestrate(send_report: bool = False) -> None:
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

        logger.info("ELT pipeline completed successfully in %.2f seconds.", duration)

        if send_report:
            send_pipeline_report()

    except Exception:
        logger.exception("Pipeline failed with a critical error.")

        if send_report:
            send_pipeline_report()
        raise

def main() -> None:
    """Main function to run the ELT pipeline."""
    parser = argparse.ArgumentParser(description="Run the ELT pipeline.")
    parser.add_argument(
        "--send-report",
        action="store_true",
        help="Send the pipeline report via email after execution.",
    )
    args = parser.parse_args()

    orchestrate(send_report=args.send_report)


if __name__ == "__main__":
    main()
