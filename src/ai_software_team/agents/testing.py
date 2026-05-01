from __future__ import annotations

from pydantic import PrivateAttr

from google.adk.models import LlmResponse
from google.adk.models.base_llm import BaseLlm
from google.genai import types


class FakeLlm(BaseLlm):
    """Deterministic LLM for testing. Cycles through responses in order."""

    responses: list[str] = []
    _call_index: int = PrivateAttr(default=0)

    @property
    def model(self) -> str:
        return "fake"

    async def generate_content_async(
        self, llm_request: object, stream: bool = False
    ):  # type: ignore[override]
        responses = self.responses
        idx = self._call_index
        text = responses[idx] if idx < len(responses) else (responses[-1] if responses else "")
        self._call_index += 1
        content = types.Content(role="model", parts=[types.Part(text=text)])
        yield LlmResponse(content=content, turn_complete=True)
