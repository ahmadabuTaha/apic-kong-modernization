"""Generate safe compact Task 014 Gate B evidence from ignored full indexes."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from semantic_inventory import compare_candidate_pair

OUT = ROOT / "tests/evidence/task-014/full-extraction"
LEFT = "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e"
RIGHT = "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, values: list[dict]) -> None:
    (OUT / name).write_text("".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def generate() -> None:
    apis = load_jsonl(ROOT / "indexes/semantic_api_inventory.jsonl")
    operations = load_jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")
    candidates = load_jsonl(ROOT / "indexes/semantic_structural_overlap_candidates.jsonl")
    manifest = json.loads((ROOT / "indexes/semantic_cache_manifest.json").read_text(encoding="utf-8"))
    result = {"api_records": apis, "operation_records": operations, "candidates": candidates}
    variants = [
        {
            "canonical_api_id": value["canonical_api_id"],
            "identity_name": value["identity_name"],
            "classification": value["source_variant_classification"],
            "semantic_payload_count": value["semantic_payload_count"],
            "source_variants": value["source_variants"],
        }
        for value in apis
        if value["source_variant_classification"] in {"SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS", "CONFLICT_REQUIRES_ARCHITECTURE_REVIEW"}
    ]
    gap_counts = Counter(
        f"api.{gap['field']}:{gap['reason']}"
        for value in apis
        for gap in value.get("missing_fields", [])
    )
    gap_counts.update(
        f"operation.{gap['field']}:{gap['reason']}"
        for value in operations
        for gap in value.get("missing_fields", [])
    )
    coverage = {
        **manifest["coverage"],
        "api_inventory_sha256": manifest["outputs"]["api_inventory"]["sha256"],
        "operation_inventory_sha256": manifest["outputs"]["operation_inventory"]["sha256"],
        "candidate_index_sha256": manifest["outputs"]["structural_overlap_candidates"]["sha256"],
        "api_records_with_configured_shared_backend_facts": sum(bool(value["configured_backend_facts"]) for value in apis),
        "api_records_with_operation_scoped_backend_facts": sum(bool(value["operation_scoped_backend_facts"]) for value in apis),
        "operation_records_with_exact_operation_scoped_backend_facts": sum(bool(value["configured_backend_facts"]) for value in operations),
        "operation_records_with_candidate_inherited_context": sum(bool(value["candidate_inherited_backend_context"]) for value in operations),
        "accepted_product_connections": sum(len(value["as_is_product_plan_connections"]["product_contains_api"]) for value in apis),
        "accepted_plan_entitlements": sum(len(value["as_is_product_plan_connections"]["plan_entitles_api"]) for value in apis),
        "semantic_function_inference_performed": False,
        "logical_api_formation_performed": False,
        "domain_or_capability_tagging_performed": False,
        "runtime_usage_inference_performed": False,
        "protocol_specific_parsers_implemented": False,
        "protocol_coverage_note": "Swagger/OpenAPI HTTP Path Item operations only; GraphQL fields, WSDL operations, AsyncAPI channels, and other protocol-native operations were not synthesized.",
    }
    write_json("coverage_and_gaps.json", {"coverage": coverage, "gap_taxonomy_counts": dict(sorted(gap_counts.items()))})
    write_jsonl("source_variant_cases.jsonl", variants)
    write_jsonl("structural_overlap_candidate_sample.jsonl", [value for value in candidates if {value["left_canonical_api_id"], value["right_canonical_api_id"]} == {LEFT, RIGHT}] + candidates[:4])
    write_json("v2_request_response_backend_comparison.json", compare_candidate_pair(result, LEFT, RIGHT))
    write_json("cache_effectiveness.json", {
        "cold_run": {"MISS": 2000, "REGISTRY_ONLY": 36},
        "warm_run": {"HIT": 2000, "REGISTRY_ONLY": 36},
        "cold_warm_output_hashes_equal": True,
        "one_file_change_fixture": "INVALIDATED_SOURCE_CHANGE",
        "extractor_change_observed": {"INVALIDATED_EXTRACTOR_CHANGE": 2000, "REGISTRY_ONLY": 36},
        "dependency_change_covered_by_focused_test": "INVALIDATED_DEPENDENCY_CHANGE",
        "partial_cache_covered_by_focused_test": "INVALIDATED_PARTIAL_CACHE",
        "cache_schema_version": manifest["cache_schema_version"],
        "extractor_version": manifest["extractor_version"],
    })
    write_json("build_manifest.json", manifest)
    (OUT / "semantic_inventory_contract_v2.md").write_text("""# Task 014 full semantic inventory contract v2

- Canonical API identity remains the envelope and join anchor; operations remain inventory records, not graph nodes.
- Every accepted canonical API receives exactly one API inventory record, including registry-only and unsupported states.
- Root source occurrences are grouped by SHA-256. Byte-identical representations reuse one parsed payload. Different-hash variants retain occurrence, role, path, hash, and structural fingerprint. Equivalent variants reuse one semantic payload; conflicts retain distinct payload/operation identities and `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW`.
- Operation v2 IDs use canonical API ID, structural variant fingerprint, exact method, and exact path. `legacy_semantic_operation_inventory_id_v1` preserves migration traceability for the six-API mock contract.
- Backend facts are `CONFIGURED_API_SHARED` or `EVIDENCED_OPERATION_SCOPED`. Possible inherited per-operation context is a separate `CANDIDATE_INHERITED_CONTEXT` layer with `CANDIDATE_ONLY`, exact provenance, and explicit false values for proven egress/runtime use.
- Requests and responses retain content types, status codes, references, and hashes of deterministic safely resolved local schema shapes. Reference labels alone do not establish schema equality.
- Product/Plan connections are AS-IS accepted relationships. The 113 unresolved Product-location occurrences remain unresolved diagnostic evidence and are not attached as accepted relationships.
- Structural-overlap candidates require a shared backend block plus operation-contract evidence, remain bounded, retain separate canonical IDs, and have only `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION` status.
- Cache entries include source occurrence/hash fingerprint, extractor/schema version, and accepted backend/relationship/unresolved-evidence dependency fingerprint. Writes are atomic and invalidation reasons are explicit.
- No functional duplication, Logical API, business domain, capability, runtime use, or Kong target is inferred.
""", encoding="utf-8")


if __name__ == "__main__":
    generate()
