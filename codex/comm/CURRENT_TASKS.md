# CURRENT TASKS

## ACTIVE TASK — Phase 6 / Task 019-E-FINAL
**Title:** All Modules — Main Business Capability → ICD, then unpaired ISD
**Status:** AUTHORIZED_FOR_CODEX — MODULE-BY-MODULE, COMPACT CHECKPOINTS
**Sole execution prompt:** `codex/comm/prompt/phase6-task019e-final-main-capabilities.md`; follow ONLY this authorization. R1/R2/R3 remain historical pilots, not executable work.
**Input:** Recovery effective catalog and cached ICD/ISD bodies. Reuse existing R2/R3 code; never refetch or mutate cache.
**Per-Module order:** FIRST all active ICDs → Main Capabilities and direct ICD links; LAST inspect ISDs without evidenced ICD relationships individually using Service name, Introduction/Summary and meaningful Schema semantics → existing/new Main capabilities. No Business Functions/Sub Capabilities and no Canonical API matching yet.
**EA decisions:** Contract lifecycles separate; Admission Journey in Compliance; externally-created contracts mapped by contract lifecycle; named GOSI/NIC/HRSD integration yields evidence-backed Integration Capability; OLD/NOT USED/IGNORE source designations excluded from active mapping but audited; Main names meaningful and no slash-joined labels; Logo/Notification allowed.
**Coverage:** all 32 Modules reconciled one at a time, eligible/excluded/unresolved listed by exact source ID. Explicit gaps now, not discovered late. Incremental checkpoints; focused checks only. No full regression suite, re-acquisition, old-stage replay, unrelated infrastructure.
**STOP:** `EA_REVIEW_019E_FINAL`. No API matching/consolidation/Kong or other downstream tasks without EA approval.

## PREVIOUS TASK — Phase 6 / Task 019-E-R3 (CONTRACTS CANDIDATE MAPPING COMPLETE; EA DIRECTIVES NOW CAPTURED)
**Evidence:** latest `codex/comm/HANSOFF.md`, implementation commit `bc80ef5`. Contracts 169 ICDs linked to 10 Main candidates with 7 mapped ambiguities and 12 ISD-only/no-ICD services; interpret those with the EA resolutions and exclusion rule in 019-E-FINAL. Prior outputs remain untouched.

## PREVIOUS TASK — Phase 6 / Task 019-E-R2 (ESTABLISHMENT CANDIDATE MAPPING COMPLETE; NOT AUTOMATICALLY APPROVED)
**Evidence:** `codex/comm/HANSOFF.md`, commit `47d934a`. 149 ICDs mapped, 11 Main candidates and review exceptions. Re-evaluate under final naming/integration and ISD rules, preserve historical outputs.

## Accepted checkpoints and constraints
- Phases 0–4 PASS/FROZEN; Task 014 2,036 canonical APIs and 2,414 accepted HTTP operations.
- Task 015 accepted/frozen provisionally for observed-function signals; Task 016 accepted/frozen for 1,170 candidate comparisons / 1,481 unpaired operations, never approved duplicates.
- Task 017 mock + 46-case expanded validation preserved. Task 017 FULL technically complete: full operation ledger, 71 within-canonical-API logical boundary proposals; no cross-API primary logical membership.
- Task 017A **TECHNICALLY COMPLETE; EA ACCEPTED AS PROVISIONAL ASSESSMENT INPUT TO NEXT PHASE, NOT AS APPROVAL OF ANY BUSINESS BOUNDARY.** All 71 reviewed: 5 retain provisional, 15 split-candidate, 23 keep AS-IS exposure, 9 require evidence, 19 technical/test exposure review; plus five oversized reviews/132 ops, 14 bounded cross-API links, 90-item Productization Decision Backlog. All individual architecture approvals remain PENDING. Full operation coverage 2,414/2,414 intact.
- Source is STAGING/sandbox, not proof of production activity, release lineage, consumer/owner intent, actual runtime egress, or retirement. Preserve frozen evidence, source provenance and original IDs.

