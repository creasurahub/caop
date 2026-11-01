# CAOP: Creasura Agentic OS Protocol

**Version 0.1** · [creasura.com/spec](https://creasura.com/spec/)

CAOP defines an **Agentic Operating System**: a persistent, event-driven system that coordinates intelligent agents, tools, knowledge, and human decisions to achieve goals over time, while maintaining durable state, enforcing policies, verifying outcomes, and recovering from failures.

It is the protocol behind Creasura One OSS. It is model-independent and framework-independent: assistants like ChatGPT or Claude reason, research, and draft; CAOP defines what valid work is, which state transitions are allowed, what evidence is required, and who can authorize an action.

## What’s in this repository

| Path | Contents |
|---|---|
| [`SPEC.md`](SPEC.md) | The CAOP v0.1 specification |
| [`openapi/caop-v0.1.openapi.yaml`](openapi/caop-v0.1.openapi.yaml) | OpenAPI 3.1 contract for the lifecycle API (13 operations), also as [JSON](openapi/caop-v0.1.openapi.json) |
| [`schema/caop-v0.1.schema.json`](schema/caop-v0.1.schema.json) | JSON Schema 2020-12 bundle (44 definitions in `$defs`) |
| [`examples/`](examples/) | 29 example payloads, each validated against its schema |

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

## Using the schemas

Reference a definition from the bundle by JSON Pointer, for example:

```json
{ "$ref": "https://creasura.com/spec/caop-v0.1.schema.json#/$defs/Commitment" }
```

Domain objects (Goal, WorkItem, Fact, Capability, Policy, Capability API) use camelCase, as in the specification’s interfaces. Lifecycle API payloads use snake_case, as on the wire.

## Learn more

- [Specification on creasura.com](https://creasura.com/spec/) · [OpenAPI contract](https://creasura.com/spec/openapi/) · [JSON Schema](https://creasura.com/spec/schema/)
- [Behind the scenes: CAOP, walked through with a real estate deal](https://creasura.com/blog/agentic-os-spec-behind-the-scenes/)
- [Behind the scenes: CAOP as a business operating system](https://creasura.com/blog/caop-business-profile/)

## License

[MIT](LICENSE) © 2026 Creasura
