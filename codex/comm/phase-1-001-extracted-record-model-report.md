# Phase 1 — Extracted Record Model Design Report

## Decision

Phase 1 will emit deterministic records for source occurrences. It will not assign final canonical identity, merge repeated representations, resolve references, or build relationships. Phase 2 will resolve identity from retained APIC identifiers and references, and Phase 3 will reconstruct relationships from the resolved identities.

The design is:

```text
raw source file
  -> per-source extraction result
  -> zero or more extracted occurrence records
  -> Phase 2 identity and reference resolution
  -> canonical APIC objects
```

## 1. Revised Phase 1 extracted-record schema

Each record represents exactly one occurrence at one location in one source file.

| Field | Type | Rule |
|---|---|---|
| `record_schema_version` | string | Version of the extracted-record contract. |
| `extracted_record_id` | string | Deterministic occurrence identifier; never a canonical object identifier. |
| `canonical_object_type_candidate` | string or null | Shape-based candidate such as `api_artifact`, `product`, `plan`, `consumer_org`, `application`, `credential`, `subscription`, `catalog_config`, or `catalog_property`. Null for evidence that must be retained without asserting a canonical type. |
| `extraction_status` | string | One of `EXTRACTED`, `EXTRACTED_WITH_MISSING_FIELDS`, `PRESERVED_EVIDENCE`, or `UNSUPPORTED_OBJECT_TYPE`. |
| `failure_reasons` | array of strings | Empty on complete extraction; otherwise stable machine-readable reason codes. Missing identity fields are explicit and are not parse failures. |
| `source_relative_path` | string | POSIX path relative to the repository root, including the `staging/` prefix. No absolute source paths. |
| `source_schema_family` | string | Phase 0 schema-family result. WSDL is retained even when this value is `OTHER`. |
| `source_object_pointer` | string | Root is the empty JSON Pointer. Collection and embedded records use RFC 6901 pointers such as `/results/0` or `/plans/default-plan`. XML evidence uses a stable XPath-like pointer, with `source_pointer_format` identifying the syntax. |
| `source_pointer_format` | string | `JSON_POINTER` or `XML_XPATH`. |
| `source_sha256` | string | SHA-256 from the immutable source file. It links occurrences to Phase 0 provenance and exact-duplicate evidence. |
| `source_object_type` | string | Observed representation, for example `openapi_document`, `api_summary`, `product_document`, `product_summary`, `product_plan`, `member`, or `wsdl_definitions`. |
| `apic_object_id` | string or null | Directly observed ID of this occurrence only. It is never derived from a name or filename. |
| `apic_object_uri` | string or null | Directly observed self URI/URL of this occurrence only. |
| `name` | string or null | Directly observed source name. It is secondary evidence. |
| `version` | string or null | Directly observed source version. |
| `resolution_scope` | object | Allowlisted observed scope identifiers or URIs, such as organization and catalog URI. Values remain evidence, not resolved relationships. |
| `reference_values` | array of objects | Allowlisted unresolved references, each containing `reference_kind`, `source_field`, `source_pointer`, and `raw_value`. |
| `attributes` | object | Type-specific, allowlisted non-sensitive metadata only. |

### Deterministic occurrence identifier

`extracted_record_id` is the lowercase hexadecimal SHA-256 of the UTF-8 encoding of a canonical JSON array:

```json
[
  "<canonical_object_type_candidate-or-null>",
  "<source_relative_path>",
  "<source_pointer_format>",
  "<source_object_pointer>"
]
```

The serialized array uses UTF-8, no insignificant whitespace, and JSON escaping. The stored value should be prefixed with `extracted-record:sha256:`. Including the pointer format prevents an XML pointer and a JSON pointer from being interpreted as the same address. The same source occurrence therefore receives the same ID on every run, while identical content at two paths remains two occurrences.

### Source-level result contract

An additional per-source extraction result is required because an empty supported collection successfully produces zero records, and an unsupported file produces no canonical candidate record. It contains:

- source path, SHA-256, detected format, and schema family;
- extraction status: `SUCCESS`, `SUCCESS_ZERO_RECORDS`, `PARTIAL`, `FAILED`, or `UNSUPPORTED_SOURCE`;
- emitted record count;
- stable failure or unsupported reason codes.

This is an extraction control ledger, not a separate observation or identity subsystem.

### Credential allowlist

Credential records may retain only:

- credential type;
- `client_id_present`;
- `client_secret_present`;
- `hashed_secret_present`;
- the credential object's own APIC ID and URI;
- `app_url` and `consumer_org_url` as unresolved references;
- non-sensitive provenance fields from the common envelope.

Client IDs, client secrets, hashed secret values, credential payloads, and unknown credential fields must not be written to an index or report.

## 2. Classification of inspected evidence shapes

| Evidence shape | Phase 1 result | Candidate type | Notes |
|---|---|---|---|
| OpenAPI/Swagger root document | One extracted occurrence | `api_artifact` | Classification is shape-based, including OpenAPI files found below the Product source folder. |
| API item in `_list.json` | One extracted summary occurrence per item | `api_artifact` | Not a distinct final API merely because it is a separate source occurrence. |
| APIC Product root | One extracted occurrence | `product` | Product API references and embedded plans remain unresolved. |
| Product item in `_list.json` | One extracted summary occurrence per item | `product` | Its ID/URL may later anchor a URI-less Product root occurrence. |
| Plan embedded in a Product root | One extracted occurrence per map entry | `plan` | Retain parent Product occurrence ID, plan map key, and API reference keys/values. Do not assert independent global plan identity. |
| Plan embedded in a Product summary | One extracted occurrence per array item | `plan` | Retain the parent Product occurrence ID and summary plan fields. |
| Consumer Organization resource | One extracted occurrence | `consumer_org` | Retain its directly observed ID and URI. |
| Consumer Organization item in `_list.json` | One extracted summary occurrence per item | `consumer_org` | Repeated representation, not a second canonical organization. |
| Application collection item | One extracted occurrence per item | `application` | Retain own ID/URI plus `consumer_org_url`. |
| Credential collection item | One allowlisted occurrence per item | `credential` | Secret and credential values are excluded. Retain only presence flags and allowed URI references. |
| Subscription collection item | One extracted occurrence per item | `subscription` | Retain own ID/URI, `app_url`, `consumer_org_url`, `product_url`, and the observed plan reference/name. |
| Catalog or catalog-setting root | One extracted occurrence | `catalog_config` | Keep the two observed source object types distinct through `source_object_type`; do not merge them in Phase 1. |
| Supported configuration collection item | One extracted occurrence per item | `catalog_property` | Preserve the original APIC item type in `source_object_type`. Empty collections emit no records. |
| `member` item | One retained unsupported-evidence occurrence per item | null | Use `UNSUPPORTED_OBJECT_TYPE`; do not rename it to another candidate type. |
| Empty supported collection | Source result only | n/a | `SUCCESS_ZERO_RECORDS`; this is not a parse or extraction failure. |
| WSDL definitions document | One retained evidence occurrence | null | Preserve path, hash, definitions name, and target namespace. Do not infer an independent API identity. |
| Markdown, `.DS_Store`, or other unsupported source | Source result only | n/a | `UNSUPPORTED_SOURCE`; no canonical candidate record. |
| Parseable but unrecognized structured shape | Source result only unless an addressable unsupported item exists | n/a | Preserve an explicit unsupported reason; do not guess a type. |
| Parse failure | Source result only | n/a | `FAILED` with the parser reason; no partially invented object record. |

Exact file duplicates do not change these rules. Every source occurrence is retained and linked to its file hash; Phase 1 does not collapse occurrences that share a hash.

## 3. Fields retained for Phase 2 URI/ID resolution

The following are resolution evidence, not Phase 1 relationships:

| Occurrence | Own identity evidence | Explicit unresolved references and context |
|---|---|---|
| API summary | `id`, `url`, `name`, version fields | organization URI, catalog URI, and other directly observed APIC URL fields |
| OpenAPI document | `info.x-ibm-name` or observed API name and `info.version` | Product/API `$ref` context is retained on the Product and Plan occurrences; no ID/URI is invented for the OpenAPI root |
| Product summary | `id`, `url`, `name`, `version` | `api_urls`, catalog URI, organization URI, and plan entries |
| Product root | `info.name`, `info.version` | `apis.*.$ref`; source path; plan occurrence IDs |
| Plan | plan map key or observed plan name | parent Product extracted-record ID and retained API reference keys/values |
| Consumer Organization | `id`, `url`, `name` | catalog and organization scope URIs |
| Application | `id`, `url`, `name` | `consumer_org_url`, catalog URI, organization URI |
| Credential | `id`, `url`, `name` when present | `app_url`, `consumer_org_url`, and presence-only credential metadata |
| Subscription | `id`, `url`, `name` | `app_url`, `consumer_org_url`, `product_url`, observed plan reference/name, and scope URIs |
| Catalog configuration/property | directly observed `id` and `url` when present | organization URI, catalog URI, and type-specific APIC reference URLs |
| WSDL | no asserted APIC identity | definitions name, target namespace, source path, and source hash for later evidence correlation |

All raw reference strings are retained exactly as observed. Any normalized comparison key used later is additional derived data and must not replace the raw value.

## 4. Interpretation of Phase 1 counts

All Phase 1 object counts are occurrence counts. They must be labeled `extracted_record_occurrences`, grouped by `canonical_object_type_candidate`, `source_object_type`, and `extraction_status` where useful.

The inspected evidence explains the projected headline counts as follows:

- 6,397 API-related occurrences: 4,357 OpenAPI documents, 2,036 API summary items, and 4 WSDL evidence records. The WSDL records do not assert four independent APIs.
- 1,010 Product occurrences: 499 Product root documents and 511 Product summary items.
- 56 Consumer Organization occurrences: 28 resource documents and 28 summary items.

These are not 6,397 unique APIs, 1,010 unique Products, or 56 unique Consumer Organizations. Exact duplicate files and repeated full/summary representations remain separate occurrences. Unique enterprise object counts are unavailable until Phase 2 completes identity resolution.

Plan, application, credential, subscription, catalog, catalog-property, unsupported-object, failed-source, and zero-record source counts must be reported separately. They must not be added to an enterprise API or Product count.

## 5. Expected Phase 1 index and output files

Derived files are limited to `indexes/` and `outputs/` during implementation:

| Path | Purpose |
|---|---|
| `indexes/extracted_records.jsonl` | One deterministic, allowlisted record per extracted or explicitly preserved object occurrence. |
| `indexes/extraction_source_results.jsonl` | One result per discovered source file, including successful zero-record collections and unsupported sources. |
| `outputs/object_extraction/extraction_summary.json` | Aggregate counts by source status, candidate type, source object type, and extraction status. Labels explicitly state that counts are occurrences. |
| `outputs/object_extraction/extraction_failures.jsonl` | Parse/extraction failures with provenance and sanitized reason codes/messages. |

Unsupported source evidence remains in `extraction_source_results.jsonl`; addressable unsupported objects such as member items and preserved WSDL evidence remain in `extracted_records.jsonl`. No parallel observation index is introduced.

The existing Phase 0 file index, schema-family output, exact-duplicate output, and parse-error output remain frozen inputs. Phase 1 must not rewrite them.

## 6. Proposed Phase 2 identity-resolution algorithm

Phase 2 should be deterministic and produce both canonical objects and an auditable resolution decision for every Phase 1 occurrence.

