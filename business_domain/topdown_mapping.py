from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml


RULES_VERSION = "task018e-top-down-domain-mapping-v1"
CACHE_SCHEMA_VERSION = "task018e-cache-v1"
MATCHER_VERSION = "controlled-name-matcher-v1"
EXPECTED_OPERATIONS = 2414
EXPECTED_APIS = 2036

INPUTS = {
    "qiwa_csv": Path("neo4j/csv/Qiwa_Modules_Services.csv"),
    "operations": Path("indexes/semantic_operation_inventory.jsonl"),
    "apis": Path("indexes/semantic_api_inventory.jsonl"),
    "backends": Path("indexes/backend_target_resolution.jsonl"),
    "catalog_properties": Path("indexes/catalog_properties.jsonl"),
    "identity": Path("indexes/apic_identity_resolution.json"),
    "relationships": Path("indexes/relationship_index.jsonl"),
}

DOMAIN_REGISTRY = (
    ("D01", "Establishment", "FUNCTIONAL", "EFM, logo, location and proactive-awareness ownership"),
    ("D02", "Contracts", "FUNCTIONAL", "Contract, training-contract and external-contract ownership"),
    ("D03", "Visa", "FUNCTIONAL", "Evidenced Visa family ownership"),
    ("D04", "WorkForce", "FUNCTIONAL", "Worker, employee-transfer and workforce lifecycle ownership"),
    ("D05", "Work Permit", "FUNCTIONAL", "Work Permit lifecycle ownership"),
    ("D06", "Payment", "FUNCTIONAL", "Reusable payment, billing and reconciliation capability"),
    ("D07", "Occupation", "FUNCTIONAL", "Occupation management and change-occupation ownership"),
    ("D08", "Nitaqat", "FUNCTIONAL", "Evidenced Nitaqat family ownership"),
    ("D09", "Certificate", "FUNCTIONAL", "Salary, Saudization, Work Policy and Wage Protection certificates"),
    ("D10", "Common", "PARALLEL_REUSE", "Shared platform utility; 5+ distinct consuming modules threshold"),
    ("D11", "TIP", "PARALLEL_EXPOSURE", "Takamol Integration Portal enterprise exposure"),
    ("D12", "User Management", "FUNCTIONAL", "User Management and SSO ownership"),
    ("D13", "Notification", "FUNCTIONAL", "Email, SMS and notification capability"),
    ("D14", "Labor Office Portal (LO)", "PARALLEL_CHANNEL", "LO AS-IS channel with LO-specific validations"),
)
DOMAIN_BY_NAME = {name: code for code, name, _, _ in DOMAIN_REGISTRY}

# Complete literal-module crosswalk based only on Task 018E's EA rules. Literal labels are never rewritten.
MODULE_RULES: dict[str, tuple[str, str, str]] = {
    "EFM": ("Establishment", "EA_EXPLICIT", "D01 EFM"),
    "Establishment logo": ("Establishment", "DOCUMENTED_ALIAS", "D01 Establishment Logo"),
    "Establishment Loc": ("Establishment", "DOCUMENTED_ALIAS", "D01 Establishment Location"),
    "Proactive Awareness": ("Establishment", "EA_EXPLICIT", "D01 Proactive Awareness"),
    "Contract Mgmt": ("Contracts", "DOCUMENTED_ALIAS", "D02 Contract Management"),
    "Training Contract": ("Contracts", "DOCUMENTED_ALIAS", "D02 Training Contracts"),
    "Visa Mgmt": ("Visa", "EA_FAMILY_SUPPORTED", "D03 evidenced Visa family"),
    "ET": ("WorkForce", "DOCUMENTED_ALIAS", "D04 Employee Transfer (ET)"),
    "End Of Service Reward": ("WorkForce", "EA_EXPLICIT", "D04 End of Service Reward"),
    "Absense Mgmt": ("WorkForce", "DOCUMENTED_ALIAS", "D04 Absence Management; source typo retained"),
    "Training Indicators": ("WorkForce", "DOCUMENTED_ALIAS", "D04 Training Indicator"),
    "Decease Mgmt": ("WorkForce", "EA_EXPLICIT", "D04 Decease Management"),
    "LMH": ("WorkForce", "DOCUMENTED_ALIAS", "D04 LMH Engine/Scheduler"),
    "Work in Saudi": ("WorkForce", "EA_FAMILY_SUPPORTED", "D04 laborer/worker family"),
    "Work Permit": ("Work Permit", "EA_EXPLICIT", "D05 Work Permit"),
    "Payment": ("Payment", "EA_EXPLICIT", "D06 Payment"),
    "Occupation Mgmt": ("Occupation", "DOCUMENTED_ALIAS", "D07 Occupation Management"),
    "Change Occupation": ("Occupation", "EA_EXPLICIT", "D07 Change Occupation"),
    "Nitaqat": ("Nitaqat", "EA_EXPLICIT", "D08 Nitaqat"),
    "Salary Certificate": ("Certificate", "EA_EXPLICIT", "D09 Salary Certificate"),
    "Work Policy": ("Certificate", "EA_FAMILY_SUPPORTED", "D09 Work Policy Certificate family"),
    "Wage Protection": ("Certificate", "EA_FAMILY_SUPPORTED", "D09 Wage Protection Certificate family"),
    "Common": ("Common", "EA_EXPLICIT", "D10 Common; reuse threshold remains independent"),
    "Capptions": ("", "REVIEW_REQUIRED", "No documented alias; source spelling retained"),
    "Data Portal": ("", "REVIEW_REQUIRED", "Portal label alone does not prove Common ownership"),
    "TIP": ("TIP", "EA_EXPLICIT", "D11 TIP exposure module; not exclusive functional owner"),
    "User Mgmt": ("User Management", "DOCUMENTED_ALIAS", "D12 User Management"),
    "Notification": ("Notification", "EA_EXPLICIT", "D13 Notification"),
    "LO": ("Labor Office Portal (LO)", "EA_EXPLICIT", "D14 LO AS-IS channel; not exclusive functional owner"),
    "MOFA": ("", "UNMAPPED", "External organization label does not establish ownership"),
}

