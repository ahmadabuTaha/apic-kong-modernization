# Phase 5 — Task 018C: Enterprise Business Domain — Deterministic QIWA Module Mapping

## Authorization and architectural intent
EA authorizes **Task 018C only**. This is a deliberate **reverse, implementation-anchored reconciliation** of APIC operations with the architect-curated QIWA integration inventory. The objective is to exploit work already completed by the architect rather than re-infer modules or backend call relationships from API names, YAML schemas, or LLM guesses. Produce a deterministic, auditable candidate domain distribution and explicit exceptions.

**Authoritative source for the QIWA module inventory and parent-child relationships:** `neo4j/csv/Qiwa_Modules_Services.csv`. Read the **actual** header, distinct Module_Name values, parent/child identities, types and source-row IDs before building a mapping. Do not assume a fixed number of distinct CSV modules or invent their labels. Preserve exact original module strings and hash the source. The curated CSV is the authoritative **AS-IS QIWA integration/module skeleton for this task**, not automatically the authoritative approved Enterprise Business Domain ontology.

**Additional architect-nominated candidate buckets:** `Occupations` and `TIP`. Keep them explicitly visible even if no CSV Module_Name exactly matches. Do not merge TIP with LO/QAAS/KAYAN exposure channels by default; assess whether TIP is a module, exposure channel, business responsibility or an overlapping architectural slice with explicit evidence/status. Include previous EA 11-candidate skeleton as historical Task 018B comparison only; do not silently rename/force-match old and new buckets. No new candidate beyond literal CSV module inventory plus explicitly supplied Occupations and TIP.

**Important distinction:** Module ownership is a **candidate domain proxy**, not proof of cross-platform enterprise domain ownership. Provide a separate field `source_qiwa_module` and `candidate_domain_bucket`; do not erase this separation. A module can expose/support another business responsibility, and cross-module dependencies do not automatically change the calling operation's primary assignment.

## Mandatory startup and constraints
1. Pull current `main`, read `AGENTS.md`, `codex/comm/CURRENT_TASKS.md`, latest `codex/comm/HANSOFF.md`, and inspect task-018B outputs / accepted 014 canonical indexes / CodeGraph / backend resolver. Confirm input path exists; locate CSV and legacy Cypher catalog if available; do not block on absent Cypher catalog.
2. Source-of-truth priority by question: **APIC canonical API/operation + catalog properties + CodeGraph** for API identity and configured invocations; **QIWA CSV** for QIWA module/service/dependency assertions; **Neo4j MCP** for focused graph corroboration only. Neo4j is not required if inaccessible: perform CSV-and-APIC deterministic mapping and explicitly label validation unavailable.
3. Preserve accepted 2,414 HTTP operations and 2,036 canonical APIs as fixed coverage baselines, including 41 zero-operation/unsupported APIs. Preserve 018B mapping unmodified as a comparison baseline, not as evidence for 018C's new primary choices.
4. Immutable staging evidence and frozen 014–018B components. No mass raw export or all-pairs search; use indexes, source paths and focused deterministic retrieval. No ICD crawling, business-domain taxonomy discovery, Task 019, productization or Kong design.

## Step 1 — CSV inventory normalization without loss of identity
Read/validate CSV encoding, headers, row count, unique module values and types. Based on actual columns, identify the Parent_Service → Service_Name/Child relation and relevant `Type` values. Do not infer a direct edge from statistical shared-component summaries. Preserve `ID`, `Module_Name`, `Parent_Service`, `Service_Name`, `Type`, `Service_Normalized`, endpoint/URL columns if actually present and source references.

For **API-HTTP**: model direct evidenced Parent→Child edges and bounded child-as-parent traversal, distinguishing `CALLS_PARENT_SERVICE` from `USES_COMPONENT` where Neo4j corroborates them. For **DP**: preserve terminal/boundary integration candidates, not automatic APIC-wrapper assertions. Other child types remain visible as supporting context. Detect duplicate rows, same-name distinct identities, whitespace, punctuation, case, many-to-many and cross-module collisions; use normalized tokens for **candidate discovery only**, preserve original IDs.

