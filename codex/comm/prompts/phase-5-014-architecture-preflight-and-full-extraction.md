# Phase 5 — Task 014 Continuation: Architecture Preflight → Full Semantic Inventory

## Authority / Inputs
Read `AGENTS.md`, `codex/comm/CURRENT_TASKS.md`, latest `codex/comm/HANSOFF.md`, original Task 014 prompt, `tests/evidence/task-014/semantic_inventory_contract.md`, and Task 014 sample/evidence. Latest sample status: `HOLD_FOR_ARCHITECTURE_REVIEW`; 6 APIs / 35 operations; 9/9 sample categories. This prompt is an explicit **continuation of Task 014 only**, not Task 015.

The Enterprise Architect reviewed four decisions:
1. **APPROVED** — Semantic Inventory Contract as the factual baseline. Keep canonical API identity joins, operation *inventory records* (not graph nodes), exact provenance, missing states, separated future hypotheses/architecture decisions.
2. **REVISION_REQUIRED** — Backend Evidence representation. The prior API_SHARED/OPERATION_SCOPED contract is **not finally approved as a complete model**. Keep already accepted Task 011 scope facts intact; investigate how to represent inherited/shared/conditional/action-scoped context without either losing useful evidence or asserting unproven operation egress.
3. **REVISION_REQUIRED** — Duplicate YAML Representations. The prior first-selected-authoritative-YAML-only approach is **not finally approved as sufficient**. Investigate duplicate representations and conflict/variant handling without conflating exact file duplicates, same canonical API, and genuine semantic variants.
4. **APPROVED** — Persistent Incremental Semantic Cache. Implement source-hash/extractor-version based incremental materialization for full extraction, without changing canonical identity or frozen indices.

## Gate A decisions — APPROVED by Enterprise Architect (2026-10-08; supersede preflight pending text)
- **Decision 1: Option A approved.** Maintain a strict two-layer Backend Attribution model. Accepted Task 011 CONFIGURED_API_SHARED and EVIDENCED_OPERATION_SCOPED records are facts about configuration; separate CANDIDATE_INHERITED_CONTEXT per operation when justified, always CANDIDATE_ONLY with provenance, never proven operation egress or observed runtime. Preserve conditional/policy context, multiple targets, exact operation-switch method/path, and UNRESOLVED_ROUTING. One operation versus many never upgrades certainty.
- **Decision 2: Option A approved.** One canonical API envelope retaining source occurrence/variant provenance. Reuse one payload for byte-identical representations; preserve different-hash structural equivalence evidence; conflicting semantic representations remain separate with CONFLICT_REQUIRES_ARCHITECTURE_REVIEW and per-variant operation identity. Never merge conflicting operations or change frozen Phase 2 IDs.
- **APPROVED:** baseline factual inventory contract and versioned incremental cache.
- **AUTHORIZED:** Gate B full extraction under constraints below. Gate A is complete; its earlier pending approval/instructions are historical.
- **Architect's specific observation:** for a likely v2 overlap (e.g. searchseasonalvisarequests vs searchseasonalvisarequests-v2), compare both **request and response** contracts **and backend** in addition to path/method. This is evidence for structural-overlap candidacy, not automatic functional duplication.
- The architect does NOT want a Blackboard initiative: continue reuse of current graph/indices and cache only; no new Blackboard, Multi-Agent system, orchestration framework, or architectural workstream.

## Mandatory operating principle
Graph-first and index-first retrieval; raw source is authoritative. Route canonical API identities and relationship/backend provenance through frozen CodeGraph + compact accepted indexes, then semantic cache, then *targeted* authoritative source parsing when semantic content is not cached or valid. **Graph reachability does not prove runtime usage or operation egress.**
Never re-run Phase 0–4 discovery/identity resolution, never overwrite frozen structural/dependency graph, do not reparse all raw staging for discovery, and never interpret name/endpoint similarity as logical duplication. Efficient full extraction may parse each unique supported source document once on cache miss; this is not a blanket prohibition on reading the needed sources.

