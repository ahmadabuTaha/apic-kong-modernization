# Codex Handoff

## Task executed

Phase 1 — Task 005: Extractor Implementation.

## Prompt file used

`codex/comm/prompts/phase-1-005-extractor-implementation.md`

## Summary of what was done

- Implemented a deterministic, occurrence-preserving Phase 1 extractor in a new `source_extractor` package without changing the frozen Phase 0 profiler.
- Added extraction for API artifacts, Products, embedded Plans, Consumer Organizations, Applications, Credentials, Subscriptions, Catalog configurations, and Catalog properties.
- Preserved source path, source hash, schema family, object pointer, observed identity values, management references, raw Product API `$ref` values, and approved mapped repository-relative paths.
- Kept occurrences separate; no identity merging, relationship resolution, graph construction, semantic classification, backend inference, or retirement/duplicate decisions were performed.
- Applied a strict Credential allowlist. Credential values and hashed-secret values are never emitted.
- Added explicit records for malformed and unsupported evidence using only the approved extraction statuses and reason codes.
- Added focused synthetic tests covering determinism, occurrence preservation, exact `$ref` mapping, unmappable reference handling, embedded Plan extraction, malformed/unsupported evidence, empty collections, WSDL evidence, and credential redaction.
- Ran the extractor twice against the full local `staging/` corpus and confirmed byte-identical output.

## Files created

- `source_extractor/__init__.py`
- `source_extractor/__main__.py`
- `source_extractor/extractor.py`
- `tests/test_extractor.py`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- `.venv/bin/pytest tests/test_extractor.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m compileall -q source_extractor`
- `git diff --check`
- Full-corpus extractor run twice with SHA-256 comparison

## Test results

- Extractor tests: **5 passed**.
- Python compilation: **passed**.
- Patch whitespace validation: **passed**.
- Determinism check: **passed**; both full-corpus runs produced SHA-256 `d71e56dc76571bd18ff4f666cb5f1ede00d9eb63f8c1287c2dd0f4508fcfde4a`.
- Repository-wide suite: **7 passed, 5 setup errors**. All five errors are in the frozen Phase 0 tests because `tests/fixtures/repository_profile/staging` is absent. This pre-existing fixture-packaging issue is outside Task 005 and was not modified.

## Generated artifacts

- Local ignored artifact: `indexes/extracted_records.jsonl`
- Size: 12,265,971 bytes
- Records: 10,221
- The generated index was not staged or committed.

## Extraction results

### Records by canonical object type

| Object type | Records |
|---|---:|
| `api_artifact` | 6,393 |
| `product` | 1,010 |
| `plan` | 1,180 |
| `consumer_org` | 56 |
| `application` | 256 |
| `credential` | 270 |
| `subscription` | 1,019 |
| `catalog_config` | 2 |
| `catalog_property` | 0 |
| Unclassified source evidence | 35 |

### Records by extraction status

| Status | Records |
|---|---:|
| `EXTRACTED` | 10,190 |
| `EXTRACTION_PARTIAL` | 0 |
| `EXTRACTION_FAILED` | 31 |

All 31 failed records use `unsupported_object_shape`: 28 member-list items and three `.DS_Store` files. Four WSDL files are retained as extracted, unclassified source evidence. Empty Catalog Property collections correctly produce zero property records.

### Key corpus checks

- 2,000 authoritative API-catalog definition occurrences were extracted.
- 2,357 Product-location API document occurrences were extracted separately.
- 2,036 API registry occurrences were extracted separately.
- 499 Product YAML occurrences and 511 Product registry occurrences were extracted separately.
- 584 embedded Product-YAML Plan occurrences and 596 Product-registry Plan occurrences were extracted separately.
- All 2,244 Product API `$ref` occurrences retain the raw reference and have the exact approved mapped `staging/...` path.
- 270 Credential occurrences use the strict approved field set.
- 540 observed sensitive source values were checked against the generated index; zero were present.

## Important findings

- The extractor preserves every source occurrence instead of collapsing matching API, Product, or Plan evidence.
- The exact approved `/staging/` mapping succeeds for every Product API `$ref` in the current corpus; the implementation retains null mapped paths for references that do not satisfy that rule.
- The full corpus contains no extracted Catalog Property items because the observed collections are empty.
- Unsupported member-list items are retained as explicit failed evidence rather than silently discarded.
- No files under `staging/` were modified.

## Unresolved issues

- The repository-wide test suite cannot fully pass until the existing Phase 0 fixture tree at `tests/fixtures/repository_profile/staging` is restored or packaged. Task 005 forbids changing the frozen Phase 0 implementation and prior tests, so this remains unresolved.
- Architecture review is required before starting the next phase/task.

## Assumptions

- Each source document or collection item is an independent occurrence even when its identity fields match another occurrence.
- WSDL files are retained as source evidence with a null canonical object type because WSDL is not an approved canonical object type.
- Empty list/collection documents provide container evidence but do not create synthetic object records.
- `.DS_Store` and unsupported member-list shapes are preserved as failed extraction evidence rather than ignored.

## Deviations from the prompt

None.

## Recommended next step

Have the Integration Architect review the Task 005 implementation, extraction counts, failure records, Credential allowlist, and deterministic output. Do not begin the next task until that review is complete and `CURRENT_TASKS.md` is updated externally.

## Final status

REVIEW_REQUIRED
