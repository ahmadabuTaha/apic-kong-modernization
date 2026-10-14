# Task 018D reviewer explanation

This is an independent deterministic assessment. Task 018B/018C distributions, joins and labels are not inputs. The 13 EA classification areas are candidates pending Enterprise Architect review; TIP is also reported independently as exposure.

## Reproducible execution

`python -m business_domain.independent_mapping_main`

`pytest -q tests/test_business_domain_independent_mapping.py`

`pytest -q`

## Results

- Operations: 2,414; canonical APIs: 2,036; zero-operation APIs: 41.
- Invocation branches: 3,743; match evidence rows: 4,748.
- Provisional primary candidates: 3; unmatched: 2,410; true ambiguous: 0.
- TIP confirmed exposure operations: 140; TIP candidates: 59.

## Evidence limits and rule application

The QIWA CSV has no route/endpoint column. Exact API names, operation names, generic route tails, shared hosts and module-family names therefore remain candidates. Exact switch message-root identifiers may confirm a configured branch-to-Parent identity; they do not prove runtime execution. EA ownership anchors apply only after a service candidate exists. Common uses distinct consuming modules at thresholds 1, 2–4 and 5+, preserving origin. TIP Product/Plan/subscription evidence never overwrites business ownership. Raw target strings, catalog values and credentials are omitted.

Named anchors are retained in the CSV evidence: SubmitOccupationCorrectionRequest→Occupation and GetGosiContractsList→Contracts ownership override consumption; sendQIWAReports branches retain switch flags separately; UpdateEstablishmentContactAddress, ValidateIssueEstablishingVisas and SubmitWorkPermitRequest remain limited by actual match evidence.

## Test outcomes

- Focused: 9 passed.
- Repository: 147 passed, 1 sandbox loopback failure, 5 known missing-fixture setup errors; isolated loopback rerun 1 passed; permitted suite excluding only tests/test_profiler.py 146 passed.
- Known baseline: tests/fixtures/repository_profile/staging is absent from worktree/HEAD; five Phase 0 setup errors remain frozen and separate.

Final status: **TASK 018D TECHNICAL PASS; STOP AT EA_REVIEW_TASK018D.** No domain is ratified.
