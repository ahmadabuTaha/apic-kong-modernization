# CURRENT TASKS

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## ACTIVE TASK
**Phase:** 5 — Enterprise Business Domain Mapping
**Task:** 018E — Enterprise Business Domain: Top-Down Deterministic Mapping
**Status:** AUTHORIZED_FOR_CODEX — CANDIDATE_DOMAIN_ATTRIBUTION
**Execution:** Full instructions in THIS CURRENT_TASKS.md. No separate prompt is necessary.
**Gate:** STOP at `EA_REVIEW_TASK018E`.

## Why Task 018E exists / mandatory directional change
The EA asks for **Domain Skeleton → QIWA Modules CSV → QIWA Parent Services → Canonical API Artifacts → HTTP Operations**, then **independent backend/CodeGraph corroboration** and a reverse pass only for gaps. This is a DOMAIN-DRIVEN API INVENTORY, NOT API-DRIVEN DOMAIN DISCOVERY.

Task 018D was technically complete but produced only three operation primary candidates because its confirmation standard narrowly required exact switch message-root evidence for almost all joins. Task 018E must NOT replicate that gate. **An exact/controlled normalized operation/API-artifact-to-QIWA-Parent name match may establish a *provisional domain candidate* without a confirmed ACE invocation.** Name matching NEVER proves runtime calls or confirmed APIC→ACE linkage. Keep confidence dimensions separate.

Use the original QIWA CSV and accepted frozen canonical indexes. Do not use Tasks 018B/018C/018D candidate assignments, their matching algorithms, or their prior join tiers as classifier inputs. Preserve all prior outputs unchanged. No forced coverage or invented domains.

## 1. Authorities and scope
1. EA's 14 classification areas and explicit Domain–Module/ownership rules below are the initial **business classification authority**, not final enterprise governance approval.
2. `neo4j/csv/Qiwa_Modules_Services.csv` is the architect-curated AS-IS QIWA module/Parent→Child service inventory (known historical baseline: 4,437 source rows and 30 literal Modules; validate actual source/hash at runtime). Source IDs, Module_Name, Parent_Service, Service_Name, Service_Normalized and Type remain traceable; the CSV has no backend URL column.
3. Accepted Task 014 canonical API/HTTP Operation indexes (2,036 canonical APIs, 2,414 accepted HTTP Operations), canonical API **artifact/identity name**, operationId/name, method, path and source pointers are first-class inputs. Existing CodeGraph, Catalog Properties, backend indexes and targeted original APIC assembly YAML corroborate independently.
4. Neo4j is optional read-only corroboration; no mandatory graph-server traversal for routine matching; do not expand all dependencies merely to guess ownership.
5. All frozen components, IDs and staging source evidence remain immutable. No Task 019, Productization, Rationalization, retirement or Kong design.

