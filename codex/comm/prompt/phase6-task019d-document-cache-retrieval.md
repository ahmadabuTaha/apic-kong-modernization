# Phase 6 / Task 019-D — Persistent Document Cache & Retrieval Index

**Status:** AUTHORIZED_FOR_CODEX — DOCUMENT_CACHE_AND_RETRIEVAL_ONLY
**EA decision:** Accept Task 019-C TECHNICAL PASS as the immutable acquisition baseline with one known source 404.
**Stop gate:** `EA_REVIEW_TASK019D`.

## Objective
Build a persistent, low-token, deterministic **document lookup and content retrieval layer** over Task 019-C's existing downloaded ICD/ISD documents for ALL modules.

Required retrieval pattern:
`Module → Service → ICD/ISD reference → verified cached content`

**Do not fetch or re-download any document in this task.** This is not semantic discovery, no text interpretation, and no classification. Avoid a vector database, embeddings, LLM summaries or an enterprise search platform for this foundation step.

## Accepted baseline
Read `AGENTS.md`, latest `codex/comm/CURRENT_TASKS.md` and `codex/comm/HANSOFF.md`, then validate targeted `019b` and `019c` manifests and indexes only.

- 32 literal modules, 952 module-scoped services and 1,941 document reference occurrences (988 ICD; 953 ISD).
- 1,940 fetched occurrences, one explicit 404 failure (Confluence page `4939350056`), zero pending/blocked.
- 1,932 distinct physical content blobs, 193,802,986 deduplicated content bytes (184.824930 MiB); source content is stored at `outputs/phase6/task019/019c/documents/blobs/`.
- Module/service occurrence pointers and acquisition indexes are authoritative for source-to-file links. Preserve the original `Module → Service → ICD/ISD` relationship, source row, ordinal, ICD/ISD type, status, stable identity, content hash, and acquisition provenance.
- `Sub Module` is not an entity or grouping key. Do not mix in older QIWA CSV or semantic/domain mapping evidence.

## Implementation: bounded, deterministic, index-first
1. Build a manifest-backed **persistent retrieval catalog** from 019-B/019-C indexes and verified local content blobs. Prefer compact SQLite or deterministic CSV/JSON indexes consistent with the repository; do not introduce an external service or large new dependency.
2. Key lookups using exact module/service identity and stable document identity; expose lookups by Module, by Module+Service, by document ID and by type (ICD/ISD). Return all occurrences even for shared or semicolon-separated references. Never invent cross-module service equivalence.
3. Return lightweight **document metadata and status first**, without opening blob bodies: typed document ID, module/service link, source row and ordinal, hash, file size, local path, content type/version and retrieval status. Support optional content loading for **explicitly selected document IDs only**.
4. Implement safe content access that verifies file existence, path containment, expected hash and byte length. Return a precise `missing_blob`, `corrupt_blob`, `acquisition_failed_404` or other evidenced status instead of falling back to remote access, inventing text, or silently omitting references.
5. Build indexes from 019-C data **without duplicating document bodies**. If 019-C stores HTML, preserve/retrieve exact raw HTML bytes; do not strip HTML, extract text, parse sections, infer endpoints or produce semantic chunks in this task. A future parser may implement versioned semantic extraction separately.
6. Incremental reuse: stamp index schema/implementation version plus source manifest/index hashes; unchanged inputs produce cache HIT and no rebuild. Changed referenced acquisition manifest/index triggers targeted invalidation/rebuild; preserve historical 019-C evidence byte-for-byte. Ensure reproducible results and stable ordering.
7. Provide a small documented CLI/library interface that is efficient for later module-by-module workloads, e.g. `list-modules`, `list-services --module`, `list-documents --module --service [--type]`, `document-info --id`, `read-document --id --out <local-path>`. CLI must never dump all HTML to terminal by default; explicit read only, with output limit/file write. Use bounded index-first retrieval, not repeated whole-directory scans.
8. No network calls, no Confluence API access, no APIC staging scans, no semantic processing, and no changes to frozen 019-A/B/C code, indexes or source files beyond additive task-owned code.

## Paths
- Versioned code: `business_capability_kg/`; tests: `tests/business_capability_kg/`.
- Persistent derived catalog/indexes: `indexes/phase6/task019/019d/`.
- Manifest, lookup examples and compact validation summary: `outputs/phase6/task019/019d/`.
- Content remains exclusively in `outputs/phase6/task019/019c/documents/blobs/`. Do not copy all 184.82 MiB into the new cache or commit source content.
- Generated evidence stays in ignored `outputs/` and `indexes/`. Avoid exposing full private URLs or source contents in committed code/logs.

## Acceptance / Validation
- Full metadata coverage: 32 modules, 952 services and all 1,941 source-reference occurrences accessible, including the 404 in lookup responses; fetched versus failed reconciles to 1,940 + 1.
- Distinguish 1,941 occurrences from 1,932 unique physical blobs. Read content only by explicit request, never during metadata-only lookup.
- Shared document reuse and 0..N ICD/ISD multiplicity preserved, with stable source provenance.
- All 1,932 fetched local physical blobs are indexed and validated for hash/byte size (use targeted/precomputed validation where safe); inaccessible 404 is not represented as an empty or successful content file.
- Cache cold/warm validation demonstrates index reuse, deterministic output, zero acquisition network requests and zero whole-document body reads for metadata queries.
- Tests cover lookup correctness, module separation, order, shared blobs, semicolon-separated references, read-on-demand, missing/corrupt blob, cache invalidation, and the known 404.
- Final summary reports counts, paths, cache HIT/MISS evidence, tests, unresolved errors and measured **catalog size/overhead** separately from the existing **193,802,986 content bytes**; do not double count bytes or claim downloads in 019-D.

## Handoff
Write a short HANSOFF section with code commit, manifest/index paths, closure, cache cold/warm telemetry, sample successful scoped lookups, 404 behavior and tests.

**STOP at EA_REVIEW_TASK019D.** No ICD/ISD semantic extraction, endpoint extraction, capability taxonomy, canonical operation matching, graph, Productization, CI/CD or Kong.
