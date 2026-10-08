import hashlib
import json
from pathlib import Path

import pytest

from backend_target_graph import build_backend_target_graph, write_backend_target_graph
from codegraph_explorer import CodeGraphExplorer


ROOT = Path(__file__).resolve().parents[1]
TASK011 = ROOT / "indexes/backend_target_resolution.jsonl"
TASK012 = ROOT / "indexes/api_dependency_observations.jsonl"


def _node(identifier: str) -> dict:
    return {
        "graph_node_id": identifier,
        "canonical_identity_record_id": identifier,
        "canonical_object_type": "api_artifact",
        "name": identifier,
        "title": identifier.title(),
        "version": "1.0.0",
    }


def _observation(
    identifier: str,
    api_id: str,
    expression: str | None,
    *,
    resolved: str | None = None,
    host: str | None = None,
    path: str | None = None,
    classification: str = "CATALOG_PROPERTY_RESOLVED",
    scope: list[dict] | None = None,
    tokens: list[str] | None = None,
    runtime: list[str] | None = None,
) -> dict:
    status = "RESOLVED" if resolved is not None or classification == "STATIC_LITERAL" else "UNRESOLVED"
    return {
        "target_observation_id": identifier,
        "canonical_api_id": api_id,
        "api_name": api_id,
        "api_version": "1.0.0",
        "original_safe_target_expression": expression,
        "resolved_safe_target_expression": resolved,
        "normalized_scheme": "https" if host else None,
        "normalized_host_or_value_key": host,
        "normalized_port": 443 if host else None,
        "normalized_target_path": path,
        "target_path_suffix_or_template": path,
        "symbolic_property_tokens": tokens or [],
        "runtime_parameter_tokens": runtime or [],
        "property_lookup_results": [
            {
                "symbolic_property_name": token,
                "lookup_status": "RESOLVED",
                "reason": "exact_catalog_property_match",
                "property_record_ids": [f"property-{token}"],
            }
            for token in tokens or []
            if token not in (runtime or [])
        ],
        "target_classification": classification,
        "resolution_status": status,
        "resolution_reason": (
            "all_catalog_properties_resolved_exactly"
            if status == "RESOLVED"
            else "partially_resolved_target_expression"
            if classification == "MIXED_PARAMETERIZED"
            else "unresolved_due_to_missing_catalog_property"
        ),
        "scope_classification": "OPERATION_SCOPED" if scope else "API_SHARED",
        "operation_scope": scope,
        "evidence_state": "EXPLICIT_CONFIGURATION_EVIDENCE",
        "confidence": "HIGH",
        "source_path": f"staging/apis/{api_id}.yaml",
        "source_pointer": f"/assembly/{identifier}/invoke/target-url",
        "source_sha256": "a" * 64,
    }


def _task012(task011: list[dict]) -> list[dict]:
    return [
        {
            "dependency_observation_id": f"dependency-{item['target_observation_id']}",
            "observation_class": "BACKEND_INVOCATION",
            "canonical_api_id": item["canonical_api_id"],
            "originating_accepted_index_record_id": item["target_observation_id"],
        }
        for item in task011
    ]


