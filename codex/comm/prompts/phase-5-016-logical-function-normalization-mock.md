# Phase 5 — Task 016: Logical Function Normalization — evidence-based MOCK FIRST

## Architecture decision and scope
The Enterprise Architect authorizes moving from Task 015 to Task 016. Task 015 **PASS / FROZEN as provisional Automated Observed Function Inventory**, not certified business-function correctness. Task 014 and Phases 0–4 remain frozen; do not reopen without a reproduced defect/contradiction/broken downstream contract. The repository currently has 2,036 canonical APIs, 2,414 HTTP operations, 2,414 Task 015 observed-function records, and 60 Task 014 structural-overlap candidate PAIRS. The 467 ambiguous/insufficient interpretations, 44 API-level gap records, 113 unresolved Product-location occurrences, and native-protocol gaps remain traceable limitations, not defects in production APIs or evidence of business inactivity.

Important source-context qualification: the APIC export corpus is from STAGING, close to a sandbox; do NOT infer production deployment, active usage, retirement, business criticality, or live equivalence. The confidence/status labels in Task 015 are **evidence strength for automated interpretation**, not API quality, runtime confidence, or business accuracy. A missing summary/description is source metadata absence, NOT necessarily an AS-IS architectural defect.

## Goal
Identify and normalize *candidate logical functions* across HTTP operations and different canonical APIs, even when names and paths differ. Task 016 starts testing WHICH operations may implement the same logical action on the same business object/resource, and WHICH differences may prevent equivalence. Do NOT form Logical APIs (Task 017), business domains (Task 018), capabilities (Task 019), API Products/Plans or Kong migration strategy.

**This instruction authorizes a representative mock and evidence review ONLY**; no estate-wide grouping until architect approval of mock.

## Grounding and efficient retrieval
Read AGENTS.md, CURRENT_TASKS.md, latest HANSOFF.md, Task 014 API/operation inventory contract and fingerprints, Task 015 provisional contract/distribution and review queue, Task 014 candidate pairs, and v2 actual request/response schema-diff evidence. Reuse accepted CodeGraph, compact indexes, Task 014/015 caches and targeted authoritative staging evidence. Do not ingest the entire staging corpus into an LLM; no new vector DB, Blackboard or multi-agent framework. Use deterministic compact candidate generation/blocking rather than all-pairs Cartesian comparison. Names/versions, backend identity, or path equality alone never prove equivalent business functions.

Enterprise Confluence has extensive API documentation but is not required or accessed for this mock. Where needed later, produce a specific evidence request for targeted Confluence lookup and retain explicit unverified source state.

## Mock selection
Select a bounded stratified sample of roughly 8–12 *pairs/groups*, including:
- the actual seasonal visa search API vs v2 pair, showing contract similarities and actual request/response field/type differences;
- different-name APIs where operations could overlap and backend or contract signals help, but not the sole decision criterion;
- same backend but differing action/payload to test false positive prevention;
- similar method/path but different backend/contract or API exposure/version;
- identical/provisional Observed Function wording across distinct canonical APIs with substantive schema differences;
- missing summary/description and Task 015 AMBIGUOUS/INSUFFICIENT interpretation cases;
- one-to-many operations and multi-operation canonical APIs where appropriate;
- technical/security endpoints that should not be merged as business functions;
- at least one negative control (CLEARLY_DIFFERENT from supported evidence) and one case NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE.
Do not fabricate examples. If a category is not evidenced, state NOT_EVIDENCED_IN_SAMPLE.

## Proposed logical function candidate contract
For EACH operation and pair/group involved:
- stable Task 014 operation ID, Task 015 observed-function ID, distinct canonical IDs, source provenance and fingerprint;
- normalized provisional action/object phrasing only as review proposal, not architecture-approved business semantics;
- independently inspect (where available) HTTP method, exact/normalized path, semantic action/object clues, parameters and required flags, request body/content/schema structure, response codes/content/schema structure, auth and exposure, backend observation/target, operation routing scope, assembly transformations if evidenced, version changes and missing evidence;
- compare **actual safe request/response shape**, not just hash/ref strings; preserve material differences such as presence, type, requiredness and transformations;
- explain positive and negative evidence separately, with specific pointer-backed source facts; distinguish API_SHARED candidate connectivity from exact operation-scoped configuration and runtime unknown;
- comparison status only: POSSIBLE_SAME_LOGICAL_FUNCTION, CLEARLY_DIFFERENT_SUPPORTED, NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE, or REVIEW_REQUIRED_CONFLICTING_SIGNALS. These are *proposal statuses*, NEVER CONFIRMED_DUPLICATE or SAME_FUNCTION_APPROVED.
- detect and document false-positive vs false-negative limits (versions, middleware, path rewrites, dynamic routing, schema aliases, façade/adaptor APIs).
- DO NOT auto-merge distinct canonical APIs, change frozen identity, retire APIs, or collapse Operation IDs.
For v2, allow **same apparent search function with DIFFERENT request/response contract** as a candidate possibility; do not automatically conclude same function, safe substitution or retirement.

## Gap policy and prior results
Keep provenance of all 11 inherited gap categories; revise their *interpretation at consumption point*, not frozen Task 014/015 source. Distinguish METADATA_ABSENT, AUTOMATED_INTERPRETATION_LIMIT, SOURCE_EVIDENCE_NOT_AVAILABLE, RUNTIME_NOT_EVIDENCED, and SEMANTIC_VALIDATION_PENDING. A task-level gap label DOWNSTREAM_BLOCKER applies only to the specific unsupported pair/group conclusion, not an automatic halt of Task 016. The staging/sandbox origin should be explicit on any output implying adoption or deployment.

Task 015 1,662 HIGH and 285 MEDIUM records reflect source/structural interpretation rule confidence, not human-approved accuracy; preserve all records as PENDING_REVIEW. Include intentionally low/none cases to test candidate recall without promoting speculation.

## Deliverables and tests
Add minimal, additive implementation only when it directly supports the mock; do not reinvent a new platform or large orchestration layer. Produce safe compact review artifacts under `tests/evidence/task-016/mock/`:
- logical_function_normalization_contract.md
- sample_pair_selection.json
- candidate_pair_comparisons.jsonl with evidence and limitations
- v2_contract_and_function_assessment.md
- false_positive_negative_cases.md
- inherited_gap_consumption_assessment.json
- candidate_review_queue.jsonl
- tests_and_replay_results.txt
Keep full generated intermediate indexes/cache only under ignored indexes/ or outputs/. Ensure source/redaction safety and deterministic output/selection; tests must check no claimed duplicates, no invented egress, no source mutation, stable IDs/provenance, frozen Task 014/015 integrity, and correct comparison of contract differences. Report existing Phase 0 fixture setup errors separately.

## Mandatory STOP
Update codex/comm/HANSOFF.md with exact sample pair counts, status distributions, uncertainty/review queue, actual comparisons, tests and specific EA review questions. Commit and push. **STOP after Task 016 mock; no full-estate Task 016 until EA explicitly approves the candidate model.** Do not implement Task 017–019.
