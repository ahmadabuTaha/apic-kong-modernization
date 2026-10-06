# Codex Handoff

## Task executed

Phase 1 / Phase 2 Boundary — Task 004: Source Precedence and Identity Bridge Closure. Architecture/evidence validation only; no implementation.

## Prompt file used

`codex/comm/prompts/phase-1-004-source-precedence-and-identity-bridge.md`

## Summary of what was done

- Applied the architecture decision that configuration artifacts under `staging/` are authoritative for AS-IS configuration content and registry/list records supply APIC identity and reference evidence.
- Validated the scoped Product artifact-to-registry bridge using exact name/version uniqueness plus complete structural corroboration.
- Validated the scoped authoritative API definition-to-registry bridge using exact name/version uniqueness, authoritative-candidate uniqueness, and Product membership convergence where available.
- Validated all Product API `$ref` values using only the approved exact `/staging/` export-root mapping.
- Characterized Product-location API documents as source occurrences and evaluated the two hash-different cases without treating hash equality or inequality as identity proof.
- Applied source precedence to registry-only Product/API records and checked for authoritative artifacts without registry counterparts.
- Defined the final resolver precedence and assessed whether the Task 003 resolution-contract gaps are closed.
- Carried forward the exact management-URL joins already validated in Task 003 without reopening them; no contradictory evidence was found.

## Validation boundary

This was read-only deterministic evidence validation. No Python was implemented, no URL was normalized, no graph edge was built, and no semantic, backend, runtime, duplicate, Domain, Exposure Channel, or Kong inference was performed.

Credential source values were not inspected or copied. This handoff contains no client ID, secret, or hashed-secret value.

## 1. Source-precedence decision

The source-precedence decision resolves the conceptual conflict from Task 003.

- The artifact is authoritative for configured AS-IS content.
- The registry record is authoritative evidence for APIC management ID, self URL, catalog/organization scope, and registry cross-references.
- A deterministic bridge enriches the artifact with registry identity; it does not permit registry content to overwrite artifact configuration.
- A registry record without an artifact remains registry-only evidence.
- An artifact without a registry record would remain authoritative configuration evidence with missing registry identity.
- Product-location API documents remain source occurrences. They neither override authoritative API-catalog definitions nor become separate API identities without separate identity evidence.

This separation permits deterministic identity enrichment without declaring `list.json` the single source of truth and without introducing a generic name-based merge rule.

## 2. Product identity bridge

### Evidence contract

For this APIC export only, an authoritative Product YAML may receive one Product registry identity when all of the following hold:

1. the source is a Product artifact in the Product catalog directory;
2. Product object type and catalog context agree;
3. `info.name` exactly equals registry Product name;
4. `info.version` exactly equals registry Product version;
5. exactly one registry candidate exists;
6. API membership agrees after exact Product registry API-URL resolution and approved Product `$ref` mapping;
7. Plan names agree within the Product context;
8. Plan-to-API entitlement membership agrees.

This is a scoped composite bridge for the observed export structure. It is not a rule that name plus version establishes identity.

### Aggregate result

| Finding | Result |
|---|---:|
| Authoritative Product YAML artifacts | 499 |
| Uniquely bridged to one registry identity | 499 |
| Authoritative Product YAML artifacts without registry identity | 0 |
| Authoritative Product YAML artifacts with multiple registry candidates | 0 |
| Bridged artifacts with API membership disagreement | 0 |
| Bridged artifacts with Plan-name disagreement | 0 |
| Bridged Plan occurrences with API entitlement disagreement | 0 of 584 |
| Product registry records without Product YAML | 12 |

All 499 authoritative Products therefore receive one APIC Product ID/self URL as enrichment while retaining YAML as the authoritative configuration content. The 12 unmatched registry Products are not reconstructed from registry summaries.

The 12 registry-only Products contain 367 registry API-URL occurrences, 12 Plan occurrences, and 367 Plan API occurrences. Thirty-four Subscription occurrences target these Products by exact Product URL. Those references remain valid registry/entitlement evidence, but the missing Product YAML configuration remains explicit.

No Product artifact-only case or bridge conflict was observed.

## 3. API Artifact identity bridge

### Evidence contract

For this APIC export only, an authoritative API definition under `staging/apis/_catalog` may receive one API registry identity when all of the following hold:

1. the source is an authoritative API definition in the API catalog directory;
2. API object type and catalog context agree;
3. API name exactly equals the registry API name;
4. declared version exactly equals the registry API version;
5. exactly one registry candidate exists;
6. exactly one authoritative API-catalog artifact candidate exists for that name/version;
7. Product registry URL membership and Product YAML `$ref` convergence agree where that API is referenced;
8. file/structural equality may corroborate the bridge but is never its sole key.

This is a scoped export bridge and not a generic name/version merge rule.

### Aggregate result

