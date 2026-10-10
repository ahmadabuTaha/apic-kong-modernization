# CURRENT TASKS

## Frozen Checkpoints
- Phase 0–4: PASS / FROZEN.
- Task 014 Semantic Inventory & Operation Extraction: PASS / FROZEN (2,036 canonical APIs; 2,414 accepted HTTP operations).
- **Task 015 Observed Function Discovery: ACCEPTED / FROZEN by Enterprise Architect on 2026-10-10 AS PROVISIONAL AUTOMATED INTERPRETATION INVENTORY**, not a business-semantic accuracy certification. Full 2,414/2,414 operation coverage; 1,662 explicitly described, 285 inferred from structural signals, 54 ambiguous and 413 insufficient under deterministic extraction rules. All records retain PENDING_REVIEW status. HANSOFF's HOLD_FOR_ARCHITECTURE_REVIEW was the completed Task 015 stop, superseded by the architect's approval to progress.
- Retain 571 Task 015 review items: 467 operation interpretations, 44 API-level gap records, and 60 structural-overlap pairs. None is silently dismissed or promoted to confirmed business truth. Known Phase 0 fixture test errors are still open.
- The source estate was exported from a staging/sandbox-like environment. Do NOT interpret missing descriptions, unconfirmed runtime usage, or low automatic semantic evidence as quality problems in production APIs or evidence of inactivity.
- Reopen a frozen component ONLY on a concrete reproducible defect, contradiction or broken downstream contract; use additive downstream evidence/exception handling by default.

## Active Task
**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 016 — Logical Function Normalization
**Status:** READY_FOR_CODEX_MOCK
**Prompt:** `codex/comm/prompts/phase-5-016-logical-function-normalization-mock.md`

### Current authorization — MOCK only
Test evidence-based candidate logical-function equivalence/non-equivalence across distinct canonical APIs and operation records, including different names, the seasonal visa v2 pair, actual request/response schema differences, action/object signals, configured backend scope and uncertainty. Use targeted, indexed, deterministic retrieval with carefully bounded raw source reads. Avoid all-pairs analysis or new vector database/Blackboard/multi-agent system.

Maintain separate:
1. structural overlap candidate,
2. provisional similar Observed Function wording,
3. possible SAME LOGICAL FUNCTION requiring semantic validation,
4. a confirmed business/function duplicate or safe replacement decision (NOT authorized now).

Treat Task 015 confidence as automated-interpretation evidence strength, NOT actual business-function accuracy. Preserve ambiguous, incomplete and contradictory cases; avoid interpreting missing Swagger summaries as API defects. Specific evidence gaps block only the affected claim/grouping, not all Task 016.

Confluence may be a future targeted enrichment source but is not a dependency of the mock and must not be bulk ingested or assumed to contain evidence not reviewed.

### Required STOP
Implement and test Task 016 MOCK only; commit safe evidence under `tests/evidence/task-016/mock/`, update `codex/comm/HANSOFF.md`, and STOP for Integration Architect / Enterprise Architect review. Do not start Task 016 full estate or Tasks 017–019.
Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
