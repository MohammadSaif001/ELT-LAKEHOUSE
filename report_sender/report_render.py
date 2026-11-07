import re
import html
from numbers import Real
from textwrap import fill

REPORT_WIDTH = 72


def format_report(report: dict) -> str:
    """
    Generate a production-style ELT pipeline monitoring report.

    Supports:
        - Pipeline execution summary
        - Bronze, Silver, and Gold layer status
        - Dataset processing statistics
        - Performance metrics and throughput
        - Error and warning classification
        - Data quality metrics
        - Actionable recommendations
    """

    def is_number(value):
        return isinstance(value, Real) and not isinstance(value, bool)

    def display(value, fallback="N/A"):
        if value is None or value == "":
            return fallback
        return str(value)

    def marker(status):
        return {
            "SUCCESS": "[OK]",
            "COMPLETED": "[OK]",
            "HEALTHY": "[OK]",
            "RUNNING": "[..]",
            "WARNING": "[!!]",
            "FAILED": "[XX]",
            "ERROR": "[XX]",
            "CRITICAL": "[XX]",
            "UNKNOWN": "[--]",
            "NOT EXECUTED": "[--]",
        }.get(status, "[--]")

    def section(title):
        return [
            "",
            "+" + "-" * (REPORT_WIDTH - 2) + "+",
            f"| {title:<{REPORT_WIDTH - 4}} |",
            "+" + "-" * (REPORT_WIDTH - 2) + "+",
        ]

    def format_message(message):
        return fill(
            display(message, "Unknown error"), width=REPORT_WIDTH - 8
        ).splitlines()

    def safe_mapping(value):
        return value if isinstance(value, dict) else {}

    def safe_list(value):
        return value if isinstance(value, (list, tuple)) else []

    if not isinstance(report, dict):
        raise TypeError("report must be a dictionary")

    datasets = safe_mapping(report.get("datasets"))
    layers = safe_mapping(report.get("layers"))
    errors = safe_list(report.get("errors"))

    status = display(report.get("status"), "UNKNOWN").upper()
    duration = report.get("duration")

    total_records = sum(
        value for value in datasets.values() if is_number(value) and value >= 0
    )

    # Optional dataset quality metrics
    total_failed = sum(
        value.get("failed", 0)
        for value in datasets.values()
        if isinstance(value, dict)
        and is_number(value.get("failed", 0))
        and value.get("failed", 0) >= 0
    )

    total_skipped = sum(
        value.get("skipped", 0)
        for value in datasets.values()
        if isinstance(value, dict)
        and is_number(value.get("skipped", 0))
        and value.get("skipped", 0) >= 0
    )

    error_count = 0
    warning_count = 0
    info_count = 0

    for error in errors:
        level = (
            str(error.get("level", "ERROR")).upper()
            if isinstance(error, dict)
            else "ERROR"
        )

        if level in ("ERROR", "CRITICAL", "FATAL"):
            error_count += 1
        elif level == "WARNING":
            warning_count += 1
        else:
            info_count += 1

    failed = status in ("FAILED", "ERROR", "CRITICAL")

    successful = status in ("SUCCESS", "COMPLETED")

    layer_failures = any(
        str(safe_mapping(layers.get(name)).get("status", "")).upper()
        in ("FAILED", "ERROR", "CRITICAL")
        for name in ("bronze", "silver", "gold")
    )

    health = (
        "CRITICAL"
        if failed or layer_failures or error_count
        else (
            "HEALTHY"
            if successful and not warning_count and not total_failed
            else "WARNING"
        )
    )

    lines = [
        "+" + "=" * (REPORT_WIDTH - 2) + "+",
        f"| {'ELT PIPELINE MONITORING REPORT':^{REPORT_WIDTH - 4}} |",
        f"| {'Automated execution summary':^{REPORT_WIDTH - 4}} |",
        "+" + "=" * (REPORT_WIDTH - 2) + "+",
        "",
        f"  {'Pipeline':<17}: "
        f"{display(report.get('pipeline_name'), 'ELT Pipeline')}",
        f"  {'Execution ID':<17}: " f"{display(report.get('execution_id'))}",
        f"  {'Environment':<17}: " f"{display(report.get('environment'))}",
        f"  {'Health':<17}: {marker(health)} {health}",
        f"  {'Status':<17}: {marker(status)} {status}",
        f"  {'Started At':<17}: {display(report.get('start_time'))}",
        f"  {'Completed At':<17}: {display(report.get('end_time'))}",
        f"  {'Duration':<17}: "
        f"{f'{duration:.2f} seconds' if is_number(duration) and duration >= 0 else 'N/A'}",
    ]

    lines.extend(section("EXECUTIVE SUMMARY"))

    lines.extend(
        [
            f"  {'Datasets':<22}: {len(datasets):,}",
            f"  {'Total Records':<22}: {total_records:,}",
            f"  {'Failed Records':<22}: {total_failed:,}",
            f"  {'Skipped Records':<22}: {total_skipped:,}",
            f"  {'Errors':<22}: {error_count:,}",
            f"  {'Warnings':<22}: {warning_count:,}",
            f"  {'Information':<22}: {info_count:,}",
            f"  {'Overall Result':<22}: {marker(health)} {health}",
        ]
    )

    lines.extend(section("MEDALLION LAYER STATUS"))

    lines.extend(
        [
            "  Layer              Status          Duration",
            "  " + "-" * 51,
        ]
    )

    for name in ("bronze", "silver", "gold"):
        layer = safe_mapping(layers.get(name))

        layer_status = str(layer.get("status") or "NOT EXECUTED").upper()

        layer_duration = layer.get("duration")

        duration_text = (
            f"{layer_duration:.2f}s"
            if is_number(layer_duration) and layer_duration >= 0
            else "N/A"
        )

        lines.append(
            f"  {name.title() + ' Layer':<20}"
            f"{marker(layer_status)} {layer_status:<10}"
            f"{duration_text:>12}"
        )

    lines.extend(section("DATASET PROCESSING DETAILS"))

    if datasets:
        lines.extend(
            [
                f"  {'Dataset':<30} {'Records':>15}",
                "  " + "-" * 47,
            ]
        )

        for name, records in datasets.items():
            dataset_name = str(name).replace("_", " ").title()

            if is_number(records) and records >= 0:
                record_text = f"{records:,}"
            elif isinstance(records, dict):
                record_text = display(records.get("records"), "N/A")
            else:
                record_text = display(records)

            lines.append(f"  {dataset_name:<30.30} {record_text:>15}")
    else:
        lines.append("  No dataset information available.")

    lines.extend(section("PERFORMANCE METRICS"))

    if is_number(duration) and duration > 0:
        throughput = total_records / duration

        lines.extend(
            [
                f"  {'Execution Duration':<22}: {duration:.2f} seconds",
                f"  {'Processing Speed':<22}: " f"{throughput:,.2f} records/second",
            ]
        )
    else:
        lines.append("  Performance metrics unavailable.")

    lines.extend(section("DATA QUALITY SUMMARY"))

    lines.extend(
        [
            f"  {'Records Processed':<22}: {total_records:,}",
            f"  {'Failed Records':<22}: {total_failed:,}",
            f"  {'Skipped Records':<22}: {total_skipped:,}",
        ]
    )

    if total_records > 0:
        failure_rate = (total_failed / total_records) * 100

        lines.append(f"  {'Failure Rate':<22}: {failure_rate:.2f}%")

    lines.extend(section("ERROR & WARNING ANALYSIS"))

    if errors:
        for index, error in enumerate(errors, start=1):

            if isinstance(error, dict):
                level = str(error.get("level", "ERROR")).upper()

                timestamp = display(error.get("timestamp"))

                message = error.get("message", "Unknown error")

            else:
                level = "ERROR"
                timestamp = "N/A"
                message = error

            lines.extend(
                [
                    f"  {marker(level)} {level} #{index}",
                    f"  Timestamp : {timestamp}",
                    f"  Message   :",
                ]
            )

            lines.extend(f"    {line}" for line in format_message(message))

            lines.append("")

    else:
        lines.append("  No errors or warnings reported.")

    lines.extend(section("ACTION REQUIRED"))

    if health == "CRITICAL":
        lines.extend(
            [
                "  [XX] Immediate investigation required.",
                "  [XX] Review failed layers and critical errors.",
                "  [XX] Check failed records and data integrity.",
            ]
        )

    elif health == "WARNING":
        lines.extend(
            [
                "  [!!] Pipeline completed with warnings or issues.",
                "  [!!] Review data quality and warning messages.",
            ]
        )

    else:
        lines.append(
            "  [OK] Pipeline completed successfully. " "No immediate action required."
        )

    lines.extend(
        [
            "",
            "+" + "=" * (REPORT_WIDTH - 2) + "+",
            f"| {'END OF REPORT':^{REPORT_WIDTH - 4}} |",
            "+" + "=" * (REPORT_WIDTH - 2) + "+",
        ]
    )

    return "\n".join(lines)


