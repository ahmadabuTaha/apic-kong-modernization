# Phase 5 — Task 017A: 71 Logical API Proposals Architecture Review / Productization Continuity Gate

## Enterprise Architect instruction — 2026-10-11
**Execute a bounded, evidence-led review of ALL 71 Task 017 FULL Logical API proposals BEFORE Task 018 Business Domain Classification.** The architect explicitly chooses to investigate the proposals now to avoid carrying an unexamined formation gap into future API productization. This task is an additive architectural validation, **NOT** re-running Task 017 Full, and NOT authorizing the final product design.

Baseline: Phases 0–4, Tasks 014/015/016 frozen. Task 017 FULL is TECHNICALLY COMPLETE: 2,414 operations reconciled, 71 within-canonical-API proposals (5 SUFFICIENT_FOR_PROVISIONAL_BOUNDARY / 13 operations; 31 PARTIAL / 145; 35 INSUFFICIENT / 205); 5 capped oversized API groups involving 132 operations; 1,919 singletons/unformed; 46 prior comparison samples. Do not overwrite accepted evidence, indexes, HANSOFF historical result or source artifacts. No business group was architect-approved.

## Core question
For each of the 71, **is there a defensible conceptual Logical API boundary, should it be SPLIT, should it stay only a single AS-IS canonical API with no conceptual assertion, or is it UNDECIDABLE?** Investigate the actual operations, business objects/actions and resource paths rather than assume because operations coexist in one source API that they should form a Logical API. Categorize POC/test/technical utility status only when evidenced; never assume 71 are POCs.

**Distinct axes:**
1. Cohesion of genuinely related operations into a conceptual resource/workflow API;
2. Functional equivalence candidate across same/different APIs (not duplicates);
3. Exposure/productization suitability, which remains a decision candidate, NOT equivalent to a Logical API or a ready-to-package Kong Product.

Use Task 017 R1–R7 decision rubric **at group and membership level**; each SUPPORTED / CONTRADICTED / NOT_EVIDENCED with exact evidence pointer and concise reasoning. Clearly separate technical PASS from evidence sufficiency from EA architecture acceptance PENDING. Never label group architecture approved.

## Review every 71 proposal without full re-extraction
- Read `indexes/task017_full_logical_api_proposals.jsonl` (71) and `indexes/task017_full_operation_disposition.jsonl` for exact members, plus linked Task014/015/016 and existing Task 017 46-case examples, accepted relationship and backend/CodeGraph indexes.
- For EACH proposal, show: stable original ID, current canonical API name(s), exact member count, method/path per source operation (or compact expandable operation rows in ignored index), supported actions/objects with evidence strengths, grouping hypothesis, observed positive cohesion evidence, *specific* negative/counterevidence, contract/versions/security differences, backend evidence scope, accepted Product/Plan/Subscription context and any gaps, R1–R7 statuses and source pointers. Generic boilerplate 'may have different consumers' alone is NOT sufficient case-specific counterevidence.
- Produce a **specific formation recommendation** chosen from:
  * `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY` (resource/workflow cohesion positively evidenced, not architect-approved);
  * `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES` (concrete supported resource/action subdivisions, proposed sub-boundary member IDs and disjointness validation);
  * `KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION` (current API relation not enough to propose conceptual group);
  * `REQUIRES_TARGETED_EVIDENCE` (cite concrete blocking missing/contradictory evidence);
  * `TECHNICAL_OR_TEST_EXPOSURE_REVIEW` (ONLY when direct source evidence supports utility/POC/test status; do NOT claim retirement).
  Optional additional fields: competing alternative split/unified boundaries and reason. Only recommend SPLIT if evidence of specific sub-boundaries exists; do NOT fabricate labels or operations. Do NOT convert INSUFFICIENT into coherent by default.
- Every recommendation includes `productization_implication`: provisional reusable resource candidate vs separate exposure/policy/consumer boundary consideration vs structural/technical candidate vs deferred due to missing evidence; **NEVER** equate these to Kong/API Products or count of products.
- Preserve approved relationships as AS-IS exposure context only. Explain if one conceptual API spans divergent Products/Plans or one APIC Product contains distinct resource candidates; do not infer active subscriptions or unified owners. Do NOT push productization decisions to undefined 'later'; capture concrete open decision and next gate.

## Five oversized groups: adjunct to the 71, NOT inside their count
Review the FIVE source APIs capped due to size (132 operations total; names per accepted review evidence include osh, osh-apis, servicemanagement-supportcentre, user-management, user-management-privilege), using bounded **resource-path/action-specific subfamily indexing**, not the full all-pairs method and not indiscriminate root grouping. Recommend evidenced smaller candidate boundaries or explicit unformed reasons, preserve one primary original operation ledger disposition and explain whether viable or no adequate evidence. Do not silently relax cap nor merge with the 71 baseline. Keep this adjunct separately labeled and quantified. This is NOT a mandate to complete broad cross-API regrouping.

