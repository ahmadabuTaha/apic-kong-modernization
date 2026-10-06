# CURRENT TASKS

## Active Task

**Phase:** Phase 1 — Object Extraction & Normalization  
**Task:** 005 — Extractor Implementation  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-1-005-extractor-implementation.md`

### Architecture Direction

Implement the deterministic Phase 1 source-occurrence extractor.

Core rules:
- actual artifacts under `staging/` are authoritative configuration evidence;
- registry/list/collection records provide APIC identity/reference evidence;
- Phase 1 extracts evidence only;
- do not merge occurrences into canonical APIC objects;
- do not resolve URLs/IDs/references;
- do not build graph edges;
- preserve raw references and provenance;
- apply only the approved Product `$ref` `/staging/` mapping;
- never emit credential secret/client ID values;
- do not invent taxonomies/statuses/reasons/object types.

### Implementation Allowed

Codex may create/modify implementation code and focused Phase 1 tests required by the task.

Do not modify raw `staging/`, frozen Phase 0 behavior, `.gitignore`, `CURRENT_TASKS.md`, or prompt files.

### Mandatory Reporting Rule

The only reporting artifact is:

`codex/comm/HANSOFF.md`

Do not create additional design/report/summary Markdown files.

### Required Stop

Stop after Phase 1 extraction implementation, validation, HANSOFF update, commit, and push.

Do not begin Phase 2 resolution.