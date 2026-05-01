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

Milestone 1 tests should cover:

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

## Milestone 1: Walking Skeleton

The first milestone proves the system shape before full automation.

Scope:

- `ai-team start`
- PM discovery chat
- `spec.md` creation
- `state.json` creation
- `events.jsonl` timeline
- run directory creation
- `ai-team status`
- `ai-team resume <run-id>`
- Langfuse trace emission when configured

Out of scope for Milestone 1:

- GitHub issue creation
- worktree management
- Developer/QA/Reviewer automation
- code implementation
- draft PR creation

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
