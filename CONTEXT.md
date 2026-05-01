# AI Software Team

An experimental multi-agent system for learning the agent stack through a realistic software-team workflow. The system exists to expose agent orchestration, agent-to-agent communication, and tool integration patterns while still producing useful software-delivery artifacts.

## Language

**AI Software Team**:
A multi-agent system that collaborates with a user to define, plan, implement, review, and verify software changes.
_Avoid_: Coding bot, autonomous developer

**AI Software Team System**:
The multi-agent orchestrator product being built in this repository.
_Avoid_: Team System, target project

**System Stack**:
The implementation stack of the **AI Software Team System** itself: Python CLI plus ADK, A2A, and MCP clients.
_Avoid_: Target stack, generated app stack

**System Package**:
The local Python package for the **AI Software Team System**, managed with `uv` and exposed through the `ai-team` CLI.
_Avoid_: Script folder, web service

**Model Provider**:
The configurable LLM provider used by all v1 agents, defaulting to Google/Gemini.
_Avoid_: Per-agent routing, hardcoded model

**Agent Prompt**:
A versioned prompt file that defines one agent's role, behavior, and handoff expectations.
_Avoid_: Hidden persona, hardcoded prompt

**Target Project**:
The repository that the **AI Software Team System** creates or modifies for the user.
_Avoid_: AI Software Team System, orchestrator repo

**Learning Lab**:
The primary product posture where architectural choices are optimized for hands-on exposure to multi-agent technologies, even when a simpler product architecture would be more direct.
_Avoid_: Production coding assistant, coding-agent SaaS

**Agent Stack**:
The collection of technologies used to build, coordinate, connect, and equip agents, including ADK, A2A, and MCP.
_Avoid_: AI stack, LLM stack

**ADK Layer**:
The part of the **Agent Stack** responsible for agent definitions, orchestration flow, and workflow state.
_Avoid_: Agent runtime, orchestration framework

**A2A Layer**:
The part of the **Agent Stack** responsible for explicit communication and handoffs between agents.
_Avoid_: Internal function call, direct delegation

**MCP Layer**:
The part of the **Agent Stack** responsible for connecting agents to external tools and systems.
_Avoid_: Plugin layer, tool wrapper

**MCP Tool Surface**:
The v1 set of external capabilities exposed through MCP or MCP-like tool adapters: GitHub, filesystem and repo inspection, shell execution, and documentation search.
_Avoid_: Hidden integration, direct external side effect

**Delivery Workspace**:
The external project system where the agents coordinate work items and hand off completed changes for review.
_Avoid_: Internal task database

**GitHub Workspace**:
The v1 **Delivery Workspace** where agents manage issues and open pull requests.
_Avoid_: Built-in project tracker, custom work queue

**Approval Boundary**:
The line between actions agents may perform automatically and actions that require explicit user approval.
_Avoid_: Permission model, safety switch

**Approval Checkpoint**:
A workflow moment where the **PM Agent** must ask the user before continuing, such as freezing the spec, initializing a new target project, creating GitHub issues, opening a draft pull request, or resuming from a blocked run.
_Avoid_: Per-command confirmation, modal permission

**Deploy Preview**:
A temporary hosted environment for manually testing an unmerged software change.
_Avoid_: Preview, staging deployment

**Central Orchestration**:
A workflow shape where one lead agent owns workflow state and delegates work to specialist agents.
_Avoid_: Peer-to-peer orchestration, agent democracy

**PM Agent**:
The central orchestrator that owns user discovery, requirements, task delegation, and delivery readiness for v1.
_Avoid_: Project manager, product owner

**Architect Agent**:
The specialist agent that analyzes the **Target Project** and turns requirements into a technical plan.
_Avoid_: System designer, tech lead

**Developer Agent**:
The specialist agent that implements code changes from assigned tasks.
_Avoid_: Frontend agent, backend agent, devops agent

**QA Agent**:
The specialist agent that defines and evaluates acceptance, test coverage, and regression risk.
_Avoid_: Tester, quality bot

**Reviewer Agent**:
The specialist agent that reviews code changes before pull request creation.
_Avoid_: Code reviewer, linter

**Delivery Workflow**:
The sequential v1 process that moves from user discovery to draft pull request delivery.
_Avoid_: Agent swarm, autonomous loop

**CLI Interface**:
The v1 user interface where the user chats with the **PM Agent** and starts, checks, or resumes delivery runs.
_Avoid_: TUI, web dashboard

