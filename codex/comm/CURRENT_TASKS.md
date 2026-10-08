# CURRENT TASKS

## Active Task

**Phase:** Phase 4 — Dependency & Runtime-Configuration Resolution  
**Task:** 013 — Additive Backend Target CodeGraph Enrichment  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Graph Enrichment + Explorer Integration + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-4-013-additive-backend-target-codegraph-enrichment.md`

### Architecture Direction

Task 012 is accepted as architecture evidence and its HOLD is resolved by explicit Enterprise Architect decisions.

Approved decisions:
- `backend_target` is now an approved canonical graph object type;
- unresolved symbolic targets may become `backend_target` nodes when explicit target evidence exists;
- use existing approved `api_invokes_target` for API → Backend Target;
- operation scope is an edge qualifier/provenance attribute, not a node;
- Security Provider remains API metadata/attribute only;
- Catalog/Configuration references remain provenance/attributes only;
- `jwt-validate/jws-jwk` observations are omitted from dependency graph enrichment.

Desired backend classification outcomes:
- `ACE`
- `BACKEND`
- `EXTERNAL_VIA_DATAPOWER`
- otherwise `VALIDATION_REQUIRED`

Classification must be evidence-based. Do not classify from names/tokens alone.

### Additive-Only Rule

Do NOT rebuild or overwrite:

- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`
- `indexes/codegraph_adjacency.jsonl`
- `indexes/relationship_index.jsonl`

Create an additive dependency layer instead.

### Required Generated Outputs

Local ignored:

- `indexes/codegraph_dependency_nodes.jsonl`
- `indexes/codegraph_dependency_edges.jsonl`
- `indexes/codegraph_dependency_adjacency.jsonl`

### Explorer Requirement

Update the local CodeGraph Explorer so an API can visibly show its Backend Target(s), and a Backend Target can show the APIs invoking it.

Preserve existing visual caps and provenance drill-down.

### Required Evidence Artifacts

Commit under:

`tests/evidence/task-013/`

At minimum:
- `backend_target_graph_summary.json`
- `backend_target_classification_summary.json`
- `api_invokes_target_samples.jsonl`
- `backend_target_reuse.json`
- `explorer_dependency_acceptance.json`
- `commands_and_results.txt`

### Frozen Components

Phase 0 through Task 012 are frozen.

Task 013 is additive only.

### Explicit Non-Goals

Do not:
- rebuild Phase 3 CodeGraph;
- create Operation nodes;
- create Security Provider nodes;
- create Catalog Property/Configuration Reference nodes;
- graph JWT/JWK patterns;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
- map/design Kong;
- design migration waves.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 013 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

### Required Stop

Stop after Task 013 implementation, additive graph generation, Explorer integration, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
