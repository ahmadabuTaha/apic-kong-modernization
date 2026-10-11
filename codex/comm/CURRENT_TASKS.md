# CURRENT TASKS

## Accepted checkpoints and boundaries
- Phases 0–4: PASS / FROZEN.
- Task 014: PASS / FROZEN — 2,036 canonical APIs, 2,414 supported HTTP operations.
- Task 015: ACCEPTED / FROZEN as provisional automated Observed Function evidence only; not business accuracy certification.
- **Task 016: EA ACCEPTED / FROZEN on 2026-10-11 as provisional Logical Function Candidate Discovery + focused semantic false-positive control.** The full evidence and HANSOFF remain authoritative for its specific findings, NOT confirmations of functional duplicates. 1,170 compared candidate pairs; refinement: 470 potential same behavior, 120 conflicting semantics, 573 insufficient evidence, 6 structural similarity only, 1 different business action supported. 1,481 unpaired operations remain individually visible. No architect-approved equivalence/duplicate/merge/retirement.
- Source is STAGING/sandbox-like. Production usage, active subscriptions/traffic, feature flags, deployment chronology and backend runtime routing remain unproven. Absence of APIC CI/CD/release management and a clear production usage map are EA-reported cross-cutting modernization constraints, not automatically actionable per-API defects.
- Do not reopen frozen components absent concrete reproduced defects; use downstream/additive exceptions, findings and evidence.

## ACTIVE TASK
**Phase:** 5 — Semantic & Business Mapping
**Task:** 017 — Logical API Formation
**Status:** READY_FOR_CODEX_MOCK
**Execute prompt:** `codex/comm/prompts/phase-5-017-logical-api-formation-mock.md`

## Enterprise Architect authorization
Proceed now. No further Task 016 focused rework or mandatory review of all 1,170 candidate pairs. **Authorize ONLY Task 017 bounded representative MOCK.**

Task 017's question is: which DISTINCT business-oriented operations should conceptually belong within coherent Logical API boundaries? This is not automatically the same question as whether two implementation operations perform the same business function. Keep both relationships separate:
- **Candidate duplicate function:** similar action + object + behavioral intent, unapproved.
- **Logical API cohesion:** business-related yet potentially distinct operations (approve/reject/cancel, etc.) that may form a coherent resource/workflow API, without merging functions or current canonical API identities.

Preserve all known contract/version differences and accepted Product/Plan/Subscription context; they may explain different exposure and should not be lost by grouping. Neither shared schema/backend nor Product membership proves cohesion; indirect subscription membership does not establish actual calls. Avoid domains (Task 018), capabilities (Task 019), runtime/production use claims, retirement, Kong conversion and deployment decisions. No source modification. No Confluence bulk ingestion. Index-first, bounded deterministic and targeted provenance verification; minimize tokens and artifacts.

## Required STOP
Complete Task 017 MOCK, tests, compact evidence under `tests/evidence/task-017/mock/`, update `codex/comm/HANSOFF.md`, commit/push and STOP for Integration Architect / EA review. Do not start full Task 017, Task 018 or Task 019 until authorization.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
