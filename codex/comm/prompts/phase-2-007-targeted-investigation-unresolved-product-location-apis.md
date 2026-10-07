# Phase 2 — Task 007: Targeted Investigation of 113 Unresolved Product-Location API Occurrences

## Phase

Phase 2 — URI / Identifier Resolution

## Task Type

Targeted investigation / evidence validation.

## Objective

Explain, with inspectable evidence, why Task 006 produced exactly 113 unresolved Product-location API occurrences and determine whether they are:

- correctly unresolved under the approved Phase 2 identity contract; or
- evidence of a reproducible resolver defect that must be fixed before Phase 2 can pass.

This task must make the investigation transparent. A summary count in `codex/comm/HANSOFF.md` is not sufficient by itself.

## Starting Observation to Verify

Task 006 reported:

- Product-location API occurrences: 2,357
- attached Product-location API copies: 2,244
- unresolved Product-location API occurrences: 113

Verify explicitly whether:

```text
2,357 - 2,244 = 113
```

fully explains the unresolved population, and prove that all 113 records are exactly the Product-location occurrences not attached by the approved bridge/reference evidence.

Do not assume the arithmetic alone proves the resolver is correct.

## Architecture Boundary

This remains Phase 2 investigation.

Do NOT begin Phase 3.

Do NOT perform:

- Domain classification;
- Exposure Channel classification;
- Logical API / Logical Capability creation;
- backend inference;
- runtime usage inference;
- duplicate or overlap classification;
- retirement analysis;
- rationalization;
- Kong mapping or design.

The goal is to explain the existing resolution outcome and identify a concrete resolver defect only if evidence proves one.

## Frozen Components

- Phase 0 remains frozen.
- Phase 1 remains frozen.
- Task 006 resolver behavior is treated as provisionally frozen for investigation.

Do not modify Phase 0 or Phase 1.

Do not modify the Task 006 resolver merely to reduce the unresolved count.

Only change `identity_resolver/` if this investigation first demonstrates a reproducible Task 006 defect against the approved identity contract. If no defect is proven, leave the resolver unchanged.

## Required Evidence Artifact Directory

This prompt explicitly authorizes a task-specific evidence directory:

`tests/evidence/task-007/`

This directory is a required task artifact and is an exception to the normal "HANSOFF-only reporting artifact" rule.

Do not create ad-hoc evidence/report files elsewhere.

All investigation scripts/commands used specifically to explain the 113 unresolved occurrences must write their inspectable outputs into this directory.

At minimum create:

- `tests/evidence/task-007/unresolved_product_location_apis.jsonl`
- `tests/evidence/task-007/investigation_summary.json`
- `tests/evidence/task-007/commands_and_results.txt`

If a focused investigation helper script is required, place it under the existing test structure, preferably:

- `tests/evidence/task-007/investigate_unresolved.py`

or use a focused test/helper already committed under `tests/`.

Do not place generated evidence under `indexes/` only; the purpose of this task is to leave a reviewable audit artifact in the repository.

## Required Per-Occurrence Evidence

For each of the 113 unresolved Product-location API occurrences, emit one JSONL record with evidence sufficient for architecture review.

Include, when available:

- Phase 1 `extracted_record_id`;
- source path;
- source pointer;
- source SHA-256;
- observed API name;
- observed declared version;
- observed title;
- observed APIC ID/self URL if any;
- organization/catalog scope evidence if any;
- whether any Product `$ref` maps exactly to this source path;
- count/list of Product `$ref` occurrences that target this path;
- Product context inferred only from the source path / directly observed Product evidence;
- count/list of registry API candidates with exact compatible identity evidence;
- count/list of authoritative API-catalog candidates with exact compatible identity evidence;
- exact name+version candidate counts for diagnostic visibility only;
- hash-equal authoritative API-catalog candidate counts for corroboration only;
- whether an approved Product/API bridge convergence exists;
- which approved attachment condition(s) were not satisfied;
- current Task 006 resolution outcome;
- references to any candidate canonical identity records considered by the resolver.

Do not use name, version, or hash as a merge rule. These fields are diagnostic evidence only.

Do not invent a new classification taxonomy for failure reasons. Record the concrete failed checks / missing evidence in plain descriptive fields.

## Required Investigation Questions

Answer with evidence:

