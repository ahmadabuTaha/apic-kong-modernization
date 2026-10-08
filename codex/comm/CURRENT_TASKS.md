# CURRENT TASKS

## Active Task
**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 014 — Semantic Inventory & Operation Extraction — Gate B Full Extraction
**Status:** READY_FOR_CODEX_FULL_EXTRACTION
**Task Type:** Additive deterministic implementation + persistent incremental cache + full canonical inventory + evidence validation

### Active prompt
Read and execute:
`codex/comm/prompts/phase-5-014-architecture-preflight-and-full-extraction.md`

Gate A Architecture Preflight is COMPLETE (latest `codex/comm/HANSOFF.md`: HOLD awaiting EA decisions); **the Enterprise Architect has now approved Option A + Option A**. Do not repeat Gate A or wait for the same decisions.

### Approved EA decisions — 2026-10-08

1. **APPROVED — Semantic Inventory Contract:** canonical API join IDs, factual API and operation inventory records (operations are NOT CodeGraph nodes), full provenance, explicit missing/review states.
2. **APPROVED — Backend Attribution Option A:** two distinct layers: factual configured backend evidence and separate, clearly labeled possible per-operation inherited context. Keep Task 011 API_SHARED/OPERATION_SCOPED facts and exact method/path anchors; preserve conditional routing. Candidate context is NEVER proven operation egress or runtime use, even for one-operation APIs.
3. **APPROVED — YAML Source Variants Option A:** one canonical API envelope with all source variant provenance; deduplicate byte-identical payload storage, retain different-hash equivalent variants; preserve conflicting variants separately for architecture review and do not union semantics or alter frozen canonical identity.
4. **APPROVED — Persistent Incremental Semantic Cache:** source fingerprint + extractor schema/version + accepted relationship/backend dependency fingerprints as applicable. Deterministic cold/warm equivalence, selective invalidation, atomic writes.

### Explicit architect instruction: v2 comparison

For cross-canonical API pairs, particularly `searchseasonalvisarequests` vs `searchseasonalvisarequests-v2`, do not stop at method/path or name. Include a **separate evidenced comparison of request AND response structures/contracts AND backend targets** with version/exposure/policy distinctions when available. Preserve matching and differing fields, resolution/missing states, source pointers, and whether backend evidence is shared configuration versus operation-scoped. Use exact request/response schema signatures when deterministically available, not schema-ref names alone. Different canonical IDs remain distinct. Report **POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION** only; do not claim actual functional duplication.

### Gate B Authorized Scope

- Reuse frozen CodeGraph and compact indexes, then cache, then targeted source parses on cache misses. No new Blackboard or Multi-Agent architecture; no broad LLM corpus analysis.
- Reconcile all accepted canonical APIs: baseline 2,036 (2,000 source-backed and 36 registry-only); preserve explicit unsupported/missing states and 113 unresolved Product-location occurrences.
- Generate complete additive semantic API and operation inventory, approved backend attribution, source variant provenance, cache manifest, coverage/gap evidence and separate structural-overlap CANDIDATES based on multiple evidence signals.
- Build safe, bounded, operation-level comparisons for v2 example including request/response/backend and report structural evidence differences. Future business functional duplicate validation belongs to Tasks 015–016 or later decisions.
- Run focused and repository tests, cold/warm/invalidation tests, redaction and byte-integrity tests, deterministic replay; commit compact artifacts under `tests/evidence/task-014/full-extraction/`. Keep generated full indices/cache under ignored `indexes/` or `outputs/`.
- Update `codex/comm/HANSOFF.md` with counts, coverage, cache metrics, exceptions, PASS / FIX_REQUIRED / HOLD_FOR_ARCHITECTURE_REVIEW and explicit findings.

### Hard constraints

Do not mutate frozen Phase 0–4 indices/graph/evidence or `staging/`. Do not invent runtime or operation egress, Functional Duplication, Domains, Capabilities, Logical APIs or Kong configuration. Do not implement Tasks 015–019. Task 018 retains its independent mandatory Domain mock. Codex discovers → Integration Architect validates → Enterprise Architect decides.

### Required STOP

Complete **Task 014 Gate B only**, generate evidence, test, update HANSOFF, commit/push and **STOP** for architecture review. Do not automatically freeze Task 014 or begin Task 015.
