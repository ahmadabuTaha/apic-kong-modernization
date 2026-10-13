from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


RULES_VERSION = "task018c-deterministic-qiwa-module-mapping-v1"
EXPECTED_OPERATION_COUNT = 2414
EXPECTED_API_COUNT = 2036
EXTRA_CANDIDATE_BUCKETS = ("Occupations", "TIP")
MATCHABLE_CHILD_TYPES = {"API-HTTP", "DP"}

INPUTS = {
    "qiwa_csv": Path("neo4j/csv/Qiwa_Modules_Services.csv"),
    "operations": Path("indexes/semantic_operation_inventory.jsonl"),
    "apis": Path("indexes/semantic_api_inventory.jsonl"),
    "observed_functions": Path("indexes/observed_function_inventory.jsonl"),
    "backends": Path("indexes/backend_target_resolution.jsonl"),
    "catalog_properties": Path("indexes/catalog_properties.jsonl"),
    "previous_018b": Path("indexes/task018b_operation_domain_initial_mapping.jsonl"),
    "codegraph_edges": Path("indexes/codegraph_dependency_edges.jsonl"),
}

OUTPUT_NAMES = {
    "distribution": "operation_domain_distribution.csv",
    "summary": "domain_distribution_summary.csv",
    "ambiguous": "ambiguous_operations.csv",
    "evidence": "apic_qiwa_match_evidence.csv",
    "zero_apis": "zero_operation_apis.csv",
    "manifest": "manifest.json",
    "reviewer": "reviewer_explanation.txt",
}

DISTRIBUTION_FIELDS = [
    "canonical_api_id", "canonical_api_name", "operation_record_id", "operation_id",
    "method", "path", "catalog_or_environment", "backend_platform_classification",
    "full_target_resolution", "apic_join_status", "join_tier", "source_qiwa_module",
    "candidate_domain_bucket", "candidate_alternatives", "supporting_modules",
    "matched_parent_service", "matched_child_service", "child_type", "csv_row_ids",
    "evidence_references", "assignment_status", "ambiguity_reason",
    "previous_018b_candidate", "comparison_to_018b", "review_required",
]

EVIDENCE_FIELDS = [
    "canonical_api_id", "operation_record_id", "operation_id", "method", "path",
    "csv_row_id", "source_qiwa_module", "parent_service", "child_service", "child_type",
    "edge_role", "traversal_depth", "matching_signals", "join_tier", "match_qualifier",
    "backend_platform_classification", "full_target_resolution", "apic_source_reference",
    "backend_evidence_reference", "qiwa_source_reference", "runtime_egress_proven",
]


def _jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_identity(value: str | None) -> str:
    """Lossy key for candidate discovery only; original strings stay in outputs."""
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def _route_segments(value: str | None) -> set[str]:
    return {
        normalized
        for segment in (value or "").split("/")
        if (normalized := normalize_identity(segment)) and not segment.startswith("$(")
    }


