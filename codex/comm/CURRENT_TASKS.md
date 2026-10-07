# CURRENT TASKS

## Active Task

**Phase:** Phase 3 — CodeGraph Core  
**Task:** 009 — CodeGraph Core Construction  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-3-009-codegraph-core-construction.md`

### Architecture Direction

Task 008 relationship reconstruction is accepted as PASS.

Task 009 builds the first deterministic CodeGraph over the accepted canonical identity and relationship indexes.

Core rules:
- represent every accepted canonical APIC identity exactly once as a graph node;
- represent every accepted canonical relationship exactly once as a graph edge;
- preserve canonical relationship direction;
- support deterministic incoming/outgoing adjacency and bounded multi-hop traversal;
- preserve provenance through pointers back to accepted Phase 2 / Task 008 records;
- do not materialize inferred or transitive relationships;
- routine graph queries must not rescan raw `staging/`;
- the 113 Task 007 unresolved Product-location occurrences remain excluded.

### Required Evidence Artifacts

Commit review evidence under:

`tests/evidence/task-009/`

At minimum:
- `codegraph_integrity.json`
- `codegraph_counts.json`
- `traversal_samples.jsonl`
- `commands_and_results.txt`

Codex must reference these files in `codex/comm/HANSOFF.md`.

### Frozen Components

Phase 0, Phase 1, Phase 2, Task 007, and Task 008 are frozen.

Do not modify them unless Task 009 proves a concrete reproducible defect or broken downstream requirement.

### Explicit Non-Goals

Do not:
- classify Domain or Exposure Channel;
- create Logical API/Capability identities;
- perform backend discovery;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
- map or design Kong;
- add a graph database, UI, or semantic/inferred edges.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 009 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 009 implementation, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin semantic enrichment, backend resolution, duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
