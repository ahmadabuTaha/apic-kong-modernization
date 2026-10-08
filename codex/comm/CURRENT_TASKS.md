# CURRENT TASKS

## Approved Checkpoint — Task 014
**Status: PASS / FROZEN**. Enterprise Architect approval: 2026-10-08.
Baseline confirmed by latest Task 014 HANSOFF: 2,036 canonical APIs, 2,414 HTTP operations, 60 structural-overlap candidate pairs, approved backend A + YAML variants A, persistent semantic cache with cold/warm parity. Task 014 frozen source/index artifacts must remain intact. Existing gaps remain as evidence, not silently resolved: 36 registry-only APIs, 5 APIs without supported HTTP Path Items, 113 unresolved Product-location occurrences, metadata absences, candidate-only backend associations, and five pre-existing Phase 0 fixture test setup errors.

## Active Task
**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 015 — Observed Function Discovery
**Status:** READY_FOR_CODEX_MOCK
**Task Type:** Bounded representative semantic discovery + inherited gap impact review

### Prompt
Read and execute:
`codex/comm/prompts/phase-5-015-observed-function-discovery.md`

### Mandatory requirements
- CodeGraph/index-first, Task 014 semantic inventory/cache-first, targeted raw evidence only where required. No new Blackboard, multi-agent framework, or Vector DB.
- Begin with a stratified mock of ~12–20 operations, covering well-described and poorly-described records, multi-operation APIs, backend evidence certainty, and v2 request/response/backend differences.
- Implement compact evidence-backed Observed Function records. Never invent function, runtime egress or a confirmed duplicate.
- **Inherited Gap Impact Register:** keep reason and provenance, affected API/operation IDs, effects on Tasks 015–019, severity NON_BLOCKING / LOCAL_REVIEW_REQUIRED / DOWNSTREAM_BLOCKER, and a mitigation/recheck trigger. Never allow upstream gaps to disappear silently.
- Generate safe review evidence, tests and review queue under `tests/evidence/task-015/mock/`.
- Do not alter frozen Phase 0–4 or Task 014 or raw staging. Only reopen passed work for proven defect, contradiction or broken downstream requirement.
- Do not implement Tasks 016–019, Logical API grouping, Business Domain/Capability mapping, or Kong migration.
- Task 018 domain mock remains independently mandatory before Task 019 capabilities.

### Stop
Update `codex/comm/HANSOFF.md`, commit and push the Task 015 mock, then **STOP for Integration Architect / Enterprise Architect review** before any estate-wide Task 015 extraction or Task 016.
