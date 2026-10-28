"""FastAPI application for the read-only ELT monitoring dashboard."""
from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

from datetime import datetime
import json
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dashboard.services import (
    dbt_reader, health_service, log_reader, status_service, telemetry_service,
)
from dashboard.services.pipeline_registry import PIPELINE_STAGES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = PROJECT_ROOT / "dashboard"

app = FastAPI(title="ELT Pipeline Health Dashboard")
app.mount(
    "/static",
    StaticFiles(directory=DASHBOARD_ROOT / "static"),
    name="static",
)
templates = Jinja2Templates(directory=DASHBOARD_ROOT / "templates")

GOLD_DIMENSIONS = [
    ("dim_customer", "Customer identity and customer location"),
    ("dim_seller", "Seller identity and seller location"),
    ("dim_product", "Product and category attributes"),
    ("dim_location", "Canonical ZIP-prefix geography"),
    ("dim_date", "Calendar reporting attributes"),
    ("dim_review", "Order review text"),
]
GOLD_FACTS = [
    ("fact_order_items", "One row per order item; sales and freight"),
    ("fact_orders", "One row per order; payment and delivery metrics"),
    ("fact_seller", "Monthly seller performance"),
    ("fact_product", "Monthly product sales and review metrics"),
]

_STATUS_BADGE = {
    "SUCCESS": ("success", "&#10003;", "SUCCESS"),
    "FAILED": ("error", "&#215;", "FAILED"),
    # RUNNING = execution started, no completion event yet; NOT the same as failed.
    "RUNNING": ("info", "&#9654;", "RUNNING"),
    "NO_DATA": ("unknown", "&#8211;", "NO DATA"),
    "UNKNOWN": ("unknown", "?", "UNKNOWN"),
    # Storage-only statuses — never used for execution health.
    "PRESENT": ("success", "&#10003;", "OUTPUT PRESENT"),
    "EMPTY": ("unknown", "&#8211;", "NO OUTPUT"),
    "PASS": ("success", "&#10003;", "PASS"),
    "ERROR": ("error", "&#215;", "ERROR"),
    "SKIPPED": ("unknown", "&#8211;", "SKIPPED"),
    "OK": ("success", "&#10003;", "PASS"),
    "WARN": ("warning", "!", "WARNING"),
    "FAIL": ("error", "&#215;", "FAILED"),
    "PENDING": ("unknown", "&#8211;", "PENDING"),
    # Incomplete execution: start seen, no matching completion, may still be running.
    "WARNING": ("warning", "!", "WARNING"),
}


_PILL_CLASS = {"success": "ok", "error": "bad", "warning": "warn", "info": "run", "unknown": "idle"}


def status_badge(status: str) -> str:
    css, _symbol, label = _STATUS_BADGE.get(status, ("unknown", "?", status))
    return f'<span class="pill pill--{_PILL_CLASS[css]}"><i></i>{label.capitalize()}</span>'


def sanitize_log(message: str) -> str:
    """Mask common secret assignments before rendering local logs."""
    result = re.sub(
        r"(?i)(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|connection[_-]?string)([\"']?\s*[=:]\s*[\"']?)([^\"'\s,;}]+)",
        r"\1\2[REDACTED]",
        message,
    )
    return re.sub(r"(?i)(://[^:/\s]+:)([^@/\s]+)(@)", r"\1[REDACTED]\3", result)


def sanitize_fields(fields: dict[str, str]) -> dict[str, str]:
    """Redact structured log fields before exposing them in the dashboard."""
    return _redact_mapping(fields)


