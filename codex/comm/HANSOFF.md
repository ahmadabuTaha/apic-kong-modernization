# Codex Handoff

## Task executed

Phase 1 — Task 002: Canonical Model Contract Alignment. Architecture/design alignment only; no implementation.

## Prompt file used

`codex/comm/prompts/phase-1-002-canonical-model-contract-alignment.md`

## Summary of what was done

- Reviewed the Task 001 extracted-record design against the established canonical ontology, canonical object types, extraction statuses/reasons, phase boundaries, and structural relationship taxonomy supplied by Task 002.
- Identified the parts of the prior design that remain valid and the proposed vocabulary that conflicts with the taxonomy freeze.
- Defined the minimum Phase 1 evidence needed for later APIC identity/reference resolution and construction of the existing Canonical API Record without replacing that record.
- Aligned treatment of every requested evidence shape using only approved canonical object types, extraction statuses, and reasons.
- Confirmed that Phase 1 reports source/extraction occurrences rather than unique enterprise objects.
- Confirmed that Product-to-API membership evidence is independent of Subscription evidence.
- Assessed the missing test fixtures as a repository/fixture packaging issue rather than evidence of a Phase 0 implementation defect.

## Canonical contract alignment result

### 1. Conflicts in the previous design

The Task 001 design has vocabulary conflicts with the canonical contract in Task 002. Its occurrence-first architecture is valid, but the following parts are not approved contract terms and must not be implemented:

- extraction statuses `EXTRACTED_WITH_MISSING_FIELDS`, `PRESERVED_EVIDENCE`, and `UNSUPPORTED_OBJECT_TYPE`;
- source-result statuses `SUCCESS`, `SUCCESS_ZERO_RECORDS`, `PARTIAL`, `FAILED`, and `UNSUPPORTED_SOURCE`;
- Phase 2 outcomes `RESOLVED_URI`, `RESOLVED_ID`, `PROPOSED_FALLBACK_MATCH`, `UNRESOLVED_NO_IDENTITY`, and `IDENTITY_CONFLICT`;
- newly proposed reason values such as `BROKEN_REFERENCE`, `TARGET_NOT_EXTRACTED`, and `TARGET_TYPE_MISMATCH`;
- controlled `source_object_type` values such as `openapi_document`, `api_summary`, `product_document`, and `wsdl_definitions` where they would create a new source-representation taxonomy;
- the `source_pointer_format` enumeration and any `reference_kind` enumeration not already present in the established contract.

The approved Phase 1 extraction statuses are only:

- `EXTRACTED`
- `EXTRACTION_PARTIAL`
- `EXTRACTION_FAILED`

The approved Phase 1 reasons are only:

- `required_field_missing`
- `unsupported_object_shape`
- `source_artifact_malformed`
- `field_type_mismatch`

The prior report remains historical Task 001 output. This handoff supersedes its conflicting vocabulary; the prior report was not modified because Task 002 permits only `codex/comm/HANSOFF.md` as its reporting artifact.

### 2. Parts of the previous design that remain valid

- A Phase 1 extracted record represents source occurrence evidence, not final canonical enterprise identity.
- The same APIC object may have multiple occurrences, including full definitions and `_list.json` summaries.
- `extracted_record_id` may be a deterministic provenance key derived from approved object-type candidate, source path, and source pointer. It must never be called or treated as a canonical object ID.
- Only the approved canonical object types may be used: `api_artifact`, `product`, `plan`, `consumer_org`, `application`, `credential`, `subscription`, `catalog_config`, and `catalog_property`.
- APIC URI/URL/object ID is primary identity and correlation evidence; name and version are secondary evidence.
- Phase 1 preserves raw IDs, URIs, references, and provenance without resolving or merging them.
- Exact file-hash equality is provenance and duplicate-file evidence; it does not establish canonical object identity.
- Credential extraction uses an explicit allowlist and never emits client IDs, client secrets, hashed-secret values, or unknown credential payload fields.
- Empty supported collections are successful source processing with zero extracted occurrences, not unique objects and not parse failures.
- WSDL source path, source hash, definitions name, and target namespace remain useful evidence, but WSDL alone does not establish an independent API identity.
- Phase 1 counts remain occurrence/extraction counts. Unique APIC AS-IS object counts require Phase 2 identity resolution.
- Phase 1 performs no Domain, Exposure Channel, Logical API, Logical Capability, backend, runtime, functional-duplicate, rationalization, or Kong classification.

