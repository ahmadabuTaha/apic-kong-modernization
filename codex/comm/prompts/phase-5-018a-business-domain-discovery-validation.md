# Phase 5 — Task 018A: Business Domain Discovery Validation

## Authorization and scope
Enterprise Architect authorizes only a BOUNDED discovery validation sample before Task 018 full. Do not run Task 018B, Task 019, productization, Kong design or retirements. Outputs are candidate domain hypotheses sourced from APIC, not EA-approved enterprise taxonomy.

Architectural target: one Domain-Centric vocabulary across Applications, APIs/Integration, Data and Events. Broad labels such as Employment, Establishment and Visa can be umbrella levels, not necessarily true domain responsibility boundaries. Domain has business objects, processes, states, capabilities and events when these are genuinely evidenced. **Do not invent processes, states, events or capabilities from API names.** Task 019 handles capability mapping separately. Each missing dimension: NOT_EVIDENCED_FROM_APIC.

## Baseline and sampling
Reuse frozen Task 014-017A indexes, not new all-pairs searches or broad source re-extraction. Baseline: 2,036 canonical APIs, 2,414 accepted HTTP operations, Task 016 pair candidates and 1,481 unpaired operations, 71 Task017 proposals, five oversized reviews covering 132 operations, 14 bounded cross-API links, 90 productization backlog entries. Preserve all IDs, source pointers, hashes, former findings and 46 adversarial review controls.

Build **40-60 distinct architectural cases** centered on source operations, preferably 70-100 UNIQUE operations; report exact coverage/shortfalls, no reversed/padded cases. Stratify for:
- Evidenced shared business responsibility across different APIs; diverging responsibility within one API.
- Business object vs process vs domain vs umbrella distinctions, at least 8 challenging boundary cases.
- Conflicting or copied descriptions, generic methods/paths, test/POC, technical utilities and reference-data lookups; at least 6 hard negative controls.
- 017A retained/split/AS-IS/evidence-required/technical cases; five oversized, selected cross-API links, SC Request, versions and Product/Plan differences.
- Different API names implying same responsibility and similar API names masking different purposes.
Each case reports actual API name, method/path, operation IDs, provenance, documented business object/action and certainty, proposed candidates, specific counterevidence, alternative, source limitations and missing evidence.

## Proposed classification semantics
Unit = source HTTP operation, never automatically the whole API. At most one evidence-backed PRIMARY domain candidate per operation; leave primary null when uncertain and retain alternatives. API-domain footprint is a derived view of sampled operations, NOT whole API classification.

Candidate taxonomy uses stable IDs, responsibility-based names, inclusion/exclusion rules, domain-vs-subdomain-vs-umbrella status, supported objects and aliases. Maintain explicit process/state/capability-signal/event evidence slots. Avoid a new Domain per endpoint or a broad mega-domain from one token. Backend vendor, API name, Product/Plan, shared schema, HTTP wrapper alone do not establish domain.

Classification statuses: DIRECTLY_SUPPORTED; PROVISIONAL_SUPPORTED; MULTIPLE_DOMAIN_CANDIDATES; CONFLICTING_EVIDENCE; INSUFFICIENT_BUSINESS_SEMANTICS; TECHNICAL_UTILITY_EVIDENCED; TEST_OR_POC_EVIDENCED. Use precise reason codes and provenance rather than arbitrary numerical scores or forced classification percentage. No owner, consumer, traffic, backend actual egress or production inference.

## Enterprise Domain Alignment gate
When finished, offer EA comparison of candidate labels against intended cross-layer enterprise model:
- Is each label an umbrella, coherent Domain, Subdomain, business object/process, capability or technical namespace?
- Which objects, processes, states, capabilities and events are documented versus unknown?
- Can the label generalize across applications, data, integration and event platforms? Clearly mark other-layer verification unavailable.
- Which overlaps need rename, merge, split or explicit uncertainty?
- How do findings enrich the 71 proposals, 5 oversized reviews, 14 cross-API links and 90 backlog entries without rewriting or approving them?
- Which architecture decisions need business owners or other non-APIC sources?
All Enterprise Architect approvals remain PENDING. Domain similarity never proves a Logical API grouping or a Product boundary.

## Deliverables
Commit under `tests/evidence/task-018/domain-validation/`:
1. `domain_discovery_method_and_guardrails.md`
2. `candidate_enterprise_domain_taxonomy.json`
3. `sampled_operation_domain_cases.jsonl`
4. `executive_sample_review.md` covering every case and 12+ deep contrasting examples
5. `api_domain_footprint_sample.jsonl`
6. `task017a_domain_enrichment_links.jsonl`
7. `enterprise_domain_alignment_decision_gate.md`
8. `sample_coverage_and_gaps.json`
9. `commands_and_results.txt` and `build_manifest.json`
Ignored detailed indexes and deterministic generation scripts may be added; keep committed evidence compact and readable.

## Tests and STOP
Validate distinct sample counts, exact source IDs/provenance, frozen hashes, no invented semantic dimensions, no forced whole-API domain, negative controls, Task017A source links, deterministic generation, source-redaction and regression safety. Technical PASS, domain-evidence sufficiency and EA acceptance are independent. Run focused and repository tests, separately report the five known Phase0 fixture setup errors. Codex updates HANSOFF.md, commits/pushes, then STOPS for EA review. No Task018 full or Task019 without explicit approval.
