# Codex Handoff

## Task executed

Phase 3 — Task 008: Deterministic Relationship Reconstruction.

## Prompt file used

`codex/comm/prompts/phase-3-008-deterministic-relationship-reconstruction.md`

## Summary of what was done

- Implemented a deterministic Phase 3 relationship builder over the frozen Phase 1 occurrence index and accepted Phase 2 canonical identity index.
- Emitted only approved structural relationship types with resolved canonical endpoints and `STRUCTURALLY_CONFIRMED` evidence.
- Deduplicated edges by canonical source identity, approved relationship type, and canonical target identity while retaining all contributing authoritative and registry provenance.
- Reconstructed Product/API, Product/Plan, contextual Plan/API, Application/Consumer Organization, Credential/Application, and Subscription/Application/Product/Plan relationships.
- Preserved raw reference values, mapped Product `$ref` paths where applicable, Phase 2 resolution outcomes, source paths/pointers, and contributing Phase 1 IDs.
- Emitted zero `api_uses_catalog_property` and `api_invokes_target` edges because the accepted evidence does not support them.
- Verified that all 113 Task 007 unresolved Product-location API occurrences remain excluded from graph nodes/edges and provenance.
- Added deterministic architecture-review evidence and focused Phase 3 tests.
- Did not modify Phase 0, Phase 1, Phase 2, Task 007 evidence, raw `staging/`, `.gitignore`, `CURRENT_TASKS.md`, or prompt files.

## Relationship builder implementation structure

- `relationship_builder/builder.py`: canonical endpoint lookup, explicit-reference reconstruction, edge validation, deterministic edge IDs, provenance aggregation, deduplication, coverage metrics, and JSONL serialization.
- `relationship_builder/__init__.py`: public builder API and approved relationship constants.
- `relationship_builder/__main__.py`: `python -m relationship_builder` entry point.
- `tests/evidence/task-008/generate_relationship_evidence.py`: deterministic review-evidence generator.
- `tests/test_relationship_builder.py`: focused synthetic and full-corpus validation.

## Exact relationship index path

`indexes/relationship_index.jsonl`

The index is a local ignored generated artifact. It contains 9,589 JSONL records, is 14,850,576 bytes, and has SHA-256 `d9fdc2e5cd61510335af572e03c21b27128d39cb9007104be774e24e3d3a8a0a`.

## Total canonical edges

9,589.

## Counts by approved relationship type

| Relationship type | Canonical edges |
|---|---:|
| `product_contains_api` | 2,611 |
| `product_contains_plan` | 596 |
| `plan_entitles_api` | 2,799 |
| `application_belongs_to_consumer_org` | 256 |
| `credential_belongs_to_application` | 270 |
| `subscription_belongs_to_application` | 1,019 |
| `subscription_targets_product` | 1,019 |
| `subscription_uses_plan` | 1,019 |
| `api_uses_catalog_property` | 0 |
| `api_invokes_target` | 0 |
| **Total** | **9,589** |

## Evidence-source findings

- Edges backed by registry identity/reference evidence: 9,589.
- Edges also backed by authoritative artifact/configuration evidence: 5,260.
- Dual authoritative-plus-registry provenance: 5,260 edges.
- Registry-only provenance: 4,329 edges.
- Evidence-source category counts overlap by design when one canonical edge has both kinds of provenance.

Breakdown of the dual-provenance population:

- `product_contains_api`: 2,244 dual-provenance; 367 registry-only.
- `product_contains_plan`: 584 dual-provenance; 12 registry-only.
- `plan_entitles_api`: 2,432 dual-provenance; 367 registry-only.
- Application, Credential, and Subscription edges are registry-reference-backed structural evidence.

Registry-only membership is represented only from direct registry references between resolved canonical identities. It does not fabricate missing authoritative configuration.

## Canonical-edge deduplication findings

