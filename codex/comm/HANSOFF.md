# Codex Handoff

## Task executed

Phase 2 — Task 007: Targeted Investigation of 113 Unresolved Product-Location API Occurrences.

## Prompt file used

`codex/comm/prompts/phase-2-007-targeted-investigation-unresolved-product-location-apis.md`

## Summary of what was done

- Reproduced the Task 006 unresolved population from the Phase 2 identity index and frozen Phase 1 occurrence index.
- Enumerated every unresolved Product-location API occurrence with source provenance, directly observed identity fields, exact Product `$ref` evidence, diagnostic API candidates, registry Product membership, canonical identity candidates, failed attachment checks, and the current resolution outcome.
- Proved that the 113 records are exactly the Product-location occurrences not attached by Task 006: 2,357 total minus 2,244 attached equals 113, with 113 unique enumerated IDs, no omissions, and zero attached/unresolved overlap.
- Compared admissible identity/reference evidence separately from name/version/hash diagnostics.
- Determined that all 113 are correctly `UNRESOLVED` under the approved Phase 2 contract and that no Task 006 resolver defect is reproducible.
- Left `identity_resolver/`, Phase 0, Phase 1, `staging/`, `CURRENT_TASKS.md`, and all prompt files unchanged.
- Added deterministic generation and focused validation for the committed Task 007 evidence.

## Exact reason the population is 113

The Phase 1 index contains 2,357 API-shaped documents under `staging/products/_catalog`. Task 006 attached 2,244 exact source occurrences through a resolved Product context where the Product YAML `$ref` mapped to that exact source path and registry API evidence agreed.

The remaining set is exactly:

```text
2,357 Product-location API occurrences
- 2,244 occurrences attached through approved convergence
=   113 unresolved occurrences
```

The arithmetic fully accounts for the population, and the independent record-set checks prove more than the arithmetic:

- 113 JSONL evidence rows;
- 113 unique Phase 1 `extracted_record_id` values;
- enumerated IDs exactly equal the Task 006 unresolved IDs;
- zero overlap with the 2,244 attached occurrence IDs;
- attached and unresolved IDs together cover all 2,357 Product-location API occurrence IDs.

## Aggregate evidence across the 113

All 113 share the same concrete attachment-evidence pattern:

- Product `$ref` mapping to the exact source path: 0 / 113;
- directly observed APIC self URL: 0 / 113;
- directly observed APIC ID with compatible scope: 0 / 113;
- source-path Product context: 0 / 113 because `staging/products/_catalog` is a flat location;
- unique authoritative API-catalog diagnostic candidate by exact name/version: 113 / 113;
- unique registry API diagnostic candidate by exact name/version: 113 / 113;
- existing authoritative-to-registry API bridge for the candidate identity: 113 / 113;
- hash-equal authoritative API-catalog diagnostic candidate: 113 / 113;
- approved Product `$ref` plus registry attachment convergence: 0 / 113;
- multiple authoritative or registry API candidates: 0 / 113;
- registry Product membership observed through the diagnostic registry API candidate but no YAML `$ref`: 113 / 113;
- membership in at least one registry-only Product: 113 / 113;
- no admissible occurrence-attachment key: 113 / 113;
- no diagnostic candidate evidence at all: 0 / 113;
- correctly unresolved: 113 / 113;
- demonstrated resolver defects: 0 / 113.

Registry Product membership counts are not unique Product contexts: 63 occurrences have one candidate membership, 37 have two, 10 have three, one has four, and two have five. Fifty occurrences therefore have multiple registry Product memberships. Registry membership identifies that an API identity is listed by a Product, but it does not reference a particular file occurrence in the flat Product-location directory.

The 113 occurrences point diagnostically to 110 candidate canonical API identities. Three identities each have two unresolved Product-location copies. Thirty-eight unresolved occurrences have another same-name/version Product-location sibling that is referenced by a Product YAML. The exact-path rule intentionally does not transfer the sibling's `$ref` to the unreferenced file by name or hash.