## PREVIOUS TASK (Task 018F; technical PASS, EA review checkpoint)
**Phase:** 5 — Enterprise Business Domain Mapping
**Task:** 018F — Enterprise Business Domain: Deterministic Artifact-First, Multi-Evidence Attribution
**Status:** AUTHORIZED_FOR_CODEX — EVIDENCE_DRIVEN_CANDIDATE_MAPPING
**Instructions:** This CURRENT_TASKS.md is the complete Task 018F authorization. Execute ONLY Task 018F; no separate prompt required.
**STOP gate:** `EA_REVIEW_TASK018F`.

## 0. Architectural correction / non-negotiable intent
**Canonical API ARTIFACT is the principal AS-IS classification unit.** Its name is often the clearest expression of what the API provides, even when it has no accepted HTTP operation or has one/many operations. Build all 2,036 Canonical API artifact records FIRST, then link all 2,414 accepted HTTP operations and the 41 zero-operation/unsupported artifacts. The API artifact, its operation name/ID, URI, request and response YAML schemas, QIWA domain/module service context, product/channel and backend evidence are **COMPLEMENTARY**, not a serial chain of mandatory prerequisites.

Task 018E's `Parent_Service match → domain` requirement demonstrably missed meaningful API artifacts such as `user-management` and `getpaymentdetails-v2`. **A QIWA Parent match is not required for a candidate Domain**. Conversely, an exact name or schema reference is not sufficient proof of runtime invocation or an approved business boundary.

The Enterprise Architect explicitly declares **TIP (Takamol Integration Portal)** and **Labor Office Portal (LO)** to be **real, independent AS-IS Domain classifications**, not only side-channel flags. Keep them in the same domain register/primary assignment candidate space as Visa/Contracts/etc. ALSO retain orthogonal exposure/channel and underlying-functional-domain attributes. A TIP/Tabayyan/QAAS API can have `primary_as_is_domain_candidate=TIP` and `underlying_functional_domain_candidate=Contracts`; this is NOT a contradiction, and a reference to Contract in an operation or schema must not automatically displace TIP ownership. For LO similarly `primary_as_is_domain_candidate=LO` and a separate underlying domain where evidenced. Do not default to functional-domain-over-channel precedence.

**New EA-defined fifteenth Domain: Utilities.** Technical integration helpers, token acquisition, validators and named enterprise utility offerings belong here when the API function evidences it. Keep **Common** separate: Common is the originally defined shared enterprise/platform component domain and 5+ distinct QIWA consuming-module reuse rule; Utilities is a named functional portfolio/domain for utility, support, tooling and technical integration offerings. Do NOT classify every technically implemented API as Utilities or Common.

**POC / Test / Mock / Sample** are separate `api_lifecycle_purpose` / `non_business_exposure_class` dispositions, **NOT a sixteenth business domain**. Their primary domain may remain null, or have a provisional functional domain separately with POC/Test status; no automatic retirement decision.

The goal is an EA-reviewable API-centric domain inventory, not maximum forced coverage and not another 018B/018C/018D/018E replay.

## 1. Accepted source authority / frozen constraints
- Use frozen canonical API/operation IDs/indexes (2,036 APIs / 2,414 accepted HTTP Operations; 41 zero-operation APIs), canonical Artifact names/identities, methods, operationId/name and URI path. Preserve exact identity and source provenance.
- Use original APIC staging API YAML as **authoritative AS-IS source when targeted**: API/OpenAPI info, tags, paths, operationId, description, request body, response codes and schema/$ref definitions, properties, references and assembly; accepted extracted schema indexes (including Task 018B schema clues only if these are factual extracted source evidence, **not its classification labels**) preferred before raw reads. Frozen staging and parsers remain unchanged.
- Use original `neo4j/csv/Qiwa_Modules_Services.csv` (baseline 4,437 rows / 30 literal Modules) and EA Domain→Module skeleton. QIWA Parent is a strong supporting association, not a prerequisite. Preserve original module spellings, source IDs and distinction between owning module and consuming modules; original CSV has no URL/endpoint column.
- Use accepted CodeGraph, catalog properties, APIC Product/Plan/Subscription/catalog membership, identity and backend indexes as available. Never assert a runtime call merely from configuration, name, or host. Neo4j optional read-only, targeted only.
- Task 018E implementation/cache patterns and factual extraction indexes may be reused **as optimizations**, but no Task 018B–018E classified domain assignments, primary candidates or match scores as authoritative input labels. Re-evaluate from original evidence with the updated EA rules; preserve historical outputs byte-unchanged.
- No unbounded source scans or all-pairs matching. No secrets, resolved credential values or sensitive endpoint URLs in deliverables.

