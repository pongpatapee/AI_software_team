from __future__ import annotations

from pathlib import Path

from google.adk.models.base_llm import BaseLlm

from ai_software_team.agents.adk import ADKAgentInvoker

_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "pm.md"

_FALLBACK_INSTRUCTION = (
    "You are the PM Agent for an AI Software Team. "
    "Your role is to confirm Product Slice Specs are complete and ready for planning. "
    "When given a spec, confirm it is clear or note any blocking ambiguities."
)


class PMAgent:
    """LLM-backed PM Agent. Confirms the Product Slice Spec before planning."""

    def __init__(self, model: str | BaseLlm) -> None:
        instruction = (
            _PROMPT_PATH.read_text() if _PROMPT_PATH.exists() else _FALLBACK_INSTRUCTION
        )
        self._invoker = ADKAgentInvoker("pm_agent", model, instruction)

    def confirm_spec(self, spec_content: str) -> str:
        """Review spec and return a brief confirmation or list of blocking ambiguities."""
        return self._invoker.invoke(
            f"Review and confirm this Product Slice Spec. "
            f"Reply with CONFIRMED if clear and complete, or list blocking ambiguities:\n\n{spec_content}"
        )
