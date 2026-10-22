# Phase 6 / Task 019-E — ICD Main/Sub Business Capability Discovery

**Status:** AUTHORIZED_FOR_CODEX — ICD_CAPABILITY_CANDIDATES_ONLY
**Stop gate:** `EA_REVIEW_TASK019E`
**EA decision:** Accept 019-D TECHNICAL PASS as retrieval foundation. Known missing ISD page 4939350056 remains an evidence exception; it is NOT an ICD extraction blocker.

## Target
Extract and register evidence-backed **Main Business Capabilities** and **Sub Business Capabilities** from acquired **ICDs** across **ALL 32 Modules**, associating each candidate with its Module, Service(s), ICD document(s) and precise content evidence. This is the FIRST semantic task. It is **not** API/Operation matching or graph construction.

Hierarchy for business context: `Module → Main Business Capability → Sub Business Capability`, with traceability `Sub Capability → Service → ICD evidence`. This is a candidate knowledge layer: Module is source context, not automatically the business ownership boundary. Preserve many-to-many service/capability support and cross-module capability candidates without forcing a single parent or global merge. The source inventory identity remains `Module → Service → ICD/ISD`; do NOT use Sub Module for grouping, names or identity.

## Ground truth / preflight
Read latest AGENTS.md, CURRENT_TASKS.md, HANSOFF.md. Validate the accepted 019-B/019-C/019-D manifests and use 019-D index-first retrieval plus explicit selected document reads for ICD only. No network, no Confluence refetch, no raw APIC staging scan. Reuse the stored bodies under 019-C; never rewrite them.
Source baseline: 32 Modules, 952 Services, 988 ICD occurrences, 1,940 fetched ICD+ISD occurrences, 1,932 unique fetched blobs. Derive exact *available unique ICD* count from accepted catalog rather than treating all 988 occurrences as separate files. Services lacking ICD are valid, including schedulers documented only via other sources; report `no_icd_reference` without creating capabilities from ISD in this task.

## Extraction pipeline (deterministic before semantic)
1. Targeted retrieval/index joins identify all modules, services, ICD edges and available ICD document IDs. Process each unique ICD body ONCE per content hash/parser version, reuse extracted evidence for every applicable service/module edge. Work in resumable bounded batches by Module/document; **do not stop after Common**. Cover the full inventory and report per-module progress.
2. Faithfully parse cached HTML/storage markup into ordered text blocks (headings, sections, paragraphs, tables, lists) with stable evidence pointers (document ID, source hash/version, section heading and block/offset or equivalent). Retain relevant table structure and nearby context. Explicitly distinguish successfully parsed content from missing/empty/unsupported/malformed; do not hallucinate missing sections.
3. Extract business-function statements, actors, business objects, lifecycle actions, rules, triggers and explicit process outcomes where evidenced. Separate **Main Capability** (coherent business ability) from **Sub Capability** (business action/ability nested under the main). Do not confuse application module, document title, HTTP endpoint, technical integration step, scheduler implementation or external-system name with a business capability.
4. Generate normalized candidate labels and stable scoped candidate IDs, store original source wording, rationale and precise evidence spans. Track extraction method, strength/confidence and `candidate | needs_review | unsupported_by_document` status; NEVER self-approve. If the evidence is too weak, output unresolved evidence/require-review records, not guessed capabilities.
5. Allow one ICD to substantiate multiple capabilities and one capability to be supported by multiple ICDs/services; preserve each source linkage. Identify possible cross-document same-capability candidates for later EA review, but do not silently merge them across modules.
6. Parser/extractor cache keyed on content hash + parser/extractor version + rules version, with explicit invalidation and cold/warm telemetry. Keep rich full-text/structured source blocks locally under 019-E ignored indexes or outputs; default downstream queries return compact capability records and evidence snippets/pointers. Do not load all 184.82 MiB or all ICDs into one LLM context.
7. Keep sensitive data and original private URLs out of committed outputs, prompt/response examples and public reports. Only local generated ignored artifacts may contain controlled source passages. Avoid printing raw whole documents and secrets.

## EA-mandated execution order — MODULE-FIRST (supersedes any ambiguous batching guidance)
**Finish each Module independently before beginning the next Module's capability model.** Module order is deterministic and checkpointed. Bounded document-level parsing batches are allowed *within* a Module; they are not permission to consolidate globally or jump to the next Module with an unfinished local capability model.

