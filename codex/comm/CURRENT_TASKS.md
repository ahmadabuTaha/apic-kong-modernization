# CURRENT TASKS

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## ACTIVE TASK
**Phase:** 5 — Enterprise Business Domain Mapping
**Task:** 018D — Enterprise Business Domain: Independent Deterministic Mapping
**Status:** AUTHORIZED_FOR_CODEX — INDEPENDENT_SOURCE_DRIVEN_CANDIDATE_MAPPING
**Execution:** THIS FILE IS THE COMPLETE TASK AUTHORIZATION; DO NOT EXECUTE TASK 018C AS THE ACTIVE TASK.
**STOP gate:** EA_REVIEW_TASK018D

## 1. Objective and independence
Build a fresh, deterministic Enterprise Business Domain mapping from (1) the Enterprise Architect's Domain→Module/business-ownership definitions specified below, (2) original QIWA integration inventory `neo4j/csv/Qiwa_Modules_Services.csv`, (3) accepted Canonical APIC APIs/Operations and CodeGraph, (4) accepted Catalog Properties and APIC configured assembly/invocation evidence, and (5) targeted raw YAML only where needed for executable switch/condition/invoke semantics.

**Task 018D is NOT a continuation, repair, reconciliation or enhancement of the 018B/018C classification results.** Their generated distributions, joins, inferred domains and join tiers must NOT be inputs or determine the new outcomes. Preserve those checkpoints unchanged; any later historical comparison is optional and outside the 018D classification pipeline. Build an independent matching algorithm instead of importing or patching the 018C matcher.

Success = complete, evidence-traceable operation coverage and honest service/domain attribution, NOT forced classification coverage.

## 2. Source authorities and operating constraints
- EA-provided Domain–Module responsibility map in Section 3: authority for initial business classification; does not magically prove ambiguous system identities.
- `neo4j/csv/Qiwa_Modules_Services.csv`: architect-curated AS-IS QIWA Module, Parent Service, Child Service and component type inventory. Inspect actual columns, IDs, distinct literal Module_Name entries, duplicates and hashes. It is NOT proof of current production invocation or runtime behavior. CSV has no endpoint URLs; avoid deriving exact APIC→ACE joins from names alone.
- Task 014 canonical APIC API/operation indexes, CodeGraph, accepted backend/catalog property indexes: authority for configured APIC identity, route and invocation facts. Preserve existing source IDs and pointers; raw APIC YAML is final authority when targeted index evidence omits assembly structure.
- Neo4j MCP: optional, read-only, focused corroboration. Do not make full output depend on Neo4j if unavailable.
- Preserve frozen phases and Tasks 014–018C; do not change staging evidence or accepted parsers/resolvers, overwrite prior reports, crawl ICDs or build a broad knowledge graph. Use deterministic index-first discovery and focused raw YAML sections only.
- Preserve all **2,414 accepted HTTP operations** (one row each in operation inventory) and **2,036 canonical APIs** (including 41 zero-operation/unsupported); report any source mismatch explicitly rather than quietly changing baseline.
- Codex discovers → Integration Architect validates → Enterprise Architect decides.

## 3. Enterprise Architect's 13 classification areas — exactly as supplied
**D01 Establishment:** EFM, Establishment Logo, Establishment Location, Proactive Awareness.

**D02 Contracts:** Contract Management, Training Contracts, External Contracts. Explicit ownership anchor: `GetGosiContractsList` belongs to Contracts even when Work Permit or another module invokes it.

**D03 Visa:** all evidenced Visa modules, including Visit Visa, Seasonal Visa, Temporary Visa, Establishing Visa and Expansion Visa. These examples establish a family rule, not permission to synthesize module names; resolve actual CSV spellings and retain unresolved exceptions.

**D04 WorkForce:** Employee Transfer (ET), Employee List, End of Service Reward, Absence Management, Training Indicator, LMH Engine (scheduler), and evidenced Laborer/Worker services. WorkForce consumes and is affected by Contracts, Visa, Nitaqat, Establishment, Occupation and wages; cross-domain usage does not transfer service ownership.

**D05 Work Permit:** Work Permit lifecycle, late Work Permits, associated payments and debts, and related Work Permit services. Separate Work Permit business process ownership from reusable enterprise Payment capability consumption.

**D06 Payment:** Amazon Pay, HyperPay, SADAD and bill lifecycle, QIWA Wallet, Reconciliation, Dynamic Payment Gateway, Invoices, Billing and Compliance. Distinguish enterprise reusable Payment services from domain-specific payment business transactions.

**D07 Occupation:** Occupation Management and Change Occupation. Explicit ownership anchor: `SubmitOccupationCorrectionRequest` belongs to Occupation even when used by several modules. Preserve origin/service identity versus consumers.

**D08 Nitaqat:** all services and modules directly related to Nitaqat.

