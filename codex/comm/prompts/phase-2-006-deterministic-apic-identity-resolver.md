# Phase 2 — Task 006: Deterministic APIC Identity Resolver

## Phase

Phase 2 — URI / Identifier Resolution

## Objective

Implement the first Phase 2 deterministic resolver that consumes the Phase 1 extracted source-occurrence index and resolves those occurrences into canonical APIC AS-IS object identities while preserving provenance, source precedence, unresolved evidence, and the approved phase boundary.

The resolver must convert:

```text
source occurrence
→ APIC object identity resolution
→ canonical APIC AS-IS identity record
```

It must NOT perform Phase 3 relationship-graph construction or later semantic/rationalization work.

## Entry Condition

Task 005 completed the deterministic Phase 1 extractor and produced:

- `indexes/extracted_records.jsonl`
- 10,221 source-occurrence records
- byte-identical repeated full-corpus output
- zero emitted credential secret/client-ID values
- all 2,244 Product API `$ref` occurrences preserved with the approved mapped `staging/...` path

Treat Phase 1 extraction behavior as frozen unless a reproducible defect directly blocks this resolver.

The known Phase 0 fixture-packaging issue is not part of this task.

## Architecture Contract

Source precedence remains fixed:

```text
actual artifact/configuration under staging/
    = authoritative AS-IS configuration evidence

registry/list/collection records
    = APIC identity / URL / ID / scope / cross-reference evidence
```

Registry evidence may enrich identity. It must never overwrite or fabricate authoritative artifact configuration.

The resolver should normally consume the compact Phase 1 extracted index first and inspect targeted raw `staging/` evidence only when verification is required.

Do not rescan/reparse the whole raw estate as the primary implementation path.

## Approved Canonical Object Types

Use only the already approved object types:

- `api_artifact`
- `product`
- `plan`
- `consumer_org`
- `application`
- `credential`
- `subscription`
- `catalog_config`
- `catalog_property`

Do not introduce a new object type.

## Approved Evidence / Resolution Vocabulary

Do not invent new taxonomy, state, status, reason, confidence, relationship, or object-type vocabulary.

Where evidence state is required, use only the existing approved values:

- `STRUCTURALLY_CONFIRMED`
- `STRUCTURALLY_INFERRED`
- `RUNTIME_CONFIRMED`
- `VALIDATION_REQUIRED`
- `UNRESOLVED`

Where confidence is required, use only:

- `HIGH`
- `MEDIUM`
- `LOW`

For reference-resolution outcome, use only the already approved values where applicable:

- `RESOLVED`
- `UNRESOLVED`
- `AMBIGUOUS`
- `BROKEN_REFERENCE`

If the implementation needs a concept not representable with the approved vocabulary, stop that specific case, preserve the evidence, and report the gap in `codex/comm/HANSOFF.md`. Do not invent a new label.

## Identity Rules — Mandatory

Primary identity/correlation evidence is:

1. exact APIC self URL;
2. APIC object ID together with compatible org/catalog scope;
3. the approved scoped Product identity bridge;
4. the approved scoped API identity bridge;
5. exact approved mapped Product `$ref` source path;
6. contextual Product-local keys where explicitly allowed below.

Do NOT use any of the following as a primary merge rule:

- name alone;
- title alone;
- name + version alone without the approved scoped bridge evidence;
- fuzzy matching;
- semantic similarity;
- file hash alone;
- inferred graph relationships;
- runtime assumptions.

Hash equality may be retained only as corroborating evidence.

## Required Resolver Lookup Structures

Build deterministic lookup structures from Phase 1 occurrences for at least:

- exact APIC self URL → occurrence(s);
- APIC ID + compatible org/catalog scope → occurrence(s);
- source path → occurrence(s);
- approved mapped Product `$ref` path → matching Product-location API source occurrence;
- Product occurrence + Plan key/name → contextual Plan occurrence;
- Product-local API key → Product-local API reference/occurrence.

Lookup ordering and iteration must be deterministic.

## Required Resolution Scope

### 1. Consumer Organization Identity

Resolve Consumer Organization occurrences by exact APIC identity evidence.

Preserve all contributing occurrences and provenance.

Do not merge by display name alone.

### 2. Application Identity and Consumer Organization Reference

Resolve Application identity from its own APIC identity evidence.

Resolve:

```text
application.consumer_org_url
→ exact consumer_org.url
```

Current validated corpus expectation: 256 / 256 resolve exactly once.

This resolution is identity/reference work only; do not emit Phase 3 graph edges yet.

### 3. Credential Identity and Application Reference

Resolve Credential identity from directly observed identity evidence.

Resolve:

```text
credential.app_url
→ exact application.url
```

Current validated corpus expectation: 270 / 270 resolve exactly once.

