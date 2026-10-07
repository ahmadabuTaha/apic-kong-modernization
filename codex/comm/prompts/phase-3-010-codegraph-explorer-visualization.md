# Phase 3 — Task 010: CodeGraph Explorer / Visualization

## Phase
Phase 3 — CodeGraph Review Tooling

## Task Type
Implementation + Evidence Validation

## Objective
Build a lightweight local CodeGraph Explorer for architecture review and debugging over the accepted Task 009 CodeGraph indexes.

Primary flow:

```text
CodeGraph indexes
→ targeted visual review
→ navigation/traversal
→ provenance inspection
→ architecture validation
```

This task is additive review tooling only. It must not alter graph semantics, identities, or relationships.

## Accepted Inputs
Primary:
- `indexes/codegraph_nodes.jsonl`
- `indexes/codegraph_edges.jsonl`
- `indexes/codegraph_adjacency.jsonl`

For provenance drill-down only, where required:
- `indexes/relationship_index.jsonl`
- `indexes/apic_identity_resolution.json`
- `indexes/extracted_records.jsonl`

Do not scan raw `staging/` during normal explorer operation.

## Frozen Components
Treat Phase 0, Phase 1, Phase 2, Task 007, Task 008, and Task 009 as frozen.

Do not modify:
- canonical identities;
- relationship types;
- graph nodes/edges;
- graph direction;
- CodeGraph core behavior;

unless a concrete reproducible defect is proven.

## Required Explorer Capabilities

### Node search
Support:
- canonical ID lookup;
- exact name where available;
- case-insensitive substring search over name/title;
- approved object-type filter.

Approved node types only:
- `api_artifact`
- `product`
- `plan`
- `consumer_org`
- `application`
- `credential`
- `subscription`
- `catalog_config`
- `catalog_property`

### Relationship filters
Support the existing approved relationship types only:
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

### Traversal controls
Provide:
- selected start node;
- incoming / outgoing / both;
- depth 1–3;
- relationship-type filters;
- expand one node;
- reset to selected node;
- clear current view.

No unbounded traversal.

### Visual graph
Render targeted neighborhoods only.

Show:
- nodes;
- directed edges;
- node type;
- node label;
- relationship type;
- selected node;
- selected edge;
- active traversal depth and filters.

Do not attempt to render all 4,718 nodes and 9,589 edges by default.

Enforce a deterministic visualization-size limit and show a visible warning when the result exceeds it.

### Details panel
For selected node show, where available:
- canonical object ID;
- object type;
- name/title/version;
- APIC ID/self URL;
- incoming count;
- outgoing count;
- source canonical record reference.

For selected edge show:
- relationship ID;
- relationship type;
- source canonical ID/type;
- target canonical ID/type;
- evidence state;
- evidence-source category where available;
- provenance pointer to Task 008 relationship record;
- contributing occurrence IDs/source paths where already present in accepted provenance.

Never display client IDs, secrets, hashes of secrets, or unapproved credential payload values.

### Provenance drill-down
Allow review of:
- relationship record reference;
- contributing occurrence IDs;
- source path/pointer where already preserved;
- authoritative-backed / registry-backed / dual evidence where Task 008 provenance supports it.

Do not invent provenance categories.

## Required Review Use Cases

Prove these visually:

1. API-centered:
   - incoming Products;
   - incoming Plans;
   - relationship provenance.

2. Product-centered:
   - contained APIs;
   - contained Plans;
   - Plan-entitled APIs;
   - registry-only vs dual evidence where present.

3. Application-centered:
   - owning Consumer Org;
   - Subscriptions;
   - targeted Products;
   - contextual Plans;
   - structurally reachable APIs through Product/Plan.

Label this clearly as **structural reachability, not runtime consumption**.

4. Registry-only relationship example.

5. Isolated-node example.

## Delivery Constraints
Build a local review tool.

Preferred:
- lightweight Python local server; or
- lightweight local/static HTML backed by existing Python query helpers.

Do not add:
- graph database;
- external hosted service;
- authentication;
- cloud dependency;
- production deployment;
- heavyweight framework unless clearly justified.

