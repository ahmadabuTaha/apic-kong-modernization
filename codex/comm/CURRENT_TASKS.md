# CURRENT TASKS

## Active Task

**Phase:** Phase 1 — Object Extraction & Normalization  
**Task:** 002 — Canonical Model Contract Alignment  
**Status:** READY_FOR_CODEX  
**Task Type:** Architecture/design alignment only — no implementation

### Prompt

Read and execute:

`codex/comm/prompts/phase-1-002-canonical-model-contract-alignment.md`

### Architecture Direction

Align the Phase 1 extraction design to the canonical model already established in the project context.

Key rules:

- Do not invent any new taxonomy, status, reason, object type, or relationship type.
- Source occurrence is evidence; it is not automatically a distinct canonical enterprise object.
- APIC URI / URL / object identifier is the primary identity/correlation evidence.
- Phase 1 extracts and preserves evidence.
- Phase 2 resolves APIC identity/references and produces canonical APIC AS-IS objects.
- Phase 3 reconstructs structural relationships / CodeGraph.
- Product → API membership is structurally independent of Subscription.
- Subscription represents configured entitlement/association, not Product membership and not runtime usage.

### Mandatory Reporting Rule

The only reporting artifact for this task is:

`codex/comm/HANSOFF.md`

Do not create any additional report, design, review, result, or summary Markdown file.

### Required Stop

Do not implement Python.

Do not modify Phase 0.

Stop after updating `codex/comm/HANSOFF.md` and wait for architecture review.
