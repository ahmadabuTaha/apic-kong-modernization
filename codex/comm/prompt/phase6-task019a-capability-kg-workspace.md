# Phase 6 — Business Capability Knowledge Graph
## Task 019-A — Workspace Consolidation and Accepted 015-A Baseline

**Status:** AUTHORIZED_FOR_CODEX
**Stop gate:** `EA_REVIEW_TASK019A`

### Intent
The EA establishes **Phase 6 / Task 019** as the next sequential workstream after Phase 5 Task 018F. The earlier `Capability-KG/015-A` Common-module inventory normalization is **already TECHNICAL PASS** according to `codex/comm/HANSOFF.md`; DO NOT rerun or redesign it. Task 019-A is **organizational consolidation and reproducible compatibility verification only**. Future phases of Task 019 (019-B onward) are separately authorized.

Scope remains: **Module → Service → ICD/ISD**, with Sub Module irrelevant to identity, taxonomy and graph. Objective of future Task 019: ICD/ISD acquisition and caching → Business Main/Sub Capability evidence → existing canonical API and Operation mappings → evidence-backed queryable knowledge graph. No Productization, CI/CD, release strategy, Kong design, or retirement.

### Directory contract (repo conventions; keep generated data gitignored)
Use a dedicated **code package**:
```text
business_capability_kg/
    __init__.py
    inventory_normalization.py   # migrated from accepted capability_kg implementation, with equivalent behavior
    # future: document_acquisition.py, cache.py, icd_extraction.py, isd_extraction.py, resolution.py, graph.py
tests/
    business_capability_kg/
        test_inventory_normalization.py
        # subsequent task tests
indexes/
    phase6/
        task019/
            019a/              # deterministic derived inventory indexes
            # future stage-local caches/indices
outputs/
    services_icd_isd_inventory.csv  # EXISTING PRIVATE INPUT — leave in place, never git add
    phase6/
        task019/
            019a/              # manifest.json, validation_summary.md etc.
            # future documents/icd, documents/isd, reports, graph, etc.
codex/comm/
    CURRENT_TASKS.md
    prompt/
        phase6-task019a-capability-kg-workspace.md
        # future phase6-task019b... prompts
```
The **single coherent workstream** is `Phase6 / Task019`; code is versioned in `business_capability_kg/`, generated indexes in `indexes/phase6/task019/`, and outputs in `outputs/phase6/task019/`, consistent with `AGENTS.md` and `.gitignore`. Do **not** put executable code under `outputs/`. Keep Codex communication files only under allowed `codex/comm/` paths.

### Execution tasks
1. Read latest `AGENTS.md`, `codex/comm/CURRENT_TASKS.md`, and latest `codex/comm/HANSOFF.md` first. Inspect existing Task 015-A implementation, tests, manifest and paths **targetedly**; do not scan unrelated staging.
2. Establish `business_capability_kg/` as the owned, versioned Python package. Prefer **minimal move/import-forward compatibility** over a rewrite. Existing imports and CLI invocations must continue working where required by tests/consumers. New entry point uses the dedicated code package. Preserve 015-A behavior byte-for-byte on source-equivalent runs.
3. Establish canonical output/index namespaces exactly under `outputs/phase6/task019/019a/` and `indexes/phase6/task019/019a/`. Reuse the accepted Common normalized records and provenance; prefer validated copy/migration with hash/count equivalence rather than reparsing the input. Existing `outputs/capability_kg/015a/` and `indexes/capability_kg/015a/` remain historical baseline, **do not delete or overwrite**.
4. Keep the local input `outputs/services_icd_isd_inventory.csv` intact and ignored by Git. Preflight verify file if needed, not GitHub presence. Never include it in commits or paste sensitive source URLs into reports.
5. Provide a compact index/manifest recording: `source_baseline=Capability-KG/015-A`, source file SHA-256 (if present), existing accepted 116 row/116 service/225 reference counts, old/new relative paths, hashes, and byte/semantic equality checks; if migration cannot be proven, stop as `REVIEW_REQUIRED_MIGRATION_MISMATCH` without claiming completion.
6. Include concise folder-level task ownership notes in `outputs/phase6/task019/019a/validation_summary.md` (NOT extra reports): 019-A consolidation; 019-B document acquisition; 019-C persistent cache; 019-D ICD semantics; 019-E ISD contracts; 019-F canonical resolution; 019-G capability API/scheduler mapping; 019-H knowledge graph; 019-I queries and validation; 019-J module rollout. These are a roadmap, **NOT permission to implement**.
7. Add focused import/CLI/migration equivalence tests, run relevant tests. Do not reopen frozen Task 015 or 018F logic. Preserve inherited external test failures as historical observations rather than attributing them to this task.

### Acceptance
- All code attributable to this workstream has a clearly-owned package `business_capability_kg/`; stable compatibility with previous 015-A entry points.
- Generated files for the new workstream live beneath task-scoped `indexes/phase6/task019/` or `outputs/phase6/task019/`, not scattered in new root namespaces.
- Accepted Common pilot identity/reference counts, row provenance, order and document multiplicity unchanged.
- Old outputs remain intact; `outputs/services_icd_isd_inventory.csv` unchanged; Stage / Phases 0–5 historical evidence unchanged.
- A targeted test confirms deterministic results and no network/download/semantic work.
- Final handoff gives short path mapping, hashes/counts, tests, blockers, commit SHA, and `EA_REVIEW_TASK019A`.

**STOP after Task 019-A.** No ISD/ICD fetch, parsing, business capability derivation, API/operation mapping, graph construction, Productization, CI/CD or Kong implementation.
