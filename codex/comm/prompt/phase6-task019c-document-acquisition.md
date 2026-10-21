# Phase 6 — Task 019-C: ICD/ISD Document Acquisition

Status: AUTHORIZED_FOR_CODEX. Stop: EA_REVIEW_TASK019C.
EA accepts 019-B technical baseline for continuation.

## Scope
Acquire ICD and ISD source documents for **all 32 Modules**, **952 Services** and **1,941 reference occurrences** from the accepted Task 019-B indexes: 988 ICD and 953 ISD references. Do not infer that 1,941 references mean 1,941 successfully retrievable files. Preserve hierarchy Module → Service → ICD/ISD; Sub Module excluded.

Read AGENTS.md, CURRENT_TASKS.md, HANSOFF.md. Validate 019-B manifest and reuse indexes/phase6/task019/019b/ (including protected source-row audit for original references). Do not rerun normalizer or scan APIC staging. The original outputs/services_icd_isd_inventory.csv remains unchanged.

## Execution
1. Resolve each source reference from the original 019-B evidence without constructing guessed URLs.
2. Retrieve available ICD/ISD document content through existing authorized access; if source access is unavailable, record exact blocked/failed/pending status and continue independent work. Never treat a page error or sign-in screen as valid source content.
3. Preserve faithful complete document bytes/source representation and metadata: document identity, ICD/ISD use, source/version when supplied, MIME type, file hash, length, title, retrieval time and provenance.
4. Persist each distinct physical document once (dedupe by verified identity/content); module ICD/ISD folders contain pointers or manifests to shared physical content. All Service-to-Document edges survive shared references and semicolon multiplicities.
5. Support incremental resume, bounded requests and retries, durable progress markers, safe local filenames, version-change detection and checksum verification. Do not repeatedly download unchanged documents.
6. Preserve all modules and services in module-specific pointers regardless of fetch success. Document acquisition and organization only; **NO semantic extraction**, endpoint analysis, Business Capabilities, Canonical API matching, scheduler identity derivation, graph, productization or CI/CD.

## Task ownership
Code: business_capability_kg/; tests: tests/business_capability_kg/.
Physical documents: outputs/phase6/task019/019c/documents/blobs/.
Module-specific reference directories:
outputs/phase6/task019/019c/modules/<module_key>/icd/
outputs/phase6/task019/019c/modules/<module_key>/isd/
Indexes: indexes/phase6/task019/019c/document_acquisition.csv, module_document_coverage.csv, failures.csv.
Reports: outputs/phase6/task019/019c/acquisition_manifest.json and acquisition_summary.md.
All fetched evidence and indexes remain local in ignored outputs/ and indexes/; never commit document content or private document URLs. Preserve earlier task artifacts unchanged.

## Acceptance
- Reconcile **32 modules, 952 services, 1,941 occurrences** to explicit fetched/failed/blocked/pending states without loss.
- Per-module links permit targeted ICD/ISD retrieval for the next task.
- Preserve one-to-many and shared-document relations; real fetched content distinguished from mocks.
- Validate hashes, sizes, stable reruns, retry/resume and shared content with deterministic tests.
- Report partial completion candidly if source access is unavailable.

## Mandatory LAST SECTION: Storage & File Size Totals
At the end of acquisition_summary.md AND the Task 019-C HANSOFF summary report:
- Number of unique successfully downloaded and validated physical content files (not reference occurrences).
- **Exact total size_bytes = sum of local on-disk bytes for each unique persisted content blob, counted once**, with converted MiB/GiB (base 1024, labeled). Use measured file sizes, not predictions.
- ICD-specific and ISD-specific distinct file counts and sizes; explicitly reconcile overlap if one blob serves both categories.
- Expected 988 ICD + 953 ISD = 1,941 reference occurrences versus fetched document count, failure/blocked/pending totals, and actual completion rate.
- Per-module unique file count and logical bytes in module_document_coverage.csv; note that shared documents cause module totals to differ from global deduplicated bytes.
- Report pointer/index overhead separately if measured; never add repeated logical references to physical total.
- If no downloads succeed, report measured 0 bytes and mark unavailable remote sizes as unmeasured, not 0-byte documents.
- Assert storage totals from filesystem sizes and manifests in tests.

STOP at EA_REVIEW_TASK019C. No next task automatically.