## 2. Domain register — EXACTLY 15 EA-defined AS-IS Domain areas
1. **Establishment** — EFM, Establishment Logo, Establishment Location, Proactive Awareness.
2. **Contracts** — Contract Management, Training Contracts, External Contracts; explicit `GetGosiContractsList` ownership anchor Contracts despite other consumers.
3. **Visa** — all evidenced Visa Modules including Visit, Seasonal, Temporary, Establishing and Expansion Visas.
4. **WorkForce** — Employee Transfer/ET, Employee List, End of Service Reward, Absence Management, Training Indicator, Decease Management / `Decease Mgmt`, LMH Engine scheduler, laborer/worker services; cross-domain consumption does not transfer ownership.
5. **Work Permit** — all Work Permit lifecycle, Work Permit payments/debts, Late Work Permit.
6. **Payment** — Amazon Pay, HyperPay (including credible `Hypp` naming), SADAD and bill lifecycle, QIWA Wallet, Reconciliation, Dynamic Payment Gateway, Invoices/Billing/Compliance.
7. **Occupation** — Occupation Management, Change Occupation; `SubmitOccupationCorrectionRequest` origin Occupation despite cross-module consumption.
8. **Nitaqat** — all Nitaqat services.
9. **Certificate** — Salary, Saudization, Work Policy, Wage Protection Certificates; distinguish a certificate business object from a dependency on certificates.
10. **Common** — shared enterprise/platform services/components (lookups, PDF generators, appointments, meeting APIs) and source-grounded service/component reuse at >=5 **distinct QIWA Modules**, with origin ownership retained. Do not turn all consumers into Common, or reclassify a dedicated named utility automatically merely because it is technical.
11. **TIP / Takamol Integration Portal** — **real first-class AS-IS Domain**, all grounded enterprise services exposed/owned in TIP, such as AJEER, Musaned, Mowamah, Tabayyan, QAAS/QIWA-as-a-Service, Kayan; these are **illustrative few-shot identifiers, never an exhaustive whitelist**. A TIP API may serve an underlying Contracts/Visa/other business object; assign/report both identities on separate dimensions.
12. **User Management** — User Management, SSO, grounded identity/user/privilege operations; distinguish user-account/authorization business functions from bare integration token generators.
13. **Notification** — Email, SMS, Notification Orchestrator, Portal Notification.
14. **LO / Labor Office Portal** — **real first-class AS-IS Domain** and actual backend channel with distinct LO-specific Business Validations; retain underlying functional business domain separately where evidenced. Do not erase LO by reassigning to other functional domains or infer from arbitrary substring.
15. **Utilities** — QKS, QueryCenter (`qc_` prefixed offerings subject to contextual validation), ADAA survey, Support Center, QIWA Policies, ServiceNow, Zendesk, Webex, S3 clients, token generation/acquisition and validators. These are EA-provided **named anchors/examples** for a Utilities domain; classify only grounded relevant functions; avoid name-only overgeneralization when `qc_` or generic `token` collides with another purpose. `gosi_getAccessToken` is an explicit Utilities/External-Integration-Authentication example, not GOSI/WorkForce/Contracts by external-system name. Preserve external-system tag independently.

No additional domain labels. Every exact literal original QIWA Module preserved; source modules with inadequate EA mapping remain explicitly review-required. TIP/LO are independent AS-IS domains even if their technical channel fields are also set.

