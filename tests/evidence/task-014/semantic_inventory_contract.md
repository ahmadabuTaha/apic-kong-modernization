# Task 014 Semantic Inventory Contract — Architecture Review Draft

## Status and boundary

This is a deterministic extraction contract and representative mock, not an approved estate-wide semantic model. Records contain extracted facts and explicit evidence states only.

The contract does not infer Observed Function, Logical Function, Logical API, Business Domain, Business Capability, ownership, duplication, retirement, runtime use, Kong design, or migration waves. An operation is an inventory record and is not a CodeGraph node.

## API inventory record

Primary join key: `canonical_api_id`, copied from the accepted Phase 2 canonical API identity.

Stable record key: `semantic_api_inventory_id = sha256(canonical_api_id)` with a type prefix.

Factual fields:

- accepted identity name, title, and version;
- source-evidenced `info.title`, `info.description`, and `info.version`;
- source-evidenced `x-ibm-configuration.type` as protocol metadata;
- declared Swagger/OpenAPI document format and parser-coverage state;
- safe descriptive tags when explicitly present;
- accepted authoritative source path, exact root pointer, source SHA-256, and source occurrence IDs;
- operation record IDs and count;
- API-shared backend observations and references to operation-scoped backend observations;
- accepted AS-IS Product/Plan relationship IDs and canonical endpoint IDs;
- unresolved Product-location occurrence references retained as unresolved, never promoted to relationships;
- explicit missing-field reasons and evidence confidence;
- `future_hypotheses` and `architectural_judgments`, both empty in Task 014.

Registry-only identities remain API records with `REGISTRY_ONLY_NO_ACCEPTED_API_YAML`, zero extracted operations, and explicit missing reasons. Registry metadata is not re-labeled as source-evidenced API-document metadata.

## Operation inventory record

An operation is identified only from an explicit Swagger/OpenAPI `paths` Path Item HTTP method.

Stable record key inputs:

```text
canonical API ID
+ accepted source path
+ exact JSON/YAML pointer
+ uppercase HTTP method
+ exact path
```

This prevents collapse of different methods on one path and different paths with similar labels.

Factual fields:

- `canonical_api_id` primary join key;
- exact uppercase method and exact path;
- source `operationId`, summary, description, and tags only when present;
- exact source path, escaped JSON pointer, source SHA-256, and document type;
- compact parameter facts: name, location, required flag, scope, and `$ref` only;
- compact request facts: body presence, required flag, content types, and schema `$ref` values;
- compact response facts: status codes, content types, and schema `$ref` values;
- explicitly matching operation-scoped backend observations;
- API-shared backend context labeled `API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS` rather than assigned as proven operation routing;
- missing-field reasons, confidence, empty future hypotheses, and empty architectural judgments.

Large schemas are not expanded. Schema references remain references.

## Backend and routing evidence

- Task 011 is authoritative for backend observation scope and resolution state.
- An `OPERATION_SCOPED` observation is associated to an operation only by exact case-insensitive HTTP verb plus exact path equality from its accepted `operation_scope` evidence.
- An `API_SHARED` observation remains on the API record. Operation records may list its observation ID as API context, but explicitly state it is not proven operation egress.
- Safe target path/template, token names, status, reason, and upstream observation/provenance IDs are retained.
- Raw resolved endpoint hosts and infrastructure values are omitted.

## AS-IS Product and Plan evidence

Only frozen accepted relationships are used:

- `product_contains_api`;
- `plan_entitles_api`;
- `product_contains_plan` for plans that entitle the sampled API.

These are AS-IS APIC structural relationships, not future Kong Product design.

The 113 Task 007 unresolved Product-location API occurrences remain explicitly unresolved. A diagnostic canonical API candidate does not attach the source occurrence or create a relationship.

## Source representation rules

### Mixed definitions

Only explicitly supported Swagger 2.0 and OpenAPI 3.x `paths` HTTP operations are extracted. Unsupported or undeclared formats receive `UNSUPPORTED_DOCUMENT_FORMAT`; no operation is fabricated from assembly policy names or labels.

### Exact duplicate source files

Accepted Phase 2 canonical identity is the deduplication boundary. Equivalent source occurrences are retained as occurrence IDs on one API record; the selected accepted source is parsed once and does not duplicate operation records.

### Multiple representations

Phase 2 accepted source precedence remains authoritative. Task 014 selects the lexically first accepted root API YAML occurrence only within the already accepted canonical identity evidence. It records all contributing and authoritative occurrence IDs and does not reconcile conflicting raw representations semantically.

If multiple accepted root API YAML representations contain conflicting semantics, the contract requires an explicit conflict state and architectural review before estate-wide rollout. The representative sample did not discover such a conflict.

### Registry-only identities

Registry-only identities are retained with no invented source document, operations, descriptions, protocol, or schema references.

## Parser coverage

Supported in this mock:

- Swagger 2.0 Path Item operations;
- OpenAPI 3.x Path Item operations;
- HTTP methods `GET`, `PUT`, `POST`, `DELETE`, `OPTIONS`, `HEAD`, `PATCH`, and `TRACE`;
- path-shared and operation parameters;
- Swagger body parameters and OpenAPI request bodies;
- response status/content/schema-reference summaries;
- local or external `$ref` strings without dereferencing.

Explicitly unsupported or not extracted:

- GraphQL field operations;
- SOAP/WSDL operations;
- AsyncAPI channels;
- OpenAPI callbacks, links, and webhooks;
- APIC assembly policy labels as semantic operations;
- schema expansion or semantic interpretation;
- inferred routes when method/path is absent.

## Missing and conflict states

Missing values are `null` plus a structured reason. Examples include `field_absent_or_blank_in_source`, `no_accepted_api_yaml_representation`, `no_supported_explicit_path_operations`, and `unsupported_document_format`.

Evidence absence is not converted into a negative business conclusion. No runtime-consumption statement is made.

## Architecture decisions required before scaling

1. Approve or revise the API and operation field contract.
2. Confirm whether accepted duplicate YAML representations require a separate conflict-comparison report before rollout.
3. Confirm whether OpenAPI callbacks/webhooks belong in the future operation contract.
4. Confirm whether GraphQL/SOAP/AsyncAPI require separate protocol-specific inventory record types.
5. Confirm whether API-shared backend context should remain API-only in later semantic tasks.
6. Confirm the evidence threshold for treating a missing description as a review gap versus acceptable source absence.

Approval of Task 014 does not authorize Task 018 domain mapping. Task 018 retains its separate architect-reviewed mock-test gate.