- Canonical edge identity is based only on canonical source ID, approved relationship type, and canonical target ID.
- 5,260 edges have multiple contributing source occurrences and were emitted once with combined provenance.
- The authoritative Product/API population of 2,244 and registry Product/API membership population of 2,611 collapse to 2,611 distinct canonical edges.
- The authoritative Plan/API population of 2,432 and registry Plan/API population of 2,799 collapse to 2,799 distinct canonical edges.
- The 584 authoritative-backed Plans plus 12 registry-only Plans produce 596 contextual Product/Plan edges.
- All 9,589 relationship IDs are unique and deterministic.

## Product and Plan structural coverage

### Product → API

- Authoritative Product `$ref` references represented: 2,244 / 2,244.
- Direct registry Product API memberships represented: 2,611 / 2,611.
- Canonical `product_contains_api` edges after deduplication: 2,611.

### Product → Plan

- Resolved contextual Plan identities linked to their Product: 596 / 596.
- Canonical `product_contains_plan` edges: 596.

### Plan → API

- Authoritative Product-local Plan API-key references represented: 2,432 / 2,432.
- Direct registry Plan API references represented: 2,799 / 2,799.
- Canonical `plan_entitles_api` edges after deduplication: 2,799.
- No Plan name or API key was resolved outside its Product context.

## Application, Credential, and Subscription coverage

- Application → Consumer Organization: 256 / 256 represented.
- Credential → Application: 270 / 270 represented.
- Subscription → Application: 1,019 / 1,019 represented.
- Subscription → Product: 1,019 / 1,019 represented.
- Subscription → contextual Plan: 1,019 / 1,019 represented.
- Subscription relationships express structural entitlement/reference only; no runtime use was inferred.

## Zero-count approved relationship types

- `api_uses_catalog_property`: 0. The accepted canonical identity index contains zero `catalog_property` identities, so there is no resolved structural target.
- `api_invokes_target`: 0. Backend resolution has not been performed and the accepted model contains no explicit resolved target identities for this relationship.

These zero counts are expected evidence absence, not parser failures. No policy text, URL, name, or guessed target was used to infer an edge.

## Excluded unresolved evidence

- `UNRESOLVED`: 113 Task 007 Product-location source occurrences excluded.
- `AMBIGUOUS`: 0 in the current accepted full-corpus Phase 2 reference population.
- `BROKEN_REFERENCE`: 0 in the current accepted full-corpus Phase 2 reference population.
- Focused tests verify that unresolved, ambiguous, and broken references emit no edge.
- Focused tests also verify that name-only and hash-only evidence emit no edge.

None of the 113 Task 007 extracted record IDs appears as relationship provenance, and none was promoted to a standalone graph node or edge endpoint.

## Evidence artifacts created

- `tests/evidence/task-008/relationship_counts.json`
  - total/counts by approved relationship type and evidence source category;
  - multi-provenance edge count and excluded evidence outcomes;
  - SHA-256 `05eca23fd721d28c5f3b685243bb149d81b50deb97c0b9873684f9c1a0d34840`.
- `tests/evidence/task-008/relationship_samples.jsonl`
  - 11 deterministic samples covering every non-zero relationship type plus dual-provenance and registry-only Product/Plan patterns;
  - SHA-256 `eb6f5f729992f377aceed50060526cae44b018d9ee0880ab907a64124e8f8a92`.
- `tests/evidence/task-008/relationship_coverage.json`
  - accepted-population numerator/denominator coverage and Task 007 exclusion verification;
  - SHA-256 `a8fdc7e42a74ccc6df4a5720fdfdeae103c5ed89f22f972b1fb770a8206845ee`.
- `tests/evidence/task-008/commands_and_results.txt`
  - commands executed and meaningful build, determinism, test, immutability, and redaction results.
- `tests/evidence/task-008/generate_relationship_evidence.py`
  - deterministic evidence-generation helper.

## Files created

- `relationship_builder/__init__.py`
- `relationship_builder/__main__.py`
- `relationship_builder/builder.py`
- `tests/test_relationship_builder.py`
- `tests/evidence/task-008/generate_relationship_evidence.py`
- `tests/evidence/task-008/relationship_counts.json`
- `tests/evidence/task-008/relationship_samples.jsonl`
- `tests/evidence/task-008/relationship_coverage.json`
- `tests/evidence/task-008/commands_and_results.txt`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests and commands executed

