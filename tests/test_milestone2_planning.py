"""Milestone 2: Agent stack, orchestration, and planning."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ai_software_team.agents.testing import FakeLlm
from ai_software_team.inspection import inspect_target_project
from ai_software_team.orchestration import run_planning_phase
from ai_software_team.runs import DiscoveryAnswers, start_run


def make_approved_run(tmp_path: Path) -> tuple[Path, Path]:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# My Project\nA sample project.")
    (target_project / "main.py").write_text("def main(): pass\n")

    state = start_run(
        DiscoveryAnswers(
            target_project=target_project,
            product_slice="Add user authentication",
            user_goal="Users need to log in securely",
            acceptance_criteria=["Users can register and log in"],
            constraints=["Use existing stack"],
            approved=True,
        )
    )
    run_dir = target_project / ".ai-team" / "runs" / state["run_id"]
    return run_dir, target_project


def make_two_response_model() -> FakeLlm:
    return FakeLlm(
        responses=[
            "Spec confirmed. Requirements are clear and ready for planning.",
            "## Implementation Plan\n\n### Findings\nFound main.py and README.md.\n\n### Tasks\n1. Implement auth module\n2. Add tests",
        ]
    )


# ---------------------------------------------------------------------------
# Tracer bullet: plan.md is produced
# ---------------------------------------------------------------------------

def test_planning_phase_writes_plan_artifact(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)
    model = make_two_response_model()

    run_planning_phase(run_dir, target_project, model=model)

    assert (run_dir / "plan.md").exists()
    plan = (run_dir / "plan.md").read_text()
    assert "## Implementation Plan" in plan


# ---------------------------------------------------------------------------
# Phase transitions recorded in state.json
# ---------------------------------------------------------------------------

def test_planning_phase_advances_through_specification_and_planning(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)

    state = run_planning_phase(run_dir, target_project, model=make_two_response_model())

    assert state["phase"] == "planning"


def test_planning_phase_updates_state_timestamps(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)
    initial_state = json.loads((run_dir / "state.json").read_text())

    state = run_planning_phase(run_dir, target_project, model=make_two_response_model())

    assert state["updated_at"] >= initial_state["updated_at"]


# ---------------------------------------------------------------------------
# A2A handoff records under handoffs/
# ---------------------------------------------------------------------------

def test_planning_phase_writes_pm_to_architect_handoff(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)

    run_planning_phase(run_dir, target_project, model=make_two_response_model())

    handoff_path = run_dir / "handoffs" / "pm_to_architect.json"
    assert handoff_path.exists()
    record = json.loads(handoff_path.read_text())
    assert record["from_agent"] == "pm"
    assert record["to_agent"] == "architect"
    assert "spec.md" in record["artifacts"]
    assert record["summary"]
    assert record["timestamp"]


def test_planning_phase_writes_architect_to_pm_handoff(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)

    run_planning_phase(run_dir, target_project, model=make_two_response_model())

    handoff_path = run_dir / "handoffs" / "architect_to_pm.json"
    assert handoff_path.exists()
    record = json.loads(handoff_path.read_text())
    assert record["from_agent"] == "architect"
    assert record["to_agent"] == "pm"
    assert "plan.md" in record["artifacts"]


# ---------------------------------------------------------------------------
# Events logged to events.jsonl
# ---------------------------------------------------------------------------

def test_planning_phase_logs_phase_and_handoff_events(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)

    run_planning_phase(run_dir, target_project, model=make_two_response_model())

    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text().splitlines()
    ]
    event_types = [e["event_type"] for e in events]

    assert "phase.advanced" in event_types
    assert "handoff" in event_types
    assert "plan.created" in event_types

    phase_events = [e for e in events if e["event_type"] == "phase.advanced"]
    phases_reached = [e["payload"]["phase"] for e in phase_events]
    assert "specification" in phases_reached
    assert "planning" in phases_reached


# ---------------------------------------------------------------------------
# Target Project inspection
# ---------------------------------------------------------------------------

def test_inspect_target_project_lists_files(tmp_path: Path) -> None:
    target_project = tmp_path / "proj"
    target_project.mkdir()
    (target_project / "app.py").write_text("# app")
    (target_project / "tests").mkdir()
    (target_project / "tests" / "test_app.py").write_text("# test")

    result = inspect_target_project(target_project)

    assert "app.py" in result
    assert "test_app.py" in result


def test_inspect_target_project_excludes_hidden_dirs(tmp_path: Path) -> None:
    target_project = tmp_path / "proj"
    target_project.mkdir()
    (target_project / ".git").mkdir()
    (target_project / ".git" / "config").write_text("hidden")
    (target_project / "main.py").write_text("visible")

    result = inspect_target_project(target_project)

    assert "main.py" in result
    assert ".git" not in result


def test_planning_phase_includes_inspection_in_plan_context(tmp_path: Path) -> None:
    run_dir, target_project = make_approved_run(tmp_path)

    class InspectionCapturingLlm(FakeLlm):
        captured_context: list[str] = []

        async def generate_content_async(self, llm_request, stream=False):
            if llm_request.contents:
                for content in llm_request.contents:
                    if content.parts:
                        for part in content.parts:
                            if hasattr(part, "text") and part.text:
                                self.captured_context.append(part.text)
            async for event in super().generate_content_async(llm_request, stream):
                yield event

    capturing_model = InspectionCapturingLlm(
        responses=[
            "Spec confirmed.",
            "## Plan\n\nBased on inspection findings.",
        ]
    )

    run_planning_phase(run_dir, target_project, model=capturing_model)

    full_context = "\n".join(capturing_model.captured_context)
    assert "main.py" in full_context or "README.md" in full_context


# ---------------------------------------------------------------------------
# CLI: resume triggers planning on approved run
# ---------------------------------------------------------------------------

def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path
    env["AI_TEAM_TEST_MODEL"] = "fake"
    return subprocess.run(
        [sys.executable, "-m", "ai_software_team.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_resume_advances_approved_run_to_planning_phase(tmp_path: Path) -> None:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# My Project")

    start_result = run_cli(
        [
            "start",
            "--target-project", str(target_project),
            "--product-slice", "Add auth",
            "--user-goal", "Users need login",
            "--acceptance-criteria", "Can log in",
            "--constraint", "Keep stack",
            "--approve",
        ],
        cwd=tmp_path,
    )
    assert start_result.returncode == 0, start_result.stderr

    runs_root = target_project / ".ai-team" / "runs"
    run_dirs = list(p for p in runs_root.iterdir() if p.is_dir())
    run_id = run_dirs[0].name

    resume_result = run_cli(
        ["resume", run_id, "--target-project", str(target_project)],
        cwd=tmp_path,
    )

    assert resume_result.returncode == 0, resume_result.stderr
    assert "planning" in resume_result.stdout

    state = json.loads((runs_root / run_id / "state.json").read_text())
    assert state["phase"] == "planning"
    assert (runs_root / run_id / "plan.md").exists()
