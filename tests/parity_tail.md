## Improvements over CAOP v0.2

Each improvement is additive: a CAOP v0.2 client that ignores it still gets the v0.2 behaviour.

1. **Vendor-neutral protocol.** MAOP names no vendor and no product in its title, ids, paths or schema `$id`, and does not position itself as an operating system. CAOP text that named a vendor kernel or specific hosts (G-002, G-008, S-006, S-015) is reworded so the obligation falls on "the runtime" or "the host"; the obligation itself is unchanged. Wire tokens are kept exactly as they are so that existing clients keep working: the error codes (`CAOP_409_UNSETTLED_EXECUTION_LEASE`, `CAOP_422_PRECOMMIT_*` and the others), the `AuthCustodian` enum value `CREASURA_VAULT`, and the compact tool names (`caop_pulse`, `caop_stage_work`, `caop_dispatch_work`, `caop_settle_receipt`, carried in `x-maop-mcp-tool`). Renaming these is listed as an open question in the migration guide.
2. **A normative outer lifecycle.** CAOP defines eight lifecycle stages and an execution state machine but no supervisor loop around them. MAOP adds `SupervisionStage` (observe, decide, plan, coordinate, act, verify, review, approve, record, recover, closed) with explicit back-edges: Act→Decide (a guard fails or new evidence invalidates the plan), Act→Coordinate (a child needs re-delegation), Verify→Act (a phase-2 deferred check fails), any→Recover (lease lost or outcome unknown) and Recover→Decide.
3. **An explicit inner (child) lifecycle.** `ChildLifecycleState` (proposed, delegated, leased, executing, submitted, verifying, accepted, rejected, cancelled, expired) maps delegated work onto the CAOP execution states instead of leaving it implicit in `parent_work_id`.
4. **Durable guards and event-driven re-evaluation.** CAOP checks pre-commit hooks at COMMIT and re-evaluates on pulse. MAOP makes each guard (authority, policy, evidence, freshness, lease, separation_of_duties, budget) a durable record that `supervision.evaluate` re-checks whenever an event arrives, such as a superseded fact, an expired lease or a returned receipt. The result is a `TransitionDecision` that lists the guards that passed and failed and the next action.
5. **Fenced leases.** CAOP v0.2 allows one open lease per thread, but a lease has no renewal and no fencing. `Lease.fencing_token` is monotonic and `leases.renew` extends a lease. A holder with a stale token cannot settle, which closes the split-brain case in which an expired worker reports after a new one has taken over.
6. **Receipts that support recovery.** `Receipt` adds `outcome_unknown` alongside succeeded and failed, plus an `idempotency_key` and `causal_parents`, and `receipts.get` reads a receipt back after a crash. Recovery becomes a lifecycle stage instead of a manual procedure.
7. **Agent identity and separation of duties.** `agents.register` with `AgentIdentity` and `AgentRole` lets the runtime enforce rules such as "implementer ≠ reviewer ≠ approver". CAOP had principals but could not check this.
8. **Authority as data.** `AuthorityGrant` makes authority explicit, scoped and expiring, with a trust level (`T0_relayed` or `T1_attested`). A delegation or a steering delta can only narrow a grant, which states CAOP's "a delta can only narrow authority" rule (G-009) in general form.
9. **First-class delegation.** `delegations.create` and `delegations.get` carry the isolation policy, the budget and the authority subset. The v0.2 sub-agent isolation and provenance-pointer rule (G-010) is preserved and extended.
10. **Causal evidence.** `CausalEvidence` (with digest, `derived_from` and bitemporal times) links receipts, facts and guards, so an invalidation (G-002) can be traced to the guards and transitions it affects.

All five v0.2 mechanisms are preserved unchanged: two-phase verification (`TwoPhaseVerification`, `Phase2DeferredCheck`, `VerifySubState`, `OutcomeVerification`), approval steering (`SteeringDelta`, G-009), sub-agent isolation (`IsolationPolicy`, `ChildWork`, `DistilledReturnPayload`, G-010), compaction (`CompactionMode`) and lazy discovery (`CapabilityStub`, `HydratedCapability`).

## Acceptance criteria checklist

"Owner" names the workstream that writes each file. Rows that depend on another workstream's file need checking against that file before the PR is opened.