## 3. Distinct classification dimensions (must not conflate)
Every **Canonical API artifact** and, where evidenced, each HTTP Operation has:
- `primary_as_is_domain_candidate`: one of 15 or null, **including TIP/LO as legal primary candidates**.
- `underlying_functional_domain_candidate`: one of the 15 or null when a TIP/LO/Utilities/Common artifact provides or refers to another functional business capability; never forced.
- `supporting_domain_candidates` and `consumed_service_domains`, separately from owner.
- `domain_evidence_tier` + `candidate_confidence` + `contradictory_evidence` + `review_status`.
- `qiwa_module_owner`, `qiwa_parent_candidate`, `qiwa_consuming_modules` and explicit relationship certainty (including NO_MATCH).
- `channel_exposure` (TIP/LO/etc.) and `backend_channel`, independently from the actual *Domain*. A Product or channel label alone is not always sufficient for ownership when shared cross-channel.
- `api_lifecycle_purpose`: BUSINESS, UTILITY, POC, TEST, MOCK, SAMPLE, INTERNAL_TECHNICAL, REVIEW_REQUIRED; these are dispositions and can coexist with domain classification. A test-named API must be checked for contradictory production-looking evidence, not blindly marked removable.
- `backend_platform_classification`, `configured_join_certainty` and `runtime_use_proven=false` unless actual runtime evidence exists (none assumed).
- Source pointers to **artifact, operation, schema request/response, path, parent/module and Product/Plan** evidence where present.

Do not propagate a primary domain from an artifact blindly to heterogeneous operations; conversely don't replace clear artifact-level domain evidence with a weaker operation-token hint.

## 4. Mandatory deterministic ARTIFACT-FIRST processing order
### Pass A — EA registry and semantic-anchor indexes
Create deterministic compact indexes for all 15 domains and EA supplied anchor names/synonyms/abbreviations (incl TIP, LO, Utilities). Anchors are case/format normalized and context-scoped, not uncontrolled substring keywords. Maintain an explicit distinction: EA_EXPLICIT_BUSINESS_ANCHOR; DOCUMENTED_ALIAS; FAMILY_RULE; GENERIC_HINT; CONTRADICTORY/INSUFFICIENT. Audit ambiguous prefixes (e.g. `qc_`, `lo`, generic `token`), acronym collisions, and overlaps (e.g. Contracts object inside TIP API).

### Pass B — Full canonical API ARTIFACT registry (before operation attribution)
Create **exactly 2,036** per-artifact records including 41 with zero operations: canonical name/ID, document path, version/source, non-secret description/tags, Product/Plan/channel exposure where indexed, operation count, accepted schema pointers, any config backend classification. 
**Classify artifact-level domain candidates using name/identity as PRIMARY SEMANTIC EVIDENCE**, supplemented by explicit EA anchors, channel/product evidence, QIWA module/service names, descriptions/tags, URI family and schema object clues. Do not demand QIWA Parent alignment. Mark POC/Test/Mock/Sample purpose independently. Preserve multiple plausible domains/contradictions without arbitrary assignment.

### Pass C — Original QIWA Domain→Module→Parent registry, supporting NOT gating
Produce complete 30-literal-Module crosswalk using EA skeleton, including WorkForce/Decease Mgmt and LO; build 993-ish source-derived module-scoped Parent identities (actual counts determined from source), source IDs and reusable identity name lookup. Build direct exact/controlled normalized artifact↔Parent and operation↔Parent candidates; distinguish owner vs consumers, standalone QIWA Parents without API exposure, and APIC artifacts outside QIWA CSV. Never label absence of a QIWA name match `NO_DOMAIN_EVIDENCE` when artifact/function/schema evidence exists.

### Pass D — Operation, URI, request AND response schema evidence
For **all 2,414** accepted HTTP Operations, preserve parent API's domain attribution and inspect available operation names/IDs/method/path. Extract and attach targeted **request and response schema semantic evidence**: named Business Objects, resource identifiers, lifecycle actions, status/state fields where genuinely evidenced, schema references and original YAML pointers. Request/response direction must be explicit; do not treat DTO wrappers, generic transport envelopes, shared schemas or referenced object names as automatic ownership. Operation name can say `contract` while artifact Product/identity says `TIP/Tabayyan/QAAS`: retain **primary AS-IS TIP candidate** when evidenced, `underlying_functional_domain=Contracts` where object supports it. If operation name absent, use API artifact context plus path/schema evidence and mark inherited vs operation-specific certainty.
Prefer accepted extracted schema indexes; parse raw YAML **only for API/operation ambiguity or absent indexed semantics** with bounded per-file retrieval, never dump raw all-file bodies into prompt context. Avoid artificial API-level fanout that pretends every operation is identical.

