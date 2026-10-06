# CURRENT TASKS

## Active Task

**Phase:** Phase 1 — Object Extraction & Normalization  
**Status:** READY_FOR_CODEX  
**Task Type:** Design refinement only — no implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-1-001-extracted-record-model.md`

### Architecture Direction

Phase 1 extracts deterministic source records and preserves APIC identifiers/URIs.

Phase 1 does **not** establish final canonical identity.

Phase 2 will resolve repeated source occurrences using APIC URI / URL / object identifiers and produce canonical APIC objects.

Phase 3 will reconstruct relationships / CodeGraph from those resolved identities.

### Required Stop

Do not write Phase 1 implementation code in this task.

Stop after producing the requested design report and updating the Codex handoff.
