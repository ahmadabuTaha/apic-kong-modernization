# Phase 1 — Task 005: Extractor Implementation

## Objective

Implement the Phase 1 deterministic extraction layer now that Task 004 closed the resolution contract for the observed APIC evidence.

Phase 1 must extract immutable source-occurrence evidence only. It must NOT perform Phase 2 identity resolution and must NOT build graph relationships.

## Architecture Contract

Source precedence is fixed:

```text
actual artifact/configuration under staging/
    = authoritative AS-IS configuration evidence

registry/list/collection records
    = APIC identity / URL / ID / scope / cross-reference evidence
```

Do not treat `list.json` as the single source of truth.

## Approved Canonical Object Types

Use only:
- `api_artifact`
- `product`
- `plan`
- `consumer_org`
- `application`
- `credential`
- `subscription`
- `catalog_config`
- `catalog_property`

Do not introduce any new object type, taxonomy, status, reason, relationship type, confidence scale, or semantic classification.

## Approved Phase 1 Extraction Statuses

Use only:
- `EXTRACTED`
- `EXTRACTION_PARTIAL`
- `EXTRACTION_FAILED`

Approved extraction reasons only:
- `required_field_missing`
- `unsupported_object_shape`
- `source_artifact_malformed`
- `field_type_mismatch`

Do not add others.

## Required Extraction Scope

Implement extraction for the evidence already validated in Tasks 001–004:

### API Artifact
- authoritative API definitions under `staging/apis/_catalog`;
- API registry records under the API catalog list/registry evidence;
- API-shaped Product-location source occurrences under `staging/products/_catalog`;
- preserve name, title, declared version, APIC ID/self URL when directly observed, org/catalog scope, source path/hash/pointer;
- preserve Product-location API occurrences as source occurrences; do not treat them as automatically separate API identities.

### Product
- authoritative Product YAML;
- Product registry records;
- Product API `$ref` values;
- Product-local API keys;
- embedded Plan keys/names;
- Plan API keys;
- APIC ID/self URL/org/catalog scope when directly observed in registry evidence.

### Plan
- extract embedded Plan occurrence in Product context;
- Plan identity remains contextual to its Product occurrence in Phase 1;
- preserve Plan key/name and Product-local API keys;
- do not invent a global Plan ID.

### Consumer Organization
- registry/list occurrence;
- detailed resource occurrence where present;
- preserve ID, self URL, name/title/state, org/catalog URLs, provenance.

### Application
- collection occurrence;
- preserve ID, self URL, name/title/state/lifecycle state where present;
- preserve `consumer_org_url`, `app_credential_urls`, org/catalog scope, provenance.

### Credential
- collection occurrence;
- preserve credential object ID/self URL/name/type if directly observed;
- preserve `app_url`, `consumer_org_url`, org/catalog scope, provenance;
- NEVER emit client ID value, client secret value, hashed-secret value, or unknown credential payload fields;
- emit presence booleans only for sensitive fields when present.

### Subscription
- collection occurrence;
- preserve ID/self URL/name;
- preserve `app_url`, `consumer_org_url`, `product_url`, Plan value, org/catalog scope, provenance;
- do not infer runtime usage.

### Catalog Config / Catalog Property
- extract already-supported catalog root / catalog-setting evidence;
- preserve empty catalog-property collections as zero object occurrences;
- do not invent catalog-property items.

### WSDL
- preserve WSDL as source evidence using source path/hash plus definitions name and target namespace;
- do not create a new canonical object type;
- WSDL evidence may have null canonical object type candidate.

## Required Occurrence-Level Record Contract

Each extracted occurrence must contain only evidence needed for later resolution. Keep it compact and deterministic.

Required common fields:
- deterministic `extracted_record_id` used only as source-occurrence provenance;
- approved `canonical_object_type_candidate` or null;
- `extraction_status`;
- `failure_reasons` using only approved reasons;
- source-relative path;
- source SHA-256;
- Phase 0 schema family where available;
- stable source pointer/object pointer;
- directly observed APIC ID;
- directly observed self URL;
- directly observed name/title/version where applicable;
- directly observed org/catalog URLs or IDs where present;
- exact raw reference values needed by later resolution.

Do not call `extracted_record_id` a canonical object ID.

## Approved Product `$ref` Mapping

Implement only the architecture-approved mapping:

```text
raw absolute $ref
→ locate exactly one /staging/ segment
→ preserve suffix beginning at staging/
→ map relative to repository/project root
```

Preserve BOTH:
- raw `$ref`
- mapped repository-relative path

If `/staging/` is missing, repeated, or maps to zero/multiple files, retain the raw evidence and do not guess.

Do not normalize any other path component.

## Phase Boundary — Mandatory

Phase 1 must NOT:
- merge Product YAML with Product registry into one canonical object;
- merge API YAML with API registry into one canonical object;
- resolve URLs to target objects;
- resolve Product `$ref` to canonical API identity;
- emit graph edges;
- assign Logical API or Logical Capability;
- classify Domain or Exposure Channel;
- classify backend;
- infer runtime usage;
- perform duplicate/overlap/rationalization analysis;
- map anything to Kong.

Phase 1 only extracts the evidence that Phase 2 will resolve.

## Output

Produce a deterministic Phase 1 extracted-occurrence index under `indexes/`.

Prefer one compact JSONL index unless the existing repository conventions clearly require another structure.

Generated indexes/outputs remain ignored/local as already established.

Do not modify raw `staging/`.

## Validation Requirements

Add focused tests for the Phase 1 extractor using temporary/synthetic fixtures or another approach that does not require fixing the known Phase 0 ignored nested `staging` fixture issue.

Validate at minimum:
- deterministic record IDs across repeated runs;
- no secret/client ID values emitted;
- Product raw and mapped `$ref` preservation;
- embedded Plan extraction;
- Consumer Org/Application/Credential/Subscription reference preservation;
- empty collections produce zero object occurrences;
- malformed/unsupported evidence uses only approved statuses/reasons;
- source files remain unchanged;
- repeat run produces identical extracted index content.

Run the extractor against the current local `staging/` evidence and report aggregate counts by approved canonical object type candidate and extraction status.

Counts remain occurrence counts, NOT unique enterprise object counts.

## Regression Guardrails

- Do not modify frozen Phase 0 behavior unless a reproducible defect blocks Phase 1.
- Do not fix the known Phase 0 fixture packaging issue in this task.
- Do not change `.gitignore` merely to make the old fixture pass.
- Do not modify `CURRENT_TASKS.md` or prompt files.
- Do not create new design/report Markdown files.

## Handoff Reporting

Update only `codex/comm/HANSOFF.md` for task reporting.

Report:
1. files created/modified;
2. implementation structure;
3. exact output index path;
4. aggregate extraction occurrence counts by approved object type and status;
5. Product/API/Plan/source occurrence counts;
6. credential-redaction validation;
7. `$ref` mapping validation;
8. tests executed and results;
9. any evidence shape that could not be represented using the approved contract;
10. whether Phase 1 implementation is ready for architecture review.

Do not introduce vocabulary to describe gaps; use plain language.

## Stop Condition

Implement Phase 1 extraction only, validate it, update `codex/comm/HANSOFF.md`, commit task changes plus HANSOFF, push, and stop.

Do not begin Phase 2 resolution.