These categories overlap as recorded in the evidence. In particular, all 113 have both exact name/version and hash-equal diagnostics, so neither diagnostic count is presented as a mutually exclusive cause.

## Required investigation answers

1. All 113 are truly unreferenced by Product YAML `$ref`: **yes**. Exact mapped-path reference count is zero for every record.
2. Registry/Product membership without YAML `$ref`: **yes, all 113** have one or more registry Product memberships through their diagnostic registry API candidate.
3. Exact APIC self URL evidence on the Product-location occurrence: **none**.
4. APIC ID plus compatible scope evidence on the Product-location occurrence: **none**.
5. Unique authoritative API-catalog candidate through the existing API bridge: **113**, but this identifies a candidate API identity and does not attach the file occurrence without Product `$ref` convergence.
6. Exact name/version diagnostic matches with no admissible attachment key: **113**.
7. Hash-equal authoritative artifacts with no admissible attachment key: **113**.
8. Multiple authoritative or registry API candidates: **0**. Multiple registry Product memberships occur for 50 records, which further prevents deriving a unique Product context from membership.
9. No diagnostic candidate evidence beyond the API-shaped document: **0**. No admissible attachment evidence: **113**.
10. Task 006 implementation defects demonstrated: **0**.
11. Smallest failing example for a resolver defect: not applicable because no defect was reproduced.
12. Why the population remains unresolved: attaching any record would require using name/version, hash equality, a sibling file's `$ref`, or registry membership as a substitute for the required exact occurrence-level Product `$ref` convergence. Each substitute is prohibited by the approved contract.

## Representative evidence

- `staging/products/_catalog/addestablishmentlocationusingml_1.0.0.yaml` — `extracted-record:sha256:9058e211cc493e372880c8204058fdaeebb9f223a62616d62af7a25cecab94b5`. It has no Product `$ref`, self URL, ID, or source-path Product context. It has one bridged candidate API identity and two registry-only Product membership candidates. A second unresolved copy with an `_1` suffix exists, so hash/name evidence cannot select a Product context.
- `staging/products/_catalog/addupdateservices_1.0.0.yaml` — `extracted-record:sha256:d98ea34dbfab60a9f08af9fd5e89129ce3e1338b439c9ee1699e0dca61b6cfbe`. It has one registry-only and one authoritative-backed registry Product membership candidate. A same-name/version/hash sibling is referenced, but the selected file is not; copying the sibling's relationship would violate exact mapped-path resolution.
- `staging/products/_catalog/addlaborerslocationLO_1.0.0.yaml` — `extracted-record:sha256:f0cf8bb4603a114f3818d3fec7aa7d1a8f2eea58bb9b354ea84188ae3276be1d`. It has one unique diagnostic API identity and one registry-only Product membership, but no occurrence-level `$ref` or direct APIC identity evidence.

Every other occurrence and its complete candidate evidence is in the committed JSONL artifact.

## Evidence artifacts created

- `tests/evidence/task-007/unresolved_product_location_apis.jsonl`
  - 113 records, one per unresolved occurrence;
  - 581,447 bytes;
  - SHA-256 `3e95b6e0073646e494a268e44efa751f9c273df68784813fd92e9be22d56ba0d`.
- `tests/evidence/task-007/investigation_summary.json`
  - aggregate counts, set proof, evidence-pattern counts, and overlap disclosure;
  - 2,157 bytes;
  - SHA-256 `9644e9c4f1c15c000f3cc5e1a430b83a4f6597ce6cb6b15f52a207005241e2a4`.
- `tests/evidence/task-007/commands_and_results.txt`
  - commands executed and meaningful deterministic/test results;
  - 3,679 bytes;
  - SHA-256 `4c147e4f9e17b074b07d038c0afb450c9c7ff9c6f08d15242f0bd673f4653d37`.
- `tests/evidence/task-007/investigate_unresolved.py`
  - deterministic evidence generator.

## Files created