### Pass E — Domain decision matrix (deterministic, auditable, NOT simplistic fixed weights)
Use evidence-specific decision rules, and emit rationale + contrary evidence:
A. EA-explicit artifact/module/offering ownership or well-supported named API purpose is eligible for `PROVISIONAL_PRIMARY_AS_IS_DOMAIN` even if no QIWA Parent exists.
B. TIP/LO as true AS-IS domains when supported by **direct API/product/module/service ownership context**, not merely a casual token in descriptions; retain underlying functional object/domain independently. Multi-channel exposure must not automatically mean exclusive ownership.
C. Utilities: named EA anchor plus actual technical/service function; `gosi_getAccessToken → Utilities` provisionally. `user-management` and `user-management-privilege` → User Management provisionally based on canonical API identity, even when operation IDs are absent and paths templated.
D. `getpaymentdetails-v2` / `GetPaymentDetails` / `/getpaymentdetailsHypp` → Payment provisional (HyperPay/Hypp signal); verify using schema/description if available; **no QIWA Parent necessary**.
E. If artifact suggests TIP but operation contains Contract, do not automatically move operation primary to Contracts; maintain explicit multi-dimensional classification and check product/config/source for TIP grounding.
F. Certificate/Establishment naming conflict, Work Permit-specific payments vs generic Payment, GOSI integration identity vs functional service ownership, Common vs Utilities, and LO underlying business function must be modeled as evidence-specific conflict cases.
G. Where evidence genuinely conflicts or is insufficient, preserve alternatives/null primary and precise reason. No all-or-nothing backend route gate.
H. Do not confuse an Operation's target technology, channel, consumer, organization, external system, token acquisition or schema dependency with functional ownership.

### Pass F — Independent CodeGraph/backend/conditional assembly corroboration
Reuse frozen CodeGraph/Catalog Property/backend observations, classify each branch: resolved ACE host → ACE_BACKEND, resolved non-ACE → EXTERNAL_VIA_DATAPOWER, missing/conflicting → PLATFORM_UNRESOLVED. `$(request.path)` dynamic path does not erase identified ACE host. Keep `technical_join` independent of `domain_candidate`. For multi-branch `sendQIWAReports`, preserve its 63 configured switch branches/flags and supporting domain candidates with no forced single primary. Configured evidence is not runtime egress. Only query targeted assembly/YAML when needed; don't reopen frozen extraction components.

### Pass G — Coverage, exceptions and verification
Report (i) 2,036 API-artifact primary candidates across **all 15 domains including TIP and LO**, (ii) 2,414 operation primary candidates and their inherited/domain-specific confidence, (iii) 41 zero-operation API artifacts WITH domain candidates where supported, (iv) QIWA Parent/service coverage independent from Domain coverage, (v) POC/Test/Mock/Sample inventory separately, (vi) TIP/LO dual-dimensional AS-IS/domain exposure, (vii) Utilities vs Common collision checks, (viii) exact reasons for null primary, and (ix) cross-domain operation/function relationships.

Audit all formerly `NO_PARENT_NAME_MATCH` **by new artifact-first rules**, NOT by recopying 018E labels. Do not target an arbitrary coverage %; measure false-positive and false-negative samples. Deliver reviewable full ledgers with explicit evidence strings and concise sample explanations, not just rollups.

## 5. Mandatory token-efficiency / staged caching
Re-use useful 018E caching infrastructure **only as cache mechanics/source-derived safe indexes, never as preassigned labels**; create namespace `indexes/task018f_cache/` for semantic/attribution stage caches. Keys incorporate SHA-256 of all dependent canonical API/operation identity indexes, QIWA CSV, schema indexes or targeted YAML, Product/Plan identity evidence, EA anchor/rule version, parser, normalization and cache schema. Change in domain definitions invalidates only rule-dependent classification stages; change in YAML invalidates its per-artifact schema stage + downstream affected identities, not everything; staging remains read-only.
- `api_artifact_identity_lookup.jsonl` indexed by artifact ID + original name, source YAML pointer and list of operation IDs (incl zero-op).
- `domain_anchor_registry.jsonl` with contextual rules and collision/exception cases.
- `qiwa_parent_module_lookup.jsonl`, `artifact_parent_edges.jsonl`, `operation_parent_edges.jsonl` built by keyed joins, never all-pairs.
- `schema_business_object_clues.jsonl`: compact safe request/response summaries: semantic object, role, field/enum status clues, original $ref/source pointer, certainty and exclusions; **not full schema dumps**.
- `api_domain_evidence_cache.jsonl`, `operation_domain_evidence_cache.jsonl`: compact source-grounded evidence vectors + provenance, not copied old classification labels.
- `product_channel_lookup.jsonl`, `backend_branch_lookup.jsonl`: read only if stage requires them; preserve independent dimensions.

