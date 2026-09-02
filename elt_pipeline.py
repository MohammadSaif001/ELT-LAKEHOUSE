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


def orchestrate(args, send_report: bool = False) -> None:
    """Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time: datetime = datetime.now()

        from src.elt_lakehouse.generators.build_pool import build_pool
        from src.elt_lakehouse.generators.build_dataset import build_dataset
        from src.elt_lakehouse.spark.silver.silver_runner import silver_runner
        from src.elt_lakehouse.ingestion.bronze.bronze_runner import bronze_runner


        if args.run_pipeline:
            build_pool()
            build_dataset()
            bronze_runner()
            silver_runner()
        elif args.silver_runner:
            silver_runner()
        elif args.build_pool:
            build_pool()
        elif args.build_dataset:
            build_dataset()
        elif args.bronze_runner:
            bronze_runner()

        duration: float = (datetime.now() - start_time).total_seconds()

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

    run_group = parser.add_mutually_exclusive_group(required=True)

    run_group.add_argument(
        "--build-pool",
        action="store_true",
        help="Run only the build_pool step of the ELT pipeline.",
    )

    run_group.add_argument(
        "--build-dataset",
        action="store_true",
        help="Run only the build_dataset step of the ELT pipeline.",
    )

    run_group.add_argument(
        "--silver-runner",
        action="store_true",
        help="Run only the silver_runner step of the ELT pipeline.",
    )

    run_group.add_argument(
        "--bronze-runner",
        action="store_true",
        help="Run only the bronze_runner step of the ELT pipeline.",
    )

    run_group.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Run the entire ELT pipeline.",
    )

    parser.add_argument(
        "--send-report",
        action="store_true",
        help="Send the pipeline report via email after execution.",
    )

    args = parser.parse_args()
    orchestrate(args=args, send_report=args.send_report)


if __name__ == "__main__":
    main()
