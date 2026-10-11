# CURRENT TASKS

## Frozen baselines
- Phases 0–4: PASS / FROZEN.
- Task 014 Semantic Inventory: PASS / FROZEN (2,036 accepted canonical APIs; 2,414 HTTP operations).
- Task 015 Observed Function Discovery: ACCEPTED / FROZEN as **provisional automated extraction**, not verified business meaning (all 2,414 operation records preserved). Keep staging/sandbox context and review gaps explicit.
- Task 016 mock: completed as a bounded comparison-method review. Task 016 full candidate inventory **EXECUTED / REVIEW_REQUIRED**, NOT semantic-equivalence approved. Full HANSOFF baseline: 1,170 candidate pairs across 933 paired operations; 1,481 visible unpaired operations; 405 possible-same, 637 conflicting signals, 125 insufficient evidence, 3 clearly different; 717 structurally equal compared pairs. Never equate those 717 with functional duplicates.
- Do not reopen the frozen components for mere new findings; use additive refinements. No changes to immutable staging sources.

## Active Task
**Phase:** 5 — Semantic & Business Mapping
**Task:** 016 — Focused Semantic Refinement / Functional Duplication False-Positive Control
**Status:** READY_FOR_CODEX_FOCUSED_REFINEMENT

### Execute prompt
`codex/comm/prompts/phase-5-016-focused-semantic-refinement.md`

## Enterprise Architect architecture finding and decision
The objective is to identify **possible duplicate implementations of the SAME business function behind different API names, endpoint forms or naming conventions**. Current structural similarity is only a candidate signal. E.g. Approve, Reject, Cancel, Activate and Deactivate are distinct business actions on the same object even if payload schema, method and backend system look identical.

**Required refinement (existing Task 016 candidates, NOT full Task 016 re-run):**
1. Use Business Action + Business Object + Behavioral Semantics as the logical-function identity hypothesis. Distinguish STRUCTURAL_SIMILARITY_ONLY, DIFFERENT_BUSINESS_ACTION_SUPPORTED, POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE, CONFLICTING_SEMANTICS_REVIEW and SEMANTIC_EVIDENCE_INSUFFICIENT.
2. Verify backend **operation-level** evidence where available, not only backend system or target identity: method/path, assembly, dispatch, branch, rewriting and transformation pointers. Unknown behavior stays unknown; no runtime inference.
3. Compare evidence for suspicious endpoint pairs across differing names/paths/forms; beware shared request/response wrappers and common schema shapes. Explicitly audit approve/reject/cancel false positives and differently named possible true duplicates.
4. Retain version/variant differences, Product/Plan/Subscription exposure links and staging limitations as contextual evidence — NEVER infer live traffic, production adoption, active feature flags, retirement or interchangeability.
5. Work incrementally using frozen Task 014/015 and existing Task 016 indexed evidence, retain all 1,170 existing candidate pairs plus the 1,481 unpaired-visible operations, prioritize targeted source verification and compact samples. Do not require human review of all pairs, do not reprocess everything, and do not use all-pairs exhaustive comparison.
6. Produce additive safe evidence under `tests/evidence/task-016/semantic-refinement/` and full local ignored indexes; validate deterministic outputs, exact reconciliation, false-positive prevention, evidence scope and frozen-component integrity. Preserve original interpretation/provenance IDs.

### STOP / authorization boundary
Update `codex/comm/HANSOFF.md`, commit/push, and STOP for Integration Architect / Enterprise Architect review. Task 017 Logical API Formation remains **NOT AUTHORIZED** until Task 016 refinement acceptance. No Rationalization, Retirement or Kong conversion actions.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
