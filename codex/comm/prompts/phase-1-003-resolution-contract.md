# Phase 1 — Task 003: Deterministic Resolution Contract

## Objective

Define the deterministic Resolution Contract that connects the APIC staging evidence into one structural AS-IS model.

This task is design/evidence validation only.

Do **not** implement Python.
Do **not** create or modify indexes.
Do **not** build CodeGraph yet.
Do **not** introduce any new taxonomy, status, reason, canonical object type, or relationship type.

Use only the already-approved project vocabulary and relationship taxonomy.

The purpose of this task is to establish exactly **how existing IDs, URLs, list/catalog records, file references, Product membership, Plan membership, and Subscription references connect the APIC estate together**.

## Architecture Direction

The APIC export appears to contain two complementary forms of structural evidence:

1. **Registry / identity evidence**
   - `list.json` / catalog summary objects
   - object IDs
   - self `url`
   - names / versions
   - organization/catalog scope URLs

2. **Configuration / relationship evidence**
   - detailed JSON resources
   - Product YAML
   - API definitions
   - Product `apis.*.$ref`
   - Product `plans.*.apis`
   - Application `consumer_org_url`
   - Credential `app_url` / Consumer Org reference
   - Subscription `app_url`, `consumer_org_url`, `product_url`, and Plan value

The resolver must decode these deterministic references.

Do not infer semantic relationships when a deterministic reference is absent.

## Important Working Hypothesis to Validate

The project currently expects that `list.json` / catalog summary files may provide the registry view for most or all APIC management objects.

Validate this from the available staging evidence.

Do not assume it is complete merely because representative examples contain IDs and URLs.

Report:

- which object types have a registry/list representation;
- which fields are consistently present;
- which objects appear only in detailed/configuration files;
- any mismatch between list representation and detailed representation;
- whether the same self URL / ID appears consistently across representations.

Do not perform a full semantic repository analysis. Use deterministic inspection and representative/aggregate evidence sufficient to validate the resolution rules.

## Existing Canonical Object Types

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

No new object types.

## Existing Relationship Types

Use only the already-approved relationship taxonomy:

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

Task 003 focuses only on the relationships that can be resolved from the current registry/configuration evidence listed below.

Do not implement backend or catalog-property resolution in this task.

## Resolution Contract to Validate

### A. Consumer Organization

Expected evidence:

- Consumer Org registry/list record:
  - `id`
  - `url`
  - `name`
  - `org_url`
  - `catalog_url`
- Consumer Org detailed resource may contain the same values.
- Application and Subscription may reference the Consumer Org through `consumer_org_url`.

Validate deterministic resolution:

```text
application.consumer_org_url
    → consumer_org.url

subscription.consumer_org_url
    → consumer_org.url
```

Primary identity evidence is exact APIC self URL where present.

Object ID plus compatible observed scope may be retained as secondary identity evidence.

Do not merge by name.

### B. Application

Expected evidence:

- Application list/detail record:
  - `id`
  - `url`
  - `consumer_org_url`
  - `app_credential_urls`
  - organization/catalog scope
- Credential and Subscription may reference the Application by URL.

Validate deterministic resolution:

```text
credential.app_url
    → application.url

subscription.app_url
    → application.url
```

Also validate whether `app_credential_urls` provide reverse/reference evidence to Credential objects.

Do not create a new relationship type for reverse evidence.

### C. Credential

Expected evidence:

- credential object self ID/URL;
- Application URL;
- Consumer Org URL;
- secret/client fields that must remain redacted.

Validate whether Credential self URLs match Application `app_credential_urls`.

Credential values, client IDs, client secrets, and hashed-secret values must never be copied into reports.

Only presence metadata may be reported.

### D. Subscription

Expected evidence:

- subscription self ID/URL where available;
- `app_url`;
- `consumer_org_url`;
- `product_url`;
- Plan value/reference.

Validate:

```text
subscription.app_url
    → application.url

subscription.product_url
    → product.url

subscription plan value
    → plan within the resolved Product context
```

Consumer Org URL is corroborating structural evidence.

Subscription is configured entitlement/association evidence only.

It does not prove runtime usage.

### E. Product

Validate both representations:

1. Product registry/catalog summary:
   - ID
   - self URL
   - name
   - version
   - API URLs/references if present
   - Plan information if present

2. Product YAML:
   - `info.name`
   - `info.version`
   - `apis.*.$ref`
   - `plans`

Determine exactly how a Product summary/list record can be deterministically correlated with its Product YAML/full representation.

Use APIC ID/URL when directly available.

Where the full Product YAML lacks self URL/ID, identify what deterministic evidence exists to correlate it with the registry representation.

