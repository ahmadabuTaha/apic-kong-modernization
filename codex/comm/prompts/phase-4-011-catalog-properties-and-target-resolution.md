# Phase 4 — Task 011: Catalog Properties Indexing & Target Resolution Foundation

## Phase

Phase 4 — Dependency & Runtime-Configuration Resolution

## Task Type

Implementation + Evidence Validation

## Objective

Establish the first deterministic Phase 4 dependency-resolution layer by:

1. indexing the locally supplied APIC Catalog Properties evidence;
2. introducing a lightweight local cache for repeated deterministic lookups;
3. resolving symbolic backend references in API YAML only when the property evidence supports them;
4. producing an architecture-reviewable target-resolution index without yet modifying the frozen CodeGraph.

This task begins Phase 4.

Phase 3 is accepted as structurally complete through Task 010:
canonical identities → structural relationships → CodeGraph → visual explorer.

## New Authoritative Supplemental Evidence

A new local source exists at:

`staging/config/catalog-properties.json`

It is intentionally local and ignored by Git.

Expected shape:

```json
{
  "catalogProperties": [
    {
      "name": "ace-tip-internal",
      "value": "ip:port",
      "protected": ""
    }
  ]
}
```

Do not assume all records have identical values, naming patterns, protection flags, or formatting beyond what is actually observed.

The file must be inspected and parsed from the local working tree at execution time.

If the file is absent, malformed, or materially different from the expected top-level structure, stop with explicit evidence and mark HOLD_FOR_ARCHITECTURE_REVIEW rather than inventing fallback values.

## Critical Evidence Rule

A YAML expression such as:

```yaml
target-url: $(ace-tip-internal)/external/logwrapperapidata
```

must be resolved only through exact property evidence.

Resolution pattern:

```text
target expression
→ exact symbolic token: ace-tip-internal
→ exact property-name lookup
→ property value
→ resolved target expression
```

Do not infer that `ace-tip-internal` is IBM ACE merely because its name contains `ace`.

The property file proves configuration values, not business capability or product ownership.

## Phase 4 Scope for Task 011

Task 011 is intentionally narrower than the full dependency model.

It covers:

- Catalog Property indexing;
- symbolic property lookup;
- APIC invoke/target URL extraction;
- target expression resolution where supported;
- unresolved/dynamic target preservation;
- lightweight content-addressed local caching;
- coverage and pattern inventory.

It does NOT yet fully model:

- OAuth2/OIDC provider dependencies;
- JWKS/introspection dependencies;
- third-party dependency taxonomy;
- canonical backend objects;
- CodeGraph dependency nodes/edges.

Those can be informed by findings from this task and handled by later Phase 4 tasks.

## Accepted Inputs

Primary structural inputs:

- `indexes/apic_identity_resolution.json`
- `indexes/extracted_records.jsonl`
- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`

New supplemental configuration evidence:

- `staging/config/catalog-properties.json`

Targeted API YAML under `staging/` may be read using accepted source pointers.

Do not perform repeated full-corpus raw scans once a deterministic source/file cache exists.

## Lightweight Local Cache — Required

The implementation must include a lightweight cache optimized for repeated local execution on a Mac M2.

Preferred approach: Python standard library + SQLite.

Recommended local ignored cache:

`indexes/cache/phase4_resolution_cache.sqlite3`

No new external database or server.

The cache must be rebuildable and disposable.

### Cache design

At minimum cache:

- source file path;
- source file SHA-256;
- parser/schema version;
- parsed API target observations;
- parsed symbolic property references;
- property lookup results;
- normalized target components;
- resolution results.

A cached record is reusable only when:

```text
source SHA-256 + parser version + relevant property-file SHA-256
```

still match.

If any relevant fingerprint changes, invalidate only affected records.

Do not invalidate/reparse the entire corpus unnecessarily.

### Cache safety

- Do not modify `.gitignore`.
- Keep cache under an already ignored generated path such as `indexes/`.
- Do not commit the SQLite cache.
- Do not persist raw protected secret values.
- Do not persist client secrets, API keys, tokens, passwords, or private keys.
- Cache must be reproducible from accepted local evidence.

### Token-efficiency objective

Normal repeated work should follow:

```text
compact indexes / SQLite cache
→ accepted canonical identity
→ cached target observations
→ property index
→ targeted raw YAML only when cache miss or source hash changed
```

Do not repeatedly load or summarize entire API YAML files into LLM context.

The implementation should enable Codex to answer targeted questions through compact generated records rather than re-reading raw source.

## Catalog Property Index

Produce a deterministic local ignored property index, recommended:

`indexes/catalog_properties.jsonl`

Each property record should include at minimum:

- deterministic property ID;
- exact property name;
- normalized lookup name;
- value classification;
- protected flag/value state;
- safe value when non-protected and non-secret;
- source file;
- source JSON pointer/index;
- source-file SHA-256;
- evidence state;
- confidence.

### Property uniqueness

For each property name classify lookup cardinality:

- unique exact value;
- repeated same value;
- conflicting multiple values;
- protected/unavailable value;
- malformed record.

Do not silently choose one value when multiple conflicting values exist.

If no environment/catalog scope exists in the file, do not invent one.

## Sensitive Property Handling

The property file may contain sensitive data.

Never emit committed evidence containing:

- passwords;
- client secrets;
- API keys;
- tokens;
- private keys;
- credentials embedded in URLs.

If `protected` indicates a protected property, do not persist its raw value into generated committed evidence.

If a non-protected record appears secret-like by name or structure, redact it conservatively and record the reason.

The local ignored property index may contain safe non-secret infrastructure values such as host/IP/port references where allowed, but committed evidence should prefer structural summaries over unnecessary raw infrastructure values.

## Target Observation Extraction

Inspect accepted API YAML source artifacts for explicit invocation evidence.

At minimum support observed `invoke.target-url` structures.

Do not assume all YAML files use one standard shape.

Build an observed target/policy pattern inventory first and support only patterns actually present.

For each observation capture:

- canonical API ID;
- API name/version where available;
- source path;
- source pointer;
- operation scope if explicitly proven;
- policy/mechanism name;
- invoke title where present;
- HTTP verb where present;
- configured `backend-type` where present;
- original safe target expression;
- symbolic tokens referenced;
- path suffix/template;
- static/dynamic/parameterized classification.

## Symbolic Resolution

For each expression containing exact APIC-style property tokens such as:

`$(property-name)`

perform exact property-name lookup.

### If exactly one safe value is proven

Resolve deterministically.

Example:

```text
$(ace-tip-internal)/external/logwrapperapidata
+
ace-tip-internal = ip:port
=
ip:port/external/logwrapperapidata
```

Preserve both:
- original expression;
- resolved expression.

### If property is missing

Status:
`UNRESOLVED`

Reason:
`unresolved_due_to_missing_catalog_property`

### If property has conflicting values without usable scope

Status:
`AMBIGUOUS`

Reason:
`ambiguous_due_to_conflicting_catalog_property_values`

### If property exists but is protected/redacted

Do not expose the value.

Use a precise state/reason such as:

`unresolved_due_to_protected_catalog_property_value`

unless safe deterministic resolution can occur without revealing the protected value.

### If runtime/context tokens remain

Keep the observation parameterized and unresolved for the unresolved portion.

Do not fabricate a concrete target.

## Target Classification

Classify target form precisely, for example:

- `STATIC_LITERAL`
- `CATALOG_PROPERTY_RESOLVED`
- `CATALOG_PROPERTY_UNRESOLVED`
- `CATALOG_PROPERTY_AMBIGUOUS`
- `RUNTIME_PARAMETERIZED`
- `MIXED_PARAMETERIZED`

Do not use vague catch-all labels such as Other/Various/Unknown.

If an unsupported structure is observed, use a precise reason such as:

`unclassified_due_to_unsupported_target_expression_shape`

and preserve evidence.

## Required Generated Outputs

Local ignored outputs:

- `indexes/catalog_properties.jsonl`
- `indexes/backend_target_resolution.jsonl`
- `indexes/cache/phase4_resolution_cache.sqlite3`

The cache is local-only and must not be committed.

## Backend Target Resolution Record

Each record should include at minimum:

- deterministic observation ID;
- canonical API ID;
- API name/version;
- source path/pointer;
- operation scope where proven;
- invocation mechanism;
- invoke title;
- verb;
- backend-type;
- original safe target expression;
- symbolic property tokens;
- property lookup result IDs;
- resolved safe target expression when supported;
- normalized host/port/path components where deterministically derivable;
- target classification;
- resolution status;
- exact reason;
- evidence state;
- confidence;
- source SHA-256;
- property-file SHA-256;
- cache hit/miss metadata for evidence runs.

## Coverage Accounting

Account for all 2,036 canonical APIs.

Report:

- total canonical APIs;
- APIs inspected;
- APIs served entirely from cache on repeated run;
- APIs reparsed due to cache miss/hash change;
- APIs with invoke/target observations;
- APIs with no explicit target observation;
- total target observations;
- property-referenced observations;
- fully property-resolved observations;
- missing-property observations;
- conflicting-property observations;
- protected-property observations;
- runtime-parameterized observations;
- literal/static observations;
- APIs with multiple target observations;
- API/shared vs operation-scoped observations.

Important:

“No explicit target observation” does NOT mean “no backend exists.”

## Filtering / Grouping Requirements

The generated indexes must support cheap deterministic filtering without reopening YAML.

At minimum allow grouping/filtering by:

- symbolic property name;
- resolved host/value key where safe;
- target path;
- HTTP verb;
- invoke title;
- backend-type;
- target classification;
- resolution status;
- canonical API ID.

This should answer queries such as:

- which APIs use `ace-tip-internal`;
- how many APIs resolve through each catalog property;
- which paths are invoked through one property;
- which APIs still have unresolved properties;
- which APIs have static literal targets;
- which APIs have multiple distinct resolved targets.

These are structural/configuration observations, not duplicate or capability conclusions.

## Cache Performance Evidence

Measure cold and warm runs.

Report:

- property file parse time;
- cold target-resolution build time;
- warm cached build/query time;
- files parsed on cold run;
- files reparsed on warm run;
- cache hit count;
- cache miss count;
- output SHA-256 equality between cold/warm deterministic builds.

Do not optimize for benchmark theater; the objective is to avoid repeated unnecessary I/O/parsing and reduce future LLM context usage.

## Required Evidence Directory

Create and commit:

`tests/evidence/task-011/`

At minimum:

- `catalog_property_summary.json`
- `target_resolution_summary.json`
- `target_resolution_samples.jsonl`
- `target_pattern_inventory.json`
- `cache_performance.json`
- `commands_and_results.txt`

Do not commit the raw properties file or the SQLite cache.

## Required Tests

Add focused tests for:

- parsing the supplied catalogProperties structure;
- exact property lookup;
- repeated same-value property behavior;
- conflicting property values;
- protected property handling;
- missing property handling;
- symbolic `$(...)` extraction;
- safe resolution of `$(property)/path`;
- multiple symbolic tokens;
- runtime-parameterized expressions;
- static literal targets;
- varied YAML invoke shapes observed in corpus;
- operation-scope preservation where explicit;
- deterministic normalization;
- credential/secret redaction;
- cache cold build;
- cache warm reuse;
- selective invalidation when one source hash changes;
- selective invalidation when property-file hash changes;
- identical logical output with and without cache;
- no Task 008 relationship modification;
- no Task 009 CodeGraph modification;
- raw `staging/` unchanged.

## Frozen Components

Phase 0 through Phase 3 Task 010 are frozen.

Task 011 must not modify:

- Phase 0 profiler;
- Phase 1 extraction;
- Phase 2 identity resolution;
- Task 008 relationships;
- Task 009 CodeGraph;
- Task 010 Explorer;
- raw `staging/` evidence.

## Explicit Non-Goals

Task 011 must NOT:

- create canonical backend/target nodes;
- emit `api_invokes_target` graph edges;
- create canonical Catalog Property nodes yet;
- emit `api_uses_catalog_property` graph edges yet;
- fully reconstruct OAuth2/OIDC dependencies;
- fully classify third-party dependencies;
- infer business capability;
- perform duplicate analysis;
- infer runtime traffic/usage;
- recommend retirement;
- rationalize Products/APIs;
- design Kong mappings;
- design migration waves.

## HANSOFF Reporting

Update only `codex/comm/HANSOFF.md` for prose reporting.

HANSOFF must report:

1. exact properties file detected and SHA-256;
2. observed properties-file schema and record count;
3. safe/property protection findings;
4. property uniqueness/conflict counts;
5. exact generated property index path;
6. exact target-resolution index path;
7. exact cache path and cache schema/version;
8. total API coverage;
9. target observation counts;
10. symbolic-property usage counts;
11. resolved/missing/ambiguous/protected/runtime-parameterized counts;
12. static target counts;
13. APIs with multiple targets;
14. observed invoke/target pattern inventory;
15. representative property-resolved example;
16. representative unresolved example;
17. operation-specific example if present;
18. cold vs warm cache performance;
19. cache hit/miss counts;
20. deterministic output hashes;
21. credential/secret redaction result;
22. confirmation frozen CodeGraph/relationship indexes unchanged;
23. evidence files committed;
24. architecture findings for subsequent dependency modeling;
25. final status: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 011 is complete only when:

- the local catalog properties file is deterministically indexed;
- all 2,036 canonical APIs are accounted for;
- symbolic property references are extracted exactly;
- safe exact property matches resolve deterministically;
- missing/conflicting/protected values remain explicit;
- no backend identity is invented;
- a lightweight reusable local cache is operational;
- a warm run avoids unnecessary YAML reparsing;
- logical output is identical with or without cache;
- committed evidence contains no secrets;
- frozen Phase 3 artifacts remain unchanged;
- HANSOFF is architecture-reviewable.

## Stop Condition

Implement and validate Phase 4 Task 011 only.

Update `codex/comm/HANSOFF.md`, commit implementation/tests/evidence/handoff changes, push, and stop.

Do not begin OAuth/OIDC dependency reconstruction, third-party dependency modeling, canonical backend modeling, CodeGraph dependency enrichment, duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
