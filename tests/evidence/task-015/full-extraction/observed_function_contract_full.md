# Task 015 full Observed Function contract

- Contract version: `task015-observed-function-full-v2`; additive-compatible with the accepted `task015-observed-function-mock-v3` contract.
- One provisional Observed Function record corresponds to exactly one accepted Task 014 HTTP operation. Identity, canonical API ID, exact method/path, source provenance, source fingerprint, request/response structure, missing evidence and backend certainty remain explicit.
- Interpretation status is `EXPLICITLY_DESCRIBED`, `INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS`, `AMBIGUOUS_NEEDS_REVIEW`, or `INSUFFICIENT_EVIDENCE`. API-level records additionally preserve `REGISTRY_ONLY_NO_OPERATIONS`, `NO_SUPPORTED_HTTP_PATHS`, and `UNSUPPORTED_PROTOCOL` gaps without inventing operations.
- HTTP method alone is insufficient. A bounded inference requires independent method/path plus parameter or schema/response structure. Contradictory source signals remain ambiguous.
- Exact operation-scoped configuration remains configured evidence. API-shared context remains candidate-only and proves neither operation egress nor runtime use.
- Every interpretation remains `PENDING_REVIEW`. Similar wording and Task 014 structural overlap never establish a Logical Function, duplicate, Logical API, domain, capability, retirement decision, runtime conclusion, or Kong design.
- Low, none, contradictory and API-gap cases may name `CONFLUENCE_POTENTIAL_UNVERIFIED` as a future targeted source. No Confluence content was retrieved and no unseen content contributes facts or certainty.
- Cache entries are keyed by stable Task 014 operation content, frozen-input dependency fingerprint, cache schema and rule version. Writes are atomic; cold, warm and selectively invalidated builds are byte deterministic.
- Source text is safely redacted for URI or credential-value patterns while retaining original-text fingerprints. No language model was used; measured model-token use is zero.
