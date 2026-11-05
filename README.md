# CAOP: Creasura Agentic OS Protocol

**Version 0.2** · [creasura.com/spec](https://creasura.com/spec/)

CAOP defines an **Agentic Operating System**: a persistent, event-driven system that coordinates intelligent agents, tools, knowledge, and human decisions to achieve goals over time, while maintaining durable state, enforcing policies, verifying outcomes, and recovering from failures.

It is the protocol behind Creasura One OSS. It is model-independent and framework-independent: assistants like ChatGPT or Claude reason, research, and draft; CAOP defines what valid work is, which state transitions are allowed, what evidence is required, and who can authorize an action.

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

As of November 5, 2026, Creasura’s reference kernel conforms to CAOP v0.1.2 at CAOP-STAGE-1 (host-delegated execution). Of the five v0.2 mechanisms it implements two, at CAOP-STAGE-1. The other three are specified but not yet implemented, so the reference kernel does not yet conform to v0.2 as a whole.

| v0.2 mechanism | Section | Reference kernel |
|---|---|---|
| Two-phase outcome verification | [§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a) | Implemented |
| Mid-flight approval steering | [§15.1](SPEC.md#151-outcome-verification-and-approval-steering-a) | Implemented |
| Hierarchical sub-agent isolation | [§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |
| Inner-loop context compaction | [§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |
| Lazy capability discovery | [§15.2](SPEC.md#152-long-horizon-context-sub-agents-compaction-and-lazy-schemas-a) | Specified, not yet implemented |

Notes for implementers:

- In the reference kernel, a verification capability (`verification_capability_id`) must be side-effect-free: it may only read external state. Dispatch refuses a deferred check whose capability is not registered as side-effect-free.
- On `APPROVE_WITH_STEERING_DELTA`, the reference kernel re-runs every policy check on the patched plan (every Policy pre-commit hook and the `minimum_attestation` check) before it dispatches.

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
