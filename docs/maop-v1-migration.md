# Migrating from CAOP v0.2 to MAOP v1

**Status:** DRAFT · **MAOP version:** 1.0.0-draft.1 · **Baseline:** CAOP v0.2 at commit `8c7bd07939171efc2d39079bd018904175ea8db2`

MAOP v1 (Multi-Agent Orchestration Protocol) succeeds CAOP v0.2. It keeps every CAOP v0.2 operation and definition and adds multi-agent supervision on top. This guide covers compatibility, client and server migration, conformance levels, a proposed deprecation timeline and the open questions. The full mapping is in [`docs/maop-v1-parity.md`](maop-v1-parity.md) and [`tests/parity.json`](../tests/parity.json). The specification is [`docs/maop-v1.md`](maop-v1.md).

## 1. Compatibility policy

1. **CAOP contracts are frozen.** The CAOP v0.1, v0.1.2 and v0.2 contract files are not edited, regenerated or reformatted. Their sha256 values at the baseline commit are below. `tests/validate.py` checks them, and so does the generator of `tests/parity.json`.

   | File | sha256 |
   |---|---|
   | `openapi/caop-v0.1.openapi.yaml` | `272fd7face00997359c9d185851995d9397281846ce6166d25a32e98f16a622f` |
   | `openapi/caop-v0.1.openapi.json` | `076a128385a1bc7d4841d1447cf3b2a4eedfc612ad393c3b14d0714f9857a4eb` |
   | `schema/caop-v0.1.schema.json` | `4cc2cda6f49926efa8521aa5dabd66803b23691ce8a7488c51f0477798005ded` |
   | `openapi/caop-v0.1.2.openapi.yaml` | `05dd1dfbe6449cc5447420023f336aa48c7221d229219cbd17396da4bf9be8b4` |
   | `openapi/caop-v0.1.2.openapi.json` | `6b727a0fa60efc1f487fe154d3eb3fe63c3f1e7121a89962a553116b04b005a8` |
   | `schema/caop-v0.1.2.schema.json` | `3a72213ecf506df646cfb8c455b564349e2eae819bf3b6b9686f6868cfdbf000` |
   | `openapi/caop-v0.2.openapi.yaml` | `aaf1ae25400fd3db9483c737b787e36a31976415434d9bb615ca3481ec790e42` |
   | `openapi/caop-v0.2.openapi.json` | `699fc607a7b0473d8b2c08bac3d1f59b11687f2f6670cb391d86ec4b1aa7fcd6` |
   | `schema/caop-v0.2.schema.json` | `7a4e7ce9fdd5328d10a93595fe0269e63ba9a8fb9bce21b300dd6c7020a45f75` |

2. **CAOP stays published.** `SPEC.md` remains the CAOP v0.2 text; the only change is a short status banner pointing to MAOP. `examples/*.json` and `examples/README.md` are unchanged. The published CAOP pages and contract URLs stay online at their current addresses. MAOP files are added next to them (`docs/maop-v1*.md`, `schema/maop-v1.schema.json`, `openapi/maop-v1.openapi.{yaml,json}`, `examples/maop-v1/`) and replace nothing.
3. **MAOP is a superset at the wire level.**
   - All 17 CAOP v0.2 operations are kept with the same operationId, HTTP method, sub-path, request body, response codes and response bodies. Only the path prefix changes.
   - All 95 CAOP v0.2 definitions keep their names and their structure. When the parity file was generated, every one was structurally identical; six have reworded descriptions only.
   - Every CAOP v0.2 example (71 of 71) validates against the same-named MAOP definition.
4. **Wire tokens are not renamed in v1.** The error codes keep their CAOP names: `CAOP_409_UNSETTLED_EXECUTION_LEASE`, `CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE`, `CAOP_422_PRECOMMIT_*` and `CAOP_422_VERIFY_ARTIFACT_MISMATCH`. So do the enum values, including `AuthCustodian.CREASURA_VAULT`, and the compact tool names `caop_pulse`, `caop_stage_work`, `caop_dispatch_work` and `caop_settle_receipt`. A client that matches on these strings needs no change. Neutral aliases are an open question (§7).
5. **Change rule within MAOP v1.** A kept definition can be refined only additively: a new optional property, a new enum value, or a reworded description. A required property is never added, a constraint is never tightened, and a value is never removed. A change of any other kind needs a new major version.

## 2. Client migration

### 2.1 Minimum change: the path prefix

Replace the `/v1` prefix with `/maop/v1`. Nothing else changes for the 17 kept operations.

