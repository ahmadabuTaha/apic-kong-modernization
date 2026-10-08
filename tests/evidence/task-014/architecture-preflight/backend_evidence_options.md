# Backend evidence attribution options

## Evidence findings

The committed sample covers a one-operation API with an API-shared invoke, a 24-operation API with 24 invokes under ordinary `switch` branches, one- and eight-operation APIs with explicit `operation-switch` anchors, an API with no accepted invocation evidence, and an explicit `NOT_EVIDENCED_IN_SAMPLE` result for a mixed shared/scoped API. Task 011 scope classifications and observation IDs are unchanged.

Operation count never upgrades configuration evidence into runtime evidence. In particular, each ordinary `switch` branch on the 24-operation sample remains `CONFIGURED_API_SHARED`; it has conditional action context but no exact method/path operation anchor. Its operation associations are candidates only.

| Case | Accepted fact | Revised representation | Limit |
|---|---|---|---|
| Shared invoke, one operation | `API_SHARED` | `CONFIGURED_API_SHARED` plus separate `CANDIDATE_INHERITED_CONTEXT` | One operation does not prove egress. |
| Shared invokes, many operations/targets | `API_SHARED` | Preserve each configured fact and conditional source pointer; candidate operation contexts remain separate | Branch semantics and runtime selection are not established. |
| `operation-switch` case | `OPERATION_SCOPED` | `EVIDENCED_OPERATION_SCOPED` with exact lower-case method and exact path | Configuration evidence, not runtime usage. |
| No accepted invocation evidence | none | `UNRESOLVED_ROUTING` | Absence is not proof that no backend exists. |

## Options

1. Keep the old conservative model. Shared facts stay only on the API record. This minimizes overclaiming but loses useful candidate context for downstream review.
2. Recommended: use two layers. The factual layer contains `CONFIGURED_API_SHARED`, `EVIDENCED_OPERATION_SCOPED`, exact Task 011 provenance, resolution, policy/action context, and optional exact operation anchors. A separate candidate layer contains `CANDIDATE_INHERITED_CONTEXT`, links to exact method/path inventory anchors, `CANDIDATE_ONLY` certainty, and an explicit denial of proven egress.
3. Attribute every shared invoke to every operation. Reject: this converts configuration context into unsupported operation-egress claims, especially for conditional/multiple-target assemblies.

Facts are Task 011 observation identity, accepted scope, source path/pointer, resolution state, policy position, and exact operation-switch method/path anchors. Candidate associations are possible inheritance from API-shared context. Neither layer proves runtime use.

## Old versus revised

The old Task 014 record safely says `API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS`, but cannot carry reviewable per-operation candidates. The recommended additive candidate layer retains those associations without placing them in `operation_scoped_backend_evidence`. Exact operation anchors use the source-evidenced lower-case HTTP method plus the exact OpenAPI path; matching is equality, not name or path similarity.
