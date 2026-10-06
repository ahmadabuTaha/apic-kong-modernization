# Phase 1 — Extracted Record Model Before URI Resolution

## Objective

Refine the Phase 1 Object Extraction & Normalization design using the evidence already inspected.

The goal is to keep Phase 1 simple and deterministic:

```text
Raw APIC evidence
→ extracted records
→ Phase 2 URI / Identifier Resolution
→ canonical APIC objects
→ Phase 3 relationship reconstruction / CodeGraph
```

Do not implement code in this task.

## Architectural Clarification

The inspected evidence shows repeated representations of the same APIC object.

Examples:

- full API definition plus API summary in `_list.json`
- full Product definition plus Product summary in `_list.json`
- Consumer Org resource plus Consumer Org summary

Therefore:

**an extracted source occurrence is not yet a final canonical object.**

Phase 1 must preserve source occurrences without attempting to merge them.

Phase 2 owns identity resolution and canonicalization using APIC identifiers.

## Primary Identity / Correlation Rule

The project already established that APIC URI / URL / object identifier is the primary relationship and identity evidence.

Names are secondary evidence only.

Examples of expected URL-based evidence include:

```text
consumer_org
  ← application.consumer_org_url

application
  ← credential.app_url

application
  ← subscription.app_url

consumer_org
  ← subscription.consumer_org_url

product
  ← subscription.product_url
```

Product / Plan / API references must also retain their source reference values for later resolution.

Do not resolve these relationships in Phase 1.

## Phase 1 Record Model

Use an extracted-record concept rather than final canonical identity.

Each extracted record should preserve, where applicable:

- `extracted_record_id`
- `canonical_object_type_candidate`
- `extraction_status`
- `failure_reasons`
- `source_relative_path`
- `source_schema_family`
- `source_object_pointer`
- `source_sha256`
- `source_object_type`
- `apic_object_id`
- `apic_object_uri`
- `name`
- `version`

`extracted_record_id` may be deterministic from:

```text
canonical object type candidate
+ source relative path
+ source object pointer
```

Do not call this a final `canonical_object_id`.

Final canonical identity belongs to Phase 2.

## Treatment of Observed Shapes

Use the already-inspected evidence:

- OpenAPI/Swagger root document → extracted `api_artifact` record
- API summary from `_list.json` → extracted API occurrence/summary record, not a separate final API identity
- APIC Product root → extracted `product` record
- Product summary from `_list.json` → extracted Product occurrence/summary record
- Product embedded plan → extracted `plan` record
- Consumer Org resource → extracted `consumer_org` record
- Consumer Org summary → extracted Consumer Org occurrence/summary record
- Application collection item → extracted `application` record
- Credential collection item → extracted `credential` record
- Subscription collection item → extracted `subscription` record
- Catalog / catalog_setting root → extracted `catalog_config` record
- Supported configuration item → extracted `catalog_property` record
- `member` records → preserve as unsupported extraction evidence; do not rename into another canonical type
- empty supported collections → successful source extraction with zero records
- Markdown / .DS_Store → unsupported source evidence, no canonical object record

Do not introduce a separate observation subsystem unless concrete downstream evidence proves it is necessary.

## WSDL

Preserve WSDL evidence and metadata, including at minimum:

- source path
- source hash
- definitions name
- targetNamespace

Do not infer an independent final API identity from a WSDL alone.

Do not discard WSDL because Phase 0 classified its format as `OTHER`.

Its relationship to APIC `wsdl-to-rest` or other API artifacts can be resolved later.

## Credential Security

Continue using an explicit allowlist.

Never write credential values or secret/hash values into derived indexes.

Metadata may include:

- credential type
- client ID present
- client secret present
- hashed secret present
- referenced application URI
- referenced consumer organization URI

## Important Count Interpretation

Phase 1 counts are **extracted record occurrences**, not enterprise API/Product counts.

For example, the previously projected:

- 6,397 API records
- 1,010 Product records
- 56 Consumer Org records

must not be reported as:

- 6,397 unique APIs
- 1,010 unique Products
- 56 unique Consumer Orgs

Those counts include repeated source representations.

The unique/canonical APIC object count can only be determined after Phase 2 URI / Identifier Resolution.

## Required Output

Return a design report only. No code changes.

The report must contain:

1. Revised Phase 1 extracted-record schema.
2. Classification of each inspected evidence shape.
3. Which fields are retained specifically for Phase 2 URI/ID resolution.
4. Revised interpretation of Phase 1 counts as source occurrences.
5. Expected Phase 1 index/output files.
6. Proposed Phase 2 identity-resolution algorithm using:
   - APIC URI
   - APIC object ID
   - explicit references
   - name only as fallback evidence
7. How Phase 2 will distinguish:
   - multiple occurrences of the same APIC object
   - broken references
   - ambiguous identifiers
8. Any evidence that contradicts this design.

## Non-Goals

Do not:

- implement Python
- modify Phase 0 profiler
- build relationships
- resolve URIs
- build CodeGraph
- classify domains
- classify exposure channels
- resolve backends
- classify duplicates semantically
- perform Kong mapping
- infer runtime usage

## Stop Condition

Stop after the revised design report.

Update the project handoff file with the findings and wait for architecture review before implementation.
