# Phase 5 — Task 015: Observed Function Discovery — evidence-first mock and gap impact control

## Architectural authority and frozen checkpoint
EA decision dated 2026-10-08: **Task 014 PASS / FROZEN** based on Codex full-extraction HANSOFF and evidence. Task 015 now authorized **for representative mock + architecture review only**. Do NOT reopen Phase 0–4 or Task 014 without a reproducible defect, concrete contradiction, or broken downstream contract. Do not start Task 016 onward.

Approved Task 014 baseline:
- 2,036 canonical APIs (2,000 source-backed; 36 registry-only);
- 2,414 unique HTTP operation inventory records;
- 60 structurally overlapping API-pair candidates, NOT confirmed duplicates;
- 2,338 operations without summary, 757 without description, 767 without operationId;
- 5 source-backed APIs without supported explicit HTTP Path Items;
- 113 unresolved Product-location occurrences, still unattached;
- confirmed request/response structural differences in searchseasonalvisarequests versus searchseasonalvisarequests-v2;
- 2,282 operation records with candidate inherited backend context; 67 with exact operation-scoped configured evidence. None proves runtime egress.
- 50 repository tests passed, 5 previously known Phase 0 fixture setup errors. These are **not** evidence of full-suite green.

Read AGENTS.md, CURRENT_TASKS.md, current HANSOFF.md, Task 014 contract v2, coverage/gaps, v2 comparison, cache effectiveness and manifest before implementing.

## Purpose
Extract an **Observed Function** for each evidenced HTTP operation, where possible: a compact, evidence-grounded statement of **what the operation appears to do** (subject/action/target), not a Logical Function, Logical API, Business Capability or Domain. Preserve genuine ambiguity. An Observed Function is a *provisional factual/interpretive semantic record*, clearly distinguished from source-extracted facts and architecture-approved conclusions.

User's concern is cumulative downstream gaps. Make gap/impact traceability a first-class deliverable and **stop downstream conclusions whenever foundational evidence is inadequate**, without reworking frozen phases.

## Retrieval & token efficiency
- Use frozen CodeGraph and compact canonical indexes for navigation; accepted Task 014 semantic API/operation inventory and persistent cache for primary semantics; inspect targeted raw authoritative Swagger/YAML/assembly only when unresolved ambiguity matters. Do not load whole files or full graph context into LLM prompts by default.
- Reuse existing index/caching infrastructure; do not create a Blackboard, new agent framework, vector DB, broker or orchestration system.
- Deterministic first: compact evidence feature projection, rules for high-confidence explicit descriptions, normalized method/path, request/response schema/parameter facts, safe backed target and assembly context. If a model is needed, send only bounded relevant records and evidence pointers; maintain model/prompt version and cached result identity. No unbounded per-operation analysis or token-heavy graph dumps. State actual model use and cost where measurable; never invent token metrics.
- Source schema hashes are similarity signals; when comparing v2, inspect actual request/response structure or safe schema diffs instead of treating matching reference names or differing hashes as a final semantic conclusion.

## Observed Function contract — propose and mock
Each *sampled* operation record must retain:
- canonical API ID, Task 014 stable operation record ID, evidence pointers and source fingerprint;
- source extracted method/path; factual descriptions, operationId, summary, tags when present; compact request/response types, status codes, schema fingerprints or safe targeted shape pointers; backend configured versus candidate certainty and conditional policy evidence;
- candidate observed function: action verb, business object/resource phrase, concise evidence-backed description, and explicit evidence type(s);
- interpretation status e.g. EXPLICITLY_DESCRIBED, INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS, AMBIGUOUS_NEEDS_REVIEW, INSUFFICIENT_EVIDENCE, UNSUPPORTED_PROTOCOL, REGISTRY_ONLY_NO_OPERATIONS. Do not use blanket Other/Unknown labels.
- certainty/evidence strength and reason, contradictory signals, missing information and unresolved links; reviewer status PENDING_REVIEW / APPROVED / REJECTED where needed.
- Provenance: distinguish configured backend and candidate inherited backend; neither implies observed runtime usage.
- Distinguish explicitly technical operations (e.g. proxy/security wrappers) from evidenced business actions; never force a business-domain or capability label.
- One API may contain multiple observed functions. Similar observed functions under different APIs MUST NOT be declared the same Logical Function in this task.