1. Validate every extracted record and preserve its raw identity/reference values.
2. Partition occurrences by compatible candidate object type. Do not compare names across different types.
3. Build exact indexes for directly observed own APIC URI, object ID, and scoped object ID. Scope is derived only from observed organization/catalog URI context.
4. Seed canonical groups from a shared non-empty own APIC URI when all occurrences have compatible types. Conflicting types or incompatible IDs create a conflict; they are never silently merged.
5. Add occurrences sharing an APIC object ID only when the type and observed scope are compatible. If one ID maps to multiple incompatible URIs or scopes, mark it ambiguous rather than selecting a target.
6. Evaluate explicit references against the URI index. A reference locates a target candidate; it does not by itself merge the referring and referenced objects. Preserve the eventual edge evidence for Phase 3.
7. For URI/ID-poor full documents, generate fallback match candidates from exact name plus version, constrained by candidate type, observed catalog/organization scope, source context, and compatible explicit references. A unique candidate can be emitted as a proposed fallback match; because names are secondary evidence, it must carry lower confidence and remain reviewable. Name alone never creates an automatic canonical merge.
8. Resolve embedded Plans within the resolved parent Product. Prefer an explicit plan ID/URI if present; otherwise use the exact source plan key/name only within that parent Product. A plan name is not globally unique.
9. Assign each occurrence one outcome: `RESOLVED_URI`, `RESOLVED_ID`, `PROPOSED_FALLBACK_MATCH`, `UNRESOLVED_NO_IDENTITY`, or `IDENTITY_CONFLICT`.
10. Emit canonical APIC objects only for accepted resolution groups. Keep every contributing `extracted_record_id` and the rule/evidence used. Preserve unresolved occurrences without manufacturing identity.

URI comparison should initially be exact. If a separately specified normalization is later approved, Phase 2 should store both raw and normalized forms, use only lossless URI normalization, and report collisions introduced by normalization.

## 7. Repeated occurrences, broken references, and ambiguity

### Multiple occurrences of the same object

Occurrences belong to the same high-confidence group when they share a compatible own APIC URI, or a compatible scoped APIC object ID, with no conflicting identity evidence. The canonical object records all contributing occurrence IDs and provenance. Hash equality is evidence of identical files, not canonical identity by itself.

### Broken references

Every retained explicit reference is resolved against the compatible URI/ID target index. No compatible target produces `BROKEN_REFERENCE`, including:

- referring extracted-record ID and source pointer;
- reference field and exact raw value;
- expected target candidate type;
- zero target candidates;
- a reason such as `TARGET_NOT_EXTRACTED` or `TARGET_TYPE_MISMATCH` when determinable from evidence.

The source occurrence remains valid evidence. A broken reference does not cause a fabricated target and does not convert configuration into runtime usage.

### Ambiguous identifiers

An identifier is ambiguous when it maps to more than one incompatible target group, such as one ID associated with multiple own URIs/scopes, one URI associated with incompatible object types, or a fallback name/version matching multiple candidates. Phase 2 emits an ambiguity record containing all candidate occurrence IDs and the conflicting evidence, makes no arbitrary selection, and leaves the reference or occurrence unresolved for architecture review.

## 8. Evidence assessment and constraints

No inspected evidence contradicts the extracted-occurrence design. The evidence does prevent a stronger Phase 1 identity claim:

- Full API and Product documents may lack the APIC object ID and self URI found in their `_list.json` summaries. URI/ID-only resolution will therefore leave some full documents unresolved without secondary evidence.
- Product roots use embedded plan maps and file references, while Product summaries use plan arrays and APIC URLs. They are different representations, not proof of different Products or Plans.
- Plan entries may lack globally unique IDs/URIs. Their safe fallback identity is contextual to a resolved parent Product.
- OpenAPI documents occur under both API and Product source folders. Folder location cannot define canonical object type.
- WSDL files were classified as `OTHER` in Phase 0 even though their definitions metadata is useful evidence. Phase 1 must explicitly preserve them without promoting them to independent APIs.
- Supported configuration collections observed in this snapshot can be empty. Zero extracted items is a successful result, not missing evidence or a parser defect.
- The observed member shape has APIC-looking fields and URLs, but the active design explicitly leaves it unsupported. Those fields do not justify renaming it into another type.

These constraints are handled by explicit missing fields, source-type provenance, fallback proposals, ambiguity reporting, and preservation of unresolved evidence. Architecture review is required before implementation.
