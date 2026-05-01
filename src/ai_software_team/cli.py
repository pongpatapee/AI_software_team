from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ai_software_team.runs import DiscoveryAnswers, load_run_state, resume_run, start_run
from ai_software_team.tracing import SystemTracer


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "start":
        return start_command(args)
    if args.command == "status":
        return status_command(args)
    if args.command == "resume":
        return resume_command(args)

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-team")
    subcommands = parser.add_subparsers(dest="command")

    start = subcommands.add_parser("start", help="Begin PM discovery for a Product Slice")
    start.add_argument("--target-project", type=Path)
    start.add_argument("--product-slice")
    start.add_argument("--user-goal")
    start.add_argument("--acceptance-criteria", action="append", default=[])
    start.add_argument("--constraint", action="append", default=[])
    start.add_argument("--approve", action="store_true")

    status = subcommands.add_parser("status", help="Show a run's current state")
    status.add_argument("--target-project", type=Path, default=Path.cwd())
    status.add_argument("--run-id")

    resume = subcommands.add_parser("resume", help="Load a resumable run")
    resume.add_argument("run_id")
    resume.add_argument("--target-project", type=Path, default=Path.cwd())

    return parser


def start_command(args: argparse.Namespace) -> int:
    if _should_use_pm_conversation(args):
        answers = run_pm_discovery_conversation(args.target_project)
    else:
        answers = collect_discovery_answers(args)

    with SystemTracer() as tracer:
        tracer.event(
            "pm.discovery.started",
            {"target_project_path": str(answers.target_project.resolve())},
        )
        state = start_run(answers)
        tracer.event("pm.discovery.spec_created", {"run_id": state["run_id"]})

    print(f"Started run {state['run_id']}")
    print(f"Run directory: {answers.target_project.resolve() / '.ai-team' / 'runs' / state['run_id']}")
    print(f"Resume with: {state['resume_command']}")
    return 0


def _should_use_pm_conversation(args: argparse.Namespace) -> bool:
    return not args.product_slice


def run_pm_discovery_conversation(target_project: Path) -> DiscoveryAnswers:
    from ai_software_team.agents.pm_discovery import PMDiscoverySession

    model = _resolve_pm_model()
    session = PMDiscoverySession(model, target_project)

    print("PM Agent: Hello! I'm here to help define your Product Slice.")
    print("PM Agent: What would you like to build?\n")

    done = False
    while not done:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        response, done = session.send(user_input)
        print(f"\nPM Agent: {response}\n")

    answers = session.extract_answers()
    print("PM Agent: Discovery complete. Creating your run...\n")
    answers = DiscoveryAnswers(
        target_project=answers.target_project,
        product_slice=answers.product_slice,
        user_goal=answers.user_goal,
        acceptance_criteria=answers.acceptance_criteria,
        constraints=answers.constraints,
        approved=True,
    )
    return answers


def status_command(args: argparse.Namespace) -> int:
    try:
        state = load_run_state(args.target_project, args.run_id)
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(format_state(state))
    return 0


def resume_command(args: argparse.Namespace) -> int:
    try:
        with SystemTracer() as tracer:
            state = resume_run(args.target_project, args.run_id)
            tracer.event("pm.run.resumed", {"run_id": state["run_id"]})

            if _should_run_planning(state):
                from ai_software_team.orchestration import run_planning_phase

                run_dir = (
                    args.target_project.resolve()
                    / ".ai-team"
                    / "runs"
                    / state["run_id"]
                )
                tracer.event("pm.planning.started", {"run_id": state["run_id"]})
                state = run_planning_phase(run_dir, args.target_project.resolve(), model=_resolve_model())
                tracer.event("pm.planning.completed", {"run_id": state["run_id"]})
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(f"Resumed run {state['run_id']}")
    print(f"Current phase: {state['phase']}")
    print(f"Status: {state['status']}")
    return 0


def _should_run_planning(state: dict) -> bool:
    return (
        state.get("phase") == "discovery"
        and state.get("approval", {}).get("discovery_gate_approved", False)
    )


def _resolve_model():
    """Return a model for planning agents. Supports AI_TEAM_TEST_MODEL=fake for tests."""
    if os.getenv("AI_TEAM_TEST_MODEL") == "fake":
        from ai_software_team.agents.testing import FakeLlm

        return FakeLlm(
            responses=[
                "Spec confirmed. Requirements are clear.",
                "## Implementation Plan\n\n### Tasks\n1. Implement the requested changes.",
            ]
        )
    return os.getenv("AI_TEAM_MODEL", "gemini-2.0-flash")


def _resolve_pm_model():
    """Return a model for the PM discovery conversation."""
    if os.getenv("AI_TEAM_TEST_MODEL") == "fake":
        from ai_software_team.agents.testing import FakeLlm

        raw_responses = os.getenv("AI_TEAM_TEST_PM_RESPONSES", "")
        responses = [raw_responses] if raw_responses else ["[READY]"]
        return FakeLlm(responses=responses)
    return os.getenv("AI_TEAM_MODEL", "gemini-2.0-flash")


def format_state(state: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Run ID: {state['run_id']}",
            f"Phase: {state['phase']}",
            f"Status: {state['status']}",
            f"Target Project: {state['target_project_path']}",
            f"Resumable: {state['resumable']}",
            f"Updated At: {state['updated_at']}",
        ]
    )


def collect_discovery_answers(args: argparse.Namespace) -> DiscoveryAnswers:
    target_project = args.target_project or Path(prompt_required("Target Project path"))
    product_slice = args.product_slice or prompt_required("Product Slice")
    user_goal = args.user_goal or prompt_required("User goal")
    acceptance_criteria = args.acceptance_criteria or [
        prompt_required("Acceptance criterion")
    ]
    constraints = args.constraint or [prompt_required("Constraint")]
    approved = args.approve or prompt_yes_no("Approve this Product Slice Spec?")

    return DiscoveryAnswers(
        target_project=target_project,
        product_slice=product_slice,
        user_goal=user_goal,
        acceptance_criteria=acceptance_criteria,
        constraints=constraints,
        approved=approved,
    )


def prompt_required(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise SystemExit(f"{label} is required.")
    return value


def prompt_yes_no(label: str) -> bool:
    value = input(f"{label} [y/N]: ").strip().lower()
    return value in {"y", "yes"}


if __name__ == "__main__":
    sys.exit(main())