| Finding | Result |
|---|---:|
| Authoritative API definitions under API catalog | 2,000 |
| Uniquely bridged to one API registry identity | 2,000 |
| Authoritative API definitions without registry identity | 0 |
| Authoritative API definitions with multiple registry candidates | 0 |
| Registry candidates with multiple authoritative definitions | 0 |
| API registry records without authoritative API-catalog definition | 36 |

All 2,000 authoritative API definitions therefore receive one APIC API ID/self URL as enrichment while retaining API-catalog artifact content as authoritative.

The Product registry contains 2,611 API URL occurrences spanning all 2,036 API registry identities. Of those occurrences, 2,566 refer to APIs with authoritative API-catalog definitions; 45 occurrences refer to the 36 registry-only APIs. The 36 remain registry identity/reference evidence and are not promoted to fully reconstructed configured APIs.

No authoritative API artifact-only case or bridge conflict was observed.

## 4. Product-location API documents

There are 2,357 API-shaped documents under `staging/products/_catalog`. They are preserved as source occurrences with their paths and hashes. They do not override the authoritative API definition under `staging/apis/_catalog`, do not automatically become separate `api_artifact` identities, and are not automatically discarded as duplicates.

- All 2,357 have exactly one API registry candidate under the approved scoped bridge evidence.
- 2,355 are byte-identical to an authoritative API-catalog definition.
- Two are hash-different from every authoritative API-catalog file.
- Product YAML contains 2,244 `$ref` occurrences, each reaching a distinct Product-location API path; all 2,244 resolve to a registry API identity that also has one authoritative API-catalog definition.
- Those 2,244 occurrences span 1,778 distinct registry API identities.

### The two hash-different cases

The two cases are:

- `staging/products/_catalog/ajeerelservices_1.0.1.yaml`
- `staging/products/_catalog/ajeervisaservice_1.0.1.yaml`

For each case:

- exactly one Product `$ref` reaches the Product-location document;
- exactly one API registry candidate exists;
- exactly one authoritative API-catalog definition exists with the same scoped bridge evidence;
- the only parsed document difference is the value at `x-ibm-configuration.wsdl-definition.wsdl`;
- both differing WSDL references contain one `/staging/` segment and map to existing source files;
- the two referenced WSDL source occurrences are byte-identical.

This evidence does not prove a separate API identity. The Product-location document remains provenance/corroborating evidence, the differing WSDL reference is preserved, and the authoritative API-catalog definition remains authoritative for API configuration content.

## 5. Approved `/staging/` mapping validation

The approved mapping was tested exactly as specified against every Product API `$ref`:

```text
raw absolute $ref
→ locate the exact /staging/ segment
→ preserve suffix beginning at staging/
→ resolve relative to repository root
```

| Validation | Result |
|---|---:|
| Product API `$ref` occurrences | 2,244 |
| Missing `/staging/` segment | 0 |
| Repeated `/staging/` segment | 0 |
| Mapped paths resolving to one existing file | 2,244 |
| Mapped paths resolving to zero files | 0 |
| Distinct mapped repository paths | 2,244 |

No other path normalization or heuristic rewrite is required or permitted. Phase 1 must retain both the raw absolute `$ref` and the mapped repository-relative `staging/...` path. Any future reference failing one of these exact conditions remains unresolved.

## 6. Final resolver precedence and order

1. Discover immutable source occurrences and retain source path, object pointer, source hash, and raw identity/reference values.
2. Classify only with the approved canonical object types and existing extraction contract.
3. Treat the actual configuration artifact in its relevant `staging/` directory as authoritative AS-IS configuration content.
4. Build exact, unnormalized indexes for APIC self URL and APIC object ID plus observed organization/catalog scope from registry/collection evidence.
5. Apply the approved `/staging/` mapping to Product API `$ref` values only; retain raw and mapped paths.
6. Apply the scoped Product bridge only when the unique registry candidate and all available API/Plan structural corroboration agree. Otherwise retain separate unresolved occurrences.
7. Apply the scoped API bridge only when registry-candidate and authoritative-artifact uniqueness hold and available Product reference evidence agrees. Otherwise retain separate unresolved occurrences.
8. Treat Product-location API documents as source occurrences associated through the approved Product `$ref` path and scoped API bridge; preserve content/hash differences without overriding the authoritative API-catalog artifact.
9. Resolve exact management references already validated in Task 003: Application to Consumer Organization, Credential to Application, Subscription to Application/Product, and Subscription Plan within the resolved Product.
10. Resolve Product registry API URLs to API registry self URLs; resolve Product-local API keys and Plan keys within the authoritative Product artifact.
11. Resolve Plan API keys through the same Product's API map. Never use a globally repeated Plan name without Product context.
12. Preserve registry-only and artifact-only evidence explicitly. Do not synthesize the missing counterpart and do not let registry summaries override artifact configuration.
13. After Phase 2 identity resolution, Phase 3 may build only approved relationships. Subscription remains entitlement/association evidence and never runtime usage evidence.

## 7. Task 003 gaps now closed

