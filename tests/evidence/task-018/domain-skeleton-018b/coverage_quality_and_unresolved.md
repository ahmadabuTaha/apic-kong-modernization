# Task 018B Coverage, Quality, and Unresolved Evidence

Full operation preservation: **2414/2414** unique Task 014 operations. Canonical API accounting: **2036/2036**, including **41** zero-operation/unsupported APIs. Skeleton: **11** fixed candidates; new candidates: **0**; enterprise approvals: **0**.

## Candidate footprint

Primary counts do not double-count operations. Alternative counts are separate and may overlap.

| Candidate | Primary operations | APIs with primary operations | Alternative occurrences | APIs with alternatives |
|---|---:|---:|---:|---:|
| Visa | 83 | 81 | 37 | 37 |
| Establishment | 237 | 225 | 197 | 195 |
| Contracts | 143 | 141 | 68 | 67 |
| Nitaqat | 39 | 35 | 27 | 27 |
| Payment | 104 | 88 | 29 | 29 |
| Common | 62 | 58 | 58 | 58 |
| User Management | 93 | 86 | 63 | 63 |
| Work Permit | 37 | 35 | 10 | 10 |
| Work Force | 261 | 255 | 128 | 125 |
| Notification | 15 | 15 | 2 | 2 |
| Certificate | 42 | 41 | 26 | 26 |

## Classification quality

- `CONFLICTING_SOURCE_EVIDENCE`: 36
- `PRIMARY_CANDIDATE_PROVISIONAL`: 1116
- `TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY`: 87
- `UNRESOLVED_AMBIGUOUS`: 187
- `UNRESOLVED_INSUFFICIENT_SEMANTICS`: 988

Targeted YAML enrichment inspected 188 unresolved, conflicting, or boundary-sensitive operations across 180 source documents. Hash mismatches: 0; parse errors: 0; unresolved local schema references: 0.

Schema names are not automatically business objects. The register distinguishes core-object candidates, object references, DTO/transport models, lookup/value sets, technical envelopes, documented actions, and state-value candidates. Enum values do not prove transitions or a state machine; shared schemas do not prove shared ownership.

## Representative negative controls

| Operation | Result | Reason |
|---|---|---|
| semantic-operation-v2:sha256:001dcdfc525f597525f04c003986cd5ead785faee0735222eee06ef5d61274d0 | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:009a6260a4df73f1bb749a514e0403bd9a5a071d227c689dd0f4aaeb1ee808b4 | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:00a656d726247f1f5a5c5f243c9c5a8a40e0ca2d87770ff1bc553d502148d191 | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:00e845ed6be485d9bef11b4848b6a6ba7a21fa440dcffdcfc718609c9db0820a | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:014785f6bb84f9e18b3ec8540f6a3426198eab8dd8dc8594f5f612b314699387 | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:015dc76c089b78a3c1cd01b74d9d6c116d6889a223de3cc85a636797b73ac5ab | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:01a2b27c9b28c886c0c2d7853406c30322643fd04bfae4e2f797423377d4c8c6 | TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY | Technical/test/POC evidence is explicit and no skeleton business target is supported. |
| semantic-operation-v2:sha256:01f6a1c99f6b2d69ff7442ede7e583b37a715741e0bb0174240e4333990adabc | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:021a28b173c9685579c7ed0000f0cf79395e3820a82d6cb5dd3ee70067945712 | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |
| semantic-operation-v2:sha256:027d5d265c7f8cfa992d9181d4da297cea09feb732884ecaef6df4c48a51072f | UNRESOLVED_INSUFFICIENT_SEMANTICS | No operation-level clue supports any of the eleven skeleton candidates. |

Unresolved evidence is a gap, not an error: APIC configuration does not establish production usage, retirement, runtime egress, enterprise ownership, or cross-layer domain authority. No whole-API inheritance or forced coverage was applied.

Final position: technical Task 018B evidence complete; Enterprise Architect decisions pending at `EA_REVIEW_BEFORE_DOMAIN_CHANGES_OR_TASK019`.
