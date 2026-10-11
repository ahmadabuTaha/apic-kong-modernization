# Phase 5 — Task 017 FULL: Evidence-led Logical API Formation

## EA authorization and baseline
The Enterprise Architect explicitly authorizes **Task 017 full-estate provisional formation** following the successful *technical* execution of the 10-case mock and 46-case expanded validation (98 unique operations / 86 canonical APIs). Approval applies to **methodology and progression**, not to any proposed business boundary, identity equivalence, or retirement.

Frozen inputs: Phases 0–4, Task 014 (2,036 canonical APIs; 2,414 accepted HTTP operations), Task 015 observed functions (provisional), Task 016 full/refinement (1,170 compared pairs; 470 potential same behavior, 120 conflicting, 573 insufficient, 6 structural-only, one supported different action; 1,481 unpaired-visible). Preserve exact original evidence, source IDs, hashes, source pointers, statuses and previous Task 017 mock/expanded outputs. Do not overwrite them. STAGING/sandbox is not verified production or runtime.

**No Domain (Task 018), Capability (Task 019), rationalization/merger/retirement, Kong topology, production assumptions, or Release Management redesign.** STOP for EA review before future tasks.

## Objective / actual enterprise problem
Create a complete, reviewable **PROVISIONAL conceptual Logical API catalog**, organized around evidenced business resource, action, lifecycle and consumer-facing boundaries, despite inconsistent APIC names/contracts/versions and no established enterprise naming standards. Explain every grouping AND every non-grouping. It is not enough to output API-name clusters or claim PASS because deterministic tests passed.

Keep two axes independent:
- FUNCTIONAL_EQUIVALENCE_CANDIDATE — possibly same action + object + behavioral semantics implemented through different exposures; NEVER an approved duplicate/substitution.
- LOGICAL_API_COHESION — distinct or related operations may belong to one conceptual business resource/workflow boundary; e.g. approve/reject/cancel distinct. Related object ≠ demonstrated shared lifecycle/ownership/consumer boundary.

A Logical API is NOT automatically the same as a deployed APIC API or APIC Product, and is NOT a Kong Service/Route/Product.

## Explicit EA-reviewed provisional decision rubric (from 46-case sample)
Use R1–R7 for **each formation proposal AND each asserted member**:
- R1 Resource: explicit/corroborated business object, workflow or resource identity; reject generic tokens.
- R2 Cohesion: distinct actions and *direct* resource-path family / lifecycle / workflow evidence. Same object token alone does not establish cohesion.
- R3 Consumer/authorization/ownership: distinguish accepted Product/Plan/Subscription exposure associations from proven owners, consumers and entitlements. Mark absent source as NOT_EVIDENCED.
- R4 Contract and variants: exact/base path, method, request/response, security, version and transformation differences preserved; never assume compatibility or newest/oldest.
- R5 Backend operation: separate configured API-shared candidate, explicitly operation-scoped configured facts and actually evidenced operation semantics; do not equate shared target/system with shared function or executed egress.
- R6 Counterevidence: concrete negative signals, plausible split/alternative boundary, what evidence would decide, no transitive closure of pairs into equivalence.
- R7 Provenance: exact canonical API ID, Task 014 operation ID, Task 015 function ID, Task 016 candidate/comparison/refinement IDs where present, current source fingerprints/pointers and certainty.

Criteria states SUPPORTED / CONTRADICTED / NOT_EVIDENCED with short cited source pointers; do not manufacture organizational standards, workflow, authorization, consumer/business-owner identities or runtime behavior. An explicit single canonical API with coherent resource-path family and distinct CRUD/workflow operations CAN be `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY` on R1+R2+R7 even if R3 and R5 are NOT_EVIDENCED; document their decision risks. Cross-canonical-API grouping requires stronger direct coherence evidence than same name/object/schema/backend; otherwise PARTIAL or leave unformed. These are PROPOSALS, not architect-approved Logical APIs.

