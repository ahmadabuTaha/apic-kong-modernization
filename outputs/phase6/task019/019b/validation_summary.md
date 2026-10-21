# Phase 6 Task 019-B validation summary

- Scope: all literal Modules and all source rows; Sub Module excluded from the working model.
- Input SHA-256: `5b1ea781534fbe595892263c69479b8ba01765a12486339be01b15d76b97cc9f`.
- Coverage: 952/952 rows; 32 modules; 952 module-scoped services.
- References: 988 ICD + 953 ISD = 1941 source occurrences; 1941 accepted + 0 rejected.
- Documents: 1941 unique typed identities; zero-document services: 0.
- Exceptions: 182 (blank 182; invalid 0; duplicate occurrence 0; identity collision 0).
- Common regression: PASS; 116 source rows, 116 services, 225 occurrences, and all six normalized CSV projections byte-match the frozen baseline.
- Per-module coverage: `indexes/phase6/task019/019b/module_coverage.csv`.
- No documents were fetched and no semantic, API, graph, runtime, or product inference was made.
- Next gate: `EA_REVIEW_TASK019B`.
