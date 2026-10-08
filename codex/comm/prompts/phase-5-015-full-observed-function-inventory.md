# Phase 5 — Task 015 continuation: Full Observed Function Inventory

## Decision and scope (EA, 2026-10-08)
The Task 015 representative mock (15 operations, 14 APIs) is **APPROVED FOR ESTATE-WIDE ROLLOUT as a provisional, evidence-grounded extraction mechanism**. This is NOT certification of business-semantic accuracy or human approval of its 15 individual interpretations. Close mock gate; execute full Task 015 and STOP for architecture review before Task 016. Task 014 remains PASS/FROZEN and Phase 0–4 frozen.

**Confluence architecture note:** Enterprise Confluence reportedly contains extensive API explanations. It is a potential future enrichment/verification source, NOT a prerequisite for Task 015, NOT a license to infer unseen facts, and NOT currently retrieved or verified. Do not bulk crawl Confluence or install connectors. Record specific unresolved function cases that would benefit from a targeted Confluence document lookup later (candidate follow-up source = CONFLUENCE_POTENTIAL_UNVERIFIED), without assigning any Confluence-derived certainty or facts. No Confluence coverage assumptions.

## Objective and stopping boundary
Produce a complete **Observed Function Inventory** from all accepted Task 014 HTTP operation inventory records (baseline 2,414). Each operation gets exactly one output record containing:
- operation ID, canonical API ID, exact method/path, source and Task 014 provenance;
- provisional action + resource/object wording **only when evidence supports it**, otherwise null/not evidenced;
- interpretation classification and evidence strength/rationale, explicit independent source signals, source contradiction, confidence limitations and reviewer status (PENDING_REVIEW);
- relevant request and response structure/schema facts, backend configured facts separate from inherited candidate-only context, never proven runtime egress;
- precise missing/evidence gap IDs and downstream effect.
Retain 36 registry-only APIs and 5 source-backed no-supported-path APIs as API-level gap records, not invented operations. Reconcile all API and operation counts against frozen Task 014 manifests. The 113 unresolved Product-location occurrences remain unresolved.

This task answers ONLY: **what does this APIC HTTP operation appear to do?** Do not confirm logical-function equivalence, duplication, logical API grouping, domains, capabilities, retirement or Kong mapping. Do not invent meaning from API name, method or same backend alone.

## Approved interpretation contract
- Reuse `tests/evidence/task-015/mock/observed_function_contract.md` and accepted mock implementation as baseline; only additive changes for scaling, deterministic correctness or clear defects in active (nonfrozen) Task 015.
- Keep statuses EXPLICITLY_DESCRIBED, INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS, AMBIGUOUS_NEEDS_REVIEW, INSUFFICIENT_EVIDENCE; record UNSUPPORTED_PROTOCOL and REGISTRY_ONLY_NO_OPERATIONS at API level.
- An explicit source description may be inaccurate or contradict operationId/path. Mark contradictory operations ambiguous and queue rather than resolve via a guessed winner. Well-described is not automatically architect-approved.
- HTTP verb alone is insufficient; method/path + independent corroborating request/response/parameter/schema evidence can justify a bounded, PROVISIONAL interpretation. Backend identity alone cannot establish business action.
- Keep reviewer status PENDING_REVIEW by default; full rollout authorization does NOT mark records APPROVED.
- Clearly distinguish technical/security/proxy actions from observed business actions where evidenced. Do not force business interpretation.
- Different canonical API IDs and even identical candidate wording stay distinct.
- In v2 pairs including searchseasonalvisarequests versus searchseasonalvisarequests-v2, preserve actual request+response schema differences and configured backend certainty; do not declare a duplicate or infer replacement/version precedence.