**Three independent verdict axes:**
1. `TECHNICAL_VALIDATION`: PASS/FAIL only for implementation, source reconciliation, deterministic outputs and tests.
2. `EVIDENCE_SUFFICIENCY`: SUFFICIENT_FOR_PROVISIONAL_BOUNDARY / PARTIAL / INSUFFICIENT / SUPPORTED_SEPARATE with explicit criteria and counterevidence.
3. `ARCHITECT_ACCEPTANCE`: PENDING for all proposals, including sufficient ones. No semantic/architectural PASS claim.

## Full coverage without false forced grouping
- Reconcile **all 2,414 supported Task 014 HTTP operations exactly once in a primary coverage ledger**, one-to-one with Task 015. Include 1,481 previously unpaired Task 016 operations (not just existing pair candidates). Distinguish a canonical API inventory vs operation inventory; retain the 36 registry-only and five source-backed/no accepted Path Item cases separately as explicit API-level nonformation reasons. Preserve native-protocol semantic limits and all Task 014–016 inherited unresolved relationship categories.
- Generate Logical API boundary candidates by bounded indexes of exact resource/workflow signals, path family, business action/object, existing canonical API multi-operation structure and Task 016 candidate graph. Use compound evidence and counterexamples. Prevent massive generic 'employee', 'contract', 'service', '/{uri}' or shared response-wrapper mega-groups. No 2,414² all-pairs, transitive clustering from pair hypotheses, name-only joining or Product-only joining.
- A source operation can be **considered** for multiple *competing* boundary options; do not assign it as a silently accepted member to multiple finalized primary groups. Use one primary ledger disposition per operation (PROVISIONAL_BOUNDARY_MEMBER / PARTIAL_BOUNDARY_MEMBER / UNFORMED_INSUFFICIENT / SEPARATE_BOUNDARY or other precise explicit reason). Keep alternatives in separate proposal relations with status and pointers. Cross-boundary overlaps must be explicit, measurable and reviewable. Never fabricate a logical source operation: one APIC operation may document multiple actions (approve/reject in one source operation), retain one source operation with separately supported logical action intents.
- Keep non-formation and standalone/singleton operations visible and searchable; absence of a Task 016 pair is not proof of distinct business function. A full-coverage catalog may have fewer grouping decisions than operations but **no lost operations**.
- Persist direct candidate→member assertion provenance; group-level certainty cannot exceed weakest material member without explicit justified scope exclusion. No transitive identity claims.
- Preserve backend operations / dispatch uncertainty, feature-flag unknowns, independent Product/Plan/Subscription membership and exposure/version concerns. A staging subscription link proves accepted membership context, not operation calls, active consumers or production deployment.

## Semantic anti-false-positive controls
- Approve / reject / cancel / submit / update / activate / deactivate / issue / retrieve and materially different business actions remain distinct functions despite shared request schema or a cohesive candidate API.
- Don't hard-reject based only on lexical words: copied descriptions, conflicting actions or single path/name signals must be tagged as unresolved unless independent evidence resolves them.
- Technical endpoints (health, token, authorization) and generic CRUD wrappers must not automatically become consumer-facing business APIs.
- Preserve the 46-case expanded sample as a **named regression fixture**, especially SC Request: `approverejectscrequest` and `cancelscrequest` remain two source operations, three logical action intents, two alternate conceptual boundaries (unified SC Request Actions vs split Decision/Cancellation), PARTIAL evidence, no ownership/lifecycle/consumer inference. Likewise retain three sufficient-for-provisional examples (Visa, Special Permit, Runaway Request) as provisional only; preserve negative controls for user-management generic URI, unrelated MOMRA checks, copied metadata, WPS wrappers, versions and employment inquiry. Do NOT require all 46 sample cases to be predicted identically if full-estate evidence legitimately differs: report every status change with supporting reason, distinguish correction from contradiction.
- Guard against version variants mistakenly merged and against logical grouping being mistaken for duplication or safe substitution.

## Execution strategy (low token / bounded)
Reuse Task 014/015/016 and Task 017 mock/expanded indexed results, accepted Product/Plan/Subscription identity-joined relationship indexes and CodeGraph. Use deterministic index-first grouping with diagnostics (block size/fanout thresholds, skipped oversized groups, uncovered signals) and selective authoritative raw-source reads ONLY when needed for a high-impact contradiction. No broad staging scan where existing indexes suffice; no Vector DB/Blackboard/multiagent/LLM-heavy estate sweeps; no Confluence access. Treat missing raw sources as unresolved, not absent functionality. Keep private full catalog under ignored `indexes/`, commit compact source-redacted evidence.