**Run Artifact**:
A durable file produced during a delivery run that exposes specs, plans, handoffs, validation, review, or delivery status.
_Avoid_: Chat transcript, hidden state

**Run State**:
The machine-readable `state.json` for one delivery run, used to track phase, agent status, worktree, GitHub links, errors, and resumability.
_Avoid_: Agent memory, hidden reasoning

**Run Timeline**:
The local `events.jsonl` log for one delivery run, recording structured phase, agent, handoff, tool, error, and delivery events.
_Avoid_: Full transcript, metrics dashboard

**Langfuse Trace**:
The default external observability trace for the **AI Software Team System**, used to inspect agent calls, handoffs, tool use, latency, token usage, errors, and costs.
_Avoid_: Target project dependency, source of truth

**Walking Skeleton**:
The first implementation milestone proving the CLI, PM discovery, run directory, spec artifact, run state, run timeline, resume/status behavior, and Langfuse tracing before full GitHub or code-writing automation.
_Avoid_: Prototype, full v1

**Project Preference**:
An explicit user-approved preference stored in configuration and reused across runs.
_Avoid_: Inferred memory, hidden personalization

**Run Directory**:
The ignored `.ai-team/runs/<run-id>/` directory inside the **Target Project** where v1 stores **Run Artifacts**.
_Avoid_: Project docs, committed artifacts

**Run Worktree**:
An isolated git worktree and branch where agents make code changes for a delivery run.
_Avoid_: User working tree, shared checkout

**Product Slice**:
A user-valuable product increment small enough to be delivered by one run and one draft pull request.
_Avoid_: Epic, full app, task

**Discovery Gate**:
The PM-controlled checkpoint requiring a confirmed **Target Project**, **Product Slice**, user goal, acceptance criteria, constraints, and user approval before planning.
_Avoid_: Informal kickoff, vague request

**Product Slice Spec**:
The PM-authored `spec.md` that defines the summary, target project, user goal, scope, non-scope, acceptance criteria, constraints, and open questions for one **Product Slice**.
_Avoid_: Requirements dump, prompt transcript

**Implementation Plan**:
The Architect-authored `plan.md` that records repo findings, proposed approach, likely file changes, data or API changes, task breakdown, risks, and validation plan.
_Avoid_: Architecture essay, implementation transcript

**Slice Issue**:
The GitHub tracking issue for one **Product Slice**, optionally accompanied by child issues when the implementation naturally splits into independently trackable tasks.
_Avoid_: Ticket swarm, task dump

**Checkpoint Commit**:
A meaningful git commit created by the **Developer Agent** inside the **Run Worktree** during implementation.
_Avoid_: Final delivery, push, merge

**Repair Loop**:
The bounded Developer-to-QA or Developer-to-Reviewer feedback cycle used to fix blocking issues before delivery.
_Avoid_: Infinite retry, autonomous self-healing

**Blocking Issue**:
A QA or review finding that prevents delivery because acceptance criteria, tests, startup, data safety, security, or coherence are not acceptable.
_Avoid_: Nit, preference, future enhancement

**Non-Blocking Note**:
A QA or review finding that should be disclosed but does not prevent draft pull request delivery.
_Avoid_: Failure, blocker

**Draft Pull Request**:
The GitHub pull request opened by the **PM Agent** at delivery with summary, linked issue, acceptance checklist, changes, tests, agent reports, non-blocking notes, and user review guidance.
_Avoid_: Merge-ready PR, final release

**Target Stack**:
A technology stack used by a **Target Project**.
_Avoid_: Required stack, universal template

**Primary Target Stack**:
The preferred v1 **Target Stack** for new **Target Projects** without an existing stack or user preference: Python, FastAPI, and React.
_Avoid_: Next.js default, TypeScript-first default

**Local Postgres Runtime**:
The default v1 persistence runtime using Docker Compose and local Postgres for new projects.
_Avoid_: SQLite default, hosted database provisioning

**Migration Workflow**:
The default database-change workflow for new Python projects, using SQLAlchemy models and Alembic migrations.
_Avoid_: Ad hoc schema edits, manual SQL-only schema changes

## Relationships

