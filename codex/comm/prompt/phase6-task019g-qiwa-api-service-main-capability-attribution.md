# Phase 6 — Task 019-G: Qiwa API-HTTP Service → Module Main Capability Attribution

## Goal and boundary
Build **additive, evidence-traceable links** between API-HTTP services in `neo4j/csv/Qiwa_Modules_Services.csv` and **Module-local Main Business Capabilities**, using existing ICD/ISD source associations and direct Parent_Service→Child_Service relationships.

**Enterprise Capability inventory and Main→Enterprise mappings are immutable and OUT OF SCOPE.** No Canonical API matching yet. This task links **Qiwa services**, not claims about all 2,036 APIC Canonical APIs.

## Input preflight — cheap and mandatory
1. In the Codex workspace, locate the exact `neo4j/csv/Qiwa_Modules_Services.csv` (the file was not accessible via GitHub Contents at that path). Read its **header + a few representative rows only** to identify actual columns for Module, Parent_Service, Child_Service, Type and service identifiers. Do not guess schema or normalize names blindly. If absent or unsuitable, STOP with `BLOCKED_SOURCE_CSV`, concrete missing fields and NO fabricated output.
2. Read **only** these existing generated indexes plus necessary index metadata: `indexes/phase6/task019/019e_final/main_icd_links.csv`, `main_isd_links.csv`, `main_capabilities.csv`, and recovery effective source-to-Service/ICD/ISD metadata needed to join; `019f/main_enterprise_links.csv` may be read **only for an immutability/lineage check**, NEVER for modifying Enterprise mappings. Do NOT read raw ICD/ISD bodies, parse schemas, reopen acquisition or rerun previous phases.

## Matching logic (one-hop, evidence first)
A. Select **Parent_Service rows with Type = API-HTTP**, using the CSV's real column semantics. Match each Qiwa Parent_Service to its existing module/service identity and ICD/ISD document associations. Prefer exact stable IDs and within-Module identity; name normalization may supply candidate review only, NEVER an automatic asserted match without corroboration. Support one-to-many document and Main links. Create direct relation `API_HTTP_PARENT_SERVICE --PROVIDES_MAIN_CAPABILITY--> Module Main` only where existing ICD/ISD evidence supports the association.

B. For each identified API-HTTP Parent_Service, find rows where **that same service is a Child_Service of another Parent_Service**. Resolve the *consumer Parent_Service's own Module and existing Main capability evidence* and create `API_HTTP_SERVICE --SUPPORTS_MAIN_CAPABILITY--> consumer Module Main`. Preserve concrete invoking parent/child row or relationship ID as evidence. **A child-of relationship alone does not prove a particular Main capability**; require that the consumer Parent_Service is actually linked via accepted source associations, not merely in the same Module. Do not conflate service provider ownership with consumers. Only **direct one-hop parent/child** traversal in this task; do not recursively propagate capabilities via chains or reverse ambiguous edges.

C. If an API-HTTP service is reused by multiple parents/Modules, retain each distinct supported context with original Module identity and Main ID. Deduplicate by stable service ID + Main ID + relationship type + consuming parent identity (where applicable), not by name alone.

D. Distinguish `NO_MATCHING_SOURCE_SERVICE`, `AMBIGUOUS_SERVICE_IDENTITY`, `PARENT_WITH_NO_MAIN_EVIDENCE`, `NO_CHILD_USAGE_EVIDENCED` (informational, not error), `SOURCE_DOCUMENT_UNRESOLVED`, and `SOURCE_EXCLUDED_OLD_IGNORE` where applicable. Do not infer retirement, usage beyond observed CSV, direct API execution, or 100% API coverage. Carry forward the five source gaps and 25 excluded source occurrences from 019-E/F where relevant, without reprocessing.

## Minimal outputs — task-owned
- `indexes/phase6/task019/019g/api_http_service_inventory.csv`: each distinct API-HTTP Parent_Service, Module, resolved source identity and direct coverage status.
- `indexes/phase6/task019/019g/api_main_capability_links.csv`: API service ID, Main ID, target Module, link type (`PROVIDES` or `SUPPORTS`), consuming Parent_Service ID (for SUPPORTS), source document/page/Service identity where relevant, exact CSV relationship pointer, evidence basis and certainty.
- `indexes/phase6/task019/019g/review_exceptions.csv`: exact unresolved or ambiguous service/relationship IDs, cause and mapping impact.
- `outputs/phase6/task019/019g/review_summary.md`: total API-HTTP parents, matched direct providers, supported child-use links, unmatched/ambiguous IDs **by name**, examples across Modules, and preserved Main/Enterprise counts.

## Acceptance and efficiency
- Check full eligible `API-HTTP Parent_Service` coverage: each is mapped or listed with exact reason, **not silently dropped**. Preserve existing Main IDs / 136 local Mains and existing 127 Enterprise candidates byte-for-byte; 019-E/019-F indexes untouched.
- Verify each SUPPORTS mapping has **two independently evidenced relationships**: API child-of consuming Parent AND consuming Parent→Main (via source ICD/ISD). If one is missing, exception, not a generated mapping.
- Reuse CSV parsing and existing joining utilities; no Neo4j server/import, new framework/cache/database, raw-document reads, 32-Module re-extraction, global APIC mapping, Kong, or full test suite. Focused checks only, bounded runtime and compact output. If the CSV lacks trustworthy relationship IDs, retain original row ordinal + raw stable identifiers as pointers.
- Commit minimum code + focused tests; add concise result to `codex/comm/HANSOFF.md` and **STOP at `EA_REVIEW_019G`**. No automatic follow-on task.
