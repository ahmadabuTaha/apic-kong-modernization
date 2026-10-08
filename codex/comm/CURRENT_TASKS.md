# CURRENT TASKS

## Frozen checkpoints
Phase 0–4: PASS / FROZEN. Task 014 Semantic Inventory: **PASS / FROZEN** (EA accepted 2026-10-08); 2,036 canonical APIs, 2,414 HTTP operations, 60 unconfirmed structural overlap candidate pairs. Do not modify frozen sources/identity/graph/Task 014 assets absent a specific reproduced defect.

## Active Task
**Phase:** 5 — Semantic & Business Mapping
**Task:** 015 — Observed Function Discovery, Full Inventory Continuation
**Status:** READY_FOR_CODEX_FULL_EXTRACTION

### Prompt
Read and execute:
`codex/comm/prompts/phase-5-015-full-observed-function-inventory.md`

### Enterprise Architect decision (2026-10-08)
Task 015 mock is **APPROVED as a bounded provisional discovery method** (15 operations, 14 APIs; HANSOFF HOLD_FOR_ARCHITECTURE_REVIEW was its required stop). Its 7 explicit, 5 multi-signal provisional, 2 ambiguous, 1 insufficient cases demonstrate evidence/uncertainty handling, not business-semantic accuracy certification. Now authorize Task 015 **full extraction only** across all accepted Task 014 operation records.

Maintain Task 015 role strictly: answer what an operation appears to do, not prove business-function correctness, duplicates, logical functions/APIs, domains, capabilities, retirement or Kong configuration. Preserve PENDING_REVIEW interpretations, contradictions, source/evidence IDs, missing fields and configured-versus-candidate backend certainty.

### Gap controls
Treat the 11-category inherited gap register as a baseline. NON_BLOCKING metadata gaps can be supported by other independent evidence; LOCAL_REVIEW_REQUIRED cases need focused follow-up; DOWNSTREAM_BLOCKER applies ONLY to the affected operation or specific downstream conclusion, never a blanket phase stop. Preserve 36 registry-only APIs, 5 HTTP-no-supported-path documents, 113 unresolved Product-location occurrences, native protocol limits and the 60 unconfirmed structural overlap pairs. Do not silently turn missing evidence into facts or merge function identities.

### Confluence note
EA confirms enterprise Confluence contains extensive API explanations, but content is numerous. **Do not read or ingest Confluence in this task.** Treat it as a possible targeted future supplementary source for low-evidence or disputed functions, subject to explicit later authorization and verifiable page provenance. No assumptions based on unseen pages; do not block current discovery.

### Implementation and stop
Use accepted frozen CodeGraph/indexes + Task 014 inventory/cache, incremental deterministic observed-function cache, and targeted source reads only if necessary. No Vector DB, Blackboard or Multi-Agent initiative. Reconcile all 2,414 operations with one record per operation, include full Gap Impact Register and review queue. Test deterministic cold/warm outputs, selective invalidation, safe redaction, frozen integrity and record counts. Commit bounded evidence under `tests/evidence/task-015/full-extraction/`, with full local ignored indexes/cache.

Update `codex/comm/HANSOFF.md`, commit/push and **STOP for architectural review of Task 015 full results**. Do not start Task 016 or Tasks 017–019. Task 018 remains a mandatory dedicated domain mock review before Task 019 business capability mapping.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
