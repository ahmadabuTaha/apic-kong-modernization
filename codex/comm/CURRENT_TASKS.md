# CURRENT TASKS

## Active Task

**Phase:** Phase 2 — URI / Identifier Resolution  
**Task:** 007 — Targeted Investigation of 113 Unresolved Product-Location API Occurrences  
**Status:** READY_FOR_CODEX  
**Task Type:** Targeted Investigation

### Prompt

Read and execute:

`codex/comm/prompts/phase-2-007-targeted-investigation-unresolved-product-location-apis.md`

### Architecture Direction

Do not begin Phase 3.

Investigate and explain exactly why Task 006 left 113 Product-location API occurrences unresolved.

The task must:
- enumerate all 113 records;
- prove how the 113 population is derived;
- inspect the admissible identity/reference evidence for each record;
- distinguish correctly unresolved evidence from any reproducible resolver defect;
- preserve the existing no-name-only/no-hash-only merge rules;
- leave Phase 0 and Phase 1 frozen;
- avoid changing the resolver unless a concrete Task 006 defect is first proven.

### Required Evidence Artifacts

This task explicitly requires committed investigation evidence under:

`tests/evidence/task-007/`

At minimum:
- `unresolved_product_location_apis.jsonl`
- `investigation_summary.json`
- `commands_and_results.txt`

Codex must reference these artifacts in `codex/comm/HANSOFF.md`.

### Reporting

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must explain the 113 with representative evidence and state whether Phase 2 is:

- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 007 investigation, evidence generation, focused validation, HANSOFF update, commit, and push.

Do not begin Phase 3 relationship reconstruction.
