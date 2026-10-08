# CURRENT TASKS

## Active Task

**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 014 — Semantic Inventory & Operation Extraction
**Status:** READY_FOR_CODEX
**Task Type:** Deterministic Semantic Contract + Representative Sample Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-5-014-semantic-inventory-operation-extraction.md`

### Accepted Architecture Decisions

- Phase 4 Task 013 handoff is PASS; do not reopen or overwrite frozen Phase 0–4 assets.
- Phase 5 order: 014 Semantic Inventory & Operation Extraction → 015 Observed Function Discovery → 016 Logical Function Normalization → 017 Logical API Formation → 018 Business Domain Classification → 019 Business Capability Mapping.
- Business Domain classification precedes Business Capability Mapping. Do not deduce capabilities from API labels or domain alone.
- Task 018 must start with a dedicated architect-reviewed **mock test** before estate-wide domain mapping.
- Future domain mapping will be reviewable JSON keyed to canonical API IDs, permitting multiple domain candidates and explicit evidence/uncertainty; Task 014 does not implement that mapping.
- Codex discovers → Integration Architect validates → Enterprise Architect decides.

### Task 014 Work Scope

1. Examine accepted compact indexes and define a semantic inventory contract preserving canonical API identity and per-operation evidence.
2. Implement deterministic **representative sample only** for API and operation inventory.
3. Capture exact evidence pointers, missing information, accepted backend observation qualifiers and AS-IS product/plan connections without inventing operation-level routing.
4. Add focused tests and concise committed evidence under `tests/evidence/task-014/`.
5. Update `codex/comm/HANSOFF.md` with results and architecture review questions.

### Key Guardrails

- Read `AGENTS.md`, this file, the latest `HANSOFF.md`, and Task 014 prompt.
- `staging/` is immutable. Frozen graph, canonical identities, backend indexes and accepted reports remain unchanged.
- Operation is an inventory record in this task, **not a CodeGraph node**.
- No semantic function inference, no logical API formation, no domain or business capability tagging in Task 014.
- Preserve unresolved Product-location occurrences, backend uncertainties and provenance. Do not infer runtime consumption.
- Avoid full corpus reprocessing and generic bulk LLM classification.

### Required Stop

**STOP after representative Task 014 mock extraction and validation**. Report PASS / FIX_REQUIRED / HOLD_FOR_ARCHITECTURE_REVIEW in `codex/comm/HANSOFF.md`, commit and push permitted Codex implementation/evidence changes, and request architectural review before scaling the inventory or starting Task 015. Task 018 has its own separate mock-test gate.
