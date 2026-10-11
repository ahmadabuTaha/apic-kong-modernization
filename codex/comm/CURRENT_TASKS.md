# CURRENT TASKS

## Frozen checkpoints
Phases 0–4 PASS / FROZEN. Task 014 PASS / FROZEN: 2,036 canonical APIs and 2,414 accepted HTTP operations. Task 015 ACCEPTED / FROZEN as **provisional automated Observed Function Inventory**, not certified business semantics: 2,414 records, including 467 ambiguous/insufficient. Do not reinterpret staging metadata gaps as production quality or usage verdicts. Preserve identities, fingerprints, provenance, accepted relationship indexes and frozen components.

## Task 016 Mock — reviewed checkpoint
**Status:** MOCK METHOD ACCEPTED / CLOSED; original 10 comparisons remain proposal-only and PENDING_REVIEW.
Latest prior HANSOFF reported 4 possible-same, 3 conflicting, 2 clearly different, 1 not comparable. Tests 70 passed, 5 pre-existing Phase 0 fixture setup errors. The mock proved bounded comparison but NOT estate-wide candidate discovery or functional sameness. EA now authorizes full Task 016 with endpoint, subscription and version-context additions; it does not approve any duplicate, retirement or API merge.

## ACTIVE TASK
**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 016 — Full Logical Function Candidate Discovery & Normalization
**Status:** READY_FOR_CODEX_FULL_EXTRACTION
**Execute:** `codex/comm/prompts/phase-5-016-full-logical-function-normalization.md`

### Architectural requirements
- Discover similar candidate logical functions across the entire accepted Task 014/015 estate, NOT limited to the original 60 structural-overlap pairs. Use bounded multi-signal candidate generation, avoid unbounded all-pairs search.
- **Endpoint analysis:** compare frontend method/path/base path, request+response and backend configured target/assembly/routing/transformations. Separate API_SHARED candidate backend from exact operation-scoped configured fact; no runtime egress inference.
- **Product, Plan, Subscription context:** for suspected related APIs, traverse only accepted Product/Plan/Subscription links and explicitly state link scope, consumer exposure and missing/unresolved status; subscription membership does NOT demonstrate calls, production use or retirement. Retain 113 unresolved Product-location occurrences.
- **Version/variant analysis:** naming and versions are not assumed to follow a reliable standard. Identify potential contract/business-rule differences, multiple concurrent variants and consumer differences. Treat old/new, active use, feature flags and parallel routing as hypotheses UNLESS exact source configuration evidence supports them. A potentially common logical business function can have different contracts or subscriber populations.
- Preserve positive and negative evidence, source uncertainty, Task 015 weak interpretations, API identities and all 11 inherited gap categories. Distinguish technical overlap, provisional functional overlap, contract compatibility and architect-approved equivalence (not authorized).
- STAGING / sandbox-like export is the evidence source; it does not prove production deployment, adoption, live traffic or version obsolescence. No Confluence bulk ingestion, Vector DB, Blackboard or multi-agent framework. Use index/cache-first targeted retrieval.
- Output full local indexed catalog plus compact evidence under `tests/evidence/task-016/full-extraction/`; validate exact coverage, safe redaction and deterministic repeatability.

### Mandatory stop
Update `codex/comm/HANSOFF.md`, commit/push and **STOP for Integration Architect / EA review before Task 017**. Do not begin Tasks 017–019, Rationalization or Kong design.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