Keep the existing strict credential allowlist. Never emit client ID value, client secret value, hashed-secret value, or unknown credential payload fields.

### 4. Subscription Identity and References

Resolve Subscription identity from directly observed identity evidence.

Resolve deterministically:

```text
subscription.app_url
→ application.url

subscription.product_url
→ product.url
```

Current validated corpus expectation:

- Subscription → Application: 1,019 / 1,019
- Subscription → Product: 1,019 / 1,019

Subscription remains structural entitlement evidence only. It does not prove runtime consumption.

### 5. Contextual Plan Resolution

Plan identity is contextual to Product.

Resolve Subscription Plan only after the Product has been resolved:

```text
resolved Product
+ exact subscription.plan value
→ exact Plan inside that Product
```

Never treat Plan name as a globally unique identity.

Current validated corpus expectation: 1,019 / 1,019 Subscription Plan references resolve exactly once inside the resolved Product context.

### 6. Product Authoritative Artifact ↔ Registry Identity Bridge

Implement the already validated Product bridge.

Authoritative Product configuration is the Product YAML under `staging/products/_catalog`.

Registry/list evidence supplies APIC identity/reference enrichment.

The scoped bridge must require the previously validated convergence evidence, including:

- compatible object type/context;
- exact Product name;
- exact declared Product version;
- unique registry candidate;
- Product API-membership agreement where available;
- Plan-name agreement;
- Plan-to-API entitlement agreement.

Do not reduce this to generic name + version matching.

Current validated corpus expectation:

- 499 authoritative Product YAML occurrences;
- 499 uniquely bridge to registry identity;
- 0 authoritative Products unmapped;
- 0 authoritative Products multiply mapped;
- 12 registry-only Products remain without authoritative Product configuration.

The 12 registry-only Products must remain explicit identity/evidence gaps. Do not fabricate Product YAML/configuration for them.

### 7. API Authoritative Artifact ↔ Registry Identity Bridge

Implement the already validated API bridge.

Authoritative API configuration is under `staging/apis/_catalog`.

Registry/list evidence supplies APIC identity/reference enrichment.

The scoped bridge must require the previously validated convergence evidence, including:

- exact API name;
- exact declared API version;
- unique compatible registry candidate;
- unique authoritative API-catalog artifact;
- Product registry/API URL convergence where available;
- Product `$ref` convergence where available.

File/hash equality is corroborating evidence only.

Current validated corpus expectation:

- 2,000 authoritative API definitions;
- 2,000 uniquely bridge to registry identity;
- 0 authoritative APIs unmapped;
- 0 authoritative APIs multiply mapped;
- 36 registry-only APIs remain without authoritative API configuration.

The 36 registry-only APIs must remain explicit identity/evidence gaps. Do not fabricate API configuration for them.

### 8. Product `$ref` Resolution

Consume the Phase 1 preserved fields:

- exact raw Product API `$ref`;
- approved mapped repository-relative `staging/...` path.

Resolve only the approved mapped path to the Product-location API source occurrence.

Do not introduce any additional path normalization.

Current validated corpus expectation:

- 2,244 Product API `$ref` occurrences;
- each maps to exactly one existing source file.

Preserve both raw `$ref` and mapped path in resolution provenance.

### 9. Product-Location API Occurrences

The 2,357 API-shaped documents under Product locations remain source occurrences, not independent canonical API identities merely because files exist.

Associate a Product-location API occurrence to an authoritative API identity only where the approved identity bridge and `$ref`/registry evidence agree.

Do not use byte identity alone as the canonical identity rule.

Preserve the two known hash-different Product-location API copies as distinct source evidence attached only when the approved bridge proves the same API identity.

### 10. Product-Local API and Plan Keys

Within a resolved Product context:

- resolve Product-local API keys against that Product's API map;
- resolve Product-local Plan keys/names against that Product's Plans;
- resolve Plan API keys through the same Product's API map.

Current validated corpus expectation for Plan API references: 2,432 / 2,432 valid.

Do not create global Plan-key or API-key identity rules from these local keys.

### 11. Registry-Only and Artifact-Only Evidence

Preserve registry-only and artifact-only cases explicitly.

A registry-only object may have a resolved APIC identity while its authoritative configured artifact remains absent from the corpus.

Do not convert missing configuration into synthetic configuration.

Do not convert absence of registry enrichment into absence of the authoritative artifact.

## Canonical APIC AS-IS Identity Output

Produce a compact deterministic Phase 2 identity-resolution index under `indexes/`.

Use a clear implementation-owned filename consistent with repository conventions. Report the exact chosen path in the handoff.

Each canonical identity record should preserve at minimum, when applicable:

