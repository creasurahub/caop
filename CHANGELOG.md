# Changelog

## 0.1.2 (2026-11-05)

An additive superset of v0.1, specified in [section 14 of `SPEC.md`](SPEC.md#14-v012-conformance-stages-causal-state-and-host-enforcement).

- **Runtime conformance profiles** CAOP-STAGE-1/2/3 (host-delegated, kernel-proxied, autonomous kernel), mapped onto the v0.1 conformance levels ([§14.1](SPEC.md#141-runtime-conformance-stages-normative-profiles), [§14.8](SPEC.md#148-compatibility-with-v01)).
- **Adoption vs. freshness:** `epistemic_status` (CANDIDATE_PROPOSAL, RATIFIED_COMMITMENT, VERIFIED_FACT) records adoption; a separate `freshness` (CURRENT, STALE_UPSTREAM_PREMISE) records whether a fact’s premises still hold ([§14.2.1](SPEC.md#1421-epistemic-status-enum-epistemic_status)).
- **Alternatives-aware, bounded causal invalidation:** facts declare `depends_on_fact_ids` and optional `depends_on_alternatives`; a dependent turns stale only when a required premise has no remaining CURRENT support, and propagation is bounded ([§14.2.3](SPEC.md#1423-synchronous-causal-invalidation-rule)).
- **Policy pre-commit hooks:** deterministic checks evaluated at COMMIT before work can be dispatched or sent for approval; a failure keeps the work item a CANDIDATE_PROPOSAL and returns `CAOP_422_PRECOMMIT_HOOK_FAILED` ([§14.3](SPEC.md#143-policy-api--deterministic-pre-commit-hooks)).
- **Capability `execution_locus` and receipts:** capabilities declare execution locus, credential custody, receipt lease, required receipt fields and promotion policy ([§14.4](SPEC.md#144-capability-api-extensions-execution_locus--artifact-validation)).
- **EXECUTE sub-states** with a lease lock on the thread (`CAOP_409_UNSETTLED_EXECUTION_LEASE`) and nonce and provider-artifact checks on receipts (`CAOP_422_VERIFY_ARTIFACT_MISMATCH`) ([§14.5](SPEC.md#145-lifecycle-api-extensions--host-execution-enforcement)).
- **Pulse dead-man’s switch:** `expected_pulse_interval_seconds` with a kernel-side timer and out-of-band notification ([§14.5.5](SPEC.md#1455-scheduled-pulse-dead-mans-switch-expected_pulse_interval_seconds)).
- **Attestation tiers:** `provenance.attestation` is HOST_ASSERTED, KERNEL_ATTESTED or USER_CONFIRMED ([§14.2.4](SPEC.md#1424-provenance-attestation-tiers-provenanceattestation)).
- **Compact binding:** four composite tools, `caop_pulse`, `caop_stage_work`, `caop_dispatch_work` and `caop_settle_receipt`, that fold the eight lifecycle stages; the v0.1 ten-tool API remains conformant ([§14.6](SPEC.md#146-normative-8-to-4-mcp--openapi-lifecycle-binding)).

Contracts added: [`openapi/caop-v0.1.2.openapi.yaml`](openapi/caop-v0.1.2.openapi.yaml) · [`openapi/caop-v0.1.2.openapi.json`](openapi/caop-v0.1.2.openapi.json) · [`schema/caop-v0.1.2.schema.json`](schema/caop-v0.1.2.schema.json). The v0.1 contract files are unchanged.

Q1–Q3 (adoption and freshness are separate; disjunctive support and bounded propagation; no required fields that invite guessing) are design decisions by the spec owner; items a–h are editorial. The full list of changes is in [Changes from the submitted draft](SPEC.md#changes-from-the-submitted-draft).

## 0.1 (2026-11-01)

- Initial release: specification, OpenAPI 3.1 contract, JSON Schema 2020-12 bundle and examples.
