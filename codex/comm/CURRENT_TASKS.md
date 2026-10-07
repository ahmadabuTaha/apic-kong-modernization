# CURRENT TASKS

## Active Task

**Phase:** Phase 4 — Dependency & Runtime-Configuration Resolution  
**Task:** 011 — Catalog Properties Indexing & Target Resolution Foundation  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Validation

### Prompt

Read and execute:

`codex/comm/prompts/phase-4-011-catalog-properties-and-target-resolution.md`

### Architecture Direction

Phase 3 is accepted as structurally complete through Task 010:
canonical identities → structural relationships → CodeGraph → visual explorer.

Task 011 begins Phase 4 using the newly supplied local configuration evidence:

`staging/config/catalog-properties.json`

Expected structure:

```json
{
  "catalogProperties": [
    {"name": "ace-tip-internal", "value": "ip:port", "protected": ""}
  ]
}
```

Core rules:
- index the properties file deterministically;
- resolve exact symbolic references such as `$(ace-tip-internal)` only from exact property evidence;
- do not infer backend technology from property names;
- preserve missing, conflicting, protected, and runtime-parameterized cases explicitly;
- account for all 2,036 canonical APIs;
- build a lightweight local reusable cache to avoid repeated YAML parsing;
- keep Task 008 relationships, Task 009 CodeGraph, and Task 010 Explorer unchanged;
- do not emit dependency graph nodes/edges yet.

### Lightweight Cache Requirement

Preferred implementation: Python standard library SQLite.

Recommended local ignored cache:

`indexes/cache/phase4_resolution_cache.sqlite3`

Cache invalidation must use:
- source file SHA-256;
- parser/schema version;
- relevant catalog-properties file SHA-256.

Warm runs should reuse cached parsed observations and avoid unnecessary raw YAML reads.

Do not modify `.gitignore` and do not commit the cache.

### Required Generated Indexes

Local ignored:
- `indexes/catalog_properties.jsonl`
- `indexes/backend_target_resolution.jsonl`
- `indexes/cache/phase4_resolution_cache.sqlite3`

### Required Evidence Artifacts

Commit under:

`tests/evidence/task-011/`

At minimum:
- `catalog_property_summary.json`
- `target_resolution_summary.json`
- `target_resolution_samples.jsonl`
- `target_pattern_inventory.json`
- `cache_performance.json`
- `commands_and_results.txt`

### Frozen Components

Phase 0 through Phase 3 Task 010 are frozen.

Do not modify them unless Task 011 proves a concrete reproducible defect that blocks Phase 4 resolution.

### Explicit Non-Goals

Do not:
- create canonical backend nodes;
- emit `api_invokes_target` edges;
- create canonical Catalog Property nodes yet;
- emit `api_uses_catalog_property` edges yet;
- fully model OAuth2/OIDC dependencies;
- fully model third-party dependencies;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
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

Stop after Phase 4 Task 011 implementation, evidence generation, validation, HANSOFF update, commit, and push.

Do not begin later dependency modeling or CodeGraph enrichment.