1. Are all 113 truly unreferenced by Product `$ref`?
2. Are some referenced indirectly by registry/Product membership but not by YAML `$ref`?
3. Do any 113 have exact APIC self URL evidence?
4. Do any have APIC ID + compatible scope evidence?
5. Do any have a unique authoritative API-catalog candidate by the already-approved API bridge criteria?
6. How many have exact name+version matches only?
7. How many are byte/hash identical to an authoritative API artifact but lack approved bridge/reference evidence?
8. How many have multiple possible authoritative or registry candidates?
9. How many have no candidate evidence at all beyond being an API-shaped Product-location document?
10. Are any of the 113 actually evidence of a Task 006 implementation defect?
11. If a defect exists, provide the smallest reproducible example and explain which approved Task 006 contract rule was implemented incorrectly.
12. If no defect exists, explain why each unresolved group must remain unresolved under the approved rules.

## Required Aggregate Evidence

`investigation_summary.json` must include at minimum:

- total Product-location API occurrences;
- attached Product-location API occurrences;
- unresolved Product-location API occurrences;
- proof that the enumerated unresolved set contains exactly 113 unique Phase 1 records;
- counts grouped by concrete evidence pattern observed during investigation;
- count with any Product `$ref`;
- count with exact self URL;
- count with APIC ID + compatible scope;
- count with unique approved authoritative/registry bridge;
- count with exact name+version diagnostic match only;
- count with hash-equal diagnostic match only;
- count with multiple candidates;
- count with no admissible candidate;
- count demonstrated to be resolver defects;
- count correctly unresolved under the approved contract.

Do not force these categories to be mutually exclusive unless the evidence naturally makes them so. If they overlap, preserve that fact.

## Command / Result Capture

`commands_and_results.txt` must contain the relevant commands executed for this targeted investigation and their meaningful stdout/stderr or summarized deterministic output.

At minimum capture:

- the command used to enumerate the 113;
- the command/test used to verify the count;
- the command/test used to generate the per-occurrence evidence;
- focused pytest command and result;
- any resolver regression command and result if resolver code is changed.

Do not dump credentials or secret values into command output.

The purpose is to let the Enterprise Architect see what was actually run, not only trust a prose summary.

## Test Requirements

Add focused validation proving:

- the unresolved set is deterministically reproducible;
- it contains exactly the same 113 Phase 1 extracted record IDs on repeated runs;
- none of those records is silently omitted;
- none is promoted by name-only, version-only, or hash-only evidence;
- any claimed resolver defect has a failing test before the fix and a passing test after the fix;
- `staging/` remains unchanged;
- credential redaction remains intact.

If no resolver defect is found, do not modify the resolver only to make a test pass.

## Source / Evidence Retrieval Order

Use the low-token evidence order:

```text
Phase 2 identity-resolution output
→ Phase 1 extracted records
→ targeted Product / registry / API evidence
→ targeted raw staging artifact only when verification is required
```

Do not perform an unnecessary full semantic scan of the repository.

## HANSOFF Reporting — Mandatory

Update only `codex/comm/HANSOFF.md` for prose reporting.

The HANSOFF must explicitly reference:

- `tests/evidence/task-007/unresolved_product_location_apis.jsonl`
- `tests/evidence/task-007/investigation_summary.json`
- `tests/evidence/task-007/commands_and_results.txt`

Report:

1. exact reason the population is 113;
2. whether 2,357 - 2,244 fully accounts for it;
3. aggregate evidence patterns found across the 113;
4. representative examples with source paths and extracted record IDs;
5. whether any of the 113 should have been attached under the already-approved Phase 2 rules;
6. whether Task 006 contains a reproducible defect;
7. any resolver code changed, with why;
8. tests/commands executed and results;
9. exact evidence files created under `tests/evidence/task-007/`;
10. recommendation: Phase 2 PASS, FIX_REQUIRED, or HOLD_FOR_ARCHITECTURE_REVIEW.

Do not hide the underlying evidence behind summary prose.

## Acceptance Criteria

Task 007 is complete only when:

- all 113 unresolved occurrences are enumerated in the committed JSONL evidence;
- each one has enough evidence to explain why it was not attached;
- the 113 count is independently reproducible;
- aggregate evidence is committed under `tests/evidence/task-007/`;
- commands/results are committed and inspectable;
- any resolver defect is backed by a reproducible test;
- no unsupported merge is introduced;
- HANSOFF points to the evidence artifacts and states the Phase 2 recommendation.

## Stop Condition

Complete only the targeted investigation and any minimal resolver correction proven necessary by that investigation.

Update `codex/comm/HANSOFF.md`, commit the task changes/evidence, push, and stop.

Do not begin Phase 3.
