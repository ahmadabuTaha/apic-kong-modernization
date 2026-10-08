from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from semantic_inventory import build_full_inventory, cache_decision, compare_candidate_pair, operation_contract
from semantic_inventory.full_inventory import CACHE_SCHEMA_VERSION, EXTRACTOR_VERSION, _build_payload


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-014/full-extraction"
LEFT = "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e"
RIGHT = "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb"


def _cached(source: str = "source-a", dependency: str = "dependency-a", version: str = EXTRACTOR_VERSION) -> dict:
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "extractor_version": version,
        "source_fingerprint": source,
        "dependency_fingerprint": dependency,
        "api_record": {},
        "operation_records": [],
    }


def test_cache_reason_taxonomy_and_one_file_change_fixture(tmp_path: Path) -> None:
    source = tmp_path / "api.yaml"
    source.write_text("swagger: '2.0'\npaths: {}\n", encoding="utf-8")
    first = hashlib.sha256(source.read_bytes()).hexdigest()
    assert cache_decision(None, source_fingerprint=first, dependency_fingerprint="d") == "MISS"
    cached = _cached(source=first, dependency="d")
    assert cache_decision(cached, source_fingerprint=first, dependency_fingerprint="d") == "HIT"
    source.write_text("swagger: '2.0'\npaths: {/changed: {}}\n", encoding="utf-8")
    changed = hashlib.sha256(source.read_bytes()).hexdigest()
    assert cache_decision(cached, source_fingerprint=changed, dependency_fingerprint="d") == "INVALIDATED_SOURCE_CHANGE"
    assert cache_decision(cached, source_fingerprint=first, dependency_fingerprint="changed") == "INVALIDATED_DEPENDENCY_CHANGE"
    assert cache_decision(_cached(source=first, dependency="d", version="old"), source_fingerprint=first, dependency_fingerprint="d") == "INVALIDATED_EXTRACTOR_CHANGE"
    partial = _cached(source=first, dependency="d")
    partial.pop("api_record")
    assert cache_decision(partial, source_fingerprint=first, dependency_fingerprint="d") == "INVALIDATED_PARTIAL_CACHE"


def test_local_schema_shape_uses_structure_not_reference_label() -> None:
    document = {
        "swagger": "2.0",
        "definitions": {
            "One": {"type": "object", "properties": {"value": {"type": "string"}}},
            "Two": {"type": "object", "properties": {"value": {"type": "integer"}}},
        },
        "paths": {
            "/one": {"post": {"parameters": [{"name": "body", "in": "body", "schema": {"$ref": "#/definitions/One"}}], "responses": {"200": {"schema": {"$ref": "#/definitions/One"}}}}},
            "/two": {"post": {"parameters": [{"name": "body", "in": "body", "schema": {"$ref": "#/definitions/Two"}}], "responses": {"200": {"schema": {"$ref": "#/definitions/Two"}}}}},
        },
    }
    one = operation_contract(document, "/one", "POST")
    two = operation_contract(document, "/two", "POST")
    assert one["request"]["content"][0]["schema_shape_sha256"] != two["request"]["content"][0]["schema_shape_sha256"]
    assert one["responses"][0]["content"][0]["schema_shape_sha256"] != two["responses"][0]["content"][0]["schema_shape_sha256"]


def test_registry_and_unsupported_format_states_are_explicit(tmp_path: Path) -> None:
    identity = {
        "canonical_identity_record_id": "api:test",
        "canonical_object_type": "api_artifact",
        "name": "test",
        "authoritative_artifact_occurrence_ids": ["occurrence:test"],
        "contributing_extracted_record_ids": ["occurrence:test"],
        "source_evidence": [],
    }
    api, operations, status = _build_payload(tmp_path, identity, [], [], [], [])
    assert status == "REGISTRY_ONLY"
    assert operations == []
    assert api["routing_state"] == "UNRESOLVED_ROUTING"
    source = tmp_path / "unsupported.yaml"
    source.write_text("info: {title: unsupported}\npaths: {}\n", encoding="utf-8")
    representation = {
        "occurrence_id": "occurrence:test",
        "source_path": "unsupported.yaml",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_role": "AUTHORITATIVE_API_ARTIFACT",
    }
    api, operations, status = _build_payload(tmp_path, identity, [representation], [], [], [])
    assert status == "UNSUPPORTED_FORMAT"
    assert operations == []
    assert api["parser_coverage_status"] == "UNSUPPORTED_DOCUMENT_FORMAT"


