# Codex Handoff

## Task executed

Phase 5 — Task 014: Semantic Inventory & Operation Extraction.

## Prompt file used

`codex/comm/prompts/phase-5-014-semantic-inventory-operation-extraction.md`

## Summary of what was done

- Defined an additive semantic API/operation inventory contract for architecture review.
- Implemented deterministic representative-sample extraction only; no estate-wide rollout was performed.
- Selected canonical APIs from compact accepted identity, relationship, backend, dependency-edge, and unresolved-occurrence evidence.
- Parsed only compact-index-selected authoritative API YAML for source semantics.
- Created factual API inventory records and explicit Swagger/OpenAPI operation records with stable deterministic IDs.
- Preserved exact source pointers, missing-field reasons, compact parameter/request/response/schema references, backend scope, AS-IS Product/Plan links, and unresolved Product-location occurrences.
- Kept API-shared backend evidence from becoming falsely proven operation egress.
- Added focused tests and safe committed review evidence.
- Did not implement Task 015–019, operation graph nodes, semantic functions, logical APIs, domain/capability mapping, runtime inference, or Kong design.

## Implementation structure

- `semantic_inventory/inventory.py`: deterministic selection, targeted YAML parsing, API/operation extraction, missing-state handling, compact reference summaries, backend qualifiers, AS-IS relationships, unresolved-occurrence preservation, safe text redaction, and JSONL output.
- `semantic_inventory/__init__.py`: public Task 014 API.
- `semantic_inventory/__main__.py`: `python -m semantic_inventory` entry point.
- `tests/test_semantic_inventory.py`: duplicate occurrence, multi-operation identity, missing metadata, registry-only, backend-scope, determinism, redaction, and frozen-integrity tests.
- `tests/evidence/task-014/generate_task014_evidence.py`: deterministic architecture-review evidence generator.

## Semantic inventory contract

The review draft is `tests/evidence/task-014/semantic_inventory_contract.md`.

Key contract rules:

- `canonical_api_id` is the primary join key.
- API inventory IDs are content-derived from canonical API identity.
- Operation inventory IDs include canonical API ID, accepted source path, exact source pointer, HTTP method, and exact path.
- Operation records are inventory records, not CodeGraph nodes.
- Only explicit Swagger 2/OpenAPI 3 Path Item methods are supported in this mock.
- Parameters, requests, responses, and schemas remain compact facts/references; schemas are not expanded.
- Task 011 is authoritative for backend scope and resolution state.
- `OPERATION_SCOPED` backend evidence matches only exact method/path evidence.
- `API_SHARED` backend evidence remains API-level context labeled `API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS`.
- AS-IS Product/Plan data comes only from accepted frozen relationships.
- Future hypotheses and architectural judgments are separate fields and remain empty.

## Representative selection

- Selection algorithm: lowest stable canonical API ID satisfying each compact-index-derived criterion.
- Selected canonical APIs: 6.
- Required categories represented: 9 / 9.
- Source-backed samples: 5.
- Registry-only samples: 1.
- Targeted sources read for selection: 3.
- Targeted sources parsed for inventory: 5.
- Estate-wide source scan: no.

The sample includes:

- explicit multi-operation REST API;
- single-operation API;
- missing/unresolved operation metadata via a registry-only API;
- API-shared backend scope;
- operation-scoped backend evidence;
- accepted AS-IS Product and Plan connections;
- registry-only canonical identity;
- API with multiple backend targets;
- API linked diagnostically to an unresolved Product-location occurrence, retained as unresolved.

## Sample inventory results

- API inventory records: 6.
- Operation inventory records: 35.
- Unique operation IDs: 35 / 35.
- Sampled Swagger 2 APIs: 5.
- Registry-only/no-document APIs: 1.
- APIs with API-shared backend evidence: 3.
- APIs with operation-scoped backend evidence: 2.
- Operations with exact operation-scoped backend evidence: 9.
- Operations missing descriptions: 34.
- Sampled unresolved Product-location occurrences: 1.
- Estate unresolved Product-location occurrences preserved: 113.
- Unresolved occurrences attached as relationships: 0.

## Local generated indexes

- `indexes/semantic_api_inventory_sample.jsonl`: 6 records; SHA-256 `6c1c034a2042f153f3b8882990413d47b1bab531ec24528489b46381e8664c25`.
- `indexes/semantic_operation_inventory_sample.jsonl`: 35 records; SHA-256 `ad7320bd1a1182128cdf7904280e26479d1a80a5db7c3fcd4c08ac2892576452`.

Both are local ignored representative-sample outputs.

## Extraction gap taxonomy

API-level missing fields in the sample:

- `api_description`: 5.
- `api_title`: 1, caused by the registry-only representation.
- `api_version`: 1, caused by the registry-only representation.
- `protocol`: 1, caused by the registry-only representation.
- `operations`: 1, caused by the registry-only representation.

Operation-level missing fields:

- `description`: 34.
- `operationId`: 34.
- `summary`: 35.

Additional explicit gaps:

- Registry-only APIs cannot yield source-evidenced operations or descriptions.
- The sample contains no unsupported document format, but unsupported syntax remains explicitly defined in the contract.
- No source-representation conflict was observed in the representative sample.

## Parser coverage and unsupported syntax

Supported:

- Swagger 2.0 and OpenAPI 3.x Path Item operations;
- standard HTTP operation methods;
- path-shared and operation parameters;
- Swagger body parameters and OpenAPI request bodies;
- response status/content summaries;
- `$ref` capture without dereferencing.

Not extracted:

- GraphQL fields, SOAP/WSDL operations, AsyncAPI channels;
- OpenAPI callbacks, links, and webhooks;
- APIC assembly policy labels as semantic operations;
- expanded schemas or inferred routes.

