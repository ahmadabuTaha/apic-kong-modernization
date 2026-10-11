# Phase 5 — Task 016: Full Logical Function Candidate Discovery and Normalization

## EA authorization and frozen boundaries (2026-10-11)
Task 016 representative mock is **ACCEPTED AS A CANDIDATE-COMPARISON METHOD**, not as proof that any compared pair implements the same business function. Advance to **full estate-wide Task 016 candidate discovery and provisional logical-function normalization** with the additional mandatory Endpoints, Subscription Context and API Version/Feature-Variant analysis below. Staging is sandbox-like; no inference of production usage, operation runtime egress, active consumers, API retirement, business criticality or feature-flag use without explicit matching evidence.

Task 014 (2,036 canonical APIs, 2,414 operations) and Task 015 (2,414 provisional Observed Functions) and Phases 0–4 remain frozen. Task 015 HIGH/MEDIUM are strength of automated interpretation, not business-semantic accuracy. Keep all source identities, Operation IDs, accepted relationships and 60 structural candidate pairs intact. Do not reopen frozen components absent a reproducible defect. Read AGENTS.md, CURRENT_TASKS.md, latest HANSOFF, Task 014/015 contracts, Task 016 mock contract/findings, relationship indexes, approved CodeGraph and source manifests first.

## Goal
Discover and normalize **provisional logical functions** across the accepted APIC HTTP operations, including pairs with dissimilar API names/paths. Reveal candidate functional overlap with explanations, counter-evidence and version/consumer context; do not form Logical APIs (Task 017), confirm duplicate APIs, retire or merge endpoints, infer feature flags, apply business-domain/capability labels, or implement Kong. Treat potential shared business intent and interchangeable API contracts as DIFFERENT dimensions.

## Candidate discovery, not merely validation of the 60 pairs
Use multi-pass bounded deterministic candidate generation/indexing (normalized action/object/observed wording; path tokens and endpoint operation shape; request/response contract signals; available backend observation targets and transformation context; accepted version families; and eligible Product/Plan/API relationship context), plus targeted safe source reads for finalists. Include the known 60 pairs but search beyond them and explicitly measure discovered candidates NOT included in the original structural-overlap set. Provide selection/recall-proxy diagnostics and false-positive negative controls without falsely claiming complete business-equivalence recall. Do not run unbounded all-pairs (2,414 x 2,414), broad LLM reasoning, Vector DB, Blackboard or multi-agent build. If candidate fan-out grows, use documented caps/queues rather than silently dropping evidence.

## Mandatory endpoint-level comparison
For each candidate pair/group, compare **both**:
- Consumer-facing HTTP operation endpoint: API identity, version, base path, method, exact and normalized path, operation selector, exposure, auth, request parameters/body, response schema and error shape, and applicable documented contract differences.
- Backend/implementation endpoint: configured backend target identity/path or unresolved path, scope of backend configuration (OPERATION_SCOPED fact vs API_SHARED candidate), assemblies, branches, rewrites, transformation policy pointers, conditional routing when evidence exists; distinguish actual source-configured backend from **runtime egress NOT PROVEN**. Do not confuse common gateway route/hostname/backend ID with business-function equivalence. Do not emit sensitive endpoint hostnames/credentials in committed reports; keep safe sanitized IDs and pointers.
- For suspect services where the endpoint information could alter judgment, retrieve targeted authoritative evidence from frozen CodeGraph/Swagger/assembly only; mark configured-versus-evidenced operation behavior rigorously.

## Mandatory Product, Plan and Subscription context
For suspect functions/APIs, check whether accepted APIC relationship indexes evidence: Product inclusion, Plan entitlements, catalog/space context and Subscriptions when available. Model the join and its provenance through its **actual evidence scope** (e.g. subscription to product/plan or application, then accepted Product-to-API linkage). Never promote Product/Plan/Subscription membership into proof that a specific HTTP operation is invoked, a consumer is active or a production deployment exists.
Report:
- subscription evidence AVAILABLE / NOT_EVIDENCED_IN_ACCEPTED_SOURCE / UNRESOLVED_RELATIONSHIP, with exact relationship IDs, appropriate indirect linkage, safe counts when grounded, and scope/uncertainty;
- whether the compared APIs share or differ in subscribed Product/Plan exposure where supportable;
- contextual question: could variants plausibly serve separate consumers, commercial plans or lifecycle tracks? Mark ONLY as hypothesis until directly evidenced.
Never treat absent subscriptions in staging as zero real enterprise consumers or as retirement evidence. Preserve 113 unresolved Product-location occurrences and do not cross-join by names when accepted IDs cannot resolve. Avoid revealing sensitive subscriber identity.

