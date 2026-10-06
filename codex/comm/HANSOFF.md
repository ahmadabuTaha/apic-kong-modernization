# Codex Handoff

## Task executed

Phase 1 / Phase 2 Boundary — Task 003: Deterministic Resolution Contract. Evidence validation and resolution design only; no implementation.

## Prompt file used

`codex/comm/prompts/phase-1-003-resolution-contract.md`

## Summary of what was done

- Inspected registry, collection, detailed-resource, Product YAML, API YAML, and existing Phase 0 provenance evidence without modifying it.
- Measured registry/list coverage and required-field presence for each in-scope canonical object type.
- Tested exact self-URL joins for Consumer Organization, Application, Credential, Subscription, Product, Plan-summary, and API-summary evidence.
- Tested Application reverse credential references without creating a reverse relationship type.
- Validated Product summary API URLs and Plan API URLs against API registry self URLs.
- Validated Product YAML `$ref` paths, Product API keys, embedded Plan keys, and Plan API keys.
- Compared registry and full YAML representations to identify deterministic joins, corroborating-only evidence, missing representations, and resolution gaps.
- Defined a minimal resolver order using only exact URLs, scoped IDs, source paths, Product-scoped Plan keys, and Product API keys.
- Confirmed that Product membership is independent of Subscription and that Subscription evidence does not prove runtime usage.

## Validation boundary

This task used deterministic aggregate inspection. Names, versions, and file hashes were measured only to characterize corroborating evidence and gaps; they were not used to merge occurrences or assert canonical identity. No URL normalization, semantic matching, backend resolution, graph construction, or runtime inference was performed.

Credential inspection was restricted to counts, IDs/self URLs, Application and Consumer Organization reference URLs, reverse credential URLs, and secret-field presence. No client ID, secret, or hashed-secret value was copied into this handoff.

## 1. Registry/list coverage by canonical object type

| Canonical object type | Observed registry/configuration representation | Coverage finding |
|---|---|---|
| `api_artifact` | `staging/apis/_catalog/_list.json` plus full API definitions in `staging/apis/_catalog`; additional API source copies under `staging/products/_catalog` | API registry has 2,036 records. There are 2,000 full API definitions under the API catalog and 2,357 API source copies under the Product catalog. |
| `product` | `staging/products/_catalog/_list.json` plus Product YAML | Product registry has 511 records. There are 499 Product YAML documents. |
| `plan` | Embedded in Product registry records and Product YAML | No independent Plan registry/self URL was observed. Product registry has 596 Plan occurrences; Product YAML has 584 Plan occurrences. Plan identity is Product-contextual. |
| `consumer_org` | Global `_list.json` plus one detailed resource per organization | 28 registry records and 28 detailed resources; all pair exactly by self URL. |
| `application` | Per-Consumer-Organization collection files under `staging/apps` | 256 collection records. No separate global registry file or second detailed representation was observed. |
| `credential` | Per-Application collection files under `staging/credentials` | 270 collection records. No separate global registry file or second detailed representation was observed. |
| `subscription` | Per-Application collection files under `staging/subscriptions` | 1,019 collection records. No separate global registry file or second detailed representation was observed. |
| `catalog_config` | Detailed catalog and catalog-setting YAML roots | The catalog root has direct ID/self URL evidence. The catalog-setting root has its own URL and configuration evidence but no independent list representation was observed. |
| `catalog_property` | Ten supported configuration JSON collections | All ten observed collections are empty; zero property items are available to validate identity or references. Backend and catalog-property resolution remain outside Task 003. |

The working hypothesis is only partly correct. API, Product, and Consumer Organization have explicit registry/list views. Application, Credential, and Subscription have APIC collection records with full identity/reference fields but no separate global list/detail pair. Plan is embedded. Catalog configuration is detailed-only, and no Catalog Property item is present.

## 2. Exact identity fields available

