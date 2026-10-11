# Negative controls and boundary ambiguity

The sample contains 13 explicit negative controls. Structural or contextual similarity is never enough to form a boundary.

## Appointment Status Workflow

- Why tested: The compared operations share structural and routing signals.
- Why not formed: Task 016 found conflicting action semantics; a shared path, schema, or backend is not cohesion proof.
- Alternative: Keep each current canonical API as a separate exposure boundary pending review.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Cancelled Visa vs Dependents Control

- Why tested: Shared sponsor-information text conflicts with cancelled-visa versus dependents paths.
- Why not formed: Keep visa cancellation history and dependent listing separate.
- Alternative: Keep visa cancellation history and dependent listing separate.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Category Lookup Boundary

- Why tested: The same path and shapes lack supported action/object semantics.
- Why not formed: Retain separate exposures until category ownership and consumers are evidenced.
- Alternative: Retain separate exposures until category ownership and consumers are evidenced.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Establishment Opening License Control

- Why tested: Copied laborer retrieval text cannot establish one boundary for GSBI-license and farming-file opening.
- Why not formed: Separate establishment-opening workflows by license/process until ownership is known.
- Alternative: Separate establishment-opening workflows by license/process until ownership is known.
- Result: `INSUFFICIENT`; EA `PENDING`.

## MOMRA Verification Boundary

- Why tested: Equal shapes coexist with violated-establishment versus certificate-validity resource signals.
- Why not formed: Separate establishment-violation and certificate-validity APIs.
- Alternative: Separate establishment-violation and certificate-validity APIs.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Subscription Price vs Authentication Control

- Why tested: API/path intent contradicts the shared refunded semantic signal.
- Why not formed: Keep pricing and authentication-indicator APIs separate.
- Alternative: Keep pricing and authentication-indicator APIs separate.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Technical Health and Token Boundary Control

- Why tested: No positive cohesion evidence in the original anchor.
- Why not formed: A system health check and security token issuance have distinct technical intents, contracts, and security context.
- Alternative: Retain separate health and token conceptual boundaries; no consolidation is proposed.
- Result: `SUPPORTED_SEPARATE`; EA `PENDING`.

## Tier Termination vs Refund Update Control

- Why tested: Shared update/refunded evidence conflicts with terminate-tier naming and path.
- Why not formed: Keep tier termination and refund update separate.
- Alternative: Keep tier termination and refund update separate.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Turnover Indicator vs Callback Control

- Why tested: A generic report signal cannot join turnover indicator and authentication callback paths.
- Why not formed: Keep turnover reporting and callback processing separate.
- Alternative: Keep turnover reporting and callback processing separate.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Unidentified Root Test Operations

- Why tested: No positive cohesion evidence in the original anchor.
- Why not formed: Root test endpoints lack sufficient business resource and behavioral evidence.
- Alternative: Keep each current canonical API as a separate exposure boundary pending review.
- Result: `INSUFFICIENT`; EA `PENDING`.

## User Management Exposure Ambiguity

- Why tested: Generic URI paths and equal shapes do not identify a resource.
- Why not formed: Keep privilege and general user-management exposures separate until resource and authorization semantics are known.
- Alternative: Keep privilege and general user-management exposures separate until resource and authorization semantics are known.
- Result: `INSUFFICIENT`; EA `PENDING`.

## WPS Certificate Retrieval

- Why tested: The wrappers share an object token and structurally equal compared shapes.
- Why not formed: Only one side has a documented action; generic wrapper and backend similarity cannot establish a boundary.
- Alternative: Keep each current canonical API as a separate exposure boundary pending review.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Worker Examination vs Contract Creation Control

- Why tested: Copied worker-examination text conflicts with an employment-contract creation path.
- Why not formed: Keep examination lookup and contract creation separate.
- Alternative: Keep examination lookup and contract creation separate.
- Result: `INSUFFICIENT`; EA `PENDING`.

## Non-transitive trap

If A and B share a schema, and B and C share a configured backend or object token, A and C are not equivalent and do not automatically share a Logical API. This register creates only direct case-to-member hypotheses and records `transitive_equivalence_inferred=false`. The user-management, Qiwa-streaming, and copied-description controls deliberately avoid joining larger similarity clusters.

Do not form a boundary when R1 is contradicted/unresolved, when R2 rests only on tokens or shapes, when copied descriptions conflict with paths, or when unresolved members would raise group certainty. Product/Plan overlap, version family, response wrapper, and API-shared backend evidence remain context only.
