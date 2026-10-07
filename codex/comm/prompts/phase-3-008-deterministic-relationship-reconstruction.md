# Phase 3 — Task 008: Deterministic Relationship Reconstruction

## Phase

Phase 3 — Relationship Reconstruction / CodeGraph

## Task Type

Implementation + evidence validation.

## Objective

Implement the first deterministic Phase 3 relationship layer over the frozen Phase 1 occurrence index and accepted Phase 2 APIC identity-resolution output.

The goal is to convert already-resolved structural references into explicit, provenance-preserving canonical relationships between canonical APIC AS-IS identities.

This task must build structural graph edges only.

It must NOT perform semantic classification, backend inference, runtime reasoning, duplicate analysis, rationalization, or Kong target-state design.

## Entry Condition

Phase 2 is accepted as PASS after Task 007.

Accepted Phase 2 evidence includes:

- `indexes/apic_identity_resolution.json`
- 4,718 canonical APIC identities
- deterministic Product/API identity bridges
- contextual Plan identity
- resolved management references
- 113 Product-location API source occurrences correctly preserved as `UNRESOLVED`
- committed Task 007 review evidence under `tests/evidence/task-007/`

Treat Phase 0, Phase 1, and the accepted Phase 2 resolver contract as frozen.

Do not reopen or redesign them unless this task demonstrates a concrete reproducible defect that breaks relationship reconstruction.

## Architecture Boundary

Phase 3 answers:

> Which canonical APIC AS-IS objects are structurally related, according to explicit resolved evidence?

Phase 3 does NOT yet answer:

- what business Domain an API belongs to;
- what Exposure Channel it represents;
- what Logical API / Logical Capability it belongs to;
- whether APIs are duplicates or overlaps;
- whether an API is active or retired;
- which backend is actually invoked;
- how APIC objects map to Kong;
- which migration wave an object belongs to.

## Approved Relationship Types

Use only the already approved relationship taxonomy:

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

For Task 008, emit only relationships that are directly supported by current accepted Phase 1 / Phase 2 structural evidence.

Do not emit `api_uses_catalog_property` or `api_invokes_target` merely because those relationship types are approved. If current evidence does not support them, report zero edges and preserve the gap.

Do not add a new relationship type.

## Structural Truth Rules

Every emitted edge must satisfy all of the following:

1. both source and target canonical identities are resolved;
2. the relationship is supported by explicit source/reference evidence already preserved by Phase 1/Phase 2;
3. the edge retains provenance back to the contributing occurrence/reference evidence;
4. unresolved/ambiguous evidence is not converted into an edge;
5. registry evidence may prove a registry relationship but must not fabricate missing authoritative configuration;
6. Subscription proves entitlement/reference structure only, not runtime usage;
7. no relationship may be inferred from names, hashes, semantic similarity, or runtime assumptions.

## Required Relationship Reconstruction Scope

### 1. Product → API

Emit:

`product_contains_api`

from accepted Product membership evidence where the Product and API canonical identities are resolved.

Prefer authoritative Product YAML `apis.<api-key>.$ref` evidence when present.

Registry-only Product membership may be represented only when it is direct registry membership evidence between resolved canonical Product and API identities. Preserve evidence source so authoritative-configured membership and registry-only membership remain distinguishable.

Do not use any of the 113 unresolved Product-location source copies as relationship endpoints merely because they have diagnostic API candidates.

### 2. Product → Plan

Emit:

`product_contains_plan`

for resolved canonical Product-context Plan identities supported by Product YAML or direct registry Product/Plan structure.

Plan identity remains contextual to Product.

Do not create a global Plan relationship based on Plan name.

### 3. Plan → API

Emit:

`plan_entitles_api`

only where the Plan's Product-local API key resolves through the same Product's API map to a resolved canonical API identity.

The validated structural reference population from Phase 2 was 2,432 / 2,432 resolved Plan API-key references.

Do not cross Product boundaries.

### 4. Application → Consumer Organization

Emit:

`application_belongs_to_consumer_org`

from the accepted exact URL resolution:

`application.consumer_org_url → consumer_org.url`

Phase 2 validated 256 / 256.

### 5. Credential → Application

Emit:

`credential_belongs_to_application`

from:

`credential.app_url → application.url`

Phase 2 validated 270 / 270.

Never emit credential secret/client-ID values in the relationship index or evidence artifacts.

### 6. Subscription → Application

Emit:

`subscription_belongs_to_application`

from:

`subscription.app_url → application.url`

Phase 2 validated 1,019 / 1,019.

