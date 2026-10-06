# CURRENT TASKS

## Active Task

**Phase:** Phase 1 / Phase 2 Boundary  
**Task:** 004 — Source Precedence and Identity Bridge Closure  
**Status:** READY_FOR_CODEX  
**Task Type:** Architecture/evidence validation only — no implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-1-004-source-precedence-and-identity-bridge.md`

### Architecture Decision

`list.json` / registry summaries are **not** the single source of truth.

The authoritative AS-IS configuration evidence is the actual artifact content present inside the relevant directories under `staging/`.

Registry/list records provide supporting APIC identity, URL, ID, and cross-reference evidence.

### Approved `$ref` Mapping

```text
raw absolute path
→ exact /staging/ suffix
→ repository-relative staging/... path
```

Preserve both raw and mapped values. Do not perform any other path normalization or heuristic rewriting.

### Task Focus

Close the remaining deterministic identity bridges for Product YAML ↔ Product registry, API catalog definition ↔ API registry, Product-location API copies ↔ authoritative API-catalog definitions, and registry-only/artifact-only evidence.

Key rules:
- actual configuration artifact takes precedence for AS-IS configuration content;
- registry/list evidence enriches identity/reference metadata;
- do not merge by name alone;
- do not invent taxonomies;
- Product → API remains independent of Subscription;
- unresolved counterpart gaps remain explicit.

### Mandatory Reporting Rule

The only reporting artifact is `codex/comm/HANSOFF.md`.

Do not create any additional report or Markdown artifact.

### Required Stop

Do not implement Python.

Do not modify Phase 0, tests, indexes, outputs, or staging.

Stop after updating `codex/comm/HANSOFF.md` and wait for architecture review.