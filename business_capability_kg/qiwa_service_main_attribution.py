"""Task 019-G bounded Qiwa API-HTTP service to Module Main attribution.

Only the Qiwa parent/child CSV, accepted 019-E-FINAL indexes, recovery catalog
metadata, and the 019-F lineage checksum are read.  No source body, parser,
schema, API artifact, or Neo4j server is used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .final_main_capability_mapping import _atomic_write, _stable_id


QIWA_CSV = Path("neo4j/csv/Qiwa_Modules_Services.csv")
CATALOG = Path("indexes/phase6/task019/019d/retrieval_catalog.sqlite3")
INPUT_019E = Path("indexes/phase6/task019/019e_final")
INPUT_019F = Path("indexes/phase6/task019/019f/main_enterprise_links.csv")
INDEX_ROOT = Path("indexes/phase6/task019/019g")
OUTPUT_ROOT = Path("outputs/phase6/task019/019g")

INPUT_HASHES = {
    "qiwa_csv": "85499b04989f0ea93214d277709ab265f718744ea21cbcd96f9a8b635a34d877",
    "catalog": "c6a7bb7ba5ff7e314e2e41482394db6e1d75ba6319db3e43c02894daf1171e76",
    "main_capabilities": "ca608f6ea6d5a4ed4882970d2a1b48ae85faff90beb223f0ce956db0a60e6ad3",
    "main_icd_links": "5dd3133a3089b6e105bf30d49e2be0ba29040de49f1b0d0686eedbd34e2607e1",
    "main_isd_links": "60ef83771b0b603ee552e78c03c878d2efebd723bda2157d4449a9bcf72b7640",
    "coverage_exceptions": "ed608a86a895f7211336ed5ec1c339d883e80edd9fa95c0f1b549fc2d2b14ce7",
    "excluded_sources": "4de746b5d63a1068895050401736820c4ad8315aedec06cac4027087e25dbf59",
    "main_enterprise_links": "4ae70dd882779890040506312cc95401203d8b48dfc3838db29a9fb51dbab73b",
}
EXPECTED = {
    "qiwa_rows": 4437, "api_http_rows": 633, "api_http_parents": 289,
    "recovery_services": 952, "mains": 136, "enterprise_candidates": 127,
    "icd_links": 978, "isd_links": 123, "source_gaps": 5, "source_exclusions": 25,
}

# Literal Qiwa relationship Module -> accepted recovery Module owner context.
# Missing labels remain unmatched rather than being guessed.  Several Qiwa
# Modules intentionally converge on one accepted recovery Module.
MODULE_CROSSWALK = {
    "Absense Mgmt": "module-termination-for-absence-expat-laborer",
    "Capptions": "module-capptions",
    "Change Occupation": "module-occupations",
    "Common": "module-common",
    "Contract Mgmt": "module-contracts",
    "Data Portal": "module-data-portal",
    "Decease Mgmt": "module-deceased-employee-entitlement",
    "EFM": "module-establishment",
    "ET": "module-employee-transfer",
    "End Of Service Reward": "module-end-of-service-reward",
    "Establishment Loc": "module-establishment",
    "Establishment logo": "module-establishment",
    "LMH": "module-lmh",
    "LO": "module-labor-offices",
    "Nitaqat": "module-nitaqat",
    "Occupation Mgmt": "module-occupations",
    "Payment": "module-payments",
    "Proactive Awareness": "module-establishment",
    "Salary Certificate": "module-certificates",
    "Training Contract": "module-contracts",
    "Training Indicators": "module-training-indicators",
    "User Mgmt": "module-user-management",
    "Visa Mgmt": "module-visa",
    "Wage Protection": "module-wage-protection",
    "Work Permit": "module-work-permit",
    "Work Policy": "module-work-policies",
    "Work in Saudi": "module-work-in-saudi",
}

INVENTORY_FIELDS = [
    "api_service_id", "qiwa_module_name", "api_http_parent_service",
    "normalized_parent_service", "eligibility_row_ids", "eligibility_relationship_pointers",
    "api_http_child_services", "expected_recovery_module_key",
    "resolved_source_service_key", "resolved_source_service_name", "direct_main_ids",
    "direct_coverage_status", "direct_match_certainty", "child_usage_row_count",
    "resolved_support_context_count", "unresolved_child_usage_count", "child_usage_status",
    "evidence_basis", "runtime_usage_proven",
]
LINK_FIELDS = [
    "link_id", "api_service_id", "qiwa_module_name", "api_http_parent_service",
    "main_capability_id", "main_capability_name", "target_module_key", "target_module_name",
    "link_type", "consuming_parent_service_id", "consuming_parent_service_name",
    "resolved_consumer_source_service_key", "source_types", "source_page_ids",
    "source_document_keys", "source_service_keys", "source_occurrence_ids",
    "source_evidence_pointers", "qiwa_relationship_row_ids", "qiwa_relationship_pointers",
    "evidence_basis", "certainty", "candidate_status", "runtime_usage_proven",
]
EXCEPTION_FIELDS = [
    "exception_id", "exception_category", "severity", "api_service_id",
    "qiwa_module_name", "api_http_parent_service", "consuming_parent_service_id",
    "consuming_parent_service_name", "qiwa_relationship_row_ids",
    "qiwa_relationship_pointers", "source_service_candidates", "source_record_id",
    "source_type", "page_id", "document_key", "source_service_or_occurrence_ids",
    "precise_reason", "mapping_impact", "status",
]


def _normalize(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path, *, bom: bool = False) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig" if bom else "utf-8", newline="") as stream:
        return [{key: value or "" for key, value in row.items()} for row in csv.DictReader(stream)]


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])
    return stream.getvalue().encode("utf-8")


def _joined(values: Any) -> str:
    return ";".join(sorted({str(value) for value in values if value not in (None, "")}))


def _api_service_id(module_name: str, normalized_parent: str) -> str:
    return _stable_id("qiwa-api-http-service", module_name, normalized_parent)


def _qiwa_parent_id(module_name: str, parent_name: str) -> str:
    return _stable_id("qiwa-parent-service", module_name, _normalize(parent_name))


def _input_paths(root: Path) -> dict[str, Path]:
    return {
        "qiwa_csv": root / QIWA_CSV,
        "catalog": root / CATALOG,
        "main_capabilities": root / INPUT_019E / "main_capabilities.csv",
        "main_icd_links": root / INPUT_019E / "main_icd_links.csv",
        "main_isd_links": root / INPUT_019E / "main_isd_links.csv",
        "coverage_exceptions": root / INPUT_019E / "coverage_exceptions.csv",
        "excluded_sources": root / INPUT_019E / "excluded_sources.csv",
        "main_enterprise_links": root / INPUT_019F,
    }


def _load_inputs(root: Path) -> dict[str, Any]:
    paths = _input_paths(root)
    if any(not path.is_file() for path in paths.values()):
        missing = [name for name, path in paths.items() if not path.is_file()]
        raise ValueError(f"MISSING_REQUIRED_INPUT:{missing}")
    actual_hashes = {name: _hash(path) for name, path in paths.items()}
    if actual_hashes != INPUT_HASHES:
        raise ValueError(f"ACCEPTED_INPUT_HASH_MISMATCH:{actual_hashes}")
    qiwa = _read_csv(paths["qiwa_csv"], bom=True)
    required = {"ID", "Service_Name", "Type", "Parent_Service", "Service_Normalized", "Module_Name"}
    if not qiwa or not required <= set(qiwa[0]):
        raise ValueError(f"UNSUITABLE_QIWA_CSV_MISSING_FIELDS:{sorted(required - set(qiwa[0] if qiwa else {}))}")
    mains = _read_csv(paths["main_capabilities"])
    icd_links = _read_csv(paths["main_icd_links"])
    isd_links = _read_csv(paths["main_isd_links"])
    gaps = _read_csv(paths["coverage_exceptions"])
    exclusions = _read_csv(paths["excluded_sources"])
    enterprise_links = _read_csv(paths["main_enterprise_links"])
    connection = sqlite3.connect(f"file:{paths['catalog']}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        services = [dict(row) for row in connection.execute(
            "SELECT service_key, module_key, service_name FROM services ORDER BY service_key"
        )]
    finally:
        connection.close()
    api_http_rows = [row for row in qiwa if row["Type"].strip().casefold() == "api-http"]
    parent_identities = {(row["Module_Name"].strip(), _normalize(row["Parent_Service"])) for row in api_http_rows}
    counts = {
        "qiwa_rows": len(qiwa), "api_http_rows": len(api_http_rows),
        "api_http_parents": len(parent_identities), "recovery_services": len(services),
        "mains": len(mains), "enterprise_candidates": len({row["enterprise_capability_id"] for row in enterprise_links}),
        "icd_links": len(icd_links), "isd_links": len(isd_links),
        "source_gaps": len(gaps), "source_exclusions": len(exclusions),
    }
    if counts != EXPECTED:
        raise ValueError(f"ACCEPTED_INPUT_CLOSURE_MISMATCH:{counts}")
    if len({row["main_capability_id"] for row in enterprise_links}) != EXPECTED["mains"]:
        raise ValueError("019F_MAIN_LINEAGE_CLOSURE_MISMATCH")
    return {
        "paths": paths, "hashes": actual_hashes, "qiwa": qiwa,
        "api_http_rows": api_http_rows, "services": services, "mains": mains,
        "icd_links": icd_links, "isd_links": isd_links, "gaps": gaps,
        "exclusions": exclusions, "enterprise_links": enterprise_links,
    }


def _source_associations(data: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    associations: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source_type, name in (("ICD", "icd_links"), ("ISD", "isd_links")):
        for row in data[name]:
            enriched = {**row, "_source_type": source_type}
            for service_key in row["service_keys"].split(";"):
                associations[service_key].append(enriched)
    return associations


def _resolve_parent(
    module_name: str, parent_name: str, services_by_module_name: dict[tuple[str, str], list[dict[str, str]]],
    services_by_name: dict[str, list[dict[str, str]]], associations: dict[str, list[dict[str, str]]],
    gaps_by_service: dict[str, list[dict[str, str]]], exclusions_by_service: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    normalized = _normalize(parent_name)
    target_module = MODULE_CROSSWALK.get(module_name, "")
    within = services_by_module_name.get((target_module, normalized), []) if target_module else []
    global_candidates = services_by_name.get(normalized, [])
    result = {
        "expected_module_key": target_module, "service": None, "associations": [],
        "status": "", "certainty": "", "reason": "", "candidate_services": global_candidates,
    }
    if not target_module:
        result.update(
            status="NO_MATCHING_SOURCE_SERVICE", certainty="UNRESOLVED",
            reason=f"Qiwa Module {module_name!r} has no accepted recovery Module crosswalk; no name-only cross-Module assertion was made.",
        )
        return result
    if len(within) > 1:
        result.update(
            status="AMBIGUOUS_SERVICE_IDENTITY", certainty="AMBIGUOUS",
            reason="Multiple recovery Services share the controlled normalized identity inside the expected Module.",
        )
        return result
    if not within:
        if global_candidates:
            result.update(
                status="AMBIGUOUS_SERVICE_IDENTITY", certainty="MODULE_CONFLICT",
                reason="Normalized name exists only in a different recovery Module; ownership conflict prevents an asserted join.",
            )
        else:
            result.update(
                status="NO_MATCHING_SOURCE_SERVICE", certainty="UNRESOLVED",
                reason="No recovery Service exists with this controlled normalized identity in the expected Module.",
            )
        return result
    service = within[0]
    source_links = associations.get(service["service_key"], [])
    result["service"] = service
    result["associations"] = source_links
    if source_links:
        result.update(
            status="MATCHED", certainty="CORROBORATED_NORMALIZED_WITHIN_MODULE_SOURCE_LINK",
            reason="Unique within-Module normalized Service identity is independently corroborated by accepted ICD/ISD Main source links.",
        )
    elif gaps_by_service.get(service["service_key"]):
        result.update(
            status="SOURCE_DOCUMENT_UNRESOLVED", certainty="UNRESOLVED_SOURCE",
            reason="Recovery Service resolves, but its source document is an accepted unresolved 019-E-FINAL gap.",
        )
    elif exclusions_by_service.get(service["service_key"]):
        result.update(
            status="SOURCE_EXCLUDED_OLD_IGNORE", certainty="EXCLUDED_SOURCE_NOT_RUNTIME_PROVEN",
            reason="Recovery Service resolves only to source-declared OLD/IGNORE evidence excluded from active Main links.",
        )
    else:
        result.update(
            status="PARENT_WITH_NO_MAIN_EVIDENCE", certainty="NO_ACCEPTED_MAIN_SOURCE_EDGE",
            reason="Recovery Service resolves, but no accepted ICD/ISD source association links it to a Main.",
        )
    return result


def _association_evidence(rows: list[dict[str, str]], main_id: str) -> dict[str, str]:
    selected = [row for row in rows if row["main_capability_id"] == main_id]
    return {
        "source_types": _joined(row["_source_type"] for row in selected),
        "source_page_ids": _joined(row["page_id"] for row in selected),
        "source_document_keys": _joined(
            key for row in selected for key in row["document_key"].split(";")
        ),
        "source_service_keys": _joined(
            key for row in selected for key in row["service_keys"].split(";")
        ),
        "source_occurrence_ids": _joined(
            occurrence for row in selected for occurrence in row["occurrence_ids"].split(";")
        ),
        "source_evidence_pointers": _joined(row["evidence_pointer"] for row in selected),
    }


def _exception(
    category: str, reason: str, impact: str, *, api_service_id: str = "",
    module_name: str = "", api_parent: str = "", consumer_id: str = "", consumer_name: str = "",
    row_ids: str = "", candidates: str = "", source_record_id: str = "", source_type: str = "",
    page_id: str = "", document_key: str = "", source_ids: str = "", severity: str = "HIGH",
) -> dict[str, str]:
    pointer = _joined(f"neo4j/csv/Qiwa_Modules_Services.csv#ID={row_id}" for row_id in row_ids.split(";") if row_id)
    return {
        "exception_id": _stable_id(
            "qiwa-main-exception", category, api_service_id, module_name, api_parent,
            consumer_id, row_ids, source_record_id, page_id,
        ),
        "exception_category": category, "severity": severity,
        "api_service_id": api_service_id, "qiwa_module_name": module_name,
        "api_http_parent_service": api_parent, "consuming_parent_service_id": consumer_id,
        "consuming_parent_service_name": consumer_name,
        "qiwa_relationship_row_ids": row_ids, "qiwa_relationship_pointers": pointer,
        "source_service_candidates": candidates, "source_record_id": source_record_id,
        "source_type": source_type, "page_id": page_id, "document_key": document_key,
        "source_service_or_occurrence_ids": source_ids, "precise_reason": reason,
        "mapping_impact": impact, "status": "EA_REVIEW_REQUIRED" if severity != "INFO" else "INFORMATIONAL",
    }


def _build_rows(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    mains = {row["main_capability_id"]: row for row in data["mains"]}
    associations = _source_associations(data)
    services_by_module_name: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    services_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for service in data["services"]:
        normalized = _normalize(service["service_name"])
        services_by_module_name[(service["module_key"], normalized)].append(service)
        services_by_name[normalized].append(service)
    gaps_by_service: dict[str, list[dict[str, str]]] = defaultdict(list)
    for gap in data["gaps"]:
        for service_key in gap["service_keys"].split(";"):
            gaps_by_service[service_key].append(gap)
    exclusions_by_service: dict[str, list[dict[str, str]]] = defaultdict(list)
    for excluded in data["exclusions"]:
        exclusions_by_service[excluded["service_key"]].append(excluded)

    eligible_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in data["api_http_rows"]:
        eligible_groups[(row["Module_Name"].strip(), _normalize(row["Parent_Service"]))].append(row)
    eligible_by_name: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for identity in eligible_groups:
        eligible_by_name[identity[1]].append(identity)

    # Direct one-hop reuse rows.  A self-edge is not "another Parent_Service".
    usage_by_api: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    ambiguous_usage_rows: list[tuple[list[tuple[str, str]], dict[str, str]]] = []
    for row in data["qiwa"]:
        service_name = _normalize(row["Service_Name"])
        identities = eligible_by_name.get(service_name, [])
        if not identities or _normalize(row["Parent_Service"]) == service_name:
            continue
        if len(identities) == 1:
            usage_by_api[identities[0]].append(row)
        else:
            ambiguous_usage_rows.append((identities, row))

    inventory, links, exceptions = [], [], []
    link_keys: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    resolutions: dict[tuple[str, str], dict[str, Any]] = {}
    for (module_name, normalized_parent), eligibility in sorted(eligible_groups.items()):
        parent_names = sorted({row["Parent_Service"].strip() for row in eligibility})
        parent_name = parent_names[0]
        api_id = _api_service_id(module_name, normalized_parent)
        resolution = _resolve_parent(
            module_name, parent_name, services_by_module_name, services_by_name,
            associations, gaps_by_service, exclusions_by_service,
        )
        resolutions[(module_name, normalized_parent)] = resolution
        main_ids = sorted({row["main_capability_id"] for row in resolution["associations"]})
        if resolution["status"] == "MATCHED":
            for main_id in main_ids:
                evidence = _association_evidence(resolution["associations"], main_id)
                row_ids = _joined(row["ID"] for row in eligibility)
                key = (api_id, main_id, "PROVIDES", "")
                link_keys[key] = {
                    "link_id": _stable_id("qiwa-main-link", *key),
                    "api_service_id": api_id, "qiwa_module_name": module_name,
                    "api_http_parent_service": parent_name, "main_capability_id": main_id,
                    "main_capability_name": mains[main_id]["name"],
                    "target_module_key": mains[main_id]["module_key"],
                    "target_module_name": mains[main_id]["module_name"], "link_type": "PROVIDES",
                    "consuming_parent_service_id": "", "consuming_parent_service_name": "",
                    "resolved_consumer_source_service_key": resolution["service"]["service_key"],
                    **evidence, "qiwa_relationship_row_ids": row_ids,
                    "qiwa_relationship_pointers": _joined(
                        f"neo4j/csv/Qiwa_Modules_Services.csv#ID={row['ID']}" for row in eligibility
                    ),
                    "evidence_basis": "Qiwa API-HTTP parent identity + unique within-Module recovery Service + accepted ICD/ISD Service-to-Main edge",
                    "certainty": resolution["certainty"], "candidate_status": "candidate",
                    "runtime_usage_proven": "false",
                }
        else:
            candidate_text = _joined(
                f"{service['module_key']}|{service['service_key']}|{service['service_name']}"
                for service in resolution["candidate_services"]
            )
            exceptions.append(_exception(
                resolution["status"], resolution["reason"],
                "This eligible API-HTTP Parent has no asserted PROVIDES Main link.",
                api_service_id=api_id, module_name=module_name, api_parent=parent_name,
                row_ids=_joined(row["ID"] for row in eligibility), candidates=candidate_text,
            ))

        usage_rows = usage_by_api.get((module_name, normalized_parent), [])
        resolved_usage_keys, unresolved_usage = set(), 0
        for usage in usage_rows:
            consumer_name = usage["Parent_Service"].strip()
            consumer_id = _qiwa_parent_id(usage["Module_Name"].strip(), consumer_name)
            consumer = _resolve_parent(
                usage["Module_Name"].strip(), consumer_name, services_by_module_name,
                services_by_name, associations, gaps_by_service, exclusions_by_service,
            )
            if consumer["status"] != "MATCHED":
                unresolved_usage += 1
                exceptions.append(_exception(
                    consumer["status"], consumer["reason"],
                    "Child reuse is observed, but no SUPPORTS Main link can be asserted without an independently evidenced consumer Parent-to-Main edge.",
                    api_service_id=api_id, module_name=module_name, api_parent=parent_name,
                    consumer_id=consumer_id, consumer_name=consumer_name, row_ids=usage["ID"],
                    candidates=_joined(
                        f"{service['module_key']}|{service['service_key']}|{service['service_name']}"
                        for service in consumer["candidate_services"]
                    ),
                ))
                continue
            for main_id in sorted({row["main_capability_id"] for row in consumer["associations"]}):
                key = (api_id, main_id, "SUPPORTS", consumer_id)
                evidence = _association_evidence(consumer["associations"], main_id)
                if key not in link_keys:
                    link_keys[key] = {
                        "link_id": _stable_id("qiwa-main-link", *key),
                        "api_service_id": api_id, "qiwa_module_name": module_name,
                        "api_http_parent_service": parent_name, "main_capability_id": main_id,
                        "main_capability_name": mains[main_id]["name"],
                        "target_module_key": mains[main_id]["module_key"],
                        "target_module_name": mains[main_id]["module_name"], "link_type": "SUPPORTS",
                        "consuming_parent_service_id": consumer_id,
                        "consuming_parent_service_name": consumer_name,
                        "resolved_consumer_source_service_key": consumer["service"]["service_key"],
                        **evidence, "qiwa_relationship_row_ids": usage["ID"],
                        "qiwa_relationship_pointers": f"neo4j/csv/Qiwa_Modules_Services.csv#ID={usage['ID']}",
                        "evidence_basis": "Direct Qiwa child-to-consuming-Parent row + independently resolved consumer recovery Service-to-Main ICD/ISD edge",
                        "certainty": "DIRECT_ONE_HOP_AND_CORROBORATED_CONSUMER_MAIN",
                        "candidate_status": "candidate", "runtime_usage_proven": "false",
                    }
                else:
                    existing = link_keys[key]
                    existing["qiwa_relationship_row_ids"] = _joined(
                        existing["qiwa_relationship_row_ids"].split(";") + [usage["ID"]]
                    )
                    existing["qiwa_relationship_pointers"] = _joined(
                        existing["qiwa_relationship_pointers"].split(";")
                        + [f"neo4j/csv/Qiwa_Modules_Services.csv#ID={usage['ID']}"]
                    )
                resolved_usage_keys.add(key)

        inventory.append({
            "api_service_id": api_id, "qiwa_module_name": module_name,
            "api_http_parent_service": parent_name, "normalized_parent_service": normalized_parent,
            "eligibility_row_ids": _joined(row["ID"] for row in eligibility),
            "eligibility_relationship_pointers": _joined(
                f"neo4j/csv/Qiwa_Modules_Services.csv#ID={row['ID']}" for row in eligibility
            ),
            "api_http_child_services": _joined(row["Service_Name"].strip() for row in eligibility),
            "expected_recovery_module_key": resolution["expected_module_key"],
            "resolved_source_service_key": resolution["service"]["service_key"] if resolution["service"] else "",
            "resolved_source_service_name": resolution["service"]["service_name"] if resolution["service"] else "",
            "direct_main_ids": _joined(main_ids),
            "direct_coverage_status": "PROVIDES_MAIN_CAPABILITY" if resolution["status"] == "MATCHED" else resolution["status"],
            "direct_match_certainty": resolution["certainty"],
            "child_usage_row_count": len(usage_rows),
            "resolved_support_context_count": len(resolved_usage_keys),
            "unresolved_child_usage_count": unresolved_usage,
            "child_usage_status": (
                "NO_CHILD_USAGE_EVIDENCED" if not usage_rows else
                "ALL_CHILD_USAGE_RESOLVED" if not unresolved_usage else
                "PARTIAL_CHILD_USAGE_RESOLVED" if resolved_usage_keys else "CHILD_USAGE_UNRESOLVED"
            ),
            "evidence_basis": resolution["reason"], "runtime_usage_proven": "false",
        })

    for identities, usage in ambiguous_usage_rows:
        exceptions.append(_exception(
            "AMBIGUOUS_SERVICE_IDENTITY",
            "The child Service normalized identity denotes multiple eligible API-HTTP Parent identities; no provider identity was selected.",
            "No SUPPORTS link was generated for this relationship row.",
            module_name=usage["Module_Name"].strip(), api_parent=usage["Service_Name"].strip(),
            consumer_id=_qiwa_parent_id(usage["Module_Name"].strip(), usage["Parent_Service"]),
            consumer_name=usage["Parent_Service"].strip(), row_ids=usage["ID"],
            candidates=_joined(f"{module}|{normalized}" for module, normalized in identities),
        ))

    # Accepted gaps and exclusions remain distinct context.  They never acquire
    # a link merely because the Qiwa CSV contains a similar service name.
    api_by_source_service: dict[str, set[str]] = defaultdict(set)
    for row in inventory:
        if row["resolved_source_service_key"]:
            api_by_source_service[row["resolved_source_service_key"]].add(row["api_service_id"])
    for gap in data["gaps"]:
        service_keys = gap["service_keys"].split(";")
        related_apis = _joined(api for service in service_keys for api in api_by_source_service.get(service, set()))
        exceptions.append(_exception(
            "SOURCE_DOCUMENT_UNRESOLVED", gap["precise_reason"],
            "Unclassified source may leave later service/API capability attribution unresolved; no Main link was invented.",
            api_service_id=related_apis, module_name=gap["module_name"],
            source_record_id=gap["exception_id"], source_type=gap["source_type"],
            page_id=gap["page_id"], document_key=gap["document_key"],
            source_ids=f"{gap['service_keys']} | {gap['occurrence_ids']}",
        ))
    for excluded in data["exclusions"]:
        related_apis = _joined(api_by_source_service.get(excluded["service_key"], set()))
        exceptions.append(_exception(
            "SOURCE_EXCLUDED_OLD_IGNORE", excluded["exclusion_reason"],
            "Source stays outside active service-to-Main links; marker is not proof of runtime retirement.",
            api_service_id=related_apis, module_name=excluded["module_name"],
            source_record_id=excluded["exclusion_id"], source_type=excluded["source_type"],
            page_id=excluded["page_id"], document_key=excluded["document_key"],
            source_ids=f"{excluded['service_key']} | {excluded['occurrence_id']}", severity="INFO",
        ))

    links = list(link_keys.values())
    return {
        "api_http_service_inventory.csv": sorted(inventory, key=lambda row: (row["qiwa_module_name"], row["normalized_parent_service"])),
        "api_main_capability_links.csv": sorted(
            links, key=lambda row: (row["api_service_id"], row["link_type"], row["target_module_key"], row["main_capability_id"], row["consuming_parent_service_id"])
        ),
        "review_exceptions.csv": sorted(
            exceptions, key=lambda row: (row["exception_category"], row["qiwa_module_name"], row["api_http_parent_service"], row["exception_id"])
        ),
    }


def _validate_outputs(data: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    inventory = rows["api_http_service_inventory.csv"]
    links = rows["api_main_capability_links.csv"]
    exceptions = rows["review_exceptions.csv"]
    if len(inventory) != EXPECTED["api_http_parents"] or len({row["api_service_id"] for row in inventory}) != len(inventory):
        raise ValueError("API_HTTP_PARENT_INVENTORY_CLOSURE_MISMATCH")
    api_ids = {row["api_service_id"] for row in inventory}
    main_ids = {row["main_capability_id"] for row in data["mains"]}
    if any(row["api_service_id"] not in api_ids or row["main_capability_id"] not in main_ids for row in links):
        raise ValueError("SERVICE_MAIN_REFERENTIAL_INTEGRITY_FAILURE")
    unresolved_inventory = [row for row in inventory if row["direct_coverage_status"] != "PROVIDES_MAIN_CAPABILITY"]
    direct_exception_api_ids = {
        row["api_service_id"] for row in exceptions
        if row["exception_category"] in {
            "NO_MATCHING_SOURCE_SERVICE", "AMBIGUOUS_SERVICE_IDENTITY",
            "PARENT_WITH_NO_MAIN_EVIDENCE", "SOURCE_DOCUMENT_UNRESOLVED", "SOURCE_EXCLUDED_OLD_IGNORE",
        } and row["api_http_parent_service"]
    }
    if {row["api_service_id"] for row in unresolved_inventory} - direct_exception_api_ids:
        raise ValueError("UNACCOUNTED_API_HTTP_PARENT")
    for row in links:
        if row["link_type"] == "SUPPORTS" and (
            not row["qiwa_relationship_pointers"] or not row["resolved_consumer_source_service_key"]
            or not row["source_evidence_pointers"] or row["certainty"] != "DIRECT_ONE_HOP_AND_CORROBORATED_CONSUMER_MAIN"
        ):
            raise ValueError("SUPPORTS_TWO_EVIDENCE_RULE_FAILURE")
    link_keys = {
        (row["api_service_id"], row["main_capability_id"], row["link_type"], row["consuming_parent_service_id"])
        for row in links
    }
    if len(link_keys) != len(links):
        raise ValueError("SERVICE_MAIN_LINK_DUPLICATION")
    if any(row["runtime_usage_proven"] != "false" for row in inventory + links):
        raise ValueError("RUNTIME_USAGE_INFERENCE_FORBIDDEN")
    counts = Counter(row["link_type"] for row in links)
    return {
        "direct_providers": sum(row["direct_coverage_status"] == "PROVIDES_MAIN_CAPABILITY" for row in inventory),
        "unresolved_parents": len(unresolved_inventory),
        "no_child_usage": sum(row["child_usage_status"] == "NO_CHILD_USAGE_EVIDENCED" for row in inventory),
        "provides_links": counts["PROVIDES"], "supports_links": counts["SUPPORTS"],
        "review_exceptions": len(exceptions),
        "exception_categories": dict(sorted(Counter(row["exception_category"] for row in exceptions).items())),
    }


def _summary(data: dict[str, Any], rows: dict[str, list[dict[str, Any]]], counts: dict[str, Any]) -> bytes:
    inventory = rows["api_http_service_inventory.csv"]
    links = rows["api_main_capability_links.csv"]
    direct_unresolved: dict[str, list[str]] = defaultdict(list)
    for row in inventory:
        if row["direct_coverage_status"] != "PROVIDES_MAIN_CAPABILITY":
            direct_unresolved[row["direct_coverage_status"]].append(
                f"{row['api_service_id']}={row['qiwa_module_name']}::{row['api_http_parent_service']}"
            )
    unresolved_lines = [
        f"- **{status}** ({len(items)}): " + "; ".join(f"`{item}`" for item in sorted(items))
        for status, items in sorted(direct_unresolved.items())
    ]
    examples, seen_modules = [], set()
    for row in links:
        if row["link_type"] != "SUPPORTS" or row["target_module_key"] in seen_modules:
            continue
        seen_modules.add(row["target_module_key"])
        examples.append(
            f"- `{row['api_http_parent_service']}` --SUPPORTS via `{row['consuming_parent_service_name']}` / "
            f"`{row['qiwa_relationship_pointers']}`→ `{row['target_module_key']}` / `{row['main_capability_name']}`; "
            f"consumer evidence `{row['source_evidence_pointers']}`."
        )
        if len(examples) == 6:
            break
    child_rows = sum(int(row["child_usage_row_count"]) for row in inventory)
    unresolved_child_rows = sum(int(row["unresolved_child_usage_count"]) for row in inventory)
    support_api_count = len({row["api_service_id"] for row in links if row["link_type"] == "SUPPORTS"})
    category_text = ", ".join(f"{key}={value}" for key, value in counts["exception_categories"].items())
    text = (
        "# Phase 6 Task 019-G review summary\n\n"
        "## Coverage\n\n"
        f"- Source CSV: {EXPECTED['qiwa_rows']} relationship rows; {EXPECTED['api_http_rows']} rows with child `Type=API-HTTP`; "
        f"{EXPECTED['api_http_parents']} distinct Module+Parent identities form the eligible inventory. `Type` classifies `Service_Name`; "
        "the selected `Parent_Service` is the consuming/orchestrating parent on those rows.\n"
        f"- Direct attribution: {counts['direct_providers']}/{EXPECTED['api_http_parents']} eligible parents resolve to accepted recovery Services and produce "
        f"{counts['provides_links']} `PROVIDES` links; {counts['unresolved_parents']} remain explicit, not forced.\n"
        f"- One-hop reuse: {child_rows} direct child-use rows were observed for eligible service names. "
        f"{counts['supports_links']} deduplicated `SUPPORTS` links span {support_api_count} API service identities; "
        f"{unresolved_child_rows} relationship rows lack an independently evidenced consumer Parent-to-Main join. "
        f"{counts['no_child_usage']} eligible parents have informational `NO_CHILD_USAGE_EVIDENCED`.\n"
        f"- Preserved lineage: {EXPECTED['mains']} Module-local Mains and {EXPECTED['enterprise_candidates']} Enterprise candidates remain byte-unchanged. "
        "No Enterprise mapping was read as classification input or modified.\n"
        f"- Review exceptions: {counts['review_exceptions']} rows ({category_text}), including all {EXPECTED['source_gaps']} accepted source gaps and "
        f"{EXPECTED['source_exclusions']} OLD/IGNORE carry-forwards. Runtime use is not proven.\n\n"
        "## Cross-Module one-hop examples\n\n" + "\n".join(examples) + "\n\n"
        "## Unmatched and ambiguous eligible parents by stable ID and name\n\n"
        + "\n".join(unresolved_lines) + "\n\n"
        "Full exact relationship-level causes and candidate identities are in `review_exceptions.csv`.\n\n"
        "## Controls and stop\n\n"
        "- PASS: every eligible API-HTTP Parent is directly mapped or carries an exact status; every SUPPORTS row has both a Qiwa child→consumer pointer and accepted consumer Service→Main source evidence.\n"
        "- PASS: deduplication key is API service + Main + link type + consuming parent; traversal is one hop only; no name-only cross-Module assertion, runtime inference, source-body read, Canonical API match, or Neo4j import occurred.\n"
        "- Final status: `QIWA_SERVICE_MAIN_ATTRIBUTION_COMPLETE_WITH_EXCEPTIONS`; STOP at `EA_REVIEW_019G`.\n"
    )
    return text.encode("utf-8")


def build_qiwa_service_main_attribution(
    root: Path, index_root: Path | None = None, output_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    paths = _input_paths(root)
    before = {name: _hash(path) for name, path in paths.items()}
    data = _load_inputs(root)
    rows = _build_rows(data)
    counts = _validate_outputs(data, rows)
    fields = {
        "api_http_service_inventory.csv": INVENTORY_FIELDS,
        "api_main_capability_links.csv": LINK_FIELDS,
        "review_exceptions.csv": EXCEPTION_FIELDS,
    }
    payloads = {name: _csv_bytes(rows[name], fields[name]) for name in fields}
    summary = _summary(data, rows, counts)
    for name, payload in payloads.items():
        _atomic_write(index_root / name, payload)
    _atomic_write(output_root / "review_summary.md", summary)
    after = {name: _hash(path) for name, path in paths.items()}
    if before != after:
        raise ValueError("ACCEPTED_INPUT_MUTATED")
    return {
        "counts": {"api_http_inventory": len(rows["api_http_service_inventory.csv"]),
                   "links": len(rows["api_main_capability_links.csv"]), **counts},
        "hashes": {
            **{name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
            "review_summary.md": hashlib.sha256(summary).hexdigest(),
        },
        "input_hashes": before, "status": "EA_REVIEW_019G",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-G bounded Qiwa service-to-Main attribution")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = build_qiwa_service_main_attribution(args.root, args.index_root, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
