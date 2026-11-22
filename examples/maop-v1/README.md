# MAOP v1 examples

Draft examples for MAOP v1.0.0-draft.1. Every file validates against [`../../schema/maop-v1.schema.json`](../../schema/maop-v1.schema.json).

## Definition examples

Each `<Name>.json` is a valid instance of `#/$defs/<Name>`.

| File | Definition |
| --- | --- |
| [`AgentIdentity.json`](AgentIdentity.json) | `#/$defs/AgentIdentity` |
| [`AgentRole.json`](AgentRole.json) | `#/$defs/AgentRole` |
| [`AgentRegistration.json`](AgentRegistration.json) | `#/$defs/AgentRegistration` |
| [`Delegation.json`](Delegation.json) | `#/$defs/Delegation` |
| [`DelegationCreate.json`](DelegationCreate.json) | `#/$defs/DelegationCreate` |
| [`AuthorityGrant.json`](AuthorityGrant.json) | `#/$defs/AuthorityGrant` |
| [`Lease.json`](Lease.json) | `#/$defs/Lease` |
| [`LeaseRenewal.json`](LeaseRenewal.json) | `#/$defs/LeaseRenewal` |
| [`Receipt.json`](Receipt.json) | `#/$defs/Receipt` |
| [`SupervisionStage.json`](SupervisionStage.json) | `#/$defs/SupervisionStage` |
| [`ChildLifecycleState.json`](ChildLifecycleState.json) | `#/$defs/ChildLifecycleState` |
| [`Guard.json`](Guard.json) | `#/$defs/Guard` |
| [`SupervisionEvaluation.json`](SupervisionEvaluation.json) | `#/$defs/SupervisionEvaluation` |
| [`TransitionDecision.json`](TransitionDecision.json) | `#/$defs/TransitionDecision` |
| [`CausalEvidence.json`](CausalEvidence.json) | `#/$defs/CausalEvidence` |

## Operation request examples

Each `<operationId>.request.json` is a valid request for one new operation. For POST operations it is the request body and validates against the named definition. For GET operations, which have no body, it holds the path parameters and validates against the operation's path parameters (each a non-empty string).

| File | Operation | Validates against |
| --- | --- | --- |
| [`agents.register.request.json`](agents.register.request.json) | `agents.register` (`POST /maop/v1/agents`) | `#/$defs/AgentRegistration` |
| [`delegations.create.request.json`](delegations.create.request.json) | `delegations.create` (`POST /maop/v1/delegations`) | `#/$defs/DelegationCreate` |
| [`delegations.get.request.json`](delegations.get.request.json) | `delegations.get` (`GET /maop/v1/delegations/{delegation_id}`) | path parameters |
| [`leases.renew.request.json`](leases.renew.request.json) | `leases.renew` (`POST /maop/v1/leases/{lease_id}/renew`) | `#/$defs/LeaseRenewal` |
| [`receipts.get.request.json`](receipts.get.request.json) | `receipts.get` (`GET /maop/v1/receipts/{receipt_id}`) | path parameters |
| [`supervision.evaluate.request.json`](supervision.evaluate.request.json) | `supervision.evaluate` (`POST /maop/v1/supervision/{work_id}/evaluate`) | `#/$defs/SupervisionEvaluation` |

The same examples are embedded as `example` values in [`../../openapi/maop-v1.openapi.yaml`](../../openapi/maop-v1.openapi.yaml).
