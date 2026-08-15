"""Pipeline Monitoring Dashboard -- Flask application.

Run with:
    python3 -m dashboard.app

or, using Flask's own runner:
    flask --app dashboard.app run

This app is read-only: it reports the ELT pipeline's status by reading
the project's existing logs/application.log, metadata/*.json state
files, and storage/ layers. It does not run, schedule, or modify the
pipeline in any way.
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template

from dashboard.services import status_service
from dashboard.services.pipeline_registry import PIPELINE_STAGES

PROJECT_ROOT = Path(__file__).resolve().parents[1]

app = Flask(__name__)


@app.route("/")
def index():
    overview = status_service.get_overview(PROJECT_ROOT)
    return render_template("index.html", overview=overview)


@app.route("/stage/<stage_key>")
def stage_detail(stage_key: str):
    valid_keys = {s.key for s in PIPELINE_STAGES}
    if stage_key not in valid_keys:
        abort(404)
    stage = status_service.get_stage(PROJECT_ROOT, stage_key)
    return render_template("stage_detail.html", stage=stage)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
