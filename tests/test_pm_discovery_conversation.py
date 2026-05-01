"""PM Agent conversational discovery — Milestone 2 gap."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ai_software_team.agents.testing import FakeLlm
from ai_software_team.agents.pm_discovery import PMDiscoverySession, READY_MARKER


def run_cli(
    args: list[str],
    cwd: Path,
    stdin: str = "",
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "ai_software_team.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        input=stdin,
        capture_output=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Tracer bullet: session sends messages and receives responses
# ---------------------------------------------------------------------------

def test_pm_discovery_session_returns_response_on_send(tmp_path: Path) -> None:
    model = FakeLlm(responses=["What product slice do you want to build?"])
    session = PMDiscoverySession(model, tmp_path / "project")

    response, done = session.send("hi")

    assert "What product slice" in response
    assert done is False


# ---------------------------------------------------------------------------
# READY signal detection
# ---------------------------------------------------------------------------

def test_pm_discovery_session_signals_done_when_ready_marker_present(tmp_path: Path) -> None:
    ready_response = f"I have everything I need. {READY_MARKER}"
    model = FakeLlm(responses=["Tell me more.", ready_response])
    session = PMDiscoverySession(model, tmp_path / "project")

    _, done1 = session.send("Add auth")
    _, done2 = session.send("Users need login")

    assert done1 is False
    assert done2 is True


def test_pm_discovery_session_strips_ready_marker_from_response(tmp_path: Path) -> None:
    model = FakeLlm(responses=[f"All done! {READY_MARKER}"])
    session = PMDiscoverySession(model, tmp_path / "project")

    response, _ = session.send("hi")

    assert READY_MARKER not in response
    assert "All done!" in response


# ---------------------------------------------------------------------------
# Answer extraction from READY response
# ---------------------------------------------------------------------------

READY_JSON_RESPONSE = f"""I have all the information needed to create the spec.

```json
{{
  "product_slice": "Add user authentication",
  "user_goal": "Users need to log in securely",
  "acceptance_criteria": ["Users can register", "Users can log in with JWT"],
  "constraints": ["Use existing Python stack", "No new dependencies"]
}}
```

{READY_MARKER}"""


def test_pm_discovery_session_extracts_answers_after_ready(tmp_path: Path) -> None:
    target_project = tmp_path / "project"
    target_project.mkdir()
    model = FakeLlm(responses=[READY_JSON_RESPONSE])
    session = PMDiscoverySession(model, target_project)

    session.send("Add user authentication to my app")
    answers = session.extract_answers()

    assert answers.product_slice == "Add user authentication"
    assert answers.user_goal == "Users need to log in securely"
    assert "Users can register" in answers.acceptance_criteria
    assert "Use existing Python stack" in answers.constraints
    assert answers.target_project == target_project


def test_pm_discovery_session_extract_raises_if_not_ready(tmp_path: Path) -> None:
    model = FakeLlm(responses=["Tell me more about your project."])
    session = PMDiscoverySession(model, tmp_path / "project")
    session.send("Something")

    try:
        session.extract_answers()
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "not ready" in str(e).lower()


# ---------------------------------------------------------------------------
# CLI: start without --product-slice triggers PM conversation
# ---------------------------------------------------------------------------

def _fake_ready_response() -> str:
    data = {
        "product_slice": "Add health check endpoint",
        "user_goal": "Need /health for monitoring",
        "acceptance_criteria": ["GET /health returns 200"],
        "constraints": ["Keep existing stack"],
    }
    return f"Great, here is the spec:\n\n```json\n{json.dumps(data, indent=2)}\n```\n\n{READY_MARKER}"


def test_cli_start_without_flags_runs_pm_conversation_and_creates_run(tmp_path: Path) -> None:
    target_project = tmp_path / "target"
    target_project.mkdir()

    # User types one message; fake PM immediately signals READY with JSON answers
    user_input = "Add a health check endpoint for monitoring\n"

    result = run_cli(
        ["start", "--target-project", str(target_project)],
        cwd=tmp_path,
        stdin=user_input,
        env_overrides={
            "AI_TEAM_TEST_MODEL": "fake",
            "AI_TEAM_TEST_PM_RESPONSES": _fake_ready_response(),
        },
    )

    assert result.returncode == 0, result.stderr
    assert "Started run" in result.stdout

    runs_root = target_project / ".ai-team" / "runs"
    run_dirs = [p for p in runs_root.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1

    spec = (run_dirs[0] / "spec.md").read_text()
    assert "Add health check endpoint" in spec