## Step 2 — Canonical APIC operation and invocation evidence
Load accepted canonical APIC operation inventory and CodeGraph relations. Resolve `invoke.target-url` including referenced **catalog property values** using existing accepted resolvers **without modifying them**. Preserve exact configured expression, resolved property/host, dynamic path remainder, catalog/environment, operation ID, HTTP method/path, source location and canonical IDs.

Produce two independent attributes:
- `backend_platform_classification`: if evidenced resolved configured invocation endpoint/host **contains 'ace' (case-insensitive per EA rule)** => `ACE_BACKEND`; if a **complete/evaluable configured endpoint/host is evidenced and does not contain 'ace'** => `EXTERNAL_VIA_DATAPOWER` (an APIC/DataPower gateway exposing an external backend); if endpoint/host absent or unresolved => `PLATFORM_UNRESOLVED`. Apply to resolved **host/platform portion**, not only the unresolved full expression. Avoid treating `$(request.path)` as reason to erase an already resolved ACE host.
- `full_target_resolution`: `FULLY_RESOLVED`, `PARTIALLY_RESOLVED_DYNAMIC_PATH`, `UNRESOLVED` (and explicit configuration conflicts if needed).

An external target through APIC/DataPower is a classification of the APIC configured invocation path, **not** proof a QIWA DP component is an APIC Wrapper, nor proof of runtime egress. Keep APIC `ACE_BACKEND`/external distinction separate from CSV child `API-HTTP`/ `DP` Type. Catalog/environment conflicts must remain unresolved instead of blending values.

## Step 3 — Deterministic joins with match-tier evidence
Correlate **APIC canonical API + operation** with the QIWA CSV **API-HTTP and DP entries**, leveraging accepted CodeGraph backend properties and source pointers.

Implement explicit matching tiers and output the tier for each candidate:
- `J1_EXACT_ENDPOINT_OR_ROUTE`: grounded endpoint/service route or durable cross-system identifier explicitly ties operation to service.
- `J2_RESOLVED_BACKEND_AND_OPERATION`: resolved endpoint/route plus compatible operation/path and a unique scoped service identity; explain exactly which data bridges the systems.
- `J3_NAME_ONLY_CANDIDATE`: case/trim/normalization matches operationId/service name, but no authoritative route bridge. **Never classify as confirmed**.
- `J0_NO_MATCH`, `JX_AMBIGUOUS`, `JS_SOURCE_UNAVAILABLE`, `JC_CONTRADICTORY`.

If no endpoint or cross-system keys are present in the CSV, explicitly state that the source alone cannot prove J1/J2; preserve J3 candidates rather than upgrading by confidence score. Do not infer `ParentService` and APIC operation identity from a name match alone. Apply scope/environment checks and record one-to-many candidates instead of arbitrarily selecting one.

For ACE-backed operations: attempt joining to a QIWA Parent Service and traverse relevant direct `API-HTTP` children, `DP` boundaries, and bounded transitive branches. **Do not infer primary domain from a child module**: primary provisional module attribution starts from a confirmed parent/entrypoint mapping; child module affiliations are supporting cross-module dependencies. For external-backed operations: seek grounded DP correlation only where evidence exists, and **do not create an ACE journey**. No match => unresolved, not `Common` or TIP fallback.

