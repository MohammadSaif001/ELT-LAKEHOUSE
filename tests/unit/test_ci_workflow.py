from pathlib import Path

import yaml


def test_dbt_validation_runs_tests_with_the_pipeline_session():
    workflow = yaml.safe_load(
        (Path(__file__).parents[2] / ".github/workflows/ci.yml").read_text()
    )
    steps = workflow["jobs"]["dbt-validation"]["steps"]
    run_commands = [step.get("run", "") for step in steps]

    assert any("elt --run-pipeline" in command for command in run_commands)
    assert not any("dbt test" in command for command in run_commands)