Explorer must be runnable locally with one documented command, e.g.:
`python -m codegraph_explorer`

HANSOFF must state the exact command.

## Performance / Safety
- targeted neighborhoods only;
- deterministic result ordering;
- transparent render-size cap;
- reviewer can reduce depth/filter scope;
- preserve canonical node/relationship IDs;
- no silent truncation;
- no credential values.

## Required Evidence Directory
Create and commit:

`tests/evidence/task-010/`

At minimum:
- `explorer_acceptance.json`
- `visual_review_samples.jsonl`
- `commands_and_results.txt`

Screenshots are optional if they can be generated deterministically without unnecessary tooling.

### explorer_acceptance.json
Include:
- startup result;
- exact local run command;
- graph node/edge counts seen by explorer;
- node search checks;
- object-type filter checks;
- incoming/outgoing/both traversal checks;
- depth 1/2/3 checks;
- isolated-node result;
- registry-only relationship result;
- provenance drill-down result;
- visualization-limit guardrail result;
- credential-redaction result;
- frozen-component modification check;
- overall PASS/FAIL.

### visual_review_samples.jsonl
Include deterministic review scenarios for:
- API-centered view;
- Product-centered view;
- Application-centered view;
- registry-only relationship;
- isolated node.

Each record should include:
- selected canonical node ID/type;
- search term;
- direction;
- depth;
- relationship filters;
- returned node IDs;
- returned relationship IDs;
- exposed provenance references;
- any visualization-limit message;
- expected review interpretation.

### commands_and_results.txt
Capture:
- explorer startup command;
- smoke-test/query commands;
- focused test results;
- repository-wide test results;
- frozen-component diff check;
- staging immutability check;
- credential-redaction check.

## Required Tests
Add focused tests for:
- search by canonical ID;
- search by name/title substring;
- type filtering;
- incoming/outgoing/both traversal;
- relationship filtering;
- depth 1/2/3;
- deterministic ordering;
- visualization-size guardrail;
- isolated-node display;
- registry-only provenance;
- dual provenance where present;
- selected-edge provenance drill-down;
- credential redaction;
- Task 007 unresolved occurrences absent;
- no mutation of graph node/edge indexes;
- raw `staging/` unchanged.

## Explicit Non-Goals
Task 010 must NOT:
- change CodeGraph nodes/edges;
- create inferred/transitive relationships;
- classify Domain or Exposure Channel;
- create Logical API/Capability;
- resolve backends;
- infer runtime usage;
- analyze Analytics;
- perform duplicate/retirement/rationalization analysis;
- map APIC to Kong;
- design migration waves;
- create a production portal.

## HANSOFF Reporting
Update only `codex/comm/HANSOFF.md` for prose reporting.

Report:
1. files created/modified;
2. explorer implementation structure;
3. exact run command;
4. dependencies introduced;
5. graph indexes consumed;
6. search/traversal/filter capabilities;
7. visualization size limit;
8. node/edge details;
9. provenance drill-down;
10. API-centered review example;
11. Product-centered review example;
12. Application-centered review example;
13. registry-only example;
14. isolated-node result;
15. credential-redaction result;
16. focused/repository-wide tests;
17. confirmation frozen graph semantics/indexes were not modified;
18. evidence files under `tests/evidence/task-010/`;
19. final recommendation: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria
Task 010 is complete only when:
- explorer starts locally with one documented command;
- reads accepted Task 009 graph indexes;
- supports targeted visual exploration;
- supports incoming/outgoing/both traversal at depth 1–3;
- supports approved relationship filters;
- exposes node/edge provenance;
- distinguishes registry-only vs dual evidence where supported;
- handles isolated nodes without inference;
- enforces visualization-size limits transparently;
- changes no graph semantics;
- exposes no sensitive credential values;
- commits Task 010 evidence;
- focused tests pass.

## Stop Condition
Implement and validate Task 010 only.

Update `codex/comm/HANSOFF.md`, commit explorer implementation/tests/evidence/handoff changes, push, and stop.

Do not begin semantic enrichment, backend resolution, duplicate analysis, runtime enrichment, rationalization, migration planning, or Kong design.