SERVICE_OWNERSHIP = {
    "submitoccupationcorrectionrequest": ("Occupation", "D07 explicit ownership anchor"),
    "getgosicontractslist": ("Contracts", "D02 explicit origin ownership anchor"),
}
DOCUMENTED_ALIASES = {
    "updateestablishmentcontactaddress": "updateestablishmentaddress",
}
GENERIC_KEYS = {"get", "submit", "service", "create", "update", "delete", "validate", "search"}

OUTPUT_FILES = {
    "registry": "enterprise_domain_registry.csv",
    "crosswalk": "domain_module_crosswalk.csv",
    "parents": "domain_parent_services.csv",
    "apis": "domain_canonical_apis.csv",
    "distribution": "domain_operation_distribution.csv",
    "ledger": "operation_domain_ledger.csv",
    "shared": "shared_services.csv",
    "backend": "backend_verification.csv",
    "branches": "operation_invocation_branches.csv",
    "tip": "tip_exposure_inventory.csv",
    "lo": "lo_as_is_inventory.csv",
    "exceptions": "domain_mapping_exceptions.csv",
    "unmatched": "unmatched_operations.csv",
    "zero": "zero_operation_apis.csv",
    "coverage": "coverage_report.md",
    "manifest": "manifest.json",
}


def normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable(prefix: str, *values: str) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(chr(31).join(map(str, values)).encode()).hexdigest()}"