## 2. Exactly 14 EA-defined AS-IS classification areas
- **D01 Establishment:** EFM; Establishment Logo; Establishment Location; Proactive Awareness.
- **D02 Contracts:** Contract Management; Training Contracts; External Contracts. Explicit origin ownership anchor: `GetGosiContractsList → Contracts` regardless of consumption by Work Permit/other modules.
- **D03 Visa:** all evidenced Visa Module family members: Visit Visa, Seasonal Visa, Temp/Temporary Visa, Establishing Visa, Expansion Visa, and other actual Visa modules evidenced in CSV. Do not fabricate aliases.
- **D04 WorkForce:** Employee Transfer (ET), Employee List, End of Service Reward, Absence Management, Training Indicator, **Decease Management (`Decease Mgmt`)**, LMH Engine/Scheduler, laborer/worker-related services. Contract/wage/Visa/Nitaqat/Establishment dependencies are *supporting/consumed* rather than ownership.
- **D05 Work Permit:** Work Permit lifecycle, related payments/debts, late Work Permits and related services; distinguish domain-specific business process from reusable Payment capability.
- **D06 Payment:** Amazon Pay, HyperPay, SADAD bill lifecycle, QIWA Wallet, Reconciliation, Dynamic Payment Gateway, Invoices, Billing, Compliance.
- **D07 Occupation:** Occupation Management, Change Occupation. Explicit ownership anchor: `SubmitOccupationCorrectionRequest → Occupation`, even where consumed in several modules.
- **D08 Nitaqat:** all evidenced Nitaqat modules and services.
- **D09 Certificate:** Salary, Saudization, Work Policy and Wage Protection Certificates. Distinguish certificate ownership from mere certificate reference/validation in another workflow.
- **D10 Common:** shared platform-centric components/utilities (lookups, PDF generation, appointments, meeting APIs, platform services). Apply **5+ distinct consuming QIWA Modules** threshold to a **service/component identity**, retaining its original owning module/domain separately. Same-module repeated calls count only once; 2–4 consuming modules retain origin plus sharing marker. Calling a Common component does NOT automatically turn the operation into Common.
- **D11 TIP — Takamol Integration Portal:** enterprise service exposure. **AJEER, Musaned, Mowamah, Tabayyan, QIWA-as-a-Service (QAAS), Kayan are FEW-SHOT EXAMPLES only**, not a whitelist and not sufficient alone for proof. Find real TIP catalog/product/plan/exposure evidence across estate; report TIP as a separate AS-IS exposure dimension alongside underlying functional domain where evidenced, with TIP included in 14-area reporting, not forced as exclusive owner.
- **D12 User Management:** User Management, SSO.
- **D13 Notification:** Email, SMS, Notification Orchestrator, Portal Notification.
- **D14 Labor Office Portal (LO):** LO/Labor Office Portal Module; an **AS-IS backend channel/scope that adds LO-specific business validations**. Retain LO as a distinct EA classification area for AS-IS, plus separate `backend_channel=LO`, `underlying_business_domain_candidate`, `lo_specific_validation_evidence`. Do not silently merge LO into WorkForce or infer LO from a generic substring.

No fifteenth domain. Exact source Module_Name values remain untouched, distinct from normalized EA labels. Unmapped source modules stay unresolved with exact reasons.

## 3. Mandatory TOP-DOWN passes (in THIS order)
**Pass A — Domain registry and complete Module crosswalk:** materialize all 14 EA areas, inspect every literal CSV Module_Name, deterministically connect explicit anchors and supported families/aliases; maintain mapping method `EA_EXPLICIT`, `EA_FAMILY_SUPPORTED`, `DOCUMENTED_ALIAS`, `REVIEW_REQUIRED`, `UNMAPPED`. Do not force a mixed/missing module to Common. Crosswalk can contain service-level override evidence separately.

**Pass B — Domain → Module → Parent Service inventory:** extract unique original parent identities per module, preserve source row IDs and children/types; dedupe formatting-only duplicates without deleting original evidence. Build fast reverse indexes by exact and normalized Parent_Service identity (multiple parents/modules preserved).

**Pass C — Match the Domain Parent Service registry against ALL Canonical API ARTIFACTS:** index original artifact names and normalized lookup keys. Attempt exact and controlled normalized artifact names and record all matches, collisions, source pointers, matched source modules and domain candidates. This pass occurs BEFORE operation fanout. Unmatched QIWA Parents and unmatched APIC Artifacts remain visible.

**Pass D — Match Operations:** for each canonical API artifact, join its accepted HTTP operations. Independently compare operationId/name against Parent Services so an operation can override an API-level candidate. Do not blindly propagate the API's candidate to all member operations of a multi-function API; record `INHERITED_ARTIFACT_CANDIDATE_REQUIRES_OPERATION_REVIEW` when only parent artifact matches. Use HTTP method/path solely as supporting/disambiguating evidence unless a documented route provides explicit matching. One row per 2,414 operation, even without a domain. Tie-breaking for exact vs normalized matches is deterministic but never arbitrarily chooses among genuinely distinct same-tier parent/domain candidates.

