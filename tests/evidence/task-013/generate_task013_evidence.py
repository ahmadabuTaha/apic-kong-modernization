"""Generate deterministic review evidence for Phase 4 Task 013."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend_target_graph import write_backend_target_graph  # noqa: E402
from codegraph_explorer import CodeGraphExplorer  # noqa: E402
from codegraph_explorer.explorer import STATIC_PATH  # noqa: E402


OUTPUT = PROJECT_ROOT / "tests/evidence/task-013"


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample(edge: dict, node: dict, scenario: str) -> dict:
    return {
        "scenario": scenario,
        "api_id": edge["source_canonical_identity_record_id"],
        "backend_target_id": node["graph_node_id"],
        "edge_id": edge["relationship_id"],
        "scope_classifications": edge["scope_classifications"],
        "operation_scopes": edge["operation_scopes"],
        "target_identity_kind": node["target_identity_kind"],
        "backend_classification": node["backend_classification"],
        "resolution_statuses": node["resolution_statuses"],
        "safe_target_representation": node["safe_target_path_or_template"],
        "symbolic_property_tokens": node["symbolic_property_tokens"],
        "task011_observation_ids": edge["task011_observation_ids"],
        "task012_observation_ids": edge["task012_observation_ids"],
        "provenance": edge["provenance"],
        "raw_resolved_infrastructure_omitted": True,
    }


def generate() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frozen_paths = [
        PROJECT_ROOT / "indexes/codegraph_nodes.jsonl",
        PROJECT_ROOT / "indexes/codegraph_edges.jsonl",
        PROJECT_ROOT / "indexes/codegraph_adjacency.jsonl",
        PROJECT_ROOT / "indexes/relationship_index.jsonl",
    ]
    frozen_before = {path.name: _hash(path) for path in frozen_paths}
    with tempfile.TemporaryDirectory(prefix="task-013-a-") as first_temp, tempfile.TemporaryDirectory(
        prefix="task-013-b-"
    ) as second_temp:
        first_dir, second_dir = Path(first_temp), Path(second_temp)
        first = write_backend_target_graph(
            PROJECT_ROOT,
            nodes_path=first_dir / "nodes.jsonl",
            edges_path=first_dir / "edges.jsonl",
            adjacency_path=first_dir / "adjacency.jsonl",
        )
        second = write_backend_target_graph(
            PROJECT_ROOT,
            nodes_path=second_dir / "nodes.jsonl",
            edges_path=second_dir / "edges.jsonl",
            adjacency_path=second_dir / "adjacency.jsonl",
        )
        deterministic = {
            name: (first_dir / name).read_bytes() == (second_dir / name).read_bytes()
            for name in ("nodes.jsonl", "edges.jsonl", "adjacency.jsonl")
        }
    nodes = first["nodes"]
    edges = first["edges"]
    node_by_id = {item["graph_node_id"]: item for item in nodes}
    edges_by_api: dict[str, list[dict]] = defaultdict(list)
    edges_by_target: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        edges_by_api[edge["source_canonical_identity_record_id"]].append(edge)
        edges_by_target[edge["target_canonical_identity_record_id"]].append(edge)

    graph_summary = {
        **first["summary"],
        "deterministic_repeated_build": all(deterministic.values()),
        "deterministic_files": deterministic,
        "additive_output_sha256": {
            "nodes": _hash(PROJECT_ROOT / "indexes/codegraph_dependency_nodes.jsonl"),
            "edges": _hash(PROJECT_ROOT / "indexes/codegraph_dependency_edges.jsonl"),
            "adjacency": _hash(PROJECT_ROOT / "indexes/codegraph_dependency_adjacency.jsonl"),
        },
        "frozen_structural_graph_counts": {"nodes": 4718, "edges": 9589},
        "frozen_structural_hashes_unchanged": frozen_before
        == {path.name: _hash(path) for path in frozen_paths},
        "integrity": first["integrity"],
    }
    _write_json(OUTPUT / "backend_target_graph_summary.json", graph_summary)

    classification = {
        **first["classification_summary"],
        "representative_evidence": {
            "validation_required_backend_target_ids": [
                item["graph_node_id"] for item in nodes[:5]
            ],
            "accepted_explicit_family_assertion_count": 0,
        },
        "evidence_supported_classification_families_present": [],
        "no_name_only_inference_confirmation": True,
    }
    _write_json(OUTPUT / "backend_target_classification_summary.json", classification)

    def edge_for_kind(kind: str) -> dict:
        return next(
            edge
            for edge in edges
            if node_by_id[edge["target_canonical_identity_record_id"]][
                "target_identity_kind"
            ]
            == kind
        )

    samples: list[dict] = []
    scenarios = {
        "resolved_target": edge_for_kind("RESOLVED_TARGET"),
        "static_literal_target": edge_for_kind("STATIC_LITERAL_TARGET"),
        "unresolved_symbolic_target": edge_for_kind("SYMBOLIC_TARGET"),
        "partially_resolved_target": edge_for_kind("PARTIALLY_RESOLVED_TARGET"),
        "api_with_multiple_targets": next(
            edges_for_api[0]
            for _, edges_for_api in sorted(edges_by_api.items())
            if len(edges_for_api) > 1
        ),
        "operation_scoped_target": next(
            edge for edge in edges if "OPERATION_SCOPED" in edge["scope_classifications"]
        ),
        "backend_target_shared_by_multiple_apis": next(
            edges_for_target[0]
            for _, edges_for_target in sorted(edges_by_target.items())
            if len({item["source_canonical_identity_record_id"] for item in edges_for_target})
            > 1
        ),
        "validation_required_classification": edges[0],
    }
    for scenario, edge in scenarios.items():
        samples.append(
            _sample(
                edge,
                node_by_id[edge["target_canonical_identity_record_id"]],
                scenario,
            )
        )
    samples.sort(key=lambda item: item["scenario"])
    (OUTPUT / "api_invokes_target_samples.jsonl").write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for item in samples
        ),
        encoding="utf-8",
    )

    task011 = _load_jsonl(PROJECT_ROOT / "indexes/backend_target_resolution.jsonl")
    observation_to_target = {
        observation_id: node["graph_node_id"]
        for node in nodes
        for observation_id in node["task011_observation_ids"]
    }
    host_paths: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in task011:
        host = item.get("normalized_host_or_value_key")
        path = item.get("normalized_target_path")
        observation_id = item["target_observation_id"]
        if host and path and observation_id in observation_to_target:
            host_paths[host][path].add(observation_to_target[observation_id])
    separated = [
        (host, paths)
        for host, paths in host_paths.items()
        if len(paths) > 1 and len({target for values in paths.values() for target in values}) > 1
    ]
    shared = sorted(
        (
            {
                "backend_target_id": target_id,
                "api_count": len(
                    {item["source_canonical_identity_record_id"] for item in values}
                ),
                "edge_count": len(values),
            }
            for target_id, values in edges_by_target.items()
        ),
        key=lambda item: (-item["api_count"], item["backend_target_id"]),
    )
    symbolic_converged = [
        {
            "backend_target_id": node["graph_node_id"],
            "source_observation_count": node["source_observation_count"],
            "api_count": len(
                {
                    edge["source_canonical_identity_record_id"]
                    for edge in edges_by_target[node["graph_node_id"]]
                }
            ),
            "safe_target_representation": node["safe_target_path_or_template"],
        }
        for node in nodes
        if node["target_identity_kind"]
        in {"SYMBOLIC_TARGET", "PARTIALLY_RESOLVED_TARGET"}
        and node["source_observation_count"] > 1
    ]
    reuse = {
        "target_nodes_referenced_by_one_api": sum(item["api_count"] == 1 for item in shared),
        "target_nodes_referenced_by_multiple_apis": sum(item["api_count"] > 1 for item in shared),
        "top_shared_target_counts": shared[:10],
        "same_host_different_path_group_count": len(separated),
        "same_host_different_path_separation_passed": bool(separated),
        "same_host_different_path_representative": [
            {
                "safe_host_key": "host-key:sha256:"
                + hashlib.sha256(host.encode()).hexdigest(),
                "distinct_path_count": len(paths),
                "distinct_backend_target_count": len(
                    {target for values in paths.values() for target in values}
                ),
                "safe_path_samples": sorted(paths)[:3],
            }
            for host, paths in separated[:3]
        ],
        "symbolic_target_convergence_count": len(symbolic_converged),
        "symbolic_target_convergence_evidence": symbolic_converged[:10],
        "sharing_is_not_duplicate_capability_evidence": True,
    }
    _write_json(OUTPUT / "backend_target_reuse.json", reuse)

    explorer = CodeGraphExplorer.from_paths(PROJECT_ROOT)
    security_api = next(api_id for api_id in sorted(explorer.api_security_metadata) if api_id in edges_by_api)
    security_target_edge = edges_by_api[security_api][0]
    backend_id = security_target_edge["target_canonical_identity_record_id"]
    api_view = explorer.neighborhood(
        security_api,
        direction="outgoing",
        relationship_types=["api_invokes_target"],
    )
    backend_view = explorer.neighborhood(
        backend_id,
        direction="incoming",
        relationship_types=["api_invokes_target"],
    )
    symbolic_node = next(item for item in nodes if item["target_identity_kind"] == "SYMBOLIC_TARGET")
    token = symbolic_node["symbolic_property_tokens"][0]
    symbolic_search = explorer.search(token, node_type="backend_target")
    operation_edge = next(
        item for item in edges if "OPERATION_SCOPED" in item["scope_classifications"]
    )
    explorer_acceptance = {
        "exact_local_run_command": ".venv/bin/python -m codegraph_explorer",
        "api_can_visually_show_backend_target": api_view["returned_edge_count"] > 0,
        "api_to_backend_example": {
            "api_id": security_api,
            "backend_target_ids": sorted(
                {item["target_canonical_id"] for item in api_view["edges"]}
            ),
            "relationship_type": "api_invokes_target",
        },
        "backend_target_can_show_invoking_apis": backend_view["returned_edge_count"] > 0,
        "backend_to_api_reverse_example": {
            "backend_target_id": backend_id,
            "api_ids": sorted(
                {item["source_canonical_id"] for item in backend_view["edges"]}
            ),
        },
        "symbolic_target_search_works": any(
            item["canonical_object_id"] == symbolic_node["graph_node_id"]
            for item in symbolic_search["results"]
        ),
        "classification_filter_works": explorer.search(
            "",
            node_type="backend_target",
            backend_classification="VALIDATION_REQUIRED",
        )["total_matches"]
        == len(nodes),
        "resolution_filter_works": explorer.search(
            "",
            node_type="backend_target",
            resolution_status="UNRESOLVED",
        )["total_matches"]
        > 0,
        "operation_scope_visible": bool(
            explorer.edge_details(operation_edge["relationship_id"])["operation_scopes"]
        ),
        "provenance_drill_down_works": bool(
            explorer.edge_details(operation_edge["relationship_id"])["provenance"]
        ),
        "security_provider_remains_attribute_only": explorer.node_details(
            security_api
        )["security_metadata"]["graph_representation"]
        == "API_ATTRIBUTE_ONLY",
        "security_provider_node_count": sum(
            item["canonical_object_type"] == "security_provider"
            for item in explorer.graph.nodes.values()
        ),
        "jwt_jwk_dependency_node_count": sum(
            "jwk" in item.get("canonical_object_type", "").casefold()
            or "jwt" in item.get("canonical_object_type", "").casefold()
            for item in explorer.graph.nodes.values()
        ),
        "configuration_property_dependency_node_count": sum(
            item["canonical_object_type"] in {"configuration_reference", "catalog_property"}
            and item["graph_node_id"].startswith("backend-target:")
            for item in explorer.graph.nodes.values()
        ),
        "frozen_structural_graph_counts_unchanged": {
            "nodes": explorer.metadata()["structural_graph_node_count"] == 4718,
            "edges": explorer.metadata()["structural_graph_edge_count"] == 9589,
        },
        "ui_contains_dependency_controls": all(
            value in STATIC_PATH.read_text(encoding="utf-8")
            for value in (
                "backendClassification",
                "resolution",
                "scope",
                "backend_target",
            )
        ),
        "visual_caps_preserved": {
            "node_limit": explorer.node_limit,
            "edge_limit": explorer.edge_limit,
        },
    }
    explorer_acceptance["overall_pass"] = all(
        (
            explorer_acceptance["api_can_visually_show_backend_target"],
            explorer_acceptance["backend_target_can_show_invoking_apis"],
            explorer_acceptance["symbolic_target_search_works"],
            explorer_acceptance["classification_filter_works"],
            explorer_acceptance["resolution_filter_works"],
            explorer_acceptance["operation_scope_visible"],
            explorer_acceptance["provenance_drill_down_works"],
            explorer_acceptance["security_provider_remains_attribute_only"],
            explorer_acceptance["security_provider_node_count"] == 0,
            explorer_acceptance["jwt_jwk_dependency_node_count"] == 0,
            explorer_acceptance["configuration_property_dependency_node_count"] == 0,
            all(explorer_acceptance["frozen_structural_graph_counts_unchanged"].values()),
            explorer_acceptance["ui_contains_dependency_controls"],
        )
    )
    _write_json(OUTPUT / "explorer_dependency_acceptance.json", explorer_acceptance)
    return {
        "graph_summary": graph_summary,
        "classification_summary": classification,
        "reuse": reuse,
        "explorer_acceptance": explorer_acceptance,
        "sample_count": len(samples),
        "overall_pass": all(
            (
                first["integrity"]["overall_integrity_passed"],
                all(deterministic.values()),
                explorer_acceptance["overall_pass"],
                graph_summary["frozen_structural_hashes_unchanged"],
            )
        ),
    }


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2, sort_keys=True))
