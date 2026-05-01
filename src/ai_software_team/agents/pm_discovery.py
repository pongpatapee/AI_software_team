from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from google.adk.agents import Agent
from google.adk import Runner
from google.adk.models.base_llm import BaseLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai_software_team.runs import DiscoveryAnswers

READY_MARKER = "[READY]"

_DISCOVERY_INSTRUCTION = """\
You are the PM Agent conducting a discovery interview to define a Product Slice.

Your job is to interview the user until you have confirmed ALL of the following:
1. Product Slice — the specific feature or increment for this run
2. User goal — why this slice matters to the user
3. Acceptance criteria — concrete, testable conditions for completion (at least one)
4. Constraints — stack, cost, timeline, or non-goal limits (at least one)

Interview rules:
- Ask one focused question at a time.
- Probe for specifics if answers are vague.
- Do NOT proceed until all four fields are clear and confirmed.

When you have gathered all four fields, output your response in this exact format:

<summary of what you gathered>

```json
{
  "product_slice": "<concise feature name>",
  "user_goal": "<why it matters>",
  "acceptance_criteria": ["<criterion 1>", "<criterion 2>"],
  "constraints": ["<constraint 1>"]
}
```

""" + READY_MARKER


class MultiTurnADKSession:
    """Persistent ADK session for multi-turn agent conversation."""

    def __init__(self, name: str, model: str | BaseLlm, instruction: str) -> None:
        self._agent = Agent(name=name, model=model, instruction=instruction)
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name="ai-software-team",
            session_service=self._session_service,
        )
        self._user_id = "user"
        self._session_id: str = asyncio.run(self._create_session())

    async def _create_session(self) -> str:
        session = await self._session_service.create_session(
            app_name="ai-software-team", user_id=self._user_id
        )
        return session.id

    def send(self, message: str) -> str:
        return asyncio.run(self._send_async(message))

    async def _send_async(self, message: str) -> str:
        result = ""
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=self._session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                result = event.content.parts[0].text or ""
        return result


class PMDiscoverySession:
    """Conversational PM Agent discovery session.

    Conducts a back-and-forth interview until the Discovery Gate is satisfied,
    then signals completion via READY_MARKER and embeds answers as JSON.
    """

    def __init__(self, model: str | BaseLlm, target_project: Path) -> None:
        self._session = MultiTurnADKSession("pm_discovery", model, _DISCOVERY_INSTRUCTION)
        self._target_project = target_project
        self._last_ready_response: str | None = None

    def send(self, user_message: str) -> tuple[str, bool]:
        """Send a user message. Returns (pm_response, is_complete)."""
        raw = self._session.send(user_message)
        done = READY_MARKER in raw
        clean = raw.replace(READY_MARKER, "").strip()
        if done:
            self._last_ready_response = raw
        return clean, done

    def extract_answers(self) -> DiscoveryAnswers:
        """Parse DiscoveryAnswers from the READY response JSON block."""
        if self._last_ready_response is None:
            raise RuntimeError("Discovery not ready — call send() until done=True first.")
        data = _parse_json_block(self._last_ready_response)
        return DiscoveryAnswers(
            target_project=self._target_project,
            product_slice=data["product_slice"],
            user_goal=data["user_goal"],
            acceptance_criteria=data["acceptance_criteria"],
            constraints=data["constraints"],
            approved=False,
        )


def _parse_json_block(text: str) -> dict:
    """Extract the first ```json ... ``` block from text."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Fallback: try bare JSON object
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON block found in PM response:\n{text}")
