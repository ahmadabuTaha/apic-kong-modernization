# Phase 3 — Task 009: CodeGraph Core Construction

## Phase

Phase 3 — CodeGraph Core

## Task Type

Implementation + Evidence Validation

## Objective

Build the first deterministic CodeGraph layer over the accepted canonical APIC identity index and accepted relationship index.

The CodeGraph must provide a compact, queryable structural view of the APIC AS-IS estate without reparsing raw source evidence and without introducing semantic or inferred relationships.

The core model is:

```text
Canonical APIC identities
        ↓
      Nodes
        +
Accepted canonical relationships
        ↓
      Edges
        ↓
Deterministic adjacency / traversal
        ↓
Targeted structural queries
```

Task 009 establishes graph mechanics only.

## Accepted Inputs

Use these accepted generated inputs as the primary source:

- `indexes/apic_identity_resolution.json`
  - 4,718 canonical APIC identities
- `indexes/relationship_index.jsonl`
  - 9,589 canonical relationships

Use Phase 1 or raw `staging/` only for focused verification if a concrete inconsistency is discovered.

Do not re-run estate-wide parsing as the primary graph-building path.

## Frozen Components

Treat as frozen:

- Phase 0 repository profiling;
- Phase 1 source extraction;
- Phase 2 identity resolution;
- Task 007 targeted unresolved investigation;
- Task 008 relationship reconstruction.

Do not modify them unless Task 009 proves a concrete reproducible defect or broken downstream requirement.

Enhancement is not a bug fix.

## CodeGraph Scope

The CodeGraph must represent:

### Nodes

Create exactly one graph node for each accepted canonical APIC AS-IS identity.

Approved node/object types remain only:

- `api_artifact`
- `product`
- `plan`
- `consumer_org`
- `application`
- `credential`
- `subscription`
- `catalog_config`
- `catalog_property`

Do not create:

- Logical API nodes;
- Domain nodes;
- Exposure Channel nodes;
- backend nodes;
- runtime consumer nodes;
- Kong nodes;
- duplicate-group nodes;
- inferred capability nodes.

The graph node ID should be the accepted canonical object ID or a deterministic one-to-one graph wrapper ID that preserves the canonical ID explicitly.

Do not create duplicate graph identities for the same canonical object.

### Edges

Use only the accepted Task 008 relationship records.

The graph must contain exactly the accepted canonical relationships from `indexes/relationship_index.jsonl`.

Approved relationship types remain:

- `product_contains_api`
- `product_contains_plan`
- `plan_entitles_api`
- `application_belongs_to_consumer_org`
- `credential_belongs_to_application`
- `subscription_belongs_to_application`
- `subscription_targets_product`
- `subscription_uses_plan`
- `api_uses_catalog_property`
- `api_invokes_target`

Do not create inferred/transitive edges.

For example, do NOT materialize a direct:

```text
consumer_org → api
```

relationship merely because a traversal can reach one through Application → Subscription → Product → API.

Traversal paths are query results, not new canonical relationships.

## Required Core Graph Functions

Implement deterministic graph access supporting at minimum:

1. fetch node by canonical ID;
2. fetch outgoing relationships for a node;
3. fetch incoming relationships for a node;
4. filter incoming/outgoing relationships by approved relationship type;
5. one-hop neighbor lookup;
6. bounded multi-hop traversal;
7. traversal restricted by allowed relationship types;
8. traversal restricted by direction:
   - outgoing;
   - incoming;
   - both;
9. path output preserving exact relationship IDs and node IDs;
10. deterministic ordering of nodes, relationships, neighbors, and paths.

Bound traversal depth explicitly. Do not implement unbounded recursive traversal.

A reasonable default maximum depth may be chosen by implementation, but it must be explicit, deterministic, and overridable within a safe bounded limit.

## Structural Query Use Cases to Prove

Task 009 must prove the graph can answer structural questions such as:

### API-centered

Given a canonical API Artifact:

- which Products contain it?
- which Plans entitle it?
- through which Products/Plans is it structurally exposed?
- which relationship evidence supports those paths?

### Product-centered

Given a Product:

- which APIs does it contain?
- which Plans does it contain?
- which APIs are entitled by each Plan?

### Application / Subscription-centered

Given an Application:

