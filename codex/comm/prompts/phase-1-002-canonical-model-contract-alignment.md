# Phase 1 — Task 002: Canonical Model Contract Alignment

## Objective

Align the Phase 1 extraction design with the already-established APIC → Kong canonical model from the project context.

This is an architecture-alignment task only.

Do **not** implement Python.
Do **not** modify Phase 0.
Do **not** create a new taxonomy, status vocabulary, reason vocabulary, object type, relationship type, or semantic classification.

The project must continue using the canonical terminology and taxonomies already established in the prior project context.

If the current evidence cannot be represented by an existing approved taxonomy or field, report the gap in `codex/comm/HANSOFF.md` for architecture review. Do not invent a replacement.

## Core Clarification

The project has used the word "canonical" for several related but distinct concepts. This task must align them without redefining the project ontology.

Use these meanings:

### 1. Canonical Ontology

The vendor-neutral architectural language used to describe APIC AS-IS and later compare it to Kong TO-BE.

It includes already-established concepts such as:

- Domain
- Exposure Channel / API Offering
- Logical API / Logical Function
- Logical Capability
- API Artifact
- Declared API Version
- Operation
- Deployment
- Endpoint
- Backend Service
- Product
- Plan
- Consumer
- Application
- Subscription / Entitlement
- Credential
- Runtime Usage
- Ownership
- Change / Release Lineage

Do not add new ontology concepts in this task.

### 2. Canonical Object Types

Use only the already-approved canonical object types:

- `api_artifact`
- `product`
- `plan`
- `consumer_org`
- `application`
- `credential`
- `subscription`
- `catalog_config`
- `catalog_property`

Do not create synonyms.

### 3. Source Artifact / Source Occurrence

A raw file or addressable object occurrence in `staging/` is evidence.

The same APIC object may appear in more than one representation, for example:

- full API definition
- API summary in `_list.json`
- full Product definition
- Product summary
- Consumer Org resource
- Consumer Org summary

Phase 1 may extract occurrences from those sources, but an occurrence is not automatically a distinct enterprise object.

### 4. APIC Object Identity

APIC URI / URL / object identifier is the primary identity and correlation evidence.

Names are secondary evidence only.

Phase 1 must preserve identity and reference evidence required for later resolution.

Phase 1 must not perform URI/object resolution.

### 5. Canonical AS-IS Record

A canonical record is the normalized AS-IS representation of an APIC object after deterministic identity resolution.

It is not a Logical API.
It is not a Logical Capability.
It is not a semantic deduplication result.
It does not collapse separate APIC API artifacts merely because they have similar names, paths, backends, or functionality.

The existing Canonical API Record shape from the project context remains the starting schema and must not be replaced by a newly invented schema.

Phase 1 prepares the evidence needed to construct that record.
Phase 2 resolves object identity and references.
Phase 3 reconstructs structural relationships.

## Required Pipeline

Use this architecture:

```text
Raw Source Artifact
    ↓
Phase 1: deterministic extraction / normalization
    ↓
APIC object evidence + IDs/URIs/references + provenance
    ↓
Phase 2: URI / Identifier Resolution
    ↓
Canonical APIC AS-IS objects
    ↓
Phase 3: Relationship Reconstruction / CodeGraph
    ↓
Later semantic enrichment:
Logical API / Logical Capability / Domain / Channel / rationalization
```

Do not move semantic enrichment into Phase 1.

## Existing Relationship Model Must Be Preserved

Do not create new relationship types.

Use the already-established structural relationship taxonomy:

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

Important architecture correction:

**API membership in a Product is independent of Subscription.**

The graph is not a single mandatory chain.

At minimum preserve the distinction:

```text
Product
  ├─ product_contains_api → API
  └─ product_contains_plan → Plan

Plan
  └─ plan_entitles_api → API
```

Separately:

```text
Consumer Org
  ↓
Application
  ↓
Credential

Application
  ↓
Subscription
  ↓
Product / Plan entitlement context
```

A Product may contain APIs even when there is no Subscription.

A Subscription proves configured entitlement/association, not Product-to-API membership and not runtime consumption.

## Taxonomy Freeze

Do not introduce or substitute statuses such as:

- `EXTRACTED_WITH_MISSING_FIELDS`
- `PRESERVED_EVIDENCE`
- `UNSUPPORTED_OBJECT_TYPE`

or any other new vocabulary unless it already exists in the approved project context.

For Phase 1 extraction, retain the already-established statuses:

- `EXTRACTED`
- `EXTRACTION_PARTIAL`
- `EXTRACTION_FAILED`

and the already-established reasons:

- `required_field_missing`
- `unsupported_object_shape`
- `source_artifact_malformed`
- `field_type_mismatch`

If these are insufficient for observed evidence, report the exact evidence gap. Do not invent another status/reason.

Likewise, continue using the existing global evidence states, resolution states, backend states, duplicate taxonomy, consumer taxonomy, productization taxonomy, review reasons, runtime taxonomy, and rationalization taxonomy from the project context. Do not redefine them.

## Phase 1 Design Alignment Required

Review the previous Phase 1 design and align it to the contract above.

In `HANSOFF.md`, report:

1. Whether the previous design conflicts with the canonical model above.
2. Which parts remain valid.
3. Which proposed fields/concepts should be renamed, removed, or deferred because they introduced a new taxonomy or confused source occurrence with canonical identity.
4. The minimum Phase 1 extracted evidence fields required to support:
   - APIC object identity
   - URI/reference resolution
   - provenance
   - credential redaction
   - later construction of the existing Canonical API Record
5. How Phase 1 should represent:
   - a full API document
   - API summary
   - Product root
   - Product summary
   - embedded Plan
   - Consumer Org
   - Application
   - Credential
   - Subscription
   - Catalog config/property
   - WSDL evidence
   - unsupported evidence
   - empty collections
6. Confirm that Phase 1 counts are source/extraction counts and must not be presented as unique enterprise object counts before Phase 2.
7. Confirm that Product → API membership is resolved independently of Subscription.
8. Identify any real evidence that the existing canonical model cannot represent.

## Existing Test Finding

The latest handoff reports 5 test setup errors because:

`tests/fixtures/repository_profile/staging`

is absent.

Do not repair this in this design task.

Report whether this is:

- a repository/fixture packaging issue, or
- evidence of a reproducible Phase 0 defect.

Do not reopen the frozen Phase 0 profiler unless a reproducible defect is demonstrated.

## Reporting Rule — Mandatory

The **only** reporting artifact for this task is:

`codex/comm/HANSOFF.md`

Do not create:

- a design report
- a review report
- a task result file
- a summary Markdown file
- any other reporting artifact

Put the complete result directly in `codex/comm/HANSOFF.md`.

## Non-Goals

Do not:

- implement Phase 1 Python
- modify Phase 0 implementation
- resolve URIs
- construct canonical IDs
- build CodeGraph
- build relationships
- classify Domain
- classify Exposure Channel
- classify Technical Role
- resolve backends
- detect functional duplicates
- perform runtime reasoning
- map APIC objects to Kong
- create any new taxonomy

## Stop Condition

Stop after updating `codex/comm/HANSOFF.md`.

Wait for architecture review before implementation.
