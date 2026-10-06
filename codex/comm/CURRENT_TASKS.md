# CURRENT TASKS

## Active Task

**Phase:** Phase 1 / Phase 2 Boundary  
**Task:** 003 — Deterministic Resolution Contract  
**Status:** READY_FOR_CODEX  
**Task Type:** Evidence validation and resolution-design only — no implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-1-003-resolution-contract.md`

### Architecture Direction

Establish exactly how the APIC staging evidence connects structurally before implementation.

Validate the deterministic joins across:

- list/catalog registry records;
- detailed JSON objects;
- APIC self URLs and IDs;
- Consumer Org → Application references;
- Credential → Application references;
- Subscription → Application/Product/Plan references;
- Product → API `$ref` membership;
- Product → Plan membership;
- Plan → API entitlement;
- API registry/list records and full API definitions under `staging/apis/_catalog`.

Key rules:

- Do not invent taxonomies or statuses.
- Do not merge by name.
- Exact APIC URL/ID/path/key evidence first.
- Product → API membership is independent of Subscription.
- Subscription is entitlement/association evidence, not runtime usage.
- Unresolved deterministic references remain unresolved.

### Mandatory Reporting Rule

The only reporting artifact is:

`codex/comm/HANSOFF.md`

Do not create any additional report or Markdown artifact.

### Required Stop

Do not implement Python.

Do not modify Phase 0, tests, indexes, outputs, or staging.

Stop after updating `codex/comm/HANSOFF.md` and wait for architecture review.
