# CURRENT TASKS

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## ACTIVE TASK
**Phase:** 5 — Enterprise Business Domain Reconciliation
**Task:** 018C — Enterprise Business Domain — Deterministic QIWA Module Mapping
**Status:** AUTHORIZED_FOR_CODEX — DETERMINISTIC_CANDIDATE_MAPPING_ONLY
**Execute:** `codex/comm/prompts/phase-5-018c-deterministic-qiwa-module-domain-mapping.md`

## EA instruction — Task 018C
Adopt `neo4j/csv/Qiwa_Modules_Services.csv` as the **AS-IS QIWA module/Parent→Child integration inventory single source of truth for this exercise**. Its actual distinct `Module_Name` values form the provisional QIWA-driven domain-bucket skeleton. Add the two EA-nominated candidate buckets **Occupations** and **TIP** (retain even with zero evidence). Do not automatically promote QIWA Modules or TIP exposure context to enterprise-ratified Business Domains; keep source module and candidate-domain fields separate.

Join **2,414 accepted canonical APIC HTTP operations** (and account for all **2,036 canonical APIs**) with CSV `API-HTTP` / `DP` components via canonical API/operation IDs, CodeGraph, configured invoke endpoint and catalog-property resolution. **Exact matching evidence is mandatory:** operationId/service name similarity produces a candidate, not a confirmed APIC→QIWA join. Preserve unresolved, ambiguous, contradictory and one-to-many matches; no arbitrary first-match selection. ACE entrypoint primary-module evidence is distinct from transitive cross-module supporting dependencies. For external-backed APIC operations, investigate DP correlation only when supported; never fabricate an ACE journey.

**Backend classification EA rule:** resolved configured invoke endpoint/host containing `ace` (case-insensitive) is `ACE_BACKEND`; known/resolved endpoint host without `ace` is `EXTERNAL_VIA_DATAPOWER`; truly unresolved host is `PLATFORM_UNRESOLVED`. Keep **full URL/path resolution independently**, including dynamic `$(request.path)`. This is configured APIC target interpretation, not proof of actual runtime egress or automatic APIC Wrapper linkage. Do not alter frozen canonical resolver.

**Mandatory deterministic CSV outputs:** full `operation_domain_distribution.csv` (2,414 rows including unmatched), `domain_distribution_summary.csv` (all CSV source modules plus Occupations/TIP), `ambiguous_operations.csv` (all unresolved/candidate/contradictory cases), and `apic_qiwa_match_evidence.csv` (row-per-join evidence). Keep 018B results as independent side-by-side baseline; do not overwrite or force its 11 domain labels to equal CSV modules.

**Success:** honest join coverage and explicit source-specific provenance, not maximum domain assignment rate. Preserve frozen Phases 0–4 and Tasks 014–018B, including 018B's historical 11-candidate comparison. Do not reuse 018A's rejected 21-label taxonomy. Run focused and repository tests, report baseline fixture failures independently, commit Task 018C outputs/evidence, update `codex/comm/HANSOFF.md` and **STOP for EA review**. No Task 019, domain ratification, API retirement, rationalization, productization or Kong TO-BE without further approval.

**Operating model:** Codex discovers → Integration Architect validates → Enterprise Architect decides.

## Completed checkpoint — Task 018B
Task 018B **TECHNICAL PASS** with 2,414/2,414 operations, 2,036/2,036 canonical APIs, 1,116 provisional primaries, 187 ambiguous, 988 insufficient semantics, 87 technical/test, 36 conflicting evidence, and 3,879 targeted schema-evidence records. Its 11 EA-supplied candidate domains (Visa, Establishment, Contracts, Nitaqat, Payment, Common, User Management, Work Permit, Work Force, Notification, Certificate) remain an **independent historical business-first baseline**, not an approved taxonomy. The user now authorizes the different CSV-first Task 018C assessment. Preserve all outputs and evidence.

## Historical checkpoint — Task 018A
Task 018A technically passed its bounded sample, but the 21 APIC-derived labels are **not accepted as proposed Enterprise Domain hypotheses**. Retain raw observations/provenance only.

