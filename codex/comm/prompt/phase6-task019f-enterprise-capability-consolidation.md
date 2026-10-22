# Phase 6 — Task 019-F: Cross-Module Enterprise Capability Consolidation

## Authorization
Execute **019-F only**. The EA has accepted `019-E-FINAL` as a **provisional baseline for consolidation**, not as final approval of every individual taxonomy boundary. Input is **ONLY existing 019-E-FINAL indexes and summaries**; do not reread HTML/ADF documents, call Confluence, parse schemas, read 019-C blobs, regenerate 019-E, or reopen previous stages. Do not run the full repository test suite.

## Required traceability model
`Module → [ICD and/or unpaired ISD document] → Module-local Main Business Capability → Enterprise Business Capability`

**Keep existing 019-E-FINAL direction/relationships intact:** Main→ICD and Main→ISD indexes are the authoritative source edges. Build consolidation as an **additive join**, never destructive replacement. Preserve Module ID, original Main ID/name/description, ICD/ISD source type, source document/page identity, Service and occurrence IDs, existing evidence pointers and source status, and newly assigned Enterprise Capability ID/name/definition. A Main can point to multiple Enterprise candidates **only when distinct documented semantics justify it**; preserve provenance and flag overlapping cases. Multiple Modules/Mains can map to one Enterprise Capability, but **similar words or shared integrations do not automatically mean the same business ability**.

## Method — indexed, low-token
1. Read and validate the six `indexes/phase6/task019/019e_final/*.csv` inputs (Main, ICD links, ISD links, excluded sources, coverage exceptions, module coverage). Validate Main closure against 136 baseline candidates, 32 Modules and exact input ID sets. Work from **names, descriptions and link rationale already indexed**; supporting indexes only where essential for a concrete ambiguity, **never raw source documents**.
2. Compare Main Capabilities across Modules based on their business outcomes, object, lifecycle, ownership and integration scope. Propose **Enterprise Business Capabilities** with specific meaningful business-ability names and concise descriptions. Distinguish `equivalent_consolidation`, `related_but_distinct`, `module_specific`, `requires_ea_decision`. Do not create a generic `Integration Management` mega-bucket: GOSI/NIC/HRSD capabilities merge only when functional scope truly matches; distinguish module business ownership and integration role. Preserve separate Employment, Termination, External and Training Contract Lifecycle capabilities unless positive evidence supports a changed boundary; do not undo existing EA decisions.
3. For **every one of the 136 Main identities**, output an explicit Enterprise linkage candidate or a named, evidenced `requires_ea_decision` row. **No silent Main drop.** Keep each original Main ID unchanged; no automated deletion/renaming in the source indexes. Where one Enterprise candidate consolidates multiple Modules, show precise source member IDs.
4. Create a **traceability view** by joining unchanged Main↔ICD and Main↔ISD links to the Main↔Enterprise candidates. Prove both ICD and ISD source identities and Service edges survive 1:many/many:1 joins without inflating unique-document coverage. Show examples with both ICD and ISD paths, where present. It is acceptable for an original linked document to support more than one Main/Enterprise Capability if explicitly evidenced; label links as candidate rather than claiming unique ownership.
5. **Carry the five unresolved 019-E-FINAL sources forward unchanged as explicit gaps**; they cannot acquire Enterprise links by invention:
   - Certificates ICD `4883382387`
   - Payments ICD `1062240312`
   - Services ISD `4416798854`
   - Training Indicators ISD `4939350056` (404)
   - Visa ICD `4237820100`
   Preserve all 25 source-excluded occurrences separately, never mistake `OLD/IGNORE` marking for verified production retirement. Include precise downstream impact: unclassified source may leave Canonical API capability mapping unresolved later. No workaround or reread in 019-F.
6. Produce a concise review of each proposed Enterprise capability: definition, mapped Modules and Main identities, count of unique linked ICD/ISD documents, merger rationale, ambiguity. **Do not assert Enterprise capability names are EA-approved**. Highlight difficult merges/splits early in `review_queue`, not only in the final summary.

## Exactly six outputs — generated locally, no raw document copies
`indexes/phase6/task019/019f/enterprise_capabilities.csv` — Enterprise candidate ID, meaningful name, definition, status.
`indexes/phase6/task019/019f/main_enterprise_links.csv` — Module, original Main ID, Enterprise ID, relationship type, compact rationale, status.
`indexes/phase6/task019/019f/enterprise_source_traceability.csv` — joined Enterprise↔Main↔Module↔(ICD/ISD) with original evidence IDs/pointers and source Service/occurrence identities.
`indexes/phase6/task019/019f/review_queue.csv` — precise disputed consolidation boundaries and original unresolved source cases, no vague aggregate-only records.
`indexes/phase6/task019/019f/coverage_reconciliation.csv` — per Module Main ID closure, ICD/ISD identities joined, source exclusions and unresolved carry-forward (no false coverage inflation).
`outputs/phase6/task019/019f/review_summary.md` — short totals, direct trace examples, merge decisions and all exceptions by identity.

## Guardrails and completion
- Do not create Business Functions, Sub Capabilities, new parser, retrieval cache, generalized knowledge graph, or architecture platform. Do not perform ISD/API matching, endpoints, APIC/Kong changes or other next phase work. Reuse existing CSV readers/utility code or write only the smallest deterministic join/classifier needed.
- Do not run a broad reclassification of 32 modules' source ICDs. **This task processes 136 Main candidate rows and their existing evidence links, not 1,985 raw document occurrences.**
- Focused checks only: source catalog/indexes unchanged, complete 136 Main identity accounting, no invented ICD/ISD links, correct preserved evidence + Module IDs, unique coverage not inflated by join, all five exceptions and source exclusions transferred, deterministic output.
- If source index metadata is insufficient to justify a merge, retain separate Enterprise candidate and flag `requires_ea_decision`; **no additional extraction to resolve it inside this task**.
- Commit minimal implementation and focused tests; update `codex/comm/HANSOFF.md` once with counts, named review decisions, source coverage and focused test results. **STOP at `EA_REVIEW_019F`**. No Canonical API linking or next task without explicit EA authorization.
