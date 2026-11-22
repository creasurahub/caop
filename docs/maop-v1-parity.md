# MAOP v1 parity with CAOP v0.2

**Status:** DRAFT · **MAOP version:** 1.0.0-draft.1 · **Baseline:** CAOP v0.2 at commit `8c7bd07939171efc2d39079bd018904175ea8db2`

This document shows that MAOP v1 (Multi-Agent Orchestration Protocol) covers every operation, schema definition, example and normative guarantee of CAOP v0.2, and lists what MAOP adds. The machine-readable version is [`tests/parity.json`](../tests/parity.json). Both are generated from the files at the pinned baseline commit, not typed by hand: the generator, [`tests/parity_gen.py`](../tests/parity_gen.py), reads `SPEC.md`, `schema/caop-v0.2.schema.json`, `openapi/caop-v0.2.openapi.yaml` and `examples/*.json` from git at that commit, validates every example, and extracts every line of `SPEC.md` that contains MUST, MUST NOT, SHALL, SHOULD or REQUIRED. Line numbers refer to `SPEC.md` at the baseline commit. Regenerate both files with `python tests/parity_gen.py all`; see [Regenerating](#regenerating).

The specification itself is [`docs/maop-v1.md`](maop-v1.md); migration and compatibility are in [`docs/maop-v1-migration.md`](maop-v1-migration.md).

## Parity rule

MAOP v1 keeps all 17 CAOP v0.2 operations with the same operationIds, methods, sub-paths, request and response bodies and semantics, under the path prefix `/maop/v1` instead of `/v1`. It keeps all 95 CAOP v0.2 definitions under the same names; a definition may only be refined additively (new optional properties, new enum values, vendor-neutral descriptions), never weakened. Every CAOP v0.2 example is therefore a valid instance of the same-named MAOP definition. Parity holds by construction; the improvements are additive.

## Baseline pin

Commit: `8c7bd07939171efc2d39079bd018904175ea8db2` (branch `main` when MAOP work started).

These nine historical contract files are frozen. The sha256 values were computed from the files at the baseline commit, and the working tree was checked against them when this file was generated.

| File | sha256 | Unchanged in working tree |
|---|---|---|
| `openapi/caop-v0.1.2.openapi.json` | `6b727a0fa60efc1f487fe154d3eb3fe63c3f1e7121a89962a553116b04b005a8` | yes |
| `openapi/caop-v0.1.2.openapi.yaml` | `05dd1dfbe6449cc5447420023f336aa48c7221d229219cbd17396da4bf9be8b4` | yes |
| `openapi/caop-v0.1.openapi.json` | `076a128385a1bc7d4841d1447cf3b2a4eedfc612ad393c3b14d0714f9857a4eb` | yes |
| `openapi/caop-v0.1.openapi.yaml` | `272fd7face00997359c9d185851995d9397281846ce6166d25a32e98f16a622f` | yes |
| `openapi/caop-v0.2.openapi.json` | `699fc607a7b0473d8b2c08bac3d1f59b11687f2f6670cb391d86ec4b1aa7fcd6` | yes |
| `openapi/caop-v0.2.openapi.yaml` | `aaf1ae25400fd3db9483c737b787e36a31976415434d9bb615ca3481ec790e42` | yes |
| `schema/caop-v0.1.2.schema.json` | `3a72213ecf506df646cfb8c455b564349e2eae819bf3b6b9686f6868cfdbf000` | yes |
| `schema/caop-v0.1.schema.json` | `4cc2cda6f49926efa8521aa5dabd66803b23691ce8a7488c51f0477798005ded` | yes |
| `schema/caop-v0.2.schema.json` | `7a4e7ce9fdd5328d10a93595fe0269e63ba9a8fb9bce21b300dd6c7020a45f75` | yes |

## Summary

| Category | CAOP v0.2 count | Kept | Refined | Replaced | Removed |
|---|---|---|---|---|---|
| Operations | 17 | 17 | 0 | 0 | 0 |
| Schema definitions | 95 | 94 | 1 | 0 | 0 |
| Examples | 71 | 71 | 0 | 0 | 0 |
| Normative guarantees (MUST/SHALL/SHOULD/REQUIRED lines) | 16 | 12 | 4 | 0 | 0 |
| Supplementary lower-case requirements (informative check) | 17 | 15 | 2 | 0 | 0 |

Nothing is removed or replaced, so no removal needs a justification. Of the 16 guarantee lines, 10 are normative statements and 6 are entries in SPEC.md's editorial history that quote those statements; the history entries are tracked so the count matches a plain keyword search, and each points at the guarantee it records.

MAOP v1 adds 6 operations and 15 definitions, for 23 operations and 110 definitions in total.

> **Generation note.** Statuses were derived by structurally comparing `schema/maop-v1.schema.json` and `openapi/maop-v1.openapi.yaml` with CAOP v0.2, ignoring descriptions. All 17 operations have the same method, sub-path, request body and response codes and bodies. 94 of 95 definitions are structurally identical. 1 are refined additively (new optional properties or enum values only; see the Note column): `Error`. 6 kept definitions have reworded, vendor-neutral descriptions only (`EntityRef`, `Fact`, `Capability`, `ObservationCreate`, `LoopDriver`, `AuthCustodian`), and their status stays `kept`. Re-run `python tests/parity_gen.py all` after any contract change; an additive change shows as `refined`, and any other change is flagged `CHECK`.

## Operations

| # | operationId | CAOP v0.2 | MAOP v1 | Request | Success response | Status |
|---|---|---|---|---|---|---|
| 1 | `observations.ingest` | `POST /v1/observations` | `POST /maop/v1/observations` | ObservationCreate | 202: ObservationAccepted | kept |
| 2 | `context.resolve` | `POST /v1/context/resolve` | `POST /maop/v1/context/resolve` | ContextResolveRequest | 200: ContextBundle | kept |
| 3 | `commitments.create` | `POST /v1/commitments` | `POST /maop/v1/commitments` | CommitmentCreate | 201: Commitment | kept |
| 4 | `commitments.list` | `GET /v1/commitments` | `GET /maop/v1/commitments` | none | 200: CommitmentList | kept |
| 5 | `plans.create` | `POST /v1/plans` | `POST /maop/v1/plans` | PlanCreate | 201: Plan | kept |
| 6 | `executions.start` | `POST /v1/executions` | `POST /maop/v1/executions` | ExecutionCreate | 202: ExecutionAccepted | kept |
| 7 | `executions.get` | `GET /v1/executions/{execution_id}` | `GET /maop/v1/executions/{execution_id}` | none | 200: Execution | kept |
| 8 | `executions.submit_result` | `POST /v1/executions/{execution_id}/results` | `POST /maop/v1/executions/{execution_id}/results` | ResultSubmission | 202: Execution | kept |
| 9 | `executions.transition` | `POST /v1/executions/{execution_id}/transitions` | `POST /maop/v1/executions/{execution_id}/transitions` | TransitionRequest | 200: Transition | kept |
| 10 | `verifications.evaluate` | `POST /v1/verifications` | `POST /maop/v1/verifications` | VerificationRequest | 200: Verification | kept |
| 11 | `records.commit` | `POST /v1/records/commit` | `POST /maop/v1/records/commit` | RecordCommit | 200: RecordCommitted | kept |
| 12 | `reviews.evaluate` | `POST /v1/reviews` | `POST /maop/v1/reviews` | ReviewRequest | 200: Review | kept |
| 13 | `approvals.decide` | `POST /v1/approvals/{approval_request_id}/decision` | `POST /maop/v1/approvals/{approval_request_id}/decision` | ApprovalDecision | 200: Approval | kept |
| 14 | `compact.pulse` | `POST /v1/compact/pulse` | `POST /maop/v1/compact/pulse` | PulseInput | 200: PulseResponse | kept |
| 15 | `compact.stage_work` | `POST /v1/compact/stage-work` | `POST /maop/v1/compact/stage-work` | StageWorkInput | 200: StageWorkResult | kept |
| 16 | `compact.dispatch_work` | `POST /v1/compact/dispatch-work` | `POST /maop/v1/compact/dispatch-work` | DispatchWorkInput | 200: DispatchWorkResult | kept |
| 17 | `compact.settle_receipt` | `POST /v1/compact/settle-receipt` | `POST /maop/v1/compact/settle-receipt` | SettleReceiptInput | 200: SettlementResult | kept |

Every operation keeps its error responses (Error envelope, same codes). Note for all rows: Same operationId, method, sub-path, request and response definitions and semantics under the /maop/v1 prefix.

## Schema definitions

| # | Definition | MAOP name | Introduced | Status | Note |
|---|---|---|---|---|---|
| 1 | `PrincipalRef` | `PrincipalRef` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 2 | `EntityRef` | `EntityRef` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 3 | `EvidenceRef` | `EvidenceRef` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 4 | `ArtifactRef` | `ArtifactRef` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 5 | `Expression` | `Expression` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 6 | `Criterion` | `Criterion` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 7 | `Constraint` | `Constraint` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 8 | `AuthorizationPolicy` | `AuthorizationPolicy` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 9 | `Goal` | `Goal` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 10 | `WorkItem` | `WorkItem` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 11 | `Fact` | `Fact` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/Fact.json. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 12 | `Capability` | `Capability` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 13 | `Policy` | `Policy` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/Policy.json. Structure identical in schema/maop-v1.schema.json. |
| 14 | `CapabilityDescriptor` | `CapabilityDescriptor` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/CapabilityDescriptor.json. Structure identical in schema/maop-v1.schema.json. |
| 15 | `CapabilityInvocation` | `CapabilityInvocation` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 16 | `CapabilityResult` | `CapabilityResult` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 17 | `ExecutionState` | `ExecutionState` | v0.1 | kept | Introduced in CAOP v0.1. Structure identical in schema/maop-v1.schema.json. |
| 18 | `ObservationCreate` | `ObservationCreate` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by observations.ingest. Example: examples/ObservationCreate.json. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 19 | `ObservationAccepted` | `ObservationAccepted` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by observations.ingest. Example: examples/ObservationAccepted.json. Structure identical in schema/maop-v1.schema.json. |
| 20 | `ContextResolveRequest` | `ContextResolveRequest` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by context.resolve. Example: examples/ContextResolveRequest.json. Structure identical in schema/maop-v1.schema.json. |
| 21 | `ContextBundle` | `ContextBundle` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by context.resolve. Example: examples/ContextBundle.json. Structure identical in schema/maop-v1.schema.json. |
| 22 | `CommitmentCreate` | `CommitmentCreate` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by commitments.create. Example: examples/CommitmentCreate.json. Structure identical in schema/maop-v1.schema.json. |
| 23 | `Commitment` | `Commitment` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by commitments.create. Example: examples/Commitment.json. Structure identical in schema/maop-v1.schema.json. |
| 24 | `CommitmentList` | `CommitmentList` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by commitments.list. Structure identical in schema/maop-v1.schema.json. |
| 25 | `PlanCreate` | `PlanCreate` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by plans.create. Example: examples/PlanCreate.json. Structure identical in schema/maop-v1.schema.json. |
| 26 | `Plan` | `Plan` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by plans.create. Example: examples/Plan.json. Structure identical in schema/maop-v1.schema.json. |
| 27 | `ExecutionCreate` | `ExecutionCreate` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.start. Example: examples/ExecutionCreate.json. Structure identical in schema/maop-v1.schema.json. |
| 28 | `ExecutionAccepted` | `ExecutionAccepted` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.start. Example: examples/ExecutionAccepted.json. Structure identical in schema/maop-v1.schema.json. |
| 29 | `Execution` | `Execution` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.get, executions.submit_result. Example: examples/Execution.json. Structure identical in schema/maop-v1.schema.json. |
| 30 | `TransitionRequest` | `TransitionRequest` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.transition. Example: examples/TransitionRequest.json. Structure identical in schema/maop-v1.schema.json. |
| 31 | `Transition` | `Transition` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.transition. Example: examples/Transition.json. Structure identical in schema/maop-v1.schema.json. |
| 32 | `ResultSubmission` | `ResultSubmission` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by executions.submit_result. Example: examples/ResultSubmission.json. Structure identical in schema/maop-v1.schema.json. |
| 33 | `VerificationRequest` | `VerificationRequest` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by verifications.evaluate. Example: examples/VerificationRequest.json. Structure identical in schema/maop-v1.schema.json. |
| 34 | `Verification` | `Verification` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by verifications.evaluate. Example: examples/Verification.json. Structure identical in schema/maop-v1.schema.json. |
| 35 | `RecordCommit` | `RecordCommit` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by records.commit. Example: examples/RecordCommit.json. Structure identical in schema/maop-v1.schema.json. |
| 36 | `RecordCommitted` | `RecordCommitted` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by records.commit. Example: examples/RecordCommitted.json. Structure identical in schema/maop-v1.schema.json. |
| 37 | `ReviewRequest` | `ReviewRequest` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by reviews.evaluate. Example: examples/ReviewRequest.json. Structure identical in schema/maop-v1.schema.json. |
| 38 | `Review` | `Review` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by reviews.evaluate. Example: examples/Review.json. Structure identical in schema/maop-v1.schema.json. |
| 39 | `ApprovalDecision` | `ApprovalDecision` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by approvals.decide. Example: examples/ApprovalDecision.json. Structure identical in schema/maop-v1.schema.json. |
| 40 | `Approval` | `Approval` | v0.1 | kept | Introduced in CAOP v0.1. Used directly by approvals.decide. Example: examples/Approval.json. Structure identical in schema/maop-v1.schema.json. |
| 41 | `EventEnvelope` | `EventEnvelope` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/EventEnvelope.json. Structure identical in schema/maop-v1.schema.json. |
| 42 | `Error` | `Error` | v0.1 | refined | Introduced in CAOP v0.1. Used directly by approvals.decide, commitments.create, commitments.list, compact.dispatch_work, compact.pulse, compact.settle_receipt, compact.stage_work, context.resolve, executions.get, executions.start, executions.submit_result, executions.transition, observations.ingest, plans.create, records.commit, reviews.evaluate, verifications.evaluate. Example: examples/Error.json. Additive refinement: /properties/error/properties/code/enum +['MAOP_403_AUTHORITY_INVALID', 'MAOP_403_AUTHORITY_WIDENING', 'MAOP_403_SEPARATION_OF_DUTIES', 'MAOP_403_TRUST_FLOOR', 'MAOP_409_IDEMPOTENCY_KEY_REUSED', 'MAOP_409_LEASE_CONFLICT', 'MAOP_409_LEASE_FENCED', 'MAOP_409_OUTCOME_UNRECONCILED', 'MAOP_410_LEASE_EXPIRED', 'MAOP_422_BUDGET_EXCEEDED', 'MAOP_422_EVIDENCE_MISMATCH', 'MAOP_422_GUARD_FAILED']. Description reworded (vendor-neutral). |
| 43 | `MetricNode` | `MetricNode` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/MetricNode.json. Structure identical in schema/maop-v1.schema.json. |
| 44 | `ApprovalRoutingRule` | `ApprovalRoutingRule` | v0.1 | kept | Introduced in CAOP v0.1. Example: examples/ApprovalRoutingRule.json. Structure identical in schema/maop-v1.schema.json. |
| 45 | `LoopDriver` | `LoopDriver` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 46 | `ExecutionLocus` | `ExecutionLocus` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 47 | `AuthCustodian` | `AuthCustodian` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. Description reworded (vendor-neutral), no structural change. |
| 48 | `AttestationTier` | `AttestationTier` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 49 | `ConformanceProfileId` | `ConformanceProfileId` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 50 | `ConformanceProfile` | `ConformanceProfile` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/ConformanceProfile.json. Structure identical in schema/maop-v1.schema.json. |
| 51 | `PromotionPolicy` | `PromotionPolicy` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/PromotionPolicy.json. Structure identical in schema/maop-v1.schema.json. |
| 52 | `CapabilityRegistration` | `CapabilityRegistration` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/CapabilityRegistration.json. Structure identical in schema/maop-v1.schema.json. |
| 53 | `EpistemicStatus` | `EpistemicStatus` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 54 | `Freshness` | `Freshness` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 55 | `DependsOnAlternatives` | `DependsOnAlternatives` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/DependsOnAlternatives.json. Structure identical in schema/maop-v1.schema.json. |
| 56 | `InvalidationContext` | `InvalidationContext` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/InvalidationContext.json. Structure identical in schema/maop-v1.schema.json. |
| 57 | `FactProvenance` | `FactProvenance` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/FactProvenance.json. Structure identical in schema/maop-v1.schema.json. |
| 58 | `BitemporalFact` | `BitemporalFact` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/BitemporalFact.json. Structure identical in schema/maop-v1.schema.json. |
| 59 | `StateConfig` | `StateConfig` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/StateConfig.json. Structure identical in schema/maop-v1.schema.json. |
| 60 | `PreCommitHook` | `PreCommitHook` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/PreCommitHook.json. Structure identical in schema/maop-v1.schema.json. |
| 61 | `PolicyRegistration` | `PolicyRegistration` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/PolicyRegistration.json. Structure identical in schema/maop-v1.schema.json. |
| 62 | `FailedHook` | `FailedHook` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/FailedHook.json. Structure identical in schema/maop-v1.schema.json. |
| 63 | `ExecuteSubState` | `ExecuteSubState` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 64 | `CommitSubState` | `CommitSubState` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Structure identical in schema/maop-v1.schema.json. |
| 65 | `DispatchStep` | `DispatchStep` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/DispatchStep.json. Structure identical in schema/maop-v1.schema.json. |
| 66 | `DispatchDirective` | `DispatchDirective` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/DispatchDirective.json. Structure identical in schema/maop-v1.schema.json. |
| 67 | `GoalPulseSLA` | `GoalPulseSLA` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/GoalPulseSLA.json. Structure identical in schema/maop-v1.schema.json. |
| 68 | `PulseInput` | `PulseInput` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.pulse. Example: examples/PulseInput.json. Structure identical in schema/maop-v1.schema.json. |
| 69 | `StageWorkInput` | `StageWorkInput` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.stage_work. Example: examples/StageWorkInput.json. Structure identical in schema/maop-v1.schema.json. |
| 70 | `DispatchWorkInput` | `DispatchWorkInput` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.dispatch_work. Example: examples/DispatchWorkInput.json. Structure identical in schema/maop-v1.schema.json. |
| 71 | `SettleReceiptInput` | `SettleReceiptInput` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.settle_receipt. Example: examples/SettleReceiptInput.json. Structure identical in schema/maop-v1.schema.json. |
| 72 | `OpenLease` | `OpenLease` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/OpenLease.json. Structure identical in schema/maop-v1.schema.json. |
| 73 | `StaleCommitment` | `StaleCommitment` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/StaleCommitment.json. Structure identical in schema/maop-v1.schema.json. |
| 74 | `UnassignedBlocker` | `UnassignedBlocker` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/UnassignedBlocker.json. Structure identical in schema/maop-v1.schema.json. |
| 75 | `RankedNextAction` | `RankedNextAction` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/RankedNextAction.json. Structure identical in schema/maop-v1.schema.json. |
| 76 | `SystemAdvisory` | `SystemAdvisory` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/SystemAdvisory.json. Structure identical in schema/maop-v1.schema.json. |
| 77 | `ResumeBrief` | `ResumeBrief` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Example: examples/ResumeBrief.json. Structure identical in schema/maop-v1.schema.json. |
| 78 | `PulseResponse` | `PulseResponse` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.pulse. Example: examples/PulseResponse.json. Structure identical in schema/maop-v1.schema.json. |
| 79 | `StageWorkResult` | `StageWorkResult` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.stage_work. Example: examples/StageWorkResult.json. Structure identical in schema/maop-v1.schema.json. |
| 80 | `SettlementResult` | `SettlementResult` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.settle_receipt. Example: examples/SettlementResult.json. Structure identical in schema/maop-v1.schema.json. |
| 81 | `DispatchWorkResult` | `DispatchWorkResult` | v0.1.2 | kept | Introduced in CAOP v0.1.2. Used directly by compact.dispatch_work. Example: examples/DispatchWorkResult.json. Structure identical in schema/maop-v1.schema.json. |
| 82 | `SteeringDelta` | `SteeringDelta` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/SteeringDelta.json. Structure identical in schema/maop-v1.schema.json. |
| 83 | `Phase2DeferredCheck` | `Phase2DeferredCheck` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/Phase2DeferredCheck.json. Structure identical in schema/maop-v1.schema.json. |
| 84 | `TwoPhaseVerification` | `TwoPhaseVerification` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/TwoPhaseVerification.json. Structure identical in schema/maop-v1.schema.json. |
| 85 | `VerifySubState` | `VerifySubState` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/VerifySubState.json. Structure identical in schema/maop-v1.schema.json. |
| 86 | `RecordSubState` | `RecordSubState` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/RecordSubState.json. Structure identical in schema/maop-v1.schema.json. |
| 87 | `OutcomeVerification` | `OutcomeVerification` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/OutcomeVerification.json. Structure identical in schema/maop-v1.schema.json. |
| 88 | `IsolationPolicy` | `IsolationPolicy` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/IsolationPolicy.json. Structure identical in schema/maop-v1.schema.json. |
| 89 | `DistilledReturnPayload` | `DistilledReturnPayload` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/DistilledReturnPayload.json. Structure identical in schema/maop-v1.schema.json. |
| 90 | `ChildWork` | `ChildWork` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/ChildWork.json. Structure identical in schema/maop-v1.schema.json. |
| 91 | `CompactionMode` | `CompactionMode` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/CompactionMode.json. Structure identical in schema/maop-v1.schema.json. |
| 92 | `CapabilityStub` | `CapabilityStub` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/CapabilityStub.json. Structure identical in schema/maop-v1.schema.json. |
| 93 | `HydratedCapability` | `HydratedCapability` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/HydratedCapability.json. Structure identical in schema/maop-v1.schema.json. |
| 94 | `DispatchWorkInputV02` | `DispatchWorkInputV02` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/DispatchWorkInputV02.json. Structure identical in schema/maop-v1.schema.json. |
| 95 | `PulseInputV02` | `PulseInputV02` | v0.2 | kept | Introduced in CAOP v0.2. Example: examples/PulseInputV02.json. Structure identical in schema/maop-v1.schema.json. |

## Examples

Each example file is matched by filename to the definition of the same name and validated against CAOP v0.2 (JSON Schema 2020-12) during generation. 71 of 71 validate.

| # | File | Definition | Valid (v0.2) | MAOP status |
|---|---|---|---|---|
| 1 | `examples/Approval.json` | `Approval` | yes | kept |
| 2 | `examples/ApprovalDecision.json` | `ApprovalDecision` | yes | kept |
| 3 | `examples/ApprovalRoutingRule.json` | `ApprovalRoutingRule` | yes | kept |
| 4 | `examples/BitemporalFact.json` | `BitemporalFact` | yes | kept |
| 5 | `examples/CapabilityDescriptor.json` | `CapabilityDescriptor` | yes | kept |
| 6 | `examples/CapabilityRegistration.json` | `CapabilityRegistration` | yes | kept |
| 7 | `examples/CapabilityStub.json` | `CapabilityStub` | yes | kept |
| 8 | `examples/ChildWork.json` | `ChildWork` | yes | kept |
| 9 | `examples/Commitment.json` | `Commitment` | yes | kept |
| 10 | `examples/CommitmentCreate.json` | `CommitmentCreate` | yes | kept |
| 11 | `examples/CompactionMode.json` | `CompactionMode` | yes | kept |
| 12 | `examples/ConformanceProfile.json` | `ConformanceProfile` | yes | kept |
| 13 | `examples/ContextBundle.json` | `ContextBundle` | yes | kept |
| 14 | `examples/ContextResolveRequest.json` | `ContextResolveRequest` | yes | kept |
| 15 | `examples/DependsOnAlternatives.json` | `DependsOnAlternatives` | yes | kept |
| 16 | `examples/DispatchDirective.json` | `DispatchDirective` | yes | kept |
| 17 | `examples/DispatchStep.json` | `DispatchStep` | yes | kept |
| 18 | `examples/DispatchWorkInput.json` | `DispatchWorkInput` | yes | kept |
| 19 | `examples/DispatchWorkInputV02.json` | `DispatchWorkInputV02` | yes | kept |
| 20 | `examples/DispatchWorkResult.json` | `DispatchWorkResult` | yes | kept |
| 21 | `examples/DistilledReturnPayload.json` | `DistilledReturnPayload` | yes | kept |
| 22 | `examples/Error.json` | `Error` | yes | kept |
| 23 | `examples/EventEnvelope.json` | `EventEnvelope` | yes | kept |
| 24 | `examples/Execution.json` | `Execution` | yes | kept |
| 25 | `examples/ExecutionAccepted.json` | `ExecutionAccepted` | yes | kept |
| 26 | `examples/ExecutionCreate.json` | `ExecutionCreate` | yes | kept |
| 27 | `examples/Fact.json` | `Fact` | yes | kept |
| 28 | `examples/FactProvenance.json` | `FactProvenance` | yes | kept |
| 29 | `examples/FailedHook.json` | `FailedHook` | yes | kept |
| 30 | `examples/GoalPulseSLA.json` | `GoalPulseSLA` | yes | kept |
| 31 | `examples/HydratedCapability.json` | `HydratedCapability` | yes | kept |
| 32 | `examples/InvalidationContext.json` | `InvalidationContext` | yes | kept |
| 33 | `examples/IsolationPolicy.json` | `IsolationPolicy` | yes | kept |
| 34 | `examples/MetricNode.json` | `MetricNode` | yes | kept |
| 35 | `examples/ObservationAccepted.json` | `ObservationAccepted` | yes | kept |
| 36 | `examples/ObservationCreate.json` | `ObservationCreate` | yes | kept |
| 37 | `examples/OpenLease.json` | `OpenLease` | yes | kept |
| 38 | `examples/OutcomeVerification.json` | `OutcomeVerification` | yes | kept |
| 39 | `examples/Phase2DeferredCheck.json` | `Phase2DeferredCheck` | yes | kept |
| 40 | `examples/Plan.json` | `Plan` | yes | kept |
| 41 | `examples/PlanCreate.json` | `PlanCreate` | yes | kept |
| 42 | `examples/Policy.json` | `Policy` | yes | kept |
| 43 | `examples/PolicyRegistration.json` | `PolicyRegistration` | yes | kept |
| 44 | `examples/PreCommitHook.json` | `PreCommitHook` | yes | kept |
| 45 | `examples/PromotionPolicy.json` | `PromotionPolicy` | yes | kept |
| 46 | `examples/PulseInput.json` | `PulseInput` | yes | kept |
| 47 | `examples/PulseInputV02.json` | `PulseInputV02` | yes | kept |
| 48 | `examples/PulseResponse.json` | `PulseResponse` | yes | kept |
| 49 | `examples/RankedNextAction.json` | `RankedNextAction` | yes | kept |
| 50 | `examples/RecordCommit.json` | `RecordCommit` | yes | kept |
| 51 | `examples/RecordCommitted.json` | `RecordCommitted` | yes | kept |
| 52 | `examples/RecordSubState.json` | `RecordSubState` | yes | kept |
| 53 | `examples/ResultSubmission.json` | `ResultSubmission` | yes | kept |
| 54 | `examples/ResumeBrief.json` | `ResumeBrief` | yes | kept |
| 55 | `examples/Review.json` | `Review` | yes | kept |
| 56 | `examples/ReviewRequest.json` | `ReviewRequest` | yes | kept |
| 57 | `examples/SettleReceiptInput.json` | `SettleReceiptInput` | yes | kept |
| 58 | `examples/SettlementResult.json` | `SettlementResult` | yes | kept |
| 59 | `examples/StageWorkInput.json` | `StageWorkInput` | yes | kept |
| 60 | `examples/StageWorkResult.json` | `StageWorkResult` | yes | kept |
| 61 | `examples/StaleCommitment.json` | `StaleCommitment` | yes | kept |
| 62 | `examples/StateConfig.json` | `StateConfig` | yes | kept |
| 63 | `examples/SteeringDelta.json` | `SteeringDelta` | yes | kept |
| 64 | `examples/SystemAdvisory.json` | `SystemAdvisory` | yes | kept |
| 65 | `examples/Transition.json` | `Transition` | yes | kept |
| 66 | `examples/TransitionRequest.json` | `TransitionRequest` | yes | kept |
| 67 | `examples/TwoPhaseVerification.json` | `TwoPhaseVerification` | yes | kept |
| 68 | `examples/UnassignedBlocker.json` | `UnassignedBlocker` | yes | kept |
| 69 | `examples/Verification.json` | `Verification` | yes | kept |
| 70 | `examples/VerificationRequest.json` | `VerificationRequest` | yes | kept |
| 71 | `examples/VerifySubState.json` | `VerifySubState` | yes | kept |

The files stay in `examples/` unchanged. New MAOP examples live in `examples/maop-v1/`.

## Normative guarantees

MAOP section names refer to topics in [`docs/maop-v1.md`](maop-v1.md).

### G-001 · SPEC.md line 789 · kept

- **CAOP section:** 14.2.1 Epistemic Status Enum (epistemic_status)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** State: epistemic status, freshness and causal invalidation
- **Note:** Same three adoption states and separate freshness value (EpistemicStatus, Freshness).

> Every fact and commitment in the State API MUST carry one of three epistemic states (adoption), and separately a freshness value: [Q1]

### G-002 · SPEC.md line 845 · refined

- **CAOP section:** 14.2.3 Synchronous Causal Invalidation Rule
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** State: epistemic status, freshness and causal invalidation
- **Note:** Obligation unchanged; subject reworded from 'the Creasura kernel' to 'the runtime' (vendor-neutral). MAOP also treats each invalidation as a trigger for supervision.evaluate (event-driven re-evaluation of durable guards).

> Whenever a new fact F_new supersedes an existing fact F_old (setting F_old.transaction_time.superseded_at), the Creasura kernel MUST, synchronously and within the same database transaction, re-evaluate every dependent commitment or fact reachable through reverse depends_on_fact_ids and depends_on_alternatives edges: [Q2]

### G-003 · SPEC.md line 850 · kept

- **CAOP section:** 14.2.3 Synchronous Causal Invalidation Rule
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** State: epistemic status, freshness and causal invalidation
- **Note:** Same max_invalidation_subgraph limit and CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE error code.

> - The kernel MUST enforce a declared max_invalidation_subgraph limit. An update whose affected subgraph exceeds it is rejected before commit with CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE (HTTP 413, in the v0.1 error envelope), and nothing is partially applied. [Q2]

### G-004 · SPEC.md line 895 · kept

- **CAOP section:** 14.3 Policy API & Deterministic Pre-Commit Hooks
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Guards: policy and pre-commit hooks (durable guards)
- **Note:** Same CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID rejection; MAOP models it as an evidence Guard.

> The kernel MUST reject unknown or cross-workspace fact IDs in depends_on_fact_ids or depends_on_alternatives with CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID. [Q3]

### G-005 · SPEC.md line 925 · kept

- **CAOP section:** 14.4 Capability API Extensions (execution_locus & Artifact Validation)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Capabilities: registration and lazy discovery
- **Note:** Same CapabilityRegistration obligations; agents.register advertises capabilities lazily.

> Every capability registered in the Capability API MUST declare its execution locus, credential custodian, lease timeout, provider-specific receipt verification keys, and Stage-2 promotion thresholds.

### G-006 · SPEC.md line 955 · kept

- **CAOP section:** 14.5.2 Normative Stage-1 Dispatch Response (Anti-Termination Envelope)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Act: dispatch and host execution
- **Note:** Same Stage-1 continuation envelope (DispatchDirective).

> To prevent conversational LLMs from treating dispatch as a completed turn and replying to the user before invoking their native tool, caop_dispatch_work in Stage 1 MUST return the following continuation envelope:

### G-007 · SPEC.md line 996 · refined

- **CAOP section:** 14.5.3 Thread Write-Locking on Open Leases (CAOP_409_UNSETTLED_EXECUTION_LEASE)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Leases and fencing
- **Note:** Same one-open-lease rule and CAOP_409_UNSETTLED_EXECUTION_LEASE; MAOP adds fenced leases (Lease.fencing_token, monotonic) and leases.renew, so a stale holder cannot settle.

> A workspace thread MAY hold at most one unsettled EXECUTE_DISPATCHED or EXECUTE_EXPIRED invocation at a time. Any call to caop_stage_work or caop_dispatch_work while a lease is open MUST be rejected with CAOP_409_UNSETTLED_EXECUTION_LEASE, forcing the host client to verify whether the previous native tool call succeeded and settle the receipt via caop_settle_receipt first.

### G-008 · SPEC.md line 1252 · refined

- **CAOP section:** 14.7 Reference Host Operating Prompt (CAOP v0.1.2)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Bindings: host operating prompt
- **Note:** Normative block kept verbatim; the obligation is generalised from two named vendor hosts to any conversational host (vendor names become informative examples).

> Deployments operating in ChatGPT (Custom GPT Instructions) or Claude (Project / MCP System Prompt) MUST include the following normative instruction block:

### G-009 · SPEC.md line 1386 · kept

- **CAOP section:** 15.1 Outcome verification and approval steering [a] (under “Normative Schema: Two-Phase Verification & Mid-Flight Steering”)
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Two-phase verification and approval steering
- **Note:** Same steering rule; MAOP states it as an authority Guard (a delta can only narrow an AuthorityGrant).

> An APPROVE_WITH_STEERING_DELTA decision binds the approval to the patched plan, not the staged one. The kernel MUST apply the delta, re-run every Policy pre-commit hook and minimum_attestation check on the patched plan, and dispatch only if all pass; otherwise the work item returns to CANDIDATE_PROPOSAL with CAOP_422_PRECOMMIT_HOOK_FAILED. A delta can only narrow authority: added_policy_constraints may add restrictions but never remove existing ones. [c]

### G-010 · SPEC.md line 1398 · refined

- **CAOP section:** 15.2 Long-horizon context: sub-agents, compaction and lazy schemas [a]
- **Kind:** normative; keywords: MUST
- **MAOP mapping:** Sub-agent isolation, compaction and lazy discovery
- **Note:** Same provenance-pointer rule; MAOP adds Delegation (isolation policy, budget, authority subset) and Receipt.causal_parents so pruned traces stay traceable.

> - **Hierarchical Sub-Agent Context Isolation:** Heavy research or artifact-generation steps spawn an isolated child Work scope (parent_work_id) with its own ephemeral scratchpad. When the child completes RECORD, its raw intermediate turns are discarded and only the ratified commitment and distilled bitemporal facts merge back into the parent control plane. Pruning removes raw traces from the active context, not from provenance: every promoted fact MUST keep a provenance pointer (child work_id, invocation IDs and a content hash of the pruned trace). Raw traces MAY be deleted only under a declared retention policy. [d]

### G-011 · SPEC.md line 1494 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 1252; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-008)

> - Informative note in §14.7 (the “MUST include” text is kept verbatim): “Conformance is determined by kernel behaviour; the kernel cannot verify that a host deployment includes this prompt.”

### G-012 · SPEC.md line 1502 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 789; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-001)

> - “MUST carry one of four epistemic states:” → “MUST carry one of three epistemic states (adoption), and separately a freshness value:”

### G-013 · SPEC.md line 1511 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 845; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-002)

> - §14.2.3 rewritten. Submitted text: “Whenever a new fact F_new supersedes an existing fact F_old (setting F_old.transaction_time.superseded_at), the Creasura kernel MUST synchronously traverse all reverse edges where depends_on_fact_ids contains F_old.fact_id and transition every active dependent commitment or fact to epistemic_status: "STALE_UPSTREAM_PREMISE" within the same database transaction.” Now: synchronous re-evaluation in the same transaction of every dependent reachable through reverse depends_on_fact_ids and depends_on_alternatives edges; a dependent becomes stale only when a required premise has no remaining CURRENT support; optional depends_on_alternatives groups interchangeable supports; staleness propagates transitively; a declared max_invalidation_subgraph limit rejects oversized updates before commit with CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE, nothing partially applied; re-support restores CURRENT; superseded facts and history are never rewritten. The §14.2.1 STALE_UPSTREAM_PREMISE definition gains “, under the support rule of §14.2.3”.

### G-014 · SPEC.md line 1513 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 895; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-004)

> - Sentence added in §14.3: “The kernel MUST reject unknown or cross-workspace fact IDs in depends_on_fact_ids or depends_on_alternatives with CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID.”

### G-015 · SPEC.md line 1541 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 1386; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-009)

> - Normative paragraph added after the caop_dispatch_work schema: “An APPROVE_WITH_STEERING_DELTA decision binds the approval to the patched plan, not the staged one. The kernel MUST apply the delta, re-run every Policy pre-commit hook and minimum_attestation check on the patched plan, and dispatch only if all pass; otherwise the work item returns to CANDIDATE_PROPOSAL with CAOP_422_PRECOMMIT_HOOK_FAILED. A delta can only narrow authority: added_policy_constraints may add restrictions but never remove existing ones.”

### G-016 · SPEC.md line 1543 · kept

- **CAOP section:** Changes from the submitted draft
- **Kind:** editorial record; keywords: MUST
- **MAOP mapping:** Compatibility and migration (CAOP history is frozen)
- **Note:** Editorial-history entry recording the change that produced SPEC.md line 1398; kept as frozen history. Its normative content is tracked by that line's guarantee. (see G-010)

> - Added to the sub-agent isolation bullet, after “its raw intermediate turns are discarded …”: “Pruning removes raw traces from the active context, not from provenance: every promoted fact MUST keep a provenance pointer (child work_id, invocation IDs and a content hash of the pruned trace). Raw traces MAY be deleted only under a declared retention policy.” The IsolationPolicy and DistilledReturnPayload schemas gain the optional fields trace_hash and retention_policy.

## Supplementary lower-case requirements

Not counted as guarantees (the keyword rule is upper case), but checked so that no lower-case obligation in the normative text is lost. Lines in code blocks and in the editorial history are skipped.

| ID | Line | CAOP section | Text | MAOP mapping | Status |
|---|---|---|---|---|---|
| S-001 | 80 | Implementation status | - In the reference kernel, a verification capability (`verification_capability_id`) must be side-effect-free: it may only read external state. Dispatch refuses a deferred check whose capability is not registered as side-effect-free. | Two-phase verification and approval steering | kept |
| S-002 | 91 | Runtime checks beyond the schema | - Receipt nonce: a Stage-1 receipt must echo the `required_nonce` from dispatch (`CAOP_422_VERIFY_ARTIFACT_MISMATCH` otherwise). | Receipts and evidence | kept |
| S-003 | 92 | Runtime checks beyond the schema | - Required receipt fields: the receipt’s `raw_output` must hold every field in the capability’s `required_receipt_fields`. | Receipts and evidence | kept |
| S-004 | 188 | 2.3 State | > **Critical requirement: provenance.** Every material fact should have a traceable origin. | Core abstractions | kept |
| S-005 | 206 | 2.4 Capability | A capability contract should describe what an operation *can do*, not merely what an agent is instructed to attempt. | Core abstractions | kept |
| S-006 | 222 | 2.5 Policy | > **Advisory vs. enforced.** A policy written in an assistant’s instructions is advisory. A policy enforced by a runtime before executing an action is an actual control. Every Creasura policy must state which it is. | Core abstractions | refined |
| S-007 | 269 | 4.1 Observe | > **Invariant:** replaying the same source event must not create duplicate observations. | Outer supervision lifecycle | kept |
| S-008 | 294 | 4.2 Understand | This operation should distinguish retrieved facts from inferred interpretations. | Outer supervision lifecycle | kept |
| S-009 | 338 | 4.4 Plan | The planner may use an LLM. The runtime must still validate the generated plan against schemas, dependencies, and policy constraints. | Outer supervision lifecycle | kept |
| S-010 | 369 | 4.6 Verify | Verification can include deterministic checks, human approval, or model-based evaluation. **The verdict must identify which checks were performed.** | Outer supervision lifecycle | kept |
| S-011 | 386 | 4.7 Record | > **Invariant:** a conflicting state version must reject the transaction or invoke an explicitly defined conflict-resolution policy. | Outer supervision lifecycle | kept |
| S-012 | 410 | 5. Execution state machine | The eight lifecycle stages should not be confused with execution states. | Child lifecycle (execution state machine) | kept |
| S-013 | 443 | 5. Execution state machine | The API must reject invalid transitions. | Child lifecycle (execution state machine) | kept |
| S-014 | 454 | 5. Execution state machine | A transition from CREATED directly to COMPLETED should be rejected unless the work type explicitly supports that shortcut. The runtime persists each accepted transition with an actor, timestamp, reason, and correlation ID. | Child lifecycle (execution state machine) | kept |
| S-015 | 464 | 6. Capability API | The boundary between the OS and the assistants and services that do the work. The OS must not assume every provider supports the same features. | Capabilities: registration and lazy discovery | refined |
| S-016 | 517 | 6.1 Native assistant mapping | > **Note:** Programmatic invocation of an assistant’s native work surfaces must use an explicitly supported interface. Do not assume arbitrary sessions can be launched through MCP. | Capabilities: registration and lazy discovery | kept |
| S-017 | 538 | 7. Cross-cutting contracts | > **v0.2:** An approval can steer the work it approves: APPROVE_WITH_STEERING_DELTA binds the approval to a patched plan, which must pass every policy check again. See [§15.1](#151-outcome-verification-and-approval-steering-a). | Two-phase verification and approval steering | kept |

## Additions

### New operations

| operationId | Method and path | Justification |
|---|---|---|
| `agents.register` | `POST /maop/v1/agents` | CAOP has principals but no agent identity: roles and capabilities could not be declared per agent, so separation of duties (implementer != reviewer != approver) could not be checked. Capabilities are advertised as stubs and hydrated lazily, preserving v0.2 lazy discovery. |
| `delegations.create` | `POST /maop/v1/delegations` | v0.2 isolates child work (parent_work_id, isolation_policy) but only through stage_work. A first-class delegation lets a supervisor hand work to another agent with an isolation policy, a budget and an authority subset that can only narrow the parent's authority (Act->Coordinate edge). |
| `delegations.get` | `GET /maop/v1/delegations/{delegation_id}` | Read model for a delegation and its child lifecycle state, so a supervisor can re-evaluate without polling executions one by one. |
| `leases.renew` | `POST /maop/v1/leases/{lease_id}/renew` | v0.2 leases have a timeout but no renewal or fencing. Renewal with a monotonic fencing_token prevents a holder whose lease expired from settling a receipt after another holder took over (split-brain). |
| `receipts.get` | `GET /maop/v1/receipts/{receipt_id}` | Receipts were only returned inline by settle_receipt. A stable read path with idempotency_key, outcome (including outcome_unknown) and causal_parents makes recovery and audit possible after a crash. |
| `supervision.evaluate` | `POST /maop/v1/supervision/{work_id}/evaluate` | CAOP re-evaluates only on pulse. Event-driven re-evaluation of durable guards returns the next outer transition (including Act->Decide, Act->Coordinate, Verify->Act and any->Recover) with the guards that passed and failed. |

### New definitions

| Definition | Justification |
|---|---|
| `AgentIdentity` | Stable identity of an agent (who acts), distinct from PrincipalRef (who is accountable). |
| `AgentRole` | Enum supervisor, planner, implementer, reviewer, verifier, approver, observer: needed for separation-of-duties guards. |
| `AgentRegistration` | Request/response body of agents.register: identity, roles and lazily advertised capability stubs. |
| `Delegation` | First-class supervisor-to-child work record: isolation policy, budget, authority subset, child lifecycle state. |
| `DelegationCreate` | Request body of delegations.create. |
| `AuthorityGrant` | Explicit, expiring, scoped authority with trust_level (T0_relayed, T1_attested); delegation and steering can only narrow it. |
| `Lease` | Fenced execution lease (lease_id, holder, fencing_token, expires_at); generalises OpenLease. |
| `LeaseRenewal` | Request body of leases.renew; the runtime rejects a stale fencing_token. |
| `Receipt` | Durable action receipt (idempotency_key, outcome incl. outcome_unknown, evidence_refs, causal_parents) for audit and recovery. |
| `SupervisionStage` | Enum of outer-lifecycle stages observe ... closed, including recover, so transitions are machine-checkable. |
| `ChildLifecycleState` | Enum of child-work states proposed ... expired, mapping delegated work onto the inner lifecycle. |
| `Guard` | Durable guard (authority, policy, evidence, freshness, lease, separation_of_duties, budget) re-evaluated on events, not only at commit. |
| `SupervisionEvaluation` | Request/response body of supervision.evaluate. |
| `TransitionDecision` | Result of evaluation: from_stage, to_stage, trigger, guards_passed, guards_failed, next_action. |
| `CausalEvidence` | Evidence item with digest, derived_from and bitemporal times, linking receipts, facts and guards causally. |

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