def _joined(values: Iterable[str | None]) -> str:
    return "|".join(sorted({str(value) for value in values if value not in (None, "")}))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def classify_backend(observations: list[dict[str, Any]]) -> tuple[str, str, str]:
    """Apply the EA host rule independently from full target/path resolution."""
    if not observations:
        return "PLATFORM_UNRESOLVED", "UNRESOLVED", "NO_CONFIGURED_INVOCATION_EVIDENCE"

    resolved = [
        item for item in observations
        if item.get("resolved_host_for_classification") or item.get("normalized_host_or_value_key")
    ]
    unresolved = [
        item for item in observations
        if not (item.get("resolved_host_for_classification") or item.get("normalized_host_or_value_key"))
    ]
    platform_values = {
        "ACE_BACKEND" if "ace" in str(item.get("resolved_host_for_classification") or item["normalized_host_or_value_key"]).casefold()
        else "EXTERNAL_VIA_DATAPOWER"
        for item in resolved
    }
    if len(platform_values) == 1 and not unresolved:
        platform = next(iter(platform_values))
    elif len(platform_values) == 1 and unresolved:
        platform = "PLATFORM_UNRESOLVED"
    elif not platform_values:
        platform = "PLATFORM_UNRESOLVED"
    else:
        platform = "PLATFORM_UNRESOLVED"

    conflict = len(platform_values) > 1 or bool(resolved and unresolved)
    if conflict:
        full = "CONFIGURATION_CONFLICT"
        reason = "RESOLVED_AND_UNRESOLVED_OR_CROSS_PLATFORM_CONFIGURATIONS"
    elif not resolved:
        full = "UNRESOLVED"
        reason = "HOST_OR_PROPERTY_UNRESOLVED"
    elif any(item.get("non_runtime_property_unresolved") for item in resolved):
        full = "UNRESOLVED"
        reason = "HOST_RESOLVED_BUT_NON_RUNTIME_PATH_PROPERTY_UNRESOLVED"
    elif any(item.get("runtime_parameter_tokens") for item in resolved):
        full = "PARTIALLY_RESOLVED_DYNAMIC_PATH"
        reason = "RESOLVED_HOST_WITH_DYNAMIC_PATH_OR_QUERY_REMAINDER"
    else:
        full = "FULLY_RESOLVED"
        reason = "RESOLVED_CONFIGURED_HOST_AND_PATH"
    return platform, full, reason


def _host_from_safe_value(value: str) -> str:
    parsed = urlsplit(value if "://" in value else f"//{value}")
    return parsed.hostname or ""


def _enrich_backend_hosts(
    backend_by_id: dict[str, dict[str, Any]],
    property_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    enriched: dict[str, dict[str, Any]] = {}
    for observation_id, original in backend_by_id.items():
        item = dict(original)
        host = item.get("normalized_host_or_value_key") or ""
        if not host and item.get("runtime_parameter_tokens"):
            property_ids = [
                property_id
                for lookup in item.get("property_lookup_results", [])
                if lookup.get("lookup_status") == "RESOLVED"
                for property_id in lookup.get("property_record_ids", [])
            ]
            hosts = {
                _host_from_safe_value(property_by_id[property_id].get("safe_value", ""))
                for property_id in property_ids
                if property_id in property_by_id
            } - {""}
            if len(hosts) == 1:
                host = next(iter(hosts))
        item["resolved_host_for_classification"] = host
        item["non_runtime_property_unresolved"] = any(
            lookup.get("lookup_status") != "RESOLVED"
            and lookup.get("symbolic_property_name") not in set(item.get("runtime_parameter_tokens", []))
            for lookup in item.get("property_lookup_results", [])
        )
        enriched[observation_id] = item
    return enriched


def _catalog_or_environment(source_path: str) -> str:
    parts = Path(source_path).parts
    try:
        return parts[parts.index("apis") + 1]
    except (ValueError, IndexError):
        return "UNSPECIFIED"


def _comparison(primary: str, previous: str) -> str:
    if primary and previous and primary == previous:
        return "EXACT_LABEL_AGREEMENT"
    if primary and previous:
        return "CHANGED_CANDIDATE_NON_EQUIVALENT_LABELS"
    if primary:
        return "PREVIOUSLY_UNMAPPED_NOW_EVIDENCED"
    if previous:
        return "TASK018C_UNRESOLVED_WITH_018B_BASELINE"
    return "STILL_UNRESOLVED"


def _csv_inventory(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = {"ID", "Service_Name", "Type", "Parent_Service", "Service_Normalized", "Module_Name"}
        missing = required - set(headers)
        if missing:
            raise ValueError(f"QIWA CSV missing required headers: {sorted(missing)}")
        rows = [{key: (value or "") for key, value in row.items()} for row in reader]
    return rows, headers


def _supporting_edges(
    module: str,
    parent: str,
    by_parent: dict[str, list[dict[str, str]]],
    parent_modules: dict[str, set[str]],
    max_depth: int = 2,
) -> tuple[list[tuple[dict[str, str], int]], set[str]]:
    edges: list[tuple[dict[str, str], int]] = []
    supporting: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(normalize_identity(parent), 1)])
    visited = {normalize_identity(parent)}
    while queue:
        parent_key, depth = queue.popleft()
        for row in sorted(by_parent.get(parent_key, []), key=lambda value: int(value["ID"])):
            edges.append((row, depth))
            child_key = normalize_identity(row["Service_Name"])
            if row["Type"] in MATCHABLE_CHILD_TYPES:
                for child_module in parent_modules.get(child_key, set()):
                    if child_module != module:
                        supporting.add(child_module)
            if row["Type"] == "API-HTTP" and child_key in parent_modules and depth < max_depth and child_key not in visited:
                visited.add(child_key)
                queue.append((child_key, depth + 1))
    return edges, supporting


