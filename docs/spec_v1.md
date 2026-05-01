# AI Software Team System Spec

## Purpose

The AI Software Team System is a learning-first multi-agent system that simulates a software team. Its primary goal is to provide hands-on experience with ADK, A2A, MCP, Langfuse, and agent workflow design while still producing useful software-delivery artifacts.

The system collaborates with a user to define one Product Slice, plan it, break it into GitHub-tracked work, implement it in an isolated worktree, validate it, review it, and deliver it as a draft pull request.

## Goals

- Learn the multi-agent stack through a realistic software-team workflow.
- Use ADK for agent definitions, orchestration, and workflow state.
- Use A2A for explicit agent-to-agent handoffs.
- Use MCP or MCP-like adapters for external tools and systems.
- Use GitHub Issues and draft Pull Requests as the v1 delivery workspace.
- Provide local run artifacts and Langfuse traces for observability.
- Support existing Target Projects and new Target Projects built incrementally.

## Non-Goals

- No deploy previews in v1.
- No automatic merging, branch deletion, issue completion, or repository settings changes.
- No full SaaS generation in one run.
- No peer-to-peer or hierarchical orchestration in v1.
- No TUI or web dashboard in v1.
- No semantic/vector long-term memory in v1.
- No hosted database provisioning for generated Target Projects in v1.

## Core Concepts

**AI Software Team System**: this repository, containing the multi-agent orchestrator.

**Target Project**: the repository the system creates or modifies for the user.

**Product Slice**: one user-valuable increment small enough for one run and one draft PR.

**Run Directory**: `.ai-team/runs/<run-id>/` inside the Target Project, ignored by default.

**Run Worktree**: isolated git worktree and branch where agents make code changes.

**Run State**: machine-readable `state.json` used for phase tracking and resumability.

**Run Timeline**: local `events.jsonl` event stream for observability.

## V1 Agent Roster

- **PM Agent**: central orchestrator, user discovery, spec ownership, issue creation, delivery readiness.
- **Architect Agent**: repository analysis, implementation plan, task breakdown, risk identification.
- **Developer Agent**: code implementation and checkpoint commits.
- **QA Agent**: acceptance validation, test review, regression risk.
- **Reviewer Agent**: code review before draft PR delivery.

V1 uses one general Developer Agent. Frontend, backend, devops, and other finer specializations are deferred.

## Orchestration Model

V1 uses central orchestration with the PM Agent as the workflow owner. The PM delegates sequentially to specialist agents and records handoffs as durable artifacts.

Future branches may explore peer-to-peer or hierarchical orchestration once the baseline system works.

## Technology Responsibilities

- **ADK Layer**: agent definitions, central orchestration, workflow state transitions.
- **A2A Layer**: explicit handoffs between PM, Architect, Developer, QA, and Reviewer agents.
- **MCP Layer**: external tool access, including GitHub, filesystem/repo inspection, shell execution, and documentation search.

## System Stack

The AI Software Team System itself is a Python CLI package managed with `uv`.

Expected shape:

```text
pyproject.toml
src/ai_software_team/
prompts/
  pm.md
  architect.md
  developer.md
  qa.md
  reviewer.md
```

CLI commands should include:

```bash
ai-team start
ai-team status
ai-team resume <run-id>
```

The starting model provider is Google/Gemini. Provider and model should be configurable, but v1 uses one provider/model configuration across all agents.

## System Testing

The AI Software Team System uses `pytest` for v1 tests.

Each milestone defines its own test expectations. Tests stay local and deterministic by default: no real GitHub, Langfuse, or network access required unless a milestone explicitly introduces an integration test behind an opt-in marker.

**Walking Skeleton (Milestone 1)** tests cover:

- run directory creation
- `state.json` persistence
- `events.jsonl` logging
- CLI `status` behavior
- CLI `resume <run-id>` behavior
- Langfuse-disabled fallback behavior

## Target Project Defaults

When modifying an existing Target Project, agents follow the existing stack.

When creating a new Target Project:

- PM asks the user for stack preference.
- If the user has no preference, Architect recommends the Primary Target Stack.

Primary Target Stack:

- Python
- FastAPI
- React
- Docker Compose
- Local Postgres
- SQLAlchemy
- Alembic

Hosted Postgres providers such as Supabase or Railway are future deployment choices, not v1 provisioning requirements.

## Workflow

1. **Discovery**: PM interviews the user.
2. **Specification**: PM writes and confirms `spec.md`.
3. **Planning**: Architect analyzes the Target Project and writes `plan.md`.
4. **Issue Breakdown**: PM creates a Slice Issue and optional child issues in GitHub.
5. **Implementation**: Developer works in the Run Worktree and creates Checkpoint Commits.
6. **Validation**: QA checks acceptance criteria and tests.
7. **Review**: Reviewer performs code review.
8. **Delivery**: PM opens a draft PR with linked artifacts and test results.