def _redact_mapping(value):
    if isinstance(value, dict):
        secret_keys = (
            "password", "passwd", "secret", "token", "api_key", "access_key",
            "private_key", "connection_string",
        )
        return {
            key: "[REDACTED]" if any(part in str(key).lower() for part in secret_keys)
            else _redact_mapping(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_mapping(item) for item in value]
    if isinstance(value, str):
        return sanitize_log(value)
    return value


def safe_json(value) -> str:
    return json.dumps(_redact_mapping(value), indent=2, default=str)


def fmt_ts(value: str | None) -> str:
    """Format a log timestamp string into a readable local-time string.

    Accepts the log format ``YYYY-MM-DD HH:MM:SS`` or ``YYYY-MM-DD HH:MM:SS,fff``
    and returns ``YYYY-MM-DD HH:MM:SS (local)``.  Falls back to the raw value
    unchanged so templates never crash on an unexpected format.
    """
    if not value:
        return "Not available"
    for fmt in ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S") + " (local)"
        except ValueError:
            continue
    return value


def duration_label(value: str | None) -> str:
    """Make stored duration values explicit without changing their precision."""
    if not value:
        return "Not available"
    if value.endswith("ms"):
        return f"{value[:-2]} milliseconds"
    if value.endswith("s"):
        return f"{value[:-1]} seconds"
    return value


templates.env.filters["status_badge"] = status_badge
templates.env.filters["sanitize_sensitive"] = lambda value: sanitize_log(str(value))
templates.env.filters["safe_json"] = safe_json
templates.env.filters["fmt_ts"] = fmt_ts
templates.env.filters["duration_label"] = duration_label


def fmt_bytes(value: int | None) -> str:
    if not value:
        return "0 B"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


templates.env.filters["fmt_bytes"] = fmt_bytes


def plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


templates.env.filters["plural"] = plural
templates.env.filters["fmt_dur"] = telemetry_service._fmt_dur


def _overview(request: Request) -> status_service.PipelineOverview:
    """Compute the overview once per request."""
    if not hasattr(request.state, "pipeline_overview"):
        logger.info("Building pipeline overview for dashboard request")
        request.state.pipeline_overview = status_service.get_overview(PROJECT_ROOT)
    return request.state.pipeline_overview


def _render(request: Request, template_name: str, **context) -> HTMLResponse:
    overview = context.get("overview") or _overview(request)
    dbt_for_telemetry = (
        context["dbt_summary"] if "dbt_summary" in context
        else dbt_reader.read_run_results(PROJECT_ROOT)
    )
    context.update({
        "telemetry": telemetry_service.build_telemetry(
            PROJECT_ROOT, overview, dbt_for_telemetry),
        "request": request,
        "overview": overview,
        "sidebar_layers": [
            layer for layer in overview.storage_layers
            if layer.key in ("bronze", "silver", "gold")
        ],
        "sidebar_processing": {
            "bronze": next(
                (stage for stage in overview.stages
                 if stage.stage.key == "bronze_ingestion"), None
            ),
            "silver": next(
                (stage for stage in overview.stages
                 if stage.stage.key == "silver_transformation"), None
            ),
            "gold": next(
                (stage for stage in overview.stages
                 if stage.stage.key == "gold_transformation"), None
            ),
        },
        "now": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
    })
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


@app.middleware("http")
async def disable_response_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", response_class=HTMLResponse, name="index")
def index(request: Request):
    logger.info("Rendering dashboard overview")
    overview = _overview(request)
    dbt_summary = dbt_reader.read_run_results(PROJECT_ROOT)
    health = health_service.build_health_report(overview, dbt_summary)
    alerts = [
        check for check in health.checks
        if check.status in (health_service.HEALTH_WARN, health_service.HEALTH_FAIL)
    ]
    gold = next(layer for layer in overview.storage_layers if layer.key == "gold")
    return _render(
        request, "index.html", overview=overview, health=health, alerts=alerts,
        primary_alert=alerts[0] if alerts else None,
        gold=gold, gold_dimensions=GOLD_DIMENSIONS, gold_facts=GOLD_FACTS,
        dbt_summary=dbt_summary,
        dbt_check=next(check for check in health.checks if check.key == "dbt_tests"),
        dbt_models={model.name: model for model in dbt_summary.models} if dbt_summary else {},
        gold_dimension_count=len(GOLD_DIMENSIONS), gold_fact_count=len(GOLD_FACTS),
        gold_model_count=len(GOLD_DIMENSIONS) + len(GOLD_FACTS),
        recent_events=[
            log_reader.LogEvent(e.timestamp, e.level, e.logger_name, sanitize_log(e.message))
            for e in reversed(log_reader.read_events(PROJECT_ROOT)[-100:])
        ],
        active_page="home", page_number="01",
    )


@app.get("/pipeline-run", response_class=HTMLResponse, name="pipeline_run")
def pipeline_run(request: Request):
    logger.info("Rendering pipeline run view")
    return _render(
        request, "pipeline_run.html", overview=_overview(request),
        active_page="pipeline_run", page_number="02",
    )


@app.get("/data-quality", response_class=HTMLResponse, name="data_quality")
def data_quality(request: Request):
    logger.info("Rendering data quality view")
    overview = _overview(request)
    dbt_summary = dbt_reader.read_run_results(PROJECT_ROOT)
    health = health_service.build_health_report(overview, dbt_summary)
    dq_dir = PROJECT_ROOT / "tests" / "data_quality"
    dq_test_files = sorted(p.name for p in dq_dir.glob("test_*.py")) if dq_dir.is_dir() else []
    dbt_test_dir = PROJECT_ROOT / "dbt_gold" / "tests"
    dbt_test_files = sorted(p.name for p in dbt_test_dir.glob("*.sql")) if dbt_test_dir.is_dir() else []
    return _render(
        request, "data_quality.html", overview=overview,
        dq_test_files=dq_test_files, dbt_test_files=dbt_test_files,
        dbt_summary=dbt_summary,
        dbt_check=next(check for check in health.checks if check.key == "dbt_tests"),
        active_page="data_quality", page_number="03",
    )


@app.get("/storage-health", response_class=HTMLResponse, name="storage_health")
def storage_health(request: Request):
    logger.info("Rendering storage health view")
    return _render(
        request, "storage_health.html", overview=_overview(request),
        active_page="storage_health", page_number="04",
    )


@app.get("/technical-details", response_class=HTMLResponse, name="technical_details")
def technical_details(request: Request):
    logger.info("Rendering technical details view")
    overview = _overview(request)
    events = log_reader.read_events(PROJECT_ROOT)
    log_tail = [
        log_reader.LogEvent(
            e.timestamp,
            e.level,
            e.logger_name,
            sanitize_log(e.message),
            sanitize_fields(e.fields),
        )
        for e in reversed(events[-500:])
    ]
    config_dir = PROJECT_ROOT / "config"
    config_files = sorted(p.name for p in config_dir.glob("*.yaml")) if config_dir.is_dir() else []
    return _render(
        request, "technical_details.html", overview=overview,
        log_tail=log_tail, config_files=config_files,
        log_levels={lvl: sum(e.normalized_level == lvl for e in log_tail)
                    for lvl in ("INFO", "WARNING", "ERROR")},
        active_page="technical_details", page_number="05",
    )


@app.get("/gold-layer", response_class=HTMLResponse, name="gold_layer")
def gold_layer(request: Request):
    logger.info("Rendering gold layer view")
    overview = _overview(request)
    dbt_summary = dbt_reader.read_run_results(PROJECT_ROOT)
    dbt_health = health_service.build_health_report(overview, dbt_summary)
    gold = next(layer for layer in overview.storage_layers if layer.key == "gold")
    return _render(
        request, "gold_layer.html", overview=overview, gold=gold,
        dimensions=GOLD_DIMENSIONS, facts=GOLD_FACTS,
        dimension_count=len(GOLD_DIMENSIONS), fact_count=len(GOLD_FACTS),
        model_count=len(GOLD_DIMENSIONS) + len(GOLD_FACTS),
        dbt_summary=dbt_summary,
        dbt_check_status=next(check.status for check in dbt_health.checks if check.key == "dbt_tests"),
        dbt_check_message=next(check.message for check in dbt_health.checks if check.key == "dbt_tests"),
        dbt_models={model.name: model for model in dbt_summary.models} if dbt_summary else {},
        active_page="gold_layer", page_number="06",
    )


@app.get("/stage/{stage_key}", response_class=HTMLResponse, name="stage_detail")
def stage_detail(request: Request, stage_key: str):
    logger.info("Rendering stage detail: stage=%s", stage_key)
    valid_keys = {stage.key for stage in PIPELINE_STAGES}
    if stage_key not in valid_keys:
        raise HTTPException(status_code=404, detail="Unknown pipeline stage")
    overview = _overview(request)
    stage = next(stage for stage in overview.stages if stage.stage.key == stage_key)
    return _render(
        request, "stage_detail.html", overview=overview, stage=stage,
        active_page="pipeline_run", page_number="02",
    )


@app.get("/api/telemetry", name="api_telemetry")
def api_telemetry():
    logger.info("Serving telemetry API")
    overview = status_service.get_overview(PROJECT_ROOT)
    dbt_summary = dbt_reader.read_run_results(PROJECT_ROOT)
    return JSONResponse(telemetry_service.build_telemetry(PROJECT_ROOT, overview, dbt_summary))


@app.get("/api/health", name="api_health")
def api_health():
    logger.info("Serving health API")
    overview = status_service.get_overview(PROJECT_ROOT)
    dbt_summary = dbt_reader.read_run_results(PROJECT_ROOT)
    health = health_service.build_health_report(overview, dbt_summary)
    payload = {
        "status": health.overall,
        "latest_run": {
            "status": overview.latest_run_status,
            # Plain-language explanation when status is not SUCCESS.
            "status_detail": overview.latest_run_detail,
            "started_at": overview.last_run_started,
            "finished_at": overview.last_run_finished,
            "duration": overview.last_run_duration,
            # last_successful_run is distinct from the latest run; only set
            # when an actual SUCCESS event exists in the history.
            "last_successful_at": overview.last_successful_run,
            "timestamp_timezone": "local (server)",
        },
        "dbt_tests": ({
            "generated_at": dbt_summary.generated_at,
            "total": dbt_summary.tests_total,
            "passed": dbt_summary.tests_passed,
            "failed": dbt_summary.tests_failed,
            "errored": dbt_summary.tests_errored,
            "warned": dbt_summary.tests_warned,
            "skipped": dbt_summary.tests_skipped,
        } if dbt_summary else None),
        "checks": [
            {
                "key": check.key,
                "label": check.label,
                "status": check.status,
                "message": check.message,
                "stage": check.stage,
                "timestamp": check.timestamp,
                "next_step": check.next_step,
            }
            for check in health.checks
        ],
    }
    http_status = 503 if health.overall == health_service.HEALTH_FAIL else 200
    return JSONResponse(payload, status_code=http_status)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=5000, reload=True)