**D09 Certificate:** Salary Certificate, Saudization Certificate, Work Policy Certificate, Wage Protection Certificate. Certificate business ownership is independent from another domain merely reading or validating a certificate.

**D10 Common:** platform-centric shared components / utilities including lookups, PDF generators, appointment management, meeting APIs, and other evidenced shared platform functionality. **Five or more DISTINCT consuming QIWA Modules ⇒ COMMON_BY_REUSE_RULE** for the reused component; repeated calls or parent rows inside one module count only once. For two through four distinct modules retain origin classification with cross-module consumption flag; within one module retain origin module. Preserve original owner/domain separately even when Common reuse status is applied. Do NOT classify all consumer APIs as Common because they call a Common component. Explicit ownership conflicts require EA review, not automatic deletion of origin.

**D11 TIP — Takamol Integration Portal:** an enterprise service/exposure scope. AJEER, Musaned, Mowamah, Tabayyan, QIWA as a Service (QAAS) and Kayan are **FEW-SHOT EXAMPLES ONLY** illustrating TIP-related offerings, not an exhaustive whitelist and not guaranteed exposure assignments for all APIs bearing those names. Discover actual TIP exposure from APIC Catalog, Product/Plan, route, service configuration, source metadata and supported links. Separate `tip_exposure_status` and `business_domain`; allow both simultaneously. TIP is retained among the 13 requested classification areas for reporting, but do NOT overwrite business ownership merely because an API is TIP exposed. Do not assume TIP is the only channel.

**D12 User Management:** User Management and SSO.

**D13 Notification:** Email, SMS, Notification Orchestrator and Portal Notification.

Do not create a fourteenth Enterprise Business Domain. Normalize Work Force/WorkForce spelling for the EA label without overwriting literal source module names. Map all actual CSV modules or mark them explicitly `MODULE_MAPPING_UNRESOLVED`; do not default to Common. Explicit EA anchors override service consumption, but do not fabricate an APIC↔service linkage.

## 4. Mandatory Domain–Module crosswalk first
Read ALL literal `Module_Name` values from the CSV. Build `qiwa_module_domain_crosswalk.csv` preserving exact original spelling, normalized discovery key, candidate domain, evidence pointer, EA anchor/family rule, mapping status, alias/conflict and review reason.

Use statuses `EA_EXPLICIT_MODULE_MAPPING`, `EA_EXPLICIT_SERVICE_OWNERSHIP`, `EA_FAMILY_RULE_SUPPORTED`, `MODULE_ALIAS_SUPPORTED`, `MODULE_MAPPING_REVIEW_REQUIRED`, `MODULE_MAPPING_UNRESOLVED`. Where one source module is generic or mixes unrelated responsibilities, preserve ambiguity and use supported service-level ownership anchors instead of claiming the entire module has one approved owner.

Do NOT regard 018C's 30 module-derived domain labels as Enterprise Domains; the 13 EA areas above are the classification vocabulary, while CSV Module_Name is an AS-IS implementation dimension.

## 5. Independent canonical Operation → Assembly Branch → Invocation reconstruction
For every accepted canonical operation use accepted CodeGraph and backend evidence first. Identify the **effective** relevant assembly actions, including direct invoke, nested switch/case, conditional and default/fallback branches, referenced catalog properties, and distinguish operation-specific reachability from API-shared assembly context. Where indexes omit branch routing, inspect specific raw YAML assembly sections and track exact source pointers.

Build distinct records:
`Canonical API → HTTP Operation → reachable/configured Assembly Branch → Invoke action → Configured target → QIWA Parent/DP candidate`.

One APIC operation may have multiple invocation branches and destinations; preserve branch predicate/flag, parent action/switch pointers and guarded/unresolved reachability. Do not count each branch as a separate HTTP operation or conclude all conditions execute at runtime. If operation-to-branch reachability cannot be proven, mark it candidate rather than asserting it.

Use **per-branch backend classification** following EA's rule after catalog property host resolution:
- resolved configured host/endpoint contains `ace` (case-insensitive): `ACE_BACKEND`.
- resolved configured host/endpoint does not contain `ace`: `EXTERNAL_VIA_DATAPOWER`.
- missing/conflicting host evidence: `PLATFORM_UNRESOLVED`.
Keep host platform separate from `FULLY_RESOLVED`, `PARTIALLY_RESOLVED_DYNAMIC_PATH`, `UNRESOLVED`, and conflict status. Dynamic `$(request.path)` must NOT erase a known ACE host. The non-ACE rule describes the configured APIC/DataPower external target, NOT a proven QIWA DP-to-APIC wrapper or runtime egress.

Aggregate an operation-level backend *summary* only after individual invocation branches have been preserved; use a multi-platform status when branch platforms disagree instead of suppressing some branches.