The v1 workflow is sequential. Parallel execution is deferred.

## Discovery Gate

PM may not leave Discovery until these are confirmed:

- Target Project: existing or new repo.
- Product Slice: the increment for this run.
- User goal: why the slice matters.
- Acceptance criteria: how completion will be judged.
- Constraints: stack, cost, deployment, security, non-goals.
- User approval to proceed.

## Run Artifacts

Each run writes artifacts under:

```text
.ai-team/runs/<run-id>/
  state.json
  events.jsonl
  spec.md
  plan.md
  handoffs/
  issues.md
  qa-report.md
  review.md
  delivery.md
```

`state.json` is resumable control state. Markdown artifacts are human-readable workflow state. Full hidden agent reasoning is not stored by default.

## GitHub Delivery

GitHub is the canonical v1 Delivery Workspace.

The PM creates one Slice Issue by default, with child issues only when they add clarity.

The PM opens a draft PR only when no Blocking Issues remain. The draft PR should include:

- Summary
- Linked issue
- Acceptance criteria checklist
- High-level changes
- Test commands and results
- Links or paths to agent reports
- Non-blocking notes
- User review guidance

## Approval Boundaries

Agents may automatically:

- Create issues.
- Create local Checkpoint Commits in the Run Worktree.
- Open draft PRs after the delivery checkpoint.

Agents may not automatically:

- Merge PRs.
- Delete branches.
- Close issues as complete.
- Modify repository settings.

Approval Checkpoints:

- Before freezing the Product Slice Spec.
- Before initializing a brand-new Target Project.
- Before creating GitHub issues.
- Before pushing a branch or opening a draft PR.
- Before continuing after a blocked run.

## QA And Review

V1 uses a bounded Repair Loop:

```text
Developer implements
QA validates
if QA fails -> Developer fixes -> QA rechecks
Reviewer reviews
if Reviewer finds blocker -> Developer fixes -> Reviewer rechecks
```

Each QA or review phase allows at most two repair attempts before the run is blocked for user input.

Blocking Issues include:

- Acceptance criteria not met.
- Tests fail for touched behavior.
- Relevant app/service cannot start.
- Data loss or migration risk.
- Security issue introduced.
- Incoherent or incomplete changes.

Non-Blocking Notes include:

- Nice-to-have refactors.
- Minor style preferences.
- Future enhancements.
- Known limitations documented in delivery artifacts.

## Observability

V1 uses local-first observability plus Langfuse.

Local observability:

- `events.jsonl` run timeline.
- Markdown artifact trail.
- Summarized tool call events.

Langfuse:

- Enabled by default when configured.
- Observes the AI Software Team System, not Target Projects.
- Tracks agent calls, handoffs, tool usage, latency, token usage, errors, and costs.

Full raw transcripts are not stored locally by default. If added later, transcript capture should be an explicit debug mode with secret redaction.

## Project Preferences

V1 supports explicit project preferences through configuration. It does not infer permanent preferences silently from chat history.

Examples:

- preferred Target Stack
- PR style
- testing preferences
- model provider configuration
- Langfuse configuration

## V1 Implementation Milestones

The milestones below decompose v1 into sequential deliveries. **Milestone 1** is the Walking Skeleton. **Milestones 2–6** complete the v1 **Delivery Workflow**, **Agent Stack**, **Run Artifacts**, and **GitHub Workspace** described elsewhere in this document. After **Milestone 6**, the behaviors in this spec are implemented end-to-end (subject to non-goals).

### Milestone 1: Walking Skeleton

Proves run layout, CLI entrypoints, local timeline, and tracing integration before multi-agent automation.

**Scope**

- `ai-team start`, `ai-team status`, `ai-team resume <run-id>`
- User discovery via CLI prompts and flags (structured input; not yet an LLM **PM Agent**)
- `spec.md` creation from discovery answers
- Run directory creation under `.ai-team/runs/<run-id>/`
- `state.json` and `events.jsonl`
- Langfuse trace emission when configured; safe fallback when not configured or unavailable

**Out of scope**

- ADK/A2A/MCP, versioned **Agent Prompts**, and LLM-backed agents
- `plan.md`, `handoffs/`, GitHub, **Run Worktree**, implementation, QA, review, draft PR

**Completion criteria**

- Milestone 1 system tests pass (see **System Testing**).
- A new run produces `spec.md`, `state.json`, and a chronological `events.jsonl`.

### Milestone 2: Agent stack, orchestration, and planning

Introduces the **ADK Layer**, **A2A Layer**, configurable **Model Provider** (Google/Gemini default), and the **Architect Agent** through the planning phase.

**Scope**

