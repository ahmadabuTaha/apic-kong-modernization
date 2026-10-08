# Phase 5 — Task 014: Semantic Inventory & Operation Extraction

## Architectural authority and scope
Enterprise Architect direction, 2026-10-08:
- Phase 5 order is 014 Semantic Inventory & Operation Extraction; 015 Observed Function Discovery; 016 Logical Function Normalization; 017 Logical API Formation; 018 Business Domain Classification; 019 Business Capability Mapping.
- **Domain mapping precedes capability mapping.** A domain association by itself must not be misrepresented as a business capability.
- Task 018 **must begin with a mock test and architect acceptance before estate-wide domain mapping.** Task 014 must not preempt this gate.
- Future Task 018 must maintain reviewable JSON mapping canonical APIs to one or more domain candidates, with evidence, uncertainty, and architect approval status. Schema and domain taxonomy are not being finalized in Task 014.
- Codex discovers -> Integration Architect validates -> Enterprise Architect decides.

## Preconditions
Read AGENTS.md, CURRENT_TASKS.md, HANSOFF.md and frozen Phase 0–4 reports/evidence before implementation. Treat Task 013 PASS as the Phase 4 completion checkpoint; do not reopen the frozen layers. If essential upstream index shape differs from expectations, report exact facts instead of guessing.

## Objective
Create a deterministic, traceable, compact **semantic source inventory** of canonical APIs and explicitly evidenced API operations to support later semantic tasks. **Do not infer observed functions or logical APIs yet.**

This task is deliberately staged with an architectural validation gate. Implement contract plus representative mock extraction; **do not run estate-wide rollout before review**.

## Work package A — Semantic Inventory Contract
Inspect accepted canonical API identity/index and compact graph, Product/Plan and backend dependency indices, and source evidence handling. Propose and implement an additive inventory record contract, documenting:
- canonical API ID as primary join key; source object/file and exact JSON/YAML pointer;
- recorded API title, description, version, protocol and available descriptive metadata;
- operation-level method, exact path or operation selector, operationId, summary and description **only when evidenced**, with stable deterministic operation record ID (not a CodeGraph node);
- parameter, request, response, schema references as *references/summary* rather than blindly expanding large schemas;
- explicit path-level/operation-level versus API-shared routing/backend evidence, with clear status and exact upstream observation references;
- AS-IS Product/Plan relationships using established canonical relations; preserve 113 unresolved Product-location API occurrences rather than silently attaching;
- source provenance, missing-field reason/status, evidence confidence/source type, resolution status;
- separate factual extracted data from future hypotheses/architectural judgments.
Do not fabricate an Operation node or mutate the frozen CodeGraph. An operation is a **semantic inventory record**, not yet an approved canonical graph entity.
Document how mixed API definitions, duplicate exact source files, registry-only identities, and multiple representations are handled. Explicitly state parser coverage and unsupported syntax.
Do not infer runtime usage, logical function, domain, business capability, ownership, duplication, retirement, Kong products, or backend family from names.

## Work package B — Deterministic sample extraction
Select a **small representative, reproducible sample** using stable canonical identities, not hand-picked success-only names. Include at least:
1. explicit multi-operation REST API;
2. single-operation API;
3. API with unresolved/missing operation metadata or description;
4. API with API_SHARED backend scope;
5. API with OPERATION_SCOPED backend evidence if present;
6. API associated to AS-IS Product/Plan if evidenced;
7. registry-only canonical API if representation permits;
8. API with multiple backend targets if present.
One API may satisfy multiple classes. Report selection criteria, sample coverage and any cases impossible to sample. Use compact accepted indexes first; only read targeted raw source for missing semantics/verification. Record exact source references.

Produce deterministic **local ignored** sample indexes in `indexes/` and human-reviewable, safe, compact **committed** sample evidence under `tests/evidence/task-014/`. Recommended names:
- `indexes/semantic_api_inventory_sample.jsonl`
- `indexes/semantic_operation_inventory_sample.jsonl`
- `tests/evidence/task-014/semantic_inventory_contract.md`
- `tests/evidence/task-014/sample_selection.json`
- `tests/evidence/task-014/api_sample_review.jsonl`
- `tests/evidence/task-014/operation_sample_review.jsonl`
- `tests/evidence/task-014/coverage_and_gaps.json`
- `tests/evidence/task-014/commands_and_results.txt`
Adjust naming only if needed for existing conventions and document it.

## Validation / acceptance
- Each sampled operation maps to an accepted canonical API ID and explicit source pointer.
- Unique deterministic operation IDs across repeated runs; no accidental collapse of method/path or distinct variants.
- API_SHARED backend evidence must not be falsely assigned to every operation as proven operation egress.
- Metadata absences, unresolved links, and source conflicts have explicit states; never manufacture values.
- Contract clearly separates extraction fact from later Observed Function, Logical Function, Logical API, Domain, Capability.
- Sensitive URI hosts, credentials, security secrets and configuration values are not exposed in committed evidence.
- Phase 0–4 frozen structural and dependency indexes and `staging/` are unchanged.
- Unit tests cover duplicates, missing descriptions, multi-operation path/method distinctions, registry-only identities, and deterministic outputs.
- Report targeted tests, whole-suite status including known preexisting fixture setup errors, exact file hashes where practical.

## Strict exclusions
No Task 015–019 implementation, no estate-wide semantic classification, no domain/capability tagging, no domain JSON mapping yet, no logical API grouping, no duplicate/retirement decisions, no productization redesign, no Kong configuration or migration waves, no new graph node/edge taxonomy. If an enrichment to frozen components seems necessary, stop and report a focused defect with evidence, rather than modifying them.

## Handoff and stop gate
Update `codex/comm/HANSOFF.md` with exact implementation paths, sample counts, extraction gap taxonomy, contract decisions requiring architect approval, test results and PASS / FIX_REQUIRED / HOLD_FOR_ARCHITECTURE_REVIEW.
**Stop after contract + deterministic representative sample + tests + handoff + commit/push.**
The next step requires Integration Architect / Enterprise Architect review of Task 014 sample/contract before any full-corpus extraction or Task 015. Do not treat completing this mock as automatic permission for Task 018 domain mock.
