from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
import re

LOG_PATTERN = re.compile(
    r"(?P<timestamp>[^|]+)\s*\|\s*"
    r"(?P<level>\w+)\s*\|\s*"
    r"(?P<logger>[^|]+)\s*\|\s*"
    r"(?P<message>.*)"
)


def parse_line(line) -> dict | None:
    match = LOG_PATTERN.match(line)

    if not match:
        return None

    return match.groupdict()


def extract_records(message) -> int | None:
    match = re.search(r"records\s*=\s*(\d+)", message, re.IGNORECASE)

    if match:
        return int(match.group(1))

    return None


def _empty_report() -> dict:
    return {
        "status": "UNKNOWN",
        "start_time": None,
        "end_time": None,
        "duration": None,
        "layers": {
            "bronze": {"status": "UNKNOWN", "duration": None},
            "silver": {"status": "UNKNOWN", "duration": None},
            "gold": {"status": "UNKNOWN", "duration": None},
        },
        "datasets": {},
        "errors": [],
    }


def generate_report() -> dict:
    logger.info("generate_report started")
    report = _empty_report()

    with open("logs/application.log", "r") as file:
        for line in file:
            data = parse_line(line)

            if data is None:
                continue

            timestamp = data["timestamp"].strip()
            level = data["level"].strip()
            message = data["message"].strip()

            message_lower = message.lower()

            if "starting elt pipeline" in message_lower:
                report = _empty_report()
                report["start_time"] = timestamp
                report["status"] = "RUNNING"

            elif "elt pipeline completed successfully" in message_lower:
                report["end_time"] = timestamp
                report["status"] = "SUCCESS"

                duration_match = re.search(
                    r"in\s+([\d.]+)\s+seconds", message, re.IGNORECASE
                )

                if duration_match:
                    report["duration"] = float(duration_match.group(1))

            elif "pipeline failed with a critical error" in message_lower:
                report["status"] = "FAILED"

                report["errors"].append(
                    {"timestamp": timestamp, "level": level, "message": message}
                )

            layer = None
            if "starting bronze ingestion" in message_lower:
                layer = "bronze"
                report["layers"][layer]["status"] = "RUNNING"
            elif "ingestion functions completed successfully" in message_lower:
                layer = "bronze"
                report["layers"][layer]["status"] = "SUCCESS"
            elif "ingestion failed" in message_lower:
                layer = "bronze"
                report["layers"][layer]["status"] = "FAILED"
            elif "starting silver layer processing" in message_lower:
                layer = "silver"
                report["layers"][layer]["status"] = "RUNNING"
            elif "silver layer processing completed successfully" in message_lower:
                layer = "silver"
                report["layers"][layer]["status"] = "SUCCESS"
            elif "all data validations completed successfully" in message_lower:
                layer = "silver"
                report["layers"][layer]["status"] = "SUCCESS"
            elif "silver layer processing failed" in message_lower:
                layer = "silver"
                report["layers"][layer]["status"] = "FAILED"
            elif "starting gold layer build" in message_lower:
                layer = "gold"
                report["layers"][layer]["status"] = "RUNNING"
            elif "gold layer build completed successfully" in message_lower:
                layer = "gold"
                report["layers"][layer]["status"] = "SUCCESS"
            elif "gold layer build failed" in message_lower:
                layer = "gold"
                report["layers"][layer]["status"] = "FAILED"

            if layer:
                duration_match = re.search(
                    r"duration_s\s*=\s*([\d.]+)", message, re.IGNORECASE
                )
                if duration_match:
                    report["layers"][layer]["duration"] = float(
                        duration_match.group(1)
                    )

            dataset_match = re.search(
                r"(customer|order|seller|product|review|payment|"
                r"geolocation|order_item)"
                r".*dataset generated successfully",
                message,
                re.IGNORECASE,
            )

            if dataset_match:
                dataset = dataset_match.group(1).lower()

                records = extract_records(message)

                if records is not None:
                    report["datasets"][dataset] = records
    return report
