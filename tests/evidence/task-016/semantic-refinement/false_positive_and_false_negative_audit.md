# Task 016 false-positive and false-negative audit

## Action false-positive controls

- `task016-semantic-audit-control:sha256:db619c1e2bd069bf5b3881ad0a158d1bcaffcd7cab5fe73c3e09b1ff498fae4a` is an audit-only control, not one of the 1,170 pairs. Direct descriptions/pointers document approve-or-reject versus cancel behavior for SC requests. These actions remain distinct even if a common command envelope or response wrapper exists.
- `logical-function-comparison-full:sha256:f900dcc8d472ce63e5a7608d12fe1f6eb1db35febea23e8b233c285cb8163c4b` compares `submitestablishmenttrainingsdisclosure` with `updateestablishmenttrainingsdisclosure`. Supported `['submit']` versus `['update']` acts on aligned object evidence, so its additive verdict is `DIFFERENT_BUSINESS_ACTION_SUPPORTED`.
- `logical-function-comparison-full:sha256:8a471753b65afa8a3e67915196a69a4948ac6800061cb1c9a407e9f782f1aa69` exposes deactivate versus activate path/name signals with structurally equal shapes, but each action has only a single source signal. It remains `SEMANTIC_EVIDENCE_INSUFFICIENT` rather than receiving a hard different-action verdict.
- All 717 structurally equal pairs remain **not proven** to implement the same function. Shared wrappers, response envelopes, endpoint shapes or backend systems are retrieval signals only.

## Differently exposed possible-same cases

- Seasonal visa v1/v2 `logical-function-comparison-full:sha256:71ba80c5451833feea201f35dd02c0b69d244c100dcbe981e182d1424a443f55` retains matching apparent search action/object across versions while preserving the `SortBy` request difference, response differences, candidate-only backend scope, and unverified coexistence/activity. Verdict: `POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE`.
- Employment-status `logical-function-comparison-full:sha256:a48d23abcca4ef7a333d4a1770f44581854dcf076daaa433fe455a5e7ee67b68` retains matching endpoint/wording context but lacks supported operation-level action evidence. Verdict: `SEMANTIC_EVIDENCE_INSUFFICIENT`; structural similarity does not fill that gap.
- The bounded cached check of 1,481 unpaired-visible operations found 0 new exact-action/object divergent-form suggestions. This does not claim complete false-negative recall.

## Backend and exposure controls

- API-shared configured targets remain `CONFIGURED_API_SHARED_CANDIDATE`; same backend system is not same backend operation.
- Operation selectors, invoke paths, branches, rewrites and transformation pointers are retained when present. GatewayScript bodies and dispatch values are omitted and script presence is not interpreted as behavior.
- Product/Plan/Subscription and version context can explain exposure differences but never demonstrate calls, production adoption, interchangeability, retirement or active feature flags.
