# Creasura Agentic OS Protocol (CAOP) v0.1

Definition, lifecycle, and API contracts for an open, portable agentic operating system.

**Version:** 0.1 · **Project:** Creasura One OSS · **Date:** November 1, 2026  
Machine-readable contracts: [OpenAPI 3.1](openapi/caop-v0.1.openapi.yaml) · [JSON Schema 2020-12](schema/caop-v0.1.schema.json)

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

> The lifecycle is a coordination protocol, not a rigid prompt chain.

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

> Programmatic invocation of an assistant’s native work surfaces must use an explicitly supported interface. Do not assume arbitrary sessions can be launched through MCP.

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

> Dry run, ContextLease, and compensation operations are part of the Business Profile, not the core.

## 13. Machine-readable contracts

CAOP v0.1 is published in two machine-readable forms generated from the same definitions:

- [**OpenAPI 3.1 contract**](openapi/caop-v0.1.openapi.yaml): every lifecycle operation, request, response, and error, with the MCP tool each one backs. [YAML](openapi/caop-v0.1.openapi.yaml) · [JSON](openapi/caop-v0.1.openapi.json)
- [**JSON Schema 2020-12**](schema/caop-v0.1.schema.json): every object in this specification, in one bundle. [caop-v0.1.schema.json](schema/caop-v0.1.schema.json)
