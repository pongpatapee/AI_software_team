# Agent Guidance

## Read First

- Read `CONTEXT.md` before making product or architecture changes. Use its domain terms consistently.
- Read `docs/spec_v1.md` before implementing v1 behavior.
- Read `docs/adr/` for accepted architecture decisions. Do not contradict ADRs without proposing a new ADR.

## Project Shape

- This repository contains the **AI Software Team System**, not a generated **Target Project**.
- The system is a `uv`-managed Python CLI package exposed as `ai-team`.
- Keep v1 focused on the documented milestones. Do not implement future-scope features unless explicitly requested.
- Preserve the distinction between local run artifacts, run state, target-project code, and Langfuse tracing.

## Python Conventions

- Put all imports at the top of the file. Do not import inside functions unless there is a documented reason such as an optional dependency fallback.
- Prefer small, typed functions with explicit inputs and return values.
- Use `pathlib.Path` for filesystem paths.
- Use dataclasses or typed structures for domain data when they make state clearer.
- Keep side effects near orchestration edges. Prefer pure helpers for formatting, path resolution, and serialization.
- Avoid broad `except Exception` blocks unless isolating an optional integration; if used, keep the fallback explicit and narrow.

## Codebase Design

- Use the architecture vocabulary from `/improve-codebase-architecture`: **Module**, **Interface**, **Implementation**, **Depth**, **Seam**, **Adapter**, **Leverage**, and **Locality**.
- Prefer **deep** Modules: a small Interface should hide meaningful behavior and give callers Leverage.
- Avoid shallow pass-through Modules. Apply the deletion test: if deleting a Module makes complexity vanish instead of reappearing across callers, the Module was not earning its keep.
- Treat the Interface as the test surface. Tests should usually cross the same Seam as callers rather than reaching into Implementation details.
- Do not introduce a Seam just because something might vary later. One Adapter is usually hypothetical; two Adapters make the Seam real.
- Preserve Locality: keep related state transitions, validation, serialization, and error handling close to the Module that owns the behavior.
- Use explicit Adapters for external systems such as Langfuse, GitHub, shell commands, filesystem writes, and future MCP tools.
- Do not use "component", "service", "API", or "boundary" when giving architecture guidance; use the vocabulary above.

## Testing

- Use `pytest` for this repository's test suite.
- Add or update tests for behavior changes, especially CLI behavior, run state, event logging, and artifact generation.
- Keep tests local and deterministic. Do not require real GitHub, Langfuse, or network access for the default test suite.
- When testing CLI behavior, assert both exit codes and user-visible output.

## CLI And Run Artifacts

- CLI commands should be predictable and resumable.
- Store run artifacts under `.ai-team/runs/<run-id>/` in the Target Project.
- Store machine-readable run state in `state.json`.
- Store local observability events in `events.jsonl`.
- Markdown artifacts should be human-readable and useful for review.
- Do not store hidden chain-of-thought or full raw agent reasoning in run artifacts.

## Observability

- Local `events.jsonl` is the canonical run timeline.
- Langfuse observes the AI Software Team System when configured; Target Projects should not receive Langfuse dependencies by default.
- Runs must continue locally if Langfuse is not configured or unavailable.
- Avoid logging secrets, raw API keys, or unnecessary full tool payloads.

## Git And External Effects

- Do not merge PRs, delete branches, close issues as complete, or modify repository settings unless explicitly requested.
- Keep code changes scoped to the requested milestone or issue.
- Do not rewrite user changes or clean up unrelated files.
- Prefer dry, inspectable artifacts before external side effects.

## Documentation

- Update `CONTEXT.md` when new domain terms or resolved ambiguities are introduced.
- Add ADRs only for decisions that are hard to reverse, surprising without context, and the result of a real trade-off.
- Keep `docs/spec_v1.md` aligned with implemented v1 behavior when scope decisions change.