- `prompts/pm.md`, `prompts/architect.md` (and stub or minimal placeholders for `developer.md`, `qa.md`, `reviewer.md` if required by the runner)
- LLM-backed **PM Agent** for discovery and specification (replacing or augmenting pure CLI discovery while preserving **Discovery Gate** invariants)
- Central orchestration: phase transitions Discovery → Specification → Planning recorded in `state.json`
- **A2A**: durable handoff records under `handoffs/` (for example PM → Architect) plus matching `events.jsonl` entries
- Read-only **MCP Layer** or MCP-like adapters for Target Project inspection (filesystem/repo listing and targeted reads) used by the **Architect Agent**
- `plan.md` per **Implementation Plan** definition in this spec
- Langfuse observes agent and handoff activity for the **AI Software Team System**

**Out of scope**

- GitHub issue creation, **Run Worktree**, code implementation, QA, Reviewer, draft PR

**Completion criteria**

- From an approved **Discovery Gate**, a run reaches a planning phase and writes `plan.md` grounded in Target Project inspection.
- `handoffs/` contains explicit PM → Architect (and return) handoff summaries; tests use mocked LLM and tool responses where needed.

### Milestone 3: GitHub issue breakdown

Connects the **GitHub Workspace** for issue tracking and records the breakdown as a run artifact.

**Scope**

- MCP or MCP-like GitHub adapter for creating a **Slice Issue** and optional child issues when they add clarity
- `issues.md` summarizing created issues and links
- **Approval Checkpoint** before creating GitHub issues; `state.json` stores issue URLs and identifiers
- Phase transition: Planning → Issue Breakdown (or equivalent phase name in `state.json`)

**Out of scope**

- **Run Worktree**, Developer implementation, QA, Reviewer, draft PR

**Completion criteria**

- With user approval and mocked or test GitHub API, the PM path creates the configured issues and persists links in `state.json` and `issues.md`.
- Default suite remains deterministic (no live GitHub).

### Milestone 4: Run worktree and Developer implementation

Adds isolated git work and the **Developer Agent** with **Checkpoint Commits**.

**Scope**

- Create and record a **Run Worktree** and branch for the run; store paths in `state.json`
- **Developer Agent** with `prompts/developer.md` implements the **Product Slice** per `plan.md` and linked issues
- **Checkpoint Commits** in the worktree only (no merge, no branch deletion)
- Phase transition through Implementation; `events.jsonl` records implementation milestones

**Out of scope**

- QA, Reviewer, draft PR (implementation may be “best effort” locally but not validated by QA agent yet)

**Completion criteria**

- Tests use a local git fixture repository: worktree creation, branch isolation, and at least one checkpoint commit recorded in run state or events.
- User’s primary working tree is not required for agent edits.

### Milestone 5: QA, Reviewer, and bounded repair loops

Adds validation and code review agents with the v1 **Repair Loop** caps.

**Scope**

- `prompts/qa.md`, `prompts/reviewer.md`
- **QA Agent** produces `qa-report.md` classifying **Blocking Issues** vs **Non-Blocking Notes**
- **Reviewer Agent** produces `review.md` with the same classification
- Bounded repair: at most two Developer↔QA repair cycles and two Developer↔Reviewer repair cycles per run phase model; then `state.json` marks the run blocked for user input
- Phases for Validation and Review recorded in `state.json` and `events.jsonl`

**Out of scope**

- Opening the draft PR and final **Delivery** artifact (`delivery.md`)

**Completion criteria**

- Tests demonstrate pass path, repair path within limits, and blocked path when limits exceeded.
- Artifacts match the semantics in **QA And Review**.

### Milestone 6: Delivery (draft pull request)

Completes the **Delivery Workflow** with user-approved publish steps and a draft PR.

**Scope**

- **Approval Checkpoint** before push and before opening the draft PR
- **PM Agent** (or orchestration edge) opens a **Draft Pull Request** meeting **GitHub Delivery** content requirements
- `delivery.md` with summary, linked issue, acceptance checklist, change overview, test commands and results, pointers to `qa-report.md` / `review.md`, non-blocking notes, and user review guidance
- Final phase and resumability: delivery complete vs blocked matches **Approval Boundaries**

**Out of scope**

- Anything listed under **Non-Goals** (merge, deploy previews, hosted DB provisioning, etc.)

**Completion criteria**

- End-to-end dry run in tests: from existing run state fixtures or a scripted happy path through draft PR creation with GitHub API mocked.
- Full v1 workflow in this spec is achievable in one run when external services are configured.

## Future Learning Branches

- Peer-to-peer orchestration.
- Hierarchical orchestration.
- Parallel agent execution.
- Separate frontend/backend/devops specialist agents.
- TUI or web dashboard.
- Browser-based UI verification.
- Hosted deployment or deploy previews.
- Supabase integration for Target Projects.
- Per-agent model routing.
- Richer long-term memory.