## Downstream gap policy approved for rollout
The mock's 11 gap categories and impact taxonomy are **accepted as a tracking baseline, not irreversible architecture truth**. Scope every gate to affected entity and intended conclusion:
- NON_BLOCKING: missing metadata alone when other independent evidence makes a bounded description possible.
- LOCAL_REVIEW_REQUIRED: need human review, targeted evidence or source validation for specific APIs/operations.
- DOWNSTREAM_BLOCKER: blocks only the unsupported specific operation/function comparison, grouping or domain/capability conclusion; NEVER globally blocks all of Tasks 015–019. Record exact affected IDs, reason, downstream task and recovery trigger.
- Never classify all 60 structural candidate pairs as functional duplicates; Task 016 resolves candidate equivalence based on richer evidence.
- Carry forward the 36 registry-only, 5 no-supported-HTTP-path, 113 unresolved Product-location, native GraphQL/WSDL semantics and API_SHARED backend candidate-only limitations with explicit provenance.
- Existing known Phase 0 fixture-packaging setup errors must be reported separately; do not modify frozen fixtures or declare whole suite green.

## Efficient deterministic full pipeline
- Start with frozen CodeGraph/accepted compact indexes; read Task 014 API and operation inventory and persistent cache. Use targeted immutable raw Swagger/assembly files only for unresolved bounded schema/action evidence.
- Reuse the versioned deterministic Task 015 mock cache/logic and extend it safely to an incremental whole-estate cache keyed by stable operation/source/evidence/dependency and interpretation-rule version. Atomic writes, selective invalidation, rerunnable/byte deterministic cold/warm parity.
- Avoid full-corpus LLM prompting or treating token count as the quality metric; report whether any LLM was used and measured tokens if available. No Vector DB, new Blackboard, multi-agent or orchestration framework.
- Avoid expensive all-pairs comparison and do not implement Task 016 within Task 015.
- If the full rollout produces many AMBIGUOUS/INSUFFICIENT results, report them honestly and prioritize targeted evidence enrichment; do not weaken quality gates to inflate coverage.

## Outputs and acceptance evidence
Generate ignored local complete indexes/cache/manifest under indexes/ or outputs/, e.g. `indexes/observed_function_inventory.jsonl` one row per accepted HTTP operation and `indexes/task015_full_gap_impact_register.jsonl` plus review queue.
Commit safe compact evidence under `tests/evidence/task-015/full-extraction/`:
1. `observed_function_contract_full.md` with versioning, status/evidence rules, and mock compatibility;
2. `coverage_and_interpretation_distribution.json`: total reconciled, API counts, high/medium/low/none, interpretation statuses and source coverage;
3. `gap_impact_and_downstream_gates.json`: affected entity counts deduplicated where possible, categories, scope-specific blockers, mitigations, number requiring review; do not sum overlapping gap category counts as unique operations;
4. `representative_findings.jsonl`: bounded samples across interpreted, inferred, ambiguous, insufficient, technical, missing-metadata and v2 cases with exact provenance;
5. `review_queue_sample.jsonl` plus count/distribution;
6. `cache_and_replay_metrics.json`;
7. `build_manifest.json` with input/output fingerprints;
8. `commands_and_results.txt`.
Do not commit secrets, raw endpoint hosts, raw complete inventories/cache or sensitive schema values.

Tests: exact 2,414 operation count reconciled (or explain divergence from accepted source), stable unique Observed Function IDs, 2,036 API identity scope, source fidelity, proper candidate backend certainty, no fabricated protocol-native operations, no invented function where evidence absent, deterministic replay + cold/warm parity + selective cache invalidation + redaction + frozen asset integrity. Run focused tests and repository suite, correctly report known five setup errors.

## Handoff & hard stop
Update `codex/comm/HANSOFF.md` with PASS / FIX_REQUIRED / HOLD_FOR_ARCHITECTURE_REVIEW, all counts, limitations, evidence quality distribution, downstream scoped blocking cases and explicit next-step questions, commit and push. **STOP after full Task 015 only.** No Task 016 until Integration Architect / EA reviews full output and records a decision. Never reopen Task 014 simply because more evidence becomes available; additive downstream enrichment is preferred.