- The **AI Software Team** is a **Learning Lab**
- The **AI Software Team System** is built in this repository
- The **AI Software Team System** uses the **System Stack**
- The **AI Software Team System** is distributed locally as the **System Package**
- The **AI Software Team System** uses one configurable **Model Provider** for all v1 agents
- **Agent Prompts** are stored as versioned files and loaded by the **AI Software Team System**
- The **AI Software Team System** creates or modifies **Target Projects**
- The **Learning Lab** exercises the **Agent Stack**
- The **Agent Stack** separates the **ADK Layer**, **A2A Layer**, and **MCP Layer**
- The **MCP Layer** exposes the **MCP Tool Surface**
- The **Delivery Workspace** contains the issues and pull requests produced by the **AI Software Team**
- The **GitHub Workspace** is the v1 **Delivery Workspace**
- The **Approval Boundary** allows agents to create issues and draft pull requests, but reserves merge, branch deletion, issue completion, and repository settings changes for the user
- **Approval Checkpoints** protect major workflow transitions and public side effects
- The **PM Agent** uses **Central Orchestration** to coordinate specialist agents in v1
- The v1 specialist roster contains the **PM Agent**, **Architect Agent**, **Developer Agent**, **QA Agent**, and **Reviewer Agent**
- The **Delivery Workflow** runs discovery, specification, planning, issue breakdown, implementation, validation, review, and delivery sequentially in v1
- The **CLI Interface** is the v1 user interaction surface
- **Run Artifacts** are the v1 visibility mechanism for specs, plans, handoffs, validation, review, and delivery status
- The **Run State** is the v1 resumability mechanism
- The **Run Timeline** is the local observability log for a delivery run
- **Langfuse Traces** are enabled by default for **AI Software Team System** observability when configured
- The **Walking Skeleton** is the first implementation milestone
- **Project Preferences** are the only v1 long-term memory mechanism
- The **Run Directory** contains **Run Artifacts** and is ignored by default
- The **Run Directory** contains **Run State** as `state.json`
- The **Run Worktree** contains code changes for a delivery run and protects the user's working tree
- The **Delivery Workflow** delivers one **Product Slice** per run
- The **Discovery Gate** must pass before the **Architect Agent** begins planning
- The **Product Slice Spec** is the PM handoff artifact to the **Architect Agent**
- The **Implementation Plan** is the Architect handoff artifact for issue breakdown and implementation
- The **PM Agent** creates a **Slice Issue** before implementation begins
- The **Developer Agent** creates **Checkpoint Commits** in the **Run Worktree**
- The **Repair Loop** allows at most two fix attempts per QA or review phase before the run is blocked for user input
- The **PM Agent** may deliver only when no **Blocking Issues** remain
- **Non-Blocking Notes** are disclosed in delivery artifacts and the draft pull request
- The **Draft Pull Request** is the v1 delivery handoff to the user
- The **Architect Agent** recommends a **Target Stack** only when the user has no stack preference and the **Target Project** has no existing stack
- The **Primary Target Stack** favors backend and platform-heavy personal projects
- The **Primary Target Stack** uses the **Local Postgres Runtime** by default
- The **Migration Workflow** belongs to the **Primary Target Stack**

## Example Dialogue

> **Dev:** "Should we collapse this into one agent with a few tools?"
> **Domain expert:** "No — the point is to learn the **Agent Stack**, so the **AI Software Team** should expose real multi-agent coordination even where a single-agent implementation would be simpler."

## Flagged Ambiguities