## Mandatory downstream Gap Impact Register
Create a machine-readable reviewable register (local indexes + compact committed evidence) with per-gap:
- upstream task and source artifact, precise gap ID, scope (api/operation/relationship/protocol), affected canonical/operation IDs;
- original condition and provenance; number of impacted records;
- downstream tasks potentially affected (015, 016, 017, 018, 019), **specific potential effect** rather than a generic warning;
- severity/state: NON_BLOCKING, LOCAL_REVIEW_REQUIRED, DOWNSTREAM_BLOCKER; confidence and rationale;
- mitigation/retrieval next action, responsible review role and recheck trigger;
- status carried-forward/resolved/accepted-limitation, without changing frozen evidence.
Give explicit handling to missing summary/description/operationId, registry-only 36, unsupported Path Item 5, WSDL-to-REST/GraphQL native semantic gaps, 113 unresolved Product-location occurrences, API_SHARED backend candidate-only context, 60 structural overlap candidates, and schema-shape differences in v2.
An absence of description is NOT automatically DOWNSTREAM_BLOCKER; a gap can be nonblocking if other evidence supports a bounded observed-function claim. Conversely do not label a vague GET/POST alone as sufficiently meaningful business function. Report review queue and impact counts by downstream task.

## Representative mock — STOP GATE
Use deterministic stratified selection targeting roughly 12–20 operations (not an estate-wide inference run), explicitly including:
1. operation with informative description or operationId (if available);
2. operation lacking summary and description but with informative path/schema evidence;
3. ambiguous/generic operation with insufficient information;
4. single-operation and multiple-operation parent APIs;
5. exact operation-scoped backend fact and API_SHARED candidate context;
6. conditional/multi-target routing where available;
7. sample v2 pair: searchseasonalvisarequests / searchseasonalvisarequests-v2, compare request and response actual safe schema shape and backend scope;
8. source-backed no-supported-path API and registry-only API as *API-level non-operation gaps*;
9. several Task 014 structural-overlap candidates with different canonical IDs, comparing what each operation appears to do but not asserting duplication;
10. cases with missing schema refs or unresolved paths where present.
An API can satisfy more than one criterion. Record selection algorithm and representation coverage. Do not choose only high-quality metadata.

## Deliverables
Codex implementation may add an additive module (e.g. observed_function/) and local ignored indexes/cache under indexes/ or outputs/. Do not alter frozen Task 014 code/output or staging.
Commit compact, safe review evidence under tests/evidence/task-015/mock/:
- observed_function_contract.md
- sample_selection.json
- observed_function_samples.jsonl
- upstream_gap_impact_register.jsonl (bounded samples plus aggregate count/report)
- coverage_evidence_and_uncertainty.json
- ambiguity_review_queue.jsonl
- v2_semantic_evidence_side_by_side.md
- commands_and_results.txt
Keep evidence secret-safe and compact with no raw host/credential leakage. Trace all claims to specific accepted provenance.

## Validation & STOP
- Full sample cardinality reconciles to selected operations and all selected canonical API identities.
- No unsupported native GraphQL/WSDL operations fabricated, no registry-only operations, no functional duplication, domain or capability assertions.
- No missing field silently replaced by an invented fact. Unresolved cases persist through precise gap IDs, not generic Unknown.
- Confirm that each observed function can point to factual evidence and uncertainty, and that candidate backend associations remain candidate-only.
- Verify evidence-driven interpretation of the v2 differences without guessing fields from hashes.
- Cold/warm deterministic records where cache is used; frozen integrity, no redaction failure; focused tests and repository tests (report known 5 setup errors separately).
- Update codex/comm/HANSOFF.md with PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW, evidence counts, explicit architecture-review questions and downstream gap effects.
**STOP after Task 015 representative mock, committed evidence, tests and push.** Architect reviews semantic precision and gap classifications before the full-estate run. No Task 016–019, no automatic Stage 015 full rollout.
