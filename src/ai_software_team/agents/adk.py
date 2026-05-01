from __future__ import annotations

import asyncio
from typing import Any

from google.adk.agents import Agent
from google.adk import Runner
from google.adk.models.base_llm import BaseLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types


class ADKAgentInvoker:
    """Single-turn ADK agent runner. Wraps google-adk for sequential invocations."""

    def __init__(
        self,
        name: str,
        model: str | BaseLlm,
        instruction: str,
        tools: list[Any] | None = None,
    ) -> None:
        self._agent = Agent(name=name, model=model, instruction=instruction, tools=tools or [])
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name="ai-software-team",
            session_service=self._session_service,
        )

    def invoke(self, context: str) -> str:
        return asyncio.run(self._run_async(context))

    async def _run_async(self, context: str) -> str:
        session = await self._session_service.create_session(
            app_name="ai-software-team", user_id="runner"
        )
        result = ""
        async for event in self._runner.run_async(
            user_id="runner",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=context)]),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                result = event.content.parts[0].text or ""
        return result
