# Phase 5 — Task 017: Logical API Formation — representative mock first

## Enterprise Architect decision (2026-10-11)
EA accepts Task 016 (full inventory + focused semantic refinement) as a **provisional candidate-discovery and false-positive-control baseline**, sufficient to proceed to Task 017. This does NOT approve the 470 potential-same pairs as equivalent business behavior or duplicates, and does NOT certify backend operation semantics. The user explicitly elects to progress rather than repeatedly rework prior phases.

Frozen: Phases 0–4; Task 014 (2,036 canonical APIs / 2,414 HTTP operations); Task 015 (provisional observed functions); Task 016 outputs (1,170 candidate pairs, refinement: 470 potential-same, 120 conflicting, 573 insufficient, 6 structural-only, 1 supported different action; 1,481 unpaired operations). Never change frozen source/identities/evidence absent reproducible defect.

**Authorization here is Task 017 REPRESENTATIVE MOCK only**; stop for architect review before full-estate logical API formation.

## Goal and boundaries
Design a **candidate logical API formation method**: identify coherent business-facing API boundaries made of logically related operations, preserving individual business actions, business objects, consumers, exposure contracts, security context, versions, and current API provenance. A Logical API is a TO-BE *conceptual grouping proposal*, NOT an APIC API artifact, not automatically an APIC Product, and not automatically a Kong Service/Route/Product.

Prioritize discovering enterprise-level opportunities hidden by inconsistent naming or developer-created parallel forms. **Do not treat matching Swagger shapes, backend system, or version family as proof of redundant functions.** Approve/Reject/Cancel/Activate/Deactivate remain distinct logical OPERATIONS even when they belong in the same logical API around a resource; related is not duplicate. Potential same-function pair may have different contracts or consumer/version purposes; preserve the variants and associated risks, do not silently collapse them.

Do not assign Business Domains (Task 018) or Capabilities (Task 019), approve duplicates/retirement, design Kong topology or migrate anything. Do not use live Production assumptions from STAGING/sandbox evidence. Missing CI/CD/release traceability and production usage map are cross-cutting limitations to future consolidation/retirement decisions, not reasons to block conceptual group formation.

## Critical distinction: two independent relation types
1. **FUNCTIONAL_EQUIVALENCE_CANDIDATE**: multiple operations possibly achieve the same Action + Object + Behavioral Intent, still unverified. Never auto-collapse their IDs.
2. **LOGICAL_API_COHESION**: distinct operations that belong to a coherent business-facing resource/workflow/API boundary (e.g. approve/reject/cancel are different actions on a contract and might belong to one logical Contract API). This must be justified by actual resource/context evidence, not solely a shared backend or word token.

A group may contain multiple distinct functions plus competing exposure/contract variants. Store every grouping assertion with independent evidence and REVIEW_REQUIRED or PROVISIONAL status, and its exact membership/provenance. Do not turn pairwise similarity into transitive equivalence: A~B and B~C do not prove A~C. Unresolved members must not contaminate group certainty.

## Evidence-led formation
Reuse frozen Task 014/015/016 indexes, version/variant context, endpoint and assembly evidence, accepted Product/Plan/Subscription relationship indexes and CodeGraph. Start index-first with bounded candidate groups; only targeted raw reads when material. Do not rebuild these layers or introduce Vector DB, all-pairs search, Blackboard or multi-agent orchestrator.

For each proposed logical API:
- Suggested stable conceptual ID and **business-neutral resource/workflow label** (provisional, never domain/capability assignment).
- List member accepted canonical API IDs and individual Task 014 operation IDs, Task 015 observed IDs, Task 016 comparison/refinement refs, source pointers/fingerprints. Explicitly mark distinct operations, candidate alternate implementations, unverified relationships, singleton cases.
- Record intended consumer-facing logical operations as **distinct action-object-intent** with provenance; neither merge differently behaving actions nor manufacture missing operations.
- Context from exact/normalized/base endpoints, method, request/response structural differences, configured backend route/operation certainty, transformation/conditional routing, Product/Plan/Subscription and version/variant exposure. Preserve differences and do not infer production calls, flag activation or retirement.
- Compare possible grouping boundaries and alternatives, including reasons NOT to group, risk of shared generic backend/schema, over-broad resource group, integration façade vs business API, and cross-API consumer concerns.
- Separate provisional functional equivalence, grouping cohesion, contract compatibility and migration safety into independent fields. Never claim substitution or shared implementation without supporting operation-level evidence.
- Suggested status: COHESIVE_LOGICAL_API_CANDIDATE, PARTIAL_OR_VARIANT_BOUNDARY_REVIEW, INSUFFICIENT_EVIDENCE_TO_FORM, or SEPARATE_LOGICAL_APIS_SUPPORTED. These are PROPOSALS only; architect approval remains pending.

## Representative mock sample
Select ~8–12 bounded, **diverse** examples with traceable sources:
- same object / different supported actions (approve, reject, cancel or similar), demonstrate grouping without collapsing distinct functions;
- different names and paths, possible same business intent (a functional-overlap hypothesis, not duplicate approval);
- versioned variants including seasonal visa v1/v2 with material schemas, consumers/product/plan exposure as available;
- employment status enquiry / querycenter with insufficient backend semantic evidence;
- multiple operations from one canonical API, and one logical API possibly represented by several canonical APIs;
- shared backend or response wrapper BUT different functions (negative grouping control);
- at least one technical/security endpoint and one ambiguity/insufficient-evidence control.
If a category is not evidenced, record NOT_EVIDENCED_IN_SAMPLE; never manufacture examples. Explicitly compare a **false positive** case where shared schemas or path would make an incoherent Logical API.

## Mock acceptance and evidence
Produce compact artifacts under `tests/evidence/task-017/mock/`, with complete local ignored indexes only if required:
- `logical_api_formation_contract.md` (identity, cohesion vs equivalence, membership graph, stability and status model);
- `representative_boundary_cases.jsonl` (grounded 8–12 cases, member operations and provenance, positive/negative reasons, context and candidate dispositions);
- `grouping_false_positive_controls.md` (approve/reject/cancel distinct, generic wrappers, same backend, transitivity, version differences);
- `coverage_and_nonformation_report.json` (sample counts, identities, cases that cannot be grouped; no claim of full coverage);
- `review_queue.jsonl` (bounded decisive architecture questions, targeted missing evidence, no mandatory review of all 1,170 Task 016 candidates);
- `commands_and_results.txt` and `build_manifest.json`.
Use deterministic generation where feasible, safe redaction, source pointer traceability, scope-specific uncertainty and regression. Test frozen integrity, stable source/member IDs, distinct business actions not collapsed, no transitive pair-grouping fallacy, unresolved consumer/backend evidence not promoted, no Product-as-Logical-API default, and no domain/capability/Kong/retirement decisions. Report the known Phase 0 fixture setup errors separately if present.

## Stop
Update `codex/comm/HANSOFF.md`, commit/push, STOP for EA review. **Do not perform Task 017 full-estate formation or Tasks 018–019**, API rationalization, Kong TO-BE, or migration without authorization.
