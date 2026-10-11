# Phase 5 / Task 017 — EXPANDED Architecture Validation Sample (decision gate before full estate)

## Enterprise Architect instruction — 2026-10-11
EA explicitly asks for **substantially more actual examples, contrasting samples, and evidence** than Task 017's original 10 mock cases before deciding whether to continue. No authorization for Task 017 full estate. Task 017 mock is TECHNICALLY EXECUTED / ARCHITECTURE REVIEW REQUIRED; its 2 cohesive candidates are provisional, not architect-approved.

**Execute an additive expanded VALIDATION SAMPLE**, not the full formation, and do NOT repeat Tasks 014–016 or reopen frozen components.

## Decision questions (must be answerable from output)
- What evidence and explicit decision rule support putting these operations in ONE conceptual Logical API, as distinct from just sharing a name, schema, backend, Product or business object?
- Why is this a cohesive business-facing boundary, and why might it NOT be? What is an alternative boundary?
- Is the proposed membership an evidence-supported current link, a conceptual grouping hypothesis, or unknowable due to missing process/consumer/ownership data?
- Which cases prove the rule detects FALSE GROUPING and avoids transitive equivalence?
- What does PASS/FAIL mean? Test/implementation PASS is distinct from evidence sufficiency and Architecture Acceptance. Report each independently.
- Which hard-to-decide cases expose blind spots in the current logic and would most affect full rollout?

## Samples: broad and challenging, not padded
Retain original 10 as immutable anchors and select **at least 30 NEW, DISTINCT additional boundary cases**, target 40–50 total cases (or as many as genuinely supportable, explaining any numerical shortfall). Cover at least ~70–100 unique source operations where feasible. Do not duplicate a pair merely by reversing sides or by repackaging the same source members, and count unique operations/canonical APIs separately.

Select via deterministic stratified/bounded index queries; include diverse functional areas *without assigning domains/capabilities*, metadata quality levels, versioning, operation sets and comparison dimensions:
- 6+ same object with DIFFERENT actions (approve/reject/cancel, submit/update, generate/delete, activate/deactivate) to test possible cohesion vs actual distinct operations.
- 6+ different names/base paths/endpoint contracts for potentially same action/object; do NOT turn them into confirmed duplicates.
- 5+ negative controls: structurally matching schemas or generic wrappers / shared backend but clearly unrelated business intent.
- 5+ version/variant or similar-name relations, including materially different Contracts and differences in exposure.
- 4+ multi-operation canonical API cases where collection/item methods may form coherent boundaries; ambiguous root and mixed technical/business operation controls.
- 4+ Product/Plan/subscription and different consumer exposure CONTEXT contrasts; no production calls inference.
- 4+ disagreement/insufficient semantics examples, including different backend configured paths, API-shared candidate route, policy/mapping/dispatch uncertainty.
These strata may overlap but each case should carry all its relevant tags. Include positives, negatives, alternatives, and uncertainties; don't select only easy keyword matches. Describe sample source universe, sampling bias and exclusions; 40–50 is a *review sample*, NOT representative statistically.

**Explicit named leads to investigate (if accepted indexed sources are present)** from Task 016 compact evidence, which did NOT appear among original Task 017 10: user-management-privilege vs user-management; getbasiccrinformation vs mcichangehistory; verifyviolatedestablishment vs verifysaudizationcertificatevalidity; osh-getcategorybyid vs getcategorybyid; employeeauthind-v2 vs contractauthenticationindicator; qiwa-streaming-v2 vs qiwa-streaming. Evaluate them as candidates to TEST, do not presuppose groupings or that they have enough semantic evidence. Also revisit SC Request as an anchor with detailed rationale/limitations; do not alter original mock evidence.

## Explicit decision rubric (proposal, not invented corporate standard)
Apply a structured rubric to **each candidate boundary and each individual membership**:
- R1: Identified and adequately supported business object/resource/workflow.
- R2: Supported distinct business actions and evidence of coherent lifecycle/workflow or resource responsibility, rather than only matching object tokens.
- R3: Consumer-facing exposure/ownership/authorization considerations, including explicit NOT_EVIDENCED where missing. Lack of enterprise standards is a reality, not permission to invent intent.
- R4: Contract/base-path/version and transformation differences and their effect on conceptual boundary; don't infer compatibility.
- R5: Backend *operation-level* versus API-shared configured candidate; group may be provisionally hypothesized without runtime proof but never claim backend behavior.
- R6: Counterevidence and alternative plausible API boundary. Give explicit **reason not to group** and what evidence would discriminate.
- R7: Source provenance and scope certainty.
Each: SUPPORTED, CONTRADICTED, or NOT_EVIDENCED with source pointers and brief rationale; structural similarity alone must never satisfy R1+R2. R3/5 may be NOT_EVIDENCED without erasing a credible proposal, but force a corresponding unresolved risk. Do not manufacture evidence.

