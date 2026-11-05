# CAOP: Creasura Agentic OS Protocol

**Version 0.1.2** · [creasura.com/spec](https://creasura.com/spec/)

CAOP defines an **Agentic Operating System**: a persistent, event-driven system that coordinates intelligent agents, tools, knowledge, and human decisions to achieve goals over time, while maintaining durable state, enforcing policies, verifying outcomes, and recovering from failures.

It is the protocol behind Creasura One OSS. It is model-independent and framework-independent: assistants like ChatGPT or Claude reason, research, and draft; CAOP defines what valid work is, which state transitions are allowed, what evidence is required, and who can authorize an action.

## What’s in this repository

| Path | Contents |
|---|---|
| [`SPEC.md`](SPEC.md) | The CAOP v0.1.2 specification (sections 1–13 from v0.1, section 14 added in v0.1.2) |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history |
| [`openapi/caop-v0.1.2.openapi.yaml`](openapi/caop-v0.1.2.openapi.yaml) | v0.1.2 (current): OpenAPI 3.1 contract for the lifecycle API (17 operations), also as [JSON](openapi/caop-v0.1.2.openapi.json) |
| [`schema/caop-v0.1.2.schema.json`](schema/caop-v0.1.2.schema.json) | v0.1.2 (current): JSON Schema 2020-12 bundle (81 definitions in `$defs`) |
| [`openapi/caop-v0.1.openapi.yaml`](openapi/caop-v0.1.openapi.yaml) | v0.1 (previous, unchanged): OpenAPI 3.1 contract for the lifecycle API (13 operations), also as [JSON](openapi/caop-v0.1.openapi.json) |
| [`schema/caop-v0.1.schema.json`](schema/caop-v0.1.schema.json) | v0.1 (previous, unchanged): JSON Schema 2020-12 bundle (44 definitions in `$defs`) |
| [`examples/`](examples/) | 57 v0.1.2 example payloads, each validated against its schema (one per definition, covering all 29 v0.1 definitions) |

v0.1.2 is an additive superset of v0.1: every v0.1 document is also valid under v0.1.2. Published contract files never change at their versioned paths.

| Version | Operations | Schemas | Examples |
|---|---|---|---|
| v0.1.2 | 17 | 81 | 57 |
| v0.1 | 13 | 44 | 29 |

## What’s new in v0.1.2

- **Runtime conformance profiles** CAOP-STAGE-1/2/3 (host-delegated, kernel-proxied, autonomous kernel), mapped onto the v0.1 conformance levels ([§14.1](SPEC.md#141-runtime-conformance-stages-normative-profiles), [§14.8](SPEC.md#148-compatibility-with-v01)).
- **Adoption vs. freshness:** `epistemic_status` (CANDIDATE_PROPOSAL, RATIFIED_COMMITMENT, VERIFIED_FACT) records adoption; a separate `freshness` (CURRENT, STALE_UPSTREAM_PREMISE) records whether a fact’s premises still hold ([§14.2.1](SPEC.md#1421-epistemic-status-enum-epistemic_status)).
- **Alternatives-aware, bounded causal invalidation:** facts declare `depends_on_fact_ids` and optional `depends_on_alternatives`; a dependent turns stale only when a required premise has no remaining CURRENT support, and propagation is bounded ([§14.2.3](SPEC.md#1423-synchronous-causal-invalidation-rule)).
- **Policy pre-commit hooks:** deterministic checks evaluated at COMMIT before work can be dispatched or sent for approval; a failure keeps the work item a CANDIDATE_PROPOSAL and returns `CAOP_422_PRECOMMIT_HOOK_FAILED` ([§14.3](SPEC.md#143-policy-api--deterministic-pre-commit-hooks)).
- **Capability `execution_locus` and receipts:** capabilities declare execution locus, credential custody, receipt lease, required receipt fields and promotion policy ([§14.4](SPEC.md#144-capability-api-extensions-execution_locus--artifact-validation)).
- **EXECUTE sub-states** with a lease lock on the thread (`CAOP_409_UNSETTLED_EXECUTION_LEASE`) and nonce and provider-artifact checks on receipts (`CAOP_422_VERIFY_ARTIFACT_MISMATCH`) ([§14.5](SPEC.md#145-lifecycle-api-extensions--host-execution-enforcement)).
- **Pulse dead-man’s switch:** `expected_pulse_interval_seconds` with a kernel-side timer and out-of-band notification ([§14.5.5](SPEC.md#1455-scheduled-pulse-dead-mans-switch-expected_pulse_interval_seconds)).
- **Attestation tiers:** `provenance.attestation` is HOST_ASSERTED, KERNEL_ATTESTED or USER_CONFIRMED ([§14.2.4](SPEC.md#1424-provenance-attestation-tiers-provenanceattestation)).
- **Compact binding:** four composite tools, `caop_pulse`, `caop_stage_work`, `caop_dispatch_work` and `caop_settle_receipt`, that fold the eight lifecycle stages; the v0.1 ten-tool API remains conformant ([§14.6](SPEC.md#146-normative-8-to-4-mcp--openapi-lifecycle-binding)).

See [`CHANGELOG.md`](CHANGELOG.md) and [section 14 of the specification](SPEC.md#14-v012-conformance-stages-causal-state-and-host-enforcement).

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

### Compact binding (v0.1.2)

An alternative public surface: 4 composite tools, each folding several lifecycle stages (`x-caop-stage`). The ten-tool API above remains conformant; an implementation may expose either or both. See [§14.6](SPEC.md#146-normative-8-to-4-mcp--openapi-lifecycle-binding).

| MCP tool | Endpoint | Folded stages |
|---|---|---|
| `caop_pulse` | `POST /v1/compact/pulse` | Observe + Review |
| `caop_stage_work` | `POST /v1/compact/stage-work` | Understand + Commit + Plan |
| `caop_dispatch_work` | `POST /v1/compact/dispatch-work` | Commit + Execute |
| `caop_settle_receipt` | `POST /v1/compact/settle-receipt` | Verify + Record + Review |

## Using the schemas

Reference a definition from the bundle by JSON Pointer, for example:

```json
{ "$ref": "https://creasura.com/spec/caop-v0.1.2.schema.json#/$defs/Commitment" }
```

Domain objects (Goal, WorkItem, Fact, Capability, Policy, Capability API) use camelCase, as in the specification’s interfaces. Lifecycle API payloads use snake_case, as on the wire.

## Learn more

- [Specification on creasura.com](https://creasura.com/spec/) · [OpenAPI contract](https://creasura.com/spec/openapi/) · [JSON Schema](https://creasura.com/spec/schema/)
- [Behind the scenes: CAOP, walked through with a real estate deal](https://creasura.com/blog/agentic-os-spec-behind-the-scenes/)
- [Behind the scenes: CAOP as a business operating system](https://creasura.com/blog/caop-business-profile/)

## License

[MIT](LICENSE) © 2026 Creasura