### 3. Fields and concepts to rename, remove, or defer

| Prior proposal | Aligned disposition |
|---|---|
| Unapproved extraction and source-result statuses | Remove. Use only `EXTRACTED`, `EXTRACTION_PARTIAL`, and `EXTRACTION_FAILED`. |
| Unapproved failure/reference reason codes | Remove. Use only the four approved extraction reasons in Phase 1. |
| Custom Phase 2 resolution outcomes and ambiguity/broken-reference reason values | Defer to Phase 2 and its already-established global resolution taxonomy. That taxonomy is not reproduced in this repository, so this task does not recreate it. |
| `canonical_object_type_candidate` | Retain only as an occurrence-level classification using the nine approved canonical object types or null when no approved type can be asserted. It is not canonical identity. |
| Controlled `source_object_type` vocabulary | Remove as a new taxonomy. Distinguish representations through existing schema-family evidence, source path, source pointer, and observed source fields. |
| `source_pointer_format` enum | Remove unless the established Canonical API Record contract already contains it. A stable source pointer is still required; its contract representation needs architecture confirmation. |
| `reference_kind` enum | Remove unless already approved. Preserve the exact source field, source pointer, and raw reference value without inventing a relationship type in Phase 1. |
| Derived `resolution_scope` structure | Defer to the existing canonical contract. Preserve directly observed organization/catalog IDs and URIs as raw evidence. |
| Generic `attributes` extension container | Defer. Use only fields defined by the existing Canonical API Record/extraction contract and explicit credential allowlist. |
| Detailed identity merging, broken-reference classification, and ambiguity algorithms | Defer to Phase 2. Phase 1 only makes the source evidence available. |
| Relationship edge construction | Defer to Phase 3 and use only the approved relationship taxonomy. |

### 4. Minimum Phase 1 extracted evidence

The minimum evidence is intentionally smaller than a replacement canonical schema.

#### Occurrence and extraction control

- `extracted_record_id`, used only as deterministic source-occurrence provenance;
- one approved `canonical_object_type_candidate`, or null when the evidence does not justify one;
- `extraction_status`, using only the three approved values;
- `failure_reasons`, using only the four approved values and empty when extraction is complete.

`EXTRACTION_PARTIAL` is used only when a field required by the established contract is missing or has the wrong type. An APIC ID or URI that is legitimately absent from a source representation must remain null; its absence must not automatically be called a failure.

#### Provenance

- source-relative path;
- Phase 0 source schema family;
- stable source object pointer for root, collection item, or embedded item;
- source SHA-256;
- the exact observed source field locations for retained references.

#### APIC identity and reference evidence

- directly observed APIC object ID;
- directly observed self URI/URL;
- directly observed name and version;
- directly observed organization and catalog IDs/URIs where present;
- exact, unmodified source reference values and their source fields/pointers, including Product API references, Plan API references, `consumer_org_url`, `app_url`, `product_url`, and an observed Subscription plan value.

No relationship edge is emitted in Phase 1. Retaining a reference does not prove that its target exists, that two occurrences are identical, or that runtime usage occurred.

#### Credential redaction

- credential type, when directly observed and allowed by the established contract;
- client ID present boolean;
- client secret present boolean;
- hashed secret present boolean;
- the credential object's own APIC ID/URI when present;
- referenced Application and Consumer Organization URIs;
- occurrence provenance.

The credential value, client ID value, client secret value, hashed-secret value, and unknown payload fields are excluded.

#### Later Canonical API Record construction

- approved `api_artifact` candidate classification for full API documents and API summaries;
- directly observed API name/title and declared version;
- source schema family and source location/pointer/hash;
- directly observed APIC API ID and self URI when present;
- raw Product/Plan API reference evidence retained on the Product/Plan occurrences.

