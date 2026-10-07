# Codex Handoff

## Task executed

Phase 2 — Task 006: Deterministic APIC Identity Resolver.

## Prompt file used

`codex/comm/prompts/phase-2-006-deterministic-apic-identity-resolver.md`

## Summary of what was done

- Implemented a deterministic Phase 2 resolver that consumes the frozen Phase 1 `indexes/extracted_records.jsonl` occurrence index.
- Added deterministic lookups for exact APIC self URL, APIC ID with compatible organization/catalog scope, source path, mapped Product `$ref` path, Product-context Plan key, and Product-local API key.
- Implemented strict Product and API identity bridges. Product bridging validates exact name/version uniqueness, API membership, Plan names, and Plan-to-API entitlements. API bridging requires unique authoritative and registry candidates and retains Product convergence evidence where available.
- Preserved authoritative artifacts, registry occurrences, Product-location copies, contributing Phase 1 record IDs, source paths/pointers, raw Product `$ref` values, and mapped paths in canonical identity provenance.
- Resolved Application → Consumer Organization, Credential → Application, Subscription → Application/Product/Plan, Product `$ref`, and Plan API-key references without emitting Phase 3 graph edges.
- Preserved registry-only Products/APIs and unassociated Product-location API copies without synthesizing configuration or identities.
- Kept authoritative artifact values ahead of registry enrichment for configured name/title/version fields.
- Added focused tests for the required resolution, rejection, preservation, redaction, determinism, and source-immutability behavior.
- Did not modify Phase 0, Phase 1, raw `staging/`, `.gitignore`, `CURRENT_TASKS.md`, or any prompt file.

## Resolver implementation structure

- `identity_resolver/resolver.py`: deterministic lookups, strict bridges, canonical identity construction, contextual Plan resolution, exact reference resolution, compact index serialization, and CLI.
- `identity_resolver/__init__.py`: public resolver API.
- `identity_resolver/__main__.py`: `python -m identity_resolver` entry point.
- `tests/test_identity_resolver.py`: focused Phase 2 coverage.

## Files created

- `identity_resolver/__init__.py`
- `identity_resolver/__main__.py`
- `identity_resolver/resolver.py`
- `tests/test_identity_resolver.py`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- `.venv/bin/pytest tests/test_identity_resolver.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m compileall -q identity_resolver`
- `git diff --check`
- Two independent full-corpus resolver runs with byte and SHA-256 comparison
- Full `staging/` SHA-256 snapshot comparison before and after resolution
- Full-corpus Credential source-value comparison against the generated index

## Test results

- Focused Phase 2 tests: **5 passed**.
- Python compilation: **passed**.
- Patch whitespace validation: **passed**.
- Full-corpus determinism: **passed**; both runs were byte-identical with SHA-256 `73c3b6481cfbfd1c7574d11cf40cbe4f2c8b99f57cd64f76f0124557e8d19185`.
- `staging/` immutability check: **passed**.
- Credential redaction check: **passed**; 540 observed credential source values were checked and zero appeared in the Phase 2 index. Credential payload key names were also absent.
- Repository-wide suite: **12 passed, 5 setup errors**. All five errors remain in frozen Phase 0 tests because `tests/fixtures/repository_profile/staging` is absent. This is the known pre-existing fixture-packaging issue and was not modified.

## Generated artifacts

- Local ignored artifact: `indexes/apic_identity_resolution.json`
- Size: 12,003,823 bytes
- Canonical identity records: 4,718
- Explicit unresolved Product-location API occurrences: 113
- The generated index is ignored by `.gitignore` and was not staged or committed.

## Full-corpus canonical identity counts

| Approved object type | Canonical identities |
|---|---:|
| `api_artifact` | 2,036 |
| `product` | 511 |
| `plan` | 596 |
| `consumer_org` | 28 |
| `application` | 256 |
| `credential` | 270 |
| `subscription` | 1,019 |
| `catalog_config` | 2 |
| `catalog_property` | 0 |
| **Total** | **4,718** |

## Source occurrence to canonical identity coverage

- Total Phase 1 occurrences: 10,221.
- Occurrences with an approved object-type candidate: 10,186.
- Typed occurrences attached to canonical identities: 10,073.
- The remaining 113 typed occurrences are unreferenced Product-location API copies. They are retained explicitly as `UNRESOLVED` occurrence evidence and are not promoted to independent canonical API identities.
- The 35 unclassified Phase 1 evidence records remain in the frozen Phase 1 index and are not converted into an unapproved Phase 2 object type.

## Exact URL and ID/scope findings