## Step 4 — Deterministic candidate-domain distribution and reconciliation
- Assign `candidate_domain_bucket` from exact QIWA `Module_Name` for evidenced operation→service parent/entrypoint ownership **only if a defensible match exists**. Keep original source module separately.
- `Occupations` and `TIP` are explicit additional candidates; classify into them only with direct source evidence or an EA-provided mapping, never because of superficial name/channel similarity. If candidate is an exposure context rather than domain, retain its `domain_ontology_review_required` flag; don't suppress the requested bucket.
- If multiple parents/modules legitimately serve one operation, keep primary null and multiple alternatives, with reason `MULTI_MODULE_AMBIGUOUS`, unless a defensible single entrypoint is evidenced. Child dependencies may be represented as `supporting_modules` not duplicated primary.
- Preserve completely unmatched operations and ambiguous operations separately. Do not optimize for classification coverage. Do not override 018B, infer business ownership, label modules as ratified enterprise domains, or declare retired/test APIs solely from module omission.
- Provide **side-by-side comparison** with 018B: matched agreement (with explicit, reviewed module→018B bucket correspondence only), changed candidate, previously unmapped now evidenced, contradictory, still-unresolved. Do not force old/new taxonomy equality.

## Mandatory downloadable CSV outputs — FULL ESTATE
Generate UTF-8 CSV files in `outputs/task018c/` (or repository-approved generated-output location) with stable ordering and deterministic quoting; no secret-bearing endpoint values:
1. `operation_domain_distribution.csv` — **one row per all 2,414 operations**, even unmatched; required columns: canonical_api_id, canonical_api_name, operation_record_id, operation_id, method, path, catalog_or_environment, backend_platform_classification, full_target_resolution, apic_join_status, join_tier, source_qiwa_module, candidate_domain_bucket, candidate_alternatives, supporting_modules, matched_parent_service, matched_child_service, child_type, csv_row_ids, evidence_references, assignment_status, ambiguity_reason, previous_018b_candidate, review_required.
2. `domain_distribution_summary.csv` — exact CSV-derived Module_Name buckets **plus Occupations and TIP even if zero**, operation primary counts, candidate-only counts, supporting-only counts, distinct canonical APIs, no-match/ambiguous counts. Include a clearly labeled overall `UNMAPPED` summary row (not a fabricated domain).
3. `ambiguous_operations.csv` — **all** cases with ambiguous/contradictory/multiple joins, multi-module conflict, name-only links, unresolved platform or insufficient evidence. Include all candidate matches and reasons; do not cap at 30 review cases.
4. `apic_qiwa_match_evidence.csv` — row-per-match-edge with exact APIC, CSV row, original parent/child/type/module, matching signals, join-tier, endpoint-classification status, source and confidence qualifiers.

Also retain zero-operation API accounting separately, provenance, source hashes, reproducible manifests and a compact reviewer explanation.

## Determinism / acceptance
- Completeness: 2,414 unique accepted HTTP operations exactly once in distribution CSV; 2,036 canonical APIs accounted for independently; all CSV rows counted/checksummed without treating source-row IDs as durable service IDs.
- CSV labels from actual inventory, plus exactly two explicitly nominated extra labels: **Occupations** and **TIP**; no synthesized Domain labels. Explicitly report if overlaps already occur in source.
- Every primary domain assignment must link to source CSV module + justified APIC↔QIWA service join. Exact name alone is insufficient; J3 candidates remain unassigned.
- Backend classification uses resolved catalog host `ace` presence independently of full runtime URL completeness; external via DataPower is configured target class, not runtime proof.
- Separate API-HTTP call edges from DP component edges. Parent-child traversal bounded, no invented call order, no cross-environment borrowing.
- Historical 018B and frozen 014–018A untouched. Tests for name collisions, dynamic `$(request.path)`, ACE and non-ACE targets, unmatched and multi-match cases, 0/1/2+ operations, stable ordering, no sensitive values, and no double-counting.
- Report real matching coverage, candidate-only, and gaps without inventing certainty. If strong joins are rare, **say so plainly**; still produce complete CSVs.
- Commit/push only Task 018C implementation and evidence under permitted repo conventions, update `codex/comm/HANSOFF.md`, then **STOP at EA_REVIEW_TASK018C**. Do not reclassify 018B outputs, approve domains, start Task 019 or Kong TO-BE.

**Operating model:** Codex discovers → Integration Architect validates → Enterprise Architect decides.