| Canonical object type | Exact identity evidence observed |
|---|---|
| `api_artifact` registry | All 2,036 records contain `id`, self `url`, `name`, `version`, `org_url`, and `catalog_url`. IDs and self URLs are unique; every self URL terminates in its stated ID. |
| Full API definition under API catalog | All 2,000 expose API name and version in API metadata. Zero have a top-level APIC object `id` or self `url`. |
| API copy under Product catalog | 2,357 full API-shaped documents expose name/version metadata but not registry identity. |
| `product` registry | All 511 records contain `id`, self `url`, `name`, `version`, `org_url`, and `catalog_url`. IDs and self URLs are unique; every self URL terminates in its stated ID. |
| Product YAML | All 499 expose `info.name` and `info.version`. Zero have a top-level APIC object `id` or self `url`. |
| `plan` | Product-scoped Plan key/name. No independent Plan ID/self URL was observed. Plan name is not globally unique. |
| `consumer_org` | All 28 registry and 28 detailed records contain `id`, self `url`, `name`, `org_url`, and `catalog_url`. Registry and detail values match on all these fields after exact self-URL pairing. |
| `application` | All 256 contain `id`, self `url`, `name`, `consumer_org_url`, `org_url`, and `catalog_url`. IDs and URLs are unique. |
| `credential` | All 270 contain `id`, self `url`, `name`, `app_url`, `consumer_org_url`, `org_url`, and `catalog_url`. IDs and URLs are unique. |
| `subscription` | All 1,019 contain `id`, self `url`, `name`, `app_url`, `consumer_org_url`, `product_url`, Plan value, `org_url`, and `catalog_url`. IDs and URLs are unique. |
| `catalog_config` | Catalog root ID/self URL; catalog-setting URL plus observed organization/catalog scope fields. |
| `catalog_property` | No item-level evidence because all observed collections are empty. |

Within each API, Product, Consumer Organization, Application, Credential, and Subscription registry/collection, no duplicate self URLs or IDs were observed and no ID disagreed with the terminal segment of its self URL.

## 3. Exact reference fields available

| Source object | Exact reference evidence |
|---|---|
| Application | `consumer_org_url`; `app_credential_urls` as reverse/corroborating references. |
| Credential | `app_url`; `consumer_org_url`. |
| Subscription | `app_url`; `consumer_org_url`; `product_url`; Product-contextual Plan value. |
| Product registry | `api_urls`; embedded `plans[].name`; embedded `plans[].apis[].id` and `.url`. |
| Product YAML | `apis.<api-key>.$ref`; `plans.<plan-key>`; `plans.<plan-key>.apis.<api-key>`. |
| API registry | API self `url` and scoped object `id`; no source-file path field was observed. |
| Consumer Organization | Self `url`, referenced exactly by Applications, Credentials, and Subscriptions. |

Reference strings were compared exactly. The only path translation examined was the explicit `/staging/` suffix carried by every Product `$ref`; the required handling of that export-root difference is recorded as a resolver gap below.

## 4. Relationship resolution assessment

The wording in the assessment column is descriptive for this handoff and does not define a new status vocabulary.