## Required deliverables
Generate ignored full indexes (use stable descriptive names, e.g.):
- `indexes/task017_full_operation_disposition.jsonl` — 2,414 exact ledger rows + direct Task 014/015 provenance and proposal links;
- `indexes/task017_full_logical_api_proposals.jsonl` — every proposed boundary with member ID list, direct assertions, criteria R1–R7, alternative split/merge, positive/negative evidence, confidence limits and 3 distinct result axes;
- `indexes/task017_full_logical_operation_intents.jsonl` — action intents without falsely splitting accepted source operation IDs;
- `indexes/task017_full_review_queue.jsonl`, `indexes/task017_full_formation_diagnostics.jsonl`, `indexes/task017_full_manifest.json`.
Actual file names can differ only if manifest documents exact mapping.

Commit compact reviewer evidence under `tests/evidence/task-017/full-extraction/`:
1. `logical_api_formation_contract.md` — definitions, primary membership/competing-boundaries model, R1–R7 and nonformation rules, explicit PASS distinction.
2. `estate_coverage_and_disposition.json` — all 2,414 accounted, unique APIs, counts by evidence sufficiency and operations grouped/partial/standalone/unformed, explicit 1,481 previous singletons coverage, 36 registry-only/5 no-path API-level gap handling, exact overlap/candidate accounting, scope limitations.
3. `reviewable_boundary_examples.jsonl` — **30–50 diverse actual proposals and nonformation controls**, readable names, operation method/path, source pointers, criteria evidence, strongest counterargument, alternative, version/exposure context; MUST include 46-case sample cross-check and SC Request.
4. `case_regression_and_contradictions.md` — original 10 and expanded 46 anchors comparison (no silent status changes), supported-same-action vs related-different-action separation, generic/shared-schema/backend false positives, sampled negative control outcomes.
5. `review_queue_and_missing_evidence.json` — counts and top prioritized architecture questions by actual failure reason; not an undifferentiated demand to review thousands manually.
6. `cache_and_tests.json`, `build_manifest.json`, `commands_and_results.txt`; add deterministic generation script only if needed for reproducibility.

Prioritize concise tabular summaries and actual illustrative named cases: reviewers must be able to challenge grouping without needing the full JSON indexes. Include source pointers and confidence; no credentials, hosts or consumer identities in committed evidence.

## Validation / acceptance tests
- Exact 2,414/2,414 reconciliation, Task 015 1:1 and retained 1,481 previous unpaired; explicit separate API-level no-path/registry-only gap inventory (no fabricated HTTP operations).
- Stable membership references, no lost/duplicated source IDs in primary ledger; alternative memberships distinct, direct, traceable; no automatic chain equivalence.
- Every asserted member and every proposed boundary has R1–R7 (or explicit nonformation rationale) and evidence pointers; no bare 'PASS' for business correctness.
- Different documented business actions preserved; reject false grouping based on shared schema, generic path, backend system or Product; preserve versions/contracts/security/exposure; no production/feature-flag/retirement inference.
- SC Request and named 46-case regression checks and transparent deviations; no invented backend operation semantics; unresolved metadata remains unresolved.
- Frozen-input SHA/fingerprint integrity, redact sensitive data, deterministic generation + hash-verified caches, bounded candidate diagnostics.
- Focused tests, prior Task 014–017 regressions and repo suite. Distinguish known five Phase 0 fixture setup errors from new failures; no need to reopen frozen Phase 0 in this task.

## Mandatory STOP
Update `codex/comm/HANSOFF.md` with total grouped/proposed/partial/insufficient/standalone distributions, coverage reconciliation, examples of correct and rejected groupings, evidence weaknesses, 46-case regressions, tests, actual deviations, and whether full catalog is fit as **provisional input** to Task 018. Commit and push authorized implementation/evidence. **STOP for EA review; do NOT begin Task 018 Domains, Task 019 Capabilities, API Rationalization, Kong design or any retirement/deployment.**
