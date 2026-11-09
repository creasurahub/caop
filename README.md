# CAOP: Creasura Agentic OS Protocol

**Version 0.2** · [creasura.com/spec](https://creasura.com/spec/)

CAOP defines an **Agentic Operating System**: a persistent, event-driven system that coordinates intelligent agents, tools, knowledge, and human decisions to achieve goals over time, while maintaining durable state, enforcing policies, verifying outcomes, and recovering from failures.

It is the protocol behind Creasura One OSS. It is model-independent and framework-independent: assistants like ChatGPT or Claude reason, research, and draft; CAOP defines what valid work is, which state transitions are allowed, what evidence is required, and who can authorize an action.

## Start here

A runtime profile says who drives the model and who runs external actions. Each maps to a v0.1 [conformance level](SPEC.md#9-conformance-levels) ([§14.1](SPEC.md#141-runtime-conformance-stages-normative-profiles), [§14.8](SPEC.md#148-compatibility-with-v01)).

| Profile | Who drives turns | Who runs external actions | Conformance level |
|---|---|---|---|
| **CAOP-STAGE-1** (host-delegated) | The host (for example ChatGPT) | The host, with its own connectors; receipts are at most HOST_ASSERTED | L2 (Stateful) |
| **CAOP-STAGE-2** (kernel-proxied) | The host | The kernel, with its own credentials | L2 (Stateful) |
| **CAOP-STAGE-3** (autonomous kernel) | The kernel, driven by events | The kernel | L3 (Autonomous) |

L1 (agentic workspace) is unchanged; it has no runtime profile.

CAOP has two public tool surfaces. Both are conformant; an implementation may expose either or both. Both are listed under [Public MCP tools](#public-mcp-tools) below. A minimal compact sequence, at CAOP-STAGE-1:

1. `caop_pulse`: Resume. The kernel returns current facts, stale commitments, open leases and capability stubs.
2. `caop_stage_work`: Stage facts, a commitment and plan steps. Policy pre-commit hooks run here; a missing owner or evidence lineage returns a specific blocker.
3. `caop_dispatch_work`: Approve, or approve with a steering delta, and dispatch. In CAOP-STAGE-1 the response holds an execution lease and a single-use nonce.
4. `caop_settle_receipt`: Report the result. The kernel checks the nonce and the required receipt fields, then records the outcome with its attestation tier.

Between calls 3 and 4 the host runs the action with its own connector. That is not a CAOP call.

Where to read next, in [`SPEC.md`](SPEC.md#start-here-caop-v02-in-brief):

- [Implementation status](SPEC.md#implementation-status): what Creasura’s reference kernel implements today, by runtime profile.
- [Section 14](SPEC.md#14-v012-conformance-stages-causal-state-and-host-enforcement): v0.1.2 runtime profiles, causal state and host enforcement.
- [Section 15](SPEC.md#15-v02-outcome-verification-approval-steering-and-long-horizon-context): the v0.2 additions, also published on their own as [CAOP v0.2: additions and release notes](https://creasura.com/spec/v0.2/).
- Contracts: [OpenAPI 3.1](openapi/caop-v0.2.openapi.yaml) (17 operations) and [JSON Schema 2020-12](schema/caop-v0.2.schema.json) (95 definitions).
- [Editorial history](SPEC.md#editorial-history): how the submitted texts of sections 14 and 15 were edited.

## What’s in this repository

| Path | Contents |
|---|---|
| [`SPEC.md`](SPEC.md) | The CAOP v0.2 specification (sections 1–13 from v0.1, section 14 added in v0.1.2, section 15 added in v0.2) |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history |
| [`openapi/caop-v0.2.openapi.yaml`](openapi/caop-v0.2.openapi.yaml) | v0.2 (current): OpenAPI 3.1 contract for the lifecycle API (17 operations), also as [JSON](openapi/caop-v0.2.openapi.json) |
| [`schema/caop-v0.2.schema.json`](schema/caop-v0.2.schema.json) | v0.2 (current): JSON Schema 2020-12 bundle (95 definitions in `$defs`) |
| [`openapi/caop-v0.1.2.openapi.yaml`](openapi/caop-v0.1.2.openapi.yaml) | v0.1.2 (previous, unchanged): OpenAPI 3.1 contract for the lifecycle API (17 operations), also as [JSON](openapi/caop-v0.1.2.openapi.json) |
| [`schema/caop-v0.1.2.schema.json`](schema/caop-v0.1.2.schema.json) | v0.1.2 (previous, unchanged): JSON Schema 2020-12 bundle (81 definitions in `$defs`) |
| [`openapi/caop-v0.1.openapi.yaml`](openapi/caop-v0.1.openapi.yaml) | v0.1 (previous, unchanged): OpenAPI 3.1 contract for the lifecycle API (13 operations), also as [JSON](openapi/caop-v0.1.openapi.json) |
| [`schema/caop-v0.1.schema.json`](schema/caop-v0.1.schema.json) | v0.1 (previous, unchanged): JSON Schema 2020-12 bundle (44 definitions in `$defs`) |
| [`examples/`](examples/) | 71 v0.2 example payloads, each validated against its schema (one per definition, covering all 29 v0.1 definitions) |

Each version is an additive superset of the one before (v0.1 ⊂ v0.1.2 ⊂ v0.2): every v0.1 document is also valid under v0.2. Published contract files never change at their versioned paths.

| Version | Operations | Schemas | Examples |
|---|---|---|---|
| v0.2 | 17 | 95 | 71 |
| v0.1.2 | 17 | 81 | 57 |
| v0.1 | 13 | 44 | 29 |

## What’s new in v0.2

- **Two-phase outcome verification:** VERIFY splits into VERIFY_PHASE_1_IMMEDIATE (the execution receipt) and VERIFY_PHASE_2_DEFERRED (a later check of `success_predicate` with `verification_capability_id`); meanwhile the work is RECORDED_AWAITING_OUTCOME_VERIFY, which maps to the v0.1 VERIFYING state, and the execution reaches COMPLETED only after the deferred check passes ([§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a)).
- **Mid-flight approval steering:** `APPROVE_WITH_STEERING_DELTA` with a `steering_delta` patches step arguments or adds policy constraints at dispatch. The approval binds to the patched plan, every Policy pre-commit hook and `minimum_attestation` check re-runs on it, and a delta can only narrow authority ([§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a)).
- **Hierarchical sub-agent isolation:** child work scopes (`parent_work_id`, `isolation_policy`) return only a `distilled_return_payload`; pruned raw traces keep a provenance pointer (`trace_hash`), and a child inherits its parent’s authority and can only narrow it ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)).
- **Inner-loop context compaction:** `compaction_mode` on `caop_pulse` (FACT_POINTERS_ONLY, SUMMARY_WITH_LINEAGE, FULL_RAW_ARTIFACTS) ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)).
- **Lazy capability discovery:** `caop_pulse` returns capability stubs and hydrates full input schemas only for `hydrate_capability_ids`, as data; capabilities are not MCP tools ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)).

See [`CHANGELOG.md`](CHANGELOG.md) and [section 15 of the specification](SPEC.md#15-v02-outcome-verification-approval-steering-and-long-horizon-context).

## Implementation status

As of November 5, 2026, Creasura’s reference kernel implements CAOP v0.2, including all five v0.2 mechanisms, at CAOP-STAGE-1 (host-delegated execution), with three exceptions: the pulse dead-man’s switch detects missed check-ins but does not yet deliver the out-of-band notification; approvals do not expire because no expiry period is defined; and approvals are not yet bound to an individual approver, because each workspace has a single authenticated principal. Parts of section 15 that only the kernel can enforce when it drives the model (CAOP-STAGE-3) are recorded and reported as advisory, as section 15 specifies.

**Status by runtime profile, as of November 5, 2026**

| Feature | CAOP-STAGE-1 | CAOP-STAGE-2 | CAOP-STAGE-3 |
|---|---|---|---|
| **Two-phase outcome verification** ([§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a)) | Implemented (reference kernel) | Specified | Specified |
| **Mid-flight approval steering** ([§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a)) | Implemented (reference kernel) | Specified | Specified |
| **Hierarchical sub-agent isolation** ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)) | Implemented (reference kernel) | Specified | Specified |
| **Inner-loop context compaction** ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)) | Implemented (reference kernel) | Specified | Specified |
| **Lazy capability discovery** ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)) | Implemented (reference kernel) | Specified | Specified |
| **Model-side context control** ([§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a)) Compacting the host’s own conversation context, compaction at every stage transition, enforcing `max_token_budget` (recorded and flagged as an advisory instead), and a separate model context for a child’s turns. | Advisory only | Advisory only | Requires this profile |
| **Pulse notification delivery** ([§14.5.5](SPEC.md#1455-scheduled-pulse-dead-mans-switch-expected_pulse_interval_seconds)) The pulse dead-man’s switch detects missed check-ins but does not yet deliver the out-of-band notification. | Specified | Specified | Does not apply |
| **Approval expiry** ([§7](SPEC.md#7-cross-cutting-contracts)) Approvals do not expire because no expiry period is defined. | Specified | Specified | Specified |
| **Approver binding** ([§7](SPEC.md#7-cross-cutting-contracts)) Approvals are not yet bound to an individual approver, because each workspace has a single authenticated principal. | Specified | Specified | Specified |

- **Implemented (reference kernel):** specified, and implemented by Creasura’s reference kernel at this profile.
- **Specified:** specified for this profile; the reference kernel does not implement it here yet.
- **Requires this profile:** needs this profile, because only a kernel that drives the model can enforce it; specified, not yet implemented.
- **Advisory only:** below the profile it needs: recorded and reported, not enforced.
- **Does not apply:** the protocol does not ask for it at this profile.

Notes for implementers:

- In the reference kernel, a verification capability (`verification_capability_id`) must be side-effect-free: it may only read external state. Dispatch refuses a deferred check whose capability is not registered as side-effect-free.
- On `APPROVE_WITH_STEERING_DELTA`, the reference kernel re-runs every policy check on the patched plan (every Policy pre-commit hook and the `minimum_attestation` check) before it dispatches.
- Child work scopes inherit the parent’s authority and can only narrow it; a distilled return merges only the child’s promoted facts, each with a provenance pointer and a verifiable `trace_hash`; raw child traces are pruned from active context and deleted only under a declared `retention_policy`.
- Compaction applies to what the kernel returns (`caop_pulse`, in all three `compaction_mode` levels) and is retrievable; capability schemas are hydrated as data and never change the host’s tool list.
- CAOP-STAGE-3 only, not available at CAOP-STAGE-1: compacting the host’s own conversation context, compaction at every stage transition, enforcing `max_token_budget` (recorded and flagged as an advisory instead), and a separate model context for a child’s turns.

### Runtime checks beyond the schema

JSON Schema checks the shape of a request. Some obligations of the protocol are not in the schemas, so the kernel checks them at run time. The reference kernel enforces, among others:

- Provenance on promoted facts: a distilled return merges a fact only with its provenance pointer and a verifiable `trace_hash`. The schema leaves `trace_hash` optional; the prose of §15.2 requires it.
- Receipt nonce: a Stage-1 receipt must echo the `required_nonce` from dispatch (`CAOP_422_VERIFY_ARTIFACT_MISMATCH` otherwise).
- Required receipt fields: the receipt’s `raw_output` must hold every field in the capability’s `required_receipt_fields`.
- One open lease per thread: new work is refused while an execution lease is unsettled (`CAOP_409_UNSETTLED_EXECUTION_LEASE`).
- Policy hooks at commit and on steering: every Policy pre-commit hook runs at commit, and runs again on the patched plan after `APPROVE_WITH_STEERING_DELTA`, with the `minimum_attestation` check.
- Side-effect-free verifier: a deferred check is dispatched only if its `verification_capability_id` is registered as side-effect-free.

Passing JSON Schema validation is therefore not proof of runtime conformance.

## The model at a glance

- **Five abstractions:** Goal, Work, State, Capability, Policy.
- **Eight lifecycle stages:** Observe → Understand → Commit → Plan → Execute → Verify → Record → Review. A coordination protocol, not a prompt chain.
- **Execution state machine:** `CREATED → READY → RUNNING → VERIFYING → COMPLETED`, with `WAITING_APPROVAL`, `BLOCKED`, `FAILED` (retry), and terminal `CANCELLED` / `EXPIRED`. Invalid transitions are rejected.
- **Advisory vs. enforced policy:** a policy in an assistant’s instructions is advisory; a policy checked by the runtime before an action is a control.
- **Cross-cutting contracts:** identity, authorization, idempotency, version checks, provenance, correlation, recovery, scoped and expiring approvals, audit, data isolation, versioning.
- **Conformance levels:** L1 agentic workspace, L2 stateful OS, L3 autonomous OS.
- **Business Profile (CAOP-Biz):** metric trees, Delegation of Authority, bitemporal facts, and two-phase verification.

## Public MCP tools

Assistants see ten outcome-oriented tools. Each maps to one endpoint in the OpenAPI contract (`x-caop-mcp-tool`):

| MCP tool | Endpoint |
|---|---|
| `observe` | `POST /v1/observations` |
| `get_context` | `POST /v1/context/resolve` |
| `create_commitment` | `POST /v1/commitments` |
| `list_commitments` | `GET /v1/commitments` |
| `propose_plan` | `POST /v1/plans` |
| `start_work` | `POST /v1/executions` |
| `get_work_status` | `GET /v1/executions/{execution_id}` |
| `submit_result` | `POST /v1/executions/{execution_id}/results` |
| `review_goals` | `POST /v1/reviews` |
| `approve_action` | `POST /v1/approvals/{approval_request_id}/decision` |

### Compact binding

An alternative public surface, added in v0.1.2: 4 composite tools, each folding several lifecycle stages (`x-caop-stage`). The ten-tool API above remains conformant; an implementation may expose either or both. See [§14.6](SPEC.md#146-normative-8-to-4-mcp--openapi-lifecycle-binding); v0.2 adds the request fields below ([section 15](SPEC.md#15-v02-outcome-verification-approval-steering-and-long-horizon-context)).

| MCP tool | Endpoint | Folded stages | Request fields added in v0.2 |
|---|---|---|---|
| `caop_pulse` | `POST /v1/compact/pulse` | Observe + Review | `compaction_mode`, `hydrate_capability_ids` |
| `caop_stage_work` | `POST /v1/compact/stage-work` | Understand + Commit + Plan | `parent_work_id`, `isolation_policy` |
| `caop_dispatch_work` | `POST /v1/compact/dispatch-work` | Commit + Execute | `steering_delta`, `two_phase_verification` |
| `caop_settle_receipt` | `POST /v1/compact/settle-receipt` | Verify + Record + Review | `distilled_return_payload` |

## Using the schemas

Reference a definition from the bundle by JSON Pointer, for example:

```json
{ "$ref": "https://creasura.com/spec/caop-v0.2.schema.json#/$defs/Commitment" }
```

Domain objects (Goal, WorkItem, Fact, Capability, Policy, Capability API) use camelCase, as in the specification’s interfaces. Lifecycle API payloads use snake_case, as on the wire.

## Learn more

- [Specification on creasura.com](https://creasura.com/spec/) · [What’s new in v0.2](https://creasura.com/spec/v0.2/) · [OpenAPI contract](https://creasura.com/spec/openapi/) · [JSON Schema](https://creasura.com/spec/schema/)
- [Behind the scenes: CAOP, walked through with a real estate deal](https://creasura.com/blog/agentic-os-spec-behind-the-scenes/)
- [Behind the scenes: CAOP as a business operating system](https://creasura.com/blog/caop-business-profile/)

## License

[MIT](LICENSE) © 2026 Creasura
