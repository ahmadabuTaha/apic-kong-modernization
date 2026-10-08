"""Build an additive backend-target layer without mutating the frozen CodeGraph."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlsplit


DEPENDENCY_NODES_PATH = Path("indexes/codegraph_dependency_nodes.jsonl")
DEPENDENCY_EDGES_PATH = Path("indexes/codegraph_dependency_edges.jsonl")
DEPENDENCY_ADJACENCY_PATH = Path("indexes/codegraph_dependency_adjacency.jsonl")
TASK011_PATH = Path("indexes/backend_target_resolution.jsonl")
TASK012_PATH = Path("indexes/api_dependency_observations.jsonl")
STRUCTURAL_NODES_PATH = Path("indexes/codegraph_nodes.jsonl")

CLASSIFICATIONS = (
    "ACE",
    "BACKEND",
    "EXTERNAL_VIA_DATAPOWER",
    "VALIDATION_REQUIRED",
)
AUTOMATIC_CLASSIFICATION_RULES: list[dict[str, Any]] = []
CLASSIFICATION_REASON = (
    "validation_required_no_accepted_explicit_backend_family_evidence"
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for item in records
        ),
        encoding="utf-8",
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:sha256:{hashlib.sha256(payload.encode()).hexdigest()}"


def _identity_kind(observation: dict[str, Any]) -> str:
    classification = observation["target_classification"]
    if classification == "STATIC_LITERAL":
        return "STATIC_LITERAL_TARGET"
    if observation["resolution_status"] == "RESOLVED":
        return "RESOLVED_TARGET"
    if classification == "MIXED_PARAMETERIZED":
        return "PARTIALLY_RESOLVED_TARGET"
    return "SYMBOLIC_TARGET"


def _query_structure(expression: str | None) -> list[str]:
    if not expression:
        return []
    try:
        query = urlsplit(expression).query
    except ValueError:
        return []
    return sorted({name for name, _ in parse_qsl(query, keep_blank_values=True)})


def _normalized_path(value: str | None) -> str:
    if not value:
        return "/"
    result = re.sub(r"/{2,}", "/", value.strip())
    if not result.startswith("/"):
        result = "/" + result
    return result


def _identity_payload(observation: dict[str, Any]) -> dict[str, Any]:
    kind = _identity_kind(observation)
    if kind in {"RESOLVED_TARGET", "STATIC_LITERAL_TARGET"}:
        expression = (
            observation.get("resolved_safe_target_expression")
            or observation["original_safe_target_expression"]
        )
        return {
            "identity_form": "CONCRETE_TARGET",
            "scheme": (observation.get("normalized_scheme") or "").casefold(),
            "host_or_value_key": (
                observation.get("normalized_host_or_value_key") or ""
            ).casefold(),
            "port": observation.get("normalized_port"),
            "path": _normalized_path(
                observation.get("normalized_target_path")
                or observation.get("target_path_suffix_or_template")
            ),
            "query_parameter_names": _query_structure(expression),
        }
    return {
        "identity_form": kind,
        "expression_structure": observation["original_safe_target_expression"].strip(),
        "symbolic_property_tokens": sorted(
            set(observation.get("symbolic_property_tokens", []))
        ),
        "runtime_parameter_tokens": sorted(
            set(observation.get("runtime_parameter_tokens", []))
        ),
        "path_template": observation.get("target_path_suffix_or_template"),
    }


def _target_key(payload: dict[str, Any]) -> str:
    return _stable_id("backend-target-key", payload)


def _display_template(observation: dict[str, Any], kind: str) -> str:
    if kind in {"SYMBOLIC_TARGET", "PARTIALLY_RESOLVED_TARGET"}:
        return observation["original_safe_target_expression"]
    path = observation.get("normalized_target_path")
    if path:
        return path
    expression = (
        observation.get("resolved_safe_target_expression")
        or observation["original_safe_target_expression"]
    )
    try:
        parsed = urlsplit(expression)
        if parsed.path:
            return parsed.path
    except ValueError:
        pass
    return "[explicit target]"


def _operation_qualifiers(observation: dict[str, Any]) -> list[dict[str, Any]]:
    if observation.get("scope_classification") != "OPERATION_SCOPED":
        return []
    result = []
    for scope in observation.get("operation_scope") or []:
        result.append(
            {
                "method": scope.get("verb"),
                "path": scope.get("path"),
                "operation_id": scope.get("operation_id"),
                "source_pointer": observation["source_pointer"],
                "task011_observation_id": observation["target_observation_id"],
            }
        )
    return result


def _safe_property_results(observation: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "symbolic_property_name": item.get("symbolic_property_name"),
                "lookup_status": item.get("lookup_status"),
                "reason": item.get("reason"),
                "property_record_ids": sorted(item.get("property_record_ids", [])),
            }
            for item in observation.get("property_lookup_results", [])
        ),
        key=lambda item: item["symbolic_property_name"] or "",
    )


def _classify(_observations: list[dict[str, Any]]) -> tuple[str, str]:
    # No accepted input currently carries an explicit backend-family assertion.
    # Hostnames, property tokens, invoke titles, and API names are deliberately
    # insufficient for ACE/BACKEND/EXTERNAL_VIA_DATAPOWER classification.
    return "VALIDATION_REQUIRED", CLASSIFICATION_REASON


def build_backend_target_graph(
    task011_observations: Iterable[dict[str, Any]],
    task012_observations: Iterable[dict[str, Any]],
    structural_nodes: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build deterministic additive nodes, edges, adjacency, and integrity evidence."""

    task011 = list(task011_observations)
    task012 = list(task012_observations)
    structural = list(structural_nodes)
    structural_by_id = {item["graph_node_id"]: item for item in structural}
    task012_by_origin: dict[str, list[str]] = defaultdict(list)
    for item in task012:
        if item.get("observation_class") != "BACKEND_INVOCATION":
            continue
        origin = item.get("originating_accepted_index_record_id")
        if origin:
            task012_by_origin[origin].append(item["dependency_observation_id"])

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    payloads: dict[str, dict[str, Any]] = {}
    excluded_without_explicit_expression = 0
    for observation in task011:
        expression = observation.get("original_safe_target_expression")
        if not isinstance(expression, str) or not expression.strip():
            excluded_without_explicit_expression += 1
            continue
        payload = _identity_payload(observation)
        key = _target_key(payload)
        groups[key].append(observation)
        payloads[key] = payload

    nodes: list[dict[str, Any]] = []
    target_ids: dict[str, str] = {}
    for key in sorted(groups):
        observations = sorted(groups[key], key=lambda item: item["target_observation_id"])
        kinds = {_identity_kind(item) for item in observations}
        kind = (
            "RESOLVED_TARGET"
            if "RESOLVED_TARGET" in kinds
            else "STATIC_LITERAL_TARGET"
            if "STATIC_LITERAL_TARGET" in kinds
            else "PARTIALLY_RESOLVED_TARGET"
            if "PARTIALLY_RESOLVED_TARGET" in kinds
            else "SYMBOLIC_TARGET"
        )
        target_id = _stable_id("backend-target", payloads[key])
        target_ids[key] = target_id
        classification, classification_reason = _classify(observations)
        templates = sorted({_display_template(item, _identity_kind(item)) for item in observations})
        property_tokens = sorted(
            {
                token
                for item in observations
                for token in item.get("symbolic_property_tokens", [])
                if token not in item.get("runtime_parameter_tokens", [])
            }
        )
        runtime_tokens = sorted(
            {
                token
                for item in observations
                for token in item.get("runtime_parameter_tokens", [])
            }
        )
        task011_ids = [item["target_observation_id"] for item in observations]
        task012_ids = sorted(
            {
                dependency_id
                for observation_id in task011_ids
                for dependency_id in task012_by_origin.get(observation_id, [])
            }
        )
        resolution_states = sorted({item["resolution_status"] for item in observations})
        node = {
            "graph_node_id": target_id,
            "canonical_identity_record_id": target_id,
            "canonical_object_type": "backend_target",
            "name": templates[0] if len(templates) == 1 else f"{templates[0]} (+{len(templates)-1})",
            "title": templates[0] if len(templates) == 1 else f"{templates[0]} (+{len(templates)-1})",
            "display_label": templates[0] if len(templates) == 1 else f"{templates[0]} (+{len(templates)-1})",
            "target_identity_kind": kind,
            "safe_normalized_target_key": key,
            "safe_target_path_or_template": templates,
            "symbolic_property_tokens": property_tokens,
            "runtime_context_tokens": runtime_tokens,
            "resolution_statuses": resolution_states,
            "resolution_status": resolution_states[0] if len(resolution_states) == 1 else "MIXED",
            "evidence_state": "EXPLICIT_CONFIGURATION_EVIDENCE",
            "confidence": "HIGH",
            "backend_classification": classification,
            "classification_evidence_reason": classification_reason,
            "source_observation_count": len(observations),
            "task011_observation_ids": task011_ids,
            "task012_observation_ids": task012_ids,
            "provenance": [
                {
                    "task011_observation_id": item["target_observation_id"],
                    "task012_observation_ids": sorted(
                        task012_by_origin.get(item["target_observation_id"], [])
                    ),
                    "source_path": item["source_path"],
                    "source_pointer": item["source_pointer"],
                    "source_sha256": item["source_sha256"],
                }
                for item in observations
            ],
        }
        nodes.append(node)

    edge_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for observation in task011:
        expression = observation.get("original_safe_target_expression")
        if not isinstance(expression, str) or not expression.strip():
            continue
        key = _target_key(_identity_payload(observation))
        edge_groups[(observation["canonical_api_id"], target_ids[key])].append(observation)

    nodes_by_id = {item["graph_node_id"]: item for item in nodes}
    edges: list[dict[str, Any]] = []
    for (api_id, target_id), observations in sorted(edge_groups.items()):
        observations.sort(key=lambda item: item["target_observation_id"])
        edge_id = _stable_id("api-invokes-target", api_id, "api_invokes_target", target_id)
        scopes = sorted({item["scope_classification"] for item in observations})
        task011_ids = [item["target_observation_id"] for item in observations]
        task012_ids = sorted(
            {
                dependency_id
                for observation_id in task011_ids
                for dependency_id in task012_by_origin.get(observation_id, [])
            }
        )
        operation_qualifiers = sorted(
            (
                qualifier
                for item in observations
                for qualifier in _operation_qualifiers(item)
            ),
            key=lambda item: (
                item.get("method") or "",
                item.get("path") or "",
                item["source_pointer"],
                item["task011_observation_id"],
            ),
        )
        edge = {
            "graph_edge_id": edge_id,
            "accepted_relationship_id": edge_id,
            "relationship_id": edge_id,
            "relationship_type": "api_invokes_target",
            "source_canonical_identity_record_id": api_id,
            "source_canonical_object_type": "api_artifact",
            "target_canonical_identity_record_id": target_id,
            "target_canonical_object_type": "backend_target",
            "evidence_state": "EXPLICIT_CONFIGURATION_EVIDENCE",
            "confidence": "HIGH",
            "scope_classifications": scopes,
            "operation_scopes": operation_qualifiers,
            "backend_classification": nodes_by_id[target_id]["backend_classification"],
            "target_identity_kind": nodes_by_id[target_id]["target_identity_kind"],
            "resolution_statuses": nodes_by_id[target_id]["resolution_statuses"],
            "symbolic_property_tokens": sorted(
                {
                    token
                    for item in observations
                    for token in item.get("symbolic_property_tokens", [])
                    if token not in item.get("runtime_parameter_tokens", [])
                }
            ),
            "runtime_context_tokens": sorted(
                {
                    token
                    for item in observations
                    for token in item.get("runtime_parameter_tokens", [])
                }
            ),
            "property_resolution_evidence": [
                json.loads(value)
                for value in sorted(
                    {
                        json.dumps(value, sort_keys=True, separators=(",", ":"))
                        for item in observations
                        for value in _safe_property_results(item)
                    }
                )
            ],
            "task011_observation_ids": task011_ids,
            "task012_observation_ids": task012_ids,
            "source_observation_count": len(observations),
            "provenance": [
                {
                    "task011_observation_id": item["target_observation_id"],
                    "task012_observation_ids": sorted(
                        task012_by_origin.get(item["target_observation_id"], [])
                    ),
                    "source_path": item["source_path"],
                    "source_pointer": item["source_pointer"],
                    "source_sha256": item["source_sha256"],
                    "scope_classification": item["scope_classification"],
                }
                for item in observations
            ],
            "dependency_layer_pointer": {
                "index_path": DEPENDENCY_EDGES_PATH.as_posix(),
                "relationship_id": edge_id,
            },
            "task008_relationship_pointer": {
                "index_path": DEPENDENCY_EDGES_PATH.as_posix(),
                "relationship_id": edge_id,
            },
        }
        edges.append(edge)

    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        outgoing[edge["source_canonical_identity_record_id"]].append(edge["relationship_id"])
        incoming[edge["target_canonical_identity_record_id"]].append(edge["relationship_id"])
    adjacency = [
        {
            "canonical_identity_record_id": node_id,
            "incoming_relationship_ids": sorted(incoming[node_id]),
            "outgoing_relationship_ids": sorted(outgoing[node_id]),
            "backend_classifications": sorted(
                {
                    edge["backend_classification"]
                    for edge in edges
                    if edge["relationship_id"] in incoming[node_id] + outgoing[node_id]
                }
            ),
            "resolution_statuses": sorted(
                {
                    status
                    for edge in edges
                    if edge["relationship_id"] in incoming[node_id] + outgoing[node_id]
                    for status in edge["resolution_statuses"]
                }
            ),
            "scope_classifications": sorted(
                {
                    scope
                    for edge in edges
                    if edge["relationship_id"] in incoming[node_id] + outgoing[node_id]
                    for scope in edge["scope_classifications"]
                }
            ),
        }
        for node_id in sorted(set(outgoing) | set(incoming))
    ]

    edge_ids = [item["relationship_id"] for item in edges]
    missing_api_endpoints = sorted(
        {
            item["source_canonical_identity_record_id"]
            for item in edges
            if item["source_canonical_identity_record_id"] not in structural_by_id
        }
    )
    missing_target_endpoints = sorted(
        {
            item["target_canonical_identity_record_id"]
            for item in edges
            if item["target_canonical_identity_record_id"] not in nodes_by_id
        }
    )
    adjacency_outgoing = sorted(
        edge_id for item in adjacency for edge_id in item["outgoing_relationship_ids"]
    )
    adjacency_incoming = sorted(
        edge_id for item in adjacency for edge_id in item["incoming_relationship_ids"]
    )
    integrity = {
        "accepted_task011_observations_consumed": len(task011),
        "admitted_task011_observations": sum(len(value) for value in groups.values()),
        "excluded_without_explicit_target_expression": excluded_without_explicit_expression,
        "missing_api_endpoints": missing_api_endpoints,
        "missing_target_endpoints": missing_target_endpoints,
        "duplicate_node_ids": len(nodes) - len(nodes_by_id),
        "duplicate_edge_ids": len(edge_ids) - len(set(edge_ids)),
        "adjacency_outgoing_complete": adjacency_outgoing == sorted(edge_ids),
        "adjacency_incoming_complete": adjacency_incoming == sorted(edge_ids),
        "forbidden_node_type_count": sum(
            item["canonical_object_type"] != "backend_target" for item in nodes
        ),
        "forbidden_relationship_type_count": sum(
            item["relationship_type"] != "api_invokes_target" for item in edges
        ),
    }
    integrity["overall_integrity_passed"] = all(
        (
            integrity["accepted_task011_observations_consumed"]
            == integrity["admitted_task011_observations"]
            + integrity["excluded_without_explicit_target_expression"],
            not missing_api_endpoints,
            not missing_target_endpoints,
            integrity["duplicate_node_ids"] == 0,
            integrity["duplicate_edge_ids"] == 0,
            integrity["adjacency_outgoing_complete"],
            integrity["adjacency_incoming_complete"],
            integrity["forbidden_node_type_count"] == 0,
            integrity["forbidden_relationship_type_count"] == 0,
        )
    )

    api_target_counts = Counter(
        item["source_canonical_identity_record_id"] for item in edges
    )
    target_api_sets: dict[str, set[str]] = defaultdict(set)
    for item in edges:
        target_api_sets[item["target_canonical_identity_record_id"]].add(
            item["source_canonical_identity_record_id"]
        )
    identity_counts = Counter(item["target_identity_kind"] for item in nodes)
    classification_counts = Counter(item["backend_classification"] for item in nodes)
    summary = {
        "accepted_task011_backend_observations_consumed": len(task011),
        "observations_excluded_without_explicit_target_expression": excluded_without_explicit_expression,
        "canonical_backend_target_node_count": len(nodes),
        "target_counts_by_identity_kind": {
            kind: identity_counts[kind]
            for kind in (
                "RESOLVED_TARGET",
                "STATIC_LITERAL_TARGET",
                "SYMBOLIC_TARGET",
                "PARTIALLY_RESOLVED_TARGET",
            )
        },
        "canonical_api_invokes_target_edge_count": len(edges),
        "apis_with_at_least_one_backend_edge": len(api_target_counts),
        "apis_with_multiple_backend_targets": sum(value > 1 for value in api_target_counts.values()),
        "backend_targets_shared_by_multiple_apis": sum(
            len(value) > 1 for value in target_api_sets.values()
        ),
        "api_shared_edge_count": sum(
            "API_SHARED" in item["scope_classifications"] for item in edges
        ),
        "operation_scoped_edge_count": sum(
            "OPERATION_SCOPED" in item["scope_classifications"] for item in edges
        ),
        "edges_with_both_scope_classes": sum(
            set(item["scope_classifications"])
            == {"API_SHARED", "OPERATION_SCOPED"}
            for item in edges
        ),
        "missing_orphan_endpoint_count": len(missing_api_endpoints)
        + len(missing_target_endpoints),
        "observation_to_node_convergence_count": len(task011) - len(nodes),
        "observation_to_edge_deduplication_count": len(task011) - len(edges),
        "unresolved_symbolic_node_count": identity_counts["SYMBOLIC_TARGET"],
        "graph_integrity_result": "PASS" if integrity["overall_integrity_passed"] else "FAIL",
    }
    classification_summary = {
        "counts": {kind: classification_counts[kind] for kind in CLASSIFICATIONS},
        "automatic_classification_evidence_rules": AUTOMATIC_CLASSIFICATION_RULES,
        "fallback_rule": CLASSIFICATION_REASON,
        "classification_coverage": {
            "automatically_classified_node_count": len(nodes)
            - classification_counts["VALIDATION_REQUIRED"],
            "validation_required_node_count": classification_counts[
                "VALIDATION_REQUIRED"
            ],
            "automatic_classification_percent": round(
                100
                * (len(nodes) - classification_counts["VALIDATION_REQUIRED"])
                / max(1, len(nodes)),
                6,
            ),
        },
        "name_only_inference_used": False,
        "finding": (
            "Accepted Task 011/012 evidence contains no explicit authoritative "
            "backend-family assertion; host, token, API, and invoke-title names "
            "remain insufficient for automatic family assignment."
        ),
    }
    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "summary": summary,
        "classification_summary": classification_summary,
        "integrity": integrity,
    }


