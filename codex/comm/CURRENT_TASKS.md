# CURRENT TASKS

## Active Task

**Phase:** Phase 3 — Relationship Reconstruction / CodeGraph  
**Task:** 008 — Deterministic Relationship Reconstruction  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-3-008-deterministic-relationship-reconstruction.md`

### Architecture Direction

Phase 2 is accepted as PASS.

Task 008 builds only deterministic structural relationships between resolved canonical APIC AS-IS identities.

Use only the approved relationship taxonomy and only explicit accepted evidence.

Do not:
- infer Domain or Exposure Channel;
- create Logical API/Capability identities;
- infer backend/runtime usage;
- perform duplicate, retirement, rationalization, migration, or Kong design work;
- promote the 113 unresolved Product-location occurrences into graph relationships.

### Required Evidence Artifacts

Commit review evidence under:

`tests/evidence/task-008/`

At minimum:
- `relationship_counts.json`
- `relationship_samples.jsonl`
- `relationship_coverage.json`
- `commands_and_results.txt`

Codex must reference these files in `codex/comm/HANSOFF.md`.

### Frozen Components

Phase 0, Phase 1, and accepted Phase 2 identity resolution are frozen.

Do not modify them unless Task 008 proves a concrete reproducible defect that blocks relationship reconstruction.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 008 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 008 implementation, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin semantic enrichment, backend resolution, duplicate analysis, rationalization, or Kong design.
