# CURRENT TASKS

## Active Task

**Phase:** Phase 4 — Dependency & Runtime-Configuration Resolution  
**Task:** 012 — API Dependency Discovery & Model Proposal  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation + Evidence Discovery + Architecture Model Proposal

### Prompt

Read and execute:

`codex/comm/prompts/phase-4-012-api-dependency-discovery-and-model-proposal.md`

### Architecture Direction

Task 011 is accepted as PASS.

Task 012 expands Phase 4 from backend target resolution into evidence-based dependency discovery across:

- backend invocation observations already produced by Task 011;
- OAuth2/OIDC/security-provider dependencies;
- explicit security endpoints such as issuer/token/introspection/JWKS where observed;
- explicit external HTTP dependencies;
- configuration/property dependencies.

Core rule:

```text
Observed evidence
≠
Proposed dependency model
≠
Approved canonical model
```

Task 012 may propose a dependency model for architecture review, but must not silently introduce canonical object types or graph relationships.

### Reuse / Token-Efficiency

Reuse:

`indexes/backend_target_resolution.jsonl`

for Task 011 backend observations.

Do not reparse backend target evidence from raw YAML.

Use a lightweight local cache for new dependency parsing, recommended:

`indexes/cache/phase4_dependency_discovery_cache.sqlite3`

Warm runs should avoid reparsing unchanged YAML.

### Required Generated Outputs

Local ignored:

- `indexes/api_dependency_observations.jsonl`
- `indexes/dependency_pattern_inventory.json`
- `indexes/cache/phase4_dependency_discovery_cache.sqlite3`

### Required Evidence Artifacts

Commit under:

`tests/evidence/task-012/`

At minimum:
- `dependency_summary.json`
- `dependency_pattern_inventory.json`
- `dependency_samples.jsonl`
- `dependency_correlation.json`
- `dependency_model_proposal.md`
- `cache_performance.json`
- `commands_and_results.txt`

### Frozen Components

Phase 0 through Task 011 are frozen.

Do not modify them unless Task 012 proves a concrete reproducible defect.

### Explicit Non-Goals

Do not:
- create dependency/backend/security-provider nodes in CodeGraph;
- emit new graph edges or relationship types;
- rebuild CodeGraph;
- change Task 011 target-resolution outcomes;
- infer third-party ownership from hostname alone;
- infer runtime usage;
- perform duplicate/retirement/rationalization analysis;
- map/design Kong;
- design migration waves.

### Mandatory Reporting Rule

The prose reporting artifact remains:

`codex/comm/HANSOFF.md`

HANSOFF must state whether Task 012 is:
- PASS;
- FIX_REQUIRED; or
- HOLD_FOR_ARCHITECTURE_REVIEW.

It must also state whether the observed evidence is sufficient to authorize a later additive CodeGraph dependency-enrichment task.

### Required Stop

Stop after Phase 4 Task 012 implementation, evidence generation, validation, model proposal, HANSOFF update, commit, and push.

Do not begin CodeGraph dependency enrichment or later rationalization/migration work.
