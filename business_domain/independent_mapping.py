from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import yaml


RULES_VERSION = "task018d-independent-source-driven-mapping-v1"
EXPECTED_OPERATIONS = 2414
EXPECTED_APIS = 2036

DOMAINS = (
    "Establishment", "Contracts", "Visa", "WorkForce", "Work Permit", "Payment",
    "Occupation", "Nitaqat", "Certificate", "Common", "TIP", "User Management", "Notification",
)

INPUTS = {
    "qiwa_csv": Path("neo4j/csv/Qiwa_Modules_Services.csv"),
    "operations": Path("indexes/semantic_operation_inventory.jsonl"),
    "apis": Path("indexes/semantic_api_inventory.jsonl"),
    "observed_functions": Path("indexes/observed_function_inventory.jsonl"),
    "backends": Path("indexes/backend_target_resolution.jsonl"),
    "catalog_properties": Path("indexes/catalog_properties.jsonl"),
    "codegraph_edges": Path("indexes/codegraph_dependency_edges.jsonl"),
    "identity": Path("indexes/apic_identity_resolution.json"),
    "relationships": Path("indexes/relationship_index.jsonl"),
}

OUTPUT_FILES = {
    "crosswalk": "qiwa_module_domain_crosswalk.csv",
    "operations": "operation_domain_distribution.csv",
    "branches": "operation_invocation_branches.csv",
    "matches": "apic_qiwa_match_evidence.csv",
    "summary": "domain_distribution_summary.csv",
    "reuse": "shared_component_reuse.csv",
    "tip": "tip_exposure_inventory.csv",
    "ambiguous": "ambiguous_operations.csv",
    "unmatched": "unmatched_operations.csv",
    "zero_apis": "zero_operation_apis.csv",
    "manifest": "manifest.json",
    "reviewer": "reviewer_explanation.md",
}

# Literal source module -> (candidate domain, status, EA basis, review reason).
# This table is derived only from CURRENT_TASKS Task 018D section 3.
MODULE_RULES: dict[str, tuple[str, str, str, str]] = {
    "EFM": ("Establishment", "EA_EXPLICIT_MODULE_MAPPING", "D01: EFM", ""),
    "Establishment logo": ("Establishment", "MODULE_ALIAS_SUPPORTED", "D01: Establishment Logo", "case-only source spelling variance"),
    "Establishment Loc": ("Establishment", "MODULE_ALIAS_SUPPORTED", "D01: Establishment Location", "abbreviated source spelling"),
    "Proactive Awareness": ("Establishment", "EA_EXPLICIT_MODULE_MAPPING", "D01: Proactive Awareness", ""),
    "Contract Mgmt": ("Contracts", "MODULE_ALIAS_SUPPORTED", "D02: Contract Management", "abbreviated source spelling"),
    "Training Contract": ("Contracts", "MODULE_ALIAS_SUPPORTED", "D02: Training Contracts", "singular source spelling"),
    "Visa Mgmt": ("Visa", "EA_FAMILY_RULE_SUPPORTED", "D03: all evidenced Visa modules", "implementation module is broader than named visa subfamilies"),
    "ET": ("WorkForce", "MODULE_ALIAS_SUPPORTED", "D04: Employee Transfer (ET)", "EA-supplied acronym"),
    "End Of Service Reward": ("WorkForce", "EA_EXPLICIT_MODULE_MAPPING", "D04: End of Service Reward", ""),
    "Absense Mgmt": ("WorkForce", "MODULE_ALIAS_SUPPORTED", "D04: Absence Management", "source typo and abbreviation preserved"),
    "Training Indicators": ("WorkForce", "MODULE_ALIAS_SUPPORTED", "D04: Training Indicator", "plural source spelling"),
    "LMH": ("WorkForce", "MODULE_ALIAS_SUPPORTED", "D04: LMH Engine", "EA-supplied acronym"),
    "Work Permit": ("Work Permit", "EA_EXPLICIT_MODULE_MAPPING", "D05: Work Permit lifecycle", ""),
    "Payment": ("Payment", "EA_EXPLICIT_MODULE_MAPPING", "D06: reusable Payment capability", "domain-specific transactions still require service review"),
    "Occupation Mgmt": ("Occupation", "MODULE_ALIAS_SUPPORTED", "D07: Occupation Management", "abbreviated source spelling"),
    "Change Occupation": ("Occupation", "EA_EXPLICIT_MODULE_MAPPING", "D07: Change Occupation", ""),
    "Nitaqat": ("Nitaqat", "EA_EXPLICIT_MODULE_MAPPING", "D08: Nitaqat", ""),
    "Salary Certificate": ("Certificate", "EA_EXPLICIT_MODULE_MAPPING", "D09: Salary Certificate", ""),
    "Work Policy": ("Certificate", "MODULE_MAPPING_REVIEW_REQUIRED", "D09 names Work Policy Certificate", "module may be broader than certificate ownership"),
    "Wage Protection": ("Certificate", "MODULE_MAPPING_REVIEW_REQUIRED", "D09 names Wage Protection Certificate", "module may be broader than certificate ownership"),
    "Common": ("Common", "EA_EXPLICIT_MODULE_MAPPING", "D10: shared platform functionality", "component-level reuse rule remains separate"),
    "TIP": ("TIP", "MODULE_MAPPING_REVIEW_REQUIRED", "D11: TIP exposure scope", "TIP exposure must not overwrite business ownership"),
    "User Mgmt": ("User Management", "MODULE_ALIAS_SUPPORTED", "D12: User Management", "abbreviated source spelling"),
    "Notification": ("Notification", "EA_EXPLICIT_MODULE_MAPPING", "D13: Notification", ""),
    "Capptions": ("Common", "MODULE_MAPPING_REVIEW_REQUIRED", "D10 shared utility family candidate", "source spelling and ownership need EA review"),
    "Data Portal": ("Common", "MODULE_MAPPING_REVIEW_REQUIRED", "D10 shared platform family candidate", "portal does not prove Common ownership"),
    "Decease Mgmt": ("", "MODULE_MAPPING_UNRESOLVED", "no exact EA module rule", "requires owner decision"),
    "LO": ("", "MODULE_MAPPING_UNRESOLVED", "no exact EA module rule", "Labor Office may be exposure/consumer rather than owner"),
    "MOFA": ("", "MODULE_MAPPING_UNRESOLVED", "no exact EA module rule", "external organization does not establish business ownership"),
    "Work in Saudi": ("WorkForce", "MODULE_MAPPING_REVIEW_REQUIRED", "D04 worker/laborer family candidate", "source module responsibility is not explicit"),
}