### 7. Subscription → Product

Emit:

`subscription_targets_product`

from:

`subscription.product_url → product.url`

Phase 2 validated 1,019 / 1,019.

This means structural subscription targeting only, not runtime use.

### 8. Subscription → Plan

Emit:

`subscription_uses_plan`

only after Product context has resolved the Subscription's Plan identity.

Phase 2 validated 1,019 / 1,019 contextual Plan references.

### 9. Catalog Property / Backend Relationships

For this task:

- emit `api_uses_catalog_property` only if an accepted explicit structural reference already exists and resolves to a canonical `catalog_property`;
- emit `api_invokes_target` only if an accepted explicit target identity exists under the current canonical model and Phase 3 contract.

Current accepted evidence has zero extracted Catalog Property objects and backend resolution has not been performed.

Therefore do not infer either relationship from raw policy text, URLs, names, or guessed targets in Task 008.

If zero are emitted, report that explicitly as expected evidence absence, not as a parser failure.

## Relationship Record Contract

Produce a compact deterministic relationship index under `indexes/`.

Prefer:

`indexes/relationship_index.jsonl`

unless an existing repository convention requires a different implementation-owned name.

Each edge must contain at minimum:

- deterministic relationship ID;
- approved `relationship_type`;
- source canonical object ID;
- source canonical object type;
- target canonical object ID;
- target canonical object type;
- evidence state using the already-approved evidence vocabulary;
- source/reference provenance sufficient to trace the edge;
- contributing Phase 1 extracted record IDs where applicable;
- raw reference value(s) where applicable;
- Phase 2 resolution reference/status where applicable;
- evidence source category sufficient to distinguish authoritative artifact/configuration evidence from registry identity/reference evidence.

Do not duplicate large raw payloads.

Do not introduce new status/reason/taxonomy vocabularies.

If a required finding cannot be represented with approved vocabulary, preserve the concrete evidence and report it in HANSOFF rather than inventing a new taxonomy.

## Edge Identity / Deduplication Rules

The graph must distinguish:

- duplicate source occurrences that prove the same canonical relationship;
- genuinely distinct canonical relationships.

If multiple source occurrences prove the same canonical source → relationship type → canonical target edge:

- emit one canonical edge;
- retain all contributing provenance/evidence references on that edge.

Do not count repeated registry/artifact occurrences as multiple enterprise relationships when they resolve to the same canonical endpoints and relationship type.

The canonical edge key must be deterministic and based on canonical endpoints + approved relationship type, not source filename order.

## Unresolved Evidence Rules

Do not create graph edges when:

- source identity is unresolved;
- target identity is unresolved;
- the reference is `AMBIGUOUS`;
- the reference is `BROKEN_REFERENCE`;
- attachment would require name-only, hash-only, sibling inheritance, or semantic inference.

The 113 Task 007 Product-location occurrences remain source evidence only and must not become standalone graph nodes or edges unless future architecture explicitly changes the identity contract.

## Required Evidence Artifact Directory

Create and commit Task 008 review evidence under:

`tests/evidence/task-008/`

At minimum create:

- `relationship_counts.json`
- `relationship_samples.jsonl`
- `relationship_coverage.json`
- `commands_and_results.txt`

If a deterministic evidence-generation helper is useful, place it under:

`tests/evidence/task-008/`

The evidence directory is required so architecture review can inspect what the code actually produced without relying only on HANSOFF prose.

## Required Evidence Content

### relationship_counts.json

Include:

- total canonical edges;
- count by approved relationship type;
- count by evidence source category;
- count of edges with multiple contributing source occurrences;
- zero-count approved relationship types explicitly listed;
- unresolved/ambiguous/broken references that were not emitted as edges, grouped by existing approved resolution outcome where applicable.

### relationship_samples.jsonl

Provide deterministic representative edge samples for every relationship type with a non-zero count.

Each sample should show:

- canonical source ID/type;
- relationship type;
- canonical target ID/type;
- contributing occurrence IDs;
- source paths/pointers;
- raw reference evidence where applicable;
- evidence state;
- evidence source category.

Include enough samples to inspect artifact-backed, registry-backed, and contextual Plan relationships where those patterns exist.

Do not expose credential values.

### relationship_coverage.json

Show structural coverage against the accepted Phase 2 populations, including at minimum:

- Product → API coverage;
- Product → Plan coverage;
- Plan → API coverage;
- Application → Consumer Org coverage;
- Credential → Application coverage;
- Subscription → Application coverage;
- Subscription → Product coverage;
- Subscription → Plan coverage;
- Catalog Property relationship coverage;
- backend/target relationship coverage.