- which Consumer Organization owns it?
- which Subscriptions belong to it?
- which Products do those Subscriptions target?
- which contextual Plans do those Subscriptions use?
- which APIs are structurally reachable through those Product / Plan relationships?

Important:

A traversal result such as:

```text
Application
→ Subscription
→ Product
→ API
```

is structural reachability only.

It must NOT be described as actual runtime API consumption.

## Provenance Rules

The CodeGraph must not duplicate large evidence payloads.

Each graph edge should preserve/reference:

- accepted canonical relationship ID;
- relationship type;
- source canonical ID;
- target canonical ID;
- evidence state;
- provenance/reference pointer back to the Task 008 relationship record.

Each graph node should preserve/reference:

- canonical object ID;
- canonical object type;
- minimal identity/display fields useful for retrieval;
- reference back to the Phase 2 canonical identity record.

When a user/traversal asks for evidence, the graph should return compact provenance pointers that can be expanded through existing indexes.

## Graph Integrity Requirements

Validate all of the following:

- graph node count equals accepted canonical identity count;
- every accepted canonical identity appears exactly once as a node;
- graph edge count equals accepted relationship count;
- every accepted relationship appears exactly once as an edge;
- every edge source exists as a node;
- every edge target exists as a node;
- no relationship type outside the approved taxonomy appears;
- no graph-only inferred edge exists;
- no duplicate edge ID exists;
- no duplicate canonical node exists;
- isolated canonical identities remain present as nodes;
- 113 Task 007 unresolved Product-location occurrences do not become graph nodes or graph edges;
- zero `api_uses_catalog_property` and zero `api_invokes_target` remain zero unless the accepted relationship index changes through a separately approved task.

## Directionality

Preserve the canonical relationship direction exactly as Task 008 emitted it.

Incoming traversal is a query/indexing capability; it does not reverse or create a second canonical edge.

Example:

```text
product_contains_api
Product → API
```

The graph may answer "which Products contain this API?" using the incoming adjacency index, but must not create a second relationship type or reverse canonical edge.

## Determinism

Repeated builds from identical accepted Phase 2 and Task 008 inputs must produce byte-identical CodeGraph indexes.

Deterministically order:

- nodes;
- edges;
- adjacency lists;
- relationship-type lists;
- traversal results;
- returned paths.

Report SHA-256 for repeated full-corpus builds.

## Output Design

Produce compact generated CodeGraph indexes under `indexes/`.

Recommended outputs:

- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`
- `indexes/codegraph_adjacency.jsonl`

Alternative compact deterministic filenames are allowed if repository conventions justify them, but HANSOFF must report exact paths.

Do not copy entire Phase 2 / Task 008 records into the graph indexes.

Prefer IDs + minimal retrieval fields + pointers.

## CLI / Query Interface

Provide a simple deterministic CLI or module interface capable of targeted graph queries without loading raw `staging/` evidence.

At minimum support:

- node lookup by canonical ID;
- incoming neighbor lookup;
- outgoing neighbor lookup;
- bounded traversal by canonical ID;
- optional relationship-type filter;
- direction selection;
- machine-readable JSON output.

Do not build a web UI, graph database server, visualization frontend, or external service in Task 009.

## Explicit Non-Goals

Task 009 must NOT:

- classify Domain;
- classify Exposure Channel;
- create Logical API / Logical Capability;
- perform backend discovery;
- parse policies for target semantics;
- infer runtime usage;
- use Analytics;
- detect duplicates / overlap;
- recommend retirement;
- rationalize Products;
- design migration waves;
- map APIC objects to Kong;
- design Kong Services / Routes / Products / Plans;
- introduce a graph database dependency;
- create semantic or inferred edges;
- reinterpret registry-only relationships as authoritative Product YAML configuration.

## Required Evidence Directory

Create and commit review evidence under:

`tests/evidence/task-009/`

At minimum create:

- `codegraph_integrity.json`
- `codegraph_counts.json`
- `traversal_samples.jsonl`
- `commands_and_results.txt`

If a deterministic evidence helper is needed, place it under the same directory.

### codegraph_integrity.json

Include at minimum:

- expected canonical node count;
- actual graph node count;
- unique canonical node IDs;
- expected accepted relationship count;
- actual graph edge count;
- unique relationship IDs;
- missing relationship endpoints;
- orphan edges;
- duplicate nodes;
- duplicate edges;
- unsupported relationship types;
- isolated node count;
- Task 007 unresolved occurrence promotion count;
- graph-only inferred edge count;
- overall integrity result.

### codegraph_counts.json

Include:

- graph nodes by approved object type;
- graph edges by approved relationship type;
- incoming/outgoing adjacency counts;
- number of connected nodes;
- number of isolated nodes;
- deterministic graph build hashes.

Do not interpret connectivity as business importance or runtime usage.

### traversal_samples.jsonl

Commit deterministic representative traversal samples covering at minimum:

1. API → incoming Product relationships;
2. API → incoming Plan entitlement relationships;
3. Product → Plans → APIs;
4. Application → Consumer Organization;
5. Application → Subscription → Product;
6. Application → Subscription → Product / Plan → API structural reachability;
7. a registry-only structural relationship example;
8. an isolated node example if isolated nodes exist.

Each traversal sample must include:

- start canonical ID/type;
- traversal direction;
- max depth;
- relationship filters where used;
- exact ordered nodes;
- exact ordered relationship IDs;
- path(s);
- compact provenance references.

Do not label Application → API reachability as runtime consumption.

### commands_and_results.txt

Capture:

- graph build command;
- repeated deterministic build/hash verification;
- graph integrity command/test;
- representative traversal commands;
- focused pytest result;
- repository-wide pytest result;
- source immutability verification;
- credential-redaction verification;
- frozen-component diff verification.

Do not include credential values.

## Required Tests

Add focused tests covering at minimum:

- one canonical identity → exactly one node;
- all accepted identities included;
- accepted relationship → exactly one graph edge;
- no inferred/transitive edge materialization;
- incoming adjacency correctness;
- outgoing adjacency correctness;
- relationship-type filtering;
- bounded multi-hop traversal;
- deterministic path ordering;
- cyclic graph safety if a synthetic cycle is supplied;
- isolated node preservation;
- missing node/edge handling without fabrication;
- Task 007 113 unresolved occurrences remain absent;
- credential values are never emitted;
- repeated full-corpus graph build is byte-identical;
- raw `staging/` remains unchanged.

## Retrieval / Token-Efficiency Rule

Normal CodeGraph retrieval must follow:

```text
CodeGraph node / adjacency indexes
→ accepted relationship record
→ accepted canonical identity record
→ Phase 1 occurrence evidence when needed
→ targeted raw staging evidence only for verification
```

Do not make routine CodeGraph queries scan the full raw repository.

The purpose of this graph layer is specifically to support low-token, targeted estate reconstruction.

## HANSOFF Reporting

Update only:

`codex/comm/HANSOFF.md`

for prose reporting.

HANSOFF must report:

1. files created/modified;
2. CodeGraph implementation structure;
3. exact generated graph index paths;
4. canonical graph node count;
5. graph node count by approved object type;
6. canonical graph edge count;
7. edge count by approved relationship type;
8. graph integrity results;
9. isolated-node findings;
10. confirmation that accepted relationships were not changed or inferred;
11. confirmation that the 113 Task 007 unresolved occurrences were not promoted;
12. deterministic repeated-build hashes;
13. representative traversal findings;
14. API-centered traversal result examples;
15. Product-centered traversal result examples;
16. Application/Subscription structural traversal examples;
17. credential-redaction result;
18. focused and repository-wide tests;
19. any reproducible defect found in a frozen earlier phase;
20. exact evidence files created under `tests/evidence/task-009/`;
21. recommendation: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 009 is complete only when:

- all accepted canonical identities are represented exactly once as graph nodes;
- all accepted canonical relationships are represented exactly once as graph edges;
- no inferred relationship is materialized;
- deterministic incoming/outgoing adjacency is available;
- bounded deterministic multi-hop traversal works;
- provenance remains traceable to accepted indexes;
- routine traversal does not require scanning raw `staging/`;
- the 113 unresolved source occurrences remain excluded;
- required review evidence is committed under `tests/evidence/task-009/`;
- focused tests pass;
- HANSOFF provides an architecture-reviewable result.

## Stop Condition

Implement and validate Task 009 only.

Update `codex/comm/HANSOFF.md`, commit CodeGraph implementation/tests/evidence/handoff changes, push, and stop.

Do not begin semantic enrichment, backend resolution, duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