| # | Criterion | Satisfied by | State |
|---|---|---|---|
| 1 | Pin the CAOP v0.2 baseline and map all 17 operations, 95 schema definitions, 71 examples and normative guarantees to MAOP or justify improvements. | `tests/parity.json` and `tests/parity_gen.py` (counts asserted at generation: 17 / 95 / 71, 16 guarantees; reproducibility checked by `tests/validate.py` check 10); this file (baseline pin, full tables, Additions, Improvements) | Done (parity) |
| 2 | Historical CAOP contracts unchanged; document migration and compatibility. | The baseline pin table above (sha256 of the 9 frozen files, checked against the working tree); [`docs/maop-v1-migration.md`](maop-v1-migration.md); `tests/validate.py` (conformance) | Done for documentation; hash check in CI depends on `tests/validate.py` |
| 3 | Vendor-neutral MAOP, with no Creasura protocol branding or operating system positioning. | `docs/maop-v1.md` (spec); `schema/maop-v1.schema.json` (relative `$id`); `openapi/maop-v1.openapi.yaml`/`.json` (placeholder server); Improvement 1 above | Depends on spec and contract workstreams |
| 4 | A normative outer and inner lifecycle, including Act→Decide and Act→Coordinate, durable guards and event-driven re-evaluation. | `docs/maop-v1.md` (lifecycle sections); `SupervisionStage`, `ChildLifecycleState`, `Guard`, `TransitionDecision` in `schema/maop-v1.schema.json`; `supervision.evaluate` in the OpenAPI; Improvements 2–4 | Depends on spec and contract workstreams |
| 5 | Preserve two-phase verification, approval steering, sub-agent isolation, compaction, lazy discovery, receipts, authority and recovery. | `tests/parity.json`: guarantees G-006–G-010 and the definitions listed in the paragraph above, all kept; additions `Receipt`, `AuthorityGrant`, `Lease`, the recover stage | Done (parity); the semantics are stated in `docs/maop-v1.md` |
| 6 | Versioned MAOP OpenAPI, JSON Schema, examples and automated conformance checks. | `openapi/maop-v1.openapi.yaml`, `openapi/maop-v1.openapi.json`, `schema/maop-v1.schema.json`, `examples/maop-v1/*.json`, `tests/validate.py`, `tests/README.md` | Depends on contract and conformance workstreams |
| 7 | A Northstar A–K trace with the outer stage, child lifecycle, trigger, guard, authority, evidence and transition. | `docs/maop-v1.md` (Northstar A–K section: one end-to-end scenario, one row per step) | Depends on spec workstream |
| 8 | Submit a reviewable PR; do not merge or deploy. | A pull request from `design/maop-v1` into `main` (not a file) | Open at integration; not merged or deployed |

## Regenerating

`tests/parity.json` and the tables in this file are generated by [`tests/parity_gen.py`](../tests/parity_gen.py), which is committed with them. From a clone whose history contains the baseline commit, run:

```sh
pip install jsonschema pyyaml          # jsonschema >= 4.18
python tests/parity_gen.py all         # rewrites tests/parity.json and docs/maop-v1-parity.md
python tests/parity_gen.py json        # only tests/parity.json
python tests/parity_gen.py md          # only this file, rendered from tests/parity.json
python tests/parity_gen.py all --out /tmp/parity   # write to another directory instead
```

The generator:

1. reads the baseline files from git at the pinned commit (`git show 8c7bd07939171efc2d39079bd018904175ea8db2:<path>`), never from the working tree;
2. asserts the nine sha256 values and the 17/95/71 counts;
3. validates every example;
4. extracts the guarantee lines; and
5. compares the MAOP contracts in the working tree with the baseline, ignoring descriptions: an identical structure is `kept`; new optional properties, new enum values, new `oneOf`/`anyOf` branches, new response codes, new optional parameters and annotation-only keywords are `refined`; anything else (a removed property or enum value, a newly required property, a new constraint keyword, a changed value) is `CHECK`.

The output is deterministic: it has no timestamps, and sets are sorted. `tests/validate.py` check 10 (`parity-reproducible`) runs the generator into a temporary directory and fails unless both files are byte-identical to the committed ones, so any change to the MAOP schema or OpenAPI must be followed by a regeneration.

Hand-written content lives in `tests/parity_gen.py` and this template (`tests/parity_tail.md`): the status judgements for the 10 normative guarantees, the section-to-topic map, the justifications for the additions, and the prose sections of this file. A reviewer can recompute the counts independently with:

```sh
git show 8c7bd07939171efc2d39079bd018904175ea8db2:SPEC.md | grep -cE '\b(MUST|SHALL|SHOULD|REQUIRED)\b'   # 16
ls examples/*.json | wc -l                                                                                 # 71
python -c "import json;print(len(json.load(open('schema/caop-v0.2.schema.json'))['\$defs']))"            # 95
```
