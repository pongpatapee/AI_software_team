import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path
    return subprocess.run(
        [sys.executable, "-m", "ai_software_team.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def start_discovered_run(
    target_project: Path,
) -> tuple[str, subprocess.CompletedProcess[str]]:
    result = run_cli(
        [
            "start",
            "--target-project",
            str(target_project),
            "--product-slice",
            "Add a saved reports page",
            "--user-goal",
            "Let users revisit important reports",
            "--acceptance-criteria",
            "Users can see saved reports",
            "--constraint",
            "Keep the existing stack",
            "--approve",
        ],
        cwd=Path.cwd(),
    )
    assert result.returncode == 0, result.stderr

    runs_root = target_project / ".ai-team" / "runs"
    run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    return run_dirs[0].name, result


def test_start_creates_run_artifacts_from_discovery_answers(tmp_path: Path) -> None:
    target_project = tmp_path / "target-project"
    target_project.mkdir()

    run_id, result = start_discovered_run(target_project)
    assert "Started run" in result.stdout

    run_dir = target_project / ".ai-team" / "runs" / run_id

    state = json.loads((run_dir / "state.json").read_text())
    assert state["run_id"] == run_dir.name
    assert state["phase"] == "discovery"
    assert state["status"] == "waiting_for_resume"
    assert state["target_project_path"] == str(target_project.resolve())
    assert state["resumable"] is True
    assert state["created_at"] is not None
    assert state["updated_at"] is not None

    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text().splitlines()
    ]
    assert [event["event_type"] for event in events] == [
        "run.started",
        "spec.created",
    ]

    spec = (run_dir / "spec.md").read_text()
    assert "# Product Slice Spec" in spec
    assert "Add a saved reports page" in spec
    assert "Users can see saved reports" in spec


def test_status_shows_latest_run_state_for_target_project(tmp_path: Path) -> None:
    target_project = tmp_path / "target-project"
    target_project.mkdir()
    run_id, _ = start_discovered_run(target_project)

    result = run_cli(
        ["status", "--target-project", str(target_project)],
        cwd=Path.cwd(),
    )

    assert result.returncode == 0, result.stderr
    assert f"Run ID: {run_id}" in result.stdout
    assert "Phase: discovery" in result.stdout
    assert "Status: waiting_for_resume" in result.stdout
    assert f"Target Project: {target_project.resolve()}" in result.stdout


def test_resume_loads_existing_run_and_records_timeline_event(tmp_path: Path) -> None:
    target_project = tmp_path / "target-project"
    target_project.mkdir()
    run_id, _ = start_discovered_run(target_project)

    result = run_cli(
        ["resume", run_id, "--target-project", str(target_project)],
        cwd=Path.cwd(),
    )

    assert result.returncode == 0, result.stderr
    assert f"Resumed run {run_id}" in result.stdout
    assert "Current phase: discovery" in result.stdout

    events_path = target_project / ".ai-team" / "runs" / run_id / "events.jsonl"
    events = [
        json.loads(line)
        for line in events_path.read_text().splitlines()
    ]
    assert events[-1]["event_type"] == "run.resumed"
