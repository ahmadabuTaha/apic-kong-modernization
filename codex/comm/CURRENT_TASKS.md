# CURRENT TASKS

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## ACTIVE TASK
**Phase:** 5 — Semantic & Business Mapping
**Task:** 018A — Business Domain Discovery Validation (ENTERPRISE-aligned)
**Status:** READY_FOR_CODEX_DOMAIN_VALIDATION_SAMPLE
**Execute:** `codex/comm/prompts/phase-5-018a-business-domain-discovery-validation.md`

## EA instruction
Run a **40–60-case deterministic operation-centered discovery validation sample only**, not full Task 018 or Task 019. Reuse accepted indexes. Probe real enterprise domain/subdomain responsibility boundaries and umbrella-vs-domain ambiguity, with explicit Business Object / Process / State / Capability / Event evidence slots; do not fabricate unavailable dimensions. Candidate taxonomy is derived from the APIC evidence and is NOT an enterprise-approved taxonomy.

Long-term architecture goal is one Domain-Centric vocabulary usable across Applications, Integration/APIs, Data and Events; broad umbrella categories must not force fine-grained domain decisions. **Enterprise Domain Alignment** must be independently reviewed by the EA at the Task018A decision gate. Keep cross-layer business model comparisons as open questions where evidence from other systems is not supplied; no fabricated enterprise approval.

Sample includes 017A 71-proposal cases, 5 oversized groups, 14 links, SC Request, positive/negative controls, technical utilities and contradictory descriptions. Classify by Task 014 HTTP **operation**, never whole canonical API by inherited name; derive sample-only API Domain Footprint and preserve all unresolved alternatives. Enrich but DO NOT change the 90-item Productization Decision Backlog, Logical API member identities or older task findings. Domain similarity cannot prove functional equivalence or one Logical API Product.

## Deliverables and mandatory STOP
Produce committed evidence under `tests/evidence/task-018/domain-validation/` as specified in prompt, run focused and repo tests, update `codex/comm/HANSOFF.md`, commit/push and STOP for EA review. **No Task018B full estate**, Task019, domain approvals, Kong topology or Productization decisions without explicit architect decision.

Codex discovers -> Integration Architect validates -> Enterprise Architect decides.
