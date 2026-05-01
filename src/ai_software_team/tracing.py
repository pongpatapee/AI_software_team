from __future__ import annotations

import os
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any

from langfuse import Langfuse


class SystemTracer(AbstractContextManager["SystemTracer"]):
    """Optional Langfuse bridge for AI Software Team System events."""

    def __init__(self) -> None:
        self._enabled = bool(
            os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
        )
        self._client: Any | None = None
        self._trace: Any | None = None

        if not self._enabled:
            return

        try:
            self._client = Langfuse(host=os.getenv("LANGFUSE_HOST"))
        except Exception:
            self._enabled = False

    def __enter__(self) -> "SystemTracer":
        if self._client is not None:
            self._trace = self._client.trace(name="ai-software-team")
        return self

    def event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        if self._trace is None:
            return
        self._trace.event(name=name, metadata=metadata or {})

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._client is not None:
            self._client.flush()

