from __future__ import annotations

from pathlib import Path

from google.adk.models.base_llm import BaseLlm

from ai_software_team.agents.adk import ADKAgentInvoker

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "architect.md"

_FALLBACK_INSTRUCTION = (
    "You are the Architect Agent for an AI Software Team. "
    "Your role is to analyze the Target Project and produce an Implementation Plan. "
    "Given a spec and file inspection results, write plan.md with: "
    "findings, proposed approach, likely file changes, task breakdown, risks, and validation plan."
)


class ArchitectAgent:
    """LLM-backed Architect Agent. Produces an Implementation Plan from spec and inspection."""

    def __init__(self, model: str | BaseLlm) -> None:
        instruction = (
            _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else _FALLBACK_INSTRUCTION
        )
        self._invoker = ADKAgentInvoker("architect_agent", model, instruction)

    def create_plan(self, spec_content: str, inspection: str) -> str:
        """Produce an Implementation Plan from the spec and Target Project inspection."""
        return self._invoker.invoke(
            f"Create an Implementation Plan for this Product Slice.\n\n"
            f"## Spec\n{spec_content}\n\n"
            f"## Target Project Inspection\n{inspection}"
        )
