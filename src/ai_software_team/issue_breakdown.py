"""Issue Breakdown phase: builds Slice Issue + optional child issues from spec/plan."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai_software_team.github_adapter import CreatedIssue, GitHubAdapter
from ai_software_team.handoffs import HandoffRecord, write_handoff
from ai_software_team.runs import advance_phase, append_event, timestamp, write_json


PHASE_ISSUE_BREAKDOWN = "issue_breakdown"


@dataclass(frozen=True)
class IssueProposal:
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    kind: str = "slice"  # "slice" or "child"


def propose_issues(
    spec_content: str,
    plan_content: str,
    include_child_issues: bool = False,
) -> list[IssueProposal]:
    """Build proposals for one Slice Issue and optional child issues.

    The Slice Issue summarizes the Product Slice from ``spec.md``. Child issues
    are produced only when ``include_child_issues`` is set and the plan exposes
    multiple, clearly distinct tasks.
    """
    slice_proposal = _slice_issue_proposal(spec_content, plan_content)
    proposals = [slice_proposal]

    if include_child_issues:
        tasks = _extract_plan_tasks(plan_content)
        if len(tasks) >= 2:
            for task in tasks:
                proposals.append(
                    IssueProposal(
                        title=task,
                        body=_child_issue_body(task, slice_proposal.title),
                        labels=["ai-software-team", "task"],
                        kind="child",
                    )
                )

    return proposals


def run_issue_breakdown_phase(
    run_dir: Path,
    adapter: GitHubAdapter,
    include_child_issues: bool = False,
) -> dict[str, Any]:
    """Execute the Issue Breakdown phase.

    Caller must have already verified ``state.approval.issue_breakdown_approved``
    is True. Creates issues via ``adapter``, writes ``issues.md``, and persists
    issue identifiers in ``state.json``.
    """
    spec_content = (run_dir / "spec.md").read_text()
    plan_content = (run_dir / "plan.md").read_text()

    proposals = propose_issues(spec_content, plan_content, include_child_issues)

    advance_phase(run_dir, PHASE_ISSUE_BREAKDOWN)
    append_event(run_dir, "agent.invoked", {"agent": "pm_agent", "phase": "issue_breakdown"})

    created: list[tuple[IssueProposal, CreatedIssue]] = []
    for proposal in proposals:
        issue = adapter.create_issue(
            title=proposal.title,
            body=proposal.body,
            labels=proposal.labels,
        )
        created.append((proposal, issue))
        append_event(
            run_dir,
            "issue.created",
            {
                "kind": proposal.kind,
                "number": issue.number,
                "url": issue.url,
                "title": issue.title,
            },
        )

    _write_issues_artifact(run_dir / "issues.md", created)
    append_event(run_dir, "issues.summary_written", {"artifact": "issues.md"})

    write_handoff(
        run_dir,
        HandoffRecord(
            from_agent="pm",
            to_agent="developer",
            summary="Issue breakdown complete. See issues.md for tracking links.",
            artifacts=["issues.md", "plan.md"],
            timestamp=timestamp(),
        ),
    )

    state = _persist_issue_links(run_dir, created)
    return state


def _slice_issue_proposal(spec_content: str, plan_content: str) -> IssueProposal:
    title = _slice_issue_title(spec_content)
    body = _slice_issue_body(spec_content, plan_content)
    return IssueProposal(
        title=title,
        body=body,
        labels=["ai-software-team", "slice"],
        kind="slice",
    )


def _slice_issue_title(spec_content: str) -> str:
    slice_text = _section(spec_content, "Product Slice").strip()
    if slice_text:
        first_line = slice_text.splitlines()[0].strip().lstrip("-").strip()
        if first_line:
            return f"Slice: {first_line}"
    return "Slice: Product Slice"


def _slice_issue_body(spec_content: str, plan_content: str) -> str:
    user_goal = _section(spec_content, "User Goal").strip() or "_See spec.md_"
    acceptance = _section(spec_content, "Acceptance Criteria").strip() or "_See spec.md_"
    constraints = _section(spec_content, "Constraints").strip() or "_See spec.md_"

    return "\n".join(
        [
            "## Product Slice",
            _section(spec_content, "Product Slice").strip() or "_See spec.md_",
            "",
            "## User Goal",
            user_goal,
            "",
            "## Acceptance Criteria",
            acceptance,
            "",
            "## Constraints",
            constraints,
            "",
            "## Implementation Plan Reference",
            "See `plan.md` in the run artifacts for the full Implementation Plan.",
            "",
            "_Tracked by the AI Software Team._",
        ]
    )


def _child_issue_body(task: str, parent_title: str) -> str:
    return "\n".join(
        [
            f"Child task for **{parent_title}**.",
            "",
            "## Task",
            task,
            "",
            "_See parent issue and `plan.md` for full context._",
        ]
    )


def _extract_plan_tasks(plan_content: str) -> list[str]:
    """Extract numbered or bulleted task lines from the plan's Tasks section."""
    section = _section(plan_content, "Tasks") or _section(plan_content, "Task Breakdown")
    if not section:
        return []
    tasks: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(?:\d+\.\s+|-\s+|\*\s+)(.+)$", line)
        if match:
            tasks.append(match.group(1).strip())
    return tasks


def _section(markdown: str, heading: str) -> str:
    """Return the text under a markdown heading until the next heading of equal-or-shallower depth."""
    pattern = re.compile(
        rf"^(#{{1,6}})\s+{re.escape(heading)}\s*$", re.MULTILINE
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    depth = len(match.group(1))
    start = match.end()
    next_heading = re.compile(rf"^#{{1,{depth}}}\s+", re.MULTILINE)
    next_match = next_heading.search(markdown, pos=start)
    end = next_match.start() if next_match else len(markdown)
    return markdown[start:end].strip()


def _write_issues_artifact(
    path: Path, created: list[tuple[IssueProposal, CreatedIssue]]
) -> None:
    lines = ["# Issues", ""]
    slice_entries = [(p, i) for p, i in created if p.kind == "slice"]
    child_entries = [(p, i) for p, i in created if p.kind == "child"]

    if slice_entries:
        lines.append("## Slice Issue")
        for proposal, issue in slice_entries:
            lines.append(f"- [#{issue.number} {issue.title}]({issue.url})")
        lines.append("")

    if child_entries:
        lines.append("## Child Issues")
        for proposal, issue in child_entries:
            lines.append(f"- [#{issue.number} {issue.title}]({issue.url})")
        lines.append("")

    path.write_text("\n".join(lines))


def _persist_issue_links(
    run_dir: Path, created: list[tuple[IssueProposal, CreatedIssue]]
) -> dict[str, Any]:
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text())
    state["github"] = {
        "issues": [
            {
                "kind": proposal.kind,
                "number": issue.number,
                "url": issue.url,
                "title": issue.title,
            }
            for proposal, issue in created
        ],
    }
    state["updated_at"] = timestamp()
    write_json(state_path, state)
    return state


__all__ = [
    "IssueProposal",
    "PHASE_ISSUE_BREAKDOWN",
    "propose_issues",
    "run_issue_breakdown_phase",
]
