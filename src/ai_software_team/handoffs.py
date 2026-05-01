from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ai_software_team.runs import append_event, timestamp


@dataclass
class HandoffRecord:
    from_agent: str
    to_agent: str
    summary: str
    artifacts: list[str]
    timestamp: str


def write_handoff(run_dir: Path, record: HandoffRecord) -> None:
    """Write an A2A handoff record to handoffs/ and log an event."""
    handoffs_dir = run_dir / "handoffs"
    handoffs_dir.mkdir(exist_ok=True)

    filename = f"{record.from_agent}_to_{record.to_agent}.json"
    (handoffs_dir / filename).write_text(
        json.dumps(asdict(record), indent=2, sort_keys=True) + "\n"
    )

    append_event(
        run_dir,
        "handoff",
        {
            "from_agent": record.from_agent,
            "to_agent": record.to_agent,
            "artifacts": record.artifacts,
        },
    )