**Retrieval route:** EA Domain/Anchor → Canonical API Artifact compact known evidence → accepted operation(s) → schema semantics or QIWA Parent index if needed → CodeGraph/backend only for verification → targeted raw YAML only when a specific unresolved semantic requires it. Use deterministic local code for 2,036/2,414 record joins, not per-record LLM reading. On-screen context should contain counts, bounded representative samples and failure reasons only. Never paste entire CSVs/YAML into Codex messages. Validate cache row counts/IDs/provenance/schema on load; hash-based invalidation and cold/warm deterministic output byte equality required. Cache telemetry: hits/misses/stages rebuilt, targeted YAML files read, actual unchanged source skips, unresolved schema refs; demonstrate changing EA rules, CSV, single YAML and schema index independently. Caches accelerate retrieval; original YAML/CSV remains authority.

## 6. Exact required outputs under `outputs/task018f/`
1. `enterprise_domain_registry.csv` — 15 domains, including TIP/LO/Utilities as first-class AS-IS domains, contextual evidence rules.
2. `canonical_api_domain_ledger.csv` — **exactly 2,036 rows**; primary AS-IS candidate, underlying functional candidate, supporting domains, lifecycle purpose, identity evidence, Product/channel, QIWA linkage if any, schema clues and EA review flags; include all 41 zero-op artifacts.
3. `operation_domain_ledger.csv` — **exactly 2,414 rows** tied to canonical API and operation IDs, artifact candidate vs operation-specific evidence, method/path, request+response object clues, provisional AS-IS primary incl TIP/LO/Utilities, underlying functional candidate, source pointers, confidence and exceptions.
4. `domain_module_crosswalk.csv` — complete literal 30 QIWA module mappings, explicit unresolved reasons.
5. `domain_parent_services.csv` — domain→module→source Parent services and source IDs, no forced APIC exposure.
6. `artifact_parent_matches.csv` and `operation_parent_matches.csv` — exact/normalized candidate edges and collision evidence without forced confirmed joins.
7. `schema_business_object_evidence.csv` — targeted extracted API/operation request/response semantic evidence, strong object vs DTO/envelope distinctions and evidence pointers.
8. `domain_distribution_summary.csv` — **both** API-level and operation-level primary counts across all 15 domains, including TIP/LO; supporting/underlying/domain overlap counts separate from exclusive primaries.
9. `tip_lo_domain_inventory.csv` — TIP/LO AS-IS owner candidates, underlying functional domains, actual Product/Plan and channel evidence and conflicts; never only parallel flags.
10. `utilities_common_inventory.csv` — QKS/QueryCenter/ADAA/Support Center/QIWA Policies/ServiceNow/Zendesk/Webex/S3/token/validator evidence, origin vs shared reuse; 5+ distinct QIWA module count threshold retained.
11. `poc_test_api_inventory.csv` — POC/Test/Mock/Sample technical exposure, confidence and non-retirement status; includes artifacts with zero operations.
12. `backend_corrob_and_branches.csv` — configured ACE/external/unresolved backend and where applicable switch/case branches; no fabricated runtime calls.
13. `domain_mapping_exceptions.csv` and `unmatched_artifacts.csv` and `unmatched_operations.csv` — precise distinguishable cause, competing evidence, source pointers, EA review action; no vague catch-all reasons.
14. `zero_operation_apis.csv` — all 41 source-derived zero/unsupported-operation APIs and artifact-level candidate statuses.
15. `coverage_report.md` and `manifest.json` — reproducibility, hashes, validations, cache telemetry, match/coverage confusion matrix (artifact evidence vs QIWA name vs schema vs Product/Plan), bounded illustrative examples, cold/warm equality, unresolved reasons.

