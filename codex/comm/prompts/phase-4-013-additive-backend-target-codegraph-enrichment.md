# Phase 4 — Task 013: Additive Backend Target CodeGraph Enrichment

## Phase

Phase 4 — Dependency & Runtime-Configuration Resolution

## Task Type

Implementation + Graph Enrichment + Explorer Integration + Evidence Validation

## Architecture Decisions Approved

The Enterprise Architect has approved the following decisions after Task 012 review.

### Canonical backend target

`backend_target` is now an approved canonical graph object type for Phase 4 dependency enrichment.

Reason:

Backend Target identity is architecturally material for APIC→Kong modernization because the estate must distinguish APIs that:

- call backend middleware / wrapper services;
- integrate directly with backend services;
- call external services through the DataPower/DMZ path.

This distinction materially affects TO-BE rationalization and migration decisions.

### Unresolved symbolic targets

A target that remains symbolic/unresolved is still a real dependency and may become a `backend_target` node when the target expression itself is explicit and evidenced.

Examples:

- `$(ace-tip-internal)/external/logwrapperapidata`
- another explicit property-based target whose concrete value is unavailable.

Do not invent the resolved infrastructure value.

### Security provider

Security Provider remains API metadata/attribute only for this phase.

Do NOT create Security Provider graph nodes.

The modernization direction already standardizes future authentication toward Keycloak, and APIC built-in OIDC/OAuth provider details are not required as standalone graph entities for the current TO-BE decision.

Preserve safe provider/security metadata on API/dependency evidence where useful.

### JWT/JWK patterns

The three `jwt-validate.jws-jwk` observations are intentionally omitted from dependency graph enrichment.

They are security implementation detail for current modernization analysis and are not an architecture gap.

Do not create graph nodes/edges from those three observations.

### Configuration references

Catalog/configuration references remain provenance/attributes on backend-target nodes/edges.

Do NOT create Catalog Property or Configuration Reference graph nodes in Task 013.

### Operation scope

Operation scope will be represented as an edge qualifier/provenance attribute on `api_invokes_target`.

Do NOT create Operation nodes in Task 013.

Preserve exact method/path when explicitly proven.

## Objective

Add a dependency layer to the existing frozen CodeGraph without rebuilding or replacing Phase 3 graph artifacts.

Current frozen graph:

- 4,718 canonical structural nodes;
- 9,589 structural edges.

Task 013 must add:

- canonical `backend_target` nodes;
- canonical `api_invokes_target` edges;
- additive dependency adjacency/indexes;
- Explorer support so selecting an API can visibly show which backend target(s) it invokes.

The existing Phase 3 graph remains authoritative and unchanged.

## Critical Additive Rule

Do NOT regenerate or overwrite:

- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`
- `indexes/codegraph_adjacency.jsonl`
- `indexes/relationship_index.jsonl`

Instead create an additive Phase 4 dependency layer.

Recommended local ignored outputs:

- `indexes/codegraph_dependency_nodes.jsonl`
- `indexes/codegraph_dependency_edges.jsonl`
- `indexes/codegraph_dependency_adjacency.jsonl`

The Explorer may load the frozen structural layer plus the additive dependency layer.

## Accepted Inputs

Use compact accepted Phase 4 evidence first:

- `indexes/backend_target_resolution.jsonl`
- `indexes/api_dependency_observations.jsonl`
- `indexes/catalog_properties.jsonl`

Existing frozen graph:

- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`
- `indexes/codegraph_adjacency.jsonl`

Do not reparse backend targets from raw YAML.

Targeted raw YAML may be used only for focused verification of a concrete inconsistency.

## Backend Target Admission Rules

A backend target node may be created only when an accepted Task 011 backend observation provides explicit target evidence.

### Admissible target forms

- fully resolved explicit target;
- static literal target;
- explicit unresolved symbolic target;
- partially resolved target whose remaining symbolic/runtime expression is preserved exactly.

### Not admissible

Do not create a target node from:

- absence of target evidence;
- guessed backend names;
- OAuth/OIDC provider observations;
- JWK/JWT observations;
- hostname similarity alone;
- inferred third-party ownership;
- general server URLs not proven as invocation targets.

## Backend Target Canonical Identity

Canonical identity must preserve the difference between target endpoint/path dependencies.

Do NOT canonicalize solely by host.

### Resolved/static target identity

Use a deterministic normalized dependency identity based on the safe normalized invocation target, including all meaningful structural components available from accepted evidence:

- scheme where present;
- host/value key where safe;
- explicit port;
- normalized path/path template;
- stable query structure only when architecturally meaningful and safely normalized.

Different backend paths must not collapse merely because they share one host.

### Symbolic/unresolved target identity

When concrete resolution is unavailable, construct deterministic identity from the explicit unresolved target expression structure:

- symbolic property token(s);
- static path/path template;
- runtime placeholders;
- relevant target expression normalization.

For example:

```text
$(ace-tip-internal)/external/logwrapperapidata
```

must be representable as a canonical unresolved backend target node without claiming the runtime host value.

### Evidence convergence

Multiple API observations may converge on one backend target node only when their normalized accepted target identity is equal.

Do not merge targets by similar names.

## Backend Target Node Schema

Each `backend_target` node should include compact safe fields such as:

- canonical backend target ID;
- object type = `backend_target`;
- display label;
- target identity kind:
  - `RESOLVED_TARGET`
  - `STATIC_LITERAL_TARGET`
  - `SYMBOLIC_TARGET`
  - `PARTIALLY_RESOLVED_TARGET`
- safe normalized target key;
- safe target/path template;
- symbolic property token(s);
- resolution status;
- evidence state;
- confidence;
- target classification;
- classification evidence/reason;
- source observation count;
- provenance references to Task 011/012 records.

Do not expose protected/secrets/infrastructure values in committed evidence.

## Backend Classification

The Enterprise Architect states that the meaningful modernization target families are:

- `ACE`
- `BACKEND`
- `EXTERNAL_VIA_DATAPOWER`

These are the desired business/architecture classification outcomes.

However, Task 013 must assign one of these only when accepted evidence supports it.

Otherwise use:

- `VALIDATION_REQUIRED`

Do not use Other/Unknown/Misc.

### Evidence requirement

Do not classify based only on a token/name containing words like:

- `ace`;
- `backend`;
- `external`;
- `dp`;
- `datapower`.

Name/token text may be retained as evidence but is not sufficient by itself for canonical classification.

Task 013 must report exact evidence rules used for any automatic classification.

If current evidence cannot safely distinguish all three families, preserve `VALIDATION_REQUIRED` and provide grouping/filtering evidence for architect review.

## api_invokes_target Edge

The existing approved relationship type:

`api_invokes_target`

is now authorized for additive Phase 4 graph enrichment.

Each edge must connect:

```text
canonical api_artifact
    → api_invokes_target
canonical backend_target
```

No new relationship type is required for Task 013.

## Edge Deduplication

Canonical edge identity:

```text
canonical API ID
+ api_invokes_target
+ canonical backend target ID
```

If multiple accepted observations support the same API→target relationship, emit one canonical edge with combined provenance.

Preserve all distinct operation scopes and source observations as qualifiers/provenance.

## Operation Scope on Edge

Each edge must support:

- `API_SHARED`;
- `OPERATION_SCOPED`;
- both, if multiple evidence observations converge on the same API→target edge.

When operation-scoped, preserve exact:

- HTTP method;
- path;
- source pointer;
- observation ID.

Do not infer operations.

Do not create Operation nodes.

## Security Metadata

Security Provider is not a graph node.

Where useful, enrich the API-side review projection with compact safe security metadata derived from Task 012, for example:

- security mechanism present;
- provider/scheme name;
- APIC built-in vs external/Keycloak only if explicitly supported by accepted evidence;
- token/authorization URL resolution state.

Do not expose secrets.

Do not let security metadata alter backend target identity.

## Configuration Provenance

For each backend node/edge, preserve configuration evidence as attributes/provenance:

- exact Catalog Property token names;
- property-resolution status;
- runtime-context token names;
- Task 011 observation IDs;
- Task 012 observation IDs where relevant.

Do not create configuration/property nodes.

## Additive Adjacency

Create dependency adjacency supporting:

- API → backend targets;
- backend target ← APIs;
- filtering by target classification;
- filtering by resolution status;
- filtering by operation scope.

Do not mutate Phase 3 adjacency.

## Explorer Integration

Update Task 010 Explorer additively so the user can select an API and see backend dependencies visually.

Required behavior:

### API view

Show:

```text
API
  → api_invokes_target
  → Backend Target
```

For each backend target display:

- target label/path;
- resolved vs symbolic status;
- classification:
  - ACE
  - BACKEND
  - EXTERNAL_VIA_DATAPOWER
  - VALIDATION_REQUIRED
- operation scope when present;
- property token(s);
- resolution status;
- evidence/provenance drill-down.

### Backend target view

Allow selecting/searching a backend target and seeing:

- APIs that invoke it;
- API count;
- operation scopes;
- target classification;
- resolution state;
- provenance.

### Filters

Add filters for:

- Backend Target node type;
- `api_invokes_target`;
- backend classification;
- resolved vs unresolved/symbolic target;
- API_SHARED vs OPERATION_SCOPED.

### Search

Support search by safe:

- target path/template;
- symbolic property token;
- canonical backend target ID;
- display label.

Do not expose protected infrastructure values.

## Explorer Visual Limits

Retain existing deterministic visual caps.

Dependency-layer rendering must obey the same no-silent-truncation behavior.

Do not attempt full-estate dependency rendering by default.

## Required Generated Outputs

Local ignored:

- `indexes/codegraph_dependency_nodes.jsonl`
- `indexes/codegraph_dependency_edges.jsonl`
- `indexes/codegraph_dependency_adjacency.jsonl`

Recommended optional compact lookup index:

- `indexes/backend_target_lookup.json`

if it materially improves Explorer/query performance.

## Required Evidence Directory

Create and commit:

`tests/evidence/task-013/`

At minimum:

- `backend_target_graph_summary.json`
- `backend_target_classification_summary.json`
- `api_invokes_target_samples.jsonl`
- `backend_target_reuse.json`
- `explorer_dependency_acceptance.json`
- `commands_and_results.txt`

## backend_target_graph_summary.json

Include:

- accepted Task 011 backend observations consumed;
- canonical backend target node count;
- resolved/static/symbolic/partial node counts;
- canonical `api_invokes_target` edge count;
- APIs with at least one backend edge;
- APIs with multiple backend targets;
- backend targets shared by multiple APIs;
- API_SHARED edge count;
- OPERATION_SCOPED edge count;
- missing/orphan endpoint count;
- deduplication/convergence metrics;
- unresolved symbolic node count;
- graph integrity result.

## backend_target_classification_summary.json

Include:

- ACE target nodes;
- BACKEND target nodes;
- EXTERNAL_VIA_DATAPOWER target nodes;
- VALIDATION_REQUIRED target nodes;
- exact automatic classification evidence rules;
- classification coverage;
- representative evidence;
- no name-only inference confirmation.

## api_invokes_target_samples.jsonl

Include deterministic representative samples for:

1. resolved target;
2. static literal target;
3. unresolved symbolic target;
4. partially resolved target;
5. API with multiple targets;
6. operation-scoped target;
7. backend target shared by multiple APIs;
8. VALIDATION_REQUIRED classification;
9. each evidence-supported backend classification family present.

Each sample must include exact API ID, backend target ID, edge ID, scope, observation/provenance IDs, and safe target representation.

## backend_target_reuse.json

Show:

- target nodes referenced by one API;
- target nodes referenced by multiple APIs;
- top shared target counts;
- same-host/different-path separation evidence;
- symbolic-target convergence evidence.

Do not interpret sharing as duplicate capability.

## explorer_dependency_acceptance.json

Prove:

- API can visually show backend target;
- backend target can show invoking APIs;
- filters work;
- symbolic target search works;
- classification filter works;
- operation scope visible;
- provenance drill-down works;
- security provider remains attribute only;
- no JWK/JWT dependency nodes appear;
- no configuration-property nodes appear;
- frozen structural graph counts remain unchanged.

## Required Tests

Add focused tests for:

- resolved backend target canonicalization;
- same host + different path remains different node;
- equivalent target observations converge;
- unresolved symbolic target becomes node;
- different symbolic paths remain distinct;
- API→backend edge creation;
- edge deduplication;
- combined provenance;
- operation scope qualifier preservation;
- multiple operations on one edge;
- no Operation nodes;
- no Security Provider nodes;
- no Catalog Property nodes;
- no JWK/JWT nodes/edges;
- backend classification requires accepted evidence;
- name-only classification is rejected;
- VALIDATION_REQUIRED fallback;
- Explorer API→backend rendering;
- Explorer backend→API reverse rendering;
- dependency filters/search;
- credential/secret redaction;
- deterministic repeated build;
- frozen Task 009 graph hashes unchanged;
- frozen Task 008 relationship index unchanged;
- raw `staging/` unchanged.

## Token / Performance Rule

Normal backend dependency review must use:

```text
dependency graph indexes
→ Task 011/012 compact observation indexes
→ targeted source only for verification
```

Do not rescan all raw YAML for Explorer queries.

Reuse existing Phase 4 caches where possible.

## Frozen Components

Phase 0 through Task 012 are frozen.

Task 013 is additive only.

Do not reopen frozen logic absent a concrete reproducible defect.

## Explicit Non-Goals

Task 013 must NOT:

- rebuild Phase 3 CodeGraph;
- overwrite structural graph indexes;
- create Operation nodes;
- create Security Provider nodes;
- create Catalog Property/Configuration Reference nodes;
- graph JWT/JWK patterns;
- infer runtime traffic/actual consumption;
- perform duplicate/overlap analysis;
- recommend retirement;
- rationalize API Products;
- design Kong Services/Routes;
- map APIC directly to Kong;
- design migration waves.

## HANSOFF Reporting

Update only `codex/comm/HANSOFF.md` for prose reporting.

HANSOFF must report:

1. implementation files created/modified;
2. exact additive graph index paths;
3. canonical backend target node count;
4. target counts by identity kind;
5. `api_invokes_target` edge count;
6. API coverage;
7. shared backend target findings;
8. operation-scope findings;
9. classification counts for ACE/BACKEND/EXTERNAL_VIA_DATAPOWER/VALIDATION_REQUIRED;
10. exact classification evidence rules;
11. unresolved symbolic-node findings;
12. same-host/different-path identity validation;
13. Explorer changes and exact run command;
14. API→backend visual example;
15. backend→API reverse example;
16. security-provider attribute behavior;
17. confirmation no Security Provider/Config/JWK nodes were created;
18. credential redaction result;
19. deterministic build result;
20. focused and repository-wide tests;
21. confirmation Phase 3 graph indexes are byte-unchanged;
22. evidence files under `tests/evidence/task-013/`;
23. architecture findings requiring future validation;
24. final status: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 013 is complete only when:

- canonical `backend_target` nodes are built deterministically from accepted evidence;
- unresolved symbolic targets are represented without fabricated runtime values;
- `api_invokes_target` edges are created additively;
- operation scope is preserved as edge qualifier/provenance;
- security provider remains attribute only;
- JWK/JWT and configuration references are not graph nodes;
- backend classification is evidence-based or VALIDATION_REQUIRED;
- frozen structural CodeGraph remains unchanged;
- Explorer visibly supports API↔Backend review;
- no secrets are exposed;
- output is deterministic;
- required evidence is committed.

## Stop Condition

Implement and validate Phase 4 Task 013 only.

Update `codex/comm/HANSOFF.md`, commit implementation/tests/evidence/handoff changes, push, and stop.

Do not begin duplicate analysis, runtime analytics enrichment, rationalization, migration planning, or Kong design.