| Approved relationship | Assessment from observed evidence | Exact deterministic join | Aggregate result |
|---|---|---|---|
| `application_belongs_to_consumer_org` | Supported by observed evidence | `application.consumer_org_url = consumer_org.url` | 256 of 256 matched exactly one Consumer Organization; none unmatched or multiple. |
| `credential_belongs_to_application` | Supported by observed evidence | `credential.app_url = application.url` | 270 of 270 matched exactly one Application. All 270 Application `app_credential_urls` matched one Credential self URL, and every Credential self URL appeared in the owning Application's reverse list. |
| `subscription_belongs_to_application` | Supported by observed evidence | `subscription.app_url = application.url` | 1,019 of 1,019 matched exactly one Application; none unmatched or multiple. |
| `subscription_targets_product` | Supported by observed evidence | `subscription.product_url = product.url` | 1,019 of 1,019 matched exactly one Product registry record; none unmatched or multiple. |
| `subscription_uses_plan` | Supported by observed evidence | Exact `subscription.product_url` first, then exact Subscription Plan value to `product.plans[].name` inside that Product | 1,019 of 1,019 matched exactly one Plan in the resolved Product; none unmatched or multiple. |
| `product_contains_api` | Partially supported across both representations | Registry path: `product.api_urls[] = api.url`. YAML path: Product API key to its `$ref`, then explicit export-root path mapping to a source occurrence. | All 2,611 Product registry API URLs matched exactly one API registry record. All 2,244 Product YAML API entries have `$ref` values whose `/staging/` suffix reaches one local source file. The unresolved gap is identity correlation between Product YAML and Product registry, and between API YAML/source copies and API registry records. |
| `product_contains_plan` | Supported by observed evidence within each Product occurrence | Product occurrence plus exact embedded Plan key/name | Product YAML contains 584 Plans; Product registry contains 596. No Product registry record has duplicate Plan names. Global Plan names are not unique and are never used without Product context. |
| `plan_entitles_api` | Supported by observed evidence within each Product occurrence | YAML: `plans.<plan-key>.apis.<api-key>` to the same Product's `apis.<api-key>`. Registry: embedded Plan API URL to the same Product's `api_urls` and API registry `url`. | All 2,432 YAML Plan API entries reference an existing Product API key. All 2,799 registry Plan API URLs occur in the parent Product's API URL list and match exactly one API registry record. No mismatches were observed. |

Subscription Consumer Organization URLs also matched exactly one Consumer Organization for all 1,019 records, and Credential Consumer Organization URLs matched for all 270 records. These corroborate scope but do not create additional relationship types in this task.

## 5. Multiple possible targets

- No exact self-URL reference resolved to multiple Consumer Organizations, Applications, Credentials, Products, or APIs.
- No Product registry record contains duplicate API URLs or duplicate Plan names.
- Plan names are not globally unique: 596 Plan occurrences use only 40 distinct names; 14 names are reused, and the most reused name occurs 489 times. A Plan value therefore has multiple possible targets if Product context is omitted. Exact Product resolution must precede Plan lookup.
- Exact name/version comparisons happened to be unique for the observed Product and API full documents, but names remain secondary evidence and were not accepted as identity joins.

## 6. Broken or unmatched reference evidence

- No unmatched exact management-URL reference was observed for the assessed Consumer Organization, Application, Credential, Subscription, Product, Plan-summary, or API-summary joins.
- No Product YAML Plan API key was absent from the same Product's `apis` map.
- Five Product YAML API keys are not referenced by any Plan in their Product. This is valid Product membership evidence, not a broken relationship: `product_contains_api` is independent of `plan_entitles_api` and Subscription.
- All 2,244 Product API `$ref` values are absolute paths from the source export host, so zero raw absolute paths exist on this workstation. Every value contains an exact `/staging/` suffix, and all 2,244 suffix-derived repository paths exist. A resolver must not silently rewrite paths; architecture must approve and record the export-root-to-repository-root mapping.

## 7. Registry/detail and representation mismatches

### Consumer Organization

The list and detail representations are complete and consistent for the inspected identity/scope fields: 28 exact URL pairs, no missing counterpart, no multiple match, and no ID/name/organization/catalog mismatch.

### Product

- Product registry: 511 records; Product YAML: 499 documents.
- Product YAML contains no APIC ID/self URL. There is therefore no primary deterministic identity key to join a Product YAML document to a Product registry record.
- Exact name plus version produces one registry candidate for each of the 499 Product YAML documents, and 12 registry Products have no Product YAML counterpart. This is corroborating evidence only and must not trigger a merge.
- When the 499 unique name/version candidate pairs are compared for validation only, Product API membership sets, Plan-name sets, and all 584 Plan API entitlement sets agree exactly. The agreement strengthens the case for a missing export manifest/identity field but does not replace one.

### API