Do not automatically merge on name alone.

If deterministic correlation is not available for a case, report the gap rather than inventing a rule.

### F. Product → API Membership

This relationship is independent of Subscription.

Validate:

```text
Product.apis.<api-key>.$ref
    → API Artifact source file / API representation
```

and whether Product list/catalog summary contains API URLs that can independently resolve to API registry entries.

The approved relationship is:

`product_contains_api`

Important:

A Product may contain an API even if no Subscription exists.

### G. Product → Plan

Plans are embedded inside Product configuration.

Validate:

```text
Product
    → plans.<plan-key>
```

The approved relationship is:

`product_contains_plan`

Do not assume a Plan name such as `default-plan` is globally unique.

Plan identity must remain contextual to its parent Product unless direct APIC Plan identity evidence exists.

### H. Plan → API Entitlement

Validate:

```text
Product.plans.<plan-key>.apis.<api-key>
    → API already referenced by Product.apis.<api-key>
```

The approved relationship is:

`plan_entitles_api`

Determine whether the Plan API key maps deterministically to the Product API key and therefore to the same API Artifact.

Report mismatches explicitly.

### I. API Registry / API Artifact

Inspect the available evidence under:

`staging/apis/_catalog`

and associated API list/catalog summary evidence.

Determine:

- registry/list representation of APIs;
- ID and URL availability;
- name/version availability;
- how the registry API object correlates to the full OpenAPI/API YAML;
- how Product `$ref` paths correlate to those API files;
- whether API files copied under Product locations are duplicates/representations of the same APIC API artifact or merely source copies requiring later resolution.

Do not use file hash alone as canonical identity.

Do not infer Logical API or functional duplication.

## Resolver Lookup Model

Validate whether the following deterministic lookup model is sufficient:

```text
Exact APIC self URL
    → APIC object occurrence(s)

APIC object ID + observed compatible scope
    → APIC object occurrence(s)

Source file path
    → extracted source occurrence

Product API $ref path
    → API source occurrence

Resolved Product + Plan key
    → Plan occurrence

Product API key
    → Product-contained API occurrence

Plan API key
    → Product API key → API occurrence
```

Do not invent fallback matching algorithms in this task.

If an exact deterministic lookup cannot resolve a case, leave it unresolved and report the evidence gap.

## Required Findings in HANSOFF.md

Report only in `codex/comm/HANSOFF.md`:

1. Registry/list coverage by canonical object type.
2. Exact identity fields available per object type.
3. Exact reference fields available per object type.
4. For each relationship below, whether deterministic resolution is:
   - supported by observed evidence,
   - partially supported,
   - or not supported by current evidence.

Relationships to assess:

- `application_belongs_to_consumer_org`
- `credential_belongs_to_application`
- `subscription_belongs_to_application`
- `subscription_targets_product`
- `subscription_uses_plan`
- `product_contains_api`
- `product_contains_plan`
- `plan_entitles_api`

Do not create new status taxonomy to express this. Use plain prose/table wording only.

5. Exact deterministic join key for every supported relationship.
6. Any relationship where multiple possible targets are observed.
7. Any broken/unmatched reference evidence.
8. Any mismatch between list records and detailed records.
9. Whether Product YAML can be correlated deterministically to Product registry/list records.
10. Whether API full definitions can be correlated deterministically to API registry/list records.
11. Whether Product `$ref` and Plan API keys deterministically reach the same API artifacts.
12. A proposed minimal resolver order using only exact IDs/URLs/paths/keys already present in evidence.
13. Any evidence gap that must be resolved before Phase 1 implementation or Phase 2 resolver implementation.

## Taxonomy Freeze

Do not invent:

- new extraction statuses;
- new resolution statuses;
- new reason codes;
- new source representation types;
- new object types;
- new relationship types;
- new confidence values;
- new semantic classifications.

If a gap exists, describe the gap in plain language in `HANSOFF.md`.

## Reporting Rule — Mandatory

The only reporting artifact for this task is:

`codex/comm/HANSOFF.md`

Do not create any other report, design, result, summary, review, or Markdown artifact.

## Non-Goals

Do not:

- implement Python;
- modify tests;
- fix the Phase 0 fixture packaging issue;
- modify Phase 0;
- generate indexes;
- build the graph;
- create canonical IDs;
- normalize URLs;
- merge by names;
- perform semantic duplicate detection;
- classify Domain;
- classify Exposure Channel;
- resolve backends;
- infer runtime usage;
- map to Kong.

## Stop Condition

Stop after updating `codex/comm/HANSOFF.md`.

Wait for architecture review before implementation.
