# Codex Handoff

## Task executed

Phase 4 — Task 012: API Dependency Discovery & Model Proposal.

## Prompt file used

`codex/comm/prompts/phase-4-012-api-dependency-discovery-and-model-proposal.md`

## Summary of what was done

- Built a deterministic dependency-observation index from accepted evidence while keeping observed evidence separate from proposed and approved architecture.
- Reused all Task 011 backend observations from the compact index without reparsing raw invoke targets or changing Task 011 outcomes.
- Target-read accepted API YAML only for security-provider, explicit security-endpoint, non-invoke HTTP-policy, and unsupported JWT/JWK patterns.
- Indexed exact Catalog Property and runtime-context references from dependency-bearing expressions.
- Added a separate disposable SQLite cache for Task 012 parsing and proved cold/warm output identity.
- Produced corpus-derived architecture-review evidence without creating dependency nodes, graph edges, or an approved taxonomy.
- Preserved explicit unresolved states, operation scope, provenance, and credential redaction.

## Implementation structure

- `dependency_discovery/discovery.py`: Task 011 reuse, targeted pattern parsing, safe reference resolution, redaction, deterministic observation/pattern indexes, correlation, coverage, and SQLite caching.
- `dependency_discovery/__init__.py`: public Task 012 API.
- `dependency_discovery/__main__.py`: `python -m dependency_discovery` entry point.
- `tests/test_dependency_discovery.py`: focused extraction, reuse, scope, provenance, redaction, cache, determinism, full-corpus coverage, and frozen-integrity tests.
- `tests/evidence/task-012/generate_dependency_evidence.py`: deterministic architecture-review evidence and cold/warm performance generator.

## Generated dependency indexes and cache

- `indexes/api_dependency_observations.jsonl`: 8,814 records; SHA-256 `0bdd8e1930fc3ef6756c2ec4515d8dcb23dcc7d26be747faf9620240b0bfe4f0`.
- `indexes/dependency_pattern_inventory.json`: SHA-256 `c6ed5fa72c949c0dc03b10b5f53e6bae9695f32ee602ff455280999e6f3cdaee`.
- `indexes/cache/phase4_dependency_discovery_cache.sqlite3`: disposable SQLite cache using schema `phase4-dependency-cache-v1` and parser version `phase4-dependency-parser-v2`.

These generated artifacts are local and ignored. The cache contains sanitized parsed candidates and never stores observed JWK/private-key material.

## Canonical API coverage

- Total canonical APIs accounted for: 2,036 / 2,036.
- APIs represented by Task 011 backend observations: 1,978.
- APIs with security-provider observations: 1,164.
- APIs with external HTTP dependency observations: 1.
- APIs with configuration-reference observations: 1,960.
- APIs with multiple dependency classes: 1,966.
- APIs with no observation in supported dependency patterns: 52.
- APIs without an accepted YAML source: 36.

Absence of a supported observation is evidence absence, not proof that an API has no dependency.

## Observation counts by class

- `BACKEND_INVOCATION`: 2,334.
- `SECURITY_PROVIDER`: 2,329.
- `CONFIGURATION_REFERENCE`: 4,147.
- `EXTERNAL_HTTP_DEPENDENCY`: 1.
- `UNCLASSIFIED_DEPENDENCY_PATTERN`: 3.
- Total: 8,814.

These are reporting classes only, not canonical object types.

## Observed security/OAuth/OIDC patterns

- Swagger 2 OAuth2 security definitions: 1,161 named/provider-reference observations.
- Swagger 2 OAuth2 `tokenUrl`: 1,161 observations; 112 resolved and 1,049 unresolved/parameterized.
- Swagger 2 OAuth2 `authorizationUrl`: 1 unresolved/parameterized observation.
- OpenAPI 3 OAuth2 security schemes: 3 provider-reference observations.
- OpenAPI 3 client-credentials `tokenUrl`: 3 unresolved/parameterized observations.
- No supported issuer, introspection, OpenID discovery, or JWKS URL endpoint pattern was observed.
- Three `jwt-validate.jws-jwk` configurations were retained as `UNCLASSIFIED_DEPENDENCY_PATTERN` with reason `unclassified_due_to_unsupported_security_scheme_shape`; their raw values were not persisted.
- API-key schemes were inventoried as non-dependency security schemes and did not become dependency observations.

