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
        "datasets": {},
        "errors": [],
    }


def generate_report() -> dict:
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
