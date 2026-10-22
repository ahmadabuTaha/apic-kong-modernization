# Task 019-E-R2 — Establishment Main Business Capability → ICD Mapping (single-module pilot)

## Authorization and boundaries
Execute **only** this task on the **Establishment** Module from the **recovery effective catalog** (not original 019-D stale entries). This replaces the R1 methodology; do not rerun R1, 019-E, recovery, or any earlier stage. One execution, one Module, then STOP for EA review.

**Only output model:** `Main Business Capability → linked ICD document(s)`. Treat each source ICD as the classification unit; preserve stable ICD/page identity and the service-to-ICD links. Read the existing recovered ICD content from local cache as needed. Determine the Main Business Capability from the actual full ICD business semantics, not from an exact keyword, extracted “Business Function”, endpoint title alone, or the R1 function qualification filter. A document may support multiple Main Capabilities when explicitly justified. Do not force a single generic bucket.

**Do not produce, persist, derive, count, or use Business Functions or Sub Capabilities**. R1's 19 “no qualifying Business Function” findings are NOT proof of missing business semantics and must NOT automatically exclude an ICD from Main Capability mapping. Build the Main taxonomy from the ICD corpus directly and consistently across the single Module. Use R1 Main names only as non-authoritative hints, not as mandatory labels or accepted mapping. No HLD prerequisite.

## Coverage requirements
- Consider every Establishment ICD occurrence in the recovery effective catalog, including scheduler/utility/interface-specification ICDs where present. Resolve shared ICDs by document identity; preserve all service edges and original source documents.
- The EA specifically flags the following service identifiers for **explicit inspection** (input list intentionally includes repetitions). Resolve each against the recovered catalog; distinguish `ICD` vs `ISD`/no-ICD based on actual source metadata, not the service name. Do not invent an ICD for an ISD-only service. Count and report distinct identifiers and duplicates:
```
module-establishment::service-get-farming-establishments-by-owner
module-establishment::service-update-cr-details
module-establishment::service-establishment-logo-icds
module-establishment::service-terminate-establishments-punishments-icd
module-establishment::service-establishment-logo-icds
module-establishment::service-update-cr-detailsv2
module-establishment::service-mci-swap-cr
module-establishment::service-manage-establishment-license
module-establishment::service-mci-swap-cr-v2
module-establishment::service-violation-management-interface-specification-documents
module-establishment::service-manual-cr-swap-v2
module-establishment::service-momra-auto-push-utility
module-establishment::service-push-mecca-locations-changes-scheduler
module-establishment::service-transfer-ownership-engine-schedularv2
module-establishment::service-push-subsequent-supervision-license
module-establishment::service-mci-update-cr-cityv2
module-establishment::service-get-subsequent-supervision-notification
module-establishment::service-establishment-logo-isds
module-establishment::service-establishment-logo-icds
module-establishment::service-set-establishment-as-a-main-hrsd
module-establishment::service-transfer-ownership-engine-schedular
module-establishment::service-manual-cr-swap
```
- Do not discard an ICD because R1 produced zero Functions. Independently examine it to decide whether it evidences a Main Capability.
- If genuinely unable to link an ICD after direct reading, write its exact identity, service(s), content/evidence inspected and **precise reason** in a clearly labeled exception row. Do NOT silently drop it and do NOT fabricate a linkage. **Pilot is not EA-accepted while unresolved ICDs remain; do not claim 100% mapped on the basis of a parser PASS.** Services without ICD and ISD-only references must be disclosed separately, not misrepresented as missing ICD classifications.
- This pilot does NOT map Canonical APIs yet. Preserve ICD/service identities for later ICD/ISD/API relationship discovery. Future objective: each in-scope Canonical API receives an explicit evidence-based capability disposition, with unresolved API mappings surfaced immediately, not deferred across phases.

## Minimal work and deliverables
Use existing code/retrieval utilities; **do not build a new generic pipeline, database, parser framework, cache layer, or rebuild 11 Modules**. No Confluence/network access. Do not mutate recovery effective catalog, existing caches or historical indexes. No full repository suite. Write only:
1. `indexes/phase6/task019/019e_r2/main_capabilities.csv` — Main ID, label, short definition, candidate status.
2. `indexes/phase6/task019/019e_r2/main_icd_links.csv` — Main ID, ICD/page/document identity, source service(s), evidence pointer and concise mapping rationale.
3. `indexes/phase6/task019/019e_r2/coverage_exceptions.csv` — one row per unresolved ICD, no-ICD service, ISD-only flagged item, or reference-resolution defect with exact reason.
4. `outputs/phase6/task019/019e_r2/review_summary.md` — input/unique ICD coverage, mapped/unresolved counts, explicit reconciliation of **all flagged service identifiers**, 3–5 real mapping examples, any ambiguity, and concise focused checks.

Test only relevant mapping/coverage integrity: no source ICD silently dropped, no fabricated page IDs, no duplicate count inflation, no missing evidence pointer, untouched baseline. No unrelated design/optimization. Candidate mapping ≠ EA approval.

Commit implementation and update `codex/comm/HANSOFF.md` with exact outcomes and exceptions, then **STOP AT `EA_REVIEW_019E_R2`**. No roll-out to other Modules, no ISD semantic work, no Canonical API matching, no Sub or Business Function inventory, no consolidation, no Kong work.