## External HTTP dependency findings

- One explicit non-`invoke` `websocket-upgrade.target-url` observation was classified from policy context as `EXTERNAL_HTTP_DEPENDENCY`.
- Ownership was not inferred from hostname and remains `ownership_validation_required`.
- General server URLs were not classified as third-party dependencies.

## Configuration-reference findings

- Total configuration-reference observations: 4,147 across 1,960 APIs.
- Distinct exact configuration tokens: 442.
- Tokens shared by multiple APIs: 262.
- Maximum APIs sharing one token: 1,032.
- Catalog Property and runtime-context tokens remain observations only; no canonical property nodes were created.

## Scope findings

- API/shared observations: 8,616.
- Operation-scoped observations: 198 across 7 APIs.
- Operation-scoped method/path evidence was preserved from Task 011 rather than flattened to API scope.

## Unresolved and unclassified observations

- `partially_resolved_target_expression`: 719.
- `runtime_context_reference`: 653.
- `unclassified_due_to_unsupported_security_scheme_shape`: 3.
- `unresolved_due_to_missing_catalog_property`: 1,460.
- `unresolved_due_to_protected_catalog_property_value`: 22.
- `unresolved_due_to_runtime_parameterization`: 3.
- `unresolved_or_parameterized_dependency_reference`: 1,053.

Counts include separate configuration-reference roles derived from the same dependency-bearing context where those roles are explicitly modeled.

## Correlation metrics

- APIs with both backend and security dependencies: 1,158.
- APIs with multiple backend targets: 133.
- APIs with operation-scoped dependencies: 7.
- Distinct security-provider references: 3; 2 are shared by multiple APIs; maximum sharing is 1,141 APIs.
- Distinct configuration tokens: 442; 262 are shared by multiple APIs; maximum sharing is 1,032 APIs.
- Distinct safe normalized endpoint keys: 1,151; 159 are shared by multiple APIs; maximum sharing is 1,141 APIs.

Shared dependencies are structural correlation only and do not establish duplicate business capability or runtime use.

## Cache performance and Task 011 reuse

- Cold build: 5.178551 seconds; 2,000 YAML files parsed; 0 hits; 2,000 misses.
- Warm build: 0.644148 seconds; 0 unchanged files reparsed; 2,000 hits; 0 misses.
- Cold and warm dependency indexes were byte-identical.
- Cold and warm pattern inventories were byte-identical.
- Task 011 backend records loaded from compact index: 2,334.
- Task 011 backend target YAML reparses: 0.
- Selective one-source invalidation reparsed only the changed source in focused tests.

## Credential and secret redaction

- Generated local indexes, the SQLite cache, committed evidence, and this handoff were compared with source credential values, secret-like Catalog Property values, and observed JWK/private-key material.
- Zero sensitive source values were exposed.
- URL user-info and secret query components are sanitized; protected/redacted values remain unresolved.

## Frozen-component integrity

- Phase 0 through Task 011 implementations were not modified.
- Task 011 backend/property indexes were unchanged.
- Task 008 relationship index was unchanged.
- Task 009 CodeGraph node, edge, and adjacency indexes were unchanged.
- Task 010 Explorer was unchanged.
- Raw `staging/` evidence was unchanged.
- No canonical dependency nodes, relationship types, or graph edges were created.

## Files created

- `dependency_discovery/__init__.py`
- `dependency_discovery/__main__.py`
- `dependency_discovery/discovery.py`
- `tests/test_dependency_discovery.py`
- `tests/evidence/task-012/generate_dependency_evidence.py`
- `tests/evidence/task-012/dependency_summary.json`
- `tests/evidence/task-012/dependency_pattern_inventory.json`
- `tests/evidence/task-012/dependency_samples.jsonl`
- `tests/evidence/task-012/dependency_correlation.json`
- `tests/evidence/task-012/dependency_model_proposal.md`
- `tests/evidence/task-012/cache_performance.json`
- `tests/evidence/task-012/commands_and_results.txt`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- Cold and warm full-corpus dependency discovery builds.
- `.venv/bin/pytest tests/test_dependency_discovery.py -q`.
- `.venv/bin/pytest -q`.
- Python compilation checks.
- `git diff --check`.
- Frozen index and raw `staging/` integrity checks.
- Credential, secret-like Catalog Property, and JWK/private-key material comparisons.