## Gate A — Architecture preflight (COMPLETED; historical record, do NOT rerun)
Carry out a focused evidence-backed evaluation for BOTH pending revisions, producing safe review artifacts and recommendations. Do **not** silently select a final semantic routing/variant contract or start estate-wide extraction until the Enterprise Architect explicitly approves the two revised designs.

### A1 Backend evidence: assess with actual operation and assembly examples
- Inspect compact Task 011/012/013 evidence and selected, relevant APIC assembly YAML; distinguish **API_SHARED configuration context**, **operation-scoped explicit invocation evidence**, action/policy scope where demonstrable, and conditional routing where supported.
- Evaluate whether an API_SHARED invocation may be inherited by several operations as *potential context* without being misrepresented as observed or proven egress. Present alternative record representations and exact provenance, certainty, scope, and limits for each.
- Explicitly compare APIs with one operation versus multiple operations. Operation count does not prove that a shared backend is actual egress. Show possible inherited context separately from exact evidenced per-operation invocation.
- Test cases: simple shared invocation; explicitly operation-specific invocation; mixed/shared and operation-specific patterns if found; conditional/branching or absent/equivocal policy evidence if found; APIs with multiple backend targets. If a pattern is not demonstrable, mark `NOT_EVIDENCED_IN_SAMPLE`.
- Distinguish: `CONFIGURED_API_SHARED`, `EVIDENCED_OPERATION_SCOPED`, `CANDIDATE_INHERITED_CONTEXT`, `UNRESOLVED_ROUTING`, or recommend another explicit taxonomy **as a proposal only**, without unapproved semantic claims. Do not change accepted Task 011 facts.
- Provide a compact side-by-side example showing what the old Task 014 contract loses or represents conservatively vs a revised contract, including risks of overclaiming.
- State clearly which backend fields are *facts* and which are *candidate architectural associations*, and how exact operation method/path anchors work.
- **Approval required:** Enterprise Architect decides final attribution/certainty model; do not assume that the user wanted API_SHARED promoted to proven operation egress.

### A2 Duplicate and variant YAML: assess with actual source groups
- Use canonical identity occurrences, file SHA, accepted root source paths, and Phase 0 exact-hash duplicate evidence to profile:
  1. byte-identical duplicate files;
  2. distinct files with semantically equivalent operation contracts;
  3. different accepted source representations under the same canonical API ID with differences (paths/methods/parameters/schemas/descriptions/backend assembly, where available);
  4. source-path conflicts or competing authoritative representations.
- Use a targeted deterministic mock with real examples for available categories. Compare normalized **structural semantic fingerprints** without expanding every schema, and retain all occurrence IDs/source SHA/provenance. Same API ID does not establish semantic equivalence.
- Report counts from a cheap index-only preflight where feasible; do not claim estate-wide semantic conflict counts until compared.
- Present recommended policy for canonical output, source variant retention, per-variant operation provenance/identity, differing methods/paths, and `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW`. Avoid silently picking lexically first YAML as semantic truth when accepted representations conflict.
- **Approval required:** Enterprise Architect decides final representation/merge/conflict treatment. Do not redefine frozen Phase 2 canonical identities.

### A3 Cross-canonical similarity feasibility (not confirmed duplicates)
The architect wants to find APIs with **different names and canonical IDs** whose behavior may overlap. This is NOT equivalent to same-canonical YAML variant detection or Phase 0 exact file duplicates.
- Test a few evidence-backed pairs for deterministic structural similarity from method/path shapes, parameter/request/response schema references, and backend target/path overlap. Names alone and shared backends alone never prove duplication.
- Preserve two independent canonical API IDs, exact source provenance, matching and differing signals, confidence limitations and explicit status POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION.
- Report false-positive and false-negative risks (generic CRUD, shared middleware, channels, version differences, dynamic routing).
- Do not assert logical-functional duplication, merge APIs or implement Tasks 015–016; those tasks will validate observed and logical functions.

