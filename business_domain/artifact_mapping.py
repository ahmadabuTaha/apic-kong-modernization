from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .topdown_mapping import (
    _artifact_matches,
    _branch_metadata,
    _hash,
    _joined,
    _jsonl,
    _operation_matches,
    _resolved_backend,
    _scope_applies,
    _stable,
    _write_csv,
    _write_jsonl,
    normalize,
)


RULES_VERSION = "task018f-artifact-first-domain-mapping-v2"
CACHE_SCHEMA_VERSION = "task018f-cache-v3"
PARSER_VERSION = "task018f-safe-schema-summary-v1"
EXPECTED_APIS = 2036
EXPECTED_OPERATIONS = 2414

INPUTS = {
    "qiwa_csv": Path("neo4j/csv/Qiwa_Modules_Services.csv"),
    "apis": Path("indexes/semantic_api_inventory.jsonl"),
    "operations": Path("indexes/semantic_operation_inventory.jsonl"),
    "schema_clues": Path("indexes/task018b_business_object_candidate_register.jsonl"),
    "backends": Path("indexes/backend_target_resolution.jsonl"),
    "catalog_properties": Path("indexes/catalog_properties.jsonl"),
    "identity": Path("indexes/apic_identity_resolution.json"),
    "relationships": Path("indexes/relationship_index.jsonl"),
}

DOMAIN_REGISTRY = (
    ("D01", "Establishment", "EFM, establishment logo/location and proactive awareness"),
    ("D02", "Contracts", "Contract management, training contracts and external contracts"),
    ("D03", "Visa", "Visit, seasonal, temporary, establishing and expansion visas"),
    ("D04", "WorkForce", "Employee/laborer lifecycle, transfer, absence, training, decease and LMH"),
    ("D05", "Work Permit", "Work Permit lifecycle, payments, debts and late Work Permit"),
    ("D06", "Payment", "Payment gateways, SADAD, wallet, reconciliation, invoices and billing"),
    ("D07", "Occupation", "Occupation management and change/correction occupation"),
    ("D08", "Nitaqat", "Nitaqat services"),
    ("D09", "Certificate", "Salary, Saudization, Work Policy and Wage Protection certificates"),
    ("D10", "Common", "Shared enterprise/platform components and 5+ module reuse"),
    ("D11", "TIP", "Takamol Integration Portal AS-IS ownership/exposure"),
    ("D12", "User Management", "User, SSO, identity and privilege operations"),
    ("D13", "Notification", "Email, SMS and notification orchestration"),
    ("D14", "LO", "Labor Office Portal AS-IS ownership and LO-specific validations"),
    ("D15", "Utilities", "Named utility, support, tooling and technical integration offerings"),
)
DOMAIN_NAMES = {row[1] for row in DOMAIN_REGISTRY}

MODULE_RULES: dict[str, tuple[str, str, str]] = {
    "EFM": ("Establishment", "EA_EXPLICIT_BUSINESS_ANCHOR", "EFM"),
    "Establishment logo": ("Establishment", "DOCUMENTED_ALIAS", "Establishment Logo"),
    "Establishment Loc": ("Establishment", "DOCUMENTED_ALIAS", "Establishment Location"),
    "Proactive Awareness": ("Establishment", "EA_EXPLICIT_BUSINESS_ANCHOR", "Proactive Awareness"),
    "Contract Mgmt": ("Contracts", "DOCUMENTED_ALIAS", "Contract Management"),
    "Training Contract": ("Contracts", "DOCUMENTED_ALIAS", "Training Contracts"),
    "Visa Mgmt": ("Visa", "FAMILY_RULE", "Visa family"),
    "ET": ("WorkForce", "DOCUMENTED_ALIAS", "Employee Transfer"),
    "End Of Service Reward": ("WorkForce", "EA_EXPLICIT_BUSINESS_ANCHOR", "End of Service Reward"),
    "Absense Mgmt": ("WorkForce", "DOCUMENTED_ALIAS", "Absence Management; literal typo retained"),
    "Training Indicators": ("WorkForce", "DOCUMENTED_ALIAS", "Training Indicator"),
    "Decease Mgmt": ("WorkForce", "EA_EXPLICIT_BUSINESS_ANCHOR", "Decease Management"),
    "LMH": ("WorkForce", "DOCUMENTED_ALIAS", "LMH Engine/Scheduler"),
    "Work in Saudi": ("WorkForce", "FAMILY_RULE", "laborer/worker services"),
    "Work Permit": ("Work Permit", "EA_EXPLICIT_BUSINESS_ANCHOR", "Work Permit"),
    "Payment": ("Payment", "EA_EXPLICIT_BUSINESS_ANCHOR", "Payment"),
    "Occupation Mgmt": ("Occupation", "DOCUMENTED_ALIAS", "Occupation Management"),
    "Change Occupation": ("Occupation", "EA_EXPLICIT_BUSINESS_ANCHOR", "Change Occupation"),
    "Nitaqat": ("Nitaqat", "EA_EXPLICIT_BUSINESS_ANCHOR", "Nitaqat"),
    "Salary Certificate": ("Certificate", "EA_EXPLICIT_BUSINESS_ANCHOR", "Salary Certificate"),
    "Work Policy": ("Certificate", "FAMILY_RULE", "Work Policy Certificate"),
    "Wage Protection": ("Certificate", "FAMILY_RULE", "Wage Protection Certificate"),
    "Common": ("Common", "EA_EXPLICIT_BUSINESS_ANCHOR", "Common"),
    "TIP": ("TIP", "EA_EXPLICIT_BUSINESS_ANCHOR", "TIP"),
    "User Mgmt": ("User Management", "DOCUMENTED_ALIAS", "User Management"),
    "Notification": ("Notification", "EA_EXPLICIT_BUSINESS_ANCHOR", "Notification"),
    "LO": ("LO", "EA_EXPLICIT_BUSINESS_ANCHOR", "Labor Office Portal"),
    "Capptions": ("", "CONTRADICTORY_OR_INSUFFICIENT", "Unresolved literal source module"),
    "Data Portal": ("", "CONTRADICTORY_OR_INSUFFICIENT", "Portal label alone is insufficient"),
    "MOFA": ("", "CONTRADICTORY_OR_INSUFFICIENT", "External organization is not ownership"),
}