def test_full_inventory_warm_run_coverage_determinism_backend_and_v2_comparison(tmp_path: Path) -> None:
    frozen = [
        ROOT / "indexes/apic_identity_resolution.json",
        ROOT / "indexes/relationship_index.jsonl",
        ROOT / "indexes/backend_target_resolution.jsonl",
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_dependency_nodes.jsonl",
        ROOT / "indexes/codegraph_dependency_edges.jsonl",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    result = build_full_inventory(
        ROOT,
        api_path=tmp_path / "api.jsonl",
        operation_path=tmp_path / "operation.jsonl",
        candidate_path=tmp_path / "candidates.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )
    coverage = result["manifest"]["coverage"]
    assert coverage["accepted_canonical_api_count"] == coverage["api_inventory_record_count"] == 2036
    assert coverage["source_backed_api_count"] == 2000
    assert coverage["registry_only_api_count"] == 36
    assert coverage["operation_inventory_record_count"] == coverage["unique_operation_id_count"] == 2414
    assert coverage["unresolved_product_location_occurrence_count"] == 113
    assert result["manifest"]["cache_events"] == {"HIT": 2000, "REGISTRY_ONLY": 36}
    assert any(value["source_variant_classification"] == "SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS" for value in result["api_records"])
    assert all(not value.get("runtime_usage_proven", False) for operation in result["operation_records"] for value in operation["configured_backend_facts"] + operation["candidate_inherited_backend_context"])
    pair = compare_candidate_pair(result, LEFT, RIGHT)
    assert pair["status"] == "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION"
    assert len(pair["operation_comparisons"]) == 1
    comparison = pair["operation_comparisons"][0]
    assert comparison["request_contract"]["state"] == "DIFFERENT"
    assert comparison["response_contract"]["state"] == "DIFFERENT"
    assert comparison["method_path"]["state"] == "EQUAL"
    assert comparison["backend_target_ids"]["state"] == "EQUAL"
    assert comparison["backend_target_paths"]["state"] == "MISSING_EVIDENCE"
    assert comparison["backend_configuration"]["state"] == "DIFFERENT"
    assert pair["version"]["state"] == "DIFFERENT"
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    first = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    again = build_full_inventory(
        ROOT,
        api_path=tmp_path / "api.jsonl",
        operation_path=tmp_path / "operation.jsonl",
        candidate_path=tmp_path / "candidates.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )
    assert first == {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    assert again["manifest"]["outputs"] == result["manifest"]["outputs"]


def test_full_outputs_do_not_contain_source_credentials() -> None:
    payload = (ROOT / "indexes/semantic_api_inventory.jsonl").read_bytes() + (ROOT / "indexes/semantic_operation_inventory.jsonl").read_bytes()
    sensitive = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive.append(item[field].encode())
    assert sensitive
    assert all(value not in payload for value in sensitive)
    assert b"http://" not in payload.lower()
    assert b"https://" not in payload.lower()


def test_full_evidence_generator_is_deterministic_and_redacted() -> None:
    subprocess.run([str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_full_evidence.py")], cwd=ROOT, check=True)
    first = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run([str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_full_evidence.py")], cwd=ROOT, check=True)
    assert first == {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in EVIDENCE.iterdir() if path.is_file()}
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)
    comparison = json.loads((EVIDENCE / "v2_request_response_backend_comparison.json").read_text())
    assert comparison["status"] == "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION"
