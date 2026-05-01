from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RUNS_ROOT = Path(".ai-team") / "runs"


@dataclass(frozen=True)
class DiscoveryAnswers:
    target_project: Path
    product_slice: str
    user_goal: str
    acceptance_criteria: list[str]
    constraints: list[str]
    approved: bool


def start_run(answers: DiscoveryAnswers) -> dict[str, Any]:
    target_project = answers.target_project.resolve()
    run_id = new_run_id()
    run_dir = target_project / RUNS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    now = timestamp()
    state = {
        "run_id": run_id,
        "phase": "discovery",
        "status": "waiting_for_resume",
        "target_project_path": str(target_project),
        "created_at": now,
        "updated_at": now,
        "resumable": True,
        "resume_command": f"ai-team resume {run_id}",
        "approval": {
            "discovery_gate_approved": answers.approved,
        },
    }

    write_json(run_dir / "state.json", state)
    append_event(run_dir, "run.started", {"phase": "discovery"})
    write_spec(run_dir / "spec.md", answers)
    append_event(run_dir, "spec.created", {"artifact": "spec.md"})
    return state


def load_run_state(target_project: Path, run_id: str | None = None) -> dict[str, Any]:
    run_dir = resolve_run_dir(target_project, run_id)
    return json.loads((run_dir / "state.json").read_text())


def resume_run(target_project: Path, run_id: str) -> dict[str, Any]:
    run_dir = resolve_run_dir(target_project, run_id)
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text())
    state["updated_at"] = timestamp()
    write_json(state_path, state)
    append_event(run_dir, "run.resumed", {"phase": state["phase"]})
    return state


def resolve_run_dir(target_project: Path, run_id: str | None = None) -> Path:
    runs_root = target_project.resolve() / RUNS_ROOT
    if run_id is not None:
        run_dir = runs_root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run {run_id} was not found in {runs_root}.")
        return run_dir

    run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No runs were found in {runs_root}.")
    return sorted(run_dirs)[-1]


def new_run_id() -> str:
    return f"run-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def advance_phase(run_dir: Path, new_phase: str) -> None:
    """Update state.json to new_phase and log a phase.advanced event."""
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text())
    state["phase"] = new_phase
    state["updated_at"] = timestamp()
    write_json(state_path, state)
    append_event(run_dir, "phase.advanced", {"phase": new_phase})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def append_event(run_dir: Path, event_type: str, payload: dict[str, Any]) -> None:
    event = {
        "timestamp": timestamp(),
        "event_type": event_type,
        "payload": payload,
    }
    with (run_dir / "events.jsonl").open("a") as event_file:
        event_file.write(json.dumps(event, sort_keys=True) + "\n")


def write_spec(path: Path, answers: DiscoveryAnswers) -> None:
    acceptance = "\n".join(f"- {item}" for item in answers.acceptance_criteria)
    constraints = "\n".join(f"- {item}" for item in answers.constraints)
    path.write_text(
        "\n".join(
            [
                "# Product Slice Spec",
                "",
                "## Target Project",
                str(answers.target_project.resolve()),
                "",
                "## Product Slice",
                answers.product_slice,
                "",
                "## User Goal",
                answers.user_goal,
                "",
                "## Acceptance Criteria",
                acceptance or "- None recorded",
                "",
                "## Constraints",
                constraints or "- None recorded",
                "",
                "## Open Questions",
                "- None",
                "",
            ]
        )
    )