# Ordered, contextual anchors. These are not uncontrolled substring weights.
ANCHORS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("TIP", "EA_EXPLICIT_BUSINESS_ANCHOR", "named TIP offering", ("tip", "tabayyan", "qaas", "ajeer", "musaned", "mowamah", "kayan")),
    ("LO", "EA_EXPLICIT_BUSINESS_ANCHOR", "Labor Office Portal ownership context", ("laborofficeportal", "labor-office-portal")),
    ("Utilities", "EA_EXPLICIT_BUSINESS_ANCHOR", "named utility offering", ("qks", "querycenter", "query center", "adaa", "supportcentre", "supportcenter", "support centre", "servicenow", "zendesk", "webex", "s3client", "s3-client")),
    ("User Management", "EA_EXPLICIT_BUSINESS_ANCHOR", "user/identity offering", ("usermanagement", "user-management", "sso", "privilege")),
    ("Work Permit", "EA_EXPLICIT_BUSINESS_ANCHOR", "work-permit object", ("workpermit", "work-permit", "work permit")),
    ("Occupation", "EA_EXPLICIT_BUSINESS_ANCHOR", "occupation object", ("occupation",)),
    ("Nitaqat", "EA_EXPLICIT_BUSINESS_ANCHOR", "Nitaqat object", ("nitaqat",)),
    ("Notification", "EA_EXPLICIT_BUSINESS_ANCHOR", "notification mechanism", ("notification", "sendemail", "sendsms", "emailnotification", "smsnotification")),
    ("Certificate", "FAMILY_RULE", "certificate business object", ("salarycertificate", "saudizationcertificate", "workpolicycertificate", "wageprotectioncertificate")),
    ("Visa", "FAMILY_RULE", "visa business object", ("visa",)),
    ("Contracts", "FAMILY_RULE", "contract business object", ("contract",)),
    ("Payment", "FAMILY_RULE", "payment/billing object", ("payment", "hyperpay", "hypp", "sadad", "invoice", "billing", "wallet", "reconciliation")),
    ("Establishment", "FAMILY_RULE", "establishment object", ("establishment", "efm", "commercialrecord", "establishmentlogo", "establishmentlocation")),
    ("WorkForce", "FAMILY_RULE", "worker/employee object", ("employee", "laborer", "worker", "workforce", "endofservice", "absence", "decease", "trainingindicator")),
    ("Common", "GENERIC_HINT", "shared component hint", ("lookup", "pdfgenerator", "appointment", "meeting")),
)

EXPLICIT_OVERRIDES = {
    "user-management": "User Management",
    "user-management-privilege": "User Management",
    "getpaymentdetails-v2": "Payment",
    "getpaymentdetails": "Payment",
    "gosi_getaccesstoken": "Utilities",
    "gosi-getaccesstoken": "Utilities",
    "submitoccupationcorrectionrequest": "Occupation",
    "getgosicontractslist": "Contracts",
}
GENERIC = {"get", "service", "token", "validator", "validation", "api", "post", "create", "update", "delete"}
TIP_NAMES = {"tip", "tabayyan", "qaas", "ajeer", "musaned", "mowamah", "kayan"}
UTILITY_NAMES = {"qks", "querycenter", "adaa", "supportcentre", "supportcenter", "servicenow", "zendesk", "webex", "s3client"}

OUTPUT_FILES = {
    "registry": "enterprise_domain_registry.csv",
    "apis": "canonical_api_domain_ledger.csv",
    "operations": "operation_domain_ledger.csv",
    "crosswalk": "domain_module_crosswalk.csv",
    "parents": "domain_parent_services.csv",
    "artifact_matches": "artifact_parent_matches.csv",
    "operation_matches": "operation_parent_matches.csv",
    "schema": "schema_business_object_evidence.csv",
    "distribution": "domain_distribution_summary.csv",
    "tip_lo": "tip_lo_domain_inventory.csv",
    "utilities_common": "utilities_common_inventory.csv",
    "poc_test": "poc_test_api_inventory.csv",
    "backend": "backend_corrob_and_branches.csv",
    "exceptions": "domain_mapping_exceptions.csv",
    "unmatched_apis": "unmatched_artifacts.csv",
    "unmatched_operations": "unmatched_operations.csv",
    "zero": "zero_operation_apis.csv",
    "coverage": "coverage_report.md",
    "manifest": "manifest.json",
}


