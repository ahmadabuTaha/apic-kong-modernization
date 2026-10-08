# CURRENT TASKS

## Active Task

**Phase:** Phase 5 — Semantic & Business Mapping
**Task:** 014 — Semantic Inventory & Operation Extraction (Architecture Preflight / Full Extraction Continuation)
**Status:** READY_FOR_CODEX_ARCHITECTURE_PREFLIGHT
**Task Type:** Architecture Options + Targeted Evidence Mock + Explicit Approval Gate

### Prompt

Read and execute:

`codex/comm/prompts/phase-5-014-architecture-preflight-and-full-extraction.md`

The original sample prompt and Task 014 contract remain historical baseline; this continuation supersedes the original **sample-only stop** without authorizing estate-wide rollout yet.

### EA decisions (2026-10-08)

- **APPROVED:** Factual Semantic Inventory Contract: canonical API IDs, traceable operation inventory records (not CodeGraph nodes), missing states, provenance.
- **REVISION_REQUIRED:** Backend Evidence representation. Do not treat previous API_SHARED/OPERATION_SCOPED record attribution contract as fully approved. Produce actual examples and alternatives; preserve frozen Task 011 facts and never infer proven operation egress from API_SHARED context.
- **REVISION_REQUIRED:** Multiple YAML representations / same-canonical-ID variants. Do not assume selecting the lexically first YAML fully resolves conflicting semantics. Produce deterministic conflict/variant assessment and alternatives; do not redefine frozen canonical identity.
- **APPROVED:** Persistent Incremental Semantic Cache, versioned and source/dependency fingerprint-based, including explicit invalidation, cold/warm parity and deterministic outputs.

### Current authorized work — Gate A only

1. Inspect latest `HANSOFF.md` and Task 014 mock evidence (6 APIs / 35 operations).
2. Test representative real examples for backend evidence attribution and YAML representation variants, using compact graph/indexes first.
3. Assess structural overlap candidates among DIFFERENT canonical API IDs / names as a separate, evidence-only feasibility study, without claiming confirmed duplication.
4. Produce options, tradeoffs, recommendation, proof samples, and two specific questions requiring Enterprise Architect decision under `tests/evidence/task-014/architecture-preflight/`.
5. Run focused validations and redaction/frozen-integrity checks.
6. Update `codex/comm/HANSOFF.md`, commit/push preflight evidence, report `HOLD_FOR_ARCHITECTURE_REVIEW` and **STOP**.

### Planned work — Gate B NOT YET AUTHORIZED

The continuation prompt fully specifies the proposed full extraction and cache plan, but **do not run estate-wide extraction until both revision-required decisions are explicitly approved** and this task status is changed to `READY_FOR_CODEX_FULL_EXTRACTION`.

Once approved: graph-first/canonical index-first, cache-first, targeted source parsing; reconcile all accepted 2,036 baseline canonical APIs (2,000 source-backed, 36 registry-only), retain unsupported/missing cases and unresolved 113 Product-location occurrences; run cold/warm and invalidation tests; emit compact committed evidence and full local ignored indexes; freeze Task 014 only after successful final validation.

### Hard guardrails

- Do not change frozen Phase 0–4 graph/indexes/identity/evidence or raw `staging/`.
- No Operation graph nodes, no invented backend route/runtime assertion, no fabricated functional/domain/capability meaning.
- Use the existing graph + indexes as the conceptual Blackboard, with incremental fingerprinted caching and compact evidence; NO new Multi-Agent framework or orchestrator.
- No Task 015–019 implementation, no Domain/Capability mapping, no rationalization, no Kong design.
- Task 018 retains its **separate mandatory domain mock review gate**.
- Codex discovers → Integration Architect validates → Enterprise Architect decides.

### Required stop

Stop after Gate A preflight report and architect-review handoff. Do not treat an approved cache/contract as approval of the two pending revisions, and do not auto-run Gate B.