def write_backend_target_graph(
    root: Path,
    *,
    task011_path: Path | None = None,
    task012_path: Path | None = None,
    structural_nodes_path: Path | None = None,
    nodes_path: Path | None = None,
    edges_path: Path | None = None,
    adjacency_path: Path | None = None,
) -> dict[str, Any]:
    task011_path = task011_path or root / TASK011_PATH
    task012_path = task012_path or root / TASK012_PATH
    structural_nodes_path = structural_nodes_path or root / STRUCTURAL_NODES_PATH
    nodes_path = nodes_path or root / DEPENDENCY_NODES_PATH
    edges_path = edges_path or root / DEPENDENCY_EDGES_PATH
    adjacency_path = adjacency_path or root / DEPENDENCY_ADJACENCY_PATH
    result = build_backend_target_graph(
        _load_jsonl(task011_path),
        _load_jsonl(task012_path),
        _load_jsonl(structural_nodes_path),
    )
    _write_jsonl(nodes_path, result["nodes"])
    _write_jsonl(edges_path, result["edges"])
    _write_jsonl(adjacency_path, result["adjacency"])
    result["outputs"] = {
        "nodes": {"path": str(nodes_path), "sha256": _hash_file(nodes_path)},
        "edges": {"path": str(edges_path), "sha256": _hash_file(edges_path)},
        "adjacency": {
            "path": str(adjacency_path),
            "sha256": _hash_file(adjacency_path),
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    result = write_backend_target_graph(args.root.resolve())
    printable = {
        key: value
        for key, value in result.items()
        if key not in {"nodes", "edges", "adjacency"}
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