## Mandatory version-family and feature-variant analysis
API version counts and naming are NOT governed by assumed consistent versioning rules. Build provisional version/variant families using canonical IDs and source evidence, even if versions/names are misleading. For each candidate family:
- compare API/exposure endpoint and backend-target/assembly policies plus operation list;
- compare actual request/response field presence, requiredness, types, nesting, enum or other safe structural compatibility and transformation evidence;
- assess differences that MAY reflect business-rule divergence, channel/consumer needs, contract evolution or architectural adaptation, using evidence-backed **hypotheses** rather than certainties;
- analyze whether both versions could coexist through explicit feature flags, policy conditions, consumer targeting, subscriptions, separate routes or migration coexistence **ONLY when there is actual source evidence**; otherwise mark `FEATURE_FLAG_NOT_EVIDENCED` / `COEXISTENCE_REASON_UNVERIFIED` instead of asserting old/new both actively used;
- distinguish version label, contract age, deployment order and actual activity. Never infer newer version is replacement or older version is obsolete. Distinguish logical-function sameness from contract compatibility or safe substitution.
Prioritize targeted v2 seasonal visa comparison (request SortBy difference, response fields/types and candidate-only backend certainty), employment-status pair and any newly discovered version families with meaningful contrasts. Keep false-positive and false-negative controls.

## Candidate comparison and output model
Retain per-operation: Task 014 ID; Task 015 Observed Function ID/status; canonical API/source fingerprints and evidence pointers; provisional normalized business action/object. Link any candidate logical-function group to its MEMBER operations with distinct provenance. Persist positive AND negative evidence for semantics, endpoint, schema, backend, API version, Product/Plan/Subscription exposure, and any verified policy/feature flag markers.

Use the mock comparison statuses as *proposals only*: `POSSIBLE_SAME_LOGICAL_FUNCTION`, `REVIEW_REQUIRED_CONFLICTING_SIGNALS`, `CLEARLY_DIFFERENT_SUPPORTED`, `NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE`. Provide separate dimensions: `BUSINESS_INTENT_HYPOTHESIS`, `CONTRACT_COMPATIBILITY`, `BACKEND_CERTAINTY`, `VERSION_OR_VARIANT_RELATION`, `SUBSCRIPTION_EVIDENCE_STATE`, `RUNTIME_USAGE_STATE`. Distinguish verified equal/different facts from unsupported/unknown; no arbitrary certainty numbers. A group can represent probable shared intent while its members have materially different contracts, versions and consumers.

**No confirmed business duplicate, no API/operation merge, retirement, substitution or production activity claim.** Do not collapse different API IDs/operations; place decisions in pending review queue for architects. Uncompared operations must remain visible (singleton/unpaired/no-bounded-candidate) and be reconciled in coverage, not silently discarded.

## Gap handling and staging discipline
Carry all 11 inherited gap classes and Task 015 review queue as traceable limitations. Missing staging description, operationId, summary or subscription does not by itself make an API defective. Indicate limited automated interpretation versus actual missing authoritative source; scope blockers only to unsupported comparison/group claim, never halt the full Task 016 inventory. Confluence documents may support *future targeted* review after explicit authorization; no bulk ingestion or unverified assertions from Confluence.

## Outputs and gates
Implement minimally and additively to Task 016 (do not change frozen Task 014/015/source). Keep complete indexes, candidate generation maps, review queue and cache in ignored indexes/ or outputs/ with deterministic fingerprints, bounded indexed retrieval and incremental replay when practical. Commit compact, secret-safe evidence under `tests/evidence/task-016/full-extraction/`:
- `logical_function_candidate_contract.md`: relationship/evidence scopes and comparison status dimensions;
- `candidate_discovery_coverage.json`: 2,414 input operations reconciled, candidate groups/pairs, original 60 vs newly discovered, unpaired counts, block coverage and bounded-recall limitations;
- `endpoint_and_subscription_comparisons.jsonl`: representative positive, conflicting and negative cases, sanitized frontend/backend endpoints, Product/Plan/Subscription scopes and missingness;
- `version_variant_family_assessment.jsonl`: bounded family examples with safe concrete schema contrasts and explicit feature-flag evidence status;
- `normalized_logical_function_candidates.jsonl`: bounded candidate/group representatives with distinct operation membership;
- `review_queue_and_gap_impact.json`: counts, issues for architect, inherited gap impacts, priority and targeted questions;
- `cache_and_tests.json`, `build_manifest.json`, `commands_and_results.txt`.
Make local full outputs discoverable in HANSOFF, not committed if huge; redact URI hosts/credentials and sensitive consumer identifiers. Tests: exact ID/coverage reconciliation; linkage scope provenance; subscription join correctness (no inference of operation-level consumption); negative controls; contradictory semantic/contract cases; version hierarchy and feature-flag non-inference; request/response safe actual structure; endpoint scope; no runtime/retirement/duplication claims; stable deterministic regeneration and frozen integrity. Report known 5 Phase 0 fixture setup errors distinctly if they persist.

## STOP
Update `codex/comm/HANSOFF.md` with status PASS / FIX_REQUIRED / REVIEW_REQUIRED, exact candidate and coverage counts, per-dimension evidence limitations, scope of any partial index, focused/repository test results and follow-up architecture decision points. Commit/push. **STOP before Task 017**, regardless of successful tests. Do not start Task 018/019 or Kong design.