- Source authority is explicit: artifact configuration takes precedence; registry evidence enriches identity and references.
- All 499 authoritative Product YAML artifacts have one deterministic scoped registry identity bridge.
- All 2,000 authoritative API-catalog definitions have one deterministic scoped registry identity bridge.
- The Product API `$ref` export-root mapping is approved and validates for all 2,244 observed references.
- Product-location API document treatment is defined without inventing another object/source-copy type.
- The two hash-different Product-location cases are isolated to WSDL reference values and do not provide separate API identity evidence.
- Product YAML/API definition occurrences can now participate in the established resolver without merging by name alone or hash alone.

## 8. Gaps that remain explicit

- Twelve Product registry records have no authoritative Product YAML. They remain registry-only evidence; their configured content cannot be reconstructed from the list record.
- Thirty-six API registry records have no authoritative API-catalog definition. They remain registry-only evidence; their configured API content cannot be reconstructed from the list record.
- Thirty-four Subscription occurrences target registry-only Products. The entitlement references resolve, but authoritative Product configuration is absent.
- Forty-five Product registry API membership occurrences refer to registry-only APIs. The registry references resolve, but authoritative API configuration is absent.
- No authoritative Product or API artifact without a registry identity was observed in this export.
- The two differing WSDL reference values must remain in provenance even though their referenced WSDL source files are byte-identical.
- Catalog Property collections remain empty, so this task supplies no evidence for `api_uses_catalog_property`. Backend and catalog-property resolution were explicitly excluded.
- The known test fixture packaging issue remains unresolved by instruction.

These are missing-counterpart or out-of-scope evidence limits, not failures of the now-defined resolution order.

## 9. Resolution-contract closure and readiness

From a resolution-contract perspective, Phase 1 implementation is ready for the evidence shapes and relationships in Task 004, subject to architecture review of this handoff. No remaining identity-bridge gap blocks extraction of occurrences, preservation of raw/mapped references, or later deterministic identity enrichment.

The resolver contract is closed for the observed evidence supporting:

- Consumer Organization identity;
- Application identity and `application_belongs_to_consumer_org`;
- Credential identity and `credential_belongs_to_application`;
- Subscription identity, `subscription_belongs_to_application`, `subscription_targets_product`, and `subscription_uses_plan`;
- Product artifact/registry identity enrichment and `product_contains_api` / `product_contains_plan` evidence;
- Product-contextual Plan identity and `plan_entitles_api` evidence;
- authoritative API Artifact/registry identity enrichment;
- Product-location API source occurrence handling;
- approved Product `$ref` path mapping.

Registry-only cases must remain visibly incomplete and must not be reported as fully reconstructed configured objects. `api_uses_catalog_property` and `api_invokes_target` are not part of this closure because Task 004 excludes catalog-property and backend resolution.

## Existing test finding

The known Phase 0 test fixture packaging issue remains outside scope. `tests/test_profiler.py` references `tests/fixtures/repository_profile/staging`, but that fixture tree is absent and the broad `staging/` ignore rule would ignore it. Task 004 explicitly forbids modifying tests or fixing this issue.

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

- Source precedence plus scoped structural corroboration closes the Product and API identity bridges without a generic name/version merge rule.
- All authoritative Product and API artifacts have exactly one registry identity in this export; there are no artifact-only cases or bridge conflicts.
- Registry-only records remain valid identity/reference evidence but cannot supply authoritative configured content.
- The approved `/staging/` mapping resolves every observed Product API `$ref` exactly once.
- The two hash-different Product-location API documents differ only in WSDL reference value, and the referenced WSDL source occurrences are byte-identical; no separate API identity is proven.
- Product-to-API membership remains independent of Plan entitlement and Subscription, and Subscription remains configured entitlement evidence rather than runtime usage.

## Unresolved issues

- Architecture review is required before implementation begins.
- The 12 Product and 36 API registry-only records have no authoritative configuration counterpart in the current evidence.
- The existing Canonical API Record field contract and approved Phase 2 resolution-state contract should be made repository-accessible for implementation; Task 004 does not redefine them.
- The test fixture packaging issue remains unresolved by instruction.

## Assumptions

- The architecture-approved composite bridges apply only to this APIC export structure and catalog context; they are not general identity rules.
- Exact names and declared versions participate only as required components of the scoped bridge with uniqueness and structural corroboration.
- Product-location API documents are source occurrences associated to the bridged API identity only when the full scoped evidence agrees.
- Artifact content remains authoritative even when an enriched registry summary differs; any future content conflict must be retained for review rather than overwritten.
- Registry-only Subscription/Product/API references remain structurally meaningful while missing authoritative configuration stays explicit.

## Deviations from the prompt

None.

## Recommended next step

Integration Architect and Enterprise Architect review and approve the closed source-precedence/resolution contract, then publish the existing Canonical API Record and Phase 2 resolution-state contracts in the repository before authorizing Phase 1 implementation. Do not begin the next task until `CURRENT_TASKS.md` is updated.

## Final status

REVIEW_REQUIRED