| operationId | CAOP v0.2 | MAOP v1 |
|---|---|---|
| `observations.ingest` | `POST /v1/observations` | `POST /maop/v1/observations` |
| `context.resolve` | `POST /v1/context/resolve` | `POST /maop/v1/context/resolve` |
| `commitments.create` | `POST /v1/commitments` | `POST /maop/v1/commitments` |
| `commitments.list` | `GET /v1/commitments` | `GET /maop/v1/commitments` |
| `plans.create` | `POST /v1/plans` | `POST /maop/v1/plans` |
| `executions.start` | `POST /v1/executions` | `POST /maop/v1/executions` |
| `executions.get` | `GET /v1/executions/{execution_id}` | `GET /maop/v1/executions/{execution_id}` |
| `executions.submit_result` | `POST /v1/executions/{execution_id}/results` | `POST /maop/v1/executions/{execution_id}/results` |
| `executions.transition` | `POST /v1/executions/{execution_id}/transitions` | `POST /maop/v1/executions/{execution_id}/transitions` |
| `verifications.evaluate` | `POST /v1/verifications` | `POST /maop/v1/verifications` |
| `records.commit` | `POST /v1/records/commit` | `POST /maop/v1/records/commit` |
| `reviews.evaluate` | `POST /v1/reviews` | `POST /maop/v1/reviews` |
| `approvals.decide` | `POST /v1/approvals/{approval_request_id}/decision` | `POST /maop/v1/approvals/{approval_request_id}/decision` |
| `compact.pulse` | `POST /v1/compact/pulse` | `POST /maop/v1/compact/pulse` |
| `compact.stage_work` | `POST /v1/compact/stage-work` | `POST /maop/v1/compact/stage-work` |
| `compact.dispatch_work` | `POST /v1/compact/dispatch-work` | `POST /maop/v1/compact/dispatch-work` |
| `compact.settle_receipt` | `POST /v1/compact/settle-receipt` | `POST /maop/v1/compact/settle-receipt` |

Generated clients that key on operationId need only a new base path. Hosts that use the compact tool binding keep the same four tools and arguments.

### 2.2 Bodies and new optional fields

- Request and response bodies of the 17 operations are unchanged, so existing payloads, fixtures and the 71 CAOP examples stay valid.
- MAOP adds no field to any kept definition. All new fields belong to the 15 new definitions, which only the new operations use. These definitions are `AgentIdentity`, `AgentRole`, `AgentRegistration`, `Delegation`, `DelegationCreate`, `AuthorityGrant`, `Lease`, `LeaseRenewal`, `Receipt`, `SupervisionStage`, `ChildLifecycleState`, `Guard`, `SupervisionEvaluation`, `TransitionDecision` and `CausalEvidence`.
- Later 1.x drafts may add optional properties to kept definitions under the rule in §1.5. Clients SHOULD ignore response properties they do not recognise. A client that validates responses strictly against the CAOP v0.2 schema should validate against `schema/maop-v1.schema.json` instead.

### 2.3 Adopting the new operations incrementally

Each step is optional and independent of the later ones. A client can stop at any step.

| Step | Adopt | What the client gains | Prerequisite |
|---|---|---|---|
| 0 | Prefix change only (§2.1) | MAOP endpoint, identical behaviour | none |
| 1 | `receipts.get` | Read a receipt back after a crash or timeout, including `outcome_unknown`, instead of guessing | none (read-only) |
| 2 | `agents.register` | Declare agent identity, roles and capability stubs, which enables separation-of-duties guards | none |
| 3 | `leases.renew` | Keep long work alive with a fenced lease. Present the latest `fencing_token`; a stale token is rejected | step 2 recommended (lease holder = registered agent) |
| 4 | `delegations.create`, `delegations.get` | Hand child work to another agent with an isolation policy, a budget and an authority subset, and track its child lifecycle state | step 2 |
| 5 | `supervision.evaluate` | Event-driven re-evaluation of durable guards. Call it when a fact is superseded, a lease expires, a receipt settles or a child changes state, and follow the returned `TransitionDecision`, which can be a back-edge such as Act→Decide or Act→Coordinate | steps 2–4 for full value |

A client that never adopts steps 1–5 still gets everything CAOP v0.2 provided.

## 3. Server migration

1. **Serve both prefixes from the same handlers.** Mount the existing handlers under `/maop/v1` as well as `/v1`. The bodies are identical, so no translation layer is needed. Keep `/v1` running for the deprecation window (§5).
2. **Keep the error envelope and codes as they are.** Return the same `Error` envelope with the same codes from both prefixes.
3. **Implement the new operations behind the conformance level you claim (§4).**
   - Leases: issue a monotonic `fencing_token`, check it on every settle and renewal, and keep `CAOP_409_UNSETTLED_EXECUTION_LEASE` for the one-open-lease rule.
   - Receipts: persist a receipt for every settled action, keyed by `idempotency_key`, before replying.
   - Guards: store each guard as a durable record and re-evaluate it on events, not only at commit.
4. **Make authority narrow only.** A delegation's `AuthorityGrant` and a steering delta may narrow the parent's authority but must never widen it.
5. **Run the conformance checks.** `python tests/validate.py` checks the MAOP contracts and examples, the parity file and the frozen CAOP hashes. Run it in CI on every change to the contracts.
6. **Keep CAOP runtime profiles meaningful.** The CAOP-STAGE-1/2/3 profiles (loop driver, credential custody, execution locus, maximum attestation) still describe how a runtime is deployed. The MAOP conformance levels below describe which MAOP surface it serves, so a runtime states both.