### Gate A deliverables (committed)
Create under `tests/evidence/task-014/architecture-preflight/`:
- `backend_evidence_options.md` (actual safe anonymized evidence, recommended choices and tradeoffs);
- `backend_evidence_samples.jsonl`;
- `yaml_variants_options.md` (exact vs equivalent vs conflicting examples);
- `yaml_variants_samples.jsonl`;
- `architecture_decisions_pending.md` (two *explicit* decisions with options, recommended path, risks and downstream implications);
- `cross_canonical_similarity_feasibility.md` with safe candidate examples or precise NOT_EVIDENCED rationale;
- `preflight_commands_and_results.txt`.
Keep generated raw/cache indexes only under ignored `indexes/` or `outputs/`; commit only safe, compact review evidence.
Run focused tests for preflight logic, deterministic replay, frozen asset integrity, and redaction. Update `codex/comm/HANSOFF.md` with gate findings and `HOLD_FOR_ARCHITECTURE_REVIEW`; commit/push and **STOP**. Await user approval via updated task instructions; do not resume autonomously.

## Gate B — Full extraction (NOW AUTHORIZED; decisions A+A approved)
Execute under the approved A+A policies recorded above and status `READY_FOR_CODEX_FULL_EXTRACTION`:

1. Implement the revised, approved semantic inventory contract additively, with migration/compatibility notes for the six-API mock.
2. Build durable **incremental caching** keyed to canonical API identity, accepted source SHA-256(s) / occurrence-variant identity, extraction schema/parser version, and any external relevant accepted-index fingerprint needed for metadata/relationship enrichment. Do not key only by API ID because Product/Plan/backend evidence may change without source YAML change. Cache facts separately from relationship enrichment if that reduces invalidation; document granularity.
3. Cache behavior: `HIT`, `MISS`, `INVALIDATED_SOURCE_CHANGE`, `INVALIDATED_EXTRACTOR_CHANGE`, `INVALIDATED_DEPENDENCY_CHANGE`, `REGISTRY_ONLY`, `UNSUPPORTED_FORMAT` with deterministic reason (extend if necessary); atomic writes/no corruption; schema-versioned record payload; no secrets; validate stale/missing/partial cache and recompute only affected records. Demonstrate warm run, cold run and one-file change fixture; no mutation of immutable `staging/`.
4. Enumerate **all 2,036 accepted canonical APIs** from frozen canonical identities: expected 2,000 source-backed and 36 registry-only as the last validated baseline; if live accepted indexes differ, report and reconcile rather than hardcoding. Never silently drop unsupported/registry-only identities. Inventory cardinality must reconcile to live accepted canonical count.
5. Extract supported Swagger 2/OpenAPI 3 HTTP operations deterministically and per approved variant contract. Preserve exact methods/paths, safe descriptions, parameter/request/response/schema refs, provenance, missing reasons, AS-IS Product/Plan edges, unresolved 113 Product-location occurrences, and backend scope/certainty per approved model. Graph/index lookup first; targeted parse source on cache miss.
6. Measure format distribution and parser coverage (Swagger 2, OpenAPI 3, registry-only, GraphQL, SOAP/WSDL, AsyncAPI, other specific parse states). Do not invent non-HTTP operations or treat unsupported protocol coverage as zero operations by business conclusion. Do not implement protocol-specific parsers without an explicit architecture instruction; report exact unsupported counts.
7. **v2 and cross-canonical candidate comparison — request + response + backend are mandatory evidence dimensions.** For each candidate pair (including v2 variants), compare at **operation level**: exact HTTP method/path and normalized shape; parameters with location/type/required; request content type(s), body presence, schema refs and safe deterministic local schema shapes (including referenced schema structure when securely, deterministically resolvable without uncontrolled dereference); response status codes, content types, response schema refs/shape; and backend-target ID/path, configuration scope, assembly/transform/conditional differences where actually evidenced. Also preserve different auth/exposure/channel and version distinctions when available. Distinguish EQUAL, DIFFERENT, NOT_COMPARABLE, MISSING_EVIDENCE for each dimension. Never treat merely same schema reference label as schema equality, or a shared backend as proven same operation egress. Avoid expensive pairwise full-corpus comparisons: use indexed blocking/candidate retrieval and bounded deterministic scoring/explanations; candidates must be independently justified, not name-only. **Commit a focused safe side-by-side comparison of the actual searchseasonalvisarequests versus searchseasonalvisarequests-v2 pair**, if both sources available, reporting requests, responses, backend, operations, configuration scope and gaps; do not invent findings or display secrets. Do not assert semantic duplication.
8. Build a separate, additive structural-overlap CANDIDATE index for pairs of **distinct canonical API IDs** when multiple independent evidence signals justify it. Include differences, provenance and status POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION. This is not a confirmed duplicate index and is not the same as same-ID source conflict reporting. Do not make name-only or backend-only duplicate claims.
9. Generate ignored local indexes in `indexes/` (full semantic API/operation inventories and cache manifest). Commit compact safe aggregation, gap taxonomy, conflict/variant cases, cache effectiveness, test evidence, build hashes and commands under `tests/evidence/task-014/full-extraction/`.
10. Validation: canonical identity coverage 100% including missing-state records; unique deterministic operation IDs (respect approved source-variant contract); no fabricated methods, duplicate operations or inferred runtime route; backend relation certainty preserved; exact and unresolved Product/Plan evidence retained; stable repeated output hashes; no credentials or raw sensitive endpoints in committed artifacts; no staging/frozen index mutation. Verify cold/warm output identity and report cache hit/miss statistics.
11. Run targeted tests and repository suite; report unrelated known fixture setup errors separately, without asserting entire suite PASS if any errors remain.
12. Update `codex/comm/HANSOFF.md` with `PASS`, `FIX_REQUIRED`, or `HOLD_FOR_ARCHITECTURE_REVIEW`, explicit record counts, coverage, unresolved exceptions, and approval questions. **STOP after Task 014 full extraction, tests, evidence, and commit/push.** No Task 015, no domain/capability assignment, no functional similarity clustering, no rationalization, no Kong design.