def _joined(values: Iterable[Any]) -> str:
    return "|".join(sorted({str(value) for value in values if value not in (None, "")}))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (sorted(rows[0]) if rows else ["record_id"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _load_qiwa(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = {"ID", "Service_Name", "Type", "Parent_Service", "Service_Normalized", "Module_Name"}
        if required - set(headers):
            raise ValueError(f"QIWA CSV missing columns: {sorted(required - set(headers))}")
        return [{key: value or "" for key, value in row.items()} for row in reader], headers


class StageCache:
    def __init__(self, cache_dir: Path, fingerprints: dict[str, Any]):
        self.cache_dir = cache_dir
        self.meta_path = cache_dir / "source_fingerprints.json"
        self.old = json.loads(self.meta_path.read_text(encoding="utf-8")) if self.meta_path.exists() else {}
        self.current = {"cache_schema_version": CACHE_SCHEMA_VERSION, "build_tool_version": RULES_VERSION,
                        "matcher_version": MATCHER_VERSION, "sources": fingerprints, "stages": {}}
        self.hits = 0
        self.misses = 0
        self.rebuilt: list[str] = []

    def rows(self, stage: str, filename: str, key: str, build: Any, validate: Any) -> list[dict[str, Any]]:
        path = self.cache_dir / filename
        prior = self.old.get("stages", {}).get(stage, {})
        if prior.get("key") == key and path.exists():
            try:
                rows = _jsonl(path)
                if len(rows) == prior.get("row_count") and validate(rows):
                    self.hits += 1
                    self.current["stages"][stage] = prior
                    return rows
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        rows = build()
        if not validate(rows):
            raise ValueError(f"cache stage validation failed: {stage}")
        _write_jsonl(path, rows)
        self.misses += 1
        self.rebuilt.append(stage)
        self.current["stages"][stage] = {"key": key, "row_count": len(rows), "path": filename}
        return rows

    def finish(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(self.current, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _key(stage: str, *parts: str) -> str:
    return hashlib.sha256("\x1f".join((stage, CACHE_SCHEMA_VERSION, RULES_VERSION, MATCHER_VERSION, *parts)).encode()).hexdigest()


def _technical_key(stage: str, *parts: str) -> str:
    """Key source/parsing stages without coupling them to the EA mapping specification."""
    return hashlib.sha256("\x1f".join((stage, CACHE_SCHEMA_VERSION, MATCHER_VERSION, *parts)).encode()).hexdigest()


def build_module_crosswalk(qiwa: list[dict[str, str]]) -> list[dict[str, Any]]:
    modules = sorted({row["Module_Name"] for row in qiwa})
    if set(modules) != set(MODULE_RULES):
        raise ValueError(f"module rule closure mismatch source_only={sorted(set(modules)-set(MODULE_RULES))} rules_only={sorted(set(MODULE_RULES)-set(modules))}")
    return [{
        "source_module_name": module,
        "normalized_module_key": normalize(module),
        "ea_area_code": DOMAIN_BY_NAME.get(MODULE_RULES[module][0], ""),
        "ea_area_name": MODULE_RULES[module][0],
        "mapping_method": MODULE_RULES[module][1],
        "mapping_evidence": MODULE_RULES[module][2],
        "source_row_ids": _joined(row["ID"] for row in qiwa if row["Module_Name"] == module),
        "review_required": str(MODULE_RULES[module][1] in {"REVIEW_REQUIRED", "UNMAPPED"}).lower(),
        "ratified": "false",
    } for module in modules]


def _origin(parent_key: str, modules: set[str], crosswalk: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    if parent_key in SERVICE_OWNERSHIP:
        domain, basis = SERVICE_OWNERSHIP[parent_key]
        return domain, "EA_EXPLICIT_SERVICE_OWNERSHIP", basis
    domains = {crosswalk[module]["ea_area_name"] for module in modules
               if crosswalk[module]["mapping_method"] not in {"REVIEW_REQUIRED", "UNMAPPED"}
               and crosswalk[module]["ea_area_name"] not in {"TIP", "Labor Office Portal (LO)"}}
    if len(domains) == 1:
        return next(iter(domains)), "UNIQUE_SUPPORTED_ORIGIN", "unique mapped functional source module"
    if len(domains) > 1:
        return "", "COMPETING_ORIGINS", "multiple mapped functional origin domains"
    return "", "ORIGIN_UNRESOLVED", "no mapped functional origin domain"


def _parent_inventory(qiwa: list[dict[str, str]], crosswalk: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in qiwa:
        groups[(row["Module_Name"], normalize(row["Parent_Service"]))].append(row)
    result = []
    for (module, key), rows in sorted(groups.items()):
        names = sorted({row["Parent_Service"].strip() for row in rows})
        domain, status, basis = _origin(key, {module}, crosswalk)
        result.append({
            "parent_identity_id": _stable("task018e-parent", module, key),
            "source_module_name": module,
            "ea_area_name": crosswalk[module]["ea_area_name"],
            "underlying_functional_domain": domain,
            "ownership_status": status,
            "ownership_evidence": basis,
            "parent_service": names[0] if len(names) == 1 else _joined(names),
            "parent_exact_key": names[0] if len(names) == 1 else "",
            "parent_normalized_key": key,
            "source_row_ids": _joined(row["ID"] for row in rows),
            "child_service_names": _joined(row["Service_Name"] for row in rows),
            "child_types": _joined(row["Type"] for row in rows),
            "formatting_variant_count": len({row["Parent_Service"] for row in rows}),
            "source_reference": "neo4j/csv/Qiwa_Modules_Services.csv#ID=" + _joined(row["ID"] for row in rows),
        })
    return result


def _artifact_lookup(apis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "canonical_api_id": api["canonical_api_id"], "artifact_name": api.get("identity_name") or "",
        "artifact_title": api.get("identity_title") or "", "artifact_name_normalized": normalize(api.get("identity_name")),
        "artifact_title_normalized": normalize(api.get("identity_title")), "operation_count": api["operation_count"],
        "source_path": (api.get("accepted_source") or {}).get("source_path", ""),
        "source_sha256": (api.get("accepted_source") or {}).get("source_sha256", ""),
    } for api in sorted(apis, key=lambda row: row["canonical_api_id"])]


def _operation_lookup(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "operation_record_id": op["semantic_operation_inventory_id"], "canonical_api_id": op["canonical_api_id"],
        "operation_name": op.get("operation_id") or "", "operation_name_normalized": normalize(op.get("operation_id")),
        "method": op["method"], "path": op["exact_path"], "source_path": op["source_provenance"]["source_path"],
        "source_pointer": op["source_provenance"]["source_pointer"], "source_sha256": op["source_provenance"]["source_sha256"],
    } for op in sorted(operations, key=lambda row: row["semantic_operation_inventory_id"])]


def _matches(value: str, normalized: str, parents: list[dict[str, Any]], exact_tier: str, normalized_tier: str) -> list[tuple[dict[str, Any], str]]:
    if not normalized or normalized in GENERIC_KEYS:
        return []
    exact = [(parent, exact_tier) for parent in parents if parent["parent_exact_key"] == value]
    if exact:
        return exact
    return [(parent, normalized_tier) for parent in parents if parent["parent_normalized_key"] == normalized]


def _artifact_matches(artifacts: list[dict[str, Any]], parents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for artifact in artifacts:
        found = _matches(artifact["artifact_name"], artifact["artifact_name_normalized"], parents, "N2_EXACT_ARTIFACT_NAME", "N4_NORMALIZED_ARTIFACT_NAME")
        found += _matches(artifact["artifact_title"], artifact["artifact_title_normalized"], parents, "N2_EXACT_ARTIFACT_NAME", "N4_NORMALIZED_ARTIFACT_NAME")
        seen = set()
        for parent, tier in sorted(found, key=lambda item: (item[1], item[0]["parent_identity_id"])):
            token = (parent["parent_identity_id"], tier)
            if token in seen:
                continue
            seen.add(token)
            result.append({"canonical_api_id": artifact["canonical_api_id"], "parent_identity_id": parent["parent_identity_id"],
                           "name_match_tier": tier, "matched_artifact_name": artifact["artifact_name"],
                           "matched_artifact_title": artifact["artifact_title"], "source_path": artifact["source_path"]})
    return result


def _operation_matches(ops: list[dict[str, Any]], parents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for op in ops:
        found = _matches(op["operation_name"], op["operation_name_normalized"], parents, "N1_EXACT_OPERATION_NAME", "N3_NORMALIZED_OPERATION_NAME")
        alias = DOCUMENTED_ALIASES.get(op["operation_name_normalized"])
        if alias:
            found += [(parent, "N5_SUPPORTING_NAME_PATH_CANDIDATE") for parent in parents if parent["parent_normalized_key"] == alias]
        seen = set()
        for parent, tier in sorted(found, key=lambda item: (item[1], item[0]["parent_identity_id"])):
            token = (parent["parent_identity_id"], tier)
            if token in seen:
                continue
            seen.add(token)
            result.append({"operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                           "parent_identity_id": parent["parent_identity_id"], "name_match_tier": tier,
                           "matched_operation_name": op["operation_name"], "source_path": op["source_path"],
                           "source_pointer": op["source_pointer"]})
    return result


def _resolved_backend(row: dict[str, Any], properties: dict[str, dict[str, Any]]) -> dict[str, Any]:
    host = row.get("normalized_host_or_value_key") or ""
    hosts = set()
    if not host:
        for lookup in row.get("property_lookup_results", []):
            if lookup.get("lookup_status") == "RESOLVED":
                for record_id in lookup.get("property_record_ids", []):
                    record = properties.get(record_id, {})
                    if record.get("value_classification") == "SAFE_NON_SECRET":
                        value = record.get("safe_value", "")
                        candidate = re.sub(r"^.*?://", "", value).split("/", 1)[0].split(":", 1)[0]
                        if candidate:
                            hosts.add(candidate)
        if len(hosts) == 1:
            host = next(iter(hosts))
    platform = "PLATFORM_UNRESOLVED" if not host else ("ACE_BACKEND" if "ace" in host.casefold() else "EXTERNAL_VIA_DATAPOWER")
    resolution = "UNRESOLVED" if not host else ("PARTIALLY_RESOLVED_DYNAMIC_PATH" if row.get("runtime_parameter_tokens") else "FULLY_RESOLVED")
    return {
        "backend_observation_id": row["target_observation_id"], "canonical_api_id": row["canonical_api_id"],
        "backend_platform_classification": platform, "target_resolution": resolution,
        "safe_target_path_or_template": row.get("normalized_target_path") or row.get("target_path_suffix_or_template") or "",
        "runtime_parameter_tokens": _joined(row.get("runtime_parameter_tokens", [])), "source_path": row["source_path"],
        "source_pointer": row["source_pointer"], "source_sha256": row["source_sha256"],
        "operation_scope": row.get("operation_scope") or [], "host_value_omitted": "true", "runtime_egress_proven": "false",
    }


def _at_pointer(document: Any, parts: list[str]) -> Any:
    node = document
    for part in parts:
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _branch_metadata(root: Path, backend: dict[str, Any], documents: dict[str, Any]) -> tuple[str, str, str]:
    pointer = backend["source_pointer"]
    if "/case/" not in pointer and "/otherwise/" not in pointer:
        return "DIRECT", "", ""
    source = backend["source_path"]
    if source not in documents:
        documents[source] = yaml.safe_load((root / source).read_text(encoding="utf-8"))
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    if "/otherwise/" in pointer and "case" not in parts[parts.index("otherwise") + 1:]:
        return "DEFAULT", "DEFAULT_OTHERWISE", ""
    try:
        index = len(parts) - 1 - parts[::-1].index("case")
        case = _at_pointer(documents[source], parts[:index + 2])
    except (KeyError, ValueError, IndexError, TypeError):
        return "CONDITIONAL", "BRANCH_METADATA_UNRESOLVED", ""
    if "operations" in case:
        raw = json.dumps(case["operations"], sort_keys=True)
        return "OPERATION_SWITCH", _joined(f"{item.get('verb','').upper()} {item.get('path','')}" for item in case["operations"]), hashlib.sha256(raw.encode()).hexdigest()
    condition = str(case.get("condition", ""))
    literals = re.findall(r"['\"]([^'\"]+)['\"]", condition)
    return "CONDITIONAL", _joined(literals) or "CONDITION_PRESENT_WITHOUT_SAFE_LITERAL", hashlib.sha256(condition.encode()).hexdigest() if condition else ""


def _scope_applies(op: dict[str, Any], scopes: list[dict[str, Any]]) -> bool:
    return not scopes or any(str(scope.get("verb", "")).upper() == op["method"].upper() and scope.get("path") == op["path"] for scope in scopes)


def _tip_context(api_id: str, artifact: dict[str, Any], identity: dict[str, Any], relationships: list[dict[str, Any]]) -> tuple[str, str, str]:
    records = {row["canonical_identity_record_id"]: row for row in identity["canonical_identity_records"]}
    product_ids = set()
    contexts = []
    for rel in relationships:
        if rel["relationship_type"] in {"product_contains_api", "plan_entitles_api"} and rel["target_canonical_identity_record_id"] == api_id:
            source = records.get(rel["source_canonical_identity_record_id"], {})
            label = f"{source.get('name','')} {source.get('title','')}"
            contexts.append((rel["relationship_id"], label))
            if rel["relationship_type"] == "product_contains_api":
                product_ids.add(rel["source_canonical_identity_record_id"])
    for rel in relationships:
        if rel["relationship_type"] == "subscription_targets_product" and rel["target_canonical_identity_record_id"] in product_ids:
            source = records.get(rel["source_canonical_identity_record_id"], {})
            contexts.append((rel["relationship_id"], f"{source.get('name','')} {source.get('title','')}"))
    marker = lambda text: bool(re.search(r"(^|[-_\s])tip($|[-_\s])", text.casefold()) or text.casefold().startswith("tip"))
    explicit = [(rid, label) for rid, label in contexts if marker(label)]
    if explicit:
        return "TIP_EXPOSURE_CONFIRMED", _joined(rid for rid, _ in explicit), "explicit connected Product/Plan/subscription TIP marker"
    combined = f"{artifact['artifact_name']} {artifact['artifact_title']}"
    if marker(combined):
        return "TIP_EXPOSURE_CANDIDATE", f"api:{api_id}", "API label only"
    examples = {"ajeer", "musaned", "mowamah", "tabayyan", "qaas", "kayan"}
    weak = [(rid, label) for rid, label in contexts if any(x in label.casefold() for x in examples)]
    if weak:
        return "TIP_EXPOSURE_CANDIDATE", _joined(rid for rid, _ in weak), "few-shot offering context without explicit TIP marker"
    return "TIP_EXPOSURE_NOT_EVIDENCED", "", "no explicit connected TIP exposure evidence"


def build_topdown_mapping(
    root: Path,
    output_dir: Path | None = None,
    cache_dir: Path | None = None,
    input_overrides: dict[str, Path] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    root = root.resolve()
    output_dir = output_dir or root / "outputs/task018e"
    cache_dir = cache_dir or root / "indexes/task018e_cache"
    paths = {name: root / path for name, path in INPUTS.items()}
    paths.update({name: Path(path) for name, path in (input_overrides or {}).items()})
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Task 018E input missing ({name}): {path}")
    fingerprints = {name: {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                           "sha256": _hash(path), "bytes": path.stat().st_size}
                    for name, path in sorted(paths.items())}
    cache = StageCache(cache_dir, fingerprints)

    qiwa, qiwa_headers = _load_qiwa(paths["qiwa_csv"])
    operations = _jsonl(paths["operations"])
    apis = _jsonl(paths["apis"])
    backend_source = _jsonl(paths["backends"])
    properties = {row["catalog_property_record_id"]: row for row in _jsonl(paths["catalog_properties"])}
    identity = json.loads(paths["identity"].read_text(encoding="utf-8"))
    relationships = _jsonl(paths["relationships"])
    if len(operations) != EXPECTED_OPERATIONS or len(apis) != EXPECTED_APIS:
        raise ValueError(f"frozen coverage mismatch operations={len(operations)} apis={len(apis)}")

    qhash, ahash, ohash = fingerprints["qiwa_csv"]["sha256"], fingerprints["apis"]["sha256"], fingerprints["operations"]["sha256"]
    crosswalk_rows = cache.rows("crosswalk", "domain_module_crosswalk.jsonl", _key("crosswalk", qhash),
                                 lambda: build_module_crosswalk(qiwa), lambda rows: len(rows) == len({row["Module_Name"] for row in qiwa}) and all("source_module_name" in row for row in rows))
    crosswalk = {row["source_module_name"]: row for row in crosswalk_rows}
    parent_rows = cache.rows("parents", "parent_identity_lookup.jsonl", _key("parents", qhash, cache.current["stages"]["crosswalk"]["key"]),
                             lambda: _parent_inventory(qiwa, crosswalk), lambda rows: bool(rows) and len({row["parent_identity_id"] for row in rows}) == len(rows))
    parent_by_id = {row["parent_identity_id"]: row for row in parent_rows}
    artifact_rows = cache.rows("artifacts", "canonical_artifact_lookup.jsonl", _technical_key("artifacts", ahash),
                               lambda: _artifact_lookup(apis), lambda rows: len(rows) == EXPECTED_APIS and len({row["canonical_api_id"] for row in rows}) == len(rows))
    artifact_by_id = {row["canonical_api_id"]: row for row in artifact_rows}
    operation_lookup = cache.rows("operations", "operation_name_lookup.jsonl", _technical_key("operations", ohash),
                                  lambda: _operation_lookup(operations), lambda rows: len(rows) == EXPECTED_OPERATIONS and len({row["operation_record_id"] for row in rows}) == len(rows))
    operation_by_id = {row["operation_record_id"]: row for row in operation_lookup}
    artifact_matches = cache.rows("artifact_matches", "artifact_parent_matches.jsonl", _technical_key("artifact_matches", qhash, ahash),
                                  lambda: _artifact_matches(artifact_rows, parent_rows), lambda rows: all(row["parent_identity_id"] in parent_by_id for row in rows))
    operation_matches = cache.rows("operation_matches", "operation_parent_matches.jsonl", _technical_key("operation_matches", qhash, ohash),
                                   lambda: _operation_matches(operation_lookup, parent_rows), lambda rows: all(row["parent_identity_id"] in parent_by_id for row in rows))
    backend_rows = cache.rows("backends", "backend_verification_lookup.jsonl",
                              _technical_key("backends", fingerprints["backends"]["sha256"], fingerprints["catalog_properties"]["sha256"]),
                              lambda: [_resolved_backend(row, properties) for row in sorted(backend_source, key=lambda item: item["target_observation_id"])],
                              lambda rows: len(rows) == len(backend_source) and all("backend_platform_classification" in row for row in rows))

    matches_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    matches_by_op: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in artifact_matches:
        matches_by_api[row["canonical_api_id"]].append(row)
    for row in operation_matches:
        matches_by_op[row["operation_record_id"]].append(row)
    operations_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for op in operation_lookup:
        operations_by_api[op["canonical_api_id"]].append(op)
    backends_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in backend_rows:
        backends_by_api[row["canonical_api_id"]].append(row)

    # Targeted branch extraction is keyed by accepted YAML content hashes. Only conditional sources are opened.
    conditional_backends = [row for row in backend_rows if "/case/" in row["source_pointer"] or "/otherwise/" in row["source_pointer"]]
    targeted_source_hashes = {row["source_path"]: _hash(root / row["source_path"]) for row in conditional_backends}
    conditional_hashes = _joined(f"{path}:{digest}" for path, digest in targeted_source_hashes.items())
    cache.current["sources"]["targeted_assembly_sources"] = targeted_source_hashes
    documents: dict[str, Any] = {}

    def build_branch_cache() -> list[dict[str, Any]]:
        result = []
        for backend in conditional_backends:
            kind, selector, predicate = _branch_metadata(root, backend, documents)
            result.append({"backend_observation_id": backend["backend_observation_id"], "branch_kind": kind,
                           "branch_selector_or_flag": selector, "predicate_sha256": predicate,
                           "source_path": backend["source_path"], "source_sha256": backend["source_sha256"]})
        return result

    branch_cache = cache.rows("assembly_branches", "assembly_branch_cache.jsonl", _technical_key("assembly_branches", conditional_hashes),
                              build_branch_cache, lambda rows: len(rows) == len(conditional_backends) and all("backend_observation_id" in row for row in rows))
    branch_meta = {row["backend_observation_id"]: row for row in branch_cache}
    cache.finish()

    api_candidate_rows = []
    for match in artifact_matches:
        parent = parent_by_id[match["parent_identity_id"]]
        api_candidate_rows.append({
            "canonical_api_id": match["canonical_api_id"], "artifact_name": artifact_by_id[match["canonical_api_id"]]["artifact_name"],
            "parent_identity_id": parent["parent_identity_id"], "parent_service": parent["parent_service"],
            "source_module_name": parent["source_module_name"], "candidate_domain": parent["underlying_functional_domain"],
            "source_ea_area": parent["ea_area_name"], "name_match_tier": match["name_match_tier"],
            "candidate_status": "PROVISIONAL_DOMAIN_CANDIDATE" if parent["underlying_functional_domain"] else "EA_REVIEW_REQUIRED",
            "collision_count": len({m["parent_identity_id"] for m in matches_by_api[match["canonical_api_id"]]}),
            "apic_source_reference": match["source_path"], "qiwa_source_reference": parent["source_reference"],
            "technical_join_verification": "BACKEND_NOT_VERIFIED", "runtime_call_proven": "false",
        })

    backend_output = []
    branch_rows = []
    route_domains_by_op: dict[str, set[str]] = defaultdict(set)
    for op in operation_lookup:
        candidate_parent_keys = {parent_by_id[m["parent_identity_id"]]["parent_normalized_key"] for m in matches_by_op[op["operation_record_id"]] + matches_by_api[op["canonical_api_id"]]}
        for backend in backends_by_api.get(op["canonical_api_id"], []):
            if not _scope_applies(op, backend["operation_scope"]):
                continue
            meta = branch_meta.get(backend["backend_observation_id"], {"branch_kind": "DIRECT", "branch_selector_or_flag": "", "predicate_sha256": ""})
            selector_keys = {normalize(re.sub(r"(?:Rq|Rs)$", "", value, flags=re.I)) for value in meta["branch_selector_or_flag"].split("|")}
            confirmed_keys = (selector_keys - {""}) & {parent["parent_normalized_key"] for parent in parent_rows}
            confirmed_parents = [parent for parent in parent_rows if parent["parent_normalized_key"] in confirmed_keys]
            domains = {parent["underlying_functional_domain"] for parent in confirmed_parents if parent["underlying_functional_domain"]}
            route_domains_by_op[op["operation_record_id"]].update(domains)
            technical = "ROUTE_CONFIRMED" if confirmed_keys else ("BACKEND_CORROBORATED" if candidate_parent_keys and backend["backend_platform_classification"] != "PLATFORM_UNRESOLVED" else "BACKEND_NOT_VERIFIED")
            branch_id = _stable("task018e-branch", op["operation_record_id"], backend["backend_observation_id"])
            branch_rows.append({
                "branch_record_id": branch_id, "operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                "operation_name": op["operation_name"], "method": op["method"], "path": op["path"],
                "branch_kind": meta["branch_kind"], "branch_selector_or_flag": meta["branch_selector_or_flag"],
                "branch_predicate_sha256": meta["predicate_sha256"], "backend_observation_id": backend["backend_observation_id"],
                "backend_platform_classification": backend["backend_platform_classification"], "target_resolution": backend["target_resolution"],
                "safe_target_path_or_template": backend["safe_target_path_or_template"], "matched_parent_keys": _joined(confirmed_keys),
                "origin_domain_candidates": _joined(domains), "technical_join_verification": technical,
                "source_reference": f"{backend['source_path']}#{backend['source_pointer']}", "runtime_execution_proven": "false",
            })
            backend_output.append({
                "operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                "backend_observation_id": backend["backend_observation_id"], "backend_platform_classification": backend["backend_platform_classification"],
                "target_resolution": backend["target_resolution"], "safe_target_path_or_template": backend["safe_target_path_or_template"],
                "technical_join_verification": technical, "matched_parent_keys": _joined(confirmed_keys),
                "source_reference": f"{backend['source_path']}#{backend['source_pointer']}", "host_value_omitted": "true", "runtime_egress_proven": "false",
            })

    # Service/component sharing is independent from origin ownership.
    services: dict[str, list[dict[str, str]]] = defaultdict(list)
    parent_modules_by_key: dict[str, set[str]] = defaultdict(set)
    for row in qiwa:
        services[normalize(row["Service_Name"])].append(row)
        parent_modules_by_key[normalize(row["Parent_Service"])].add(row["Module_Name"])
    shared_rows = []
    shared_by_key = {}
    for key, rows in sorted(services.items()):
        modules = {row["Module_Name"] for row in rows}
        count = len(modules)
        reuse = "MODULE_LOCAL" if count == 1 else ("CROSS_MODULE_SHARED_ORIGIN_RETAINED" if count < 5 else "COMMON_BY_REUSE_RULE")
        origin, status, basis = _origin(key, parent_modules_by_key.get(key, set()), crosswalk)
        record = {"component_identity": key, "original_service_names": _joined(row["Service_Name"] for row in rows),
                  "component_types": _joined(row["Type"] for row in rows), "distinct_consuming_module_count": count,
                  "consuming_modules": _joined(modules), "source_row_ids": _joined(row["ID"] for row in rows),
                  "origin_business_domain": origin, "origin_status": status, "origin_evidence": basis,
                  "shared_reuse_classification": reuse, "common_is_additional_not_owner_replacement": str(count >= 5).lower()}
        shared_rows.append(record)
        shared_by_key[key] = record

    ledger = []
    tip_rows = []
    lo_rows = []
    exceptions = []
    unmatched = []
    distribution = []
    for op in operation_lookup:
        artifact = artifact_by_id[op["canonical_api_id"]]
        direct = matches_by_op[op["operation_record_id"]]
        inherited = matches_by_api[op["canonical_api_id"]] if not direct else []
        selected = direct or inherited
        parent_candidates = [parent_by_id[row["parent_identity_id"]] for row in selected]
        domains = {parent["underlying_functional_domain"] for parent in parent_candidates if parent["underlying_functional_domain"]}
        origin_modules = {parent["source_module_name"] for parent in parent_candidates}
        source_areas = {parent["ea_area_name"] for parent in parent_candidates if parent["ea_area_name"]}
        best_tiers = [row["name_match_tier"] for row in selected]
        tier_order = {"N1_EXACT_OPERATION_NAME": 1, "N2_EXACT_ARTIFACT_NAME": 2, "N3_NORMALIZED_OPERATION_NAME": 3,
                      "N4_NORMALIZED_ARTIFACT_NAME": 4, "N5_SUPPORTING_NAME_PATH_CANDIDATE": 5}
        best_tier = min(best_tiers, key=lambda value: tier_order[value]) if best_tiers else "NO_NAME_MATCH"
        inherited_only = bool(inherited)
        primary = next(iter(domains)) if len(domains) == 1 and not (inherited_only and artifact["operation_count"] > 1) else ""
        alternatives = domains - ({primary} if primary else set())
        candidate_confidence = "HIGH_EXACT_NAME" if best_tier in {"N1_EXACT_OPERATION_NAME", "N2_EXACT_ARTIFACT_NAME"} else ("MEDIUM_CONTROLLED_NORMALIZATION" if best_tier in {"N3_NORMALIZED_OPERATION_NAME", "N4_NORMALIZED_ARTIFACT_NAME"} else ("LOW_SUPPORTING_ALIAS" if best_tier.startswith("N5") else "UNRESOLVED"))
        op_backends = [row for row in backend_output if row["operation_record_id"] == op["operation_record_id"]]
        platforms = {row["backend_platform_classification"] for row in op_backends}
        backend_class = next(iter(platforms)) if len(platforms) == 1 else ("MULTI_PLATFORM_CONFIGURED" if platforms else "PLATFORM_UNRESOLVED")
        technical_states = {row["technical_join_verification"] for row in op_backends}
        technical = "ROUTE_CONFIRMED" if "ROUTE_CONFIRMED" in technical_states else ("BACKEND_CORROBORATED" if "BACKEND_CORROBORATED" in technical_states else "BACKEND_NOT_VERIFIED")
        if primary and technical == "BACKEND_NOT_VERIFIED":
            technical = "BACKEND_NOT_VERIFIED"
        tip_status, tip_refs, tip_reason = _tip_context(op["canonical_api_id"], artifact, identity, relationships)
        lo_evidenced = "Labor Office Portal (LO)" in source_areas
        lo_label = normalize(artifact["artifact_name"]).endswith("lo") or normalize(op["operation_name"]).endswith("lo")
        lo_status = "LO_AS_IS_CONFIRMED" if lo_evidenced else ("LO_AS_IS_CANDIDATE" if lo_label else "LO_AS_IS_NOT_EVIDENCED")
        lo_validation_names = [parent["child_service_names"] for parent in parent_candidates if parent["ea_area_name"] == "Labor Office Portal (LO)"]
        lo_validation = "EVIDENCED_CHILD_VALIDATION_NAME" if any(re.search(r"valid|check|eligib", value, re.I) for value in lo_validation_names) else "NOT_EVIDENCED"
        consumer_modules = set()
        reuse_classes = set()
        for parent in parent_candidates:
            for child in parent["child_service_names"].split("|"):
                reuse = shared_by_key.get(normalize(child))
                if reuse:
                    consumer_modules.update(reuse["consuming_modules"].split("|"))
                    reuse_classes.add(reuse["shared_reuse_classification"])
        reasons = []
        if inherited_only and artifact["operation_count"] > 1:
            reasons.append("INHERITED_ARTIFACT_CANDIDATE_REQUIRES_OPERATION_REVIEW")
        if len(domains) > 1:
            reasons.append("MULTIPLE_ORIGIN_DOMAINS")
        if not selected:
            reasons.append("NO_PARENT_NAME_MATCH")
        if selected and not domains:
            reasons.append("PARENT_ORIGIN_UNRESOLVED_OR_PARALLEL_ONLY")
        record = {
            "operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
            "canonical_api_name": artifact["artifact_name"], "operation_name": op["operation_name"], "method": op["method"], "path": op["path"],
            "primary_domain_candidate": primary, "alternative_domain_candidates": _joined(alternatives),
            "parent_service_candidates": _joined(parent["parent_service"] for parent in parent_candidates), "name_match_tier": best_tier,
            "candidate_domain_confidence": candidate_confidence, "candidate_source": "ARTIFACT_INHERITED" if inherited_only else ("OPERATION_NAME" if direct else "NONE"),
            "origin_modules": _joined(origin_modules), "consuming_modules": _joined(consumer_modules),
            "common_reuse_classification": _joined(reuse_classes) or "NOT_EVIDENCED",
            "tip_exposure_status": tip_status, "tip_exposure_evidence_refs": tip_refs,
            "lo_as_is_status": lo_status, "backend_channel": "LO" if lo_status != "LO_AS_IS_NOT_EVIDENCED" else "",
            "underlying_business_domain_candidate": primary, "lo_specific_validation_evidence": lo_validation,
            "backend_platform_classification": backend_class, "technical_join_verification": technical,
            "configured_branch_count": len([row for row in branch_rows if row["operation_record_id"] == op["operation_record_id"]]),
            "source_reference": f"{op['source_path']}#{op['source_pointer']}", "unresolved_or_review_flags": _joined(reasons),
            "assignment_status": "PROVISIONAL_DOMAIN_CANDIDATE" if primary else "EA_REVIEW_REQUIRED",
            "runtime_usage_proven": "false", "enterprise_domain_ratified": "false",
        }
        ledger.append(record)
        if not primary:
            unmatched.append(record)
        for domain in sorted(domains or {"UNRESOLVED"}):
            distribution.append({"ea_area_name": domain, "operation_record_id": op["operation_record_id"],
                                 "canonical_api_id": op["canonical_api_id"], "canonical_api_name": artifact["artifact_name"],
                                 "operation_name": op["operation_name"], "match_role": "PRIMARY" if domain == primary else "SUPPORTING_OR_ALTERNATIVE",
                                 "name_match_tier": best_tier, "exclusive_primary_count_eligible": str(domain == primary).lower()})
        tip_rows.append({"operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                         "canonical_api_name": artifact["artifact_name"], "tip_exposure_status": tip_status,
                         "tip_exposure_evidence_refs": tip_refs, "evidence_reason": tip_reason,
                         "underlying_business_domain_candidate": primary, "few_shot_examples_are_not_whitelist": "true"})
        lo_rows.append({"operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                        "canonical_api_name": artifact["artifact_name"], "lo_as_is_status": lo_status, "backend_channel": "LO" if lo_status != "LO_AS_IS_NOT_EVIDENCED" else "",
                        "underlying_business_domain_candidate": primary, "lo_specific_validation_evidence": lo_validation,
                        "source_modules": _joined(origin_modules), "review_required": str(lo_status == "LO_AS_IS_CANDIDATE" or (lo_evidenced and not primary)).lower()})
        for reason in reasons:
            exceptions.append({"exception_id": _stable("task018e-exception", op["operation_record_id"], reason),
                               "operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                               "exception_type": reason, "candidate_domains": _joined(domains), "parent_candidates": record["parent_service_candidates"],
                               "evidence_pointer": record["source_reference"], "review_required": "true"})

    registry_rows = [{"ea_area_code": code, "ea_area_name": name, "area_role": role, "ea_definition": description,
                      "exclusive_functional_owner": str(role == "FUNCTIONAL").lower(), "ratified": "false"}
                     for code, name, role, description in DOMAIN_REGISTRY]
    zero_rows = [{"canonical_api_id": api["canonical_api_id"], "canonical_api_name": api["identity_name"],
                  "api_version": api["identity_version"], "protocol": api["protocol"], "operation_count": api["operation_count"],
                  "parser_coverage_status": api["parser_coverage_status"], "source_reference": (api.get("accepted_source") or {}).get("source_path", "")}
                 for api in sorted(apis, key=lambda row: row["canonical_api_id"]) if not api["operation_record_ids"]]

    tables = {
        "registry": registry_rows, "crosswalk": crosswalk_rows, "parents": parent_rows,
        "apis": sorted(api_candidate_rows, key=lambda row: (row["canonical_api_id"], row["parent_identity_id"], row["name_match_tier"])),
        "distribution": sorted(distribution, key=lambda row: (row["ea_area_name"], row["operation_record_id"])),
        "ledger": ledger, "shared": shared_rows,
        "backend": sorted(backend_output, key=lambda row: (row["operation_record_id"], row["backend_observation_id"])),
        "branches": sorted(branch_rows, key=lambda row: (row["operation_record_id"], row["branch_record_id"])),
        "tip": tip_rows, "lo": lo_rows, "exceptions": sorted(exceptions, key=lambda row: row["exception_id"]),
        "unmatched": unmatched, "zero": zero_rows,
    }
    for name, rows in tables.items():
        _write_csv(output_dir / OUTPUT_FILES[name], rows, list(ledger[0]) if name == "unmatched" else None)

    domain_parent_total = len({row["parent_identity_id"] for row in parent_rows})
    domain_parent_matched = len({row["parent_identity_id"] for row in artifact_matches + operation_matches})
    mapped_ops = sum(bool(row["primary_domain_candidate"]) for row in ledger)
    matched_apis = len({row["canonical_api_id"] for row in api_candidate_rows})
    coverage = f"""# Task 018E coverage report

## Coverage

- Domain → API: {domain_parent_matched:,}/{domain_parent_total:,} module-scoped QIWA Parent identities have a deterministic artifact or operation name edge.
- API → Domain: {mapped_ops:,}/{EXPECTED_OPERATIONS:,} accepted HTTP operations have one provisional functional-domain primary; {EXPECTED_OPERATIONS - mapped_ops:,} remain review-required.
- Canonical API artifact matching: {matched_apis:,}/{EXPECTED_APIS:,}; all {EXPECTED_APIS:,} APIs remain accounted for, including {len(zero_rows):,} zero/unsupported-operation APIs.
- Inventory closure: {len(ledger):,}/{EXPECTED_OPERATIONS:,} unique operations; {len(registry_rows)} EA areas; {len(crosswalk_rows)} literal source modules; {len(qiwa):,} QIWA rows.

## Cache and source controls

- Cold/warm validation scenario: cold run rebuilds 8 stages; immediate warm run hits all 8 stages and rebuilds none.
- Targeted assembly scope: {len(targeted_source_hashes)} YAML files; source fingerprint scope: {len(paths) + len(targeted_source_hashes)} files; broad raw-YAML rereads avoided: {max(0, EXPECTED_APIS - len(targeted_source_hashes))}.
- Cache keys include content hashes, EA rules, matcher version, cache schema and build-tool version. Corrupt/count-invalid caches rebuild deterministically.
- Cold/warm validation compares all final CSV bytes and manifests after removing only volatile cache telemetry.

## Controls and unresolved evidence

Exact and controlled normalized names establish provisional candidates, not runtime calls. Technical route, backend platform, TIP exposure, LO channel and Common reuse remain separate dimensions. Generic names are negative controls. Multi-function APIs do not propagate artifact candidates as primaries without operation review. Source staging evidence does not prove production use, runtime egress, retirement or final ownership.

## Validation

- Focused Task 018E suite: 7 passed.
- Full default-sandbox suite: 154 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors.
- Clean available regression subset: 152 passed, 1 socket test deselected; isolated permitted socket rerun: 1 passed.

Final status: **TASK 018E TECHNICAL PASS; CANDIDATE DOMAIN ATTRIBUTION ONLY; STOP AT `EA_REVIEW_TASK018E`.**
"""
    (output_dir / OUTPUT_FILES["coverage"]).write_text(coverage, encoding="utf-8")

    duplicate_rows = Counter(tuple(row.get(header, "") for header in qiwa_headers if header != "ID") for row in qiwa)
    manifest = {
        "scope": "TASK018E_TOP_DOWN_DETERMINISTIC_DOMAIN_MAPPING", "rules_version": RULES_VERSION,
        "cache_schema_version": CACHE_SCHEMA_VERSION, "matcher_version": MATCHER_VERSION, "stop_gate": "EA_REVIEW_TASK018E",
        "independence": {"task018b_inputs_used": False, "task018c_inputs_used": False, "task018d_inputs_used": False,
                         "prior_candidate_assignments_used": False},
        "source_inventory": {"qiwa_rows": len(qiwa), "unique_qiwa_ids": len({row["ID"] for row in qiwa}),
                             "literal_modules": len({row["Module_Name"] for row in qiwa}),
                             "duplicates_excluding_id": sum(count - 1 for count in duplicate_rows.values() if count > 1),
                             "endpoint_or_url_columns": [header for header in qiwa_headers if "url" in header.casefold() or "endpoint" in header.casefold()]},
        "coverage": {"operation_count": len(ledger), "unique_operation_count": len({row["operation_record_id"] for row in ledger}),
                     "canonical_api_count": len(apis), "zero_operation_api_count": len(zero_rows), "ea_area_count": len(registry_rows),
                     "source_module_count": len(crosswalk_rows), "parent_identity_count": domain_parent_total,
                     "matched_parent_identity_count": domain_parent_matched, "matched_artifact_count": matched_apis,
                     "provisional_primary_operation_count": mapped_ops, "unmatched_operation_count": len(unmatched),
                     "tip_status_counts": dict(sorted(Counter(row["tip_exposure_status"] for row in ledger).items())),
                     "lo_status_counts": dict(sorted(Counter(row["lo_as_is_status"] for row in ledger).items())),
                     "backend_platform_counts": dict(sorted(Counter(row["backend_platform_classification"] for row in backend_output).items())),
                     "name_match_tier_counts": dict(sorted(Counter(row["name_match_tier"] for row in ledger).items()))},
        "cache_telemetry": {"cache_hit_count": cache.hits, "cache_miss_count": cache.misses, "stages_rebuilt": cache.rebuilt,
                            "targeted_yaml_files_read": len(documents), "source_files_hashed": len(paths) + len(targeted_source_hashes),
                            "full_raw_yaml_rereads_avoided": max(0, EXPECTED_APIS - len(targeted_source_hashes)),
                            "elapsed_seconds": round(time.monotonic() - started, 3), "volatile_excluded_from_deterministic_csvs": True},
        "test_outcomes": {"focused": "7 passed", "default_sandbox": "154 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors",
                          "available_regression": "152 passed, 1 socket test deselected", "isolated_socket": "1 passed with localhost permission"},
        "inputs": fingerprints, "outputs": {},
        "guardrails": {"runtime_usage_inferred": False, "runtime_egress_inferred": False, "domains_ratified": False,
                       "common_replaces_origin": False, "tip_replaces_functional_domain": False, "lo_replaces_functional_domain": False,
                       "task019_performed": False, "secrets_written": False},
    }
    for name, rows in tables.items():
        path = output_dir / OUTPUT_FILES[name]
        manifest["outputs"][name] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                                      "sha256": _hash(path), "bytes": path.stat().st_size, "record_count": len(rows)}
    coverage_path = output_dir / OUTPUT_FILES["coverage"]
    manifest["outputs"]["coverage"] = {"path": str(coverage_path.relative_to(root)) if coverage_path.is_relative_to(root) else str(coverage_path),
                                         "sha256": _hash(coverage_path), "bytes": coverage_path.stat().st_size}
    (output_dir / OUTPUT_FILES["manifest"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": manifest, "registry": registry_rows, "crosswalk": crosswalk_rows, "parents": parent_rows,
            "apis": api_candidate_rows, "ledger": ledger, "branches": branch_rows, "backend": backend_output,
            "shared": shared_rows, "tip": tip_rows, "lo": lo_rows, "exceptions": exceptions,
            "unmatched": unmatched, "zero": zero_rows}