- Exact self-URL lookup keys: 4,122.
- APIC ID plus organization/catalog scope lookup keys: 4,121.
- The 56 Consumer Organization occurrences converged to 28 identities through exact APIC identity evidence; no display-name merge was used.
- ID/scope compatibility is used only when observed scope values do not conflict. Conflicting scope is not merged.

## Product bridge results

- Authoritative Product YAML occurrences: 499.
- Uniquely bridged to registry identities: 499.
- Unmapped authoritative Products: 0.
- Multiply mapped authoritative Products: 0.
- Registry-only Products: 12.
- Artifact-only authoritative Products: 0.
- Every accepted Product bridge passed API-membership, Plan-name, and Plan-to-API entitlement agreement checks.

## API bridge results

- Authoritative API-catalog definitions: 2,000.
- Uniquely bridged to registry identities: 2,000.
- Unmapped authoritative APIs: 0.
- Multiply mapped authoritative APIs: 0.
- Registry-only APIs: 36.
- Artifact-only authoritative APIs: 0.
- Attached Product-location API copies: 2,244.
- The two known hash-different Product-location copies were attached through the approved Product `$ref`/registry convergence, not through hash equality.

## Contextual Plan and local-key results

- Canonical Product-context Plan identities: 596.
- Subscription Plan references resolved inside the resolved Product: 1,019 / 1,019.
- Product-local Plan API-key references resolved through the same Product API map: 2,432 / 2,432.
- No global Plan-name or Product-local API-key identity rule was created.

## Management reference results

- Application → Consumer Organization: 256 / 256 `RESOLVED` by exact URL.
- Credential → Application: 270 / 270 `RESOLVED` by exact URL.
- Subscription → Application: 1,019 / 1,019 `RESOLVED` by exact URL.
- Subscription → Product: 1,019 / 1,019 `RESOLVED` by exact URL.
- Subscription → contextual Plan: 1,019 / 1,019 `RESOLVED`.
- Subscription evidence remains structural entitlement evidence only; no runtime use was inferred.

## Product `$ref` results

- Raw/mapped Product API `$ref` occurrences: 2,244.
- Exact mapped-path resolutions to one Product-location source occurrence: 2,244 / 2,244 `RESOLVED`.
- Both raw `$ref` and mapped `staging/...` path are retained in provenance.
- No additional path normalization was introduced.

## Registry-only, artifact-only, and unresolved evidence

- Registry-only configured-artifact gaps remain explicit for 12 Products and 36 APIs.
- There are no artifact-only authoritative Product or API identities in the current corpus.
- 113 unreferenced Product-location API occurrences remain `UNRESOLVED`; they were not treated as independent APIs and were not matched by name or hash alone.
- Current full-corpus managed references contain zero ambiguous or broken references and zero unresolved mapped Product `$ref` values.
- Focused tests verify `AMBIGUOUS`, `BROKEN_REFERENCE`, and `UNRESOLVED` preservation without guessing when those evidence shapes are supplied.

## Important findings

- The full corpus matches every validated Task 006 resolution expectation.
- Exact identity resolution reduces duplicate Consumer Organization source occurrences without using display names.
- All authoritative Product and API artifacts have registry identity enrichment, while registry-only objects remain identity records with empty authoritative-artifact provenance.
- File/hash equality is never a primary merge rule.
- No Domain, Exposure Channel, Logical API/Capability, backend/runtime, duplicate, retirement, rationalization, migration, or Kong design work was performed.

## Unresolved issues

- The frozen Phase 0 test fixture tree at `tests/fixtures/repository_profile/staging` is still absent, causing the five known repository-wide setup errors.
- The 113 unreferenced Product-location API copies require additional evidence before they can be associated; Task 006 correctly leaves them unresolved.
- Architecture review is required before any Phase 3 work begins.

## Assumptions

- `staging/apis/_catalog` is the authoritative API-catalog artifact location and `staging/products/_catalog` contains authoritative Product YAML plus Product-location API copies, consistent with the prompt and frozen Phase 1 schema evidence.
- Registry records sharing an exact APIC self URL represent the same AS-IS identity; records with conflicting URL or scope evidence are not merged through names.
- A missing approved mapped Product `$ref` path is `UNRESOLVED`; an observed mapped path with no target is `BROKEN_REFERENCE`; multiple exact mapped-path occurrences are `AMBIGUOUS`.
- Registry-only objects may have structurally confirmed APIC identity while authoritative configuration remains absent.

## Deviations from the prompt

None.

## Recommended next step

Have the Integration Architect and Enterprise Architect review the Task 006 resolver, canonical index contract, strict bridge evidence, registry-only gaps, and 113 unresolved Product-location copies. Do not start Phase 3 until that review is complete and `CURRENT_TASKS.md` is updated externally.

## Final status

REVIEW_REQUIRED