No secret-bearing URI/host/catalog values; include safe relative HTTP path where allowed. All CSVs sorted deterministically with stable IDs, no silent omissions.

## 7. Mandatory acceptance scenarios and controls
1. **`user-management`** — API artifact-level primary User Management candidate despite empty operationId and templated paths; operations inherit cautiously, no fake operation semantics.
2. **`user-management-privilege`** — User Management candidate; privilege scope and possible multi-op distinction preserved.
3. **`getpaymentdetails-v2` / `GetPaymentDetails` / `/getpaymentdetailshypp`** — Payment candidate from API/operation/path without QIWA Parent; describe Hypp/HyperPay assumption; don't invent backend ownership. Review `getpaymentdetails` sibling separately; do NOT declare duplicates.
4. **`gosi_getAccessToken`** — Utilities candidate, technical external-auth function; GOSI as external system not WorkForce by token name.
5. **TIP/Tabayyan/QAAS scenario** — PRIMARY AS-IS TIP when strong ownership evidence; underlying Contracts/other function separately, despite contract operation/schema label. TIP from actual Product/Plan/catalog is supported; examples alone not global whitelist.
6. **LO scenario** — PRIMARY AS-IS LO when grounded LO backend/ownership evidence; underlying business function separate; preserve LO-specific business validations.
7. **`SubmitOccupationCorrectionRequest`** — Occupation origin despite multiple QIWA consumer modules.
8. **`GetGosiContractsList`** — Contracts origin regardless of Work Permit consumption.
9. **`sendQIWAReports`** — switch 63 branches/multi-domains, do not invent a single business operation owner.
10. **Request vs Response YAML schema** — named business object and action vs DTO/wrapper/reference only; prove source pointer and direction, handle multi-object operations and source inheritance.
11. **POC/Test/Mock/Sample** — clear lifecycle purpose separate from domain and non-approval of retirement.
12. **Utilities vs Common** — QKS, qc_, ADAA, Support Center, QIWA Policies, ServiceNow, Zendesk, Webex, S3 client, tokens/validators grounded in evidence; technical is not automatically Utilities; >=5 distinct QIWA consumer modules marks Common shared reuse with origin retained.
13. **Zero-operation artifact** — name/schema-based API-level classification attempted and counted; never lost because no operationId.
14. **Generic-name/collision negatives** — `get`, `service`, `token`, `qc_`, substring LO, schema referenced by unrelated service; no automatic ownership misassignment.
15. **Historical regression** — compare 018E summary as a **diagnostic AFTER new output generation only**, never imported into classification logic; explain movement of source-evidenced artifacts from no-parent to candidate without pursuing arbitrary numeric thresholds.

All tests use real source examples where available; if a named exemplar isn't present, explicitly record `SOURCE_NOT_FOUND` rather than fabricate it. Verify exact closure 2,036 APIs, 2,414 operations and 41 zero-operation APIs; all 15 registered domains, full original modules, separate dimensions, deterministic source hashes and IDs, independent source evidence, redaction, cache cold/warm byte equality, incremental invalidation and bounded YAML reads.

## 8. Execution and stop
Implement Task 018F deterministically, with targeted extraction and new code/tests/complete outputs; never patch frozen baseline parsers solely to improve coverage. Run focused tests and available repository regression; distinguish known sandbox/missing-fixture defects from new failures. Publish concise `codex/comm/HANSOFF.md` including API-first and operation-level attribution distributions, TIP/LO/Utilities primary counts, POC/Test dispositions, zero-op inventory, schema-evidence impact, cache statistics and quality caveats.

Commit/push Task 018F changes following existing repo guardrails. **STOP: `EA_REVIEW_TASK018F`.** No Task 019, rationalization, productization, retirement, business-domain ratification or Kong TO-BE design without explicit EA approval.

## Historical checkpoint — read only, not classifier input
- 018E TECHNICAL PASS: 618 provisional functional primaries / 2,414 operations, but QIWA-Parent-dependent classification missed obvious artifact evidence and relegated TIP/LO to channel-only dimensions; these are precisely the issues Task 018F must address.
- 018D TECHNICAL PASS: independent branch/Shared reuse/TIP observations; route confirmation too restrictive for business candidates.
- 018B/018C and earlier frozen milestones remain unchanged.
