# CURRENT TASKS

## Frozen / accepted historical checkpoints
- Phases 0–4 PASS / FROZEN.
- Task 014 PASS / FROZEN: 2,036 canonical APIs, 2,414 supported HTTP operations.
- Task 015 ACCEPTED / FROZEN as **provisional automated** Observed Function inventory; not verified business accuracy.
- Task 016 ACCEPTED / FROZEN as **provisional** functional candidate discovery/refinement, not approved equivalence or duplication. Full 1,170 compared operation pairs; refinement 470 potential same, 120 conflicting, 573 insufficient, 6 structural only, 1 supported different action. Retain 1,481 unpaired-visible operations.
- Task 017 Mock and Expanded Validation: **METHOD ACCEPTED FOR FULL PROVISIONAL FORMATION**, not approval of sample boundary assignments. Original 10 mock cases + 36 expanded = 46 cases, 98 unique operations, 86 canonical APIs; evidence outcomes: 3 sufficient for provisional, 19 partial, 23 insufficient, 1 supported separate; architecture approval 0/46. Original tests passed (99 repository tests, 5 known Phase 0 fixture setup errors). Keep original evidence unchanged, maintain sample as regression suite.

## ACTIVE TASK
**Phase:** 5 — Semantic & Business Mapping
**Task:** 017 — FULL Logical API Formation
**Status:** READY_FOR_CODEX_FULL_EXTRACTION
**Execute:** `codex/comm/prompts/phase-5-017-full-logical-api-formation.md`

## EA authorization and execution intent
The Enterprise Architect explicitly authorizes Task 017 **FULL ESTATE provisional logical API formation** following expanded evidence review. This is **NOT** an architecture approval of any Logical API or duplicate, merger, replacement, retirement, or runtime use.

Build explainable, source-provenanced conceptual Logical API boundaries across all 2,414 supported operations, maintaining explicit unformed/singleton outcomes and accounting for the 1,481 unpaired Task 016 operations. Retain 36 registry-only API and five source-backed API no-supported-path gaps without inventing operations. Reuse Task 014–016 indexed catalogs and Task 017 original/expanded cases; NO expensive re-extraction or all-pairs search. Business action/object/resource and workflow evidence drives conceptual cohesion; matching name/schema/backend/Product is never proof. Maintain distinct business actions, current API identities, Product/Plan/Subscription exposure, versions and contracts.

Apply the R1–R7 explicit rubric at boundary/member level. R1+R2+R7 can support a **SUFFICIENT_FOR_PROVISIONAL_BOUNDARY** proposal for a well-evidenced resource-path family in a multi-operation accepted API even without R3 consumer/ownership or R5 runtime/backend-semantic evidence; those gaps remain recorded. Cross-API grouping demands stronger evidence and alternatives/counterevidence; unknowns remain explicit. Keep technical PASS/FAIL, evidence sufficiency, and EA acceptance (PENDING) separate. Retain 46 sample cases as named regression, especially SC Request PARTIAL and negative controls.

Staging/sandbox exports do not establish production, usage, release lineage, active flags, subscriptions in production or live backend egress. Lack of standardized naming, APIC CI/CD/Release Management and Production usage mapping are architectural constraints, not license to invent status. Preserve frozen phases, API IDs, source hashes/fingerprints and original Task 017 sample evidence. No Confluence bulk ingestion, Vector DB, Blackboard or multi-agent design.

## Required outputs and STOP
Execute ONLY the full Task 017 prompt. Generate full local ignored formation/coverage/review indexes plus compact committed evidence under `tests/evidence/task-017/full-extraction/`; compile and run tests, update `codex/comm/HANSOFF.md`, commit/push and STOP for Integration Architect / EA review. Do NOT start Task 018 Business Domain Classification, Task 019 Business Capability Mapping, API Rationalization or Kong TO-BE.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
