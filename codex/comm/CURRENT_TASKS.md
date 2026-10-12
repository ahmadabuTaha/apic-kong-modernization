# CURRENT TASKS

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## ACTIVE TASK
**Phase:** 5 — Semantic & Business Mapping
**Task:** 018B — Enterprise Business Domain Skeleton & Initial Operation Mapping
**Status:** AUTHORIZED_FOR_CODEX — CANDIDATE_MAPPING_ONLY
**Scope:** Initial full-ledger inventory mapping against the EA-supplied skeleton; targeted YAML evidence enrichment; bounded review and STOP. This is NOT enterprise-domain approval.

## EA decision after Task 018A
Task 018A achieved **technical PASS** (51 cases / 92 operations), but its **21 APIC-derived domain/subdomain/umbrella/technical labels are REJECTED as a basis for Enterprise Business Domain hypotheses**. Do not repurpose, relabel, or silently seed Task 018B with that taxonomy. Preserve Task 018A source observations, IDs, tests and evidence as historical inputs only; do not reopen frozen work.

The Enterprise Architect supplies the **authoritative INITIAL SKELETON of 11 candidates**, not a ratified enterprise taxonomy:
1. Visa
2. Establishment
3. Contracts
4. Nitaqat
5. Payment
6. Common
7. User Management
8. Work Permit
9. Work Force
10. Notification
11. Certificate

Use these exact skeleton labels as stable candidates for first-pass mapping. Do **not** add, rename, merge, split or promote labels in this task. In particular, retain Common, User Management and Notification as **candidate classification buckets**, with an explicit future question about business-domain vs shared/technical capability status. Certificate is an independent candidate and must not be silently absorbed into Visa, Work Permit or Establishment.

## Task 018B — Required approach
**Fundamental direction:** BUSINESS-FIRST skeleton -> APIC operation inventory -> targeted business-object/action evidence -> candidate assignment -> ambiguity and reconsideration backlog. Do not generate domains bottom-up from API/module/backend naming or graph clusters.

**Unit of classification:** each of the **2,414 accepted Task 014 HTTP operations** exactly once, retaining the parent canonical API and full source identity/provenance. Derive a separate rollup for all **2,036 canonical APIs** including zero-operation/unsupported cases; never make API-level footprint a substitute for operation-by-operation classification.

### Pass 1 — Initial candidate-domain inventory
- Reuse frozen Task 014/015/017/017A indexes and accepted semantic operation evidence, with no broad raw reread, all-pairs clustering, or dependency exploration.
- Map each operation to **zero or one provisional primary** from the 11 skeleton candidates when evidence supports it; retain multiple alternatives for cross-domain or ambiguous cases. Null primary plus a precise reason is a valid result, not an error. Explicitly mark technical/test/POC and insufficient semantics cases without inventing a twelfth domain.
- For each operation store canonical API ID, operation ID, HTTP method/path, source evidence pointers, proposed primary/alternatives, certainty and precise reason, documented action/object clues, contradicted alternatives, and review requirements.
- Do not treat exposure channel (LO/TIP/QAAS/KAYAN), QIWA Module, Product/Plan, ACE Parent/Child, invocation host, generic workflow verb or API name alone as ownership/domain proof. Do not equate a referenced object (e.g. establishmentId) with the primary business object being acted upon.

### Pass 2 — Targeted YAML / Business Object evidence
- For unresolved, conflicting and boundary-sensitive operations only, inspect relevant existing canonical/indexed schema evidence first and specific source YAML pointers only when necessary.
- Resolve request/response schema references and fields sufficiently to separate: CORE_BUSINESS_OBJECT_CANDIDATE, OBJECT_REFERENCE, DTO_OR_TRANSPORT_MODEL, LOOKUP_OR_VALUE_SET, TECHNICAL_ENVELOPE, BUSINESS_ACTION, and STATE_VALUE_CANDIDATE. These are evidence-role categories, **not** new domains.
- A YAML schema/definition is **not** automatically a business object; status enums are state candidates, **not** a proven state machine; HTTP method is not a business process; a shared schema is not a shared business owner.
- Preserve source pointer/definition path, exact field or operation evidence, alternatives, contradictory/copy-pasted descriptions, and what remains not evidenced. Do not fabricate processes, lifecycles, events or business ownership.
- The objective is better initial classification and an object candidate register, NOT reconstructing every ICD, object lifecycle or complete enterprise ontology.