- "Useful product" and "learning project" could pull the architecture in different directions — resolved: this is a **Learning Lab** first, with product usefulness as a secondary goal.
- "End-to-end delivery" could include hosted testing environments — resolved: **Deploy Previews** are out of scope for v1 because they add deployment complexity and potential real costs.
- "Workspace" could mean an internal planning database or an external collaboration tool — resolved: v1 uses a **GitHub Workspace**.
- "Automatic GitHub management" could include irreversible repository actions — resolved: the **Approval Boundary** permits issue creation and draft pull request creation, but not merges, branch deletion, issue completion, or repository settings changes.
- "Approval" could mean confirming every local command — resolved: **Approval Checkpoints** apply to major phase transitions and external side effects, not every file edit or test command inside the **Run Worktree**.
- "Multi-agent orchestration" could mean central, hierarchical, or peer-to-peer workflows — resolved: v1 uses **Central Orchestration** through the **PM Agent**, with other models deferred to future versions or branches.
- "Specialist developer agents" could mean separate frontend, backend, and devops agents — resolved: v1 uses one general **Developer Agent**, with finer specialization deferred.
- "Multi-agent workflow" could imply parallel execution — resolved: the v1 **Delivery Workflow** is sequential, with parallelization deferred until the baseline is understood.
- "Agent framework" responsibilities could blur together — resolved: the **ADK Layer** owns orchestration, the **A2A Layer** owns inter-agent handoffs, and the **MCP Layer** owns external tool access.
- "Tool use" could happen through hidden integrations — resolved: external systems should be reached through the **MCP Tool Surface** when practical.
- "CLI" could imply an opaque terminal-only experience — resolved: the **CLI Interface** is paired with durable **Run Artifacts** for visibility.
- "User interface" could imply a TUI or web dashboard — resolved: v1 uses a **CLI Interface**, with richer visual interfaces deferred.
- "Run artifacts" could be committed project documentation or transient execution state — resolved: v1 stores them in the ignored **Run Directory** unless the user explicitly chooses otherwise.
- "Run state" could imply storing full agent reasoning — resolved: **Run State** stores resumable control state, while **Run Artifacts** store human-readable design and delivery details.
- "Observability" could mean only local logs or only an external tracing service — resolved: v1 uses a local **Run Timeline** plus default **Langfuse Traces** for the **AI Software Team System**.
- "Langfuse" could be installed into generated apps — resolved: **Langfuse Traces** observe the **AI Software Team System**, not **Target Projects** by default.
- "First milestone" could try to implement the whole AI team at once — resolved: start with the **Walking Skeleton** before GitHub, worktree, implementation, QA, and PR automation.
- "Long-term memory" could mean implicit agent memory across chats — resolved: v1 only stores explicit **Project Preferences**.
- "Agents modifying a repo" could mean editing the user's active checkout — resolved: agents make code changes in a **Run Worktree**.
- "Small change" could exclude starting new projects — resolved: v1 can initialize or modify a single repository, but each run delivers one **Product Slice** instead of a full app.
- "Requirements gathering" could end while the request is still vague — resolved: the **Discovery Gate** requires confirmed scope, acceptance criteria, constraints, and user approval.
- "Spec" could mean an unstructured conversation summary — resolved: the **Product Slice Spec** has a fixed v1 structure and cannot contain blocking open questions when handed to the **Architect Agent**.
- "Architecture plan" could mean broad system design — resolved: the **Implementation Plan** is scoped to one **Product Slice** and must include task and validation guidance.
- "Issue breakdown" could create many tiny tickets — resolved: v1 creates one **Slice Issue** by default, with child issues only when they add clarity.
- "Agent commits" could imply publishing or finalizing work — resolved: **Checkpoint Commits** are local to the **Run Worktree** until the **PM Agent** reaches delivery.
- "Fix feedback" could loop indefinitely — resolved: the **Repair Loop** is capped at two attempts per QA or review phase.
- "Review finding" could mean either a blocker or a note — resolved: **Blocking Issues** stop delivery, while **Non-Blocking Notes** are disclosed without stopping draft pull request creation.
- "Pull request delivery" could imply merge readiness — resolved: v1 opens a **Draft Pull Request** for user review.
- "Project codebase" could mean either this repository or the generated software repository — resolved: this repository contains the **AI Software Team System**, while generated or modified repositories are **Target Projects**.
- "Python stack" could refer to either the orchestrator or generated projects — resolved: the **System Stack** is Python for the **AI Software Team System**, while the **Primary Target Stack** is Python, FastAPI, React, and Postgres for new **Target Projects**.
- "System interface" could imply a service or loose scripts — resolved: the **AI Software Team System** is a `uv`-managed **System Package** with an `ai-team` CLI.
- "Model configuration" could imply per-agent routing — resolved: v1 uses one configurable **Model Provider** across all agents, starting with Google/Gemini.
- "Agent behavior" could be hidden in code or prompts alone — resolved: **Agent Prompts** are versioned files, while workflow invariants are enforced in code.
- "New project stack choice" could mean agents choose unilaterally — resolved: the **PM Agent** asks for user preference first, and the **Architect Agent** recommends a **Target Stack** only as a fallback.
- "Default web app stack" could mean TypeScript and Next.js — resolved: the **Primary Target Stack** is Python, FastAPI, and React because the expected use cases are more backend and platform-heavy.
- "Default database" could mean SQLite for simplicity or a hosted provider for production parity — resolved: v1 uses the **Local Postgres Runtime**, with hosted Postgres providers left as future deployment choices.
- "Database changes" could be handwritten directly against Postgres — resolved: the **Migration Workflow** uses SQLAlchemy and Alembic by default.
