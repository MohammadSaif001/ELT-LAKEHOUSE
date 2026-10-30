import argparse
import subprocess
import sys
from datetime import datetime, timezone

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)

# ==========================
# ELT Pipeline
# ==========================


def send_pipeline_report() -> None:
    """Build and send the latest pipeline report."""
    try:
        # Keep reporting dependencies optional so normal pipeline stages do not
        # require the email configuration to be available.
        from report_sender.email_configure import format_report, send_email
        from report_sender.log_parsing import generate_report

        report = generate_report()
        send_email(body=format_report(report))
    except Exception:
        logger.exception("Failed to generate or send the pipeline report.")


@monitor_memory
def orchestrate(args, send_report: bool = False) -> None:
    """Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time: datetime = datetime.now(timezone.utc)

        if args.setup:
            # Setup is intentionally separate from generation so profiling can
            # be refreshed without creating a new synthetic dataset.
            from src.elt_lakehouse.spark.jobs.download_data import download_dataset
            from src.elt_lakehouse.spark.jobs.build_profile_job import run_profile_job

            download_dataset()
            run_profile_job()

        elif args.run_pipeline:
            # The full run follows the dependency order: pools, generated
            # files, Bronze, Silver, and finally the dbt-backed Gold layer.
            from src.elt_lakehouse.spark.jobs.pool_job import run_pool_job

            run_pool_job()

            from src.elt_lakehouse.spark.common.spark_session import (
                create_spark_session,
            )
            from src.elt_lakehouse.spark.jobs.bronze_job import run_bronze_ingestion
            from src.elt_lakehouse.spark.jobs.dataset_job import run_dataset_job
            from src.elt_lakehouse.spark.jobs.silver_job import run_silver_processing
            from src.elt_lakehouse.spark.jobs.gold_job import main as run_gold_processing

            run_dataset_job()
            spark = create_spark_session()
            try:
                # Bronze and Silver share one session to avoid starting
                # separate Spark applications during the full pipeline run.
                run_bronze_ingestion(spark=spark)
                run_silver_processing(spark=spark)
            finally:
                # Always release the Spark resources, including after a stage
                # raises an exception.
                spark.stop()

            run_gold_processing()

        elif args.silver_runner:
            from src.elt_lakehouse.spark.jobs.silver_job import run_silver_processing

            run_silver_processing()
        elif args.build_pool:
            from src.elt_lakehouse.spark.jobs.pool_job import run_pool_job

            run_pool_job()
        elif args.build_dataset:
            from src.elt_lakehouse.spark.jobs.dataset_job import run_dataset_job

            run_dataset_job()
        elif args.bronze_runner:
            from src.elt_lakehouse.spark.jobs.bronze_job import run_bronze_ingestion

            run_bronze_ingestion()

        elif args.launch_dashboard:

            import webbrowser

            # Open the local UI before handing control to Uvicorn's development
            # server. The dashboard only reports existing pipeline state.
            webbrowser.open("http://127.0.0.1:5000")

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "dashboard.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "5000",
                ],
                check=True,
            )
        elif args.run_tests:
            # Run tests through the active interpreter so the selected uv
            # environment is used instead of a system pytest executable.
            subprocess.run(
                [sys.executable, "-m", "pytest"],
                check=True,
            )
        elif args.gold_runner:
            # Gold depends on completed Silver tables and is exposed as a
            # standalone stage for reruns without repeating ingestion.
            from src.elt_lakehouse.spark.jobs.gold_job import main as run_gold_processing

            run_gold_processing()
        elif args.serve_gold:
            # Serving is its own stage: Gold Delta is already built, so a failed
            # publish can be retried without rebuilding anything.
            from src.elt_lakehouse.serving.postgres_writer import publish_gold
            from src.elt_lakehouse.spark.common.spark_session import create_spark_session

            spark = create_spark_session()
            try:
                publish_gold(spark)
            finally:
                spark.stop()

        duration: float = (datetime.now(timezone.utc) - start_time).total_seconds()

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

    # Each invocation runs one pipeline action; --send-report remains a
    # modifier and can be combined with any action.
    run_group = parser.add_mutually_exclusive_group(required=True)

    run_group.add_argument(
        "--setup",
        action="store_true",
        help="Download the source dataset and build its profiling metadata.",
    )

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

    run_group.add_argument(
        "--launch-dashboard",
        action="store_true",
        help="Launch the dashboard after execution.",
    )

    run_group.add_argument(
        "--run-tests",
        action="store_true",
        help="Run the test suite for the ELT pipeline.",
    )

    run_group.add_argument(
        "--gold-runner",
        action="store_true",
        help="Run the build_gold step of the ELT pipeline.",
    )

    run_group.add_argument(
        "--serve-gold",
        action="store_true",
        help="Publish the Gold Delta tables to PostgreSQL (needs POSTGRES_* env vars).",
    )

    args = parser.parse_args()
    orchestrate(args=args, send_report=args.send_report)


if __name__ == "__main__":
    main()