**Pass E — ownership and consumption:** resolve origin service/module separately from all calling/consuming modules. Explicit EA ownership anchors apply to the service identity but do not invent an APIC→service technical join. For a service referenced by multiple source rows, distinguish formatting aliases, origin and consumer modules. Preserve per-service 1 / 2–4 / >=5 distinct consuming module reuse classes. For 5+ mark Common reuse separately and keep origin; do NOT reassign all dependent operations to Common. Conditional multi-module invocations (e.g. `sendQIWAReports`) retain each branch and its potential origin domain without forcing one operation primary.

**Pass F — independent technical corroboration:** use accepted Catalog Property/CodeGraph backend observations and targeted assembly source as needed. Apply EA rule **resolved endpoint/host contains 'ace' (case-insensitive) → ACE_BACKEND; resolved host without 'ace' → EXTERNAL_VIA_DATAPOWER; unknown/conflicting → PLATFORM_UNRESOLVED**. Keep full target path resolution independent; `$(request.path)` does not erase a known ACE host. Separate `name_match_tier`, `candidate_domain_confidence`, `backend_platform_classification` and `technical_join_verification`. ACE host evidence alone does not prove specific Parent; name alone does not prove actual invoke. Operation-specific assembly switch/case, defaults, flags, nested invokes and multi-target evidence are represented by separate branch records where available, without claiming runtime execution or route egress.

**Pass G — reverse EXCEPTIONS ONLY:** reconcile all 2,414 operations and all 2,036 APIs, inspect previously unmatched/colliding APIs bottom-up using existing indexes, operation names and targeted YAML only as needed. This must NOT initiate a new domain discovery algorithm or reconstruct every backend journey. Report both `Domain→API coverage` (exposed domain parents) and `API→Domain coverage` (candidate-mapped canonical operations), with exact denominators.

## 4. Deterministic name-match contract
Candidate signals, in evidence-priority order:
- `N1_EXACT_OPERATION_NAME`: literal operation name equals QIWA Parent_Service.
- `N2_EXACT_ARTIFACT_NAME`: literal canonical API Artifact name equals Parent_Service.
- `N3_NORMALIZED_OPERATION_NAME`: controlled case/trim/whitespace/separator normalization.
- `N4_NORMALIZED_ARTIFACT_NAME`: controlled equivalent for Artifact.
- `N5_SUPPORTING_NAME_PATH_CANDIDATE`: documented aliases/service/path hints only; lower certainty, never automatic definitive ownership.
- `NO_NAME_MATCH`.

Index both sides once, return **all** deterministic same-key candidates. Keep raw strings and source IDs; don't conflate name collisions with technical route conflicts. Exact/normalized match with unique mapped origin can yield a `PROVISIONAL_DOMAIN_CANDIDATE` EVEN WITHOUT a confirmed invoke. Multiple modules *consuming* one original service are not multiple origin domains by default. Where ownership truly competes or operation is multi-functional, preserve alternatives/null primary and `EA_REVIEW_REQUIRED`.

Separate technical states: `NAME_MATCHED`, `BACKEND_CORROBORATED`, `ROUTE_CONFIRMED`, `BACKEND_NOT_VERIFIED`, `BACKEND_CONTRADICTORY`. Route confirmation requires route evidence; never upgrade based on text normalization alone.

Negative controls: common/generic names (`get`, `submit`, `service`), copied descriptions, shared path segments and same-normalized-key different source identities must not cause forced primary. No name-only assumption about actual production use.

## 5. TIP and LO as explicit parallel dimensions
- TIP examples are few-shot clues to investigate **real** APIC Product/Plan/catalog/exposure membership. Report `TIP_EXPOSURE_CONFIRMED` only where configuration relationship supports it; `TIP_EXPOSURE_CANDIDATE` for weaker hints; `TIP_EXPOSURE_NOT_EVIDENCED` otherwise, preserving source pointers and other channels.
- LO is distinct AS-IS backend/channel with additional business validations, not just a synonym for a functional domain. Report `LO_AS_IS_CONFIRMED` vs candidate/not evidenced, original LO Module or supported API configuration, underlying functional domain if independently grounded, and presence/absence of LO-specific validation evidence. Keep LO in 14-area reporting without incorrectly double-counting exclusive functional owners.