- deterministic canonical identity record ID;
- approved canonical object type;
- directly observed APIC ID/self URL;
- org/catalog scope evidence;
- name/title/declared version as observed;
- authoritative artifact occurrence reference(s);
- registry occurrence reference(s);
- Product-location/source-copy occurrence reference(s);
- contributing Phase 1 `extracted_record_id` values;
- source paths/pointers needed for provenance;
- raw and mapped Product `$ref` evidence where applicable;
- approved evidence/reference-resolution state where applicable;
- confidence only when needed and only from the approved confidence vocabulary;
- explicit unresolved/ambiguous/broken-reference evidence without guessing.

A canonical identity record ID is an implementation identifier for the resolved APIC AS-IS object. It must not be presented as a Logical API ID, business capability ID, or Kong ID.

Keep output compact. Prefer references back to Phase 1 evidence rather than duplicating large raw payloads.

## Determinism

The resolver must be deterministic.

Validate at minimum:

- deterministic canonical record IDs;
- deterministic ordering;
- repeated full-corpus runs produce byte-identical output;
- the same Phase 1 input produces the same resolution result;
- no environment/time/random ordering leakage affects output.

Report the repeated-run SHA-256 values.

## Provenance Requirements

Every resolved canonical object must remain traceable to its contributing source occurrences.

Do not discard an occurrence simply because another occurrence is authoritative.

Preserve enough provenance to answer:

- which authoritative artifact defines this configured object?
- which registry evidence enriched its APIC identity?
- which Product-local copies/references point to it?
- which evidence was unresolved, ambiguous, or missing?

## Explicit Non-Goals — Mandatory

Task 006 must NOT:

- build the Phase 3 relationship graph / CodeGraph edges;
- assign Domain;
- assign Exposure Channel;
- create Logical API or Logical Capability identities;
- classify business capability;
- classify backend or infer `api_invokes_target`;
- infer runtime usage;
- analyze runtime analytics;
- perform duplicate/overlap detection;
- declare APIs retired;
- produce migration candidates;
- redesign Products/Plans;
- map APIC objects directly to Kong objects;
- design Kong Gateway Services/Routes/Consumers;
- change the approved canonical ontology/taxonomies.

Reference resolution performed internally by the resolver is allowed; emitting the semantic relationship graph is not.

## Validation Requirements

Add focused Phase 2 tests covering at minimum:

- exact self-URL lookup;
- APIC ID + compatible scope lookup;
- rejection of name-only merge;
- Product scoped bridge;
- API scoped bridge;
- contextual Plan identity;
- Application → Consumer Org exact URL resolution;
- Credential → Application exact URL resolution;
- Subscription → Application/Product/Plan resolution;
- Product `$ref` mapped-path resolution;
- registry-only Product preservation;
- registry-only API preservation;
- ambiguous/unresolved reference preservation without guessing;
- Product-location API occurrence association only with approved convergence evidence;
- credential redaction remains intact;
- deterministic repeated output;
- source `staging/` files remain unchanged.

Run against the current full Phase 1 extracted index and report observed resolution counts against the validated corpus expectations above.

If a count differs, do not force the implementation to match the expected number. Preserve the evidence and report the discrepancy.

## Regression Guardrails

- Phase 0 is frozen.
- Phase 1 is frozen after Task 005 acceptance for Phase 2 entry.
- Do not redesign Phase 1 because Phase 2 discovers new evidence.
- Change Phase 1 only if a reproducible Phase 1 defect directly blocks Phase 2, and report it before making a broad change.
- Do not fix the known Phase 0 fixture packaging issue.
- Do not change `.gitignore`.
- Do not modify raw `staging/`.
- Do not modify `CURRENT_TASKS.md` or prompt files.
- Do not create new design/review/result Markdown files.

## Handoff Reporting

Update only:

`codex/comm/HANSOFF.md`

Report:

1. files created/modified;
2. resolver implementation structure;
3. exact Phase 2 output/index path;
4. full-corpus canonical identity counts by approved object type;
5. source occurrence → canonical identity coverage;
6. exact URL and ID+scope resolution findings;
7. Product bridge results;
8. API bridge results;
9. contextual Plan resolution results;
10. Subscription/Application/Consumer Org/Credential resolution counts;
11. Product `$ref` resolution counts;
12. registry-only / artifact-only counts;
13. unresolved, ambiguous, or broken-reference evidence;
14. credential-redaction validation;
15. deterministic repeated-run SHA-256 values;
16. focused and repository-wide tests executed and results;
17. any discrepancy from the validated corpus expectations;
18. whether Phase 2 Task 006 is ready for architecture review.

Do not invent vocabulary to describe gaps; use plain language when the approved taxonomy does not represent a finding.

## Stop Condition

Implement Task 006 only.

Validate the deterministic APIC identity resolver, update `codex/comm/HANSOFF.md`, commit the implementation and handoff changes, push, and stop.

Do not begin Phase 3 relationship reconstruction.
