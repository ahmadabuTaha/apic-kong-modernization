# Capability-KG / Task 015-A — Module → Service → ICD/ISD Reference Normalization

**Phase:** Business Capability Knowledge Graph — Foundation  
**Status:** AUTHORIZED_FOR_CODEX (subject to input preflight)  
**Scope:** 015-A only; stop at EA_REVIEW_CAPKG_015A.

## Objective
Build a deterministic, lossless, query-friendly index from the exact input **services_icd_isd_inventory.csv** using this authoritative hierarchy only:

**Module → Service → ICD references (0..N) / ISD references (0..N)**

The input field `Module Codex(Sub Module)` is **NOT** an identity, relationship, classification, grouping key, or required output field. Ignore it in the operational model. Preserve original input rows for audit only.

This is reference normalization, **not** ICD/ISD retrieval, semantic extraction, capability classification, API matching, graph build, productization, CI/CD, or Kong design.

## Source/preflight
- Required exact source filename: `services_icd_isd_inventory.csv`, provided by EA as a ChatGPT attachment. Locate an explicitly supplied copy in the Codex workspace/repository or request the user/team to place it into an approved input location. **The attached file is NOT automatically available to GitHub Codex; do not assume that it is.**
- Do NOT silently substitute `neo4j/csv/Qiwa_Modules_Services.csv` or the 018F QIWA indexes: different source and purpose.
- If exact source is unavailable, report `BLOCKED_INPUT_NOT_AVAILABLE` with expected filename/location and stop before claiming populated inventory coverage. Parser and fixture-based tests may be prepared, but no real-data counts claimed.
- Source columns (literal): `Module`, `Module Codex(Sub Module)`, `Service`, `ICD`, `ISD`. Read UTF-8 with optional BOM using a CSV parser; keep original row number (data row numbering starting 2 to match CSV header).
- Begin with **Common** module as pilot, then stop for EA review; do not process all other modules in the production output. Preflight may inspect headers/source availability without scanning all other module contents for interpretation.

## Deterministic normalization
1. Preserve source identifiers: `source_file_sha256`, `source_row_number`, `raw_module`, `raw_service`, `raw_icd_cell`, `raw_isd_cell`. Preserve row identity for repeated names and repeated exact rows.
2. Create module keys from deterministic, collision-safe normalization of **Module only**, plus original display name; collision triggers explicit exception, never silent merge.
3. Create a service identity scoped to the module and normalized service label, but preserve **each source row and all its references**. Distinct rows with same service label can resolve to one module-scoped service only if no source identity conflict; retain source rows separately. Do not infer cross-module service equivalence.
4. For ICD and ISD separately: split on semicolon `;`, trim whitespace, discard empty tokens from the reference list while preserving original cell. Maintain occurrence order and originating row. Multiple ICDs and/or ISDs per service are expected; `0..N` is valid, including ICD-only schedulers, ISD-only rows, and neither (flag no-document references, don't drop the service).
5. A document is identified by a safely normalized exact source reference / stable Confluence page ID when parseable; keep full reference only in controlled internal index if policy permits and avoid leaking protected URLs to public reports. A single document can be referenced by multiple rows/services/modules; deduplicate the document identity but never erase usage edges.
6. Validate URL/reference syntax without fetching. Do not conclude that references are reachable or documents exist. Flag `invalid_reference_format`, `blank_reference`, `duplicate_reference_occurrence` and `identity_collision` distinctly and with row-level provenance.
7. No capability names, Canonical APIs, scheduler jobs, graph edges, business ownership or HTTP operations are to be inferred from names or reference URLs.

## Minimal deliverables — additive only
Choose repo-consistent output/index paths under `indexes/` and `outputs/` in a dedicated `capability_kg/015a/` namespace (do not alter frozen or existing Task 015/018F outputs). Implement a small deterministic CLI or reusable parser, plus focused tests.

- `modules.csv`: module_key, module_name, source row count.
- `services.csv`: module_key, service_key, service_name, source row references/count.
- `documents.csv`: document_key, document_type [ICD|ISD], reference identifier and sanitized source metadata (no document body).
- `service_document_edges.csv`: module_key, service_key, document_key, type, source_row_number, reference_ordinal; preserve 1:N references and repeated occurrences as traceable source edges.
- `source_rows.csv`: row-level ledger retaining original Module, Service and raw ICD/ISD cells, source hash and row number; original Sub Module may be retained here **solely for lossless source audit**, never a business/entity relation.
- `exceptions.csv`: row/type/reason/original reference pointer for malformed references, collisions, etc.
- `manifest.json` and a **short** `validation_summary.md` with pilot totals, input/output hashes, deterministic rerun result, unresolved exception counts and next-step readiness.

Index schemas may be adjusted minimally to existing repo conventions, provided provenance, cardinalities, and distinctions remain intact.

## Tests/acceptance
- Focused fixtures: 1 ICD+1 ISD; 1 ICD+2 ISDs; 2+ ICDs+no ISD; ISD-only; neither; repeated URL within/across rows; leading/trailing spaces; semicolon empty tokens; duplicate service labels and module-key collision.
- No lost pilot source rows; every nonempty split ICD/ISD token maps to **exactly one** row-level reference occurrence or explicit parse exception. Report reference counts before/after normalization and assert equality with accepted+rejected.
- A module and service index is sufficient to answer `Module → Services → ICD/ISD references` deterministically; do not read/download documents.
- Two runs on unchanged input produce byte-identical deterministic outputs (except intentionally separated execution-time metadata), and the parser does not scan staging/ or require network.
- Maintain frozen phases and Task 018F as historical evidence; do not change their code/data. Only additive task-owned implementation.
- Run focused tests; report inherited environmental failures separately rather than masking them.

## Token and execution discipline
Inspect relevant indexes, project conventions and exact input only. Pilot **Common** only. Do not read ICD/ISD pages. Do not use LLM semantic classification. Do not implement tasks 015-B through J. Compact handoff: paths, counts, tests, exception categories, sample Module→Service→References lookup, blockers and commit SHA.

**STOP:** EA_REVIEW_CAPKG_015A. No automatic continuation.
