import hashlib
import json
from pathlib import Path

import pytest

from backend_target_resolver import (
    build_resolution_indexes,
    index_catalog_properties,
    resolve_target_expression,
)
from backend_target_resolver.resolver import extract_symbolic_tokens, extract_target_observations


ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
PROPERTIES = ROOT / "staging/config/catalog-properties.json"
TASK_011_EVIDENCE = ROOT / "tests/evidence/task-011"


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _properties(tmp_path: Path, records: list[dict]) -> tuple[list[dict], dict, dict]:
    path = tmp_path / "properties.json"
    _write(path, json.dumps({"catalogProperties": records}))
    return index_catalog_properties(path)


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_catalog_property_structure_exact_lookup_cardinality_and_redaction(tmp_path: Path) -> None:
    records, lookup, summary = _properties(
        tmp_path,
        [
            {"name": "host", "value": "example.internal:8443", "protected": ""},
            {"name": "same", "value": "one", "protected": ""},
            {"name": "same", "value": "one", "protected": ""},
            {"name": "conflict", "value": "one", "protected": ""},
            {"name": "conflict", "value": "two", "protected": ""},
            {"name": "protected", "value": "must-not-persist", "protected": "true"},
            {"name": "client-secret", "value": "must-also-not-persist", "protected": ""},
        ],
    )
    assert summary["catalog_property_record_count"] == 7
    assert lookup["host"][0]["lookup_cardinality"] == "unique_exact_value"
    assert {item["lookup_cardinality"] for item in lookup["same"]} == {"repeated_same_value"}
    assert {item["lookup_cardinality"] for item in lookup["conflict"]} == {"conflicting_multiple_values"}
    assert lookup["protected"][0]["safe_value"] is None
    assert lookup["client-secret"][0]["safe_value"] is None
    serialized = json.dumps(records)
    assert "must-not-persist" not in serialized
    assert "must-also-not-persist" not in serialized


def test_symbolic_resolution_missing_conflict_protected_runtime_static_and_multiple(tmp_path: Path) -> None:
    _, lookup, _ = _properties(
        tmp_path,
        [
            {"name": "host", "value": "example.internal:8443", "protected": ""},
            {"name": "path", "value": "/v1/items", "protected": ""},
            {"name": "conflict", "value": "one", "protected": ""},
            {"name": "conflict", "value": "two", "protected": ""},
            {"name": "protected", "value": "hidden", "protected": True},
        ],
    )
    assert extract_symbolic_tokens("$(host)$(path)?x=$(host)") == ["host", "path"]
    resolved = resolve_target_expression("$(host)/health", lookup)
    assert resolved["target_classification"] == "CATALOG_PROPERTY_RESOLVED"
    assert resolved["resolved_safe_target_expression"] == "example.internal:8443/health"
    multiple = resolve_target_expression("$(host)$(path)", lookup)
    assert multiple["resolved_safe_target_expression"] == "example.internal:8443/v1/items"
    assert resolve_target_expression("$(missing)/x", lookup)["resolution_reason"] == "unresolved_due_to_missing_catalog_property"
    assert resolve_target_expression("$(conflict)/x", lookup)["resolution_status"] == "AMBIGUOUS"
    assert resolve_target_expression("$(protected)/x", lookup)["resolution_reason"] == "unresolved_due_to_protected_catalog_property_value"
    runtime = resolve_target_expression("$(request.path)", lookup)
    assert runtime["target_classification"] == "RUNTIME_PARAMETERIZED"
    mixed = resolve_target_expression("$(host)$(missing)", lookup)
    assert mixed["target_classification"] == "MIXED_PARAMETERIZED"
    static = resolve_target_expression("https://service.invalid/v1", lookup)
    assert static["target_classification"] == "STATIC_LITERAL"
    secret_url = resolve_target_expression("https://user:password@service.invalid/x?token=value", lookup)
    assert "password" not in secret_url["original_safe_target_expression"]
    assert "token=value" not in secret_url["original_safe_target_expression"]


def test_varied_invoke_shapes_and_explicit_operation_scope() -> None:
    document = {
        "assembly": {
            "execute": [
                {"invoke": {"title": "shared", "verb": "GET", "target-url": "$(host)/shared"}},
                {
                    "operation-switch": {
                        "case": [
                            {
                                "operations": [{"verb": "post", "path": "/items", "operationId": "create"}],
                                "execute": [
                                    {"invoke": {"title": "scoped", "backend-type": "detect", "target_url": "$(host)/items"}}
                                ],
                            }
                        ]
                    }
                },
            ]
        }
    }
    observations = extract_target_observations(document)
    assert len(observations) == 2
    assert {item["invoke_shape"] for item in observations} == {"invoke.target-url", "invoke.target_url"}
    scoped = next(item for item in observations if item["operation_scope"])
    assert scoped["operation_scope"] == [{"verb": "post", "path": "/items", "operation_id": "create"}]
    assert scoped["backend_type"] == "detect"