## 6. CACHING / low-token operating contract (MANDATORY)
**Index once, query many.** Before opening raw source, consult existing frozen indexes and incremental caches. Cache is an implementation optimization, NOT new evidence or an alternative source of truth.

Build small deterministic stage-specific caches under `indexes/task018e_cache/` (or repository-approved equivalent), e.g.:
1. `source_fingerprints.json` — SHA-256/source version of QIWA CSV, canonical API/operation indexes, CodeGraph/backend property indexes, EA mapping spec/schema/rule version, cache schema version, build tool version.
2. `domain_module_crosswalk.jsonl` and `parent_identity_lookup.jsonl` — sorted domain/module/parent IDs, exact and normalized keys, original CSV row refs.
3. `canonical_artifact_lookup.jsonl` and `operation_name_lookup.jsonl` — indexed names/IDs/source pointers, without full YAML body.
4. `artifact_parent_matches.jsonl`, `operation_parent_matches.jsonl` — deduped deterministic candidate edges, match tier, conflicts, ownership/consumption evidence refs.
5. `backend_verification_lookup.jsonl` — derived safe host/platform/target resolution/CodeGraph pointer results, only if needed; no secrets.
6. `assembly_branch_cache.jsonl` — **targeted** extracted branch selectors/invoke references keyed by source hash + operation/assembly identity; parse only files selected by unresolved cases or conditional evidence.

Use a stable cache key including **input content hashes + relevant EA rule version + normalization/matcher version + cache schema**. If a dependency changes, invalidate only affected stages and descendants: e.g. Domain skeleton change rebuilds crosswalk/ownership/distribution but does not reparse APIC YAML; source CSV change rebuilds CSV-dependent identity matches; one YAML change reparses just that file's branch cache. Never reuse stale caches because a path or timestamp stayed the same. Validate entry row counts, IDs, schema and provenance on cache read; corrupt/incomplete cache → deterministic regeneration.

**Token efficiency:** per-question retrieval `Domain → Module → compact Parent index → matching Artifact IDs → matched Operation IDs → evidence pointers → raw YAML only for specific dispute`. No printing thousands of records to Codex context. Use Python/CLI streaming deterministic joins, hashes, manifest/count summaries and bounded review samples; on-screen/task handoff show top-level totals + top unresolved reasons + selected positive/negative controls, not full CSV dumps. Avoid per-row LLM classification, broad Neo4j queries and all-pairs comparisons. Ensure cached artifacts include *pointers*, not copied full source blobs, and no sensitive credential/URL values.

Measure/cache-report: `cache_hit_count`, `cache_miss_count`, `stages_rebuilt`, `targeted_yaml_files_read`, `source_files_hashed`, `full_raw_yaml_rereads_avoided`, elapsed duration if available and precise notes on rebuild/invalidation. Cold and warm runs must produce byte-identical final CSVs and equivalent manifests apart from explicitly volatile run telemetry (which must not enter hashed deterministic outputs). Tests must exercise cache hit, changed CSV, changed EA mapping, and single-file YAML invalidation. Cache must not introduce false evidence or change classification results.

