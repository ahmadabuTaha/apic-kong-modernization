# Phase 3 — Task 011: Deterministic Backend / Target Resolution

## Phase

Phase 3 — Backend / Target Resolution

## Task Type

Implementation + Evidence Validation

## Objective

Resolve backend/target invocation evidence for the accepted APIC API estate in a deterministic, evidence-first way.

This task addresses the known structural gap exposed by the CodeGraph Explorer:

```text
api_invokes_target = 0
```

The goal is to determine, from explicit APIC source evidence, what backend/target each API or operation is configured to invoke, where that can be proven, while preserving unresolved and dynamic cases honestly.

Task 011 is a **target evidence extraction and resolution task**.

It is NOT yet a graph-enrichment task.

## Critical Architecture Constraint

The approved canonical object taxonomy currently does NOT contain a backend/target object type.

Therefore Task 011 must NOT:

- invent `backend_service`, `target_service`, `endpoint`, or another canonical object type;
- create backend/target CodeGraph nodes;
- emit `api_invokes_target` graph edges;
- modify the accepted relationship taxonomy;
- modify Task 008 relationship records;
- modify Task 009 CodeGraph indexes.

Instead, Task 011 must produce a deterministic target-resolution index that can be architecture-reviewed before a later task decides how resolved targets should be represented canonically.

## Accepted Inputs

Use the accepted indexes first for identity/provenance:

- `indexes/apic_identity_resolution.json`
- `indexes/extracted_records.jsonl`
- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`

Use targeted source artifacts under `staging/` only to inspect API definitions, assemblies/policies, operation overrides, catalog variables/properties, and explicit invocation configuration.

Do not perform repeated full raw-repository scans for each API.

Prefer:

```text
canonical API identity
→ accepted occurrence/source pointers
→ targeted API source artifact
→ invocation/policy evidence
```

## Frozen Components

Treat as frozen:

- Phase 0 repository profiling;
- Phase 1 extraction;
- Phase 2 identity resolution;
- Task 007 unresolved occurrence investigation;
- Task 008 relationship reconstruction;
- Task 009 CodeGraph Core;
- Task 010 CodeGraph Explorer.

Do not modify them unless Task 011 proves a concrete reproducible defect that blocks target resolution.

## Scope of Target Evidence

Inspect explicit backend/target configuration found in APIC API artifacts and their assembly/policy structure.

Support only invocation mechanisms actually observed in the corpus.

Examples MAY include, only if present:

- invoke/proxy policies;
- explicit target URL fields;
- operation-specific target overrides;
- API-level target configuration;
- variables or property references used inside target URLs;
- policy constructs that deterministically choose between explicit targets.

Do not assume a policy mechanism exists merely because APIC supports it.

The corpus is authoritative.

## Required Extraction Granularity

Resolve target evidence at the narrowest supported scope.

At minimum distinguish:

- API-level target evidence;
- operation-level target evidence where the source explicitly scopes invocation to an operation;
- shared/default invocation evidence;
- multiple explicit targets within one API/operation;
- dynamic or parameterized targets.

Do not collapse operation-specific targets into one API-level target when the evidence shows differences.

Do not invent operation mapping when source evidence does not support it.

## Required Resolution States

Use the existing global evidence/resolution concepts where applicable.

For each target observation, preserve a precise resolution outcome such as:

- `RESOLVED` — explicit target expression is deterministically recoverable;
- `UNRESOLVED` — target depends on missing/unresolved evidence;
- `AMBIGUOUS` — more than one target interpretation is supported and cannot be deterministically selected;
- `BROKEN_REFERENCE` — an explicit referenced property/object is missing or invalid.

Do not convert a dynamic target into a guessed static URL.

## Target Expression Preservation

For every target observation preserve both:

1. the source expression as evidence, safely projected;
2. a normalized target representation where deterministic.

Examples of normalization may include:

- scheme;
- host expression;
- port;
- path template;
- query presence;
- variable placeholders.

Normalization must not destroy the original evidence expression.

Do not resolve environment variables, catalog properties, runtime context variables, or secrets unless explicit accepted evidence proves the value.

## Dynamic / Parameterized Targets

Dynamic targets are expected and must remain visible.

Examples:

```text
https://$(backend.host)/service
$(target-url)
https://host/${context.variable}/path
```

If the final runtime URL cannot be determined statically:

- preserve the exact safe expression;
- extract known static components;
- list unresolved placeholders/references;
- classify as dynamic/parameterized;
- do not fabricate a concrete endpoint.

## Catalog Property / Variable Handling

Task 009 currently has:

```text
catalog_property identities = 0
api_uses_catalog_property = 0
```

Task 011 may discover explicit references to catalog variables/properties in target expressions.

If so:

- record the reference and source pointer;
- record whether a value is explicitly available in accepted source evidence;
- preserve unresolved references;
- do NOT create `catalog_property` canonical identities;
- do NOT add `api_uses_catalog_property` relationships.

If this exposes a taxonomy/extraction gap, report it for architecture review.

## Target Normalization and Candidate Grouping

Produce deterministic normalized target keys only when supported by explicit evidence.

Useful structural fields may include:

- scheme;
- normalized host expression;
- explicit port;
- normalized path template;
- complete normalized target expression;
- static vs parameterized flag.

A grouping such as “multiple APIs reference the same normalized target expression” is allowed as an observational metric.

It is NOT duplicate analysis and must not be interpreted as equivalent business capability.

## Required Output

Produce a local ignored deterministic index, recommended:

`indexes/backend_target_resolution.jsonl`

Each record should include at minimum:

- deterministic target-observation ID;
- canonical API ID;
- API name/version where available;
- source occurrence/source path;
- operation scope where explicitly known;
- invocation mechanism/policy type;
- original safe target expression;
- normalized target expression/components where deterministically possible;
- static vs parameterized/dynamic classification;
- referenced variables/properties;
- resolution status;
- evidence state;
- confidence;
- provenance/source pointer;
- explicit reason when unresolved/ambiguous/broken.

Do not put credential values or secrets in this index.

## Coverage Accounting

Task 011 must provide exact denominator/numerator accounting.

At minimum report:

- total canonical APIs: 2,036;
- APIs with at least one source artifact inspected;
- APIs with explicit target/invocation evidence;
- APIs with no explicit target evidence found;
- APIs with one resolved target observation;
- APIs with multiple target observations;
- APIs with dynamic/parameterized target expressions;
- APIs with unresolved target references;
- operation-scoped target observations;
- API-scoped target observations;
- total target observations;
- resolved / unresolved / ambiguous / broken-reference counts.

Important:

“No explicit target evidence found” must NOT be interpreted as “API has no backend.”

It means only that Task 011 did not find admissible explicit target evidence in the inspected source.

## Policy / Invocation Mechanism Inventory

Produce an observed invocation-mechanism inventory from the corpus.

For each observed mechanism report:

- exact mechanism/policy name;
- count of APIs;
- count of observations;
- representative source pointers;
- whether target extraction is supported;
- whether target is static, parameterized, or mixed.

Do not create a generic `other` mechanism if a more precise observed name exists.

If a mechanism cannot yet be parsed, use a precise reason such as:

- `unparsed_due_to_unsupported_policy_shape`;
- `unresolved_due_to_missing_property_value`;
- `unresolved_due_to_runtime_expression`.

## Operation-Level Integrity

Where operations are explicitly identifiable:

- preserve method/path;
- bind target evidence only to operations supported by source structure;
- distinguish shared/default assembly behavior from operation-specific behavior;
- do not copy one operation target to all operations without explicit inheritance evidence.

If operation-level mapping cannot be proven, keep the target at API/shared scope.

## Security / Redaction

Never emit:

- client secrets;
- API keys;
- tokens;
- passwords;
- private keys;
- credential payload values.

If credentials appear embedded in a URL, redact user-info/secret portions while preserving enough structural evidence to review the target.

Tests must prove redaction.

## Required Evidence Directory

Create and commit:

`tests/evidence/task-011/`

At minimum:

- `target_resolution_summary.json`
- `target_resolution_samples.jsonl`
- `invocation_mechanism_inventory.json`
- `commands_and_results.txt`

Optional deterministic helper scripts may live in the same directory.

### target_resolution_summary.json

Include:

- total canonical APIs;
- APIs inspected;
- APIs with explicit target evidence;
- APIs without explicit target evidence;
- target observation count;
- resolved/unresolved/ambiguous/broken-reference counts;
- static vs parameterized counts;
- API-scoped vs operation-scoped counts;
- APIs with one target;
- APIs with multiple targets;
- unresolved placeholder/reference counts;
- exact generated index path;
- deterministic SHA-256;
- overall acceptance result.

### target_resolution_samples.jsonl

Include representative deterministic examples covering, where present:

1. static explicit target;
2. parameterized/dynamic target;
3. multiple targets in one API;
4. operation-specific target;
5. shared/default target;
6. unresolved property/variable reference;
7. no explicit target evidence case;
8. credential-redaction case if safely testable.

Each sample must include canonical API ID and exact provenance.

### invocation_mechanism_inventory.json

Include every observed target/invocation mechanism with exact counts and parser support status.

Do not collapse different mechanisms into vague categories.

### commands_and_results.txt

Capture:

- target-resolution build command;
- repeated deterministic generation/hash check;
- focused tests;
- repository-wide tests;
- staging immutability;
- frozen-component diff check;
- credential-redaction validation.

## Required Tests

Add focused tests for at minimum:

- static target extraction;
- parameterized target preservation;
- multiple explicit targets;
- operation-scoped target mapping;
- shared/default target mapping;
- unresolved property/variable handling;
- broken reference handling;
- ambiguous evidence handling;
- no-target-evidence handling without false assertion;
- normalization determinism;
- credential redaction;
- canonical API provenance;
- repeated full-corpus output byte identity;
- no changes to Task 008 relationship index;
- no changes to Task 009 CodeGraph indexes;
- raw `staging/` unchanged.

## Explicit Non-Goals

Task 011 must NOT:

- add backend nodes to CodeGraph;
- emit `api_invokes_target` edges;
- add `catalog_property` nodes;
- emit `api_uses_catalog_property` edges;
- perform duplicate/overlap detection;
- infer business capability;
- classify Domain or Exposure Channel;
- infer actual runtime usage;
- use analytics to declare targets active/inactive;
- recommend retirement;
- rationalize APIs or Products;
- map targets to Kong;
- design Kong Services/Routes;
- design migration waves.

## HANSOFF Reporting

Update only `codex/comm/HANSOFF.md` for prose reporting.

HANSOFF must report:

1. implementation files created/modified;
2. exact target-resolution index path;
3. total canonical APIs and inspection coverage;
4. exact target observation counts;
5. resolution-state counts;
6. static vs parameterized/dynamic counts;
7. operation-scoped vs API/shared counts;
8. observed invocation mechanism inventory;
9. representative static target example;
10. representative dynamic target example;
11. multiple-target example if present;
12. operation-specific example if present;
13. unresolved/broken evidence examples;
14. APIs with no explicit target evidence;
15. normalized target grouping metrics;
16. catalog variable/property findings;
17. credential-redaction result;
18. deterministic hash result;
19. focused/repository-wide test results;
20. confirmation frozen relationship/CodeGraph indexes were unchanged;
21. evidence files under `tests/evidence/task-011/`;
22. architecture findings that require a later canonical backend/target modeling decision;
23. final recommendation: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 011 is complete only when:

- all 2,036 canonical APIs are deterministically accounted for;
- target evidence is extracted only from explicit source evidence;
- dynamic targets remain dynamic;
- operation-specific evidence is not collapsed incorrectly;
- unresolved/missing references remain explicit;
- no backend/target canonical type is invented;
- no CodeGraph node/edge is added or modified;
- no runtime usage is inferred;
- output is deterministic;
- credential redaction passes;
- evidence artifacts are committed;
- HANSOFF is architecture-reviewable.

## Stop Condition

Implement and validate Task 011 only.

Update `codex/comm/HANSOFF.md`, commit implementation/tests/evidence/handoff changes, push, and stop.

Do not begin backend canonical modeling, CodeGraph enrichment, semantic duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
