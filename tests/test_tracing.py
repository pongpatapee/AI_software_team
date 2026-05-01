from ai_software_team import tracing
from ai_software_team.tracing import SystemTracer


def test_langfuse_client_creation_failure_disables_tracing(monkeypatch) -> None:
    class BrokenLangfuse:
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("invalid Langfuse configuration")

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "secret-key")
    monkeypatch.setattr(tracing, "Langfuse", BrokenLangfuse)

    with SystemTracer() as tracer:
        tracer.event("pm.discovery.started", {"run_id": "run-test"})