## Cross-API and productization continuity
- The existing 71 are entirely *within* one canonical API each. Identify **bounded directly relevant cross-API candidate LINKS** from Task 016 comparison/refinement and the 46-case Task 017 sample only for high-relevance source operations/groups (including SC Request approve/reject vs cancel). These are **links/alternatives**, NOT a new full cross-API logical grouping pass. Record both POSITIVE and CONTRARY evidence. NO transitive or name/schema-only inference.
- Produce a durable `productization_decision_backlog`: all 71 baseline IDs + five oversized adjunct reviews + any relevant bounded cross-API opportunities, with normalized decision status, evidence gaps, concrete next decision gate/required owner evidence. All 2,414 operations remain represented by immutable full Task 017 ledger; do not create fake 'products' for 1,919 singletons.
- Explicitly identify which unresolved decisions Task 018 Domain and Task 019 Capability may help (resource taxonomy / common business purpose), versus which they CANNOT prove (shared lifecycle owner, consumer intent, release boundary, active production usage, safe substitution). This distinction is mandatory.
- Mark a **Productization Readiness Gate** after Task 019 and before TO-BE API Product / Plan / Subscription / monetization design, reviewing 71 recommendations + oversized and cross-API candidate links. This is a *gate/decision register* only, NOT the design task.

## Outputs — human review FIRST, compact and reproducible
Commit compact artifacts under `tests/evidence/task-017/architecture-review-71/`:
1. `review_criteria_and_decisions.md` — recommendation definitions, R1–R7, independent validation axes, no inferred authority.
2. `all_71_decision_register.jsonl` — **71 exact baseline proposal IDs exactly once**, source operation/member references, evidence/counterevidence, recommendation, alternatives, Productization implication, gaps, bounded cross-API links, classification rationale/provenance, EA approval PENDING.
3. `executive_all_71_review.md` — **every one of 71** in human-readable tables with *meaningful* item-specific grouping/negative reason, source API names, operation summary, recommendation and Productization implication; not a generic list of ids/statuses.
4. `deep_dive_cases.md` — 12–18 purposefully diverse deep dives (all five initially sufficient if applicable, SC Request cross-API anchor, several partial, insufficient/technical/test, contract/product variant and at least one false-positive). Exact path/method/source pointers and alternative boundary.
5. `five_oversized_adjunct.jsonl` — precisely five, coverage of 132 operations, capped subfamily alternatives only when evidenced.
6. `cross_api_opportunity_links.jsonl` — small relevant bounded evidence-first candidate links, status and both positive/negative reasons; may be zero with explicit reason. No new primary cross-API memberships.
7. `productization_decision_backlog.jsonl` — all 71 + adjunct/links with decisions/open dependencies and scheduled **logical next gate** (after Task019, prior to design), not scheduled background tasks.
8. `coverage_and_decision_summary.json` — exact counts by previous and new recommendation, coverage of 71/71, member/references intact, oversized 5/132 separate, full 2,414 ledger unchanged, status reconciliation; no fabricated approvals.
9. `commands_and_results.txt`, `build_manifest.json`; bounded deterministic generator if needed.
Put complete detailed member expansions into ignored `indexes/` to avoid bloating committed outputs; executive table still must enable architect to recognize real APIs and actions.

## Tests and guardrails
- Exactly 71 distinct stable proposal IDs; no omissions, duplicates, silent changed membership, or altered original verdict/IDs/hashes; total operation coverage remains 2,414 and Task016 unpaired preserved.
- Specific case-by-case rationale, not a status relabel based solely on previous `SUFFICIENT/PARTIAL/INSUFFICIENT`; require source evidence for any recommended split/technical identity.
- Five oversized remain outside 71, exactly 132 source operations, no change of original primary dispositions. No transitive equivalence or broad all-pairs.
- R1–R7 status/evidence and contrary evidence; security/contract/versions/exposure retained; Product/Plan/Subscription no production call inference.
- Existing 46-case controls preserved, especially SC Request (2 source operations, 3 distinct action intents, PARTIAL alternative Unified Actions vs split Decision/Cancellation); negatives remain negatives absent stronger source.
- Separation: technical test PASS != evidence sufficiency != architect decision. **EA acceptance remains PENDING**.
- Provenance/redaction, deterministic rebuild, index-first reuse, no frozen source mutation, no production/retirement/Kong/Domain/Capability assignments.
- Run focused regression, relevant prior tests, repo tests. Report five pre-existing Phase 0 fixture errors separately, and any NEW test issue explicitly.

## Mandatory STOP
Update only `codex/comm/HANSOFF.md` on Codex execution (ChatGPT must not write HANSOFF), commit/push authorized changes and evidence. In HANSOFF report all-71 distribution, exact evidence-based examples, five oversized adjunct, productization backlog and decision gate, tests and any constraints. STOP for EA review. **Do not initiate Task 018, Task 019, productization solution design, Kong architecture or retirement.**
