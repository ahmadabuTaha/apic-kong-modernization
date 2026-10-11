# Task 017A architecture review criteria and decisions

## Scope and authority

This is a bounded architecture review of the 71 frozen Task 017 proposals, plus five separately counted oversized adjuncts and directly relevant cross-API links from the accepted 46-case sample. It does not regenerate Task 017, change primary operation membership, perform a broad all-pairs search, or authorize a Logical API, API Product, Kong topology, retirement, Domain, or Capability. Enterprise Architect acceptance is `PENDING` throughout.

## Independent axes

1. Technical validation verifies deterministic construction, reconciliation, provenance, and tests.
2. Evidence sufficiency preserves the frozen Task 017 assessment.
3. Architecture acceptance remains an explicit Enterprise Architect decision.

Technical `PASS` is not architecture approval. Functional-equivalence links, conceptual cohesion, and productization suitability are separate questions.

## R1-R7

| Criterion | Review question |
|---|---|
| R1 | Is a non-generic resource/workflow identity directly supported? |
| R2 | Do distinct actions and paths support shared responsibility/lifecycle rather than mere coexistence? |
| R3 | Is shared consumer, owner, authorization, or entitlement intent evidenced? Product/Plan/Subscription links alone are exposure context. |
| R4 | Are method/path, version, request/response shapes, statuses, and security variants retained without compatibility inference? |
| R5 | Is operation-scoped backend configuration present? API-shared candidates do not prove behavior or runtime egress. |
| R6 | Is concrete counterevidence and a competing boundary/nonformation alternative retained? |
| R7 | Are canonical API, Task 014/015/016 identifiers, source hash, and exact pointer traceable? |

Every criterion is `SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED`, with source references. Group and member evidence is preserved in the committed decision register and expandable ignored index.

## Recommendation meanings

- `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`: direct resource/workflow cohesion is positive, but not approved.
- `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`: exact resource/action/path evidence supports named disjoint subsets; unmatched members remain explicit.
- `KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION`: current API coexistence is the only group signal.
- `REQUIRES_TARGETED_EVIDENCE`: a named missing or contradictory fact blocks a decision.
- `TECHNICAL_OR_TEST_EXPOSURE_REVIEW`: direct source identity or Task 015 nature supports a technical/test review; retirement is not inferred.

The Productization Readiness Gate is `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`. Task 018/019 may add resource taxonomy or common-business-purpose evidence. They cannot establish shared lifecycle ownership, consumer intent, release boundaries, active production use, or safe substitution.
