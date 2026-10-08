"""Generate compact, redacted Task 014 Gate A architecture evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from semantic_preflight import backend_case, build_variant_profile, compare_cross_canonical_pair

OUT = ROOT / "tests/evidence/task-014/architecture-preflight"


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def generate() -> None:
    backend = [
        backend_case(ROOT, "apic-identity:sha256:0009ee4eeece2430096ec9be843777a8e4258c260de73c9f9fb702bc865a55ce", "simple_shared_single_operation"),
        backend_case(ROOT, "apic-identity:sha256:0187d497510d1bf2bd0681b8cd6d0efba73232ad9af4bb4a72efbbf2dd9d69ca", "shared_conditional_multi_operation_multiple_targets"),
        backend_case(ROOT, "apic-identity:sha256:3b86d823b059c406a32787df5cfad04009ee90c7da92f8f8d93c6161b6b9cb0c", "explicit_operation_scoped_single_operation"),
        backend_case(ROOT, "apic-identity:sha256:3d4ca17f0a9ef1fd790fa0f40e2b0969d7508f74f095d31ca2fefa7f899fe629", "explicit_operation_scoped_multi_operation"),
        {
            "case": "mixed_api_shared_and_operation_scoped_same_api",
            "case_status": "NOT_EVIDENCED_IN_SAMPLE",
            "basis": "Compact Task 011 evidence has zero canonical APIs containing both accepted scope classifications.",
            "runtime_usage_proven": False,
        },
        {
            "case": "absent_or_equivocal_backend_evidence",
            "case_status": "EVIDENCED",
            "canonical_api_id": "apic-identity:sha256:04f4b16ef367adef6140193d54c2f60e7397844cfaa76f42fea3cdfa70a486cd",
            "accepted_scope_facts": [],
            "fact_taxonomy": "UNRESOLVED_ROUTING",
            "reason": "Registry-only canonical API; no accepted source document or Task 011 invocation observation.",
            "runtime_usage_proven": False,
        },
    ]
    write_jsonl("backend_evidence_samples.jsonl", backend)

    variants = build_variant_profile(ROOT)
    write_jsonl("yaml_variants_samples.jsonl", [{"record_type": "INDEX_ONLY_SUMMARY", **variants["summary"]}, *variants["samples"]])

    pairs = [
        compare_cross_canonical_pair(
            ROOT,
            "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
            "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
            "backend-target:sha256:9edc5ce72c9462bb2af910f2d193140014601a8422e60c623ebdf43c842a107f",
        ),
        compare_cross_canonical_pair(
            ROOT,
            "apic-identity:sha256:05afc366ab4881e1a066cf2b1f75881d83596b5ac19bbb2b2b4fdc239f27c201",
            "apic-identity:sha256:6ee892bf220701b553d4a49282520a6dae2d66e2d3ba5600e20749b13441162d",
            "backend-target:sha256:1eebf982f3d4d4984ad254abbbcdba76e60b5b26643a7e8521067665297cc495",
        ),
        compare_cross_canonical_pair(
            ROOT,
            "apic-identity:sha256:0f7a768abf0fdf88824ff5a4b3f1f03ad36592bb2f7c59bc2a2f771297fbfcf7",
            "apic-identity:sha256:c265a4fb25b5c37c1dbd76a0d96ad8357354e04c8403c3ddf15512f4d266a3c0",
            "backend-target:sha256:2d510af14a89dfb0bda088e6ff8f5cd35b5f31ccc5f3ceeef588aa145aeabb87",
        ),
    ]

    (OUT / "backend_evidence_options.md").write_text("""# Backend evidence attribution options

## Evidence findings

The committed sample covers a one-operation API with an API-shared invoke, a 24-operation API with 24 invokes under ordinary `switch` branches, one- and eight-operation APIs with explicit `operation-switch` anchors, an API with no accepted invocation evidence, and an explicit `NOT_EVIDENCED_IN_SAMPLE` result for a mixed shared/scoped API. Task 011 scope classifications and observation IDs are unchanged.

Operation count never upgrades configuration evidence into runtime evidence. In particular, each ordinary `switch` branch on the 24-operation sample remains `CONFIGURED_API_SHARED`; it has conditional action context but no exact method/path operation anchor. Its operation associations are candidates only.

| Case | Accepted fact | Revised representation | Limit |
|---|---|---|---|
| Shared invoke, one operation | `API_SHARED` | `CONFIGURED_API_SHARED` plus separate `CANDIDATE_INHERITED_CONTEXT` | One operation does not prove egress. |
| Shared invokes, many operations/targets | `API_SHARED` | Preserve each configured fact and conditional source pointer; candidate operation contexts remain separate | Branch semantics and runtime selection are not established. |
| `operation-switch` case | `OPERATION_SCOPED` | `EVIDENCED_OPERATION_SCOPED` with exact lower-case method and exact path | Configuration evidence, not runtime usage. |
| No accepted invocation evidence | none | `UNRESOLVED_ROUTING` | Absence is not proof that no backend exists. |

## Options