## 6. Independent deterministic APIC ↔ QIWA matching (do not reuse Task018C conclusions)
Preserve APIC canonical/operation IDs, source pointer, branch/action pointer, backend observation and catalog scope, plus original QIWA row `ID`, `Module_Name`, `Parent_Service`, `Service_Name` and `Type`. Candidate discovery may use controlled normalization, but the normalized identity cannot substitute for original durable IDs.

**Forbid** confirming a join based on equality of an arbitrary normalized URL segment to a Parent/Service name, generic path tokens, shared hosts, copied descriptions, similar API/operation names, or a module-family name. Require an explicit durable cross-system identifier or exact operation-specific configured route with documented transformations and unique scoped/corroborated service identity. When route templates/dynamic variables prevent deterministic service selection, retain candidate status. Where the CSV has no route evidence, report that J1/J2-style confirmation cannot be derived from the CSV alone.

Join/evidence categories:
- `CONFIRMED_EXPLICIT_ROUTE` — durable ID or specific configured destination + grounded transform.
- `CONFIRMED_UNIQUE_SCOPED_ROUTE` — uniquely corroborated operation-specific target with scope/environment support.
- `CANDIDATE_NAME_MATCH`.
- `CANDIDATE_DYNAMIC_ROUTE`.
- `MULTI_BRANCH_CONFIRMED` — multiple independently evidenced conditional targets, NOT automatically ambiguity.
- `AMBIGUOUS_IDENTITY` — incompatible competing identities for same branch/target.
- `CONTRADICTORY_EVIDENCE`.
- `NO_MATCH_EVIDENCED`.

Distinct CSV row IDs or trailing whitespace alone do not establish distinct executing Parent Services; preserve source rows and original strings. Distinguish duplicate descriptions, reused services, different Parent identities and different invoking modules.

For ACE invocations, reconstruct evidence-backed entrypoint Parent and Parent→`API-HTTP` Child relationships with bounded child-as-parent recursion, cycles guarded. Include DP component edges; `API-HTTP` or `DP` child Type does not by itself prove APIC wrapper existence. Preserve non-API-HTTP component dependencies as supporting context when useful.

For non-ACE invocations, investigate QIWA DP correlation only when grounded; do not invent an ACE Parent. All joins preserve environment/source provenance, original CSV IDs, match tiers and match limitations.

## 7. Origin ownership vs consumption vs conditional orchestration
Maintain distinct `origin_module`, `origin_business_domain`, `consuming_modules`, `supporting_domains`, `shared_reuse_classification`, `tip_exposure_status`, and `operation_business_domain_candidate`.

Determine **service origin** from EA's explicit ownership anchors first; otherwise use evidenced QIWA service/parent identity and mapped original module if unambiguous. A service consumed from a different module stays within its origin domain. When source module is ambiguous and ownership cannot be established, leave origin candidate unresolved.

For a component, calculate number of **unique normalized consuming Modules** from actual source graph/CSV relationships; dedupe same module, repeated source rows, repeated Parent calls and formatting aliases. Retain original modules and source-row proof:
- 1 consuming module: `MODULE_LOCAL`.
- 2–4: `CROSS_MODULE_SHARED_ORIGIN_RETAINED`.
- 5+: `COMMON_BY_REUSE_RULE`, origin kept separately.
- unresolvable identity/consumers: `REUSE_REVIEW_REQUIRED`.

Apply five-module threshold to the **shared service/component**, not automatically the calling APIC Operation. Keep the original owner domain even where Common is an additional shared classification. A business operation orchestrating multiple domain-owned services should not be forced into one primary domain unless its own business responsibility is evidenced.

**Validation anchors (not permission to invent technical joins):**
- `SubmitOccupationCorrectionRequest`: origin Occupation; consumed in other modules; no multi-domain ownership purely from consumption.
- `GetGosiContractsList`: origin Contracts; Work Permit consuming it does not change ownership.
- `sendQIWAReport`: investigate exact switch/case and flag-driven multi-module invocations, report each branch separately; this may be conditional multi-module orchestration, NOT a multi-parent conflict.
- `UpdateEstablishmentContactAddress`: check establishment module aliases/ownership.
- `ValidateIssueEstablishingVisas`: distinguish whitespace duplicates vs truly distinct service identities.
- `SubmitWorkPermitRequest`: inspect evidenced ACE→API-HTTP→DP dependencies and ownership separately.

## 8. TIP few-shot discovery (NOT name whitelist)
Treat AJEER, Musaned, Mowamah, Tabayyan, QAAS and Kayan only as examples of TIP's varied offerings. Use them to identify reliable **actual configuration patterns** that show TIP exposure, then apply those proven criteria across APIC records without restricting to those names. Require explicit Catalog/Product/Plan/route/exposure references or corroborated TIP-specific metadata; labels alone do not prove TIP. Keep exposure and business ownership separate. Output status for each candidate: `TIP_EXPOSURE_CONFIRMED`, `TIP_EXPOSURE_CANDIDATE`, `TIP_EXPOSURE_NOT_EVIDENCED`, `TIP_EXPOSURE_CONTRADICTORY`. Preserve multi-channel cases and evidence pointers.