def _synthetic() -> tuple[list[dict], list[dict]]:
    observations = [
        _observation(
            "resolved-a",
            "api-a",
            "$(target)/one",
            resolved="https://service.invalid:443/one",
            host="service.invalid",
            path="/one",
            tokens=["target"],
        ),
        _observation(
            "static-equivalent",
            "api-b",
            "https://service.invalid:443/one",
            resolved="https://service.invalid:443/one",
            host="service.invalid",
            path="/one",
            classification="STATIC_LITERAL",
        ),
        _observation(
            "different-path",
            "api-a",
            "https://service.invalid:443/two",
            resolved="https://service.invalid:443/two",
            host="service.invalid",
            path="/two",
            classification="STATIC_LITERAL",
        ),
        _observation(
            "symbolic-one",
            "api-a",
            "$(ace-name-only)/one",
            path="/one",
            classification="CATALOG_PROPERTY_UNRESOLVED",
            tokens=["ace-name-only"],
        ),
        _observation(
            "symbolic-two",
            "api-a",
            "$(ace-name-only)/two",
            path="/two",
            classification="CATALOG_PROPERTY_UNRESOLVED",
            tokens=["ace-name-only"],
        ),
        _observation(
            "partial",
            "api-b",
            "$(target)$(request.path)",
            classification="MIXED_PARAMETERIZED",
            tokens=["target", "request.path"],
            runtime=["request.path"],
        ),
        _observation(
            "operation-one",
            "api-c",
            "https://service.invalid:443/operation",
            resolved="https://service.invalid:443/operation",
            host="service.invalid",
            path="/operation",
            classification="STATIC_LITERAL",
            scope=[{"verb": "get", "path": "/one", "operation_id": "one"}],
        ),
        _observation(
            "operation-two",
            "api-c",
            "https://service.invalid:443/operation",
            resolved="https://service.invalid:443/operation",
            host="service.invalid",
            path="/operation",
            classification="STATIC_LITERAL",
            scope=[{"verb": "post", "path": "/two", "operation_id": "two"}],
        ),
    ]
    return observations, [_node("api-a"), _node("api-b"), _node("api-c")]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_canonicalization_convergence_symbolic_identity_edges_scope_and_classification() -> None:
    observations, structural = _synthetic()
    result = build_backend_target_graph(observations, _task012(observations), structural)
    assert result["integrity"]["overall_integrity_passed"] is True
    assert len(result["nodes"]) == 6
    concrete_one = next(
        item
        for item in result["nodes"]
        if item["safe_target_path_or_template"] == ["/one"]
        and item["target_identity_kind"] == "RESOLVED_TARGET"
    )
    assert concrete_one["source_observation_count"] == 2
    assert len(
        {
            item["graph_node_id"]
            for item in result["nodes"]
            if item["safe_target_path_or_template"] in (["/one"], ["/two"])
            and item["target_identity_kind"] in {"RESOLVED_TARGET", "STATIC_LITERAL_TARGET"}
        }
    ) == 2
    symbolic = [item for item in result["nodes"] if item["target_identity_kind"] == "SYMBOLIC_TARGET"]
    assert len(symbolic) == 2
    assert {tuple(item["safe_target_path_or_template"]) for item in symbolic} == {
        ("$(ace-name-only)/one",),
        ("$(ace-name-only)/two",),
    }
    assert all(item["backend_classification"] == "VALIDATION_REQUIRED" for item in result["nodes"])
    assert result["classification_summary"]["name_only_inference_used"] is False
    assert all(item["canonical_object_type"] == "backend_target" for item in result["nodes"])
    assert all(item["relationship_type"] == "api_invokes_target" for item in result["edges"])
    assert not any(item["canonical_object_type"] in {"operation", "security_provider", "catalog_property"} for item in result["nodes"])
    operation_edge = next(item for item in result["edges"] if len(item["operation_scopes"]) == 2)
    assert [(item["method"], item["path"]) for item in operation_edge["operation_scopes"]] == [
        ("get", "/one"),
        ("post", "/two"),
    ]
    assert operation_edge["source_observation_count"] == 2
    assert len(operation_edge["task011_observation_ids"]) == 2