1. Keep the old conservative model. Shared facts stay only on the API record. This minimizes overclaiming but loses useful candidate context for downstream review.
2. Recommended: use two layers. The factual layer contains `CONFIGURED_API_SHARED`, `EVIDENCED_OPERATION_SCOPED`, exact Task 011 provenance, resolution, policy/action context, and optional exact operation anchors. A separate candidate layer contains `CANDIDATE_INHERITED_CONTEXT`, links to exact method/path inventory anchors, `CANDIDATE_ONLY` certainty, and an explicit denial of proven egress.
3. Attribute every shared invoke to every operation. Reject: this converts configuration context into unsupported operation-egress claims, especially for conditional/multiple-target assemblies.

Facts are Task 011 observation identity, accepted scope, source path/pointer, resolution state, policy position, and exact operation-switch method/path anchors. Candidate associations are possible inheritance from API-shared context. Neither layer proves runtime use.

## Old versus revised

The old Task 014 record safely says `API_LEVEL_ONLY_NOT_PROVEN_OPERATION_EGRESS`, but cannot carry reviewable per-operation candidates. The recommended additive candidate layer retains those associations without placing them in `operation_scoped_backend_evidence`. Exact operation anchors use the source-evidenced lower-case HTTP method plus the exact OpenAPI path; matching is equality, not name or path similarity.
""", encoding="utf-8")

    (OUT / "yaml_variants_options.md").write_text(f"""# YAML representation and variant options

## Index-only profile

- Canonical API groups with multiple root YAML representations: {variants['summary']['canonical_api_groups_with_multiple_root_yaml_representations']}.
- Groups whose representations all have one SHA-256: {variants['summary']['groups_all_representations_same_sha256']}.
- Groups with multiple SHA-256 values: {variants['summary']['groups_with_multiple_sha256_values']}.
- Groups with more than one authoritative API artifact: {variants['summary']['groups_with_multiple_authoritative_api_artifacts']}.
- Representation-count distribution: `{json.dumps(variants['summary']['representation_count_distribution'], sort_keys=True)}`.

This is an estate-wide cheap occurrence/hash profile, not an estate-wide semantic comparison. Targeted parsing compared only the two multi-hash groups. Both are `SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS`: their operation contracts and safe assembly-policy shapes match even though bytes differ. A real conflicting same-ID representation was therefore `NOT_EVIDENCED_IN_SAMPLE`. The committed JSONL retains occurrence IDs, source roles, paths, file hashes, fingerprints, operation counts, and exact method/path anchors.

## Proposed classifications

1. `BYTE_IDENTICAL_DUPLICATE_REPRESENTATIONS`: retain every occurrence as provenance; materialize one structural payload.
2. `SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS`: retain every variant and fingerprint; canonical output may reference one shared structural payload only if the architect approves.
3. `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW`: retain separate variant operation records and provenance; never union, overwrite, or lexically select semantic truth automatically.
4. `COMPETING_AUTHORITATIVE_REPRESENTATIONS`: a source-role conflict requiring review even when structure matches. None occurred in the index profile.

## Options

1. Lexically select the first accepted API YAML. Reject for conflicts because it can silently discard methods, parameters, schemas, or assembly differences.
2. Recommended: canonical API envelope plus retained source variants. Collapse only byte-identical payload storage; preserve equivalent-variant fingerprints; emit per-variant operations and `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW` when fingerprints differ. Do not redefine the Phase 2 canonical ID.
3. Merge all variants. Reject as a default because unioning can invent a contract that no source contains.

The normalized fingerprint includes format, exact method/path, path shape, compact parameter facts, request/response `$ref` values and statuses, and value-free assembly-policy shapes. It does not expand schemas or expose endpoint/credential values. Descriptive presence is recorded separately so text-only differences do not masquerade as contract conflicts.
""", encoding="utf-8")

    (OUT / "architecture_decisions_pending.md").write_text("""# Task 014 architecture decisions pending

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
""", encoding="utf-8")

    examples = "\n".join(
        f"- `{p['apis'][0]['api_name']}` / `{p['apis'][1]['api_name']}`: method/path-shape Jaccard {p['matching_signals']['method_path_shape_jaccard']}; shared backend target is a candidate signal only; status `{p['status']}`."
        for p in pairs
    )
    (OUT / "cross_canonical_similarity_feasibility.md").write_text(f"""# Cross-canonical structural similarity feasibility

Three targeted pairs retain two different canonical IDs and names, exact source paths/hashes, a shared backend-target identity, matching/differing method/path shapes, and schema-reference overlap. They were selected from compact dependency edges and then parsed only at their accepted API sources.

{examples}

These are feasibility examples, not duplicate findings. The only allowed status is `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`. Names were not used as proof. Shared backend alone is insufficient; generic CRUD shapes, shared middleware, versioned facades, protocol/channel differences, and dynamic routing create false positives. Path rewrites, schema aliases, indirect references, and assembly transformations create false negatives. Tasks 015–016 must validate observed and logical functions before any business-semantic conclusion.

```json
{json.dumps(pairs, sort_keys=True, indent=2)}
```
""", encoding="utf-8")


if __name__ == "__main__":
    generate()