## Duplicate, mixed, and multiple representation handling

- Phase 2 canonical identity is the deduplication boundary.
- Exact duplicate source occurrences remain provenance on one API record and do not duplicate operations.
- Accepted source precedence remains authoritative; one accepted root API YAML is parsed once.
- All contributing and authoritative occurrence IDs remain recorded.
- Conflicting accepted representations require an explicit conflict state and architecture review before rollout; none was observed in this sample.
- Registry-only identities remain inventory records with explicit missing states and zero fabricated operations.

## Backend and routing behavior

- API-shared backend observations are present on API records only.
- Operation records retain API-shared observation IDs as context but explicitly deny proven operation egress.
- Operation-scoped observations require exact method and path equality.
- Backend resolution statuses, reasons, token names, source pointers, and Task 011 observation IDs are preserved.
- Raw endpoint hosts and resolved infrastructure values are omitted from committed evidence.

## AS-IS Product/Plan and unresolved evidence

- Product and Plan connections use only accepted `product_contains_api`, `plan_entitles_api`, and `product_contains_plan` relationships.
- These are AS-IS APIC relationships, not Kong Product design.
- The 113 Task 007 unresolved Product-location occurrences remain unresolved and are never silently attached from diagnostic candidates.
- The representative sample includes one such occurrence with status `PRESERVED_UNRESOLVED_NOT_ATTACHED`.

## Files created

- `semantic_inventory/__init__.py`
- `semantic_inventory/__main__.py`
- `semantic_inventory/inventory.py`
- `tests/test_semantic_inventory.py`
- `tests/evidence/task-014/generate_task014_evidence.py`
- `tests/evidence/task-014/semantic_inventory_contract.md`
- `tests/evidence/task-014/sample_selection.json`
- `tests/evidence/task-014/api_sample_review.jsonl`
- `tests/evidence/task-014/operation_sample_review.jsonl`
- `tests/evidence/task-014/coverage_and_gaps.json`
- `tests/evidence/task-014/commands_and_results.txt`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- `.venv/bin/python -m semantic_inventory`.
- `.venv/bin/python tests/evidence/task-014/generate_task014_evidence.py`.
- `.venv/bin/pytest tests/test_semantic_inventory.py -q`.
- `.venv/bin/pytest -q`.
- Python compilation checks.
- `git diff --check`.
- Independent repeated-build byte comparison.
- Frozen Phase 0–4 index and raw `staging/` integrity comparisons.
- Credential, secret-like Catalog Property, JWK/private-key, and URI-host redaction comparisons.

## Test results

- Focused Task 014 tests: **3 passed in 3.06s**.
- Deterministic API and operation output: **PASS**.
- Required sample category coverage: **9 / 9**.
- Operation ID uniqueness: **35 / 35**.
- Backend scope preservation: **PASS**.
- Unresolved Product-location preservation: **PASS**.
- Frozen Phase 0–4 and raw evidence integrity: **PASS**.
- Secret/URI redaction: **PASS**, zero sensitive source values exposed.
- Repository-wide suite: **41 passed, 5 setup errors in 47.87s**. The five setup errors remain the known frozen Phase 0 fixture-packaging issue because `tests/fixtures/repository_profile/staging` is absent. No Task 014 test failed.

## Generated artifacts

- Local ignored: `indexes/semantic_api_inventory_sample.jsonl` and `indexes/semantic_operation_inventory_sample.jsonl`.
- Committed: contract, selection, API review, operation review, coverage/gaps, commands/results, and evidence generator under `tests/evidence/task-014/`.

## Frozen-component integrity

- Phase 0–4 canonical identity, relationship, structural graph, backend, dependency observation, and additive dependency graph indexes are byte-unchanged.
- Raw `staging/` evidence is unchanged.
- No CodeGraph node, edge, relationship taxonomy, backend resolution, or dependency implementation was modified.

## Important findings

- The compact indexes can drive a representative semantic mock with only five targeted source parses.
- Most sampled operations lack operationId, summary, and description; later semantic work must treat source absence explicitly rather than infer meaning from API labels.
- Exact operation-scoped backend evidence is available for 9 sample operations, while API-shared evidence cannot safely establish per-operation egress.
- Registry-only canonical identities require a first-class no-source state.
- Unresolved Product-location evidence can coexist with accepted registry Product/Plan relationships without being silently promoted.

## Unresolved issues and architecture review questions

- Approve or revise the API and operation field contract before estate-wide rollout.
- Decide whether duplicate accepted YAML representations require a separate conflict-comparison report.
- Decide whether callbacks/webhooks and GraphQL/SOAP/AsyncAPI require protocol-specific inventory records.
- Confirm that API-shared backend evidence remains API-only context in later semantic tasks.
- Confirm the missing-description review threshold for later observed-function work.
- Five frozen Phase 0 tests still cannot start because their fixture directory is absent.

## Assumptions

- Phase 2 accepted canonical API identities and source precedence remain authoritative.
- Task 011 scope and resolution outcomes remain authoritative backend evidence.
- Task 008 relationships remain authoritative AS-IS Product/Plan connections.
- Task 007 candidate canonical IDs are diagnostic bridges only and do not authorize occurrence attachment.
- Exact source method/path is sufficient for a factual operation inventory record but not for semantic function inference.

## Deviations from the prompt

None.

## Recommended next step

Integration Architect and Enterprise Architect should review and approve or revise the Task 014 contract, parser coverage, missing-state taxonomy, and representative evidence before any estate-wide semantic extraction or Task 015 work. Task 018 retains its separate mock-test approval gate.

## Final status

HOLD_FOR_ARCHITECTURE_REVIEW