def _synthetic_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(
        root / "staging/config/catalog-properties.json",
        json.dumps({"catalogProperties": [{"name": "host", "value": "service.invalid:8443", "protected": ""}]}),
    )
    _write(root / "staging/apis/a.yaml", "x-ibm-configuration:\n  assembly:\n    execute:\n    - invoke:\n        title: A\n        verb: GET\n        target-url: $(host)/a\n")
    _write(root / "staging/apis/b.yaml", "x-ibm-configuration:\n  assembly:\n    execute:\n    - invoke:\n        title: B\n        verb: POST\n        target-url: https://literal.invalid/b\n")
    identities = []
    for name in ("a", "b"):
        identities.append(
            {
                "canonical_identity_record_id": f"api-{name}",
                "canonical_object_type": "api_artifact",
                "name": name,
                "version": "1.0.0",
                "source_evidence": [{"source_relative_path": f"staging/apis/{name}.yaml"}],
            }
        )
    phase2 = root / "indexes/apic_identity_resolution.json"
    _write(phase2, json.dumps({"canonical_identity_records": identities}))
    return root


def test_cache_cold_warm_selective_source_and_property_invalidation(tmp_path: Path) -> None:
    root = _synthetic_root(tmp_path)
    cold = build_resolution_indexes(root)
    cold_property = (root / "indexes/catalog_properties.jsonl").read_bytes()
    cold_targets = (root / "indexes/backend_target_resolution.jsonl").read_bytes()
    assert cold["cache"]["files_parsed"] == 2
    assert cold["cache"]["resolution_cache_misses"] == 2

    warm = build_resolution_indexes(root)
    assert warm["cache"]["files_parsed"] == 0
    assert warm["cache"]["resolution_cache_hits"] == 2
    assert cold_targets == (root / "indexes/backend_target_resolution.jsonl").read_bytes()

    with (root / "staging/apis/a.yaml").open("a", encoding="utf-8") as stream:
        stream.write("# source hash change\n")
    source_changed = build_resolution_indexes(root)
    assert source_changed["cache"]["files_parsed"] == 1
    assert source_changed["cache"]["resolution_cache_hits"] == 1
    assert source_changed["cache"]["resolution_cache_misses"] == 1

    properties_path = root / "staging/config/catalog-properties.json"
    _write(properties_path, json.dumps({"catalogProperties": [{"name": "host", "value": "service-two.invalid:8443", "protected": ""}]}))
    property_changed = build_resolution_indexes(root)
    assert property_changed["cache"]["files_parsed"] == 0
    assert property_changed["cache"]["parsed_source_cache_hits"] == 2
    assert property_changed["cache"]["resolution_cache_misses"] == 2
    assert cold_property != (root / "indexes/catalog_properties.jsonl").read_bytes()

    uncached_root = _synthetic_root(tmp_path / "uncached")
    uncached = build_resolution_indexes(uncached_root)
    cached_again = build_resolution_indexes(uncached_root)
    assert uncached["output"]["property_index_sha256"] == cached_again["output"]["property_index_sha256"]
    assert uncached["output"]["target_index_sha256"] == cached_again["output"]["target_index_sha256"]


@pytest.mark.skipif(
    not PHASE2.is_file() or not PROPERTIES.is_file(),
    reason="local accepted Phase 4 evidence is required",
)
def test_full_corpus_outputs_are_complete_redacted_and_frozen_inputs_unchanged(tmp_path: Path) -> None:
    frozen_paths = [
        ROOT / "indexes/relationship_index.jsonl",
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_adjacency.jsonl",
    ]
    frozen_before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen_paths}
    staging_before = _tree_hashes(ROOT / "staging")
    result = build_resolution_indexes(
        ROOT,
        property_index_path=tmp_path / "catalog_properties.jsonl",
        target_index_path=tmp_path / "backend_target_resolution.jsonl",
        cache_path=tmp_path / "cache.sqlite3",
    )
    assert result["target_summary"]["total_canonical_apis"] == 2036
    assert result["target_summary"]["apis_inspected"] == 2036
    assert result["target_summary"]["total_target_observations"] == 2334
    assert result["target_summary"]["apis_with_target_observations"] == 1978
    assert result["target_summary"]["apis_with_no_explicit_target_observation"] == 58
    assert result["property_summary"]["catalog_property_record_count"] == 326
    assert json.loads((TASK_011_EVIDENCE / "target_resolution_summary.json").read_text())["total_canonical_apis"] == 2036

    output_bytes = (tmp_path / "catalog_properties.jsonl").read_bytes() + (tmp_path / "backend_target_resolution.jsonl").read_bytes() + (tmp_path / "cache.sqlite3").read_bytes()
    sensitive_values: list[bytes] = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive_values.append(item[field].encode())
    raw_properties = json.loads(PROPERTIES.read_text())["catalogProperties"]
    for item in raw_properties:
        if "secret" in str(item.get("name", "")).casefold() and isinstance(item.get("value"), str):
            sensitive_values.append(item["value"].encode())
    assert sensitive_values
    assert all(value not in output_bytes for value in sensitive_values)
    assert frozen_before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen_paths}
    assert staging_before == _tree_hashes(ROOT / "staging")
