# Task 018E coverage report

## Coverage

- Domain → API: 638/993 module-scoped QIWA Parent identities have a deterministic artifact or operation name edge.
- API → Domain: 618/2,414 accepted HTTP operations have one provisional functional-domain primary; 1,796 remain review-required.
- Canonical API artifact matching: 642/2,036; all 2,036 APIs remain accounted for, including 41 zero/unsupported-operation APIs.
- Inventory closure: 2,414/2,414 unique operations; 14 EA areas; 30 literal source modules; 4,437 QIWA rows.

## Cache and source controls

- Cold/warm validation scenario: cold run rebuilds 8 stages; immediate warm run hits all 8 stages and rebuilds none.
- Targeted assembly scope: 38 YAML files; source fingerprint scope: 45 files; broad raw-YAML rereads avoided: 1998.
- Cache keys include content hashes, EA rules, matcher version, cache schema and build-tool version. Corrupt/count-invalid caches rebuild deterministically.
- Cold/warm validation compares all final CSV bytes and manifests after removing only volatile cache telemetry.

## Controls and unresolved evidence

Exact and controlled normalized names establish provisional candidates, not runtime calls. Technical route, backend platform, TIP exposure, LO channel and Common reuse remain separate dimensions. Generic names are negative controls. Multi-function APIs do not propagate artifact candidates as primaries without operation review. Source staging evidence does not prove production use, runtime egress, retirement or final ownership.

## Validation

- Focused Task 018E suite: 7 passed.
- Full default-sandbox suite: 154 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors.
- Clean available regression subset: 152 passed, 1 socket test deselected; isolated permitted socket rerun: 1 passed.

Final status: **TASK 018E TECHNICAL PASS; CANDIDATE DOMAIN ATTRIBUTION ONLY; STOP AT `EA_REVIEW_TASK018E`.**
