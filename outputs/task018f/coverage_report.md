# Task 018F coverage report

## Artifact-first closure

- Canonical API artifacts: 2,036/2,036; zero/unsupported-operation artifacts: 41/41.
- Accepted HTTP operations: 2,414/2,414; schema evidence rows: 12,876 with request/response direction retained.
- QIWA source: 4,437 rows, 30 literal modules and 993 module-scoped Parent identities.
- Domain registry: exactly 15 first-class AS-IS domains, including TIP, LO and Utilities.

## Candidate distributions

- API primary candidates: {"Certificate": 19, "Common": 86, "Contracts": 171, "Establishment": 313, "LO": 64, "NULL": 566, "Nitaqat": 21, "Notification": 15, "Occupation": 69, "Payment": 78, "TIP": 235, "User Management": 20, "Utilities": 125, "Visa": 84, "Work Permit": 57, "WorkForce": 113}
- Operation primary candidates: {"Certificate": 16, "Common": 78, "Contracts": 173, "Establishment": 317, "LO": 62, "NULL": 748, "Nitaqat": 18, "Notification": 21, "Occupation": 75, "Payment": 90, "TIP": 283, "User Management": 68, "Utilities": 218, "Visa": 87, "Work Permit": 45, "WorkForce": 115}
- Lifecycle purpose: {"BUSINESS": 1345, "POC": 4, "REVIEW_REQUIRED": 552, "SAMPLE": 1, "TEST": 10, "UTILITY": 124}
- TIP/LO inventory rows: 340; Utilities/Common review rows: 211; lifecycle POC/Test/Mock/Sample rows: 15.
- Null primary is intentional for 566 artifacts and 748 operations; exceptions retain precise source pointers and review actions.

## Acceptance controls and caveats

`user-management`, `user-management-privilege`, `getpaymentdetails-v2`, `gosi_getAccessToken`, `SubmitOccupationCorrectionRequest`, and `GetGosiContractsList` are evaluated from artifact/operation evidence without a mandatory QIWA Parent. TIP and LO remain legal primaries with a separate underlying functional domain. POC/Test/Mock/Sample is a lifecycle disposition, never a business domain or retirement decision. `sendQIWAReports` retains 63 configured applicable backend branches and no forced owner when evidence conflicts. Schema references, Product/Plan links, backend configuration and QIWA name edges do not prove runtime use or final ownership.

## Cache and reproducibility

- Cold and warm runs use the same twelve validated stages; cache telemetry is recorded in `manifest.json` and excluded from deterministic output comparisons.
- Raw YAML access is bounded to conditional backend sources; original staging evidence remains read-only.
- Cache keys independently cover canonical identities, QIWA CSV, schema indexes, Product/Plan relationship inputs, backend inputs, EA rules and parser versions. CSV output is deterministic; cold/warm equality is test-controlled.

## Validation

- Focused Task 018F suite: 8 passed.
- Full default-sandbox suite: 162 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors.
- Available regression subset: 160 passed, 1 sandbox socket test deselected; isolated permitted socket rerun: 1 passed.

Final status: **TASK 018F TECHNICAL EXECUTION; CANDIDATE MAPPING ONLY; STOP AT `EA_REVIEW_TASK018F`.**