Where an expected count is not architecture-approved in advance, report observed numerator/denominator evidence rather than forcing a count.

### commands_and_results.txt

Capture meaningful commands and results used to:

- build the relationship index;
- verify deterministic output;
- verify edge counts;
- run focused tests;
- run repository-wide tests;
- verify source immutability;
- verify credential redaction;
- inspect that Phase 0/1/2 implementations were not modified unless a concrete defect required it.

Do not include secrets.

## Required Tests

Add focused Phase 3 tests covering at minimum:

- deterministic relationship IDs;
- canonical edge deduplication with multiple provenance sources;
- Product → API reconstruction;
- Product → Plan reconstruction;
- contextual Plan → API reconstruction;
- Application → Consumer Org reconstruction;
- Credential → Application reconstruction;
- Subscription → Application/Product/Plan reconstruction;
- unresolved target does not emit an edge;
- ambiguous/broken reference does not emit an edge;
- name-only/hash-only evidence does not emit an edge;
- the 113 Task 007 unresolved Product-location occurrences are not promoted into graph relationships;
- no credential secret/client-ID values are emitted;
- repeated full-corpus runs produce byte-identical relationship output;
- raw `staging/` remains unchanged.

## Retrieval / Token-Efficiency Rule

Use:

```text
Phase 2 canonical identity-resolution output
→ Phase 1 extracted records only where edge provenance/reference detail is needed
→ Task 007 evidence where the 113 unresolved copies need validation
→ targeted raw staging evidence only for verification
```

Do not reparse/rescan the whole raw corpus as the primary relationship-building path.

## Regression Guardrails

- Phase 0 is frozen.
- Phase 1 is frozen.
- Phase 2 identity resolution is accepted and frozen.
- Task 007 evidence is accepted.
- Do not modify previous-phase implementation to make Phase 3 easier.
- Reopen a frozen component only for a concrete reproducible defect or broken downstream requirement.
- Distinguish a bug fix from an enhancement.
- Do not modify raw `staging/`.
- Do not change `.gitignore`.
- Do not modify `CURRENT_TASKS.md` or prompt files.
- Do not create ad-hoc report Markdown files.

## Explicit Non-Goals

Task 008 must NOT:

- assign Domain;
- assign Exposure Channel;
- create Logical API or Logical Capability identities;
- infer API business meaning;
- perform backend resolution;
- inspect runtime Analytics;
- classify duplicates or overlaps;
- classify retired/active APIs;
- rationalize Products or APIs;
- generate migration candidates;
- map APIC to Kong;
- design Kong products/plans/services/routes;
- start migration-wave planning.

## HANSOFF Reporting

Update only:

`codex/comm/HANSOFF.md`

for prose reporting.

HANSOFF must reference the committed Task 008 evidence directory and report:

1. files created/modified;
2. relationship builder implementation structure;
3. exact relationship-index path;
4. total canonical edges;
5. counts by approved relationship type;
6. authoritative-artifact-backed vs registry-backed relationship evidence;
7. canonical-edge deduplication findings;
8. Product → API / Product → Plan / Plan → API coverage;
9. Application/Credential/Subscription relationship coverage;
10. zero-count approved relationship types and why;
11. unresolved/ambiguous/broken evidence excluded from edges;
12. confirmation that the 113 Task 007 occurrences were not improperly promoted;
13. deterministic repeated-run SHA-256;
14. credential-redaction result;
15. focused and repository-wide test results;
16. any reproducible defect found in a frozen earlier phase;
17. exact evidence files created under `tests/evidence/task-008/`;
18. recommendation: PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

## Acceptance Criteria

Task 008 is complete only when:

- the canonical relationship index is deterministic;
- all emitted edges use only approved relationship types;
- every edge has canonical endpoints and provenance;
- repeated source evidence is deduplicated into one canonical edge while preserving all evidence;
- unresolved/ambiguous/broken references do not become edges;
- the 113 unresolved Product-location occurrences remain unresolved source evidence;
- required review evidence is committed under `tests/evidence/task-008/`;
- focused tests pass;
- HANSOFF provides an architecture-reviewable result.

## Stop Condition

Implement and validate Task 008 only.

Update `codex/comm/HANSOFF.md`, commit the Phase 3 implementation/tests/evidence/handoff changes, push, and stop.

Do not begin semantic enrichment, backend resolution, duplicate analysis, rationalization, or Kong design.