### Pass 3 — Review and reclassification candidates (do NOT apply EA decisions)
- Provide domain-by-domain operation/API footprint counts (clearly differentiate primary, alternatives, unresolved, technical/test; no double-counting of primary).
- Produce candidate reassignment/ambiguity cases with original candidate, proposed alternative, object/action evidence, counterevidence, missing business proof and proposed verification source.
- Surface overlap and cross-domain dependencies without forcing one coherent API to belong to a single domain. Do not auto-create, split or merge any domain.
- Only consult ICD/Atlassian or Neo4j for a **specific evidence question** when accessible and strictly needed; missing access stays unresolved. Neo4j is implementation dependency evidence, not domain-boundary authority. Do not exhaustively crawl ICDs or reconstruct backend journeys for every operation.
- Preserve Task 017A's 71 reviews, five oversized adjuncts, 14 cross-API links and 90-item Productization Decision Backlog unchanged. Task 018A's rejected candidate taxonomy must not re-enter by indirect reuse.

## Expected evidence / review outputs
Commit compact, reproducible Task 018B evidence under a **new task-specific directory** such as `tests/evidence/task-018/domain-skeleton-018b/`; avoid overwriting Task 018A evidence. Keep expandable machine-readable ledgers under `indexes/` as permitted by repository conventions.
1. `skeleton_contract.md` — exact 11 EA-supplied candidates; provisional status and inclusion/exclusion decision questions, with no invented business definitions.
2. `operation_domain_initial_mapping.jsonl` — one entry per 2,414 operation (or documented evidence pointer plus complete deterministic export).
3. `canonical_api_domain_footprint.jsonl` — 2,036-API coverage, operation-level multi-domain footprint, and zero-operation/unsupported visibility.
4. `business_object_candidate_register.jsonl` — targeted YAML-derived objects/references/DTOs/actions/state candidates with pointers and evidence limitations.
5. `domain_review_reclassification_backlog.md` — bounded priority reviews, ambiguity/counterevidence and decisions for Enterprise Architect.
6. `coverage_quality_and_unresolved.md` — exact totals, primary/alternative/unmapped distribution, representative negative controls, absence of forced coverage, and tests/results.

If outputs would be too large to commit, preserve the full ledger deterministically in indexes and commit a compact manifest, summary, source pointers, rebuild instructions and review sample; do not silently drop operations.

## Acceptance criteria / STOP gate
- Exact **2,414/2,414 operation** preservation, **2,036/2,036 canonical API** accounting, stable IDs and provenance; no silent forced or whole-API classification.
- Exactly **11 skeleton candidate domains including Certificate**, with **zero new domains** invented.
- Reclassification candidates are recommendations only. No EA-approved Domain, ownership, Product/Plan, retirement, functional duplicate, runtime usage or Kong TO-BE decision.
- YAML Object/DTO/reference/enum distinctions evidenced and appropriately uncertain; no invented state transitions or processes.
- Frozen pipelines and old findings remain unchanged. Validate determinism and tests; document gaps separately from errors.
- Update `codex/comm/HANSOFF.md`, commit/push eligible Codex-generated evidence, and **STOP for EA review before domain changes, Task 019, rationalization, productization or Kong design**.

Operating model: **Codex discovers -> Integration Architect validates -> Enterprise Architect decides.**

## Historical task status
- **018A:** Technical PASS; APIC-derived 21-label taxonomy architecturally rejected as enterprise-domain input. Retain evidence, not domain proposals.
- **017A and Phases 0–4:** Preserve accepted checkpoints and approval gates as above.