Use three **independent** result axes:
1. **Technical validation**: PASS / FAIL (machine tests, stable IDs, reproduction, source integrity).
2. **Evidence sufficiency**: SUFFICIENT_FOR_PROVISIONAL_BOUNDARY / PARTIAL / INSUFFICIENT / SUPPORTED_SEPARATE (explicit R1–R7 why).
3. **Architect acceptance**: ALWAYS PENDING for new candidate boundaries, pending explicit decision; NEVER infer approval from passing tests.
Preserve original Task 017 mock status, mark new judgements as *expanded review findings*; don't overwrite prior labels or score unsupported certainty. Do not call a proposed boundary "validated" from software PASS.

## SC Request detailed case study — mandatory
For `approverejectscrequest` POST /apprejscreq vs `cancelscrequest` POST /cancelscreq:
- Show exact 2 source operations, supported approve/reject/cancel intents (without manufacturing 3 APIC source operations).
- Show front-end contract types, differing configured backend paths (/sc/apprejscreq vs /sc/cancelscreq), API_SHARED certainty, distinct Product/Plan IDs/relationships, and absence of proven actual calls.
- Explicitly differentiate "same SC Request object" from "same lifecycle, owner, consumer boundary, entitlement or release path" (NOT EVIDENCED unless accepted source directly supports).
- Provide at least two plausible conceptual boundaries: unified SC Request Actions, or separate Decision and Cancellation APIs, with evidence and tradeoffs, and answer what could make either architecture reasonable.
- Explain exactly why provisional cohesion is possible but **architectural PASS is unavailable**; do not infer business lifecycle or user roles.
- Do not read raw stage files unless accessible and targeted; source pointers in indexes are evidence pointers, not authorization to infer contents.

## Artifact expectations — reviewer friendly, LOW TOKEN
Commit compact evidence under `tests/evidence/task-017/expanded-validation/`:
- `architecture_decision_rubric.md` (criteria, statuses, scope and false-positive rules)
- `expanded_sample_register.jsonl` (all ~40–50; readable fields with names, paths, actions, candidate boundary, original APIs, direct pointers, R1–R7 dispositions, pros, cons, alternate grouping, evidence strength, 3 independent result axes)
- `executive_review_table.md` (human-readable **all cases**: names, membership, justification for / against, confidence limitations, next decision; no enormous raw JSON pasted here)
- `sc_request_deep_dive.md` (traceable detailed two-operation walkthrough)
- `negative_controls_and_boundary_ambiguity.md` (at least 5 false-positive controls, non-transitive A~B~C traps and when NOT to form)
- `sample_coverage_and_gaps.json` (original 10 vs new count, canonical/operation unique counts, strata, bias, unaddressable categories and why)
- `review_decision_sheet.md` (small number of decisive EA approval/reject/change-rule questions; not 50 compulsory manual verdicts)
- `commands_and_results.txt`, `build_manifest.json`.
Full machine indexes may remain ignored under `indexes/`. Avoid requiring a new dashboard, CI/CD or production telemetry. Safe/secret-redacted evidence. Reuse accepted indexes/caches and minimal targeted raw source reads; no all-pairs search.

Tests: deterministic sample selection and reproducibility; no double counting; old 10 preserved; membership/source ID exactness; positive and negative group distinctions; approve/reject/cancel distinct; no false "PASS" for architecture; R1–R7 source evidence/counterevidence completeness; no promotion of source schema similarity/shared backend into functional identity; no unauthorized domains/capabilities/Kong/retirement/production assumptions. Run focused tests and existing regressions; preserve frozen source. Report known Phase0 fixture setup issue separately.

## STOP
Update `codex/comm/HANSOFF.md` with exact new-sample counts, actual examples spanning all decision classes, SC Request deep-dive result, rubric issues, tests and open questions. Commit and push. **STOP for explicit EA decision on whether Task 017 Full is viable.** Do not initiate Task 017 full, Tasks 018–019, API retirement or Kong architecture.