- API registry: 2,036 records; full definitions under `staging/apis/_catalog`: 2,000.
- Full API definitions contain no top-level APIC ID/self URL. There is no primary deterministic key joining a full definition to its registry record.
- Exact API name plus version produces one registry candidate for each of the 2,000 full definitions, while 36 registry APIs have no full definition under the API catalog. This remains corroborating evidence only.
- There are 2,357 API-shaped source copies under `staging/products/_catalog`. All have one exact name/version registry candidate. Of these, 2,355 have a byte-identical API-catalog file and two do not. File hash alone is not canonical identity, so neither case authorizes an identity merge.
- The 2,244 files reached by Product YAML `$ref` occurrences all have one name/version registry candidate; 2,242 have a byte-identical API-catalog file and two do not. These are source occurrences requiring Phase 2 identity resolution, not automatically distinct or merged API artifacts.

## 8. Product YAML to Product registry correlation

Product YAML cannot currently be correlated to Product registry records by an approved primary deterministic key. The YAML lacks APIC object ID and self URL, and the Product registry provides no source-file path. Name/version, membership equality, and matching Plan structures are strong corroboration, but Task 003 prohibits name-based merging and fallback algorithms.

Required disposition: preserve both occurrences and leave their common APIC identity unresolved until an export manifest, embedded APIC identity field, or architecture-approved existing identity mapping is available.

## 9. API definition to API registry correlation

Full API definitions likewise cannot currently be correlated to API registry records by APIC self URL, object ID, or registry-provided source path. Unique name/version correspondence and identical file hashes are secondary evidence only. The same applies to API copies stored under Product locations.

Required disposition: the API registry records, API-catalog definitions, and Product-location copies remain separate source occurrences until Phase 2 receives an approved deterministic identity bridge.

## 10. Product `$ref` and Plan API key convergence

Within each Product YAML occurrence, convergence is deterministic:

1. `Product.apis.<api-key>.$ref` identifies the referenced API source path after an explicit export-root mapping.
2. `Product.plans.<plan-key>.apis.<api-key>` uses the same Product-local API key.
3. All 2,432 observed Plan API entries find that key in the parent Product's `apis` map.

Within each Product registry occurrence, convergence is also deterministic:

1. Every embedded Plan API URL is present in the same Product's `api_urls`.
2. Every one of the 2,799 Plan API URL occurrences resolves to exactly one API registry self URL.

The unresolved step is joining the YAML-side Product/API occurrences to the registry-side Product/API occurrences. The two representations cannot yet be declared the same canonical objects solely from name/version or file hash.

## 11. Minimal resolver order

1. Index every directly observed APIC self URL without normalization and retain all source occurrences for each key.
2. Index APIC object ID together with directly observed organization/catalog scope. Use it only when type and scope are compatible; do not override conflicting self-URL evidence.
3. Resolve `application.consumer_org_url`, `credential.app_url`, `credential.consumer_org_url`, `subscription.app_url`, `subscription.consumer_org_url`, and `subscription.product_url` by exact self URL.
4. Validate Application `app_credential_urls` against Credential self URLs as reverse/corroborating evidence for `credential_belongs_to_application`; emit no new relationship type.
5. Resolve Subscription Plan only after Product URL resolution, using the exact Plan value within that Product.
6. Resolve Product registry `api_urls` and embedded Plan API URLs against exact API registry self URLs. Resolve Plan names only within their parent Product.
7. For Product YAML, resolve the exact Product API key and Plan key in the same document. Resolve each Plan API key through the same Product's `apis` map.
8. Resolve Product `$ref` to a source occurrence only after architecture supplies an explicit source-export-root to repository-`staging/` mapping. Preserve both the raw `$ref` and mapped source path.
9. Leave Product YAML-to-registry and API YAML-to-registry identity unresolved until a primary deterministic bridge is supplied. Do not use name, name/version, or hash as an automatic merge key.
10. After Phase 2 identity resolution, Phase 3 may emit only the approved structural relationships. Subscription remains entitlement/association evidence and never runtime usage evidence.

