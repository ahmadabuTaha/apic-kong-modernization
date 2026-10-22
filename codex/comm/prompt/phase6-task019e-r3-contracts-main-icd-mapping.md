# Task 019-E-R3 — Contracts: Main Business Capability → ICDs

**Authorized scope: Contracts Module only.** Reuse R2's existing mapper and the **recovery effective catalog**; read locally cached Contracts ICD bodies. Do not rerun R2/Recovery/older tasks or process any other Module. Complete the Contracts ICD inventory, then derive Main Business Capability candidates directly from the ICD business semantics and link ICDs with stable page/document/service identities and source evidence. **No Business Function or Sub Capability extraction, records, or intermediary model.**

**Capability names:** use clear business-ability noun phrases (e.g. “Contract Lifecycle Management”, “Contract Template Management”), with “Management”, “Administration”, “Validation”, “Monitoring”, or another meaningful capability noun as appropriate. **No slash-separated keyword piles, one-word bare labels, or automatic prefix/suffix padding**. Do not blindly copy the Contracts HLD: where locally available it is only a taxonomy cross-check, not evidence or a mandatory list. R2 Establishment candidate labels are not a cross-Module taxonomy.

**Coverage:** account for every Contracts ICD occurrence and unique document from the recovery catalog; each gets a well-supported Main candidate link or a precise, immediately visible unresolved exception with original service, source identity and reason. One ICD can have multiple justified links. Do not mislabel services with ISD-only/no-ICD references as missing documents or invent ICDs. Explicitly inspect recovered Contracts page `6121750531` and ensure no stale 198-byte placeholder is used. Avoid R1's strict business-function qualification filter; it was not a reliable classification gate. No synthetic capability to force coverage. Candidate mapping is not EA approval.

**Reuse, don't rebuild:** Prefer a minimal parameterization of R2's `business_capability_kg.establishment_main_icd_mapping` for Contracts if needed; no new generic platform, parser, cache, DB, pipeline or framework. No Confluence/network requests, no changes to any existing catalogs/caches, and no 11-Module replay. No ISD body parsing, Canonical API/Operation matching, cross-module merging, or Kong work. Do not run the full repository test suite.

**Exactly four task-scoped outputs:**
- `indexes/phase6/task019/019e_r3/main_capabilities.csv`
- `indexes/phase6/task019/019e_r3/main_icd_links.csv`
- `indexes/phase6/task019/019e_r3/coverage_exceptions.csv`
- `outputs/phase6/task019/019e_r3/review_summary.md`

Review summary must state total Services / ICD occurrences / unique ICD documents / mapped ICDs / unresolved ICDs / ISD-only or no-ICD services separately; list **every** unresolved or ambiguous source by exact identity and reason, include 3–5 genuine Main↔ICD evidence examples, and show focused integrity-check results. Only targeted checks: exact source coverage, valid evidence pointers, no duplicate inflation, names, untouched frozen inputs. If missing input or unreadable document prevents complete coverage, report the blocker immediately, do not hide it in aggregate PASS and do not broaden scope.

Commit only necessary implementation/test changes and update `codex/comm/HANSOFF.md` with exact results. **STOP: `EA_REVIEW_019E_R3`.** No other Module without approval.
