# CURRENT TASKS

## Active Task

**Phase:** Phase 3 — Backend / Target Resolution  
**Task:** 011 — Deterministic Backend / Target Resolution  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-3-011-backend-target-resolution.md`

### Architecture Direction

Task 010 CodeGraph Explorer is accepted as PASS.

Task 011 addresses the known structural gap:

`api_invokes_target = 0`

The task must deterministically extract backend/target invocation evidence from explicit APIC source configuration and produce a target-resolution index for architecture review.

Critical rule: the approved canonical object taxonomy currently has no backend/target object type.

Therefore Task 011 must:
- resolve target evidence without inventing backend/target canonical nodes;
- preserve static, dynamic, parameterized, unresolved, ambiguous, and broken-reference cases explicitly;
- preserve operation-level scope when proven;
- preserve source expression and provenance;
- account for all 2,036 canonical APIs;
- keep Task 008 relationships and Task 009 CodeGraph unchanged;
- not emit `api_invokes_target` edges yet.

### Required Generated Index

Recommended local ignored index:

`indexes/backend_target_resolution.jsonl`

### Required Evidence Artifacts

Commit review evidence under:

`tests/evidence/task-011/`

At minimum:
- `target_resolution_summary.json`
- `target_resolution_samples.jsonl`
- `invocation_mechanism_inventory.json`
- `commands_and_results.txt`

Codex must reference these files in `codex/comm/HANSOFF.md`.

### Frozen Components

Phase 0, Phase 1, Phase 2, Task 007, Task 008, Task 009, and Task 010 are frozen.

Do not modify them unless Task 011 proves a concrete reproducible defect that blocks target resolution.

### Explicit Non-Goals

Do not:
- invent a backend/target canonical object type;
- add backend nodes to CodeGraph;
- emit `api_invokes_target` relationships;
- add catalog-property nodes/relationships;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
- classify Domain or Exposure Channel;
- map or design Kong;
- design migration waves.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 011 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 011 implementation, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin backend canonical modeling, CodeGraph enrichment, semantic duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