## 12. Evidence gaps before implementation

- No deterministic primary identity bridge is present between Product YAML and Product registry records.
- No deterministic primary identity bridge is present between full/copy API definitions and API registry records.
- The source export's absolute root is absent locally. The observed `/staging/` suffix maps all Product references, but that mapping requires an explicit contract rather than silent path rewriting.
- Twelve Product registry records lack Product YAML counterparts, and 36 API registry records lack full definitions under the API catalog.
- Two Product-location API copies differ by hash from all API-catalog files despite having a unique name/version registry candidate. This is a review point, not duplicate or identity evidence.
- No non-empty Catalog Property collection is available to validate item identity or `api_uses_catalog_property`; that relationship is outside this task in any event.
- The architecture-owned Canonical API Record field contract and approved global Phase 2 resolution states remain absent from the repository. Task 003 does not recreate them.

These gaps do not invalidate the exact URL joins. They prevent a complete end-to-end canonical resolution contract from being implemented without architecture decisions or additional identity evidence.

## Existing test finding

The known Phase 0 test fixture packaging issue remains outside scope. `tests/test_profiler.py` references `tests/fixtures/repository_profile/staging`, but that fixture tree is absent and the broad `staging/` ignore rule would ignore it. The task explicitly forbids modifying tests or fixing this issue.

## Files created

None.

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- `.venv/bin/pytest`

## Test results

- 7 tests collected: 2 passed and 5 errored during fixture setup.
- All five errors are caused by the absent `tests/fixtures/repository_profile/staging` source directory.
- The result reproduces the known repository/fixture packaging issue; it does not reproduce a Phase 0 profiling defect with a valid source tree.

## Generated artifacts

- `codex/comm/HANSOFF.md` is the sole task artifact.
- No files were created or modified under `staging/`, `indexes/`, or `outputs/`.

## Important findings

- Every assessed management-URL reference resolves uniquely with no unmatched target in the observed registry/collection evidence.
- Product registry API membership and embedded Plan entitlements resolve exactly to API registry URLs.
- Product YAML Plan API keys resolve exactly through the Product-local API map.
- Product/API full YAML occurrences cannot be joined to registry identities using primary APIC identity evidence because they lack APIC self IDs/URLs and registry records lack source paths.
- Name/version and hash evidence is corroborating only and must not be used for automatic identity merging.
- Product membership exists independently of Plan entitlement and Subscription; five Product API keys are not referenced by a Plan in the observed YAML evidence, which is not by itself a broken relationship.

## Unresolved issues

- Architecture must provide an approved deterministic bridge for Product YAML-to-registry identity.
- Architecture must provide an approved deterministic bridge for API YAML/copy-to-registry identity.
- Architecture must approve and specify the export-root-to-repository-`staging/` path mapping before Product `$ref` resolution is implemented.
- The Canonical API Record contract and approved Phase 2 resolution states must be made available before implementation.
- The known test fixture packaging issue remains unresolved by instruction.

## Assumptions

- APIC collection records under Applications, Credentials, and Subscriptions are registry-quality identity occurrences even though no separate global `_list.json` exists for those types.
- Direct string equality is required for URL joins; no case, slash, scheme, host, or encoding normalization was applied.
- Product Plan identity is the resolved parent Product plus exact Plan key/name because no direct Plan ID/self URL was observed.
- The observed `/staging/` path suffix is evidence of an export-root boundary, but it is not an authorized mapping until architecture approves the contract.
- Existing Phase 0 file hashes are used only to describe exact source-copy equality and never as canonical identity.

## Deviations from the prompt

None.

## Recommended next step

Integration Architect and Enterprise Architect review the three blocking contract decisions: Product YAML identity mapping, API definition/copy identity mapping, and export-root path mapping. Supply the existing Canonical API Record and Phase 2 resolution contracts before authorizing implementation. Do not begin implementation or the next task until `CURRENT_TASKS.md` is updated.

## Final status

REVIEW_REQUIRED
