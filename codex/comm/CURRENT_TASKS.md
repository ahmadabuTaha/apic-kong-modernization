# CURRENT TASKS

## Active Task

**Phase:** Phase 3 — CodeGraph Review Tooling  
**Task:** 010 — CodeGraph Explorer / Visualization  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-3-010-codegraph-explorer-visualization.md`

### Architecture Direction

Task 009 CodeGraph Core is accepted as PASS.

Task 010 builds a local visual review/debug explorer over the existing accepted CodeGraph indexes.

Core rules:
- read existing CodeGraph nodes/edges/adjacency only;
- support targeted visual neighborhoods, not full-graph default rendering;
- support search, incoming/outgoing/both traversal, depth 1–3, and relationship filters;
- expose node/edge provenance;
- distinguish registry-only vs dual evidence where accepted provenance supports it;
- preserve isolated nodes without inference;
- do not mutate CodeGraph nodes, edges, directions, identities, or semantics;
- the 113 Task 007 unresolved occurrences remain excluded.

### Required Evidence Artifacts

Commit review evidence under:

`tests/evidence/task-010/`

At minimum:
- `explorer_acceptance.json`
- `visual_review_samples.jsonl`
- `commands_and_results.txt`

Codex must reference these files in `codex/comm/HANSOFF.md`.

### Frozen Components

Phase 0, Phase 1, Phase 2, Task 007, Task 008, and Task 009 are frozen.

Do not modify them unless Task 010 proves a concrete reproducible defect.

### Explicit Non-Goals

Do not:
- create or infer new graph relationships;
- classify Domain or Exposure Channel;
- create Logical API/Capability identities;
- resolve backends;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
- map or design Kong;
- build a production portal.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 010 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 010 implementation, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin semantic enrichment, backend resolution, duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
