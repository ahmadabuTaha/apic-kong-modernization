# Phase 6 / Task 019-B — All-Modules ICD/ISD Inventory Normalization

**Status:** AUTHORIZED_FOR_CODEX — ALL MODULES, NOT COMMON-ONLY. EA directs expansion after Task 019-A technical PASS.
**Stop gate:** `EA_REVIEW_TASK019B`

## Objective
Extend the accepted Common pilot to **every literal Module** in the exact EA-supplied local file `outputs/services_icd_isd_inventory.csv`, using the frozen identity hierarchy:
`Module → Service → ICD references (0..N) / ISD references (0..N)`.
`Module Codex(Sub Module)` must NOT influence identity, classification, grouping, counts or graph hierarchy (retain only in original row-audit if needed).

Do not substitute `neo4j/csv/Qiwa_Modules_Services.csv`; the two inventories serve different purposes.

## Preconditions — hard stop
1. Read `AGENTS.md`, latest `codex/comm/CURRENT_TASKS.md`, and latest `codex/comm/HANSOFF.md`.
2. Confirm Task 019-A technical PASS in latest HANSOFF and Task 019-B ACTIVE in CURRENT_TASKS. The EA has explicitly authorized all-module expansion in this turn. Do not treat the earlier Common-only pilot as a scope restriction for 019-B.
3. Validate local exact source file presence, expected five CSV headers, source SHA-256 and accepted Common pilot baseline. Preserve input byte-for-byte; file is gitignored.
4. Use Task 019-A's `business_capability_kg/` package and canonical namespaces; if missing, stop and explain, not recreate or bypass.

## Work — deterministic only
- Apply the **existing accepted normalizer** over **ALL rows and ALL literal Modules** in the input, without sampling, Common-only filters or semantic interpretation. Common is a regression checkpoint only, **not** the output scope. Do not hardcode module count from the separate QIWA data source.
- Preserve each input row including CSV row number, raw Module, raw Service, raw ICD/ISD cells, source SHA and separate reference occurrence order. Distinct Modules remain distinct even when service names are identical.
- Parse ICD and ISD columns independently: split semicolon `;`, strip surrounding whitespace, preserve empty-cell/invalid-format cases in explicit diagnostics. 0..N documents per Service is valid. ICD-only schedulers and ISD-only collections must remain represented without inventing API/Job identities.
- Deduplicate stable document *identities* when grounded by source reference/page ID, but preserve **all** occurrences and edges (including repeated document use by multiple services/modules).
- Validate safe URI/page-ID parsing only; **do not download documents** or test Confluence reachability.
- Keep protected full URLs only in controlled audit records, use sanitized identifiers in reusable indexes and summaries. No credentials or secrets in outputs.
- Preserve module-scope service IDs, stable deterministic keys and provenance. Detect and explicitly report collisions; do not silently merge unrelated entities.
- Process reproducibly and efficiently from the one local input (single CSV parse / index reuse as appropriate), without touching staging or rebuilding APIC phases.
- Reconcile exact Common membership, its accepted 116 source rows/116 module-scoped services/225 reference occurrences, and compare against 015-A / 019-A baselines; do not alter frozen outputs. If mismatched, stop as `COMMON_BASELINE_REGRESSION`.

## Output ownership
- Executable code/changes only under `business_capability_kg/` (plus focused tests under `tests/business_capability_kg/`), according to repository conventions.
- Derived indexes: `indexes/phase6/task019/019b/` (e.g. `modules.csv`, `services.csv`, `documents.csv`, `service_document_edges.csv`, `source_rows.csv`, `exceptions.csv`).
- Reports: `outputs/phase6/task019/019b/manifest.json` and `validation_summary.md` only (plus strictly necessary structured outputs).
- Prior `indexes/capability_kg/015a/`, `outputs/capability_kg/015a/`, and Task 019-A outputs remain immutable.
- Keep an index easily filtered by Module so later 019-C acquisition can process one Module at a time without reopening or scanning all rows.

## Required validation
1. **Full coverage:** processed source rows equal total CSV data rows, with no skipped module. Unique module names represented exactly (literal labels preserved). Totals are measured, not assumed.
2. **Reference closure:** count every nonempty ICD/ISD token across entire file; `accepted_occurrences + rejected_occurrences = source_occurrences`. Preserve edge provenance and distinguish document identity count from occurrence count.
3. **Cardinality:** fixtures for 0, 1 and N ICD/ISD, semicolon-separated tokens, duplicate references, cross-module same-name services, invalid URI, blank columns, zero-document services, and normalization collisions.
4. **Common regression:** 116 source rows, 116 services, 225 accepted occurrences; compare stable pilot IDs and normalized mappings to original 015-A, not merely totals.
5. **Determinism/cache readiness:** two unchanged runs yield byte-identical indexes; manifest records hashes and parser/schema version. Supports targeted module filtering for future work.
6. **Sanitization:** no protected full URLs/secrets in public ledgers or report; private audit may contain original refs in ignored output.
7. Focused tests pass. Report inherited environmental test failures separately.

## Handoff / stop
Write concise Codex handoff: input hash, total modules/rows/services/ICD refs/ISD refs, unique doc count, coverage reconciliation, exceptions by explicit cause, per-module coverage table/CSV path, Common regression verdict, output paths, test results, commit SHA, and `EA_REVIEW_TASK019B`.

**STOP at 019-B.** Do not implement document acquisition/cache, ICD capability semantics, ISD endpoint extraction, canonical API matching, knowledge graph, productization, CI/CD, or Kong.
