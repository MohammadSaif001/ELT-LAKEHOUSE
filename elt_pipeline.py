import argparse
import subprocess
import sys
from datetime import datetime, timezone

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


def send_pipeline_report() -> None:
    """Build and send the latest pipeline report."""
    try:
        from report_sender.email_configure import format_report, send_email
        from report_sender.log_parsing import generate_report

        report = generate_report()
        send_email(body=format_report(report))
    except Exception:
        logger.exception("Failed to generate or send the pipeline report.")


@monitor_memory
def orchestrate(args, send_report: bool = False) -> None:
    """Run the requested pipeline stages in dependency order."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time = datetime.now(timezone.utc)

        if args.launch_dashboard:
            import webbrowser

            webbrowser.open("http://127.0.0.1:5000")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "flask",
                    "--app",
                    "dashboard.app",
                    "run",
                ],
                check=True,
            )
        else:
            run_all = args.run_pipeline

            if run_all or args.setup:
                from src.elt_lakehouse.spark.jobs.download_data import download_dataset

                download_dataset()

            if run_all or args.setup or args.build_profiling:
                from src.elt_lakehouse.spark.jobs.build_profile_job import (
                    run_profile_job,
                )

                run_profile_job()

            if run_all or args.build_pool:
                from src.elt_lakehouse.spark.jobs.pool_job import run_pool_job

                run_pool_job()

            if run_all or args.build_dataset:
                from src.elt_lakehouse.spark.jobs.dataset_job import run_dataset_job

                run_dataset_job()

            if run_all or args.bronze_runner or args.silver_runner:
                from src.elt_lakehouse.spark.common.spark_session import (
                    create_spark_session,
                )

                spark = create_spark_session()
                try:
                    if run_all or args.bronze_runner:
                        from src.elt_lakehouse.spark.jobs.bronze_job import (
                            run_bronze_ingestion,
                        )

                        run_bronze_ingestion(spark=spark)

                    if run_all or args.silver_runner:
                        from src.elt_lakehouse.spark.jobs.silver_job import (
                            run_silver_processing,
                        )

                        run_silver_processing(spark=spark)
                finally:
                    spark.stop()

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info("ELT pipeline completed successfully in %.2f seconds.", duration)

        if send_report:
            send_pipeline_report()

    except Exception:
        logger.exception("Pipeline failed with a critical error.")
        if send_report:
            send_pipeline_report()
        raise


def main() -> None:
    """Parse command-line arguments and run the ELT pipeline."""
    parser = argparse.ArgumentParser(description="Run selected ELT pipeline stages.")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Download the dataset and build profiling metadata.",
    )
    parser.add_argument(
        "--build-profiling", action="store_true", help="Build dataset profiles."
    )
    parser.add_argument("--build-pool", action="store_true", help="Build pools.")
    parser.add_argument(
        "--build-dataset", action="store_true", help="Generate datasets."
    )
    parser.add_argument(
        "--bronze-runner", action="store_true", help="Run bronze ingestion."
    )
    parser.add_argument(
        "--silver-runner", action="store_true", help="Run silver processing."
    )
    parser.add_argument(
        "--run-pipeline",
        action="store_true",
        help="Run every stage: setup, profiling, pool, dataset, bronze, and silver.",
    )
    parser.add_argument(
        "--launch-dashboard", action="store_true", help="Launch the dashboard."
    )
    parser.add_argument(
        "--send-report",
        action="store_true",
        help="Send the pipeline report after execution.",
    )

    args = parser.parse_args()
    selected_stages = any(
        (
            args.setup,
            args.build_profiling,
            args.build_pool,
            args.build_dataset,
            args.bronze_runner,
            args.silver_runner,
            args.run_pipeline,
        )
    )
    if args.launch_dashboard and selected_stages:
        parser.error("--launch-dashboard cannot be combined with pipeline stages.")
    if not args.launch_dashboard and not selected_stages:
        parser.error("Choose at least one pipeline stage or --launch-dashboard.")

    orchestrate(args=args, send_report=args.send_report)


if __name__ == "__main__":
    main()