## Unchanged architectural constraints
- Canonical API ID is the join anchor; operation remains an inventory record, not CodeGraph node.
- Raw `staging/` is immutable; all Phase 0–4 frozen assets byte unchanged.
- No change to Task 011 evidence or Task 013 backend graph based on interpretive hypotheses.
- Accepted Product/Plan relationships only; retain 113 unresolved Product-location occurrences as unresolved.
- Missing operation description / summary / operationId is a documented source gap, **not an automatic failure** or license to infer business functionality.
- Task 018 Business Domain classification before Task 019 Capability Mapping, and Task 018 requires its own explicit mock acceptance. This prompt does not authorize either.
- Codex discovers → Integration Architect validates → Enterprise Architect decides.

## Token efficiency via existing indexes and cache only
- Reuse existing CodeGraph, compact accepted indexes, Task 014 inventory and Codex handoffs as inputs. No Blackboard design/project, multi-agent framework, orchestrator, broker or new graph database.
- Deterministic resumable workflow: INDEX_LOOKUP -> CACHE_CHECK -> TARGETED_PARSE_IF_MISS -> VALIDATE -> MATERIALIZE -> REPORT. Produce compact pointer-based evidence projections, never bulk graph/YAML dumps into model context.
- Implement versioned persistent cache with precise dependency invalidation, distinguishing source-derived facts from relationship/backend enrichments. Use atomic writes and prove cold/warm parity.
- Task 014 extraction is programmatic, not an LLM semantic inference task; do not run full corpus through an LLM. Cache savings should be measured, not advertised as zero total future reasoning tokens.
- Keep future semantic decision cache separate from factual extraction cache; do not implement unapproved Tasks 015–019.