GREEN = "#16803c"
RED = "#dc2626"

_STATUS_RE = re.compile(
    r"""
    (?P<green>
        \[OK\](?:\s*(?:HEALTHY|SUCCESS))?
        | \bSUCCESSFUL\b
        | \bCOMPLETED\b
        | \bPASSED\b
    )
    |
    (?P<red>
        \[FAILED\]
        | \bFAILED\b
        | \bFAILURE\b
        | \bERRORS?\b
        | \bCRITICAL\b
        | \bWARNINGS?\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _colorize(match: re.Match) -> str:
    color = GREEN if match.lastgroup == "green" else RED
    return f'<span style="color: {color}; font-weight: bold;">{match.group(0)}</span>'


def _format_html_report(body: str) -> str:
    """Create a clean, centered HTML report with green and red status text only."""

    escaped_body = html.escape(str(body))
    escaped_body = _STATUS_RE.sub(_colorize, escaped_body)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="margin: 0; padding: 0; background-color: #f1f5f9;">

    <!-- Outer wrapper: centers everything -->
    <div style="
        width: 100%;
        padding: 25px 0;
        background-color: #f1f5f9;
        text-align: center;
        font-family: comic mono, consolas, menlo, monospace;
    ">

        <!-- Report card -->
        <div style="
            display: inline-block;
            width: 100%;
            max-width: 850px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            text-align: left;
        ">

            <!-- Header -->
            <div style="
                background-color: #172554;
                color: #ffffff;
                padding: 25px 30px;
                text-align: center;
            ">
                <h2 style="margin: 0; font-size: 21px;">
                    ELT Pipeline Monitoring Report
                </h2>

                <p style="
                    margin: 7px 0 0;
                    color: #cbd5e1;
                    font-size: 13px;
                ">
                    Automated execution summary
                </p>
            </div>

            <!-- Report body -->
            <div style="padding: 25px; text-align: left;">
                <pre style="
                    margin: 0;
                    color: #334155;
                    font-family: 'Comic Mono', Consolas, Menlo, monospace;
                    font-size: 13px;
                    line-height: 1.7;
                    white-space: pre-wrap;
                    overflow-wrap: anywhere;
                ">{escaped_body}</pre>
            </div>

            <!-- Footer -->
            <div style="
                padding: 15px 25px;
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
                color: #64748b;
                font-size: 11px;
                text-align: center;
            ">
                Automated ELT Pipeline Monitoring System
            </div>

        </div>
    </div>

</body>
</html>"""