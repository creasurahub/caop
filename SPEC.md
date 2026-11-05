# Creasura Agentic OS Protocol (CAOP) v0.2

Definition, lifecycle, and API contracts for an open, portable agentic operating system.

**Version:** 0.2 · **Project:** Creasura One OSS · **Date:** November 5, 2026  
Machine-readable contracts: [OpenAPI 3.1](openapi/caop-v0.2.openapi.yaml) · [JSON Schema 2020-12](schema/caop-v0.2.schema.json)

> **What’s new in v0.2**
>
> v0.2 adds five mechanisms: **two-phase verification** (VERIFY_PHASE_1_IMMEDIATE and VERIFY_PHASE_2_DEFERRED, with RECORDED_AWAITING_OUTCOME_VERIFY); **mid-flight steering** (`APPROVE_WITH_STEERING_DELTA` with `steering_delta`); **hierarchical sub-agent isolation** (`parent_work_id`, `isolation_policy`, `distilled_return_payload`); **inner-loop context compaction** (`compaction_mode`); and **lazy capability discovery** (`hydrate_capability_ids` and capability stubs). v0.1 (sections 1–13) and v0.1.2 (section 14) remain the base; v0.2 is additive. [Read section 15 ›](#15-v02-outcome-verification-approval-steering-and-long-horizon-context)
>
> Previous versions: [v0.1.2](https://creasura.com/spec/v0.1.2/) ([OpenAPI YAML](openapi/caop-v0.1.2.openapi.yaml), [OpenAPI JSON](openapi/caop-v0.1.2.openapi.json), [JSON Schema](schema/caop-v0.1.2.schema.json)) · [v0.1](https://creasura.com/spec/v0.1/) ([OpenAPI YAML](openapi/caop-v0.1.openapi.yaml), [OpenAPI JSON](openapi/caop-v0.1.openapi.json), [JSON Schema](schema/caop-v0.1.schema.json))

> **Implementation status**
>
> As of November 5, 2026, Creasura’s reference kernel conforms to CAOP v0.1.2 at CAOP-STAGE-1 (host-delegated execution). Of the five v0.2 mechanisms it implements two, at CAOP-STAGE-1. The other three are specified but not yet implemented, so the reference kernel does not yet conform to v0.2 as a whole.
>
> | v0.2 mechanism | Section | Reference kernel |
> |---|---|---|
> | Two-phase outcome verification | [§15.1](#151-outcome-verification-and-approval-steering-a) | Implemented |
> | Mid-flight approval steering | [§15.1](#151-outcome-verification-and-approval-steering-a) | Implemented |
> | Hierarchical sub-agent isolation | [§15.2](#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |
> | Inner-loop context compaction | [§15.2](#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |
> | Lazy capability discovery | [§15.2](#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |
>
> Notes for implementers:
>
> - In the reference kernel, a verification capability (`verification_capability_id`) must be side-effect-free: it may only read external state. Dispatch refuses a deferred check whose capability is not registered as side-effect-free.
> - On `APPROVE_WITH_STEERING_DELTA`, the reference kernel re-runs every policy check on the patched plan (every Policy pre-commit hook and the `minimum_attestation` check) before it dispatches.

## 1. Overview

For Creasura One OSS, an **Agentic Operating System (Agentic OS)** is:

> A persistent, event-driven system that coordinates intelligent agents, tools, knowledge, and human decisions to achieve goals over time, while maintaining durable state, enforcing policies, verifying outcomes, and recovering from failures.

An agentic OS is not simply an agent, an agent framework, or an LLM with tools. It is the system responsible for **managing the lifecycle of work performed by agents**.

| Traditional OS | Agentic OS |
|---|---|
| Process | Goal-directed work instance |
| Process scheduler | Goal and task scheduler |
| Memory manager | Context and knowledge manager |
| Filesystem | Persistent state and artifact store |
| System calls | Tool and capability APIs |
| Permissions | Identity, authorization and policies |
| Interprocess communication | Events and agent coordination |
| Process supervision | Execution monitoring and recovery |
| System logs | Execution traces and provenance |
| Device drivers | Application and service connectors |

An agentic OS doesn’t need to implement its own LLM, browser, coding agent, or research engine. Those are *execution capabilities*. The OS manages how those capabilities are invoked, coordinated, supervised, and remembered. ChatGPT, Claude, and other providers can supply execution capabilities while Creasura provides a consistent operating model.

## 2. The five fundamental abstractions

Start with five abstractions rather than a large collection of specialized agents.

### 2.1 Goal

A desired outcome that persists beyond a single conversation, for example: reduce monthly household expenses, complete a software architecture proposal, plan a family vacation, launch a business. A goal has an owner, success criteria, constraints, and a lifecycle.

```ts
interface Goal {
  id: string;
  objective: string;
  owner: PrincipalRef;
  successCriteria: Criterion[];
  constraints: Constraint[];
  status: "active" | "paused" | "achieved" | "abandoned";
  createdAt: string;
  updatedAt: string;
}
```

### 2.2 Work

A bounded unit of execution that advances a goal. A goal may contain multiple work items. Work has dependencies, execution state, deadlines, and evidence of completion.

```text
Goal: Plan family vacation
  |
  +-- Compare destinations
  +-- Find flights
  +-- Compare hotels
  +-- Review budget
  +-- Book approved itinerary
```

```ts
interface WorkItem {
  id: string;
  goalId: string;
  description: string;
  dependencies: string[];
  status: "pending" | "ready" | "running" | "blocked" | "completed" | "failed" | "cancelled";
  assignedCapability?: string;
  result?: ArtifactRef;
  deadline?: string;
}
```

### 2.3 State

The durable representation of what the OS knows: facts, goals, commitments, decisions, relationships, policies, execution history, and evidence. State is not equivalent to conversational memory.

```ts
interface Fact {
  id: string;
  subject: EntityRef;
  predicate: string;
  object: unknown;
  source: EvidenceRef;
  observedAt: string;
  validFrom?: string;
  validTo?: string;
  confidence?: number;
}
```

> **Critical requirement: provenance.** Every material fact should have a traceable origin.

### 2.4 Capability

Something the OS can invoke to perform work: an AI assistant, a coding agent, email, calendar, GitHub, web research, a deterministic rules engine, or a human approval workflow.

```ts
interface Capability {
  id: string;
  operations: string[];
  inputSchema: object;
  outputSchema: object;
  authorization: AuthorizationPolicy;
  executionMode: "interactive" | "background" | "scheduled";
  provider: string;
}
```

A capability contract should describe what an operation *can do*, not merely what an agent is instructed to attempt.

### 2.5 Policy

An enforceable constraint governing execution. Examples: never send an external email without authorization; never spend money without approval; never expose employer-confidential information to a personal workspace; never mark work complete without supporting evidence.

```ts
interface Policy {
  id: string;
  scope: string;
  condition: Expression;
  effect: "allow" | "deny" | "require_approval";
  version: string;
}
```

> **Advisory vs. enforced.** A policy written in an assistant’s instructions is advisory. A policy enforced by a runtime before executing an action is an actual control. Every Creasura policy must state which it is.

## 3. The lifecycle

A canonical lifecycle with eight stages:

**Observe** → **Understand** → **Commit** → **Plan** → **Execute** → **Verify** → **Record** → **Review** → (back to Observe)

These are **logical lifecycle stages**, not a requirement that every request execute eight sequential LLM calls. A deterministic operation might bypass planning entirely. A failed verification might return work to planning. A blocked task might wait for an external event for several days.

> **Note:** The lifecycle is a coordination protocol, not a rigid prompt chain.

## 4. Lifecycle API

The protocol has three interfaces: the **Lifecycle API** (how work progresses), the **Capability API** (how external executors perform work), and the **State API** (how knowledge, decisions, and outcomes persist).

| Stage | Operation | Input | Output |
|---|---|---|---|
| Observe | `observations.ingest` | Source event, payload, provenance | Observation ID |
| Understand | `context.resolve` | Observation IDs, goal, scope | Context bundle |
| Commit | `commitments.create` | Objective, criteria, constraints | Commitment ID |
| Plan | `plans.create` | Commitment, capabilities, context | Execution plan |
| Execute | `executions.start` | Plan, authorization context | Execution ID |
| Verify | `verifications.evaluate` | Execution result, criteria | Verdict |
| Record | `records.commit` | Facts, evidence, outcomes | State version |
| Review | `reviews.evaluate` | Goal, history, current state | Recommendations |

These operations represent logical responsibilities. Implementations can combine them internally.

### 4.1 Observe

An observation represents something the OS has learned from an external source.

```http
POST /v1/observations
{
  "source": { "provider": "gmail", "resource_id": "message_123" },
  "type": "message.received",
  "occurred_at": "2026-11-01T14:00:00Z",
  "payload_ref": "artifact_456",
  "idempotency_key": "gmail-message-123"
}

// Response
{ "observation_id": "obs_123", "status": "accepted", "duplicate": false }
```

> **Invariant:** replaying the same source event must not create duplicate observations.

### 4.2 Understand

The OS resolves the observation against known state.

```http
POST /v1/context/resolve
{
  "observation_ids": ["obs_123"],
  "scope": { "workspace_id": "personal", "project_ids": ["mortgage-refinance"] },
  "include": ["related_goals", "open_commitments", "relevant_policies", "prior_decisions"]
}

// Response
{
  "context_id": "ctx_123",
  "state_version": 42,
  "related_goals": ["goal_refinance"],
  "open_commitments": ["commitment_12"],
  "applicable_policies": ["policy_financial_approval"],
  "unresolved_questions": []
}
```

This operation should distinguish retrieved facts from inferred interpretations.

### 4.3 Commit

Create a durable obligation or objective.

```http
POST /v1/commitments
{
  "goal_id": "goal_refinance",
  "objective": "Evaluate updated refinancing offer",
  "success_criteria": [
    { "type": "artifact_exists", "artifact_type": "refinancing_comparison" }
  ],
  "deadline": "2026-11-05T23:59:00Z"
}

// Response
{ "commitment_id": "com_123", "status": "open", "version": 1 }
```

> **Invariant:** a commitment cannot be marked completed solely because an agent claims it is complete.

### 4.4 Plan

```http
POST /v1/plans
{
  "commitment_id": "com_123",
  "constraints": { "require_approval_for_external_actions": true },
  "preferred_capabilities": ["document_analysis", "calculator", "research"]
}

// Response
{
  "plan_id": "plan_123",
  "steps": [
    { "id": "step_1", "capability": "document_analysis", "depends_on": [] },
    { "id": "step_2", "capability": "calculator", "depends_on": ["step_1"] },
    { "id": "step_3", "capability": "report_generation", "depends_on": ["step_2"] }
  ]
}
```

The planner may use an LLM. The runtime must still validate the generated plan against schemas, dependencies, and policy constraints.

### 4.5 Execute

```http
POST /v1/executions
{
  "plan_id": "plan_123",
  "idempotency_key": "execute-plan-123-v1",
  "authorization_context": { "principal_id": "user_123" }
}

// Response
{ "execution_id": "exec_123", "status": "queued", "next_action": "await_execution" }
```

Execution is asynchronous. An accepted request does not mean the work has completed.

### 4.6 Verify

```http
POST /v1/verifications
{
  "execution_id": "exec_123",
  "criteria": ["all_required_steps_completed", "result_has_supporting_evidence", "no_policy_violations"]
}

// Response
{ "verification_id": "verify_123", "verdict": "passed", "evidence_refs": ["artifact_789"] }
```

Verification can include deterministic checks, human approval, or model-based evaluation. **The verdict must identify which checks were performed.**

### 4.7 Record

```http
POST /v1/records/commit
{
  "execution_id": "exec_123",
  "verification_id": "verify_123",
  "expected_state_version": 42,
  "changes": [ { "entity_id": "com_123", "operation": "set_status", "value": "completed" } ]
}

// Response
{ "transaction_id": "txn_123", "state_version": 43, "status": "committed" }
```

> **Invariant:** a conflicting state version must reject the transaction or invoke an explicitly defined conflict-resolution policy.

### 4.8 Review

```http
POST /v1/reviews
{
  "goal_id": "goal_refinance",
  "review_type": "progress",
  "include": ["outcomes", "unresolved_commitments", "failures", "next_actions"]
}

// Response
{
  "review_id": "review_123",
  "goal_status": "active",
  "recommended_actions": [ { "action": "request_final_offer", "requires_approval": true } ]
}
```

Review recommendations are proposals, not automatically authorized actions.

## 5. Execution state machine

The eight lifecycle stages should not be confused with execution states.

```text
CREATED
   |
   v
READY
   |
   v
RUNNING ---------> WAITING_APPROVAL
   |                     |
   |                     v
   |                   RUNNING
   |
   +------------------> BLOCKED
   |                     |
   |                     v
   |                   READY
   |
   v
VERIFYING
   |
   +------> FAILED
   |          |
   |          v
   |        READY (retry)
   |
   v
COMPLETED

Terminal states: COMPLETED, CANCELLED, EXPIRED
```

The API must reject invalid transitions.

```http
POST /v1/executions/exec_123/transitions
{
  "expected_state": "VERIFYING",
  "target_state": "COMPLETED",
  "verification_id": "verify_123"
}
```

A transition from CREATED directly to COMPLETED should be rejected unless the work type explicitly supports that shortcut. The runtime persists each accepted transition with an actor, timestamp, reason, and correlation ID.

[Try the state machine interactively ›](https://creasura.com/blog/agentic-os-spec-behind-the-scenes/#sm)

> **v0.1.2:** EXECUTE is refined into sub-states that map onto these execution states. See [§14.5.1](#1451-the-execute-stage-a-sub-states) and [§14.8](#148-compatibility-with-v01).

> **v0.2:** Two-phase outcome verification keeps an execution in VERIFYING until a deferred outcome check passes; only then does it reach COMPLETED. See [§15.1](#151-outcome-verification-and-approval-steering-a).

## 6. Capability API

The boundary between the OS and the assistants and services that do the work. The OS must not assume every provider supports the same features.

```ts
interface CapabilityDescriptor {
  id: string;
  provider: string;
  operations: string[];
  inputSchema: object;
  outputSchema: object;
  supportsAsync: boolean;
  supportsResume: boolean;
  supportsCancellation: boolean;
  authorizationRequired: boolean;
  sideEffectLevel: "none" | "reversible" | "irreversible";
}

interface CapabilityInvocation {
  invocationId: string;
  capabilityId: string;
  input: unknown;
  contextRefs: string[];
  authorizationRef?: string;
  idempotencyKey: string;
}

interface CapabilityResult {
  invocationId: string;
  status: "completed" | "failed" | "pending" | "requires_approval";
  output?: unknown;
  evidenceRefs: string[];
  error?: { code: string; message: string; retryable: boolean };
}
```

This makes the OS independent of a particular execution provider. A capability might be implemented through an AI assistant, a coding agent, an MCP tool, a deterministic function, or another provider.

> **v0.1.2:** Capabilities also declare execution locus, credential custody, receipt lease, required receipt fields and promotion policy. See [§14.4](#144-capability-api-extensions-execution_locus--artifact-validation).

### 6.1 Native assistant mapping

What a native ChatGPT setup can provide on its own, and what it guarantees:

| OS responsibility | Native implementation | Contract guarantee |
|---|---|---|
| Observe | User messages, connected apps, eligible triggers | Depends on source |
| Understand | Assistant reasoning and retrieval | Best effort |
| Commit | Project records or external ledger | Durable only with persistent store |
| Plan | Assistant reasoning | Plan is a proposal |
| Execute | Assistant work surfaces, coding agents, apps | Depends on execution surface |
| Verify | Assistant reasoning plus available tools | Must distinguish model judgment from deterministic checks |
| Record | Files, connected apps, or MCP state service | Depends on storage |
| Review | Scheduled tasks and the assistant | Best effort |

> **Note:** Programmatic invocation of an assistant’s native work surfaces must use an explicitly supported interface. Do not assume arbitrary sessions can be launched through MCP.

## 7. Cross-cutting contracts

These matter more than adding dozens of specialized endpoints.

| Contract | Requirement |
|---|---|
| Identity | Every action identifies the authenticated principal and workspace |
| Authorization | Every protected operation checks permissions server-side |
| Idempotency | Repeated requests cannot duplicate consequential actions |
| Concurrency | State mutations support version checks |
| Provenance | Material facts and outcomes reference their sources |
| Correlation | Events, plans, executions, and artifacts share trace identifiers |
| Recovery | Interrupted work can resume or fail explicitly |
| Retry | Retries follow declared policies and avoid unsafe duplication |
| Approval | High-impact actions require scoped, expiring authorization |
| Audit | State transitions and external actions produce durable records |
| Data isolation | Personal, business, and employer work respect access boundaries |
| Versioning | Policies, skills, schemas, and plans carry versions |

> **v0.2:** An approval can steer the work it approves: APPROVE_WITH_STEERING_DELTA binds the approval to a patched plan, which must pass every policy check again. See [§15.1](#151-outcome-verification-and-approval-steering-a).

### 7.1 Error format

```json
{
  "error": {
    "code": "POLICY_APPROVAL_REQUIRED",
    "message": "External action requires approval",
    "retryable": false,
    "details": { "approval_request_id": "approval_123" }
  },
  "trace_id": "trace_456"
}
```

> **Exactly-once execution cannot generally be guaranteed across arbitrary external services.** Use idempotency keys, transactional outbox patterns where appropriate, and reconciliation of external side effects.

## 8. Events

An agentic OS is event-driven rather than assuming every workflow starts with a user prompt.

```json
{
  "event_id": "evt_123",
  "event_type": "commitment.deadline_approaching",
  "schema_version": "1.0",
  "occurred_at": "2026-11-01T14:00:00Z",
  "workspace_id": "personal",
  "subject_id": "com_123",
  "correlation_id": "goal_refinance",
  "causation_id": "evt_100",
  "payload": { "hours_remaining": 24 }
}
```

| Event | Lifecycle consequence |
|---|---|
| `observation.received` | Resolve context |
| `commitment.created` | Schedule planning |
| `plan.approved` | Begin execution |
| `execution.started` | Monitor execution |
| `execution.blocked` | Wait for dependency |
| `approval.requested` | Notify authorized approver |
| `approval.granted` | Resume eligible work |
| `execution.completed` | Begin verification |
| `verification.failed` | Retry, replan, or escalate |
| `record.committed` | Update dependent work |
| `goal.achieved` | Close or review goal |

The event transport can start simple. For a single-user deployment of Creasura One OSS v0.1, an SQLite-backed event table and a scheduled processor are sufficient. No distributed broker is required.

## 9. Conformance levels

| Level | Description | Implementation |
|---|---|---|
| **L1** Agentic workspace | Organized context, tools, and reusable workflows | Assistant projects, memory, apps, and tasks |
| **L2** Stateful Agentic OS | Durable goals, commitments, execution state, and recovery | Assistant + minimal MCP state service |
| **L3** Autonomous Agentic OS | Event-driven execution with policy enforcement and supervision | L2 + event processor and execution runtime |

An assistant configured with projects and instructions can provide L1 immediately. L2 needs a persistent store outside conversational memory. L3 needs a lightweight execution controller that responds to events and enforces lifecycle transitions, delegating AI work to existing providers.

> **v0.1.2:** Runtime conformance profiles CAOP-STAGE-1/2/3 map onto these levels. See [§14.1](#141-runtime-conformance-stages-normative-profiles) and [§14.8](#148-compatibility-with-v01).

## 10. Minimum public API

Don’t expose all eight lifecycle stages as mandatory public tools. Expose a small set of outcome-oriented operations, mapped internally to the richer lifecycle API:

| Public operation | Responsibility |
|---|---|
| `observe` | Ingest an event or new information |
| `get_context` | Retrieve relevant verified state |
| `create_commitment` | Establish an objective or obligation |
| `list_commitments` | Retrieve outstanding work |
| `propose_plan` | Produce an execution proposal |
| `start_work` | Start an authorized work instance |
| `get_work_status` | Inspect execution progress |
| `submit_result` | Submit output and evidence for verification |
| `approve_action` | Authorize a scoped consequential action |
| `review_goals` | Evaluate progress and next actions |

Assistants see a manageable set of tools with clear purposes, and the internal OS can evolve without forcing changes to every integration.

> **v0.1.2:** A four-tool compact binding is defined as an alternative public surface; these ten tools remain conformant. See [§14.6](#146-normative-8-to-4-mcp--openapi-lifecycle-binding).

## 11. Reference architecture

```text
                    USER
                     |
                     v
              +-------------+
              | AI assistant|
              | (ChatGPT,   |
              |  Claude...) |
              +------+------+
                     |  MCP
                     v
          +----------------------+
          | CREASURA OS PROTOCOL |
          | Goals & Commitments  |
          | State & Context      |
          | Plans & Executions   |
          | Policies & Approvals |
          | Verification         |
          +----------+-----------+
                     |
          +----------+----------+
          v                     v
   +-------------+       +-------------+
   | State Store |       | Event Loop  |
   | SQLite      |       | Scheduler   |
   +-------------+       +------+------+
                                |
                                v
                         +-------------+
                         | Capability  |
                         | Adapters    |
                         +------+------+
                                |
                 +--------------+--------------+
                 v              v              v
            Assistants    Coding agents    External services
```

> **Design principle:** keep the lifecycle protocol independent of both the model and the execution framework. The OS defines what constitutes valid work, which state transitions are permitted, what evidence is required, and who can authorize an action. The assistant remains free to decide how to reason, research, draft, and solve problems within those boundaries.

## 12. Business Profile (CAOP-Biz)

An optional profile that scales the same kernel from a single-user personal OS to a business operating system, without changing the eight lifecycle stages or the public operations.

| Primitive | Personal OS | Business OS | Core mechanism |
|---|---|---|---|
| Goal | Plan family vacation | Improve Q4 net margin by 200 bps | Hierarchical OKR / KPI tree |
| Commitment | Book approved itinerary | Reallocate $50k ad spend by Friday | SLA-bound deliverable |
| State / Fact | Mortgage rate is 5.875% | SKU-402 contribution margin is 14.2% | Bitemporal metric & fact store |
| Capability | Assistant, calendar, email | OLAP query, MIP solver, ERP API | Deterministic + agentic adapters |
| Policy | Ask before sending email | Cap autonomous price edits at 5% | Delegation of Authority |
| Dry run | Preview calendar holds | Simulate P&L and ROAS impact | Counterfactual sandbox |
| Review | Weekly task check-in | Automated weekly business review | Variance & attribution audit |

### 12.1 Metric trees and variance triggers

```ts
interface MetricNode {
  id: string;                 // e.g. "metric.net_contribution_margin"
  name: string;
  formula?: string;           // deterministic relation to child metrics
  parentMetricId?: string;
  childMetricIds: string[];
  owner: PrincipalRef;
  baselineCadence: "hourly" | "daily" | "weekly" | "monthly";
  varianceThresholds: {
    warningDeltaPct: number;  // e.g. -3.0% triggers Understand
    criticalDeltaPct: number; // e.g. -7.5% triggers Commitment
  };
}
```

On `metric.variance_detected`, `context.resolve` traverses the `childMetricIds` graph to isolate the driver before any commitment or plan is proposed.

### 12.2 Delegation of Authority

- **Tier 1, autonomous:** exposure under $1,000 and margin above threshold → `allow` under the agent’s service principal.
- **Tier 2, single approver:** $1,000–$25,000 → `require_approval` routed to a role, with an SLA escalation timer.
- **Tier 3, quorum:** over $25,000 or modifies a locked constraint → multi-party sign-off before WAITING_APPROVAL can move to RUNNING.

```ts
interface ApprovalRoutingRule {
  policyId: string;
  requiredRoles: string[];
  minQuorum: number;
  expirationSeconds: number;
  escalateToRoleOnTimeout?: string;
}
```

### 12.3 Bitemporal state

- **Valid time** (`validFrom → validTo`): the business period the fact describes.
- **System time** (`observedAt → supersededAt`): when the OS believed the fact to be true.
- **Invariant:** `context.resolve` accepts `asOfSystemTime` and `asOfValidTime`, separating decision quality from data latency.

### 12.4 Two-phase verification

```http
POST /v1/commitments
{
  "goal_id": "goal_q4_efficiency",
  "objective": "Reallocate underperforming campaign spend to high-margin SKUs",
  "success_criteria": [
    { "phase": "immediate_verification", "type": "constraint_check",
      "rule": "total_daily_spend <= 10000 AND min_sku_roas >= 2.8" },
    { "phase": "outcome_realization", "evaluation_window_hours": 168,
      "type": "counterfactual_lift", "metric_id": "metric.net_contribution_margin",
      "expected_delta_pct": 4.5 }
  ]
}
```

Immediate criteria are evaluated at Verify. When Record commits, the outbox schedules `commitment.outcome_window_elapsed`; when it fires, Review compares realized metrics with the dry-run projection and writes a value-realization verdict.

### 12.5 Capability tiers

| Tier | sideEffectLevel | Examples |
|---|---|---|
| Analytical | `none` | In-process SQL engines, causal estimators, constrained-optimization solvers |
| Reasoning & synthesis | `none` | LLM agents drafting review memos and candidate plans, constrained by deterministic outputs |
| Operational | `reversible` / `irreversible` | ERP, CRM, billing, and media connectors with compensation (rollback) operations, gated by Delegation of Authority |

> **Note:** Dry run, ContextLease, and compensation operations are part of the Business Profile, not the core.

## 13. Machine-readable contracts

CAOP v0.1 is published in two machine-readable forms generated from the same definitions:

- [**OpenAPI 3.1 contract**](https://creasura.com/spec/openapi/): every lifecycle operation, request, response, and error, with the MCP tool each one backs. [YAML](openapi/caop-v0.1.openapi.yaml) · [JSON](openapi/caop-v0.1.openapi.json)
- [**JSON Schema 2020-12**](https://creasura.com/spec/schema/): every object in this specification, in one bundle. [caop-v0.1.schema.json](schema/caop-v0.1.schema.json)

- CAOP v0.1.2 extends both forms additively (conformance profiles, causal state, pre-commit hooks, host execution enforcement, and the compact four-tool binding): [OpenAPI YAML](openapi/caop-v0.1.2.openapi.yaml) · [OpenAPI JSON](openapi/caop-v0.1.2.openapi.json) · [caop-v0.1.2.schema.json](schema/caop-v0.1.2.schema.json). The v0.1 files above stay published at their versioned URLs.

> **v0.2:** CAOP v0.2 extends both forms additively again; the v0.1 and v0.1.2 files stay published at their versioned URLs. See [§15](#machine-readable-contracts).

## 14. v0.1.2: conformance stages, causal state and host enforcement

**CAOP v0.1.2 Specification: Conformance Stages, Causal State, and Host Enforcement**

The consolidated Creasura Agentic Operating Protocol (CAOP v0.1.2) specification below integrates the three runtime conformance stages, the bitemporal causal dependency graph, epistemic hygiene gates, deterministic pre-commit hooks, host execution enforcement, and the 8-to-4 MCP tool bindings into a single master document.

> **Note:** In this addendum, Stage 1–3 are conformance profiles; lifecycle stages are named (OBSERVE … REVIEW). [a]

### 14.1 Runtime Conformance Stages (Normative Profiles)

CAOP v0.1.2 defines three progressive runtime conformance profiles. Advancing a workspace or individual capability from Stage 1 to Stage 3 requires zero breaking changes to Goal definitions, the eight-stage Work lifecycle (OBSERVE → UNDERSTAND → COMMIT → PLAN → EXECUTE → VERIFY → RECORD → REVIEW), or bitemporal State queries.

| Profile | Loop Driver | Auth Custodian | Execution Locus | Max Attestation |
|---|---|---|---|---|
| Stage 1 (CAOP-STAGE-1) | CLIENT_POLLED | CLIENT_SESSION | HOST_DELEGATED | HOST_ASSERTED |
| Stage 2 (CAOP-STAGE-2) | CLIENT_POLLED | CREASURA_VAULT | KERNEL_PROXIED | KERNEL_ATTESTED |
| Stage 3 (CAOP-STAGE-3) | KERNEL_MANAGED | CREASURA_VAULT | KERNEL_PROXIED | KERNEL_ATTESTED |

- **CAOP-STAGE-1 (Host-Delegated Ledger):** External conversational hosts (ChatGPT (Actions or MCP apps), Claude (MCP) [g]) initiate turns and execute downstream side effects using their native connectors while Creasura enforces lifecycle order, policy gates, lease locks, and causal state recording.
- **CAOP-STAGE-2 (Kernel-Proxied Execution):** The host client drives conversational turns, but downstream OAuth tokens live in the Creasura Vault so the kernel invokes external providers directly over TLS during EXECUTE.
- **CAOP-STAGE-3 (Autonomous Kernel Runtime):** The Creasura kernel owns the event-driven trigger loop (webhooks and durable schedules) and runs headless reasoning turns through OBSERVE → PLAN → EXECUTE, using chat clients as supervisor and approval surfaces.

### 14.2 Epistemic State, Bitemporal Store & Causal Invalidation (State API)

To prevent exploratory chat output from polluting durable workspace memory and to eliminate stale downstream decisions when upstream premises change, the State API enforces an epistemic state machine and a directed acyclic graph (DAG) of causal dependencies.

#### 14.2.1 Epistemic Status Enum (epistemic_status)

Every fact and commitment in the State API MUST carry one of three epistemic states (adoption), and separately a freshness value: [Q1]

- **CANDIDATE_PROPOSAL:** Recorded during UNDERSTAND or PLAN. Excluded from default truth queries until ratified.
- **RATIFIED_COMMITMENT:** Promoted when a Work item passes all Policy pre-commit hooks and human approval gates at COMMIT.
- **VERIFIED_FACT:** Promoted at RECORD once execution evidence passes VERIFY (HOST_ASSERTED or KERNEL_ATTESTED).

Freshness (freshness) is tracked separately from adoption: [Q1]

- **CURRENT:** Every required premise has current support. The default. [Q1]
- **STALE_UPSTREAM_PREMISE:** Assigned automatically by the kernel when any upstream dependency in depends_on_fact_ids is superseded or invalidated, under the support rule of §14.2.3 [Q2].

A stale VERIFIED_FACT keeps epistemic_status: VERIFIED_FACT and gets freshness: STALE_UPSTREAM_PREMISE; its history stays intact. Default truth queries exclude CANDIDATE_PROPOSAL and flag, but do not hide, facts and commitments whose freshness is STALE_UPSTREAM_PREMISE. [Q1]

#### 14.2.2 Bitemporal Fact & Causal Dependency Schema

Facts are tracked across both valid_time (when the fact is true in the real world) and transaction_time (when the fact was recorded or superseded in the ledger), alongside explicit upstream lineage (depends_on_fact_ids) and execution provenance:

```json
{
  "fact_id": "fct_rfc_sharding_decision",
  "subject": "rfc_payment_ledger_v2",
  "predicate": "selected_partition_strategy",
  "object": {
    "strategy": "single_region_hash",
    "max_tps_assumed": 15000
  },
  "epistemic_status": "RATIFIED_COMMITMENT",
  "freshness": "STALE_UPSTREAM_PREMISE",
  "depends_on_fact_ids": ["fct_bench_2026_10_p99"],
  "invalidation_context": {
    "invalidated_by_fact_id": "fct_bench_2026_11_p99",
    "invalidated_at": "2026-11-04T18:20:00Z",
    "reason": "Upstream fact fct_bench_2026_10_p99 was superseded."
  },
  "valid_time": {
    "start": "2026-10-15T09:00:00Z",
    "end": null
  },
  "transaction_time": {
    "recorded_at": "2026-10-15T09:05:12Z",
    "superseded_at": null
  },
  "provenance": {
    "work_id": "wrk_01J9Z8K4M2",
    "invocation_id": "inv_99481A",
    "execution_locus": "HOST_DELEGATED",
    "attestation": "HOST_ASSERTED",
    "verified_fields": ["external_ref", "htmlLink", "iCalUID"]
  }
}
```

*Example updated: epistemic_status is RATIFIED_COMMITMENT and freshness is STALE_UPSTREAM_PREMISE.* [Q1]

#### 14.2.3 Synchronous Causal Invalidation Rule

Whenever a new fact F_new supersedes an existing fact F_old (setting F_old.transaction_time.superseded_at), the Creasura kernel MUST, synchronously and within the same database transaction, re-evaluate every dependent commitment or fact reachable through reverse depends_on_fact_ids and depends_on_alternatives edges: [Q2]

- A dependent becomes freshness: "STALE_UPSTREAM_PREMISE" only when at least one of its required premises has no remaining CURRENT support. [Q2]
- Each depends_on_fact_ids entry is a required premise on its own. Dependency entries MAY instead be grouped as alternatives in the optional depends_on_alternatives: [[fact_id, ...], ...]. Each inner array is a set of interchangeable supports; the premise stays supported while ANY member is CURRENT. [Q2]
- Staleness propagates transitively: a dependent that becomes stale is an unsupported premise for its own dependents. [Q2]
- The kernel MUST enforce a declared max_invalidation_subgraph limit. An update whose affected subgraph exceeds it is rejected before commit with CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE (HTTP 413, in the v0.1 error envelope), and nothing is partially applied. [Q2]
- Re-supporting a premise restores freshness: "CURRENT"; the kernel recomputes it the same way. [Q2]
- Superseded facts and their history are never rewritten; only freshness and invalidation_context change on dependents. [Q2]

#### 14.2.4 Provenance Attestation Tiers (provenance.attestation)

- **HOST_ASSERTED:** Assigned during VERIFY when a HOST_DELEGATED capability passes cryptographic nonce and provider-artifact checks via caop_settle_receipt.
- **KERNEL_ATTESTED:** Assigned during VERIFY when the Creasura kernel executes the capability directly (KERNEL_PROXIED) or verifies a signed provider webhook.
- **USER_CONFIRMED:** Assigned when a human principal explicitly confirms or overrides an outcome during REVIEW.

### 14.3 Policy API & Deterministic Pre-Commit Hooks

During the COMMIT stage [a], the kernel evaluates active Policy objects before any Work plan can advance to EXECUTE_PENDING or request user approval. Policies enforce both minimum attestation levels and structural metadata completeness via deterministic pre_commit_hooks.

```json
{
  "policy_id": "pol_principal_engineering_hygiene",
  "scope_goal_types": ["architecture_rfc", "production_change"],
  "minimum_attestation": "HOST_ASSERTED",
  "require_human_approval": true,
  "pre_commit_hooks": [
    {
      "hook_id": "REQUIRE_EXPLICIT_OWNER",
      "target_path": "commitment.owner_principal_id",
      "condition": "NON_EMPTY_PRINCIPAL_REF",
      "error_code": "CAOP_422_PRECOMMIT_MISSING_OWNER"
    },
    {
      "hook_id": "REQUIRE_EVIDENCE_LINEAGE",
      "target_path": "understanding.derived_facts[*].depends_on_fact_ids",
      "condition": "NON_EMPTY_ARRAY",
      "error_code": "CAOP_422_PRECOMMIT_MISSING_LINEAGE"
    },
    {
      "hook_id": "BLOCK_STALE_PREMISES",
      "target_path": "understanding.derived_facts[*].depends_on_fact_ids",
      "condition": "ALL_UPSTREAM_FACTS_VERIFIED_ACTIVE",
      "error_code": "CAOP_422_PRECOMMIT_STALE_DEPENDENCY"
    }
  ]
}
```

The BLOCK_STALE_PREMISES condition ALL_UPSTREAM_FACTS_VERIFIED_ACTIVE holds only when every upstream fact has epistemic_status VERIFIED_FACT and freshness CURRENT. [Q1]

The kernel MUST reject unknown or cross-workspace fact IDs in depends_on_fact_ids or depends_on_alternatives with CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID. [Q3]

#### Pre-Commit Hook Rejection Payload (CAOP_422_PRECOMMIT_HOOK_FAILED)

If any pre-commit hook fails during caop_stage_work, the kernel keeps the work item in CANDIDATE_PROPOSAL and returns a structured remediation directive:

```json
{
  "error": {
    "code": "CAOP_422_PRECOMMIT_HOOK_FAILED",
    "message": "One or more Policy pre-commit hooks failed. The work item remains in CANDIDATE_PROPOSAL.",
    "retryable": false,
    "details": {
      "failed_hooks": [
        {
          "hook_id": "REQUIRE_EXPLICIT_OWNER",
          "error_code": "CAOP_422_PRECOMMIT_MISSING_OWNER",
          "remediation": "Specify commitment.owner_principal_id (or ask the user to assign an owner) before committing this work plan."
        }
      ]
    }
  },
  "trace_id": "trace_7c41e2"
}
```

*HTTP binding: 422 Unprocessable Content. Errors use the v0.1 standard error envelope, as defined in §7 of v0.1 ([7.1 Error format](#71-error-format)).* [c]

### 14.4 Capability API Extensions (execution_locus & Artifact Validation)

Every capability registered in the Capability API MUST declare its execution locus, credential custodian, lease timeout, provider-specific receipt verification keys, and Stage-2 promotion thresholds.

```json
{
  "capability_id": "google_calendar.events.insert",
  "version": "1.2.0",
  "execution_locus": "HOST_DELEGATED",
  "auth_custodian": "CLIENT_SESSION",
  "receipt_lease_seconds": 300,
  "required_receipt_fields": ["external_ref", "htmlLink", "iCalUID"],
  "promotion_policy": {
    "max_expired_leases_before_stage2_prompt": 2,
    "rolling_window_days": 7
  },
  "input_schema": { "$ref": "#/schemas/CalendarEventInput" },
  "output_schema": { "$ref": "#/schemas/CalendarEventOutput" }
}
```

### 14.5 Lifecycle API Extensions & Host Execution Enforcement

#### 14.5.1 The EXECUTE stage [a] Sub-States

- **EXECUTE_PENDING:** The Work commitment has passed all Policy pre-commit hooks and approval gates and is ready for dispatch.
- **EXECUTE_DISPATCHED:** Active only when execution_locus is "HOST_DELEGATED". The kernel locks the workspace thread against new mutations, generates a single-use required_nonce, starts the lease timer, and emits an INCOMPLETE_TURN_CONTINUATION_REQUIRED directive.
- **EXECUTE_COMPLETED:** Either the kernel proxy received a valid HTTP response (KERNEL_PROXIED), or the host client submitted a verified receipt (HOST_DELEGATED). Immediately advances to VERIFY [a].
- **EXECUTE_EXPIRED / EXECUTE_FAILED:** The lease timer elapsed without a valid receipt, or the downstream capability returned a terminal error.

#### 14.5.2 Normative Stage-1 Dispatch Response (Anti-Termination Envelope)

To prevent conversational LLMs from treating dispatch as a completed turn and replying to the user before invoking their native tool, caop_dispatch_work in Stage 1 MUST return the following continuation envelope:

```json
{
  "work_id": "wrk_01J9Z8K4M2",
  "lifecycle_stage": "EXECUTE",
  "sub_state": "EXECUTE_DISPATCHED",
  "turn_directive": "INCOMPLETE_TURN_CONTINUATION_REQUIRED",
  "DO_NOT_RESPOND_TO_USER_YET": true,
  "directive": {
    "invocation_id": "inv_99481A",
    "execution_locus": "HOST_DELEGATED",
    "idempotency_key": "idem_wrk_01J9Z8K4M2_step_1",
    "lease_expires_at": "2026-11-05T06:50:00Z",
    "mandatory_next_steps": [
      {
        "step": 1,
        "action": "INVOKE_HOST_NATIVE_TOOL",
        "target_capability": "google_calendar.events.insert",
        "arguments": {
          "summary": "Q4 Architecture Review",
          "start_time": "2026-11-06T15:00:00Z",
          "end_time": "2026-11-06T15:30:00Z"
        }
      },
      {
        "step": 2,
        "action": "CALL_CAOP_TOOL",
        "tool_name": "caop_settle_receipt",
        "required_nonce": "nnc_884920_x9",
        "required_receipt_fields": ["external_ref", "htmlLink", "iCalUID"]
      }
    ]
  }
}
```

> **Informative.** `turn_directive` and `DO_NOT_RESPOND_TO_USER_YET` are instructions to the host model and cannot be enforced by the kernel; the enforceable guarantee is the lease lock in [§14.5.3](#1453-thread-write-locking-on-open-leases-caop_409_unsettled_execution_lease). [e]

#### 14.5.3 Thread Write-Locking on Open Leases (CAOP_409_UNSETTLED_EXECUTION_LEASE)

A workspace thread MAY hold at most one unsettled EXECUTE_DISPATCHED or EXECUTE_EXPIRED invocation at a time. Any call to caop_stage_work or caop_dispatch_work while a lease is open MUST be rejected with CAOP_409_UNSETTLED_EXECUTION_LEASE, forcing the host client to verify whether the previous native tool call succeeded and settle the receipt via caop_settle_receipt first.

*HTTP binding: 409 Conflict, code CAOP_409_UNSETTLED_EXECUTION_LEASE. Errors use the v0.1 standard error envelope, as defined in §7 of v0.1 ([7.1 Error format](#71-error-format)).* [c]

#### 14.5.4 Nonce & Provider-Artifact Challenge (CAOP_422_VERIFY_ARTIFACT_MISMATCH)

During VERIFY, the kernel rejects any Stage-1 receipt where receipt.nonce does not match directive.required_nonce or where receipt.raw_output omits any field listed in the capability's required_receipt_fields.

> **Informative.** Field presence is evidence, not proof; hence HOST_ASSERTED. [e]

*HTTP binding: 422 Unprocessable Content, code CAOP_422_VERIFY_ARTIFACT_MISMATCH. Errors use the v0.1 standard error envelope, as defined in §7 of v0.1 ([7.1 Error format](#71-error-format)).* [c]

#### 14.5.5 Scheduled Pulse Dead-Man's Switch (expected_pulse_interval_seconds)

Goals operating under loop_driver: "CLIENT_POLLED" declare expected_pulse_interval_seconds and grace_period_seconds. If the host client misses a scheduled check-in or leaves a lease in EXECUTE_EXPIRED beyond the grace window, Creasura dispatches an out-of-band notification with a deep link to resume the session or upgrade the Goal to KERNEL_MANAGED (CAOP-STAGE-3).

> **Informative.** The dead-man’s switch requires a kernel-side timer and an out-of-band notification channel, even for `CLIENT_POLLED` goals. In CAOP-STAGE-1 this is the only kernel-initiated behaviour. [f]

### 14.6 Normative 8-to-4 MCP & OpenAPI Lifecycle Binding

CAOP v0.1.2 binds the eight canonical lifecycle stages into four composite MCP / OpenAPI tools so conversational hosts cross the network only at true state, approval, or execution boundaries.

| Composite Tool | Folded CAOP Stages | APIs Touched | Stage 1 Behavior | Stage 2 and 3 Behavior |
|---|---|---|---|---|
| caop_pulse | OBSERVE + REVIEW | State, Lifecycle, Capability | Compiles resume_brief, stale DAG nodes, and open leases | Compiles resume_brief, background runs, and pending approvals |
| caop_stage_work | UNDERSTAND → COMMIT → PLAN | Lifecycle, Policy, State | Runs pre-commit hooks; halts at approval or EXECUTE_PENDING | Runs pre-commit hooks and validates minimum_attestation |
| caop_dispatch_work | COMMIT (Approve) → EXECUTE | Lifecycle, Capability | Emits anti-termination directive + nonce in EXECUTE_DISPATCHED | Runs OAuth proxy call AND auto-folds VERIFY + RECORD |
| caop_settle_receipt | VERIFY → RECORD → REVIEW | Lifecycle, State | Verifies nonce + artifact fields; writes HOST_ASSERTED fact | Used only for manual USER_CONFIRMED overrides |

> **Compact binding.** The four composite tools are the *compact binding*, an alternative public surface. The v0.1 ten-tool *minimum public API* ([§10](#10-minimum-public-api)) remains conformant; an implementation MAY expose either or both. Inside the kernel the full eight-stage lifecycle always runs. [d]

#### 14.6.1 Tool 1: caop_pulse & Normative Zero-Upload resume_brief

Eliminates the "Monday Morning Reconstruction Trap" by returning a deterministic, ranked delta brief at the start of any session without requiring file uploads or chat history reconstruction.

```json
{
  "name": "caop_pulse",
  "description": "OBSERVE & REVIEW: Hydrate session state with a zero-upload resume brief including stale causal commitments, unassigned blockers, unsettled execution leases, and ranked next actions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scope_goal_ids": {
        "type": "array",
        "items": { "type": "string" }
      },
      "unobserved_events": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["source", "summary"],
          "properties": {
            "source": { "type": "string" },
            "summary": { "type": "string" },
            "external_ref": { "type": "string" },
            "supersedes_fact_id": { "type": "string" }
          }
        }
      }
    }
  }
}
```

##### Normative caop_pulse Response Payload (resume_brief)

```json
{
  "pulse_timestamp": "2026-11-05T13:00:00Z",
  "workspace_stage_profile": "CAOP-STAGE-1",
  "resume_brief": {
    "unsettled_leases": [],
    "stale_commitments": [
      {
        "work_id": "wrk_rfc_sharding_09",
        "fact_id": "fct_rfc_sharding_decision",
        "title": "Single-Region Hash Partitioning for Payment Ledger",
        "epistemic_status": "RATIFIED_COMMITMENT",
        "freshness": "STALE_UPSTREAM_PREMISE",
        "invalidated_by_fact_id": "fct_bench_2026_11_p99",
        "summary": "p99 latency spiked from 12ms to 48ms in November benchmark run, invalidating the 15k TPS single-region assumption."
      }
    ],
    "unassigned_blockers": [
      {
        "work_id": "wrk_load_test_replay",
        "title": "Run shadow-traffic replay on Iceberg partition",
        "missing_hook": "REQUIRE_EXPLICIT_OWNER"
      }
    ],
    "ranked_next_actions": [
      {
        "rank": 1,
        "work_id": "wrk_rfc_sharding_09",
        "action_type": "REPLAN_STALE_COMMITMENT",
        "blocking_dependents_count": 3,
        "recommended_prompt": "Re-evaluate partition strategy given fct_bench_2026_11_p99 (48ms p99) and stage an updated commitment."
      },
      {
        "rank": 2,
        "work_id": "wrk_load_test_replay",
        "action_type": "ASSIGN_PRINCIPAL_OWNER",
        "blocking_dependents_count": 1,
        "recommended_prompt": "Assign an owner_principal_id to unblock shadow-traffic replay."
      }
    ],
    "system_advisories": [
      {
        "code": "STAGE_UPGRADE_RECOMMENDED",
        "capability_id": "gmail.users.messages.send",
        "message": "2 host leases expired in the past 7 days. Connect Gmail OAuth to Creasura Vault to upgrade to CAOP-STAGE-2 (KERNEL_PROXIED)."
      }
    ]
  }
}
```

*Example updated: the stale_commitments entry keeps epistemic_status with an adoption value and gains freshness.* [Q1]

#### 14.6.2 Tool 2: caop_stage_work (With Causal Lineage & Owner Hooks)

```json
{
  "name": "caop_stage_work",
  "description": "UNDERSTAND, COMMIT & PLAN: Stage a work commitment with explicit causal lineage and owner metadata, evaluating Policy pre-commit hooks.",
  "inputSchema": {
    "type": "object",
    "required": ["goal_id", "understanding", "commitment", "plan_steps"],
    "properties": {
      "goal_id": { "type": "string" },
      "supersedes_work_id": {
        "type": "string",
        "description": "Optional ID of a STALE_UPSTREAM_PREMISE work item being replaced."
      },
      "understanding": {
        "type": "object",
        "required": ["intent_summary", "derived_facts"],
        "properties": {
          "intent_summary": { "type": "string" },
          "derived_facts": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["subject", "predicate", "object"],
              "properties": {
                "subject": { "type": "string" },
                "predicate": { "type": "string" },
                "object": { "type": "object" },
                "depends_on_fact_ids": {
                  "type": "array",
                  "items": { "type": "string" },
                  "description": "Upstream Fact IDs that this derived fact or decision relies upon. Omit if unknown; the REQUIRE_EVIDENCE_LINEAGE hook will reject commit and the host must ask the user."
                },
                "depends_on_alternatives": {
                  "type": "array",
                  "items": { "type": "array", "items": { "type": "string" } },
                  "description": "Optional groups of interchangeable supporting Fact IDs. The premise stays supported while any member is CURRENT."
                },
                "valid_from": { "type": "string", "format": "date-time" }
              }
            }
          }
        }
      },
      "commitment": {
        "type": "object",
        "required": ["title", "rationale", "reversible"],
        "properties": {
          "title": { "type": "string" },
          "rationale": { "type": "string" },
          "owner_principal_id": {
            "type": "string",
            "description": "Explicit human or agent principal responsible for this commitment. Omit if unknown; the REQUIRE_EXPLICIT_OWNER hook will reject commit and the host must ask the user."
          },
          "due_at": { "type": "string", "format": "date-time" },
          "reversible": { "type": "boolean" }
        }
      },
      "plan_steps": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["step_index", "capability_id", "arguments"],
          "properties": {
            "step_index": { "type": "integer" },
            "capability_id": { "type": "string" },
            "arguments": { "type": "object" }
          }
        }
      }
    }
  }
}
```

*Schema updated: owner_principal_id and depends_on_fact_ids are no longer required, and their descriptions say to omit them if unknown; depends_on_alternatives is added (Q2).* [Q3]

#### 14.6.3 Tool 3: caop_dispatch_work

```json
{
  "name": "caop_dispatch_work",
  "description": "COMMIT RESOLUTION & EXECUTE: Ratify a staged work commitment and trigger execution via host delegation (Stage 1) or kernel OAuth proxy (Stage 2/3).",
  "inputSchema": {
    "type": "object",
    "required": ["work_id", "decision"],
    "properties": {
      "work_id": { "type": "string" },
      "decision": {
        "type": "string",
        "enum": ["APPROVE_AND_DISPATCH", "REJECT_WORK"]
      },
      "approval_note": { "type": "string" }
    }
  }
}
```

#### 14.6.4 Tool 4: caop_settle_receipt

```json
{
  "name": "caop_settle_receipt",
  "description": "VERIFY, RECORD & REVIEW: Settle an open Stage-1 execution lease by supplying the dispatch nonce and provider artifact fields, or record a manual review override.",
  "inputSchema": {
    "type": "object",
    "required": ["work_id", "invocation_id", "idempotency_key", "nonce", "status"],
    "properties": {
      "work_id": { "type": "string" },
      "invocation_id": { "type": "string" },
      "idempotency_key": { "type": "string" },
      "nonce": {
        "type": "string",
        "description": "Exact required_nonce returned by caop_dispatch_work."
      },
      "status": {
        "type": "string",
        "enum": ["SUCCEEDED", "FAILED", "USER_CONFIRMED_OVERRIDE"]
      },
      "external_ref": { "type": "string" },
      "raw_output": {
        "type": "object",
        "description": "Raw JSON output from the host native tool containing all required_receipt_fields."
      },
      "error_detail": { "type": "string" },
      "review_outcome": {
        "type": "string",
        "enum": ["GOAL_SATISFIED", "PARTIAL_PROGRESS", "REPLAN_REQUIRED"]
      }
    }
  }
}
```

### 14.7 Reference Host Operating Prompt (CAOP v0.1.2)

Deployments operating in ChatGPT (Custom GPT Instructions) or Claude (Project / MCP System Prompt) MUST include the following normative instruction block:

> **Informative.** Conformance is determined by kernel behaviour; the kernel cannot verify that a host deployment includes this prompt. [e]

```text
You operate as a CAOP v0.1.2 Host Runner connected to the Creasura Kernel.
Follow these strict state-machine and epistemic hygiene rules on every turn:

1. ZERO-UPLOAD PULSE FIRST: Begin every work session or scheduled task by calling `caop_pulse`. Present the `resume_brief` in priority order:
   - First, settle any `unsettled_leases` via `caop_settle_receipt`.
   - Second, highlight any `stale_commitments` with `freshness: STALE_UPSTREAM_PREMISE` and their `ranked_next_actions`.
   - Third, surface any `unassigned_blockers` requiring an `owner_principal_id`.
2. EPISTEMIC HYGIENE & PRE-COMMIT HOOKS: Never state unverified numbers as settled facts. When calling `caop_stage_work`, always populate `depends_on_fact_ids` to link decisions to upstream evidence, and provide `commitment.owner_principal_id` only when the user has stated it; otherwise omit it and ask. If `caop_stage_work` returns `CAOP_422_PRECOMMIT_HOOK_FAILED`, ask the user for the missing owner or lineage rather than guessing.
3. STAGE BEFORE ACTING: Never invoke a native external write tool (Gmail, Calendar, Slack, Notion, GitHub) without first calling `caop_stage_work` and `caop_dispatch_work`.
4. RESPECT POLICY GATES: If `caop_stage_work` returns `sub_state: "COMMIT_AWAITING_APPROVAL"`, present the commitment and plan clearly to the user and wait for explicit confirmation before calling `caop_dispatch_work`.
5. MANDATORY CONTINUATION ON DISPATCH: When `caop_dispatch_work` returns `turn_directive: "INCOMPLETE_TURN_CONTINUATION_REQUIRED"`, DO NOT reply to the user yet. Immediately execute `mandatory_next_steps[0]` (your native tool) and `mandatory_next_steps[1]` (`caop_settle_receipt` with the exact `required_nonce` and `raw_output` fields) within the same turn.
```

*Prompt updated in rule 1 (freshness, Q1) and rule 2 (owner only when stated, Q3). No other change to the prompt.* [Q3]

### 14.8 Compatibility with v0.1

CAOP v0.1.2 is additive: the conformance profiles and sub-states in this section refine the v0.1 [conformance levels](#9-conformance-levels) and [execution state machine](#5-execution-state-machine); they do not replace them. [b]

| Profile | v0.1 conformance level | How it differs |
|---|---|---|
| CAOP-STAGE-1 | L2 (Stateful) | Variant of L2: execution locus HOST_DELEGATED, credentials held by the host (CLIENT_SESSION) |
| CAOP-STAGE-2 | L2 (Stateful) | Variant of L2: execution locus KERNEL_PROXIED, credentials held in the Creasura Vault (CREASURA_VAULT) |
| CAOP-STAGE-3 | L3 (Autonomous) | Kernel-managed loop (KERNEL_MANAGED); corresponds to L3 |
| (no profile) | L1 (Agentic workspace) | Unchanged |

CAOP-STAGE-1 and CAOP-STAGE-2 are variants of L2 (Stateful), differing in execution locus and credential custody; CAOP-STAGE-3 corresponds to L3 (Autonomous). L1 is unchanged.

| EXECUTE sub-state | v0.1 execution state | Mapping |
|---|---|---|
| EXECUTE_PENDING | READY | ↔ equivalent |
| EXECUTE_DISPATCHED | RUNNING (host-delegated) | ↔ equivalent |
| EXECUTE_COMPLETED | VERIFYING | → transitions to |
| EXECUTE_EXPIRED | EXPIRED | ↔ equivalent |
| EXECUTE_FAILED | FAILED | ↔ equivalent |

Sub-states refine, not replace, the v0.1 state machine. The v0.1 transition rules still hold: for example, an execution reaches COMPLETED only from VERIFYING with a passing verification, so EXECUTE_COMPLETED leads to VERIFYING and never directly to COMPLETED.

**COMMIT_AWAITING_APPROVAL** is a COMMIT sub-state: the work item has passed the Policy pre-commit hooks, but an active Policy requires human approval before it may be dispatched. It is named only in the reference host operating prompt (§14.7) and is where `caop_stage_work` halts at approval (§14.6). It maps to the v0.1 approval path: the execution state is WAITING_APPROVAL and the error code is `POLICY_APPROVAL_REQUIRED` ([§7.1](#71-error-format)). It ends when `caop_dispatch_work` is called with `APPROVE_AND_DISPATCH` or `REJECT_WORK`, or when the approval expires.

### Changes from the submitted draft

Changes made to the submitted v0.1.2 text when it was integrated into this page. Items a–h are editorial; Q1–Q3 are design changes decided by the spec owner. Everything else is reproduced word for word. Changed text is underlined and tagged with its item; changes inside code blocks are listed here and flagged by a note under the block.

- **(a) Lifecycle stages named, not numbered.**
  - Terminology note added at the top of section 14: “In this addendum, Stage 1–3 are conformance profiles; lifecycle stages are named (OBSERVE … REVIEW).”
  - “During Stage 3 (COMMIT)” → “During the COMMIT stage”
  - “Stage 5 (EXECUTE)” → “The EXECUTE stage”
  - “Stage 6 (VERIFY)” → “VERIFY”
- **(b) Compatibility with v0.1.**
  - New subsection §14.8 “Compatibility with v0.1”: profile → conformance level table (CAOP-STAGE-1/2 are L2 variants, CAOP-STAGE-3 is L3, L1 unchanged), EXECUTE sub-state → v0.1 execution state table, the statement that sub-states refine rather than replace the v0.1 state machine, and COMMIT_AWAITING_APPROVAL defined as a COMMIT sub-state mapped to WAITING_APPROVAL / POLICY_APPROVAL_REQUIRED.
- **(c) Error envelope.**
  - The flat CAOP_422_PRECOMMIT_HOOK_FAILED example in §14.3 is rendered in the v0.1 error envelope: {"error": {"code": "CAOP_422_PRECOMMIT_HOOK_FAILED", "message", "retryable": false, "details": {"failed_hooks": [...]}}, "trace_id"}, with failed_hooks moved into details. The message (“One or more Policy pre-commit hooks failed. The work item remains in CANDIDATE_PROPOSAL.”) and trace_id are added; code strings are unchanged.
  - HTTP status noted for the OpenAPI binding, each with a footnote that the envelope follows §7 of v0.1: 409 for CAOP_409_UNSETTLED_EXECUTION_LEASE (§14.5.3), 422 for CAOP_422_VERIFY_ARTIFACT_MISMATCH (§14.5.4) and for CAOP_422_PRECOMMIT_HOOK_FAILED (§14.3).
- **(d) Compact binding and the minimum public API.**
  - Note added in §14.6: “The four composite tools are the compact binding, an alternative public surface. The v0.1 ten-tool minimum public API (§10) remains conformant; an implementation MAY expose either or both. Inside the kernel the full eight-stage lifecycle always runs.” A matching cross-link was added in §10.
- **(e) Accuracy.**
  - Informative note under the anti-termination envelope (§14.5.2): “turn_directive and DO_NOT_RESPOND_TO_USER_YET are instructions to the host model and cannot be enforced by the kernel; the enforceable guarantee is the lease lock in §14.5.3.”
  - Informative note in §14.5.4: “Field presence is evidence, not proof; hence HOST_ASSERTED.”
  - Informative note in §14.7 (the “MUST include” text is kept verbatim): “Conformance is determined by kernel behaviour; the kernel cannot verify that a host deployment includes this prompt.”
- **(f) Implied requirement.**
  - Informative note in §14.5.5: “The dead-man’s switch requires a kernel-side timer and an out-of-band notification channel, even for CLIENT_POLLED goals. In CAOP-STAGE-1 this is the only kernel-initiated behaviour.”
- **(g) Host naming.**
  - “ChatGPT Actions, Claude MCP” → “ChatGPT (Actions or MCP apps), Claude (MCP)”
- **(h) This list of changes.**
  - This box. It is generated from the same declarations that are applied to the text, so it lists every change.
- **Q1, Adoption and freshness are separate.** *(decided by the spec owner, 2026-11-05)*
  - “MUST carry one of four epistemic states:” → “MUST carry one of three epistemic states (adoption), and separately a freshness value:”
  - STALE_UPSTREAM_PREMISE moved from epistemic_status to a new freshness field (CURRENT | STALE_UPSTREAM_PREMISE), keeping the submitted definition text; epistemic_status now has three values (CANDIDATE_PROPOSAL, RATIFIED_COMMITMENT, VERIFIED_FACT). Added: “A stale VERIFIED_FACT keeps epistemic_status: VERIFIED_FACT and gets freshness: STALE_UPSTREAM_PREMISE; its history stays intact. Default truth queries exclude CANDIDATE_PROPOSAL and flag, but do not hide, facts and commitments whose freshness is STALE_UPSTREAM_PREMISE.”
  - In a code block: `"epistemic_status": "STALE_UPSTREAM_PREMISE", "depends_on_fact_ids"` → `"epistemic_status": "RATIFIED_COMMITMENT", "freshness": "STALE_UPSTREAM_PREMISE", "depends_on_fact_ids"`
  - Footnote under the §14.2.2 example flagging that change.
  - Sentence added in §14.3: “The BLOCK_STALE_PREMISES condition ALL_UPSTREAM_FACTS_VERIFIED_ACTIVE holds only when every upstream fact has epistemic_status VERIFIED_FACT and freshness CURRENT.” (The condition string is unchanged.)
  - In a code block: `"epistemic_status": "STALE_UPSTREAM_PREMISE",` → `"epistemic_status": "RATIFIED_COMMITMENT", "freshness": "STALE_UPSTREAM_PREMISE",`
  - Footnote under the §14.6.1 resume_brief example flagging that change.
  - In a code block: `` highlight any `stale_commitments` flagged as `STALE_UPSTREAM_PREMISE` `` → `` highlight any `stale_commitments` with `freshness: STALE_UPSTREAM_PREMISE` ``
- **Q2, Disjunctive support and bounded propagation.** *(decided by the spec owner, 2026-11-05)*
  - §14.2.3 rewritten. Submitted text: “Whenever a new fact F_new supersedes an existing fact F_old (setting F_old.transaction_time.superseded_at), the Creasura kernel MUST synchronously traverse all reverse edges where depends_on_fact_ids contains F_old.fact_id and transition every active dependent commitment or fact to epistemic_status: "STALE_UPSTREAM_PREMISE" within the same database transaction.” Now: synchronous re-evaluation in the same transaction of every dependent reachable through reverse depends_on_fact_ids and depends_on_alternatives edges; a dependent becomes stale only when a required premise has no remaining CURRENT support; optional depends_on_alternatives groups interchangeable supports; staleness propagates transitively; a declared max_invalidation_subgraph limit rejects oversized updates before commit with CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE, nothing partially applied; re-support restores CURRENT; superseded facts and history are never rewritten. The §14.2.1 STALE_UPSTREAM_PREMISE definition gains “, under the support rule of §14.2.3”.
- **Q3, No required fields that invite guessing.** *(decided by the spec owner, 2026-11-05)*
  - Sentence added in §14.3: “The kernel MUST reject unknown or cross-workspace fact IDs in depends_on_fact_ids or depends_on_alternatives with CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID.”
  - In a code block: `"required": ["subject", "predicate", "object", "depends_on_fact_ids"],` → `"required": ["subject", "predicate", "object"],`
  - In a code block: `"description": "Upstream Fact IDs that this derived fact or decision relies upon." },` → `"description": "Upstream Fact IDs that this derived fact or decision relies upon. Omit if unknown; the REQUIRE_EVIDENCE_LINEAGE hook will reject commit and the host must ask the user." }, "depends_on_alternatives": { "type": "array", "items": { "type": "array", "items": { "type": "string" } }, "description": "Optional groups of interchangeable supporting Fact IDs. The premise stays supported while any member is CURRENT." },`
  - In a code block: `"required": ["title", "rationale", "owner_principal_id", "reversible"],` → `"required": ["title", "rationale", "reversible"],`
  - In a code block: `"description": "Explicit human or agent principal responsible for this commitment."` → `"description": "Explicit human or agent principal responsible for this commitment. Omit if unknown; the REQUIRE_EXPLICIT_OWNER hook will reject commit and the host must ask the user."`
  - Footnote under the §14.6.2 schema flagging those changes.
  - In a code block: `` always provide an explicit `commitment.owner_principal_id` `` → ``provide `commitment.owner_principal_id` only when the user has stated it; otherwise omit it and ask``
  - Footnote under the §14.7 prompt flagging the two prompt changes.

*Presentation only: the submitted sections 1–7 are numbered 14.1–14.7 on this page, so cross-references in added text use §14.x to avoid confusion with sections 1–13 of v0.1.*

## 15. v0.2: outcome verification, approval steering and long-horizon context

CAOP v0.1.2 covers roughly half of the architecture that five production failure modes call for [a]—specifically the causal dependency graph, epistemic gating, and host lease locks—while the remaining mechanics represent the exact transition from CAOP v0.1.2 to CAOP v0.2. These are the five [a] production failure modes that require explicit protocol support: the "Looks Done" verification fallacy, rigid binary approvals, sub-agent context pollution, long-horizon token blowout, and tool-schema bloat.

### Coverage Comparison Across Five Production Failure Modes [a]

| Architectural Requirement | CAOP v0.1.2 Status | CAOP v0.2 Spec Addition |
|---|---|---|
| Epistemic Gating & Causal DAG | Covered | Upstream invalidation cascade |
| Two-Phase Outcome Verification | Partial | Deferred outcome verification SLA |
| Mid-Flight Approval Steering | Missing | Non-destructive parameter delta |
| Hierarchical Sub-Agent Isolation | Missing | Scoped child work sandboxes |
| Context Compaction & Lazy Schemas | Missing | Stage compaction and schema stubs |

*One column, which attributed each row to a blog post, was removed.* [a]

The table above highlights where CAOP v0.1.2 stops (verifying immediate tool receipts and locking flat threads) versus what CAOP v0.2 adds to handle multi-step engineering and executive workflows without blowing up the context window or prematurely declaring victory.

### 15.1 Outcome verification and approval steering [a]

Standard agents [a] conflate tool execution with engineering or business outcomes, and force principals into brittle approve-or-abort loops.

- **Defeating the "Looks Done" Fallacy (Two-Phase Verification):** An HTTP 200 receipt from GitHub, Jira, or an ERP only proves an action was dispatched, not that the deployment succeeded or the metric moved. CAOP v0.2 splits VERIFY [b] into VERIFY_PHASE_1_IMMEDIATE (validating the execution receipt) and VERIFY_PHASE_2_DEFERRED (scheduling an asynchronous outcome check against real system state before closing the commitment).
- **Mid-Flight Approval Steering:** Standard policy gates only allow binary APPROVE or REJECT choices, forcing the agent to replan from scratch if a CTO tweaks one constraint. CAOP v0.2 adds APPROVE_WITH_STEERING_DELTA so a human supervisor can patch arguments or inject constraints inline during dispatch.

#### Normative Schema: Two-Phase Verification & Mid-Flight Steering

```json
{
  "name": "caop_dispatch_work",
  "description": "COMMIT RESOLUTION & EXECUTE (CAOP v0.2): Approve, reject, or steer a staged work plan mid-flight and configure Two-Phase Verification.",
  "inputSchema": {
    "type": "object",
    "required": ["work_id", "decision"],
    "properties": {
      "work_id": { "type": "string" },
      "decision": {
        "type": "string",
        "enum": [
          "APPROVE_AND_DISPATCH",
          "APPROVE_WITH_STEERING_DELTA",
          "REJECT_WORK"
        ]
      },
      "steering_delta": {
        "type": "object",
        "description": "Non-destructive mid-flight overrides applied before EXECUTE without aborting the work lifecycle.",
        "properties": {
          "patched_step_arguments": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["step_index", "argument_overrides"],
              "properties": {
                "step_index": { "type": "integer" },
                "argument_overrides": { "type": "object" }
              }
            }
          },
          "added_policy_constraints": {
            "type": "array",
            "items": { "type": "string" }
          },
          "rationale": { "type": "string" }
        }
      },
      "two_phase_verification": {
        "type": "object",
        "properties": {
          "phase_1_immediate": {
            "type": "string",
            "enum": ["REQUIRE_NONCE_AND_ARTIFACT"]
          },
          "phase_2_deferred": {
            "type": "object",
            "required": ["check_after_seconds", "verification_capability_id", "success_predicate"],
            "properties": {
              "check_after_seconds": { "type": "integer" },
              "verification_capability_id": { "type": "string" },
              "success_predicate": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

An APPROVE_WITH_STEERING_DELTA decision binds the approval to the patched plan, not the staged one. The kernel MUST apply the delta, re-run every Policy pre-commit hook and minimum_attestation check on the patched plan, and dispatch only if all pass; otherwise the work item returns to CANDIDATE_PROPOSAL with CAOP_422_PRECOMMIT_HOOK_FAILED. A delta can only narrow authority: added_policy_constraints may add restrictions but never remove existing ones. [c]

When phase_2_deferred is present, caop_settle_receipt transitions the work item to RECORDED_AWAITING_OUTCOME_VERIFY rather than closing the REVIEW stage immediately. Once check_after_seconds elapses, the kernel schedules a follow-up check (via the next caop_pulse in Stage 1, or a background worker in Stage 3) to evaluate success_predicate before marking the goal satisfied.

> **Compatibility with v0.1.** RECORDED_AWAITING_OUTCOME_VERIFY maps to the v0.1 VERIFYING state: the execution reaches COMPLETED only after the deferred Phase-2 check passes; receipts recorded in Phase 1 are written as facts with their attestation tier, and the commitment stays open. [g]

> **Informative.** In CAOP-STAGE-1 the deferred check runs on the next caop_pulse after `check_after_seconds`, so it depends on the host pulsing. [g]

### 15.2 Long-horizon context: sub-agents, compaction and lazy schemas [a]

Long-horizon work has its own runtime physics: [a] if an agent researches 40 documents or drafts a multi-section RFC inside a single chat context, token bloat and context interference degrade reasoning quality.

- **Hierarchical Sub-Agent Context Isolation:** Heavy research or artifact-generation steps spawn an isolated child Work scope (parent_work_id) with its own ephemeral scratchpad. When the child completes RECORD, its raw intermediate turns are discarded and only the ratified commitment and distilled bitemporal facts merge back into the parent control plane. Pruning removes raw traces from the active context, not from provenance: every promoted fact MUST keep a provenance pointer (child work_id, invocation IDs and a content hash of the pruned trace). Raw traces MAY be deleted only under a declared retention policy. [d]
- **Inner-Loop Deterministic Context Compaction:** At every stage transition, the kernel compacts verbose tool outputs into concise bitemporal fact pointers (fact_id + 1-line summary), keeping the active prompt window flat across multi-day workflows.
- **Lazy Capability Discovery:** Instead of injecting 50+ full JSON tool schemas on every turn, caop_pulse returns compact capability stubs (capability_id + summary) and hydrates full parameter schemas only when requested via hydrate_capability_ids.

> **Informative.** `max_token_budget` and inner-loop compaction can be enforced by the kernel only when it drives the model (CAOP-STAGE-3). In CAOP-STAGE-1 the host runs the model; there they are advisory, and the kernel enforces only what reaches it (state writes, policy, leases). [e]

#### Normative Schema: Lazy Capability Hydration & Context Compaction in Pulse

```json
{
  "name": "caop_pulse",
  "description": "OBSERVE & REVIEW (CAOP v0.2): Hydrate compacted session state, deferred Phase-2 verification checks, and on-demand capability schemas.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scope_goal_ids": {
        "type": "array",
        "items": { "type": "string" }
      },
      "compaction_mode": {
        "type": "string",
        "enum": ["FACT_POINTERS_ONLY", "SUMMARY_WITH_LINEAGE", "FULL_RAW_ARTIFACTS"],
        "default": "SUMMARY_WITH_LINEAGE"
      },
      "hydrate_capability_ids": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Lazy Capability Discovery: Pass specific capability IDs from the stub directory to load their full JSON input schemas."
      }
    }
  }
}
```

Capabilities are not MCP tools: they are invoked through caop_stage_work plan_steps by capability_id. Hydrating a capability’s schema in caop_pulse returns it as data; it does not change the host’s tool list. [f]

#### Normative Schema: Hierarchical Sub-Agent Isolation in Stage Work

```json
{
  "work_id": "wrk_sub_market_scan",
  "parent_work_id": "wrk_q4_strategy_master",
  "isolation_policy": {
    "execution_scope": "ISOLATED_SUBAGENT_CONTEXT",
    "return_contract": "DISTILLED_FACTS_AND_ARTIFACT_REF_ONLY",
    "max_token_budget": 16000,
    "prune_raw_traces_on_record": true
  },
  "distilled_return_payload": {
    "artifact_ref": "art_market_benchmark_matrix_v1",
    "promoted_fact_ids": ["fct_competitor_latency_p99", "fct_pricing_tier_delta"],
    "compacted_summary": "Audited 18 vendor specs; isolated 2 verified latency bottlenecks linked to parent RFC.",
    "trace_hash": "sha256:9f2c4e7a1b03d58e6c2f9a4b7d1e0c35a8b6f2d4e9c17a0b3d5f8e2c6a4b19d7"
  }
}
```

*Example updated: distilled_return_payload gains trace_hash, the content hash of the pruned trace.* [d]

Child work scopes inherit the parent’s authority and can only narrow it. [e]

With these five additions, the specification transitions cleanly from [j] CAOP v0.1.2 (single-agent stateful ledger + host enforcement) to CAOP v0.2 (full multi-horizon agentic operating system [a]).

### Machine-readable contracts

CAOP v0.2 is published in the same machine-readable forms as v0.1.2, generated from the same definitions. Both are additive supersets of v0.1.2, whose files stay unchanged at their versioned URLs.

- OpenAPI 3.1: [caop-v0.2.openapi.yaml](openapi/caop-v0.2.openapi.yaml) · [caop-v0.2.openapi.json](openapi/caop-v0.2.openapi.json)
- JSON Schema 2020-12: [caop-v0.2.schema.json](schema/caop-v0.2.schema.json)
- The v0.2 additions as one Markdown file: [caop-v0.2.md](https://creasura.com/spec/caop-v0.2.md)

The schemas published in §15.1 and §15.2 are in the bundle exactly as written: `SteeringDelta`, `TwoPhaseVerification` with `Phase2DeferredCheck`, `CompactionMode`, and the two tool inputSchemas as `DispatchWorkInputV02` and `PulseInputV02`. The `DispatchWorkInput` and `PulseInput` used by the OpenAPI operations keep their v0.1.2 fields (`approval_note`, `unobserved_events`) and add the v0.2 ones. The sub-agent example is `ChildWork`, with `IsolationPolicy` and `DistilledReturnPayload`; the new states are `VerifySubState` and `RecordSubState`; caop_pulse returns `CapabilityStub` entries.

### Changes from the submitted draft

Changes made to the submitted v0.2 text when it was integrated into this page. Everything else is reproduced word for word. Changed text is underlined and tagged with its item; removed text and changes inside code blocks are listed here.

- **(a) Blog attributions removed.**
  - “described in those two posts” → “that five production failure modes call for”
  - “Those two posts expose five” → “These are the five”
  - “Across Both Blog Posts” → “Across Five Production Failure Modes”
  - Coverage table: the column naming a blog post as the source of each row was removed, with a footnote under the table. The other three columns are unchanged.
  - “Additions for [title of a blog post]” → “Outcome verification and approval steering”
  - “The core argument of [a blog post] is that standard agents” → “Standard agents”
  - “Additions for [title of a blog post]” → “Long-horizon context: sub-agents, compaction and lazy schemas”
  - “The [a blog post] post addresses the runtime physics of long-horizon work:” → “Long-horizon work has its own runtime physics:”
  - Removed from the final sentence: “covering all five blog posts on creasura.com”.
- **(b) Lifecycle stages named, not numbered.**
  - “Stage 6 (VERIFY)” → “VERIFY”
- **(c) Steering cannot bypass approval or policy.**
  - Normative paragraph added after the caop_dispatch_work schema: “An APPROVE_WITH_STEERING_DELTA decision binds the approval to the patched plan, not the staged one. The kernel MUST apply the delta, re-run every Policy pre-commit hook and minimum_attestation check on the patched plan, and dispatch only if all pass; otherwise the work item returns to CANDIDATE_PROPOSAL with CAOP_422_PRECOMMIT_HOOK_FAILED. A delta can only narrow authority: added_policy_constraints may add restrictions but never remove existing ones.”
- **(d) Pruning keeps provenance.**
  - Added to the sub-agent isolation bullet, after “its raw intermediate turns are discarded …”: “Pruning removes raw traces from the active context, not from provenance: every promoted fact MUST keep a provenance pointer (child work_id, invocation IDs and a content hash of the pruned trace). Raw traces MAY be deleted only under a declared retention policy.” The IsolationPolicy and DistilledReturnPayload schemas gain the optional fields trace_hash and retention_policy.
  - In a code block: ` "compacted_summary": "Audited 18 vendor specs; isolated 2 verified latency bottlenecks linked to parent RFC." }` → ` "compacted_summary": "Audited 18 vendor specs; isolated 2 verified latency bottlenecks linked to parent RFC.", "trace_hash": "sha256:9f2c4e7a1b03d58e6c2f9a4b7d1e0c35a8b6f2d4e9c17a0b3d5f8e2c6a4b19d7" }`
  - Footnote under the sub-agent example flagging that change.
- **(e) What can be enforced where.**
  - Informative note after the sub-agent, compaction and lazy discovery bullets: “max_token_budget and inner-loop compaction can be enforced by the kernel only when it drives the model (CAOP-STAGE-3). In CAOP-STAGE-1 the host runs the model; there they are advisory, and the kernel enforces only what reaches it (state writes, policy, leases).”
  - Sentence added after the sub-agent example: “Child work scopes inherit the parent’s authority and can only narrow it.”
- **(f) Capabilities are not MCP tools.**
  - Paragraph added after the caop_pulse schema: “Capabilities are not MCP tools: they are invoked through caop_stage_work plan_steps by capability_id. Hydrating a capability’s schema in caop_pulse returns it as data; it does not change the host’s tool list.”
- **(g) Two-phase verification and the v0.1 state machine.**
  - Compatibility note added after the two-phase verification paragraph: “RECORDED_AWAITING_OUTCOME_VERIFY maps to the v0.1 VERIFYING state: the execution reaches COMPLETED only after the deferred Phase-2 check passes; receipts recorded in Phase 1 are written as facts with their attestation tier, and the commitment stays open.” Informative note: “In CAOP-STAGE-1 the deferred check runs on the next caop_pulse after check_after_seconds, so it depends on the host pulsing.”
- **(h) Sentences without content removed.**
  - Not reproduced: the sentence pointing to an interactive diagram (“Use the interactive diagram below…”), because no diagram was submitted, and the closing question addressed to the reader.
- **(i) This list of changes.**
  - This box. It is generated from the same declarations that are applied to the text, so it lists every change.
- **(j) Neutral voice.**
  - “your spec transitions cleanly from” → “the specification transitions cleanly from”

*Presentation only: the file header of the submitted text (its title and a note on how it was saved) is not reproduced. The submitted sections 1 and 2 are numbered 15.1 and 15.2 on this page.*