## Test results

- Focused Task 012 tests: **3 passed in 8.75s**.
- Evidence generation: **PASS**; 9 required representative samples produced.
- Canonical API coverage: **2,036 / 2,036 accounted for**.
- Cache reuse and deterministic output: **PASS**.
- Secret redaction: **PASS**, zero sensitive source values exposed.
- Frozen components and raw evidence: **unchanged**.
- Repository-wide suite: **35 passed, 5 setup errors in 31.80s**. The five setup errors remain the known frozen Phase 0 fixture-packaging issue because `tests/fixtures/repository_profile/staging` is absent. No Task 012 test failed.

## Generated artifacts

- Local ignored: `indexes/api_dependency_observations.jsonl`, `indexes/dependency_pattern_inventory.json`, and `indexes/cache/phase4_dependency_discovery_cache.sqlite3`.
- Committed: the seven required evidence files under `tests/evidence/task-012/`, plus the deterministic evidence generator.

## Proposed dependency object candidates

Pending explicit architecture approval, the evidence supports considering: Dependency Endpoint, Security Provider, Configuration Reference, and Backend Target. These are proposal candidates only and were not implemented as canonical types.

## Proposed relationship candidates

Pending explicit approval, the evidence supports considering: API/operation invokes target, API/operation uses security provider, security provider exposes a role-qualified endpoint, and dependency observation uses configuration reference. No relationship was emitted in Task 012.

## Important findings

- Security-definition context produces material provider/endpoint evidence across 1,164 APIs, but endpoint presence and resolution vary substantially.
- Operation scope is material and requires an explicit canonical modeling decision before graph enrichment.
- Symbolic references and resolved environment values must remain distinct when evidence is missing, protected, or runtime-parameterized.
- The same endpoint/provider/token can be shared by many APIs; sharing is not evidence of duplicate capability.
- No frozen-component defect was found.

## Unresolved architecture decisions and issues

- Decide whether operation scope is modeled as nodes, edge qualifiers, or provenance-only data.
- Approve or reject each proposed dependency object and relationship candidate.
- Define environment/catalog identity requirements for providers and endpoints.
- Decide whether unresolved symbolic targets may become graph nodes.
- Define provider-to-multiple-endpoint-role modeling.
- Decide whether configuration references are nodes or relationship provenance.
- Define the admission threshold for external dependency candidates whose ownership is unvalidated.
- Define safe representation rules for protected references.
- Five frozen Phase 0 tests still cannot start because their fixture directory is absent.

## Assumptions

- Phase 2 accepted source pointers identify the authoritative API YAML eligible for targeted Task 012 parsing.
- Task 011 target classifications and resolution states are authoritative and must be preserved.
- Exact context, not hostname text, determines observation class.
- Safe normalized endpoint keys are correlation keys only, not approved canonical identities.
- The 36 canonical APIs without accepted YAML remain accounted for but cannot yield newly parsed dependency patterns.

## Deviations from the prompt

None.

## Evidence sufficiency for later CodeGraph enrichment

The evidence is sufficient for Integration and Enterprise Architects to decide the dependency taxonomy, identity, scope, and admission rules. It is **not sufficient by itself to authorize a later CodeGraph dependency-enrichment implementation**; explicit architecture approval is required first.

## Recommended next step

Review and decide the proposed dependency objects, relationships, identity rules, operation-scope representation, protected-reference policy, and evidence thresholds. Do not start graph enrichment until those decisions are approved and `CURRENT_TASKS.md` is updated externally.

## Final status

HOLD_FOR_ARCHITECTURE_REVIEW