- `.venv/bin/python -m relationship_builder --phase2 indexes/apic_identity_resolution.json --phase1 indexes/extracted_records.jsonl --output-root .`
- `.venv/bin/python tests/evidence/task-008/generate_relationship_evidence.py --phase2 indexes/apic_identity_resolution.json --phase1 indexes/extracted_records.jsonl --output-directory tests/evidence/task-008`
- Two full relationship/evidence generation runs with SHA-256 comparison
- `.venv/bin/pytest tests/test_relationship_builder.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m compileall -q relationship_builder`
- `.venv/bin/python -m py_compile tests/evidence/task-008/generate_relationship_evidence.py tests/test_relationship_builder.py`
- `git diff --check`
- Frozen implementation diff check
- Full `staging/` SHA-256 snapshot comparison before and after reconstruction
- Full-corpus credential source-value comparison against relationship/evidence outputs

## Test results

- Focused Phase 3 tests: **3 passed**.
- Repeated full-corpus relationship index: **byte-identical** with SHA-256 `d9fdc2e5cd61510335af572e03c21b27128d39cb9007104be774e24e3d3a8a0a` on both runs.
- Repeated Task 008 count/sample/coverage artifacts: **byte-identical** on both runs.
- Relationship ID uniqueness: **9,589 / 9,589 unique**.
- Accepted-reference coverage: **passed** for all required Product, Plan, Application, Credential, and Subscription populations.
- Task 007 non-promotion: **passed**, 0 / 113 promoted.
- Source immutability: **passed**, `staging/` unchanged.
- Credential redaction: **passed**; 540 observed source credential values checked, zero emitted.
- Python compilation and whitespace checks: **passed**.
- Repository-wide suite: **18 passed, 5 setup errors**. The five errors remain the known frozen Phase 0 fixture-packaging issue because `tests/fixtures/repository_profile/staging` is absent. No Task 008 test failed.

## Generated artifacts

- Local ignored index: `indexes/relationship_index.jsonl`.
- Committed review artifacts: `tests/evidence/task-008/relationship_counts.json`, `relationship_samples.jsonl`, `relationship_coverage.json`, and `commands_and_results.txt`.
- No generated file under `indexes/` or `outputs/` is staged for version control.

## Important findings

- Direct registry Product/API and Plan/API evidence extends beyond authoritative Product YAML references by 367 canonical edges in each relationship population; those edges remain visibly registry-only.
- Twelve Product/Plan edges are registry-only, matching the 12 registry-only Products retained by Phase 2.
- All authoritative structural relationships agree with and deduplicate against registry relationships at the canonical endpoint level.
- The accepted Phase 2 resolution is sufficient for every required Task 008 structural edge; no earlier-phase defect was found.
- The graph contains structural configuration and entitlement evidence only. It makes no semantic, runtime, backend, retirement, duplicate, rationalization, migration, or Kong assertions.

## Unresolved issues

- The 113 Product-location source occurrences remain correctly unresolved and excluded pending future evidence or an explicit architecture-contract change.
- Catalog Property and backend/target relationships remain absent because their prerequisite accepted evidence does not exist in the current phase.
- The known frozen Phase 0 fixture-packaging issue continues to cause five repository-wide setup errors.

## Assumptions

- Accepted Phase 2 canonical IDs and resolved-reference outcomes are authoritative inputs for Phase 3 endpoint selection.
- Direct registry `api_urls` and registry Plan API URLs are admissible registry relationship evidence when both canonical endpoints resolve.
- Evidence-source categories describe provenance and may overlap on one canonical edge.
- A canonical edge with multiple source occurrences is one enterprise relationship with multiple provenance items, not multiple relationships.

## Deviations from the prompt

None.

## Recommended next step

Accept Phase 3 Task 008 as PASS and have the Integration Architect and Enterprise Architect review the committed counts, coverage, and representative edge provenance. Do not begin semantic enrichment, backend resolution, duplicate analysis, rationalization, migration, or Kong design until `CURRENT_TASKS.md` is updated externally.

## Final status

PASS
