# CURRENT TASKS

## Active Task

**Phase:** Phase 2 — URI / Identifier Resolution  
**Task:** 006 — Deterministic APIC Identity Resolver  
**Status:** READY_FOR_CODEX  
**Task Type:** Implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-2-006-deterministic-apic-identity-resolver.md`

### Architecture Direction

Implement the first deterministic Phase 2 resolver over the frozen Phase 1 extracted-occurrence index.

Core rules:
- Phase 1 source occurrences remain immutable evidence/provenance;
- actual artifacts under `staging/` remain authoritative configuration evidence;
- registry/list records provide APIC identity/reference enrichment;
- resolve identity by exact self URL, APIC ID + compatible scope, and the approved scoped Product/API bridges;
- Plan identity is contextual to Product;
- resolve only the approved Product `$ref` mapped path;
- preserve registry-only, artifact-only, unresolved, ambiguous, and broken-reference evidence explicitly;
- never merge by name alone or hash alone;
- never emit credential secret/client ID values;
- do not invent taxonomies/statuses/reasons/object types.

### Phase Boundary

Task 006 performs APIC identity/reference resolution only.

Do not:
- build Phase 3 CodeGraph edges;
- classify Domain or Exposure Channel;
- create Logical API/Capability identities;
- infer backend/runtime usage;
- perform duplicate, retirement, rationalization, or Kong mapping/design work.

### Frozen Components

Phase 0 remains frozen.

Phase 1 is accepted for Phase 2 entry and remains frozen unless a reproducible Phase 1 defect directly blocks this task.

The known Phase 0 fixture-packaging issue remains outside scope.

### Implementation Allowed

Codex may create/modify resolver implementation code and focused Phase 2 tests required by the task.

Do not modify raw `staging/`, frozen Phase 0 behavior, `.gitignore`, `CURRENT_TASKS.md`, or prompt files.

### Mandatory Reporting Rule

The only reporting artifact is:

`codex/comm/HANSOFF.md`

Do not create additional design/report/summary Markdown files.

### Required Stop

Stop after Task 006 implementation, validation, HANSOFF update, commit, and push.

Do not begin Phase 3 relationship reconstruction.