def test_additive_explorer_api_backend_reverse_search_filters_and_provenance(tmp_path: Path) -> None:
    observations, structural = _synthetic()
    root = tmp_path / "repo"
    _write_jsonl(root / "indexes/codegraph_nodes.jsonl", structural)
    _write_jsonl(root / "indexes/codegraph_edges.jsonl", [])
    _write_jsonl(
        root / "indexes/codegraph_adjacency.jsonl",
        [
            {
                "canonical_identity_record_id": item["graph_node_id"],
                "incoming_relationship_ids": [],
                "outgoing_relationship_ids": [],
            }
            for item in structural
        ],
    )
    _write_jsonl(root / "indexes/relationship_index.jsonl", [])
    _write_jsonl(root / "indexes/backend_target_resolution.jsonl", observations)
    task012 = _task012(observations) + [
        {
            "dependency_observation_id": "security-api-a",
            "observation_class": "SECURITY_PROVIDER",
            "canonical_api_id": "api-a",
            "mechanism_or_policy_name": "oauth2",
            "scheme_or_provider_name": "provider",
            "resolution_status": "UNRESOLVED",
        },
        {
            "dependency_observation_id": "ignored-jwk",
            "observation_class": "UNCLASSIFIED_DEPENDENCY_PATTERN",
            "canonical_api_id": "api-a",
            "mechanism_or_policy_name": "jwt-validate",
            "resolution_status": "UNRESOLVED",
        },
    ]
    _write_jsonl(root / "indexes/api_dependency_observations.jsonl", task012)
    write_backend_target_graph(root)
    explorer = CodeGraphExplorer.from_paths(root)
    metadata = explorer.metadata()
    assert metadata["structural_graph_node_count"] == 3
    assert metadata["dependency_graph_node_count"] == 6
    assert "backend_target" in metadata["approved_node_types"]
    outgoing = explorer.neighborhood(
        "api-a", direction="outgoing", relationship_types=["api_invokes_target"]
    )
    assert outgoing["returned_edge_count"] == 4
    backend_id = outgoing["edges"][0]["target_canonical_id"]
    reverse = explorer.neighborhood(
        backend_id, direction="incoming", relationship_types=["api_invokes_target"]
    )
    assert reverse["returned_edge_count"] >= 1
    assert any(item["canonical_object_id"] == "api-a" for item in reverse["nodes"])
    assert explorer.search("ace-name-only", node_type="backend_target")["total_matches"] == 2
    assert explorer.search(
        "",
        node_type="backend_target",
        backend_classification="VALIDATION_REQUIRED",
        resolution_status="UNRESOLVED",
    )["total_matches"] == 3
    filtered = explorer.neighborhood(
        "api-c",
        direction="outgoing",
        relationship_types=["api_invokes_target"],
        scope_classifications=["OPERATION_SCOPED"],
    )
    assert filtered["returned_edge_count"] == 1
    detail = explorer.edge_details(filtered["edges"][0]["relationship_id"])
    assert len(detail["operation_scopes"]) == 2
    assert detail["task011_observation_ids"] == ["operation-one", "operation-two"]
    assert explorer.node_details("api-a")["security_metadata"]["graph_representation"] == "API_ATTRIBUTE_ONLY"
    assert not any(item["object_type"] in {"security_provider", "catalog_property", "operation"} for item in explorer.search("")["results"])


@pytest.mark.skipif(
    not TASK011.is_file() or not TASK012.is_file(),
    reason="accepted Phase 4 dependency indexes are required",
)
def test_full_corpus_determinism_redaction_and_frozen_integrity(tmp_path: Path) -> None:
    frozen = [
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_adjacency.jsonl",
        ROOT / "indexes/relationship_index.jsonl",
        ROOT / "indexes/backend_target_resolution.jsonl",
        ROOT / "indexes/api_dependency_observations.jsonl",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    staging_before = _tree_hashes(ROOT / "staging")
    first = write_backend_target_graph(
        ROOT,
        nodes_path=tmp_path / "first/nodes.jsonl",
        edges_path=tmp_path / "first/edges.jsonl",
        adjacency_path=tmp_path / "first/adjacency.jsonl",
    )
    second = write_backend_target_graph(
        ROOT,
        nodes_path=tmp_path / "second/nodes.jsonl",
        edges_path=tmp_path / "second/edges.jsonl",
        adjacency_path=tmp_path / "second/adjacency.jsonl",
    )
    assert first["integrity"]["overall_integrity_passed"] is True
    assert first["summary"]["accepted_task011_backend_observations_consumed"] == 2334
    assert first["summary"]["observations_excluded_without_explicit_target_expression"] == 2
    assert first["summary"]["canonical_backend_target_node_count"] == 1480
    assert first["summary"]["canonical_api_invokes_target_edge_count"] == 2307
    assert first["summary"]["target_counts_by_identity_kind"] == {
        "RESOLVED_TARGET": 1091,
        "STATIC_LITERAL_TARGET": 57,
        "SYMBOLIC_TARGET": 68,
        "PARTIALLY_RESOLVED_TARGET": 264,
    }
    assert first["summary"]["missing_orphan_endpoint_count"] == 0
    assert first["classification_summary"]["counts"] == {
        "ACE": 0,
        "BACKEND": 0,
        "EXTERNAL_VIA_DATAPOWER": 0,
        "VALIDATION_REQUIRED": 1480,
    }
    assert first["classification_summary"]["name_only_inference_used"] is False
    assert {
        item["canonical_object_type"] for item in first["nodes"]
    } == {"backend_target"}
    for name in ("nodes.jsonl", "edges.jsonl", "adjacency.jsonl"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    payload = b"".join((tmp_path / "first" / name).read_bytes() for name in ("nodes.jsonl", "edges.jsonl", "adjacency.jsonl"))
    sensitive_values = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive_values.append(item[field].encode())
    assert sensitive_values
    assert all(value not in payload for value in sensitive_values)
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    assert staging_before == _tree_hashes(ROOT / "staging")