## 7. Required FULL deliverables under `outputs/task018e/`
1. `enterprise_domain_registry.csv` — 14 EA classification areas, description/role incl TIP exposure and LO AS-IS dimensions.
2. `domain_module_crosswalk.csv` — all literal source QIWA modules and mapping evidence.
3. `domain_parent_services.csv` — domain→module→parent service inventory with original CSV IDs/children and unresolved parent/domain.
4. `domain_canonical_apis.csv` — per evidenced domain/parent↔API artifact candidate, match tier, multiple domains/collisions; include APIC artifacts with no match in separate coverage accounting.
5. `domain_operation_distribution.csv` — domain→matched API→operation coverage including supporting/secondary candidates without double counting accepted operations in exclusive totals.
6. `operation_domain_ledger.csv` — **exactly 2,414 distinct accepted HTTP operations**, candidate primary/alternatives, method/path, parent matches and tier, inferred-from-artifact vs operation match, origin/consumer modules, TIP/LO/Common independent classifications, backend verification, source refs, unresolved/review flags.
7. `shared_services.csv` — distinct consuming QIWA module counts, source rows, origin ownership and Common thresholds.
8. `backend_verification.csv` — configured ACE/external/unresolved host and target evidence, technical join status separate from candidate domain.
9. `operation_invocation_branches.csv` — where evidenced, one row/conditional or direct invoke branch without collapsing operation inventory.
10. `tip_exposure_inventory.csv` — TIP evidence and few-shot discovery coverage, confirmed/candidate/not evidenced as appropriate.
11. `lo_as_is_inventory.csv` — LO scope and LO-specific validations evidence, underlying domains separately.
12. `domain_mapping_exceptions.csv` — collisions, multiple origin domains, ownership gaps, routing contradictions and unresolved mapping reasons separated.
13. `unmatched_operations.csv` — non-domain-mapped cases, precise reasons (no parent name, unresolved module, mixed API, etc.).
14. `zero_operation_apis.csv` — all 41 baseline zero/unsupported-operation canonical APIs, reconciled from source.
15. `coverage_report.md`, `manifest.json` — BOTH coverage directions, stage/cache metrics, input/output hashes, controls, exact denominators, reproducible rebuild and cold/warm consistency results.

Commit a compact source/rebuild manifest for caches if full caches would be oversized; preserve deterministic rebuild tooling. Do not silently drop final CSVs. No secret-bearing endpoint or Catalog Property values in deliverables.

## 8. Required focused examples and acceptance tests
Use exact source pointers (never fabricate APIC→ACE joins) for:
- `SubmitOccupationCorrectionRequest` → Occupation origin, multi-module consumer references distinct.
- `GetGosiContractsList` → Contracts origin, Work Permit may consume.
- `SubmitWorkPermitRequest` → Work Permit candidate name matching, ACE verification independent.
- `sendQIWAReports` → conditional switch/case, multi-domain branches not false ambiguity.
- `UpdateEstablishmentContactAddress` → Establishment alias/name matching.
- `ValidateIssueEstablishingVisas` → Visa, dedupe formatting-only duplicate rows.
- `Decease Mgmt` → WorkForce newly EA-defined mapping.
- `LO` → LO AS-IS scope plus underlying domain independent.
- TIP few-shot and additional discovered offerings.
- Common 1, 4, 5 distinct consumer module tests; same-module repeated calls not counted twice.
- Generic-name false positives and same-key collisions; exact name vs artifact/inherited multi-op behavior.

**Acceptance:** retain 2,414 operation identity/coverage, 2,036 API identity/coverage, all source module labels and 14 areas; real top-down mapping and separate bottom-up exception audit; per-operation candidate eligibility not gated by technical invoke confirmation; ownership/consumption distinct; TIP/LO independent; full CSVs deterministic; cold/warm cache equality, incremental invalidation, cache statistics, no secrets, no forced/undocumented joins; document precise unresolved evidence.

Run focused and available repository regression tests; report pre-existing frozen fixture/sandbox issues separately. Commit/push new Task 018E implementation, outputs and evidence, update `codex/comm/HANSOFF.md`, and **STOP at `EA_REVIEW_TASK018E`**. Do not ratify Domains, begin Task 019, Rationalization, Productization, retirement, or Kong TO-BE without EA approval.

## Historical checkpoints (preserve, not inputs)
- **018D:** Technical PASS; independent but overly restrictive route-confirmed candidate assignment (3 primary operations); valuable branch/reuse/TIP observations remain historical only.
- **018C:** Technical PASS; earlier module-based attribution and broad review file not authoritative input.
- **018B:** Technical PASS; business-first 11-candidate experiment, not current source of domain labels.
- **018A:** Technical PASS; rejected 21-label APIC-derived domain taxonomy; do not resurrect.
