# CURRENT TASKS

## Accepted / frozen baseline
- Phases 0–4: PASS / FROZEN.
- Task 014: PASS / FROZEN — 2,036 canonical APIs and 2,414 HTTP operations.
- Task 015: ACCEPTED / FROZEN as provisional observed-function interpretation.
- Task 016: ACCEPTED / FROZEN as provisional candidate-discovery + semantic false-positive control, **not** architect-approved duplicate or functional equivalence. Full 1,170 pair proposals; semantic refinement 470 potential same behavior, 120 conflicting, 573 insufficient, 6 structural only, 1 supported different action. Maintain 1,481 unpaired operations.
- Original Task 017 10-case mock: **TECHNICAL EXECUTION COMPLETE / ARCHITECTURAL VALIDATION PENDING.** Ten cases over 22 operations; 2 cohesive provisional, 3 partial/variant, 4 insufficient, 1 separate. Its 90 passed repo tests (and five known Phase 0 setup errors) are implementation test outcomes, NOT a PASS for business/API boundary correctness.
- Source is STAGING/sandbox-like. No proven production usage, deployment sequence, consumer activity, flags or actual runtime egress. Enterprise lacks consistent APIC naming, CI/CD/release management and reliable Production use mapping (EA reported). Never fill those gaps with invented standards or assumptions.

## ACTIVE TASK
**Phase:** 5 — Semantic & Business Mapping
**Task:** 017 — Expanded Logical API Boundary Validation Sample
**Status:** READY_FOR_CODEX_EXPANDED_VALIDATION
**Execute:** `codex/comm/prompts/phase-5-017-expanded-evidence-validation.md`

## EA scope and reason
The architect explicitly **does not approve proceeding to Task 017 full estate** on just 10 examples. Expand the mock to roughly 40–50 traceable cases (retain original 10, add >=30 genuinely distinct new cases where evidence permits) with adversarial positive/negative boundary evidence. Include a detailed SC Request study (approve/reject vs cancel), business-object vs lifecycle/consumer/ownership evidence separation, alternative coherent boundaries, contradictory examples, versions, Product/Plan/subscription exposure context, backend scope and cases that must not group.

**Machine test PASS != architecture PASS.** For every case apply explicit resource/action, workflow cohesion, consumer boundary, contract, backend certainty, negative evidence, source provenance criteria; show evidence-sufficiency status separate from technical test outcome and EA approval (PENDING). No invented organizational standard. Preserve alternative groupings and avoid equating API cohesion with functional duplication, or treating schema/shared backend/name overlap as sufficient.

Consume existing Task 014–016 indexes and Task 017 10-case mock. New results are additive; do not mutate frozen inputs or original mock reports. Keep candidate IDs and operation IDs traceable; no auto-merge, retirement, domain/capability assignment, Kong design, Product-as-logical-API shortcut, production inference, full-estate extraction or manual adjudication of thousands of comparisons. Minimize token use via indexed/bounded deterministic sampling, compact tables and targeted raw verification only.

## Mandatory STOP
Generate evidence under `tests/evidence/task-017/expanded-validation/`; execute tests, update `codex/comm/HANSOFF.md`, commit/push, then STOP for EA review of the expanded evidence before any Task 017 Full. Do not start Tasks 018/019.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
