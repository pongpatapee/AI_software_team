"""Milestone 3: GitHub issue breakdown."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ai_software_team.github_adapter import (
    RecordingGitHubAdapter,
    adapter_from_env,
)
from ai_software_team.issue_breakdown import (
    PHASE_ISSUE_BREAKDOWN,
    propose_issues,
    run_issue_breakdown_phase,
)
from ai_software_team.orchestration import run_planning_phase
from ai_software_team.runs import DiscoveryAnswers, start_run

from tests.test_milestone2_planning import make_two_response_model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_run_through_planning(tmp_path: Path) -> tuple[Path, Path]:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# Sample\n")
    (target_project / "main.py").write_text("def main(): pass\n")

    state = start_run(
        DiscoveryAnswers(
            target_project=target_project,
            product_slice="Add saved reports page",
            user_goal="Let users revisit reports",
            acceptance_criteria=["Users can list and open saved reports"],
            constraints=["Keep existing stack"],
            approved=True,
        )
    )
    run_dir = target_project / ".ai-team" / "runs" / state["run_id"]
    run_planning_phase(run_dir, target_project, model=make_two_response_model())
    return run_dir, target_project


# ---------------------------------------------------------------------------
# Adapter resolution
# ---------------------------------------------------------------------------


def test_adapter_from_env_returns_recording_adapter_when_fake() -> None:
    adapter = adapter_from_env({"AI_TEAM_GITHUB_ADAPTER": "fake"})
    assert isinstance(adapter, RecordingGitHubAdapter)


def test_recording_adapter_records_calls_and_returns_synthetic_url() -> None:
    adapter = RecordingGitHubAdapter(repo="acme/widgets")
    issue = adapter.create_issue("title", "body", labels=["slice"])
    assert issue.url.startswith("https://github.com/acme/widgets/issues/")
    assert issue.number > 0
    assert adapter.calls == [{"title": "title", "body": "body", "labels": ["slice"]}]


# ---------------------------------------------------------------------------
# Proposal builder
# ---------------------------------------------------------------------------


def test_propose_issues_returns_single_slice_issue_by_default() -> None:
    spec = (
        "# Product Slice Spec\n\n"
        "## Product Slice\nAdd saved reports page\n\n"
        "## User Goal\nUsers want to revisit reports\n\n"
        "## Acceptance Criteria\n- Users can list reports\n\n"
        "## Constraints\n- Keep stack\n"
    )
    plan = "# Plan\n\n## Tasks\n1. Build it\n2. Test it\n"

    proposals = propose_issues(spec, plan)

    assert len(proposals) == 1
    assert proposals[0].kind == "slice"
    assert "Add saved reports page" in proposals[0].title


def test_propose_issues_adds_child_issues_when_requested() -> None:
    spec = (
        "## Product Slice\nFeature\n\n"
        "## User Goal\nGoal\n\n"
        "## Acceptance Criteria\n- Done\n\n"
        "## Constraints\n- Stack\n"
    )
    plan = "## Tasks\n1. Build the API\n2. Build the UI\n"

    proposals = propose_issues(spec, plan, include_child_issues=True)

    kinds = [p.kind for p in proposals]
    titles = [p.title for p in proposals]
    assert kinds.count("slice") == 1
    assert kinds.count("child") == 2
    assert "Build the API" in titles
    assert "Build the UI" in titles


def test_propose_issues_skips_child_issues_when_only_one_task() -> None:
    spec = (
        "## Product Slice\nFeature\n\n"
        "## User Goal\nGoal\n\n"
        "## Acceptance Criteria\n- Done\n\n"
        "## Constraints\n- Stack\n"
    )
    plan = "## Tasks\n1. Single task\n"

    proposals = propose_issues(spec, plan, include_child_issues=True)

    assert all(p.kind == "slice" for p in proposals)


# ---------------------------------------------------------------------------
# Phase orchestration: artifacts, state, events
# ---------------------------------------------------------------------------


def test_issue_breakdown_phase_creates_slice_issue_via_adapter(tmp_path: Path) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    adapter = RecordingGitHubAdapter(repo="acme/widgets")

    state = run_issue_breakdown_phase(run_dir, adapter=adapter)

    assert state["phase"] == PHASE_ISSUE_BREAKDOWN
    assert len(adapter.calls) == 1
    assert "saved reports" in adapter.calls[0]["title"].lower()


def test_issue_breakdown_phase_persists_issue_links_in_state(tmp_path: Path) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    adapter = RecordingGitHubAdapter(repo="acme/widgets")

    state = run_issue_breakdown_phase(run_dir, adapter=adapter)

    issues = state["github"]["issues"]
    assert len(issues) == 1
    assert issues[0]["kind"] == "slice"
    assert issues[0]["url"].startswith("https://github.com/acme/widgets/issues/")
    assert isinstance(issues[0]["number"], int)


def test_issue_breakdown_phase_writes_issues_md(tmp_path: Path) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    adapter = RecordingGitHubAdapter(repo="acme/widgets")

    run_issue_breakdown_phase(run_dir, adapter=adapter)

    issues_md = (run_dir / "issues.md").read_text()
    assert "# Issues" in issues_md
    assert "## Slice Issue" in issues_md
    assert "https://github.com/acme/widgets/issues/" in issues_md


def test_issue_breakdown_phase_logs_phase_and_issue_events(tmp_path: Path) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    adapter = RecordingGitHubAdapter()

    run_issue_breakdown_phase(run_dir, adapter=adapter)

    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text().splitlines()
    ]
    event_types = [e["event_type"] for e in events]

    assert "phase.advanced" in event_types
    assert "issue.created" in event_types
    assert "issues.summary_written" in event_types
    assert any(
        e["event_type"] == "phase.advanced"
        and e["payload"]["phase"] == PHASE_ISSUE_BREAKDOWN
        for e in events
    )


def test_issue_breakdown_phase_writes_pm_to_developer_handoff(tmp_path: Path) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    adapter = RecordingGitHubAdapter()

    run_issue_breakdown_phase(run_dir, adapter=adapter)

    handoff = json.loads(
        (run_dir / "handoffs" / "pm_to_developer.json").read_text()
    )
    assert handoff["from_agent"] == "pm"
    assert handoff["to_agent"] == "developer"
    assert "issues.md" in handoff["artifacts"]


def test_issue_breakdown_phase_creates_child_issues_when_enabled(
    tmp_path: Path,
) -> None:
    run_dir, _ = make_run_through_planning(tmp_path)
    # Replace plan.md with a multi-task plan to trigger child issues.
    (run_dir / "plan.md").write_text(
        "# Plan\n\n## Tasks\n1. First task\n2. Second task\n"
    )
    adapter = RecordingGitHubAdapter()

    state = run_issue_breakdown_phase(
        run_dir, adapter=adapter, include_child_issues=True
    )

    kinds = [issue["kind"] for issue in state["github"]["issues"]]
    assert kinds.count("slice") == 1
    assert kinds.count("child") == 2


# ---------------------------------------------------------------------------
# CLI: approval checkpoint and issue creation
# ---------------------------------------------------------------------------


def run_cli(
    args: list[str], cwd: Path, env_overrides: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path
    env["AI_TEAM_TEST_MODEL"] = "fake"
    env["AI_TEAM_GITHUB_ADAPTER"] = "fake"
    env["AI_TEAM_GITHUB_FAKE_REPO"] = "acme/widgets"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "ai_software_team.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def start_run_via_cli(target_project: Path, cwd: Path) -> str:
    result = run_cli(
        [
            "start",
            "--target-project", str(target_project),
            "--product-slice", "Add saved reports page",
            "--user-goal", "Users want saved reports",
            "--acceptance-criteria", "List saved reports",
            "--constraint", "Keep stack",
            "--approve",
        ],
        cwd=cwd,
    )
    assert result.returncode == 0, result.stderr
    runs_root = target_project / ".ai-team" / "runs"
    return next(p for p in runs_root.iterdir() if p.is_dir()).name


def test_resume_without_issue_approval_stays_at_planning_with_prompt(
    tmp_path: Path,
) -> None:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# Sample\n")
    run_id = start_run_via_cli(target_project, tmp_path)

    result = run_cli(
        ["resume", run_id, "--target-project", str(target_project)],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "Current phase: planning" in result.stdout
    assert "--approve-issues" in result.stdout

    state = json.loads(
        (target_project / ".ai-team" / "runs" / run_id / "state.json").read_text()
    )
    assert state["phase"] == "planning"
    assert "github" not in state


def test_resume_with_approve_issues_creates_issues_and_advances_phase(
    tmp_path: Path,
) -> None:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# Sample\n")
    run_id = start_run_via_cli(target_project, tmp_path)

    # First resume: planning only
    run_cli(
        ["resume", run_id, "--target-project", str(target_project)],
        cwd=tmp_path,
    )

    # Second resume: approve issues
    result = run_cli(
        [
            "resume", run_id,
            "--target-project", str(target_project),
            "--approve-issues",
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert f"Current phase: {PHASE_ISSUE_BREAKDOWN}" in result.stdout

    run_dir = target_project / ".ai-team" / "runs" / run_id
    state = json.loads((run_dir / "state.json").read_text())
    assert state["phase"] == PHASE_ISSUE_BREAKDOWN
    assert state["approval"]["issue_breakdown_approved"] is True
    assert state["github"]["issues"]
    assert state["github"]["issues"][0]["url"].startswith(
        "https://github.com/acme/widgets/issues/"
    )

    issues_md = (run_dir / "issues.md").read_text()
    assert "## Slice Issue" in issues_md


def test_resume_runs_planning_and_issue_breakdown_in_one_invocation(
    tmp_path: Path,
) -> None:
    target_project = tmp_path / "target"
    target_project.mkdir()
    (target_project / "README.md").write_text("# Sample\n")
    run_id = start_run_via_cli(target_project, tmp_path)

    result = run_cli(
        [
            "resume", run_id,
            "--target-project", str(target_project),
            "--approve-issues",
        ],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    run_dir = target_project / ".ai-team" / "runs" / run_id
    state = json.loads((run_dir / "state.json").read_text())
    assert state["phase"] == PHASE_ISSUE_BREAKDOWN
    assert (run_dir / "plan.md").exists()
    assert (run_dir / "issues.md").exists()
