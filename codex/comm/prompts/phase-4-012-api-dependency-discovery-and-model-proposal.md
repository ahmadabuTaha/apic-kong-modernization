# Phase 4 — Task 012: API Dependency Discovery & Model Proposal

## Phase

Phase 4 — Dependency & Runtime-Configuration Resolution

## Task Type

Implementation + Evidence Discovery + Architecture Model Proposal

## Objective

Extend Phase 4 beyond backend target resolution and build an evidence-based inventory of the dependency patterns actually present in the APIC API estate.

Task 012 must discover and classify observed API dependencies such as:

- backend invocation targets already resolved/indexed by Task 011;
- OAuth2/OIDC/security-provider dependencies;
- token, introspection, authorization, issuer, JWKS, or related security endpoints where explicitly present;
- explicit third-party/external HTTP dependencies;
- symbolic/configuration dependencies;
- other dependency mechanisms only when directly evidenced by the corpus.

The task must produce a **dependency observation index and an architecture model proposal**.

It must NOT yet create canonical dependency nodes or CodeGraph edges.

## Architecture Boundary

Task 011 proved that a single API may contain:

- one or more invoke targets;
- symbolic Catalog Property references;
- runtime parameters;
- operation-scoped targets.

The project also expects OAuth2/OIDC and third-party dependencies to exist in some API definitions.

However, the approved canonical taxonomy does not yet define dependency object types beyond the existing relationship placeholders.

Therefore Task 012 must separate:

```text
OBSERVED EVIDENCE
from
PROPOSED DEPENDENCY MODEL
from
APPROVED CANONICAL MODEL
```

Only the first two are in scope.

Do not treat the proposal as approved canonical truth.

## Accepted Inputs

Prefer compact accepted/generated evidence first:

- `indexes/backend_target_resolution.jsonl`
- `indexes/catalog_properties.jsonl`
- `indexes/apic_identity_resolution.json`
- `indexes/extracted_records.jsonl`
- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`

Local supplemental configuration:

- `staging/config/catalog-properties.json`

Targeted API YAML under `staging/` may be inspected only when required for dependency mechanisms not already represented in compact indexes.

## Reuse / Token-Efficiency Rule

Do NOT re-extract Task 011 backend target evidence from raw YAML.

Reuse:

`indexes/backend_target_resolution.jsonl`

as the accepted source for backend invocation observations.

For additional security/provider/third-party dependency discovery:

```text
canonical API
→ compact accepted occurrence/source pointer
→ cache lookup
→ targeted YAML read only on cache miss
```

Do not repeatedly summarize whole API YAML files into LLM context.

## Lightweight Cache

Create a separate disposable Phase 4 dependency-discovery cache, recommended:

`indexes/cache/phase4_dependency_discovery_cache.sqlite3`

Use Python standard-library SQLite unless a simpler deterministic standard-library mechanism is demonstrably better.

Cache keying must include at minimum:

- source path;
- source SHA-256;
- parser/schema version;
- relevant dependency-parser version.

Reuse unchanged parsed results on warm runs.

Do not modify Task 011 cache schema or implementation unless a concrete defect requires it.

Do not commit the cache.

## Discovery First — No Assumed APIC Shape

Do not assume OAuth/OIDC/security dependencies use one standard YAML structure.

Before classifying them, build an observed-pattern inventory from the corpus.

For each dependency-bearing structure capture:

- YAML path / JSON pointer pattern;
- policy/section name;
- field names;
- value shape;
- number of APIs using the pattern;
- number of observations;
- whether deterministic extraction is supported;
- representative source pointers.

Examples of contexts that MAY appear, only if actually observed:

- security definitions/schemes;
- OAuth2/OIDC provider definitions;
- issuer fields;
- authorization/token endpoints;
- introspection endpoints;
- JWKS/JWK endpoints;
- invoke-like security calls;
- assembly policies;
- configuration/property references.

Do not infer unsupported mechanisms from APIC documentation or general product knowledge.

The local corpus is authoritative for this task.

## Dependency Observation Classes

The task may use the following **observation classes** for evidence reporting only:

- `BACKEND_INVOCATION`
- `SECURITY_PROVIDER`
- `EXTERNAL_HTTP_DEPENDENCY`
- `CONFIGURATION_REFERENCE`
- `UNCLASSIFIED_DEPENDENCY_PATTERN`

These are observation/reporting classes, NOT approved canonical object types.

Use `UNCLASSIFIED_DEPENDENCY_PATTERN` only when the mechanism is evidenced but cannot be safely assigned to another class, and include a precise reason such as:

- `unclassified_due_to_unsupported_security_scheme_shape`;
- `unclassified_due_to_ambiguous_policy_context`;
- `unclassified_due_to_dynamic_runtime_expression`.

Do not use vague Other/Misc/Unknown labels.

## Context Determines Meaning

Do not classify a dependency solely from hostname or URL text.

Examples:

- a URL inside an invoke target context may be a backend/external invocation;
- a URL inside OAuth/OIDC provider configuration is a security-provider dependency;
- a Catalog Property token is a configuration dependency;
- the same hostname may appear in more than one dependency role.

Dependency class must derive from source context and explicit evidence.

## Backend Invocation Reuse

Import Task 011 target observations without reparsing them.

Preserve at minimum:

- canonical API ID;
- operation/API scope;
- original target expression;
- symbolic property references;
- resolved target expression where safe;
- target classification;
- resolution status;
- source provenance.

Task 012 must not reinterpret Task 011 RESOLVED/UNRESOLVED outcomes.

## Security Dependency Discovery

Discover explicit security-provider dependencies actually present in the API definitions.

Preserve, where evidenced:

- security mechanism type;
- provider/scheme name;
- issuer;
- authorization endpoint;
- token endpoint;
- introspection endpoint;
- JWKS/JWK endpoint;
- scopes/flow metadata only where structurally useful and safe;
- property/context references;
- source scope;
- source pointer;
- API or operation scope where explicitly defined.

Do not expose secrets, client credentials, tokens, or private key material.

If a provider is identified by name but its concrete endpoint is absent, preserve it as a named/provider reference without inventing an endpoint.

If APIC built-in/provider-local configuration differs from external OIDC/OAuth, preserve the observed distinction only when evidence supports it.

## External / Third-Party Dependency Discovery

Identify explicit external HTTP dependency observations only from accepted configuration context.

Do not label something “third-party” merely because its hostname differs.

Use source evidence and available configuration context.

If ownership cannot be proven, report it as:

`EXTERNAL_HTTP_DEPENDENCY` + `ownership_validation_required`

rather than asserting third-party ownership.

## Configuration Dependency Discovery

Index dependency-relevant symbolic tokens, especially those used by:

- backend targets;
- security-provider fields;
- endpoint expressions;
- dependency-bearing policies.

Reuse Task 011 Catalog Property index where possible.

Preserve:

- exact property/token name;
- resolved/unresolved status;
- count of APIs using it;
- dependency contexts in which it appears.

Do not create canonical Catalog Property nodes yet.

## Required Generated Outputs

Local ignored generated outputs:

- `indexes/api_dependency_observations.jsonl`
- `indexes/dependency_pattern_inventory.json`
- `indexes/cache/phase4_dependency_discovery_cache.sqlite3`

### api_dependency_observations.jsonl

Each record should include at minimum:

- deterministic observation ID;
- canonical API ID;
- API name/version where available;
- API/shared/operation scope;
- method/path when explicitly proven;
- observation class;
- mechanism/policy/security-scheme name;
- dependency role;
- safe raw expression/value reference;
- resolved safe endpoint/target where supported;
- referenced Catalog Properties/context tokens;
- resolution status;
- evidence state;
- confidence;
- source path;
- source pointer;
- source SHA-256;
- originating accepted index record ID where reused.

Do not duplicate equivalent observations produced from the same source/context.

## Dependency Pattern Inventory

Produce an exhaustive observed inventory grouped by exact mechanism/context.

For every observed pattern report:

- exact YAML/JSON path pattern;
- mechanism name;
- observation class;
- parser support status;
- API count;
- observation count;
- resolution-state counts;
- representative source pointers;
- whether the pattern was reused from Task 011 or newly parsed in Task 012.

## Architecture Model Proposal

Create committed architecture-review evidence:

`tests/evidence/task-012/dependency_model_proposal.md`

The proposal must be derived from actual observed evidence.

It must clearly separate:

### Observed dependency concepts
What was actually found.

### Proposed canonical object candidates
For example, only if justified by evidence:
- dependency endpoint;
- security provider;
- configuration reference;
- backend target.

### Proposed relationship candidates
For example, only if justified:
- API/operation invokes target;
- API uses security provider;
- dependency uses configuration property.

### Scope problem
Explain API-level vs operation-level dependency modeling.

### Identity strategy
Propose how endpoint/provider identity could be constructed without conflating:
- same hostname/different paths;
- same provider/different endpoints;
- symbolic vs resolved targets;
- environment-specific values.

### Evidence/provenance rules
Define what would qualify a proposed node/relationship for future graph enrichment.

### Explicit unresolved architecture questions
List decisions requiring Enterprise/Integration Architect approval.

Do NOT implement the proposed taxonomy in Task 012.

## Coverage Accounting

Account for all 2,036 canonical APIs.

Report:

- APIs represented by Task 011 backend observations;
- APIs with security-provider observations;
- APIs with external HTTP dependency observations;
- APIs with configuration-reference observations;
- APIs with multiple dependency classes;
- APIs with no dependency observation in supported patterns;
- operation-scoped dependency observations;
- API/shared dependency observations;
- total observations by class;
- unresolved observations by exact reason.

Avoid double-counting one evidence item across classes unless the record explicitly models separate roles.

## Cross-Dependency Correlation

Generate safe observational metrics such as:

- number of APIs sharing the same security-provider reference;
- number of APIs sharing the same Catalog Property token;
- number of APIs sharing the same resolved endpoint key;
- number of APIs with both backend and security dependencies;
- number of APIs with multiple backend targets;
- number of APIs with operation-specific dependencies.

These are correlation metrics only.

Do not interpret shared dependency as duplicate business capability.

## Performance Requirements

Measure cold and warm dependency discovery.

Target behavior:

- Task 011 backend observations loaded from compact index, not reparsed;
- unchanged YAML security/dependency patterns served from SQLite cache;
- warm run reparses zero unchanged API files;
- deterministic output byte identity across cold/warm runs.

Report timing and cache hit/miss counts.

## Security / Redaction

Never emit:

- OAuth client secrets;
- passwords;
- API keys;
- bearer tokens;
- private keys;
- credential payload values;
- sensitive protected Catalog Property values.

URLs containing user-info credentials must be safely redacted.

Security tests must inspect generated local indexes and committed evidence.

## Required Evidence Directory

Create and commit:

`tests/evidence/task-012/`

At minimum:

- `dependency_summary.json`
- `dependency_pattern_inventory.json`
- `dependency_samples.jsonl`
- `dependency_correlation.json`
- `dependency_model_proposal.md`
- `cache_performance.json`
- `commands_and_results.txt`

## Required Samples

Include representative evidence for, where present:

1. backend invocation reused from Task 011;
2. Catalog Property-based configuration dependency;
3. OAuth2/OIDC/security-provider dependency;
4. explicit security endpoint;
5. external HTTP dependency;
6. API with more than one dependency class;
7. operation-scoped dependency;
8. unresolved dependency;
9. unclassified dependency pattern with precise reason.

If a category is not present in the corpus, state zero observed rather than fabricating a sample.

## Required Tests

Add focused tests for:

- Task 011 backend observation reuse without raw target reparsing;
- security-provider pattern extraction;
- OAuth/OIDC endpoint extraction for observed shapes;
- named provider without endpoint;
- configuration-reference extraction;
- external HTTP dependency classification from context;
- no hostname-only third-party inference;
- operation-scope preservation;
- exact provenance;
- deterministic deduplication;
- unresolved-pattern handling;
- secret/credential redaction;
- cold cache build;
- warm cache reuse;
- selective source invalidation;
- byte-identical logical outputs;
- all 2,036 APIs accounted for;
- no modification to Task 011 outputs;
- no modification to Task 008 relationships;
- no modification to Task 009 CodeGraph;
- no modification to Task 010 Explorer;
- raw `staging/` unchanged.

## Frozen Components

Phase 0 through Task 011 are frozen.

Task 012 may consume their outputs but must not redesign or rewrite them absent a concrete reproducible defect.

## Explicit Non-Goals

Task 012 must NOT:

- create canonical dependency nodes;
- create backend/security-provider/catalog-property nodes in CodeGraph;
- emit new graph relationship types;
- modify approved relationship taxonomy;
- rebuild the CodeGraph;
- change Task 011 resolution outcomes;
- infer runtime traffic or actual consumption;
- infer third-party ownership from URL alone;
- perform duplicate/overlap analysis;
- recommend retirement;
- rationalize APIs/Products;
- design Kong Services/Routes;
- map APIC directly to Kong;
- design migration waves.

## HANSOFF Reporting

Update only `codex/comm/HANSOFF.md` for prose reporting.

HANSOFF must report:

1. implementation structure;
2. exact generated dependency indexes/cache;
3. all 2,036 API coverage;
4. observation counts by class;
5. observed security/OAuth/OIDC patterns;
6. external HTTP dependency findings;
7. configuration-reference findings;
8. operation vs API/shared scope counts;
9. unresolved/unclassified counts by precise reason;
10. correlation metrics;
11. cold/warm cache performance;
12. confirmation Task 011 backend observations were reused rather than reparsed;
13. credential/secret redaction;
14. frozen-component integrity;
15. evidence files;
16. proposed dependency object candidates;
17. proposed relationship candidates;
18. unresolved architecture decisions;
19. whether evidence is sufficient to authorize a later CodeGraph dependency-enrichment task;
20. final status: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 012 is complete only when:

- dependency patterns are discovered from the actual corpus;
- Task 011 backend target evidence is reused;
- security/provider and other supported dependency evidence is indexed deterministically;
- source context determines dependency meaning;
- operation scope is preserved;
- no canonical dependency taxonomy is silently introduced;
- all 2,036 APIs are accounted for;
- cache reduces repeated YAML parsing;
- output is deterministic;
- no secrets are exposed;
- architecture model proposal is evidence-based;
- frozen CodeGraph and earlier indexes remain unchanged;
- HANSOFF provides enough evidence for an architecture decision on future CodeGraph enrichment.

## Stop Condition

Implement and validate Phase 4 Task 012 only.

Update `codex/comm/HANSOFF.md`, commit implementation/tests/evidence/handoff changes, push, and stop.

Do not begin CodeGraph dependency enrichment, duplicate analysis, runtime analytics enrichment, rationalization, migration planning, or Kong design.