SERVICE_OWNERSHIP = {
    "submitoccupationcorrectionrequest": ("Occupation", "D07 explicit service ownership anchor"),
    "getgosicontractslist": ("Contracts", "D02 explicit service ownership anchor"),
}

STRONG_MAPPING_STATUSES = {
    "EA_EXPLICIT_MODULE_MAPPING", "EA_EXPLICIT_SERVICE_OWNERSHIP",
    "EA_FAMILY_RULE_SUPPORTED", "MODULE_ALIAS_SUPPORTED",
}

TEST_OUTCOMES = {
    "focused": "9 passed",
    "repository": "147 passed, 1 sandbox loopback failure, 5 known missing-fixture setup errors; isolated loopback rerun 1 passed; permitted suite excluding only tests/test_profiler.py 146 passed",
    "known_baseline": "tests/fixtures/repository_profile/staging is absent from worktree/HEAD; five Phase 0 setup errors remain frozen and separate",
}


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def _jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    payload = "\x1f".join(str(value) for value in values)
    return f"{prefix}:sha256:{hashlib.sha256(payload.encode()).hexdigest()}"


def _joined(values: Iterable[str | None]) -> str:
    return "|".join(sorted({str(value) for value in values if value not in (None, "")}))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_qiwa(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = {"ID", "Service_Name", "Type", "Parent_Service", "Service_Normalized", "Module_Name"}
        if missing := required - set(headers):
            raise ValueError(f"QIWA CSV missing columns: {sorted(missing)}")
        return [{key: value or "" for key, value in row.items()} for row in reader], headers


def build_module_crosswalk(qiwa_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    modules = sorted({row["Module_Name"] for row in qiwa_rows})
    missing_rules = set(modules) - set(MODULE_RULES)
    extra_rules = set(MODULE_RULES) - set(modules)
    if missing_rules or extra_rules:
        raise ValueError(f"module rule closure mismatch missing={sorted(missing_rules)} extra={sorted(extra_rules)}")
    result = []
    for module in modules:
        domain, status, basis, reason = MODULE_RULES[module]
        result.append({
            "source_qiwa_module": module,
            "normalized_discovery_key": normalize(module),
            "candidate_enterprise_business_domain": domain,
            "mapping_status": status,
            "ea_anchor_or_family_rule": basis,
            "evidence_pointer": "codex/comm/CURRENT_TASKS.md#3-enterprise-architects-13-classification-areas--exactly-as-supplied",
            "alias_or_conflict": reason,
            "review_reason": reason if status in {"MODULE_MAPPING_REVIEW_REQUIRED", "MODULE_MAPPING_UNRESOLVED"} else "",
            "enterprise_domain_ratified": "false",
        })
    return result


def _host(value: str) -> str:
    parsed = urlsplit(value if "://" in value else f"//{value}")
    return parsed.hostname or ""


def enrich_backend(observation: dict[str, Any], properties: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = dict(observation)
    resolved_host = item.get("normalized_host_or_value_key") or ""
    missing_nonruntime = False
    if not resolved_host:
        hosts: set[str] = set()
        for lookup in item.get("property_lookup_results", []):
            token = lookup.get("symbolic_property_name")
            if lookup.get("lookup_status") == "RESOLVED":
                for record_id in lookup.get("property_record_ids", []):
                    record = properties.get(record_id)
                    if record and record.get("value_classification") == "SAFE_NON_SECRET":
                        if candidate := _host(record.get("safe_value", "")):
                            hosts.add(candidate)
            elif token not in set(item.get("runtime_parameter_tokens", [])):
                missing_nonruntime = True
        if len(hosts) == 1:
            resolved_host = next(iter(hosts))
    item["_resolved_host"] = resolved_host
    item["_missing_nonruntime"] = missing_nonruntime
    if resolved_host:
        item["_platform"] = "ACE_BACKEND" if "ace" in resolved_host.casefold() else "EXTERNAL_VIA_DATAPOWER"
        if missing_nonruntime:
            item["_target_resolution"] = "UNRESOLVED"
        elif item.get("runtime_parameter_tokens"):
            item["_target_resolution"] = "PARTIALLY_RESOLVED_DYNAMIC_PATH"
        else:
            item["_target_resolution"] = "FULLY_RESOLVED"
    else:
        item["_platform"] = "PLATFORM_UNRESOLVED"
        item["_target_resolution"] = "UNRESOLVED"
    return item


def _pointer_parts(pointer: str) -> list[str]:
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def _at_pointer(document: Any, parts: list[str]) -> Any:
    node = document
    for part in parts:
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _condition_metadata(root: Path, backend: dict[str, Any], cache: dict[str, tuple[dict[str, Any], str]]) -> dict[str, str]:
    pointer = backend["source_pointer"]
    if "/operation-switch/case/" not in pointer and "/switch/case/" not in pointer and "/otherwise/" not in pointer:
        return {"selector": "", "predicate_sha256": "", "kind": "DIRECT"}
    source_path = backend["source_path"]
    if source_path not in cache:
        path = root / source_path
        cache[source_path] = (yaml.safe_load(path.read_text(encoding="utf-8")), _hash(path))
    document, _ = cache[source_path]
    parts = _pointer_parts(pointer)
    if "/otherwise/" in pointer and "case" not in parts[parts.index("otherwise") + 1:]:
        return {"selector": "DEFAULT_OTHERWISE", "predicate_sha256": "", "kind": "DEFAULT"}
    try:
        case_index = len(parts) - 1 - parts[::-1].index("case")
        case = _at_pointer(document, parts[:case_index + 2])
    except (KeyError, ValueError, IndexError, TypeError):
        return {"selector": "BRANCH_METADATA_UNRESOLVED", "predicate_sha256": "", "kind": "CONDITIONAL"}
    if "operations" in case:
        selectors = [f"{item.get('verb', '').upper()} {item.get('path', '')}" for item in case.get("operations", [])]
        raw = json.dumps(case.get("operations", []), sort_keys=True)
        return {"selector": _joined(selectors), "predicate_sha256": hashlib.sha256(raw.encode()).hexdigest(), "kind": "OPERATION_SWITCH"}
    condition = str(case.get("condition", ""))
    literals = re.findall(r"['\"]([^'\"]+)['\"]", condition)
    selector = _joined(literals) or "CONDITION_PRESENT_WITHOUT_SAFE_LITERAL"
    return {"selector": selector, "predicate_sha256": hashlib.sha256(condition.encode()).hexdigest() if condition else "", "kind": "CONDITIONAL"}


def _condition_parent_keys(selector: str) -> set[str]:
    keys = set()
    for literal in selector.split("|"):
        candidate = re.sub(r"(?:Rq|Rs)$", "", literal, flags=re.IGNORECASE)
        if candidate != literal and normalize(candidate):
            keys.add(normalize(candidate))
    return keys


def _route_tail(path: str | None) -> str:
    parts = [part for part in (path or "").split("/") if part and not part.startswith("$(")]
    return normalize(parts[-1]) if parts else ""


def _operation_matches_scope(facts: dict[str, Any], scopes: list[dict[str, Any]]) -> bool:
    return any(
        str(scope.get("verb", "")).upper() == str(facts["method"]).upper()
        and scope.get("path") == facts["exact_path"]
        for scope in scopes
    )


def classify_identity_outcome(confirmed_parent_keys: set[str], *, contradictory: bool = False) -> str:
    if contradictory:
        return "CONTRADICTORY_EVIDENCE"
    if len(confirmed_parent_keys) > 1:
        return "AMBIGUOUS_IDENTITY"
    if confirmed_parent_keys:
        return "CONFIRMED_EXPLICIT_ROUTE"
    return "NO_MATCH_EVIDENCED"


def _tip_marker(value: str) -> bool:
    text = value.casefold()
    return bool(re.search(r"(^|[-_\s])tip($|[-_\s])", text) or text.startswith("tip") or text.endswith("tip"))


def _tip_context(
    api_id: str,
    api: dict[str, Any],
    related_labels: dict[str, list[tuple[str, str, str]]],
) -> tuple[str, str, str]:
    contexts = related_labels.get(api_id, [])
    explicit = [(kind, object_id, label) for kind, object_id, label in contexts if _tip_marker(label)]
    if explicit:
        return "TIP_EXPOSURE_CONFIRMED", _joined(f"{kind}:{object_id}" for kind, object_id, _ in explicit), "explicit connected Product/Plan/subscription TIP marker"
    combined = f"{api.get('identity_name', '')} {api.get('identity_title', '')}"
    if _tip_marker(combined):
        return "TIP_EXPOSURE_CANDIDATE", f"api:{api_id}", "API label only; no connected TIP context"
    examples = {"ajeer", "musaned", "mowamah", "tabayyan", "qaas", "kayan"}
    candidate = [
        (kind, object_id, label) for kind, object_id, label in contexts
        if "external" in label.casefold() and any(example in label.casefold() for example in examples)
    ]
    if candidate:
        return "TIP_EXPOSURE_CANDIDATE", _joined(f"{kind}:{object_id}" for kind, object_id, _ in candidate), "few-shot offering plus external Product context; TIP not explicit"
    return "TIP_EXPOSURE_NOT_EVIDENCED", "", "no explicit connected TIP exposure evidence"


def _build_tip_relationships(identity: dict[str, Any], relationships: list[dict[str, Any]]) -> dict[str, list[tuple[str, str, str]]]:
    records = {item["canonical_identity_record_id"]: item for item in identity["canonical_identity_records"]}
    result: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    products_to_apis: dict[str, set[str]] = defaultdict(set)
    for relation in relationships:
        if relation["relationship_type"] == "product_contains_api":
            products_to_apis[relation["source_canonical_identity_record_id"]].add(relation["target_canonical_identity_record_id"])
        if relation["relationship_type"] in {"product_contains_api", "plan_entitles_api"}:
            source = records.get(relation["source_canonical_identity_record_id"], {})
            api_id = relation["target_canonical_identity_record_id"]
            label = f"{source.get('name', '')} {source.get('title', '')}".strip()
            result[api_id].append((source.get("canonical_object_type", "context"), relation["source_canonical_identity_record_id"], label))
    for relation in relationships:
        if relation["relationship_type"] != "subscription_targets_product":
            continue
        subscription = records.get(relation["source_canonical_identity_record_id"], {})
        label = f"{subscription.get('name', '')} {subscription.get('title', '')}".strip()
        for api_id in products_to_apis.get(relation["target_canonical_identity_record_id"], set()):
            result[api_id].append(("subscription", relation["source_canonical_identity_record_id"], label))
    return result


def _origin_domain(parent_key: str, rows: list[dict[str, str]], crosswalk: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    if parent_key in SERVICE_OWNERSHIP:
        domain, basis = SERVICE_OWNERSHIP[parent_key]
        return domain, "EA_EXPLICIT_SERVICE_OWNERSHIP", basis
    domains = {
        crosswalk[row["Module_Name"]]["candidate_enterprise_business_domain"]
        for row in rows
        if crosswalk[row["Module_Name"]]["mapping_status"] in STRONG_MAPPING_STATUSES
        and crosswalk[row["Module_Name"]]["candidate_enterprise_business_domain"] != "TIP"
    }
    if len(domains) == 1:
        return next(iter(domains)), "MODULE_MAPPING_SUPPORTED", "unique supported source module domain"
    if len(domains) > 1:
        return "", "OWNERSHIP_AMBIGUOUS", "same normalized Parent occurs in multiple supported domains"
    return "", "OWNERSHIP_UNRESOLVED", "no supported source module ownership"


def _shared_reuse(
    qiwa_rows: list[dict[str, str]],
    parent_rows: dict[str, list[dict[str, str]]],
    crosswalk: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    services: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in qiwa_rows:
        services[normalize(row["Service_Name"])].append(row)
    output = []
    lookup = {}
    for key, rows in sorted(services.items()):
        modules = sorted({row["Module_Name"] for row in rows})
        count = len({normalize(module) for module in modules})
        if not key:
            status = "REUSE_REVIEW_REQUIRED"
        elif count == 1:
            status = "MODULE_LOCAL"
        elif count < 5:
            status = "CROSS_MODULE_SHARED_ORIGIN_RETAINED"
        else:
            status = "COMMON_BY_REUSE_RULE"
        origin, origin_status, basis = _origin_domain(key, parent_rows.get(key, []), crosswalk)
        record = {
            "component_identity": key,
            "original_service_names": _joined(row["Service_Name"] for row in rows),
            "component_types": _joined(row["Type"] for row in rows),
            "origin_business_domain": origin,
            "origin_status": origin_status,
            "origin_evidence": basis,
            "distinct_consuming_module_count": count,
            "consuming_modules": _joined(modules),
            "direct_parent_services": _joined(row["Parent_Service"] for row in rows),
            "direct_csv_row_ids": _joined(row["ID"] for row in rows),
            "transitive_parent_candidate_count": len(parent_rows.get(key, [])),
            "transitive_parent_modules": _joined(row["Module_Name"] for row in parent_rows.get(key, [])),
            "transitive_parent_csv_row_ids": _joined(row["ID"] for row in parent_rows.get(key, [])),
            "shared_reuse_classification": status,
            "common_is_additional_not_owner_replacement": "true" if status == "COMMON_BY_REUSE_RULE" else "false",
            "review_required": "true" if status == "REUSE_REVIEW_REQUIRED" or not origin else "false",
        }
        output.append(record); lookup[key] = record
    return output, lookup


def build_independent_mapping(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir or root / "outputs/task018d"
    paths = {name: root / path for name, path in INPUTS.items()}
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Task 018D input missing ({name}): {path}")

    qiwa_rows, qiwa_headers = _load_qiwa(paths["qiwa_csv"])
    operations = _jsonl(paths["operations"])
    apis = _jsonl(paths["apis"])
    functions = {row["task014_operation_record_id"]: row for row in _jsonl(paths["observed_functions"])}
    properties = {row["catalog_property_record_id"]: row for row in _jsonl(paths["catalog_properties"])}
    backend_rows = [enrich_backend(row, properties) for row in _jsonl(paths["backends"])]
    identity = json.loads(paths["identity"].read_text(encoding="utf-8"))
    relationships = _jsonl(paths["relationships"])
    if len(operations) != EXPECTED_OPERATIONS or len(apis) != EXPECTED_APIS:
        raise ValueError(f"frozen coverage mismatch operations={len(operations)} apis={len(apis)}")

    crosswalk_rows = build_module_crosswalk(qiwa_rows)
    crosswalk = {row["source_qiwa_module"]: row for row in crosswalk_rows}
    parent_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    dp_services: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in qiwa_rows:
        parent_rows[normalize(row["Parent_Service"])].append(row)
        if row["Type"] == "DP":
            dp_services[normalize(row["Service_Name"])].append(row)
    reuse_rows, reuse_lookup = _shared_reuse(qiwa_rows, parent_rows, crosswalk)

    api_by_id = {api["canonical_api_id"]: api for api in apis}
    operations_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        operations_by_api[operation["canonical_api_id"]].append(operation)
    backends_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for backend in backend_rows:
        backends_by_api[backend["canonical_api_id"]].append(backend)
    tip_relationships = _build_tip_relationships(identity, relationships)
    yaml_cache: dict[str, tuple[dict[str, Any], str]] = {}

    branch_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    branch_matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    branches_by_operation: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for api_id in sorted(operations_by_api):
        api = api_by_id[api_id]
        api_operations = sorted(operations_by_api[api_id], key=lambda row: row["semantic_operation_inventory_id"])
        for backend in sorted(backends_by_api.get(api_id, []), key=lambda row: row["target_observation_id"]):
            condition = _condition_metadata(root, backend, yaml_cache)
            scopes = backend.get("operation_scope") or []
            applicable = [
                operation for operation in api_operations
                if not scopes or _operation_matches_scope(functions[operation["semantic_operation_inventory_id"]]["source_facts"], scopes)
            ]
            for operation in applicable:
                op_id = operation["semantic_operation_inventory_id"]
                facts = functions[op_id]["source_facts"]
                if scopes:
                    reachability = "OPERATION_SCOPED_EXPLICIT"
                elif condition["kind"] in {"CONDITIONAL", "DEFAULT"}:
                    reachability = "API_SHARED_CONDITIONAL_CANDIDATE"
                elif "/catch/" in backend["source_pointer"]:
                    reachability = "ERROR_PATH_CANDIDATE"
                elif "/targets/" in backend["source_pointer"]:
                    reachability = "REFERENCED_TARGET_CONTEXT_CANDIDATE"
                else:
                    reachability = "API_SHARED_DIRECT_CONFIGURED"
                branch_id = _stable_id("task018d-invocation-branch", op_id, backend["target_observation_id"])
                branch = {
                    "branch_record_id": branch_id,
                    "canonical_api_id": api_id,
                    "canonical_api_name": api["identity_name"],
                    "operation_record_id": op_id,
                    "operation_id": facts.get("operation_id") or "",
                    "method": facts["method"], "path": facts["exact_path"],
                    "catalog_or_environment": Path(operation["source_provenance"]["source_path"]).parts[2] if len(Path(operation["source_provenance"]["source_path"]).parts) > 2 else "UNSPECIFIED",
                    "branch_kind": condition["kind"], "branch_selector_or_flag": condition["selector"],
                    "branch_predicate_sha256": condition["predicate_sha256"], "branch_reachability": reachability,
                    "invoke_source_pointer": backend["source_pointer"],
                    "backend_observation_id": backend["target_observation_id"],
                    "backend_platform_classification": backend["_platform"],
                    "target_resolution": backend["_target_resolution"],
                    "runtime_parameter_tokens": _joined(backend.get("runtime_parameter_tokens", [])),
                    "matched_parent_candidates": "", "origin_business_domain_candidates": "",
                    "join_category": "NO_MATCH_EVIDENCED", "match_limitations": "",
                    "runtime_egress_proven": "false",
                }

                confirmed_keys = _condition_parent_keys(condition["selector"]) & set(parent_rows)
                route_key = _route_tail(backend.get("normalized_target_path"))
                name_keys = {
                    normalize(facts.get("operation_id")), normalize(api.get("identity_name")), route_key,
                } - {""}
                candidate_keys = (name_keys & set(parent_rows)) - confirmed_keys
                dp_keys = ({route_key} & set(dp_services)) if backend["_platform"] == "EXTERNAL_VIA_DATAPOWER" else set()
                if confirmed_keys:
                    join_category = "CONFIRMED_EXPLICIT_ROUTE"
                elif backend.get("runtime_parameter_tokens") and candidate_keys:
                    join_category = "CANDIDATE_DYNAMIC_ROUTE"
                elif candidate_keys or dp_keys:
                    join_category = "CANDIDATE_NAME_MATCH"
                else:
                    join_category = "NO_MATCH_EVIDENCED"

                candidate_records: list[tuple[str, dict[str, str], str, str]] = []
                for key in sorted(confirmed_keys):
                    for row in sorted(parent_rows[key], key=lambda value: int(value["ID"])):
                        candidate_records.append((key, row, "CONFIRMED_EXPLICIT_ROUTE", "exact switch root flag minus Rq/Rs equals QIWA Parent identity"))
                for key in sorted(candidate_keys):
                    for row in sorted(parent_rows[key], key=lambda value: int(value["ID"])):
                        category = "CANDIDATE_DYNAMIC_ROUTE" if backend.get("runtime_parameter_tokens") else "CANDIDATE_NAME_MATCH"
                        candidate_records.append((key, row, category, "normalized operation/API/route-tail discovery only; CSV has no route evidence"))
                for key in sorted(dp_keys):
                    for row in sorted(dp_services[key], key=lambda value: int(value["ID"])):
                        candidate_records.append((normalize(row["Parent_Service"]), row, "CANDIDATE_NAME_MATCH", "non-ACE route-tail DP correlation; no wrapper or ACE Parent inferred"))

                parents = {row["Parent_Service"].strip() for _, row, _, _ in candidate_records}
                domains = set()
                for parent_key, source_row, category, limitation in candidate_records:
                    origin_domain, origin_status, origin_basis = _origin_domain(parent_key, parent_rows.get(parent_key, [source_row]), crosswalk)
                    if origin_domain:
                        domains.add(origin_domain)
                    evidence = {
                        "match_evidence_id": _stable_id("task018d-match-evidence", branch_id, source_row["ID"], category),
                        "branch_record_id": branch_id, "canonical_api_id": api_id, "operation_record_id": op_id,
                        "operation_id": facts.get("operation_id") or "", "method": facts["method"], "path": facts["exact_path"],
                        "backend_observation_id": backend["target_observation_id"], "invoke_source_pointer": backend["source_pointer"],
                        "branch_selector_or_flag": condition["selector"], "join_category": category,
                        "matching_signal": limitation.split(";", 1)[0], "match_limitations": limitation,
                        "csv_row_id": source_row["ID"], "source_qiwa_module": source_row["Module_Name"],
                        "parent_service": source_row["Parent_Service"], "child_service": source_row["Service_Name"],
                        "child_type": source_row["Type"], "origin_business_domain": origin_domain,
                        "origin_status": origin_status, "origin_evidence": origin_basis,
                        "backend_platform_classification": backend["_platform"], "target_resolution": backend["_target_resolution"],
                        "apic_source_reference": f"{operation['source_provenance']['source_path']}#{operation['source_provenance']['source_pointer']}",
                        "qiwa_source_reference": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={source_row['ID']}",
                        "runtime_egress_proven": "false",
                    }
                    match_rows.append(evidence); branch_matches[branch_id].append(evidence)
                identity_outcome = classify_identity_outcome(confirmed_keys)
                if identity_outcome == "AMBIGUOUS_IDENTITY":
                    branch["join_category"] = identity_outcome
                    branch["match_limitations"] = "multiple incompatible confirmed Parent identities for one branch"
                else:
                    branch["join_category"] = join_category
                    branch["match_limitations"] = "CSV has no endpoint/route columns; non-explicit matches stay candidates" if join_category != "CONFIRMED_EXPLICIT_ROUTE" else "configured branch evidence, not runtime execution proof"
                branch["matched_parent_candidates"] = _joined(parents)
                branch["origin_business_domain_candidates"] = _joined(domains)
                branch_rows.append(branch); branches_by_operation[op_id].append(branch)

    operation_rows: list[dict[str, Any]] = []
    ambiguous_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []
    tip_rows: list[dict[str, Any]] = []
    for operation in sorted(operations, key=lambda row: row["semantic_operation_inventory_id"]):
        op_id = operation["semantic_operation_inventory_id"]
        api = api_by_id[operation["canonical_api_id"]]
        facts = functions[op_id]["source_facts"]
        branches = branches_by_operation.get(op_id, [])
        confirmed = [match for branch in branches for match in branch_matches[branch["branch_record_id"]] if match["join_category"].startswith("CONFIRMED")]
        all_matches = [match for branch in branches for match in branch_matches[branch["branch_record_id"]]]
        confirmed_domains = {match["origin_business_domain"] for match in confirmed if match["origin_business_domain"] and match["origin_business_domain"] != "TIP"}
        confirmed_parents = {normalize(match["parent_service"]) for match in confirmed}
        true_ambiguous = any(branch["join_category"] in {"AMBIGUOUS_IDENTITY", "CONTRADICTORY_EVIDENCE"} for branch in branches)
        if true_ambiguous:
            match_status = "AMBIGUOUS_IDENTITY"
        elif len({branch["branch_record_id"] for branch in branches if branch["join_category"] == "CONFIRMED_EXPLICIT_ROUTE"}) > 1:
            match_status = "MULTI_BRANCH_CONFIRMED"
        elif confirmed:
            match_status = "CONFIRMED_EXPLICIT_ROUTE"
        elif any(branch["join_category"] == "CANDIDATE_DYNAMIC_ROUTE" for branch in branches):
            match_status = "CANDIDATE_DYNAMIC_ROUTE"
        elif all_matches:
            match_status = "CANDIDATE_NAME_MATCH"
        else:
            match_status = "NO_MATCH_EVIDENCED"
        primary = next(iter(confirmed_domains)) if len(confirmed_domains) == 1 and not true_ambiguous else ""
        platforms = {branch["backend_platform_classification"] for branch in branches}
        resolutions = {branch["target_resolution"] for branch in branches}
        backend_summary = next(iter(platforms)) if len(platforms) == 1 else ("MULTI_PLATFORM_CONFIGURED" if platforms else "PLATFORM_UNRESOLVED")
        resolution_summary = next(iter(resolutions)) if len(resolutions) == 1 else ("MIXED_TARGET_RESOLUTION" if resolutions else "UNRESOLVED")
        modules = {match["source_qiwa_module"] for match in confirmed}
        candidate_domains = {match["origin_business_domain"] for match in all_matches if match["origin_business_domain"]}
        supporting_domains = candidate_domains - ({primary} if primary else set())
        reuse_states = {
            reuse_lookup[normalize(match["child_service"])]["shared_reuse_classification"]
            for match in all_matches if normalize(match["child_service"]) in reuse_lookup
        }
        tip_status, tip_refs, tip_reason = _tip_context(operation["canonical_api_id"], api, tip_relationships)
        review_reasons = []
        if not primary:
            review_reasons.append("NO_SINGLE_EVIDENCED_BUSINESS_OWNER")
        if match_status in {"CANDIDATE_NAME_MATCH", "CANDIDATE_DYNAMIC_ROUTE", "NO_MATCH_EVIDENCED"}:
            review_reasons.append("ADEQUATE_CROSS_SYSTEM_MATCH_MISSING")
        if true_ambiguous:
            review_reasons.append("INCOMPATIBLE_SERVICE_OR_ROUTE_IDENTITY")
        record = {
            "canonical_api_id": operation["canonical_api_id"], "canonical_api_name": api["identity_name"],
            "operation_record_id": op_id, "operation_id": facts.get("operation_id") or "",
            "method": facts["method"], "path": facts["exact_path"],
            "catalog_or_environment": Path(operation["source_provenance"]["source_path"]).parts[2] if len(Path(operation["source_provenance"]["source_path"]).parts) > 2 else "UNSPECIFIED",
            "operation_business_domain_candidate": primary, "origin_modules": _joined(modules),
            "invoked_or_supplementary_domains": _joined(supporting_domains),
            "backend_platform_summary": backend_summary, "target_resolution_summary": resolution_summary,
            "invocation_branch_count": len(branches), "match_and_evidence_status": match_status,
            "confirmed_parent_count": len(confirmed_parents), "candidate_domain_alternatives": _joined(candidate_domains - ({primary} if primary else set())),
            "shared_reuse_classification": _joined(reuse_states) or "NOT_EVIDENCED",
            "tip_exposure_status": tip_status, "tip_exposure_evidence_refs": tip_refs,
            "assignment_status": "PROVISIONAL_EVIDENCED_CANDIDATE" if primary else "UNASSIGNED",
            "unresolved_or_review_reason": _joined(review_reasons), "review_required": "true",
            "runtime_egress_proven": "false", "enterprise_domain_ratified": "false",
        }
        operation_rows.append(record)
        if true_ambiguous:
            ambiguous_rows.append(record)
        if not confirmed:
            unmatched_rows.append(record)
        if tip_status != "TIP_EXPOSURE_NOT_EVIDENCED":
            tip_rows.append({
                "canonical_api_id": operation["canonical_api_id"], "canonical_api_name": api["identity_name"],
                "operation_record_id": op_id, "operation_id": facts.get("operation_id") or "",
                "method": facts["method"], "path": facts["exact_path"],
                "tip_exposure_status": tip_status, "tip_exposure_evidence_refs": tip_refs,
                "tip_exposure_reason": tip_reason, "independent_business_domain_candidate": primary,
                "business_domain_alternatives": _joined(candidate_domains), "multi_channel_preserved": "true",
                "review_required": "true" if tip_status != "TIP_EXPOSURE_CONFIRMED" else "false",
            })

    summary_rows = []
    for domain in DOMAINS:
        primary_rows = [row for row in operation_rows if row["operation_business_domain_candidate"] == domain]
        support_rows = [row for row in operation_rows if domain in row["invoked_or_supplementary_domains"].split("|")]
        summary_rows.append({
            "classification_area": domain, "area_role": "TIP_EXPOSURE_DIMENSION" if domain == "TIP" else "BUSINESS_DOMAIN_CANDIDATE",
            "business_domain_primary_operation_count": len(primary_rows),
            "supporting_operation_count": len(support_rows),
            "common_component_operation_count": sum("COMMON_BY_REUSE_RULE" in row["shared_reuse_classification"] for row in operation_rows) if domain == "Common" else 0,
            "tip_exposure_confirmed_operation_count": sum(row["tip_exposure_status"] == "TIP_EXPOSURE_CONFIRMED" for row in operation_rows) if domain == "TIP" else 0,
            "tip_exposure_candidate_operation_count": sum(row["tip_exposure_status"] == "TIP_EXPOSURE_CANDIDATE" for row in operation_rows) if domain == "TIP" else 0,
            "distinct_primary_canonical_api_count": len({row["canonical_api_id"] for row in primary_rows}),
            "unmapped_operation_count": 0, "ambiguous_operation_count": 0,
        })
    summary_rows.extend([
        {"classification_area": "UNMAPPED", "area_role": "NON_DOMAIN_TOTAL", "business_domain_primary_operation_count": sum(not row["operation_business_domain_candidate"] for row in operation_rows), "supporting_operation_count": 0, "common_component_operation_count": 0, "tip_exposure_confirmed_operation_count": 0, "tip_exposure_candidate_operation_count": 0, "distinct_primary_canonical_api_count": 0, "unmapped_operation_count": len(unmatched_rows), "ambiguous_operation_count": 0},
        {"classification_area": "AMBIGUOUS", "area_role": "NON_DOMAIN_TOTAL", "business_domain_primary_operation_count": 0, "supporting_operation_count": 0, "common_component_operation_count": 0, "tip_exposure_confirmed_operation_count": 0, "tip_exposure_candidate_operation_count": 0, "distinct_primary_canonical_api_count": 0, "unmapped_operation_count": 0, "ambiguous_operation_count": len(ambiguous_rows)},
    ])

    zero_apis = [{
        "canonical_api_id": api["canonical_api_id"], "canonical_api_name": api["identity_name"],
        "api_version": api["identity_version"], "protocol": api["protocol"], "operation_count": api["operation_count"],
        "parser_coverage_status": api["parser_coverage_status"],
        "source_reference": (api.get("accepted_source") or {}).get("source_path", "SOURCE_EVIDENCE_UNAVAILABLE"),
    } for api in sorted(apis, key=lambda row: row["canonical_api_id"]) if not api["operation_record_ids"]]

    tables: dict[str, tuple[list[str], list[dict[str, Any]]]] = {
        "crosswalk": (list(crosswalk_rows[0]), crosswalk_rows),
        "operations": (list(operation_rows[0]), operation_rows),
        "branches": (list(branch_rows[0]), sorted(branch_rows, key=lambda row: (row["operation_record_id"], row["branch_record_id"]))),
        "matches": (list(match_rows[0]) if match_rows else ["match_evidence_id"], sorted(match_rows, key=lambda row: (row["operation_record_id"], row["branch_record_id"], int(row["csv_row_id"])) )),
        "summary": (list(summary_rows[0]), summary_rows),
        "reuse": (list(reuse_rows[0]), reuse_rows),
        "tip": (list(tip_rows[0]) if tip_rows else ["operation_record_id"], sorted(tip_rows, key=lambda row: row["operation_record_id"])),
        "ambiguous": (list(operation_rows[0]), ambiguous_rows),
        "unmatched": (list(operation_rows[0]), unmatched_rows),
        "zero_apis": (list(zero_apis[0]), zero_apis),
    }
    for name, (fields, rows) in tables.items():
        _write_csv(output_dir / OUTPUT_FILES[name], fields, rows)

    duplicate_rows = Counter(tuple(row.get(header, "") for header in qiwa_headers if header != "ID") for row in qiwa_rows)
    manifest = {
        "scope": "TASK018D_INDEPENDENT_SOURCE_DRIVEN_CANDIDATE_MAPPING",
        "rules_version": RULES_VERSION, "stop_gate": "EA_REVIEW_TASK018D",
        "independence": {"task018b_inputs_used": False, "task018c_inputs_used": False, "historical_outcomes_used_as_labels": False},
        "domain_vocabulary": list(DOMAINS),
        "source_inventory": {"path": str(INPUTS["qiwa_csv"]), "sha256": _hash(paths["qiwa_csv"]), "bytes": paths["qiwa_csv"].stat().st_size, "row_count": len(qiwa_rows), "unique_id_count": len({row["ID"] for row in qiwa_rows}), "modules": sorted({row["Module_Name"] for row in qiwa_rows}), "types": dict(sorted(Counter(row["Type"] for row in qiwa_rows).items())), "duplicates_excluding_id": sum(count - 1 for count in duplicate_rows.values() if count > 1), "endpoint_or_url_columns": [header for header in qiwa_headers if "url" in header.casefold() or "endpoint" in header.casefold()]},
        "summary": {
            "operation_count": len(operation_rows), "unique_operation_count": len({row["operation_record_id"] for row in operation_rows}),
            "canonical_api_count": len(apis), "zero_operation_api_count": len(zero_apis),
            "invocation_branch_count": len(branch_rows), "match_evidence_count": len(match_rows),
            "primary_assignment_count": sum(bool(row["operation_business_domain_candidate"]) for row in operation_rows),
            "match_status_counts": dict(sorted(Counter(row["match_and_evidence_status"] for row in operation_rows).items())),
            "branch_platform_counts": dict(sorted(Counter(row["backend_platform_classification"] for row in branch_rows).items())),
            "branch_resolution_counts": dict(sorted(Counter(row["target_resolution"] for row in branch_rows).items())),
            "tip_status_counts": dict(sorted(Counter(row["tip_exposure_status"] for row in operation_rows).items())),
            "ambiguous_operation_count": len(ambiguous_rows), "unmatched_operation_count": len(unmatched_rows),
            "targeted_yaml_file_count": len(yaml_cache), "targeted_yaml_hash_mismatches": sum(_hash(root / source) != next(row["source_sha256"] for row in backend_rows if row["source_path"] == source) for source in yaml_cache),
        },
        "matching_limits": ["QIWA CSV contains no endpoint or route columns", "generic URL segments and names are candidates only", "configured branches do not prove runtime execution", "DP child type does not prove APIC wrapper"],
        "test_outcomes": TEST_OUTCOMES,
        "inputs": {name: {"path": _safe_relative(path, root), "sha256": _hash(path), "bytes": path.stat().st_size} for name, path in sorted(paths.items())},
        "outputs": {},
        "guardrails": {"runtime_egress_inferred": False, "enterprise_domain_ratified": False, "task019_performed": False, "tip_overwrites_business_owner": False, "common_overwrites_origin_owner": False},
    }
    for name in tables:
        path = output_dir / OUTPUT_FILES[name]
        manifest["outputs"][name] = {"path": _safe_relative(path, root), "sha256": _hash(path), "bytes": path.stat().st_size, "record_count": len(tables[name][1])}

    reviewer = f"""# Task 018D reviewer explanation

This is an independent deterministic assessment. Task 018B/018C distributions, joins and labels are not inputs. The 13 EA classification areas are candidates pending Enterprise Architect review; TIP is also reported independently as exposure.

## Reproducible execution

`python -m business_domain.independent_mapping_main`

`pytest -q tests/test_business_domain_independent_mapping.py`

`pytest -q`

## Results

- Operations: {len(operation_rows):,}; canonical APIs: {len(apis):,}; zero-operation APIs: {len(zero_apis):,}.
- Invocation branches: {len(branch_rows):,}; match evidence rows: {len(match_rows):,}.
- Provisional primary candidates: {manifest['summary']['primary_assignment_count']:,}; unmatched: {len(unmatched_rows):,}; true ambiguous: {len(ambiguous_rows):,}.
- TIP confirmed exposure operations: {manifest['summary']['tip_status_counts'].get('TIP_EXPOSURE_CONFIRMED', 0):,}; TIP candidates: {manifest['summary']['tip_status_counts'].get('TIP_EXPOSURE_CANDIDATE', 0):,}.

## Evidence limits and rule application

The QIWA CSV has no route/endpoint column. Exact API names, operation names, generic route tails, shared hosts and module-family names therefore remain candidates. Exact switch message-root identifiers may confirm a configured branch-to-Parent identity; they do not prove runtime execution. EA ownership anchors apply only after a service candidate exists. Common uses distinct consuming modules at thresholds 1, 2–4 and 5+, preserving origin. TIP Product/Plan/subscription evidence never overwrites business ownership. Raw target strings, catalog values and credentials are omitted.

Named anchors are retained in the CSV evidence: SubmitOccupationCorrectionRequest→Occupation and GetGosiContractsList→Contracts ownership override consumption; sendQIWAReports branches retain switch flags separately; UpdateEstablishmentContactAddress, ValidateIssueEstablishingVisas and SubmitWorkPermitRequest remain limited by actual match evidence.

## Test outcomes

- Focused: {TEST_OUTCOMES['focused']}.
- Repository: {TEST_OUTCOMES['repository']}.
- Known baseline: {TEST_OUTCOMES['known_baseline']}.

Final status: **TASK 018D TECHNICAL PASS; STOP AT EA_REVIEW_TASK018D.** No domain is ratified.
"""
    (output_dir / OUTPUT_FILES["reviewer"]).write_text(reviewer, encoding="utf-8")
    reviewer_path = output_dir / OUTPUT_FILES["reviewer"]
    manifest["outputs"]["reviewer"] = {"path": _safe_relative(reviewer_path, root), "sha256": _hash(reviewer_path), "bytes": reviewer_path.stat().st_size}
    (output_dir / OUTPUT_FILES["manifest"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": manifest, "crosswalk": crosswalk_rows, "operations": operation_rows, "branches": branch_rows, "matches": match_rows, "summary": summary_rows, "reuse": reuse_rows, "tip": tip_rows, "ambiguous": ambiguous_rows, "unmatched": unmatched_rows, "zero_apis": zero_apis}