- `tests/evidence/task-007/investigate_unresolved.py`
- `tests/evidence/task-007/unresolved_product_location_apis.jsonl`
- `tests/evidence/task-007/investigation_summary.json`
- `tests/evidence/task-007/commands_and_results.txt`
- `tests/test_task_007_evidence.py`

## Files modified

- `codex/comm/HANSOFF.md`

No resolver, Phase 0, Phase 1, source-evidence, task-control, or prompt file was modified.

## Tests and commands executed

- `.venv/bin/python tests/evidence/task-007/investigate_unresolved.py --phase2 indexes/apic_identity_resolution.json --phase1 indexes/extracted_records.jsonl --output-directory tests/evidence/task-007`
- `wc -l tests/evidence/task-007/unresolved_product_location_apis.jsonl`
- Two full evidence-generation runs with SHA-256 comparison
- `.venv/bin/pytest tests/test_task_007_evidence.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m py_compile tests/evidence/task-007/investigate_unresolved.py tests/test_task_007_evidence.py`
- `git diff --check`
- `git diff -- identity_resolver`

## Test results

- Focused Task 007 tests: **3 passed**.
- Repeated generation: **passed**; both committed evidence artifacts were byte-identical across runs.
- Exact unresolved-ID set reproduction: **passed**.
- No omission/no overlap/full Product-location coverage: **passed**.
- Name/version/hash-only non-promotion: **passed**.
- `staging/` hash snapshot before/after investigation: **unchanged**.
- Credential redaction: **passed**; all observed credential values remain absent from the Task 007 evidence and Phase 2 identity index.
- Python compilation: **passed**.
- Resolver-change check: **passed**; `identity_resolver/` has no changes.
- Repository-wide suite: **15 passed, 5 setup errors**. The five errors are the known frozen Phase 0 fixture-packaging issue because `tests/fixtures/repository_profile/staging` is absent. No Task 007 test failed.

## Generated artifacts

The three required committed review artifacts are under `tests/evidence/task-007/` and listed above. The investigation consumed the existing ignored Phase 1 and Phase 2 indexes; it did not create or stage a new artifact under `indexes/` or `outputs/`.

## Important findings

- The unresolved count is complete and deterministic; it is not a summary-calculation artifact.
- The candidate API identities are not themselves ambiguous: all 113 have a unique existing API bridge. What is missing is admissible evidence attaching each specific source occurrence.
- All 113 participate in registry Product membership, but every one also participates in at least one registry-only Product. The registry records do not identify which flat source-file copy belongs to which Product.
- Hash equality is universal across this population but remains corroboration only. Using it would directly violate the no-hash-only rule.
- Thirty-eight records demonstrate why `$ref` evidence cannot be inherited from a sibling path: the sibling may be referenced while the selected occurrence is not.
- Task 006 correctly preserved rather than guessed these occurrence associations.

## Unresolved issues

- The 113 source occurrences remain `UNRESOLVED` because the corpus lacks an approved occurrence-level attachment key. Architecture may decide whether future evidence or an explicitly revised identity contract should address them; Task 007 does not authorize that change.
- The known frozen Phase 0 fixture-packaging issue continues to cause five repository-wide setup errors.

## Assumptions

- The existing Task 006 Phase 2 index and frozen Phase 1 extracted index are the deterministic starting evidence required by the prompt.
- Registry Product `api_urls` are direct membership evidence for API identities, but they are not direct references to Product-location source paths.
- A same-name/version or hash-equal sibling is a separate source occurrence unless the approved exact mapped Product `$ref` evidence attaches it.
- Evidence categories intentionally overlap and are reported independently.

## Deviations from the prompt

None.

## Recommended next step

Accept Phase 2 Task 007 as PASS. The Integration Architect and Enterprise Architect should review the committed per-occurrence evidence and decide whether the 113 correctly unresolved copies require any future contract change. Do not begin Phase 3 until `CURRENT_TASKS.md` is updated externally.

## Final status

PASS