This evidence allows Phase 2 to resolve APIC identity and lets later phases construct the existing Canonical API Record from immutable source evidence. It does not create a Logical API, Logical Capability, Deployment, Endpoint, Backend Service, relationship edge, or runtime fact in Phase 1.

The exact established Canonical API Record field contract is not present in the current repository. Field-for-field mapping beyond the minimum evidence above therefore requires the architecture-owned contract before implementation. This is a documentation dependency, not permission to invent a replacement schema.

### 5. Aligned treatment of evidence shapes

| Evidence | Phase 1 representation |
|---|---|
| Full API document | One occurrence with candidate `api_artifact`, approved extraction status/reasons, declared name/version, directly observed ID/URI if present, and provenance. No identity resolution or semantic grouping. |
| API summary | One occurrence with candidate `api_artifact`, direct summary ID/URI/name/version/reference evidence, and provenance. It may represent the same APIC object as a full document, but Phase 1 does not decide that. |
| Product root | One occurrence with candidate `product`; retain name/version, any direct ID/URI, Product API references, embedded Plan locations, and provenance. |
| Product summary | One occurrence with candidate `product`; retain direct ID/URI/name/version, API URLs, Plan source evidence, and provenance. |
| Embedded Plan | One occurrence with candidate `plan`; retain its source key/name, parent Product occurrence provenance, and API references. Do not assert globally unique Plan identity. |
| Consumer Organization resource or summary | One occurrence with candidate `consumer_org`; retain direct ID/URI/name and scope/provenance evidence. Repeated representations remain separate occurrences. |
| Application item | One occurrence with candidate `application`; retain direct ID/URI/name, raw `consumer_org_url`, and provenance. |
| Credential item | One occurrence with candidate `credential`; emit only the credential allowlist, raw Application/Consumer Organization URI references, and provenance. |
| Subscription item | One occurrence with candidate `subscription`; retain direct ID/URI/name, raw `app_url`, `consumer_org_url`, `product_url`, observed Plan value, and provenance. This is configured entitlement/association evidence only. |
| Catalog root/setting | One occurrence with candidate `catalog_config`; preserve direct identifiers/URIs and provenance without merging the source representations. |
| Supported catalog configuration item | One occurrence with candidate `catalog_property`; retain direct identifiers/URIs, source fields, and provenance. |
| WSDL evidence | Extract path/hash, definitions name, and target namespace with `EXTRACTED`; leave canonical object type candidate null unless separate APIC identity evidence establishes an approved type in a later phase. Do not create a WSDL object type or independent API identity. |
| Unsupported addressable evidence, including `member` | Preserve provenance with null canonical object type, `EXTRACTION_FAILED`, and `unsupported_object_shape`. Do not rename it into an approved type. |
| Unsupported non-structured source such as Markdown or `.DS_Store` | Preserve source provenance with `EXTRACTION_FAILED` and `unsupported_object_shape`; emit no canonical object occurrence. |
| Malformed supported source | Preserve source provenance with `EXTRACTION_FAILED` and `source_artifact_malformed`; do not invent partial object content. |
| Supported source with a field of the wrong type | Use `EXTRACTION_PARTIAL` or `EXTRACTION_FAILED`, as required by the established contract, with `field_type_mismatch`; preserve valid evidence only. |
| Empty supported collection | Record successful source processing with zero extracted occurrences. If a source-level extraction status is required, use `EXTRACTED`; do not invent a zero-record status or an object record. |

### 6. Count interpretation

Confirmed: Phase 1 counts are source/extraction occurrence counts and must never be presented as unique enterprise object counts before Phase 2.

The previously projected 6,397 API-related occurrences, 1,010 Product occurrences, and 56 Consumer Organization occurrences include repeated source representations. WSDL evidence must remain distinguishable from `api_artifact` candidates even if included in an API-related source count. Exact file duplicates remain occurrences in Phase 1. Phase 2 determines canonical APIC AS-IS object counts through URI/identifier resolution.

### 7. Product membership and Subscription independence

Confirmed: Product-to-API membership is resolved independently of Subscription.

Phase 1 preserves three distinct evidence sets without building edges:

- Product API references, later supporting `product_contains_api`;
- Product embedded Plan evidence, later supporting `product_contains_plan`, and Plan API references, later supporting `plan_entitles_api`;
- Subscription references to Application, Product, and Plan, later supporting `subscription_belongs_to_application`, `subscription_targets_product`, and `subscription_uses_plan`.

A Product can contain an API with no Subscription. A Subscription is configured entitlement/association evidence; it does not prove Product membership, runtime consumption, or API invocation. `api_invokes_target` remains a separate structural relationship for a later phase and cannot be inferred from Subscription.

### 8. Evidence gaps against the canonical model

No inspected source evidence requires a new canonical object type or relationship type.

- WSDL can be preserved as source evidence with no asserted canonical object type until it is correlated to an APIC API artifact.
- `member` and other unsupported shapes can be preserved as failed extraction evidence without renaming them.
- Empty collections require no object type.
- Repeated full/summary forms are source occurrences handled by later APIC identity resolution.

The material contract gap is documentary: the architecture-owned Canonical API Record field schema and the approved global Phase 2 resolution states are referenced by the task but are not stored in this repository. Implementation must not begin until those existing contracts are made available or explicitly mapped by architecture review.

## Existing test finding

The five setup errors are a repository/fixture packaging issue, not evidence of a reproducible Phase 0 defect:

- `tests/test_profiler.py` requires `tests/fixtures/repository_profile/staging`.
- Git tracks only `tests/test_profiler.py`; it does not track the required fixture tree.
- `.gitignore` contains `staging/`, which also ignores a nested fixture path named `staging`.
- The failing tests stop because the source directory does not exist; they do not reach profiling behavior with a valid fixture.
- The two tests that construct temporary source trees pass, which provides no reproduction of a Phase 0 implementation defect.

Per the active prompt, the fixtures, `.gitignore`, tests, and frozen Phase 0 profiler were not modified.

## Files created

None.

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- `.venv/bin/pytest`

## Test results

- 7 tests collected: 2 passed and 5 errored during fixture setup.
- All five errors are caused by the absent `tests/fixtures/repository_profile/staging` source directory.
- The result reproduces the repository/fixture packaging issue described above; it does not reproduce a Phase 0 profiling defect with a valid source tree.

## Generated artifacts

- `codex/comm/HANSOFF.md` is the sole task artifact.
- No files were created or modified under `staging/`, `indexes/`, or `outputs/`.

## Important findings

- Task 001's occurrence-first phase architecture remains valid, but its invented statuses, reasons, representation vocabulary, and resolution outcomes conflict with the taxonomy freeze.
- The existing canonical object and relationship types can represent the inspected APIC evidence without extension.
- The exact Canonical API Record schema and approved global Phase 2 resolution states are not repository-local and are required before implementation.
- The missing test fixture is a packaging issue caused by an untracked required fixture tree and a broad ignore rule; it is not a demonstrated profiler defect.

## Unresolved issues

- Architecture review must supply or point to the existing Canonical API Record field contract before Phase 1 implementation.
- Architecture review must supply or point to the existing global Phase 2 resolution taxonomy before URI/identifier resolution is designed or implemented.
- The repository fixture packaging issue remains unresolved by instruction.
- Task 001's separate design report still contains superseded vocabulary and must not be treated as the implementation contract; Task 002 did not permit modifying that file.

## Assumptions

- `canonical_object_type_candidate` is retained as occurrence classification because Task 001 explicitly established it and its values are restricted to the nine approved canonical object types.
- Null candidate type is allowed for evidence such as WSDL and unsupported shapes because assigning an approved type without evidence would violate project guardrails.
- Approved extraction statuses can apply to source-level processing when no object occurrence is emitted, including an empty collection.
- Raw APIC URL fields are preserved exactly; no URI normalization or resolution occurs in Phase 1.

## Deviations from the prompt

None.

## Recommended next step

Integration Architect and Enterprise Architect review this alignment, provide the existing Canonical API Record field contract and approved Phase 2 resolution taxonomy, and decide how the superseded Task 001 report should be marked or retired in a future explicitly scoped task. Do not begin implementation or fix the test fixture until a new active task authorizes it.

## Final status

REVIEW_REQUIRED