def build_qiwa_mapping(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir or root / "outputs/task018c"
    paths = {name: root / relative for name, relative in INPUTS.items()}
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"required Task 018C input missing ({name}): {path}")

    csv_rows, csv_headers = _csv_inventory(paths["qiwa_csv"])
    qiwa_csv_sha256 = _sha256(paths["qiwa_csv"])
    operations = _jsonl(paths["operations"])
    apis = _jsonl(paths["apis"])
    observed = {row["task014_operation_record_id"]: row for row in _jsonl(paths["observed_functions"])}
    raw_backend_by_id = {row["target_observation_id"]: row for row in _jsonl(paths["backends"])}
    property_by_id = {row["catalog_property_record_id"]: row for row in _jsonl(paths["catalog_properties"])}
    backend_by_id = _enrich_backend_hosts(raw_backend_by_id, property_by_id)
    previous = {row["task014_operation_id"]: row for row in _jsonl(paths["previous_018b"])}

    if len(operations) != EXPECTED_OPERATION_COUNT or len(apis) != EXPECTED_API_COUNT:
        raise ValueError(f"frozen coverage mismatch: operations={len(operations)}, apis={len(apis)}")

    api_by_id = {row["canonical_api_id"]: row for row in apis}
    by_parent: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_service: dict[str, list[dict[str, str]]] = defaultdict(list)
    parent_modules: dict[str, set[str]] = defaultdict(set)
    for row in csv_rows:
        parent_key = normalize_identity(row["Parent_Service"])
        service_key = normalize_identity(row["Service_Name"])
        by_parent[parent_key].append(row)
        parent_modules[parent_key].add(row["Module_Name"])
        if row["Type"] in MATCHABLE_CHILD_TYPES:
            by_service[service_key].append(row)

    distribution: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    operation_candidates: dict[str, set[str]] = defaultdict(set)
    operation_support: dict[str, set[str]] = defaultdict(set)

    for operation in sorted(operations, key=lambda row: row["semantic_operation_inventory_id"]):
        operation_record_id = operation["semantic_operation_inventory_id"]
        function = observed[operation_record_id]
        facts = function["source_facts"]
        api = api_by_id[operation["canonical_api_id"]]
        refs = {
            fact["target_observation_id"]
            for fact in operation.get("configured_backend_facts", []) + operation.get("candidate_inherited_backend_context", [])
        }
        backend_observations = [backend_by_id[ref] for ref in sorted(refs) if ref in backend_by_id]
        platform, full_resolution, platform_reason = classify_backend(backend_observations)

        strong_parent: dict[tuple[str, str], dict[str, Any]] = {}
        strong_dp: list[tuple[dict[str, str], str, str, str]] = []
        op_route_segments = _route_segments(facts.get("exact_path"))
        for backend in backend_observations:
            if not backend.get("resolved_host_for_classification"):
                continue
            backend_ref = backend["target_observation_id"]
            backend_is_ace = "ace" in str(backend["resolved_host_for_classification"]).casefold()
            for key in _route_segments(backend.get("normalized_target_path")) if backend.get("resolution_status") == "RESOLVED" else set():
                if backend_is_ace:
                    for source_row in by_parent.get(key, []):
                        identity = (source_row["Module_Name"], source_row["Parent_Service"])
                        strong_parent[identity] = {
                            "tier": "J1_EXACT_ENDPOINT_OR_ROUTE",
                            "signal": "RESOLVED_ACE_TARGET_ROUTE_SEGMENT_EQUALS_PARENT_SERVICE",
                            "backend_ref": backend_ref,
                            "source_row": source_row,
                        }
                else:
                    for source_row in by_service.get(key, []):
                        if source_row["Type"] == "DP":
                            strong_dp.append((source_row, "J1_EXACT_ENDPOINT_OR_ROUTE", "RESOLVED_EXTERNAL_TARGET_ROUTE_SEGMENT_EQUALS_DP_SERVICE", backend_ref))
            if backend_is_ace and not backend.get("non_runtime_property_unresolved") and "request.path" in backend.get("runtime_parameter_tokens", []):
                for key in op_route_segments:
                    for source_row in by_parent.get(key, []):
                        identity = (source_row["Module_Name"], source_row["Parent_Service"])
                        strong_parent.setdefault(identity, {
                            "tier": "J2_RESOLVED_BACKEND_AND_OPERATION",
                            "signal": "RESOLVED_HOST_DYNAMIC_REQUEST_PATH_AND_OPERATION_ROUTE_EQUALS_PARENT",
                            "backend_ref": backend_ref,
                            "source_row": source_row,
                        })

        name_rows: list[tuple[dict[str, str], str]] = []
        name_keys = {
            normalize_identity(facts.get("operation_id")),
            normalize_identity(api.get("identity_name")),
        } - {""}
        for key in name_keys:
            name_rows.extend((row, "NORMALIZED_OPERATION_OR_API_NAME_EQUALS_PARENT") for row in by_parent.get(key, []))
            name_rows.extend((row, "NORMALIZED_OPERATION_OR_API_NAME_EQUALS_CHILD_SERVICE") for row in by_service.get(key, []))

        strong_identities = sorted(strong_parent)
        strong_modules = {module for module, _ in strong_identities}
        strong_parents = {parent for _, parent in strong_identities}
        primary = ""
        source_module = ""
        alternatives: set[str] = set()
        supporting: set[str] = set()
        matched_parents: set[str] = set()
        matched_children: set[str] = set()
        child_types: set[str] = set()
        csv_ids: set[str] = set()
        evidence_refs: set[str] = set(refs)
        ambiguity_reasons: list[str] = []

        if full_resolution == "CONFIGURATION_CONFLICT":
            join_status, join_tier = "CONTRADICTORY_CONFIGURATION", "JC_CONTRADICTORY"
            alternatives.update(strong_modules)
            alternatives.update(row["Module_Name"] for row, *_ in strong_dp)
            alternatives.update(row["Module_Name"] for row, _ in name_rows)
            ambiguity_reasons.append(platform_reason)
        elif len(strong_modules) == 1 and len(strong_parents) == 1:
            source_module = primary = next(iter(strong_modules))
            join_tier = min((value["tier"] for value in strong_parent.values()), key=lambda value: (0 if value.startswith("J1") else 1, value))
            join_status = "CONFIRMED_ENTRYPOINT"
        elif strong_identities:
            alternatives.update(strong_modules)
            join_status, join_tier = "AMBIGUOUS_ENTRYPOINT", "JX_AMBIGUOUS"
            ambiguity_reasons.append("MULTI_MODULE_AMBIGUOUS" if len(strong_modules) > 1 else "MULTI_PARENT_AMBIGUOUS")
        elif strong_dp:
            alternatives.update(row["Module_Name"] for row, *_ in strong_dp)
            join_status, join_tier = "DP_CORRELATION_CANDIDATE", "J1_EXACT_ENDPOINT_OR_ROUTE"
            ambiguity_reasons.append("DP_BOUNDARY_MATCH_DOES_NOT_PROVE_ENTRYPOINT_OWNERSHIP")
        elif name_rows:
            alternatives.update(row["Module_Name"] for row, _ in name_rows)
            join_status, join_tier = "NAME_ONLY_CANDIDATE", "J3_NAME_ONLY_CANDIDATE"
            ambiguity_reasons.append("NAME_ONLY_NO_AUTHORITATIVE_ROUTE_BRIDGE")
        else:
            join_status, join_tier = "NO_MATCH", "J0_NO_MATCH"
            ambiguity_reasons.append("INSUFFICIENT_CROSS_SYSTEM_EVIDENCE")

        for (module, parent), match in sorted(strong_parent.items()):
            matched_parents.add(parent)
            source_row = match["source_row"]
            csv_ids.add(source_row["ID"])
            evidence.append({
                "canonical_api_id": operation["canonical_api_id"],
                "operation_record_id": operation_record_id,
                "operation_id": facts.get("operation_id") or "",
                "method": facts["method"], "path": facts["exact_path"],
                "csv_row_id": source_row["ID"], "source_qiwa_module": module,
                "parent_service": parent, "child_service": source_row["Service_Name"],
                "child_type": source_row["Type"], "edge_role": "ENTRYPOINT_PARENT_MATCH",
                "traversal_depth": 0, "matching_signals": match["signal"],
                "join_tier": "JC_CONTRADICTORY" if full_resolution == "CONFIGURATION_CONFLICT" else match["tier"],
                "match_qualifier": "PRIMARY_ELIGIBLE_ONLY_IF_UNIQUE_MODULE_AND_PARENT",
                "backend_platform_classification": platform, "full_target_resolution": full_resolution,
                "apic_source_reference": f"{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}",
                "backend_evidence_reference": match["backend_ref"],
                "qiwa_source_reference": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={source_row['ID']}",
                "runtime_egress_proven": "false",
            })
            if primary:
                edges, edge_support = _supporting_edges(module, parent, by_parent, parent_modules)
                supporting.update(edge_support)
                for edge, depth in edges:
                    csv_ids.add(edge["ID"]); matched_children.add(edge["Service_Name"]); child_types.add(edge["Type"])
                    child_is_parent = normalize_identity(edge["Service_Name"]) in parent_modules
                    base_role = "CALLS_PARENT_SERVICE_CANDIDATE" if edge["Type"] == "API-HTTP" and child_is_parent else "USES_COMPONENT_CSV_EDGE"
                    edge_role = base_role if depth == 1 else f"BOUNDED_TRANSITIVE_{base_role}"
                    evidence.append({
                        "canonical_api_id": operation["canonical_api_id"], "operation_record_id": operation_record_id,
                        "operation_id": facts.get("operation_id") or "", "method": facts["method"], "path": facts["exact_path"],
                        "csv_row_id": edge["ID"], "source_qiwa_module": edge["Module_Name"],
                        "parent_service": edge["Parent_Service"], "child_service": edge["Service_Name"],
                        "child_type": edge["Type"], "edge_role": edge_role,
                        "traversal_depth": depth, "matching_signals": "CSV_PARENT_TO_CHILD_EDGE",
                        "join_tier": match["tier"], "match_qualifier": "SUPPORTING_DEPENDENCY_NOT_PRIMARY_OWNERSHIP",
                        "backend_platform_classification": platform, "full_target_resolution": full_resolution,
                        "apic_source_reference": f"{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}",
                        "backend_evidence_reference": match["backend_ref"],
                        "qiwa_source_reference": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={edge['ID']}",
                        "runtime_egress_proven": "false",
                    })

        for source_row, tier, signal, backend_ref in sorted(strong_dp, key=lambda value: int(value[0]["ID"])):
            csv_ids.add(source_row["ID"]); matched_parents.add(source_row["Parent_Service"])
            matched_children.add(source_row["Service_Name"]); child_types.add(source_row["Type"])
            evidence.append({
                "canonical_api_id": operation["canonical_api_id"], "operation_record_id": operation_record_id,
                "operation_id": facts.get("operation_id") or "", "method": facts["method"], "path": facts["exact_path"],
                "csv_row_id": source_row["ID"], "source_qiwa_module": source_row["Module_Name"],
                "parent_service": source_row["Parent_Service"], "child_service": source_row["Service_Name"],
                "child_type": source_row["Type"], "edge_role": "DP_BOUNDARY_CORRELATION", "traversal_depth": 0,
                "matching_signals": signal, "join_tier": tier,
                "match_qualifier": "GROUNDED_DP_CORRELATION_NOT_APIC_WRAPPER_OR_PRIMARY_PROOF",
                "backend_platform_classification": platform, "full_target_resolution": full_resolution,
                "apic_source_reference": f"{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}",
                "backend_evidence_reference": backend_ref,
                "qiwa_source_reference": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={source_row['ID']}",
                "runtime_egress_proven": "false",
            })

        if not strong_identities and not strong_dp:
            seen_name_edges: set[tuple[str, str]] = set()
            for source_row, signal in sorted(name_rows, key=lambda value: (int(value[0]["ID"]), value[1])):
                key = (source_row["ID"], signal)
                if key in seen_name_edges:
                    continue
                seen_name_edges.add(key); csv_ids.add(source_row["ID"])
                matched_parents.add(source_row["Parent_Service"]); matched_children.add(source_row["Service_Name"])
                child_types.add(source_row["Type"])
                evidence.append({
                    "canonical_api_id": operation["canonical_api_id"], "operation_record_id": operation_record_id,
                    "operation_id": facts.get("operation_id") or "", "method": facts["method"], "path": facts["exact_path"],
                    "csv_row_id": source_row["ID"], "source_qiwa_module": source_row["Module_Name"],
                    "parent_service": source_row["Parent_Service"], "child_service": source_row["Service_Name"],
                    "child_type": source_row["Type"], "edge_role": "NAME_ONLY_CANDIDATE", "traversal_depth": 0,
                    "matching_signals": signal, "join_tier": "J3_NAME_ONLY_CANDIDATE",
                    "match_qualifier": "CANDIDATE_ONLY_EXACT_NORMALIZED_NAME_NO_ROUTE_BRIDGE",
                    "backend_platform_classification": platform, "full_target_resolution": full_resolution,
                    "apic_source_reference": f"{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}",
                    "backend_evidence_reference": "", "qiwa_source_reference": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={source_row['ID']}",
                    "runtime_egress_proven": "false",
                })

        alternatives.discard(primary)
        supporting.discard(primary)
        operation_candidates[operation_record_id].update(alternatives)
        operation_support[operation_record_id].update(supporting)
        previous_candidate = (previous.get(operation_record_id, {}).get("domain_assessment", {}).get("proposed_primary") or "")
        if platform == "PLATFORM_UNRESOLVED":
            ambiguity_reasons.append(platform_reason)
        distribution.append({
            "canonical_api_id": operation["canonical_api_id"], "canonical_api_name": api["identity_name"],
            "operation_record_id": operation_record_id, "operation_id": facts.get("operation_id") or "",
            "method": facts["method"], "path": facts["exact_path"],
            "catalog_or_environment": _catalog_or_environment(operation["source_provenance"]["source_path"]),
            "backend_platform_classification": platform, "full_target_resolution": full_resolution,
            "apic_join_status": join_status, "join_tier": join_tier, "source_qiwa_module": source_module,
            "candidate_domain_bucket": primary, "candidate_alternatives": _joined(alternatives),
            "supporting_modules": _joined(supporting), "matched_parent_service": _joined(matched_parents),
            "matched_child_service": _joined(matched_children), "child_type": _joined(child_types),
            "csv_row_ids": _joined(csv_ids),
            "evidence_references": _joined(evidence_refs | {f"QIWA_CSV_SHA256:{qiwa_csv_sha256}"}),
            "assignment_status": "PROVISIONAL_QIWA_MODULE_CANDIDATE" if primary else "UNASSIGNED",
            "ambiguity_reason": _joined(ambiguity_reasons), "previous_018b_candidate": previous_candidate,
            "comparison_to_018b": _comparison(primary, previous_candidate), "review_required": "true",
        })

    evidence.sort(key=lambda row: (
        row["operation_record_id"], int(row["csv_row_id"]), row["edge_role"], row["matching_signals"]
    ))
    ambiguous = [
        row for row in distribution
        if row["assignment_status"] == "UNASSIGNED"
        or row["backend_platform_classification"] == "PLATFORM_UNRESOLVED"
        or row["join_tier"] in {"J3_NAME_ONLY_CANDIDATE", "JX_AMBIGUOUS", "JC_CONTRADICTORY"}
    ]

    csv_modules = sorted({row["Module_Name"] for row in csv_rows})
    buckets = sorted(set(csv_modules) | set(EXTRA_CANDIDATE_BUCKETS))
    summary_rows: list[dict[str, Any]] = []
    for bucket in buckets:
        primary_rows = [row for row in distribution if row["candidate_domain_bucket"] == bucket]
        candidate_rows = [row for row in distribution if bucket in operation_candidates[row["operation_record_id"]]]
        support_rows = [row for row in distribution if bucket in operation_support[row["operation_record_id"]]]
        summary_rows.append({
            "candidate_domain_bucket": bucket,
            "bucket_origin": "QIWA_CSV_AND_EA_NOMINATED_OVERLAP" if bucket == "TIP" else ("QIWA_CSV_MODULE" if bucket in csv_modules else "EA_NOMINATED_ADDITIONAL"),
            "operation_primary_count": len(primary_rows), "candidate_only_count": len(candidate_rows),
            "supporting_only_count": len(support_rows),
            "distinct_canonical_api_count": len({row["canonical_api_id"] for row in primary_rows}),
            "no_match_count": 0,
            "ambiguous_count": sum(1 for row in candidate_rows if row["join_tier"] in {"JX_AMBIGUOUS", "JC_CONTRADICTORY"}),
        })
    unmapped = [row for row in distribution if not row["candidate_domain_bucket"]]
    summary_rows.append({
        "candidate_domain_bucket": "UNMAPPED", "bucket_origin": "OVERALL_NON_DOMAIN_SUMMARY",
        "operation_primary_count": len(unmapped), "candidate_only_count": 0, "supporting_only_count": 0,
        "distinct_canonical_api_count": len({row["canonical_api_id"] for row in unmapped}),
        "no_match_count": sum(row["apic_join_status"] == "NO_MATCH" for row in distribution),
        "ambiguous_count": sum(row["apic_join_status"] in {"AMBIGUOUS_ENTRYPOINT", "CONTRADICTORY_CONFIGURATION"} for row in distribution),
    })

    zero_apis = [
        {
            "canonical_api_id": api["canonical_api_id"], "canonical_api_name": api["identity_name"],
            "api_version": api["identity_version"], "protocol": api["protocol"],
            "operation_count": api["operation_count"], "parser_coverage_status": api["parser_coverage_status"],
            "source_reference": (api.get("accepted_source") or {}).get("source_path", "SOURCE_EVIDENCE_UNAVAILABLE"),
        }
        for api in sorted(apis, key=lambda row: row["canonical_api_id"])
        if not api["operation_record_ids"]
    ]

    _write_csv(output_dir / OUTPUT_NAMES["distribution"], DISTRIBUTION_FIELDS, distribution)
    summary_fields = ["candidate_domain_bucket", "bucket_origin", "operation_primary_count", "candidate_only_count", "supporting_only_count", "distinct_canonical_api_count", "no_match_count", "ambiguous_count"]
    _write_csv(output_dir / OUTPUT_NAMES["summary"], summary_fields, summary_rows)
    _write_csv(output_dir / OUTPUT_NAMES["ambiguous"], DISTRIBUTION_FIELDS, ambiguous)
    _write_csv(output_dir / OUTPUT_NAMES["evidence"], EVIDENCE_FIELDS, evidence)
    _write_csv(output_dir / OUTPUT_NAMES["zero_apis"], ["canonical_api_id", "canonical_api_name", "api_version", "protocol", "operation_count", "parser_coverage_status", "source_reference"], zero_apis)

    duplicate_without_id = Counter(tuple(row.get(header, "") for header in csv_headers if header != "ID") for row in csv_rows)
    manifest: dict[str, Any] = {
        "scope": "TASK018C_DETERMINISTIC_CANDIDATE_MAPPING_ONLY",
        "rules_version": RULES_VERSION,
        "source_inventory": {
            "path": str(INPUTS["qiwa_csv"]), "sha256": qiwa_csv_sha256,
            "bytes": paths["qiwa_csv"].stat().st_size, "encoding": "UTF-8-SIG",
            "headers": csv_headers, "row_count": len(csv_rows), "unique_id_count": len({row["ID"] for row in csv_rows}),
            "distinct_modules": csv_modules, "distinct_types": dict(sorted(Counter(row["Type"] for row in csv_rows).items())),
            "duplicate_rows_excluding_id_count": sum(count - 1 for count in duplicate_without_id.values() if count > 1),
            "endpoint_or_url_columns_present": [header for header in csv_headers if "url" in header.casefold() or "endpoint" in header.casefold()],
        },
        "candidate_buckets": buckets,
        "nominated_bucket_overlap": {"TIP": "ALREADY_PRESENT_AS_LITERAL_CSV_MODULE", "Occupations": "ABSENT_FROM_CSV_RETAINED_AT_ZERO_UNLESS_DIRECTLY_EVIDENCED"},
        "summary": {
            "operation_count": len(distribution), "unique_operation_count": len({row["operation_record_id"] for row in distribution}),
            "canonical_api_count": len(apis), "zero_operation_api_count": len(zero_apis),
            "join_status_counts": dict(sorted(Counter(row["apic_join_status"] for row in distribution).items())),
            "join_tier_counts": dict(sorted(Counter(row["join_tier"] for row in distribution).items())),
            "backend_platform_counts": dict(sorted(Counter(row["backend_platform_classification"] for row in distribution).items())),
            "full_target_resolution_counts": dict(sorted(Counter(row["full_target_resolution"] for row in distribution).items())),
            "primary_assignment_count": sum(bool(row["candidate_domain_bucket"]) for row in distribution),
            "ambiguous_review_row_count": len(ambiguous), "match_evidence_row_count": len(evidence),
            "comparison_to_018b_counts": dict(sorted(Counter(row["comparison_to_018b"] for row in distribution).items())),
        },
        "guardrails": {
            "runtime_egress_proven": False, "enterprise_domain_ratified": False,
            "name_only_promoted_to_primary": False, "dp_match_promoted_to_apic_wrapper": False,
            "task018b_modified": False, "task019_performed": False,
            "neo4j_validation": "NOT_REQUIRED_FOR_DETERMINISTIC_CSV_APIC_MAPPING",
        },
        "inputs": {name: {"path": str(path.relative_to(root)), "sha256": _sha256(path), "bytes": path.stat().st_size} for name, path in sorted(paths.items())},
        "outputs": {},
        "stop_gate": "EA_REVIEW_TASK018C",
    }
    for name in ("distribution", "summary", "ambiguous", "evidence", "zero_apis"):
        path = output_dir / OUTPUT_NAMES[name]
        with path.open(encoding="utf-8", newline="") as handle:
            count = sum(1 for _ in csv.reader(handle)) - 1
        manifest["outputs"][name] = {"path": _display_path(path, root), "sha256": _sha256(path), "bytes": path.stat().st_size, "record_count": count}

    manifest_path = output_dir / OUTPUT_NAMES["manifest"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    explanation = (
        "Task 018C deterministic reviewer note\n"
        "\n"
        "QIWA Module_Name is an AS-IS module proxy, not a ratified enterprise Business Domain. "
        "Primary candidates require a unique exact configured-route-to-parent bridge. Exact normalized names alone remain J3 and unassigned. "
        "DP correlations are boundaries, not proof of an APIC wrapper or ACE journey. Supporting modules come only from bounded CSV Parent-to-Child traversal. "
        "Configured targets do not prove runtime egress. Task 018B remains an independent historical baseline.\n"
        f"\nSee manifest.json for source hashes, coverage, tier counts, limitations, and the EA_REVIEW_TASK018C stop gate.\n"
    )
    (output_dir / OUTPUT_NAMES["reviewer"]).write_text(explanation, encoding="utf-8")
    return {"manifest": manifest, "distribution": distribution, "summary": summary_rows, "ambiguous": ambiguous, "evidence": evidence, "zero_apis": zero_apis}
