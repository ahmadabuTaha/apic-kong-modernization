# Task 014 architecture decisions pending

## Decision 1 — backend attribution and certainty

Choose one:

- **A (recommended):** two-layer fact/candidate model. Preserve `CONFIGURED_API_SHARED` and exact `EVIDENCED_OPERATION_SCOPED` facts; permit separate `CANDIDATE_INHERITED_CONTEXT` links that explicitly do not assert operation egress; use `UNRESOLVED_ROUTING` when no accepted invocation evidence exists.
- **B:** keep API-shared evidence only at API level and omit inherited candidates.
- **C:** provide another explicit taxonomy and attribution rule.

Risk of A: candidate links may be misread unless certainty and limitations are mandatory. Risk of B: later reviewers lose useful, traceable context. Promoting API-shared invokes to proven egress is not offered because evidence does not support it. This decision controls the Gate B operation/backend record contract and cache schema.

## Decision 2 — same-canonical YAML variants

Choose one:

- **A (recommended):** canonical API envelope with retained source variants; collapse byte-identical payload storage, retain structurally equivalent variant provenance, and keep conflicting variants separate with `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW` and per-variant operation identity.
- **B:** always keep every source occurrence as a separate payload/operation set, even when byte-identical.
- **C:** define another deterministic merge/conflict policy.

Risk of A: fingerprint evolution needs explicit versioning and invalidation. Risk of B: duplicate operations can obscure the canonical inventory. Automatic lexical selection or unconditional merge is not offered because either can discard or invent source semantics. This decision controls Gate B cardinality, operation IDs, cache keys, and conflict reporting without changing frozen Phase 2 identity.

Gate B remains unauthorized until both decisions are recorded in task instructions.