## 9. Mandatory NEW deterministic outputs (no prior Task 018B/018C input)
Write in `outputs/task018d/` with UTF-8 CSV, stable ordering, source IDs, counts and secret-safe evidence pointers:
1. `qiwa_module_domain_crosswalk.csv` — all QIWA modules and EA domain mapping evidence/uncertainty.
2. `operation_domain_distribution.csv` — EXACTLY 2,414 rows (one/operation), with API/operation IDs, method/path, environment, primary domain candidate, origin Module, invoked/supplementary domains, backend summary, invocation count, match & evidence status, Common reuse status, TIP exposure, unresolved and review reason.
3. `operation_invocation_branches.csv` — one per evidenced operation-specific branch/action with switch flag/condition, invoke source pointer, backend host category, target resolution, matched parent/candidate, origin domain, join tier and unresolved evidence. No raw secret-bearing target strings.
4. `apic_qiwa_match_evidence.csv` — row-per-join/source with route/branch evidence and CSV IDs, preserving candidate-vs-confirmed.
5. `domain_distribution_summary.csv` — 13 EA areas with *business-domain primary*, supporting counts, Common component counts, TIP exposure counts, distinct API counts, and separate unmapped/ambiguous totals; don't double-count primaries. Clarify TIP as exposure reporting dimension, not exclusive business owner.
6. `shared_component_reuse.csv` — identities, origin, distinct module consumers, direct/transitive usage and 1/2–4/5+ rule.
7. `tip_exposure_inventory.csv` — TIP exposure candidates and confirmed APIC operations, source/catalog/product context and independent Business Domain candidates.
8. `ambiguous_operations.csv` — **true** incompatible service/route/ownership ambiguity only; never all unmatched.
9. `unmatched_operations.csv` — every operation lacking adequate cross-system matching; include J3/name/dynamic candidates and reason.
10. `zero_operation_apis.csv` — all APIs not represented in the accepted 2,414 HTTP operation ledger, with source-reconciled total.
11. `manifest.json`, `reviewer_explanation.md` — input/output hashes, reproducible execution commands, total counts, unresolved cases, exact rule application, representative examples, test outcomes.

Preserve all prior historical artifacts without modification; do NOT emit an 018C→018D reconciliation as a required classification stage or use historical outcomes as labels. If committed CSVs are large, follow repo source/output conventions and commit reproducible artifacts with source hashes; do not omit the full requested CSV distribution.

## 10. Required validations, evidence and STOP
- Validate complete 2,414 unique HTTP Operations and 2,036 unique Canonical APIs; zero-operation/unsupported visibility.
- All original QIWA Module strings present in crosswalk; exactly 13 architect-defined top-level classification areas, TIP handled separately as exposure where appropriate; no new domains.
- Positive/negative fixtures for all named services above, 1/4/5 distinct consuming Modules, same-module repeated rows, cross-module ownership, explicit multi-invoke switch/conditional reachability, generic URL-segment false positives, route name collisions, dynamic `$(request.path)`, ACE vs external vs unresolved host, DP-wrapper non-inference.
- Preserve independently evidenced branches, distinguish true ambiguity vs no-match, don't assign business ownership from API name, dependencies, or TIP exposure.
- Deterministic generation, source and output hash checks, exact coverage, no credentials in outputs, focused regression + repository test outcomes, pre-existing fixture issues separately reported.
- Leave frozen accepted components unchanged. Update `codex/comm/HANSOFF.md` only as part of Codex execution handoff, commit/push new Task 018D implementation/evidence/output under approved conventions, and **STOP at `EA_REVIEW_TASK018D`**. No Task 019, Domain ratification, API retirement, Rationalization, Productization or Kong TO-BE without separate EA approval.

## Completed checkpoint — Task 018C (historical only)
Task 018C technically passed a 2,414-operation QIWA CSV mapping exercise with 450 provisional entrypoint assignments. Its classification, joins and matching algorithms are **NOT authoritative inputs** to Task 018D, and its previous "ambiguous" output mixed several unrelated review statuses. Preserve results for historical audit only.

## Completed checkpoint — Task 018B (historical only)
Task 018B technically passed a business-first 11-candidate mapping with 1,116 provisional primaries, 2,414 operations and 2,036 APIs accounted for. Its candidates do not drive Task 018D.

## Historical checkpoint — Task 018A
Task 018A technically passed, but its 21 APIC-derived labels are not accepted as proposed Enterprise Domain hypotheses. Retain raw evidence/provenance only.
