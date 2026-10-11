# Phase 5 — Task 016: Focused Semantic Refinement (EA Review Finding)

## Decision / why this exists
The Enterprise Architect reviewed Task 016 full output and identified a material **classification risk**: API endpoints can have identical request/response structures and similar paths or backend systems while implementing different BUSINESS ACTIONS (approve vs reject vs cancel, activate vs deactivate, create vs retrieve). Conversely, differently named/exposed APIs can implement the same business behavior. The modernization objective is to detect **potential redundant implementations of the same business function hidden by inconsistent naming/form**, NOT to count structurally similar operations as functional duplicates.

**Execute this targeted refinement of the existing Task 016 candidate inventory, not a new estate extraction.** Latest Task 016 full: 2,414 operations; 1,170 proposed pairs; 405 possible-same; 637 conflicting; 125 insufficient; 3 clearly different; 717 structurally equal compared shape pairs. All remain unapproved. Prior phases and Tasks 014/015 are FROZEN; do not alter them. Task 016 full evidence is a baseline pending review, not approved semantic equivalence. STAGING/sandbox is not production usage evidence.

## Functional equivalence test (mandatory)
Distinguish at least:
1. **STRUCTURAL_SIMILARITY_ONLY** — matching schemas/method/path/backend-system or shared boilerplate without evidence of same behavior;
2. **DIFFERENT_BUSINESS_ACTION_SUPPORTED** — evidence shows differing actions/behavior on the same object (e.g. approve/reject/cancel). This is NOT a duplicate candidate even if request/response hashes match;
3. **POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE** — supported matching apparent business action AND object/intent, perhaps different API naming, paths, wrappers, versions, or contracts, while behavioral identity remains pending;
4. **SEMANTIC_EVIDENCE_INSUFFICIENT** or **CONFLICTING_SEMANTICS_REVIEW** — operation-level behavior cannot be confidently established.

Do not treat these as architectural approval, duplicate verdict, retirement, replacement or merge decision. Preserve prior pair statuses and provenance; output an **additive refinement verdict and supporting evidence** without silently rewriting frozen/past reports. **Logical Function Identity hypothesis = Business Action + Business Object + Behavioral Semantics**; endpoint/schema/backend/subscription similarities support candidate *retrieval*, never prove identity.

## Focused evidence retrieval
Consume Task 016 full local candidate-pair/group indexes, Task 015 observed functions, Task 014 semantic operation inventory, CodeGraph and accepted API/Product/Plan/Subscription relationship indexes. Retrieve raw staging sources **only for focused verification**, and do not alter staging. First concentrate on:
- candidates with equal request/response shapes but different business verbs (approve, reject, cancel, terminate, activate, deactivate, update, validate, search/retrieve);
- pairs whose only shared signals are schema, backend target/system, HTTP path shape or generic wording;
- cases where names/paths differ but inferred Business Action + Object and targeted assembly/backend operation semantics may match;
- version-family and shared-Product/Subscription cases as context, never a duplication shortcut;
- the actual v1/v2 seasonal visa case, employment-status comparison and a selection of negative controls;
- cases with no support for resolving backend operation.

**Backend operation distinction:** Compare not only backend system/host or backend target identity, but operation-specific HTTP method/path, dispatch discriminator, mapping, assembly invoke, URL rewrite, conditional branch, GatewayScript behavior, and backend operation when evidence supports resolution. Do NOT read script presence as proof of what it does. Distinguish CONFIGURED_API_SHARED_CANDIDATE, CONFIGURED_OPERATION_SCOPED, RESOLVED_OPERATION_SEMANTICS and NOT_EVIDENCED. No runtime egress/traffic inference. Keep credentials, hosts, consumer PII and raw payload values out of committed reports.

## Action disambiguation and error controls
- Preserve explicit source actions and source pointers. Reject/rejection, approve/approval, cancel/cancellation, activate/deactivate, generate/delete, and read/write are **distinct behavior categories** unless targeted authoritative evidence documents equivalence.
- Avoid false lexical matches, stem collisions, generic CRUD heuristics, and relying on Task 015 HIGH as verified accuracy.
- Distinguish different endpoint paths with same business action/object from different actions performed on same object. When action can only be inferred from a name, mark as provisional; do NOT make hard different-business verdict without independent supporting evidence.
- Same schema may represent a reusable command envelope or common API response wrapper; it does not prove business duplication.
- Backend *system* sameness differs from backend *operation* sameness; if dispatch depends on values not in source, explicitly leave behavior unresolved.
- Subscription existence/absence and version numbering only contextualize exposure and coexistence hypotheses. No production usage or retirement decisions.

## Execution boundary / low-token
Use bounded indexed checks and targeted verification against the 1,170 existing candidates, not 2,414×2,414 pairs and not a complete regeneration of old analyses. Add candidate checks for **missed same-action same-object across divergent forms** only where existing bounded indexes allow, with separate counts and provenance; avoid claiming recall completeness. Keep 1,481 unpaired operations visible. No Vector DB/Blackboard/multi-agent build or mass Confluence crawl. Do not demand manual adjudication of all 1,170; provide compact prioritized review samples and aggregate outcomes.

## Evidence and acceptance
Write additive source code/tests only when needed and compact evidence under `tests/evidence/task-016/semantic-refinement/`; full outputs to ignored `indexes/`. Include:
- `refinement_contract.md` and explicit definitions/decision matrix;
- `pair_refinement_distribution.json` reconciling **all 1,170 existing pairs exactly once**, old-status vs new-refinement cross-tabulation, ambiguous evidence reasons, how many structurally-equal pairs are NOT proven same function, and counts of newly suggested divergent-form candidates (if any);
- `focused_cases.jsonl` with specific names, exact method/path, business action/object, request/response comparison, scoped backend operation evidence, direct evidence pointers, Product/Plan/Subscription only as context, and reasoned negative vs positive evidence;
- `false_positive_and_false_negative_audit.md` including approve/reject/cancel-type controls, same-schema false positives and differently named same-behavior candidates;
- `review_priorities.json` noting specific unresolved behavioral semantics and targeted source requests;
- `commands_and_results.txt` with deterministic regeneration and focused/regression test outcomes.
Maintain source/identity fidelity; never edit frozen components; no invented behavior, no semantic merge. Verify exact counts, output stability, scoped certainty, redaction, continued unpaired visibility and absence of approved duplicates. Known five Phase 0 fixture setup errors must remain separate if present.

## STOP
Update `codex/comm/HANSOFF.md` with actual distributions, grounded examples, limitations, tests, notable contradictions and whether the refined candidate layer is adequate for Task 017. Commit/push and **STOP for architect review**. Do NOT start Task 017 or any later modernization work.
