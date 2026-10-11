# Task 016 focused semantic refinement contract

Logical Function Identity remains a hypothesis composed of **Business Action + Business Object + Behavioral Semantics**. Structural similarities retrieve review candidates; they never prove identity.

| Refinement verdict | Deterministic meaning | Prohibited interpretation |
|---|---|---|
| `STRUCTURAL_SIMILARITY_ONLY` | Schema, endpoint, backend-system, or generic wording signals exist without aligned supported behavior. | Not a duplicate or same function. |
| `DIFFERENT_BUSINESS_ACTION_SUPPORTED` | Independently documented or corroborated actions differ on an aligned object. Approve, reject, cancel, terminate, activate/deactivate, create/retrieve and read/write stay distinct. | Not a duplicate candidate, merge, or retirement basis. |
| `POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE` | Supported action sets and object evidence align across different exposure forms. Behavioral identity remains pending. | Not approved equivalence or interchangeability. |
| `CONFLICTING_SEMANTICS_REVIEW` | Source signals conflict, object intent does not align, or interpretation remains contradictory. | Do not resolve from schema/backend similarity. |
| `SEMANTIC_EVIDENCE_INSUFFICIENT` | Operation-level action/object/behavior cannot be established. | Unknown is not same, different, unused, or retired. |

Source descriptions/summaries provide documented action evidence. Two agreeing structural sources may provide provisional corroboration. A name or single path signal alone cannot support a hard different-action verdict. Task 015 HIGH remains automated interpretation strength, not verified business meaning.

Backend certainty is separate: `CONFIGURED_API_SHARED_CANDIDATE`, `CONFIGURED_OPERATION_SCOPED`, `RESOLVED_OPERATION_SEMANTICS`, or `NOT_EVIDENCED`. Assembly selector/invoke/rewrite/branch/transformation pointers may narrow configuration scope; GatewayScript presence is never interpreted as behavior and configuration never proves runtime egress.

Product, Plan, Subscription, version and staging context remain contextual only. No record approves a duplicate, merge, replacement, retirement, live traffic, production adoption, active feature flag, Logical API, or Kong design.
