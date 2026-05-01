from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.adk.models.base_llm import BaseLlm

from ai_software_team.agents.architect import ArchitectAgent
from ai_software_team.agents.pm import PMAgent
from ai_software_team.handoffs import HandoffRecord, write_handoff
from ai_software_team.inspection import inspect_target_project
from ai_software_team.runs import advance_phase, append_event, timestamp

DEFAULT_MODEL = "gemini-2.0-flash"


def run_planning_phase(
    run_dir: Path,
    target_project: Path,
    model: str | BaseLlm = DEFAULT_MODEL,
) -> dict[str, Any]:
    """
    Orchestrate Discovery → Specification → Planning phases.

    Writes:
      - handoffs/pm_to_architect.json  (A2A: PM → Architect)
      - handoffs/architect_to_pm.json  (A2A: Architect → PM)
      - plan.md
      - Updated state.json (phase=planning)
    """
    spec_content = (run_dir / "spec.md").read_text()
    inspection = inspect_target_project(target_project)

    # Specification phase
    advance_phase(run_dir, "specification")
    pm_agent = PMAgent(model)
    pm_confirmation = pm_agent.confirm_spec(spec_content)
    append_event(run_dir, "agent.invoked", {"agent": "pm_agent", "phase": "specification"})

    write_handoff(
        run_dir,
        HandoffRecord(
            from_agent="pm",
            to_agent="architect",
            summary=pm_confirmation,
            artifacts=["spec.md"],
            timestamp=timestamp(),
        ),
    )

    # Planning phase
    advance_phase(run_dir, "planning")
    architect_agent = ArchitectAgent(model)
    plan_content = architect_agent.create_plan(spec_content, inspection)
    append_event(run_dir, "agent.invoked", {"agent": "architect_agent", "phase": "planning"})

    (run_dir / "plan.md").write_text(plan_content)
    append_event(run_dir, "plan.created", {"artifact": "plan.md"})

    write_handoff(
        run_dir,
        HandoffRecord(
            from_agent="architect",
            to_agent="pm",
            summary="Planning complete. See plan.md for implementation details.",
            artifacts=["plan.md"],
            timestamp=timestamp(),
        ),
    )

    return json.loads((run_dir / "state.json").read_text())