For each Module, strictly follow these steps:
1. **Module scope lock:** enumerate ALL ICD reference occurrences and unique available ICDs linked to its Services from 019-D. Include ICD-only and no-ICD service cases; record source/count/hash reconciliation.
2. **Read all available ICDs for THIS Module:** extract business functions, rules, actors, outcomes and evidence pointers at document level. Reuse existing parsed evidence for shared ICD blobs, without rereading unchanged content. Missing/unparseable ICDs remain explicit gaps.
3. **Within-Module Sub Capability construction:** consolidate *only within this Module* the evidenced business functions into candidate Sub Capabilities, preserving distinct functional variants, business outcomes, rules and all service/document evidence. Do not flatten meaningful distinctions to generic labels.
4. **Within-Module Main Capability construction:** assemble Main Capability candidates **after** the Sub candidates have been reviewed against the Module's complete available ICD evidence. A Module may contain multiple Main Capabilities, and its Module name is not automatically one of them.
5. **Module completion gate:** produce a compact independent `module_capability_model` and `module_completion_manifest`, including ALL input ICD IDs/counts and dispositions, precise Main → Sub → Service → ICD linkages, gaps, review-required items, deterministic hashes and checkpoint status. Gate = `MODULE_COMPLETE_WITH_EVIDENCE` when every available ICD was covered and all exceptions are accounted for; `MODULE_COMPLETE_WITH_GAPS` when source/parser gaps are explicitly documented; `MODULE_PARTIAL` if the available corpus is not yet fully processed. Do NOT claim any Module completed based solely on some ICDs. A documented unavailable source can qualify for COMPLETE_WITH_GAPS, not all-evidence-complete.
6. **Only then move to the next Module.** Persist a per-module checkpoint so interrupted jobs resume the incomplete Module without revisiting completed models unless their source/algorithm version changes.

When all 32 Modules have been individually processed, emit a **cross-module comparison candidate queue only** (potential overlaps/relationships with evidence pointers); do not merge, rename or approve Sub or Main Capabilities across Modules. **Later separate EA-authorized tasks** must consolidate Sub Capabilities first and Main Capabilities second, retaining the 32 immutable local model identities and mappings.

Treat local completion as **evidence-accounting and candidate completeness**, NOT EA approval or guarantee of API implementation. No API coverage assertions are possible from ICD alone. Keep separate explicit evidence gaps and review items; do not invent mapping for no-ICD services.

### Additional task-owned outputs
- `outputs/phase6/task019/019e/modules/<module_key>/module_capability_model.json` and `module_completion_manifest.json` (or equivalent deterministic structured outputs).
- `indexes/phase6/task019/019e/module_completion.csv` with status, ICD expected/available/processed/failed counts, local Main/Sub counts, evidence closure, source signature and checkpoint hash.
- `indexes/phase6/task019/019e/cross_module_review_candidates.csv`: observation queue only, NO automatic global consolidation.
- Final `validation_summary.md` and HANSOFF must include count of Modules in each completion status, enumerate partials/gaps with reasons and separate **Task 019-E focused suite PASS** from inherited full-repository failures/setup errors. If any Module remains PARTIAL, report full execution as PARTIAL and stop for EA review.

## Deliverables
- Code: `business_capability_kg/`; focused tests: `tests/business_capability_kg/`.
- Indexes: `indexes/phase6/task019/019e/` with `icd_parse_status.csv`, `main_capabilities.csv`, `sub_capabilities.csv`, `capability_evidence.csv`, `capability_service_icd_edges.csv`, `review_queue.csv`, and targeted versioned parse/extraction cache. Schema may be compactly adapted to repo conventions; keep distinct main/sub IDs and all provenance.
- Reports: `outputs/phase6/task019/019e/manifest.json`, `module_coverage.csv`, `validation_summary.md`. Give per-module ICD counts, available/parsed/unsupported, candidates/review flags and evidence coverage; report number of modules actually processed. A partial run must be explicitly labeled PARTIAL, never TECHNICAL PASS for all modules.
- Retrieval examples: (1) Module → Main/Sub candidates; (2) Sub Capability → Services/ICDs/evidence; (3) ICD → candidate capabilities; (4) no-ICD service → explicit uncovered state.

## Validation and stopping rules
- ALL 32 module labels and ALL 952 services represented in coverage, including services with no ICD. Reconcile exact ICD reference counts with frozen 019-D catalog, independent of ISD.
- Each candidate must cite a real fetched ICD with stable content pointer and service/module relationship. No candidate derived exclusively from name, Product, 018F domain candidate, prior classifier or ISD.
- Parsing/extraction is deterministic or captures versioned repeatable inputs/outputs; rerun unchanged documents is a cache HIT. Test HTML tables/headings, mixed content, evidence offsets, multi-capability and shared ICD, no-ICD services, low-evidence refusal, malformed content and cache invalidation.
- Candidates are **EA review inputs only**; do not assert approved business boundaries or functional API equivalence.
- Run targeted tests, report inherited global test suite issues separately with explicit counts. Maintain a concise exception register and never conceal a missing document / parser gap.
- No ISD request/response/operation extraction, no canonical API matching, no scheduler job identity synthesis, no knowledge-graph construction, no productization, CI/CD or Kong.
- In final handoff report actual processed module/doc counts, evidence-backed capability/sub-capability candidate counts, unresolved count, cache effectiveness, tests, evidence paths, and commit SHA. Stop at `EA_REVIEW_TASK019E` without auto-continuation.