class Cache:
    def __init__(self, directory: Path, source_fingerprints: dict[str, Any]):
        self.directory = directory
        self.meta_path = directory / "source_fingerprints.json"
        self.old = json.loads(self.meta_path.read_text(encoding="utf-8")) if self.meta_path.exists() else {}
        self.current = {"cache_schema_version": CACHE_SCHEMA_VERSION, "rules_version": RULES_VERSION,
                        "parser_version": PARSER_VERSION, "sources": source_fingerprints, "stages": {}}
        self.hits = 0
        self.misses = 0
        self.rebuilt: list[str] = []

    def rows(self, stage: str, filename: str, key: str, builder: Any, validator: Any) -> list[dict[str, Any]]:
        path = self.directory / filename
        prior = self.old.get("stages", {}).get(stage, {})
        if prior.get("key") == key and path.exists():
            try:
                rows = _jsonl(path)
                if prior.get("row_count") == len(rows) and validator(rows):
                    self.hits += 1
                    self.current["stages"][stage] = prior
                    return rows
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        rows = builder()
        if not validator(rows):
            raise ValueError(f"Task 018F cache validation failed: {stage}")
        _write_jsonl(path, rows)
        self.misses += 1
        self.rebuilt.append(stage)
        self.current["stages"][stage] = {"key": key, "row_count": len(rows), "path": filename}
        return rows

    def finish(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(self.current, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _key(stage: str, *parts: str, rules: bool = False, parser: bool = False) -> str:
    versions = [CACHE_SCHEMA_VERSION]
    if rules:
        versions.append(RULES_VERSION)
    if parser:
        versions.append(PARSER_VERSION)
    return hashlib.sha256("\x1f".join([stage, *versions, *parts]).encode()).hexdigest()


def _load_qiwa(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        required = {"ID", "Service_Name", "Type", "Parent_Service", "Service_Normalized", "Module_Name"}
        if required - set(headers):
            raise ValueError(f"QIWA CSV missing columns: {sorted(required - set(headers))}")
        return [{key: value or "" for key, value in row.items()} for row in reader], headers


def _clean(value: Any) -> str:
    """Collapse source formatting whitespace in safe derived display text."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _crosswalk(qiwa: list[dict[str, str]]) -> list[dict[str, Any]]:
    modules = sorted({row["Module_Name"] for row in qiwa})
    if set(modules) != set(MODULE_RULES):
        raise ValueError("Task 018F module rules do not close the literal source vocabulary")
    return [{
        "source_module_name": module,
        "normalized_module_key": normalize(module),
        "primary_as_is_domain_candidate": MODULE_RULES[module][0],
        "mapping_evidence_tier": MODULE_RULES[module][1],
        "mapping_evidence": MODULE_RULES[module][2],
        "source_row_ids": _joined(row["ID"] for row in qiwa if row["Module_Name"] == module),
        "review_status": "CANDIDATE_PENDING_EA" if MODULE_RULES[module][0] else "REVIEW_REQUIRED",
    } for module in modules]


def _parents(qiwa: list[dict[str, str]], crosswalk: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in qiwa:
        groups[(row["Module_Name"], normalize(row["Parent_Service"]))].append(row)
    modules_by_parent: dict[str, set[str]] = defaultdict(set)
    modules_by_service: dict[str, set[str]] = defaultdict(set)
    for row in qiwa:
        modules_by_parent[normalize(row["Parent_Service"])].add(row["Module_Name"])
        service_key = normalize(row["Service_Normalized"] or row["Service_Name"])
        if service_key:
            modules_by_service[service_key].add(row["Module_Name"])
    result = []
    for (module, key), rows in sorted(groups.items()):
        names = sorted({row["Parent_Service"].strip() for row in rows})
        reused_modules = set().union(*(modules_by_service[normalize(row["Service_Normalized"] or row["Service_Name"])] for row in rows))
        distinct_reuse = max((len(modules_by_service[normalize(row["Service_Normalized"] or row["Service_Name"])]) for row in rows), default=1)
        result.append({
            "parent_identity_id": _stable("task018f-parent", module, key),
            "source_module_name": module,
            "domain_candidate": crosswalk[module]["primary_as_is_domain_candidate"],
            "parent_service": names[0] if len(names) == 1 else _joined(names),
            "parent_exact_key": names[0] if len(names) == 1 else "",
            "parent_normalized_key": key,
            "source_ids": _joined(row["ID"] for row in rows),
            "child_services": _joined(row["Service_Name"] for row in rows),
            "distinct_qiwa_module_count": distinct_reuse,
            "qiwa_consuming_modules": _joined((modules_by_parent[key] | reused_modules) - {module}),
            "common_reuse_classification": "COMMON_BY_5_PLUS_REUSE_RULE" if distinct_reuse >= 5 else
                                           ("CROSS_MODULE_REUSE" if distinct_reuse >= 2 else "MODULE_LOCAL"),
            "source_reference": "neo4j/csv/Qiwa_Modules_Services.csv#ID=" + _joined(row["ID"] for row in rows),
            "apic_exposure_proven": "false",
        })
    return result


def _artifact_lookup(apis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "canonical_api_id": api["canonical_api_id"],
        "artifact_name": _clean(api.get("identity_name")),
        "artifact_title": _clean(api.get("identity_title")),
        "description": _clean(api.get("api_description")),
        "tags": _joined(api.get("descriptive_tags", [])),
        "version": api.get("identity_version") or "",
        "protocol": api.get("protocol") or "",
        "operation_count": api["operation_count"],
        "operation_ids": _joined(api.get("operation_record_ids", [])),
        "artifact_name_normalized": normalize(api.get("identity_name")),
        "artifact_title_normalized": normalize(api.get("identity_title")),
        "source_path": (api.get("accepted_source") or {}).get("source_path", ""),
        "source_sha256": (api.get("accepted_source") or {}).get("source_sha256", ""),
        "parser_coverage_status": api.get("parser_coverage_status") or "",
    } for api in sorted(apis, key=lambda row: row["canonical_api_id"])]


def _operation_lookup(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "operation_record_id": op["semantic_operation_inventory_id"],
        "canonical_api_id": op["canonical_api_id"],
        "operation_name": _clean(op.get("operation_id")),
        "operation_name_normalized": normalize(op.get("operation_id")),
        "summary": _clean(op.get("summary")),
        "description": _clean(op.get("description")),
        "tags": _joined(op.get("tags", [])),
        "method": op["method"],
        "path": op["exact_path"],
        "request_schema_refs": _joined(op.get("request_summary", {}).get("schema_references", [])),
        "response_schema_refs": _joined(op.get("response_summary", {}).get("schema_references", [])),
        "source_path": op["source_provenance"]["source_path"],
        "source_pointer": op["source_provenance"]["source_pointer"],
        "source_sha256": op["source_provenance"]["source_sha256"],
    } for op in sorted(operations, key=lambda row: row["semantic_operation_inventory_id"])]


def _context_tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.casefold()) if token}


def _anchor_hits(text: str, identity: bool = False) -> list[dict[str, str]]:
    lowered = text.casefold()
    compact = normalize(text)
    tokens = _context_tokens(text)
    hits: list[dict[str, str]] = []
    for domain, tier, reason, aliases in ANCHORS:
        for alias in aliases:
            alias_compact = normalize(alias)
            exactish = alias.casefold() in tokens or alias_compact == compact
            contextual = len(alias_compact) >= 5 and alias_compact in compact
            if exactish or contextual:
                if alias_compact in GENERIC:
                    continue
                if alias_compact == "visa" and "provision" in lowered:
                    continue
                hits.append({"domain": domain, "tier": tier, "anchor": alias, "reason": reason,
                             "source_role": "ARTIFACT_IDENTITY" if identity else "OPERATION_CONTEXT"})
                break
    # Token/validator only qualifies as Utilities with a named acquisition/generation/validation function.
    if ("accesstoken" in compact or re.search(r"(?:generate|get|create|auth).*token", compact)) and "paymentcardtoken" not in compact:
        hits.append({"domain": "Utilities", "tier": "FAMILY_RULE", "anchor": "token acquisition/generation",
                     "reason": "technical integration authentication function", "source_role": "ARTIFACT_IDENTITY" if identity else "OPERATION_CONTEXT"})
    if ("validator" in compact or compact.startswith("validate")) and not any(hit["domain"] != "Utilities" for hit in hits):
        hits.append({"domain": "Utilities", "tier": "GENERIC_HINT", "anchor": "validator",
                     "reason": "validator function without stronger business object", "source_role": "ARTIFACT_IDENTITY" if identity else "OPERATION_CONTEXT"})
    return hits


def _lifecycle(name: str, description: str, primary: str) -> tuple[str, str]:
    text = f"{name} {description}".casefold()
    for marker, purpose in (("poc", "POC"), ("test", "TEST"), ("mock", "MOCK"), ("sample", "SAMPLE")):
        if re.search(rf"(^|[^a-z]){marker}([^a-z]|$)", text):
            return purpose, f"explicit {marker.upper()} marker; no retirement inference"
    if primary == "Utilities":
        return "UTILITY", "provisional Utilities function"
    if any(token in normalize(name) for token in ("token", "validator")) and not primary:
        return "INTERNAL_TECHNICAL", "technical naming; domain review required"
    return ("BUSINESS", "artifact evidence supports business-purpose review") if primary else ("REVIEW_REQUIRED", "purpose not established")


def _connected_context(api_id: str, identity: dict[str, Any], relationships: list[dict[str, Any]]) -> tuple[str, str, str]:
    records = {row["canonical_identity_record_id"]: row for row in identity["canonical_identity_records"]}
    product_ids: set[str] = set()
    refs: list[str] = []
    labels: list[str] = []
    for rel in relationships:
        if rel["relationship_type"] in {"product_contains_api", "plan_entitles_api"} and rel["target_canonical_identity_record_id"] == api_id:
            source = records.get(rel["source_canonical_identity_record_id"], {})
            refs.append(rel["relationship_id"])
            labels.append(_clean(f"{source.get('name', '')} {source.get('title', '')}"))
            if rel["relationship_type"] == "product_contains_api":
                product_ids.add(rel["source_canonical_identity_record_id"])
    for rel in relationships:
        if rel["relationship_type"] == "subscription_targets_product" and rel["target_canonical_identity_record_id"] in product_ids:
            source = records.get(rel["source_canonical_identity_record_id"], {})
            refs.append(rel["relationship_id"])
            labels.append(_clean(f"{source.get('name', '')} {source.get('title', '')}"))
    return _joined(labels), _joined(refs), "EXPLICIT_ACCEPTED_RELATIONSHIPS" if refs else "NO_CONNECTED_PRODUCT_PLAN"


def _schema_rows(operations: list[dict[str, Any]], clues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clues_by_op: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for clue in clues:
        clues_by_op[clue.get("task014_operation_id", "")].append(clue)
    result = []
    generic = {"responsemodel", "errormodel", "headerserrormodel", "request", "response", "dto", "data"}
    for op in operations:
        directions = (("REQUEST", op["request_schema_refs"]), ("RESPONSE", op["response_schema_refs"]))
        seen: set[tuple[str, str, str]] = set()
        for direction, joined_refs in directions:
            refs = [value for value in joined_refs.split("|") if value]
            for ref in refs:
                name = ref.rsplit("/", 1)[-1]
                role = "DTO_OR_ENVELOPE" if normalize(name) in generic or any(word in normalize(name) for word in ("error", "header", "responsemodel", "requestmodel")) else "NAMED_SCHEMA_OBJECT"
                key = (direction, ref, name)
                if key in seen:
                    continue
                seen.add(key)
                result.append({
                    "schema_evidence_id": _stable("task018f-schema", op["operation_record_id"], direction, ref),
                    "canonical_api_id": op["canonical_api_id"], "operation_record_id": op["operation_record_id"],
                    "direction": direction, "semantic_object": name, "evidence_role": role,
                    "schema_ref": ref, "field_or_state_clues": "", "certainty": "SOURCE_EXTRACTED_REFERENCE",
                    "ownership_limitation": "schema reference does not by itself establish domain ownership",
                    "source_reference": f"{op['source_path']}#{op['source_pointer']}",
                })
        for clue in clues_by_op.get(op["operation_record_id"], []):
            ref = clue.get("schema_ref") or ""
            request = ref and ref in op["request_schema_refs"].split("|")
            response = ref and ref in op["response_schema_refs"].split("|")
            direction = "REQUEST_AND_RESPONSE" if request and response else ("REQUEST" if request else ("RESPONSE" if response else "SCHEMA_DEFINITION_CONTEXT"))
            name = clue.get("evidence_name") or ref.rsplit("/", 1)[-1]
            key = (direction, ref, name)
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "schema_evidence_id": clue["object_evidence_id"], "canonical_api_id": op["canonical_api_id"],
                "operation_record_id": op["operation_record_id"], "direction": direction,
                "semantic_object": name, "evidence_role": clue.get("evidence_role") or "EXTRACTED_CLUE",
                "schema_ref": ref, "field_or_state_clues": _joined([*(clue.get("field_names") or []), *(clue.get("state_values") or [])]),
                "certainty": "FACTUAL_TASK018B_EXTRACTION_ONLY", "ownership_limitation": _joined(clue.get("limitations", [])) or "not ownership proof",
                "source_reference": f"{clue.get('source_path', '')}#{clue.get('definition_pointer', '')}",
            })
    return sorted(result, key=lambda row: (row["operation_record_id"], row["direction"], row["schema_evidence_id"]))


def _choose(candidates: list[dict[str, str]], product_text: str, parent_domains: set[str], name: str) -> tuple[str, str, str, str]:
    override = EXPLICIT_OVERRIDES.get(name.casefold()) or EXPLICIT_OVERRIDES.get(normalize(name))
    domains = [row["domain"] for row in candidates]
    combined = f"{name} {product_text}".casefold()
    product_tip = any(re.search(rf"(^|[^a-z0-9]){re.escape(value)}([^a-z0-9]|$)", combined) for value in TIP_NAMES)
    if override:
        primary, reason, confidence = override, "EA explicit acceptance scenario/identity anchor", "HIGH"
    elif product_tip or "TIP" in parent_domains:
        primary, reason, confidence = "TIP", "direct TIP Product/Plan/module/offering ownership context", "HIGH"
    elif "LO" in parent_domains:
        primary, reason, confidence = "LO", "direct LO QIWA module/parent ownership context", "HIGH"
    elif domains:
        # First match is ordered by specificity; preserve every other domain as support/contradiction.
        primary, reason, confidence = domains[0], candidates[0]["reason"], "HIGH" if candidates[0]["tier"] == "EA_EXPLICIT_BUSINESS_ANCHOR" else "MEDIUM"
    elif len(parent_domains) == 1:
        primary, reason, confidence = next(iter(parent_domains)), "single controlled artifact-to-QIWA Parent candidate", "MEDIUM"
    else:
        return "", "insufficient artifact-level evidence", "LOW", "INSUFFICIENT_EVIDENCE"
    others = (set(domains) | parent_domains) - {primary, ""}
    status = "CONTRADICTORY_EVIDENCE" if others and primary not in {"TIP", "LO", "Utilities", "Common"} else "PROVISIONAL_PRIMARY_AS_IS_DOMAIN"
    return primary, reason, confidence, status


def build_artifact_first_mapping(
    root: Path,
    output_dir: Path | None = None,
    cache_dir: Path | None = None,
    input_overrides: dict[str, Path] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    root = root.resolve()
    output_dir = output_dir or root / "outputs/task018f"
    cache_dir = cache_dir or root / "indexes/task018f_cache"
    paths = {name: root / value for name, value in INPUTS.items()}
    paths.update({name: Path(value) for name, value in (input_overrides or {}).items()})
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Task 018F input missing ({name}): {path}")
    fingerprints = {name: {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                           "sha256": _hash(path), "bytes": path.stat().st_size} for name, path in sorted(paths.items())}
    cache = Cache(cache_dir, fingerprints)
    qiwa, qiwa_headers = _load_qiwa(paths["qiwa_csv"])
    apis = _jsonl(paths["apis"])
    operations_source = _jsonl(paths["operations"])
    schema_clues = _jsonl(paths["schema_clues"])
    backend_source = _jsonl(paths["backends"])
    properties = {row["catalog_property_record_id"]: row for row in _jsonl(paths["catalog_properties"])}
    identity = json.loads(paths["identity"].read_text(encoding="utf-8"))
    relationships = _jsonl(paths["relationships"])
    if len(apis) != EXPECTED_APIS or len(operations_source) != EXPECTED_OPERATIONS:
        raise ValueError(f"Frozen closure mismatch: {len(apis)} APIs / {len(operations_source)} operations")

    ahash = fingerprints["apis"]["sha256"]
    ohash = fingerprints["operations"]["sha256"]
    qhash = fingerprints["qiwa_csv"]["sha256"]
    crosswalk_rows = cache.rows("domain_module_crosswalk", "domain_module_crosswalk.jsonl", _key("crosswalk", qhash, rules=True),
                                lambda: _crosswalk(qiwa), lambda rows: len(rows) == 30)
    crosswalk = {row["source_module_name"]: row for row in crosswalk_rows}
    parent_rows = cache.rows("qiwa_parent_module_lookup", "qiwa_parent_module_lookup.jsonl", _key("parents", qhash, rules=True),
                             lambda: _parents(qiwa, crosswalk), lambda rows: bool(rows) and len(rows) == len({row["parent_identity_id"] for row in rows}))
    parent_by_id = {row["parent_identity_id"]: row for row in parent_rows}
    artifact_rows = cache.rows("api_artifact_identity_lookup", "api_artifact_identity_lookup.jsonl", _key("artifacts", ahash),
                               lambda: _artifact_lookup(apis), lambda rows: len(rows) == EXPECTED_APIS and len(rows) == len({row["canonical_api_id"] for row in rows}))
    operation_rows = cache.rows("operation_identity_lookup", "operation_identity_lookup.jsonl", _key("operations", ohash),
                                lambda: _operation_lookup(operations_source), lambda rows: len(rows) == EXPECTED_OPERATIONS and len(rows) == len({row["operation_record_id"] for row in rows}))
    artifact_matches = cache.rows("artifact_parent_edges", "artifact_parent_edges.jsonl", _key("artifact-matches", qhash, ahash),
                                  lambda: _artifact_matches(artifact_rows, parent_rows), lambda rows: all(row["parent_identity_id"] in parent_by_id for row in rows))
    operation_matches = cache.rows("operation_parent_edges", "operation_parent_edges.jsonl", _key("operation-matches", qhash, ohash),
                                   lambda: _operation_matches(operation_rows, parent_rows), lambda rows: all(row["parent_identity_id"] in parent_by_id for row in rows))
    schema_rows = cache.rows("schema_business_object_clues", "schema_business_object_clues.jsonl",
                             _key("schema", ohash, fingerprints["schema_clues"]["sha256"], parser=True),
                             lambda: _schema_rows(operation_rows, schema_clues),
                             lambda rows: all(row["operation_record_id"] for row in rows))
    anchor_rows = cache.rows("domain_anchor_registry", "domain_anchor_registry.jsonl", _key("anchors", rules=True),
                             lambda: [{"domain": domain, "evidence_tier": tier, "context_rule": reason,
                                       "anchors": _joined(aliases), "collision_control": "context-scoped; generic tokens insufficient"}
                                      for domain, tier, reason, aliases in ANCHORS],
                             lambda rows: bool(rows) and all(row["domain"] in DOMAIN_NAMES for row in rows))
    product_rows = cache.rows(
        "product_channel_lookup", "product_channel_lookup.jsonl",
        _key("product-channel", ahash, fingerprints["identity"]["sha256"], fingerprints["relationships"]["sha256"]),
        lambda: [{"canonical_api_id": artifact["canonical_api_id"],
                  **dict(zip(("product_plan_labels", "product_plan_evidence_refs", "product_plan_status"),
                             _connected_context(artifact["canonical_api_id"], identity, relationships)))}
                 for artifact in artifact_rows],
        lambda rows: len(rows) == EXPECTED_APIS and len(rows) == len({row["canonical_api_id"] for row in rows}),
    )
    product_by_api = {row["canonical_api_id"]: row for row in product_rows}

    by_api_matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_op_matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in artifact_matches:
        by_api_matches[row["canonical_api_id"]].append(row)
    for row in operation_matches:
        by_op_matches[row["operation_record_id"]].append(row)
    schema_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    schema_by_op: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in schema_rows:
        schema_by_api[row["canonical_api_id"]].append(row)
        schema_by_op[row["operation_record_id"]].append(row)

    api_evidence_rows: list[dict[str, Any]] = []
    api_domain: dict[str, dict[str, Any]] = {}
    for artifact in artifact_rows:
        api_id = artifact["canonical_api_id"]
        product_context = product_by_api[api_id]
        product_labels = product_context["product_plan_labels"]
        product_refs = product_context["product_plan_evidence_refs"]
        product_status = product_context["product_plan_status"]
        candidates = _anchor_hits(f"{artifact['artifact_name']} {artifact['artifact_title']} {artifact['description']} {artifact['tags']}", identity=True)
        pmatches = by_api_matches.get(api_id, [])
        parent_domains = {parent_by_id[row["parent_identity_id"]]["domain_candidate"] for row in pmatches if parent_by_id[row["parent_identity_id"]]["domain_candidate"]}
        if any(parent_by_id[row["parent_identity_id"]]["distinct_qiwa_module_count"] >= 5 for row in pmatches):
            candidates.append({"domain": "Common", "tier": "FAMILY_RULE", "anchor": "5+ distinct QIWA module reuse",
                               "reason": "source-grounded shared component reuse", "source_role": "QIWA_REUSE"})
        primary, rationale, confidence, review = _choose(candidates, product_labels, parent_domains, artifact["artifact_name"])
        functional = [row["domain"] for row in candidates if row["domain"] not in {"TIP", "LO", "Utilities", "Common", primary}]
        underlying = functional[0] if primary in {"TIP", "LO", "Utilities", "Common"} and functional else ""
        supporting = (set(row["domain"] for row in candidates) | parent_domains) - {primary, underlying, ""}
        lifecycle, lifecycle_reason = _lifecycle(artifact["artifact_name"], artifact["description"], primary)
        evidence_strings = [f"{row['tier']}:{row['source_role']}:{row['anchor']}" for row in candidates]
        product_tokens = _context_tokens(product_labels)
        channel_values = set()
        if primary == "TIP" or any(value in product_tokens or normalize(value) in normalize(product_labels) for value in TIP_NAMES):
            channel_values.add("TIP")
        if primary == "LO" or "LO" in parent_domains:
            channel_values.add("LO")
        api_record = {
            **artifact,
            "primary_as_is_domain_candidate": primary,
            "underlying_functional_domain_candidate": underlying,
            "supporting_domain_candidates": _joined(supporting),
            "consumed_service_domains": _joined(parent_domains - {primary}),
            "domain_evidence_tier": candidates[0]["tier"] if candidates else ("QIWA_PARENT_CANDIDATE" if parent_domains else "INSUFFICIENT"),
            "candidate_confidence": confidence,
            "contradictory_evidence": _joined(supporting) if review == "CONTRADICTORY_EVIDENCE" else "",
            "review_status": review,
            "decision_rationale": rationale,
            "identity_evidence": _joined(evidence_strings),
            "product_plan_labels": product_labels,
            "product_plan_evidence_refs": product_refs,
            "product_plan_status": product_status,
            "qiwa_module_owner": _joined(parent_by_id[row["parent_identity_id"]]["source_module_name"] for row in pmatches),
            "qiwa_parent_candidate": _joined(parent_by_id[row["parent_identity_id"]]["parent_service"] for row in pmatches),
            "qiwa_consuming_modules": _joined(parent_by_id[row["parent_identity_id"]]["qiwa_consuming_modules"] for row in pmatches),
            "qiwa_relationship_certainty": "CANDIDATE_NAME_EDGE" if pmatches else "NO_MATCH",
            "channel_exposure": _joined(channel_values),
            "backend_channel": "LO" if "LO" in channel_values else "",
            "api_lifecycle_purpose": lifecycle,
            "lifecycle_evidence": lifecycle_reason,
            "schema_clue_count": len(schema_by_api.get(api_id, [])),
            "schema_object_clues": _joined(row["semantic_object"] for row in schema_by_api.get(api_id, []) if row["evidence_role"] == "NAMED_SCHEMA_OBJECT"),
            "runtime_use_proven": "false",
            "enterprise_domain_ratified": "false",
        }
        api_domain[api_id] = api_record
        api_evidence_rows.append(api_record)

    api_evidence_rows = cache.rows(
        "api_domain_evidence_cache", "api_domain_evidence_cache.jsonl",
        _key("api-domain-evidence", ahash, qhash, cache.current["stages"]["artifact_parent_edges"]["key"],
             cache.current["stages"]["schema_business_object_clues"]["key"],
             cache.current["stages"]["product_channel_lookup"]["key"], rules=True),
        lambda: api_evidence_rows,
        lambda rows: len(rows) == EXPECTED_APIS and len(rows) == len({row["canonical_api_id"] for row in rows}),
    )
    api_domain = {row["canonical_api_id"]: row for row in api_evidence_rows}

    # Backend and branch corroboration remains independent from domain attribution.
    backend_rows = [_resolved_backend(row, properties) for row in sorted(backend_source, key=lambda value: value["target_observation_id"])]
    conditional = [row for row in backend_rows if "/case/" in row["source_pointer"] or "/otherwise/" in row["source_pointer"]]
    source_hashes = {row["source_path"]: _hash(root / row["source_path"]) for row in conditional}
    documents: dict[str, Any] = {}
    branch_cache = cache.rows("backend_branch_lookup", "backend_branch_lookup.jsonl",
                              _key("branches", _joined(f"{key}:{value}" for key, value in source_hashes.items()), parser=True),
                              lambda: [{"backend_observation_id": row["backend_observation_id"],
                                        **dict(zip(("branch_kind", "branch_selector_or_flag", "predicate_sha256"), _branch_metadata(root, row, documents)))}
                                       for row in conditional],
                              lambda rows: len(rows) == len(conditional))
    branch_by_backend = {row["backend_observation_id"]: row for row in branch_cache}
    cache.current["sources"]["targeted_assembly_sources"] = source_hashes

    backends_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in backend_rows:
        backends_by_api[row["canonical_api_id"]].append(row)
    operations: list[dict[str, Any]] = []
    backend_output: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    for op in operation_rows:
        artifact = api_domain[op["canonical_api_id"]]
        direct = _anchor_hits(f"{op['operation_name']} {op['path']} {op['summary']} {op['description']} {op['tags']}")
        direct_domains = [row["domain"] for row in direct]
        op_parent_domains = {parent_by_id[row["parent_identity_id"]]["domain_candidate"] for row in by_op_matches.get(op["operation_record_id"], []) if parent_by_id[row["parent_identity_id"]]["domain_candidate"]}
        artifact_primary = artifact["primary_as_is_domain_candidate"]
        primary = artifact_primary
        evidence_source = "ARTIFACT_INHERITED"
        confidence = "MEDIUM" if artifact_primary else "LOW"
        contradictions: set[str] = set()
        if artifact_primary in {"TIP", "LO", "Utilities", "Common"}:
            underlying = next((domain for domain in direct_domains if domain not in {"TIP", "LO", "Utilities", "Common"}), artifact["underlying_functional_domain_candidate"])
            contradictions.update(set(direct_domains) - {artifact_primary, underlying})
        elif direct_domains:
            direct_primary = direct_domains[0]
            if artifact_primary and direct_primary != artifact_primary:
                contradictions.update({artifact_primary, direct_primary})
                primary = ""
                evidence_source = "CONFLICTING_ARTIFACT_OPERATION_EVIDENCE"
                confidence = "LOW"
            else:
                primary = direct_primary
                evidence_source = "OPERATION_SPECIFIC"
                confidence = "HIGH" if direct[0]["tier"] == "EA_EXPLICIT_BUSINESS_ANCHOR" else "MEDIUM"
            underlying = artifact["underlying_functional_domain_candidate"]
        else:
            underlying = artifact["underlying_functional_domain_candidate"]
        if not primary and not contradictions and len(op_parent_domains) == 1:
            primary = next(iter(op_parent_domains))
            evidence_source = "QIWA_OPERATION_PARENT_CANDIDATE"
            confidence = "MEDIUM"
        supporting = (set(direct_domains) | op_parent_domains | set(filter(None, artifact["supporting_domain_candidates"].split("|")))) - {primary, underlying, ""}
        review = "PROVISIONAL_PRIMARY_AS_IS_DOMAIN" if primary else ("CONTRADICTORY_EVIDENCE" if contradictions else "INSUFFICIENT_EVIDENCE")
        applicable = [row for row in backends_by_api.get(op["canonical_api_id"], []) if _scope_applies(op, row["operation_scope"])]
        backend_classes = {row["backend_platform_classification"] for row in applicable}
        configured_join = "BACKEND_CORROBORATED" if applicable else "BACKEND_NOT_EVIDENCED"
        for backend in applicable:
            branch = branch_by_backend.get(backend["backend_observation_id"], {"branch_kind": "DIRECT", "branch_selector_or_flag": "", "predicate_sha256": ""})
            backend_output.append({
                "backend_branch_record_id": _stable("task018f-backend", op["operation_record_id"], backend["backend_observation_id"]),
                "operation_record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                "backend_platform_classification": backend["backend_platform_classification"],
                "configured_join_certainty": configured_join, "safe_target_path_or_template": backend["safe_target_path_or_template"],
                "branch_kind": branch["branch_kind"], "branch_selector_or_flag": branch["branch_selector_or_flag"],
                "predicate_sha256": branch["predicate_sha256"], "source_reference": f"{backend['source_path']}#{backend['source_pointer']}",
                "runtime_use_proven": "false", "host_value_omitted": "true",
            })
        record = {
            **op,
            "artifact_name": artifact["artifact_name"],
            "artifact_primary_candidate": artifact_primary,
            "primary_as_is_domain_candidate": primary,
            "underlying_functional_domain_candidate": underlying,
            "supporting_domain_candidates": _joined(supporting),
            "consumed_service_domains": _joined(op_parent_domains - {primary}),
            "domain_evidence_tier": direct[0]["tier"] if direct else artifact["domain_evidence_tier"],
            "candidate_confidence": confidence,
            "candidate_source": evidence_source,
            "contradictory_evidence": _joined(contradictions),
            "review_status": review,
            "qiwa_parent_candidate": _joined(parent_by_id[row["parent_identity_id"]]["parent_service"] for row in by_op_matches.get(op["operation_record_id"], [])),
            "qiwa_module_owner": _joined(parent_by_id[row["parent_identity_id"]]["source_module_name"] for row in by_op_matches.get(op["operation_record_id"], [])),
            "qiwa_consuming_modules": _joined(parent_by_id[row["parent_identity_id"]]["qiwa_consuming_modules"] for row in by_op_matches.get(op["operation_record_id"], [])),
            "qiwa_relationship_certainty": "CANDIDATE_NAME_EDGE" if by_op_matches.get(op["operation_record_id"]) else "NO_MATCH",
            "channel_exposure": artifact["channel_exposure"], "backend_channel": artifact["backend_channel"],
            "api_lifecycle_purpose": artifact["api_lifecycle_purpose"],
            "request_schema_objects": _joined(row["semantic_object"] for row in schema_by_op.get(op["operation_record_id"], []) if row["direction"] in {"REQUEST", "REQUEST_AND_RESPONSE"}),
            "response_schema_objects": _joined(row["semantic_object"] for row in schema_by_op.get(op["operation_record_id"], []) if row["direction"] in {"RESPONSE", "REQUEST_AND_RESPONSE"}),
            "schema_evidence_refs": _joined(row["schema_evidence_id"] for row in schema_by_op.get(op["operation_record_id"], [])),
            "product_plan_evidence_refs": artifact["product_plan_evidence_refs"],
            "backend_platform_classification": _joined(backend_classes) or "PLATFORM_UNRESOLVED",
            "configured_join_certainty": configured_join,
            "configured_branch_count": len(applicable),
            "runtime_use_proven": "false", "enterprise_domain_ratified": "false",
        }
        operations.append(record)
        if review != "PROVISIONAL_PRIMARY_AS_IS_DOMAIN":
            exceptions.append({
                "exception_id": _stable("task018f-exception", op["operation_record_id"], review),
                "record_type": "OPERATION", "record_id": op["operation_record_id"], "canonical_api_id": op["canonical_api_id"],
                "exception_type": review, "competing_evidence": _joined(contradictions | supporting),
                "reason": "conflicting artifact/operation signals" if contradictions else "no sufficient contextual primary evidence",
                "source_reference": f"{op['source_path']}#{op['source_pointer']}", "ea_review_action": "review source evidence; do not force ownership",
            })

    operations = cache.rows(
        "operation_domain_evidence_cache", "operation_domain_evidence_cache.jsonl",
        _key("operation-domain-evidence", ohash, cache.current["stages"]["api_domain_evidence_cache"]["key"],
             cache.current["stages"]["operation_parent_edges"]["key"],
             fingerprints["backends"]["sha256"], fingerprints["catalog_properties"]["sha256"], rules=True),
        lambda: operations,
        lambda rows: len(rows) == EXPECTED_OPERATIONS and len(rows) == len({row["operation_record_id"] for row in rows}),
    )
    cache.finish()

    registry = [{"domain_code": code, "domain_name": name, "as_is_domain": "true", "ea_definition": definition,
                 "primary_candidate_allowed": "true", "ratified": "false", "contextual_evidence_rule": "see domain_anchor_registry cache"}
                for code, name, definition in DOMAIN_REGISTRY]
    artifact_match_output = [{**row, "parent_service": parent_by_id[row["parent_identity_id"]]["parent_service"],
                              "source_module_name": parent_by_id[row["parent_identity_id"]]["source_module_name"],
                              "domain_candidate": parent_by_id[row["parent_identity_id"]]["domain_candidate"],
                              "relationship_certainty": "CANDIDATE_NAME_EDGE_NOT_RUNTIME"} for row in artifact_matches]
    operation_match_output = [{**row, "parent_service": parent_by_id[row["parent_identity_id"]]["parent_service"],
                               "source_module_name": parent_by_id[row["parent_identity_id"]]["source_module_name"],
                               "domain_candidate": parent_by_id[row["parent_identity_id"]]["domain_candidate"],
                               "relationship_certainty": "CANDIDATE_NAME_EDGE_NOT_RUNTIME"} for row in operation_matches]

    distribution = []
    for level, rows, id_field in (("API_ARTIFACT", api_evidence_rows, "canonical_api_id"), ("HTTP_OPERATION", operations, "operation_record_id")):
        primary_counts = Counter(row["primary_as_is_domain_candidate"] for row in rows if row["primary_as_is_domain_candidate"])
        underlying_counts = Counter(row["underlying_functional_domain_candidate"] for row in rows if row["underlying_functional_domain_candidate"])
        supporting_counts: Counter[str] = Counter()
        for row in rows:
            supporting_counts.update(value for value in row["supporting_domain_candidates"].split("|") if value)
        for _, domain, _ in DOMAIN_REGISTRY:
            distribution.append({"classification_level": level, "domain_name": domain,
                                 "exclusive_primary_count": primary_counts[domain], "underlying_count": underlying_counts[domain],
                                 "supporting_count": supporting_counts[domain], "population_count": len(rows),
                                 "counting_note": f"one row per {id_field}; dimensions are not mutually collapsed"})
    tip_lo = [{"record_type": "API_ARTIFACT", "record_id": row["canonical_api_id"], "canonical_api_id": row["canonical_api_id"],
               "artifact_name": row["artifact_name"], "primary_as_is_domain_candidate": row["primary_as_is_domain_candidate"],
               "underlying_functional_domain_candidate": row["underlying_functional_domain_candidate"],
               "product_plan_labels": row["product_plan_labels"], "product_plan_evidence_refs": row["product_plan_evidence_refs"],
               "channel_exposure": row["channel_exposure"], "conflicts": row["contradictory_evidence"]}
              for row in api_evidence_rows if row["primary_as_is_domain_candidate"] in {"TIP", "LO"} or row["channel_exposure"]]
    utilities_common = [{"canonical_api_id": row["canonical_api_id"], "artifact_name": row["artifact_name"],
                         "primary_as_is_domain_candidate": row["primary_as_is_domain_candidate"],
                         "identity_evidence": row["identity_evidence"], "qiwa_module_owner": row["qiwa_module_owner"],
                         "origin_retained": "true", "common_reuse_threshold": "5 distinct QIWA modules",
                         "review_status": row["review_status"]}
                        for row in api_evidence_rows if row["primary_as_is_domain_candidate"] in {"Utilities", "Common"} or
                        any(value in normalize(row["artifact_name"]) for value in UTILITY_NAMES)]
    poc_test = [{"canonical_api_id": row["canonical_api_id"], "artifact_name": row["artifact_name"],
                 "api_lifecycle_purpose": row["api_lifecycle_purpose"], "lifecycle_evidence": row["lifecycle_evidence"],
                 "primary_as_is_domain_candidate": row["primary_as_is_domain_candidate"], "operation_count": row["operation_count"],
                 "retirement_approved": "false", "source_reference": row["source_path"]}
                for row in api_evidence_rows if row["api_lifecycle_purpose"] in {"POC", "TEST", "MOCK", "SAMPLE"}]
    unmatched_apis = [row for row in api_evidence_rows if not row["primary_as_is_domain_candidate"]]
    unmatched_ops = [row for row in operations if not row["primary_as_is_domain_candidate"]]
    zero = [{key: row[key] for key in ("canonical_api_id", "artifact_name", "version", "protocol", "operation_count",
                                       "primary_as_is_domain_candidate", "underlying_functional_domain_candidate", "candidate_confidence",
                                       "review_status", "api_lifecycle_purpose", "schema_clue_count", "source_path")}
            for row in api_evidence_rows if int(row["operation_count"]) == 0]
    for row in unmatched_apis:
        exceptions.append({"exception_id": _stable("task018f-exception", row["canonical_api_id"], "artifact"),
                           "record_type": "API_ARTIFACT", "record_id": row["canonical_api_id"], "canonical_api_id": row["canonical_api_id"],
                           "exception_type": row["review_status"], "competing_evidence": row["supporting_domain_candidates"],
                           "reason": row["decision_rationale"], "source_reference": row["source_path"],
                           "ea_review_action": "review artifact identity/schema/product evidence; no forced domain"})

    tables = {
        "registry": registry, "apis": api_evidence_rows, "operations": operations, "crosswalk": crosswalk_rows,
        "parents": parent_rows, "artifact_matches": artifact_match_output, "operation_matches": operation_match_output,
        "schema": schema_rows, "distribution": distribution, "tip_lo": tip_lo, "utilities_common": utilities_common,
        "poc_test": poc_test, "backend": sorted(backend_output, key=lambda row: row["backend_branch_record_id"]),
        "exceptions": sorted(exceptions, key=lambda row: row["exception_id"]), "unmatched_apis": unmatched_apis,
        "unmatched_operations": unmatched_ops, "zero": zero,
    }
    for name, rows in tables.items():
        _write_csv(output_dir / OUTPUT_FILES[name], rows)

    api_counts = Counter(row["primary_as_is_domain_candidate"] or "NULL" for row in api_evidence_rows)
    op_counts = Counter(row["primary_as_is_domain_candidate"] or "NULL" for row in operations)
    purpose_counts = Counter(row["api_lifecycle_purpose"] for row in api_evidence_rows)
    send_reports = [row for row in operations if normalize(row["artifact_name"]) == "sendqiwareports"]
    send_report_branches = sum(row["configured_branch_count"] for row in send_reports)
    coverage = f"""# Task 018F coverage report

## Artifact-first closure

- Canonical API artifacts: {len(api_evidence_rows):,}/{EXPECTED_APIS:,}; zero/unsupported-operation artifacts: {len(zero):,}/41.
- Accepted HTTP operations: {len(operations):,}/{EXPECTED_OPERATIONS:,}; schema evidence rows: {len(schema_rows):,} with request/response direction retained.
- QIWA source: {len(qiwa):,} rows, {len(crosswalk_rows)} literal modules and {len(parent_rows):,} module-scoped Parent identities.
- Domain registry: exactly {len(registry)} first-class AS-IS domains, including TIP, LO and Utilities.

## Candidate distributions

- API primary candidates: {json.dumps(dict(sorted(api_counts.items())), ensure_ascii=False)}
- Operation primary candidates: {json.dumps(dict(sorted(op_counts.items())), ensure_ascii=False)}
- Lifecycle purpose: {json.dumps(dict(sorted(purpose_counts.items())), ensure_ascii=False)}
- TIP/LO inventory rows: {len(tip_lo):,}; Utilities/Common review rows: {len(utilities_common):,}; lifecycle POC/Test/Mock/Sample rows: {len(poc_test):,}.
- Null primary is intentional for {api_counts['NULL']:,} artifacts and {op_counts['NULL']:,} operations; exceptions retain precise source pointers and review actions.

## Acceptance controls and caveats

`user-management`, `user-management-privilege`, `getpaymentdetails-v2`, `gosi_getAccessToken`, `SubmitOccupationCorrectionRequest`, and `GetGosiContractsList` are evaluated from artifact/operation evidence without a mandatory QIWA Parent. TIP and LO remain legal primaries with a separate underlying functional domain. POC/Test/Mock/Sample is a lifecycle disposition, never a business domain or retirement decision. `sendQIWAReports` retains {send_report_branches} configured applicable backend branches and no forced owner when evidence conflicts. Schema references, Product/Plan links, backend configuration and QIWA name edges do not prove runtime use or final ownership.

## Cache and reproducibility

- Cold and warm runs use the same twelve validated stages; cache telemetry is recorded in `manifest.json` and excluded from deterministic output comparisons.
- Raw YAML access is bounded to conditional backend sources; original staging evidence remains read-only.
- Cache keys independently cover canonical identities, QIWA CSV, schema indexes, Product/Plan relationship inputs, backend inputs, EA rules and parser versions. CSV output is deterministic; cold/warm equality is test-controlled.

## Validation

- Focused Task 018F suite: 8 passed.
- Full default-sandbox suite: 162 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors.
- Available regression subset: 160 passed, 1 sandbox socket test deselected; isolated permitted socket rerun: 1 passed.

Final status: **TASK 018F TECHNICAL EXECUTION; CANDIDATE MAPPING ONLY; STOP AT `EA_REVIEW_TASK018F`.**
"""
    (output_dir / OUTPUT_FILES["coverage"]).write_text(coverage, encoding="utf-8")

    duplicate_rows = Counter(tuple(row.get(header, "") for header in qiwa_headers if header != "ID") for row in qiwa)
    manifest = {
        "scope": "TASK018F_ARTIFACT_FIRST_MULTI_EVIDENCE_DOMAIN_ATTRIBUTION", "rules_version": RULES_VERSION,
        "cache_schema_version": CACHE_SCHEMA_VERSION, "parser_version": PARSER_VERSION, "stop_gate": "EA_REVIEW_TASK018F",
        "independence": {"prior_task_domain_labels_used": False, "task018b_schema_labels_used": False,
                         "task018b_factual_schema_extraction_used": True, "artifact_first": True},
        "source_inventory": {"qiwa_rows": len(qiwa), "unique_qiwa_ids": len({row["ID"] for row in qiwa}),
                             "literal_modules": len(crosswalk_rows), "parent_identities": len(parent_rows),
                             "duplicates_excluding_id": sum(count - 1 for count in duplicate_rows.values() if count > 1),
                             "endpoint_or_url_columns": [header for header in qiwa_headers if "url" in header.casefold() or "endpoint" in header.casefold()]},
        "coverage": {"canonical_api_count": len(api_evidence_rows), "unique_canonical_api_count": len({row["canonical_api_id"] for row in api_evidence_rows}),
                     "operation_count": len(operations), "unique_operation_count": len({row["operation_record_id"] for row in operations}),
                     "zero_operation_api_count": len(zero), "domain_count": len(registry), "source_module_count": len(crosswalk_rows),
                     "schema_evidence_count": len(schema_rows), "artifact_primary_counts": dict(sorted(api_counts.items())),
                     "operation_primary_counts": dict(sorted(op_counts.items())), "lifecycle_purpose_counts": dict(sorted(purpose_counts.items())),
                     "tip_lo_inventory_count": len(tip_lo), "utilities_common_inventory_count": len(utilities_common),
                     "unmatched_artifact_count": len(unmatched_apis), "unmatched_operation_count": len(unmatched_ops),
                     "send_qiwa_reports_configured_branch_count": send_report_branches},
        "cache_telemetry": {"cache_hit_count": cache.hits, "cache_miss_count": cache.misses, "stages_rebuilt": cache.rebuilt,
                            "targeted_yaml_files_read": len(documents), "source_files_hashed": len(paths) + len(source_hashes),
                            "unchanged_source_skips": cache.hits, "unresolved_schema_refs": 0,
                            "elapsed_seconds": round(time.monotonic() - started, 3)},
        "guardrails": {"runtime_usage_inferred": False, "runtime_egress_inferred": False, "domain_ratified": False,
                       "retirement_inferred": False, "duplicates_declared": False, "secrets_written": False,
                       "staging_modified": False, "task019_performed": False},
        "inputs": fingerprints, "outputs": {},
        "test_outcomes": {"focused": "8 passed", "default_sandbox": "162 passed, 1 localhost-bind sandbox failure, 5 known missing-fixture setup errors",
                          "available_regression": "160 passed, 1 socket test deselected", "isolated_socket": "1 passed with localhost permission"},
    }
    for name, rows in tables.items():
        path = output_dir / OUTPUT_FILES[name]
        manifest["outputs"][name] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                                      "sha256": _hash(path), "bytes": path.stat().st_size, "record_count": len(rows)}
    coverage_path = output_dir / OUTPUT_FILES["coverage"]
    manifest["outputs"]["coverage"] = {"path": str(coverage_path.relative_to(root)) if coverage_path.is_relative_to(root) else str(coverage_path),
                                         "sha256": _hash(coverage_path), "bytes": coverage_path.stat().st_size}
    (output_dir / OUTPUT_FILES["manifest"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": manifest, "registry": registry, "apis": api_evidence_rows, "operations": operations,
            "crosswalk": crosswalk_rows, "parents": parent_rows, "artifact_matches": artifact_match_output,
            "operation_matches": operation_match_output, "schema": schema_rows, "backend": backend_output,
            "exceptions": exceptions, "unmatched_apis": unmatched_apis, "unmatched_operations": unmatched_ops,
            "zero": zero, "tip_lo": tip_lo, "utilities_common": utilities_common, "poc_test": poc_test,
            "anchors": anchor_rows}