## 4. Conformance levels

The levels are cumulative. If [`docs/maop-v1.md`](maop-v1.md) names them differently, its names are normative and this table is the migration view.

| Level | Required operations | Required behaviour | Relation to CAOP |
|---|---|---|---|
| **MAOP-Core** | The 17 kept operations under `/maop/v1` | Every CAOP v0.2 guarantee (G-001–G-010 in the parity file); all CAOP v0.2 examples accepted | Equivalent to a CAOP v0.2 runtime at any CAOP-STAGE profile |
| **MAOP-Coordinated** | Core + `agents.register`, `delegations.create`, `delegations.get`, `receipts.get` | Agent identity and roles; delegation with isolation policy, budget and narrow-only authority; durable receipts including `outcome_unknown` | Extends v0.2 sub-agent isolation (`parent_work_id`, `isolation_policy`) |
| **MAOP-Supervised** | Coordinated + `leases.renew`, `supervision.evaluate` | Fenced leases; durable guards re-evaluated on events; the outer supervision lifecycle with its back-edges (Act→Decide, Act→Coordinate, Verify→Act, any→Recover, Recover→Decide) | Corresponds to CAOP L3 (event-driven, supervised) |

A runtime claims one level and passes the checks for that level. A server that serves only `/v1` stays a CAOP v0.2 runtime, and it is not MAOP-conformant until it serves `/maop/v1`.

## 5. Deprecation timeline (proposal for founder decision)

> **Proposal, not adopted.** Every date and step below needs a founder decision before it applies. Until then, CAOP v0.2 remains a supported, current protocol alongside the MAOP draft.

| Phase | Trigger (proposed) | CAOP v0.2 `/v1` | MAOP `/maop/v1` |
|---|---|---|---|
| P0 Draft | This PR merged | Current, fully supported | `1.0.0-draft.N`, may change additively |
| P1 Release candidate | Founder accepts the draft, and one runtime passes MAOP-Core | Supported, documented as "superseded by MAOP v1" | `1.0.0-rc.N`, frozen except for fixes |
| P2 MAOP v1.0.0 | RC with no open blocking issues for an agreed period (proposed: 30 days) | Deprecated: still served, with a `Deprecation` response header and a link to this guide | Stable |
| P3 Sunset of `/v1` serving | Proposed: no earlier than 6 months after P2, and only after known clients have moved | Runtimes may stop serving `/v1`; the CAOP documents and contract files stay published, frozen | Stable |

At no phase are the CAOP v0.1, v0.1.2 or v0.2 files deleted or edited. Deprecation applies to serving the `/v1` prefix, not to the published specifications.

## 6. Checklist

**Client**
- [ ] Base path switched to `/maop/v1`. Calls still keyed on the same operationIds.
- [ ] Unknown response properties ignored, or responses validated against `schema/maop-v1.schema.json`.
- [ ] Error-code matching left as is (codes unchanged).
- [ ] New operations adopted in the order of §2.3, as needed.

**Server**
- [ ] `/maop/v1` served by the same handlers as `/v1`.
- [ ] Conformance level chosen and its operations implemented.
- [ ] `python tests/validate.py` passes in CI.
- [ ] `/v1` kept running until the decided sunset date.

## 7. Open questions

1. **Legacy wire tokens.** Should MAOP v1 add vendor-neutral aliases for the `CAOP_*` error codes, the `CREASURA_VAULT` enum value and the `caop_*` compact tool names? If it does, should it accept both forms during the deprecation window, or should renaming wait until MAOP v2? The current draft keeps them verbatim for compatibility.
2. **Deprecation dates.** Should the timeline in §5 be adopted, and with which dates and windows? The proposed values are 30 days in RC and at least 6 months before `/v1` sunset.
3. **Canonical URLs.** Where will MAOP be published? The schema uses a relative `$id` (`maop-v1.schema.json`) and the OpenAPI uses the placeholder server `https://maop.example.com`. Choosing the published URLs is a follow-up for MAOP-W1.
4. **Generator integration.** The MAOP files are written by hand in this repository for now. When and how should the site's spec generator produce them, as it already does for CAOP?
5. **Conformance level names.** Should the three levels in §4 be adopted as written, renamed, or merged with the CAOP L1–L3 levels and the CAOP-STAGE-1/2/3 profiles?
6. **Host prompt obligation (G-008).** CAOP's normative host prompt is tied to two named hosts. Is MAOP's generalisation to any conversational host acceptable, or should the host prompt become informative?
7. **Dual-prefix period.** Must a MAOP-Core runtime keep serving `/v1` during P0–P2, or is serving it optional?
8. **Lease migration.** Do `OpenLease` records that already exist get a `fencing_token` when a runtime upgrades, or does fencing apply only to leases issued after the upgrade?
