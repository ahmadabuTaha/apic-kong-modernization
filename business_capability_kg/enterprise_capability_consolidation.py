"""Task 019-F index-only Enterprise Capability consolidation.

The accepted 019-E-FINAL CSVs are the only semantic inputs.  This module
performs an additive Main-to-Enterprise join and never opens source bodies,
parse caches, schemas, or acquisition artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .final_main_capability_mapping import _atomic_write, _stable_id


INPUT_ROOT = Path("indexes/phase6/task019/019e_final")
OUTPUT_INDEX_ROOT = Path("indexes/phase6/task019/019f")
OUTPUT_REPORT_ROOT = Path("outputs/phase6/task019/019f")

INPUT_HASHES = {
    "coverage_exceptions.csv": "ed608a86a895f7211336ed5ec1c339d883e80edd9fa95c0f1b549fc2d2b14ce7",
    "excluded_sources.csv": "4de746b5d63a1068895050401736820c4ad8315aedec06cac4027087e25dbf59",
    "main_capabilities.csv": "ca608f6ea6d5a4ed4882970d2a1b48ae85faff90beb223f0ce956db0a60e6ad3",
    "main_icd_links.csv": "5dd3133a3089b6e105bf30d49e2be0ba29040de49f1b0d0686eedbd34e2607e1",
    "main_isd_links.csv": "60ef83771b0b603ee552e78c03c878d2efebd723bda2157d4449a9bcf72b7640",
    "module_coverage.csv": "ac093096228a7f81fd5dad286530b2af0ec3d1713b9814cb65246c358c1f1456",
}
EXPECTED = {
    "modules": 32, "mains": 136, "icd_links": 978, "isd_links": 123,
    "exclusions": 25, "exceptions": 5,
}
EXPECTED_EXCEPTION_PAGES = {"4883382387", "1062240312", "4416798854", "4939350056", "4237820100"}


MERGE_GROUPS: dict[str, dict[str, Any]] = {
    "saudization-certificate": {
        "name": "Saudization Certificate Management",
        "definition": "Validate, issue, retrieve, and monitor Saudization certificates.",
        "members": ("main-final-1e3551f7c83db3694822", "main-final-4353be644eeeff2757fa"),
        "rationale": "Both Module candidates manage the same Saudization certificate lifecycle and business object.",
    },
    "establishment-compliance": {
        "name": "Establishment Compliance Management",
        "definition": "Assess and manage establishment compliance, inspections, violations, punishments, and obligations.",
        "members": ("main-final-7c9225967152182a9fb1", "main-final-77797b7673101336ef1b"),
        "rationale": "Common and Establishment candidates express the same establishment-compliance outcome.",
    },
    "end-of-service-reward": {
        "name": "End of Service Reward Management",
        "definition": "Calculate end-of-service rewards and provide the supporting reference data.",
        "members": ("main-final-3c421be31e44dec2786c", "main-final-26596547e9c1f9badfe2"),
        "rationale": "Both candidates have the same reward-calculation outcome and object.",
    },
    "employment-contract-termination": {
        "name": "Employment Contract Termination Management",
        "definition": "Submit, assess, decide, cancel, search, and monitor employment-contract termination requests.",
        "members": ("main-final-fa8bd4f3dbbde49d7834", "main-final-c4e25eb147467dfaf7e4"),
        "rationale": "The Labor Office candidate is a channel-specific realization of the same termination lifecycle.",
    },
    "employee-transfer-lifecycle": {
        "name": "Employee Transfer Lifecycle Management",
        "definition": "Submit, validate, decide, cancel, and maintain employee-transfer and sponsorship-change requests.",
        "members": ("main-final-4a4da69a47784a6635a0", "main-final-f63654997bcf0b0e3533"),
        "rationale": "The Labor Office path and Employee Transfer Module manage the same transfer lifecycle.",
    },
    "establishment-location": {
        "name": "Establishment Location Management",
        "definition": "Create and maintain establishment locations and their laborer assignments.",
        "members": ("main-final-f877f91652ff5efed938", "main-final-aa32e4dcacdee992536c"),
        "rationale": "The Labor Office path preserves the same location and assignment outcome.",
    },
    "external-contract-lifecycle": {
        "name": "External Contract Lifecycle Management",
        "definition": "Create, maintain, retrieve, approve, cancel, and expire external contracts.",
        "members": ("main-final-7aeef9f3fa59b6d714c8", "main-final-427d3ff17d0f6921f85e"),
        "rationale": "Contracts and Work in Saudi provide complementary stages of the same external-contract lifecycle.",
    },
    "work-permit-lifecycle": {
        "name": "Work Permit Lifecycle Management",
        "definition": "Create, submit, retrieve, search, cancel, close, calculate, and update work-permit requests and statuses.",
        "members": ("main-final-5c63ecea73cd848e1bdc", "main-final-bd119adf3fdd34cd8539"),
        "rationale": "The Labor Office path is a channel-specific realization of the Work Permit lifecycle.",
    },
    "wage-protection-certificate": {
        "name": "Wage Protection Certificate Management",
        "definition": "Create, validate, issue, retrieve, update, and monitor Wage Protection certificates and compliance rates.",
        "members": ("main-final-aa324c126e686b89e95d", "main-final-039270fafa4c2476b473"),
        "rationale": "Both candidates manage the same Wage Protection certificate object and lifecycle.",
    },
}


BOUNDARY_REVIEWS = (
    {
        "key": "gosi-integration-scope", "priority": "HIGH",
        "members": ("main-final-052d3ce6178bd455e2b1", "main-final-ebc6eb4697d7ceb8883b"),
        "issue": "Contract-specific GOSI exchange versus broader GOSI workforce/contract integration.",
        "decision": "Confirm whether these are one Enterprise integration ability or ownership-specific capabilities.",
    },
    {
        "key": "nic-integration-scope", "priority": "HIGH",
        "members": ("main-final-f15714f9ed2653355261", "main-final-67a244f5112c1a951cde", "main-final-1b4bde48c0bbe6f7b872", "main-final-db97212c9688640c60a8", "main-final-78a68034bcecf38b25ae"),
        "issue": "NIC integrations carry different deceased-employee, transfer, event-reporting, workforce, and absence outcomes.",
        "decision": "Keep outcome-specific boundaries or approve a layered shared NIC integration capability.",
    },
    {
        "key": "nic-authentication-scope", "priority": "MEDIUM",
        "members": ("main-final-963c7e07ace85a2b497a", "main-final-cc97d23525c107f12a3b"),
        "issue": "NIC integration authentication and NIC identity authentication may represent different authentication subjects.",
        "decision": "Confirm whether token/integration authentication and user/identity authentication remain separate.",
    },
    {
        "key": "shared-visa-boundary", "priority": "HIGH",
        "members": ("main-final-261a3dc82ef2281c5816", "main-final-c818834ebe80dbff80e1", "main-final-b846bafb576461a6b94b"),
        "issue": "Shared Common and Labor Office visa services overlap the Visa Module's general lifecycle without identifying a single visa subtype.",
        "decision": "Confirm enterprise ownership and whether channel/shared realizations consolidate into general Visa Lifecycle Management.",
    },
    {
        "key": "shared-work-permit-boundary", "priority": "HIGH",
        "members": ("main-final-12c36c65e7becd0abec4", "main-final-5c63ecea73cd848e1bdc"),
        "issue": "Common provides shared work-permit data/debt/calculation while the Work Permit candidate owns the lifecycle.",
        "decision": "Confirm whether Common is a realization of the lifecycle or a distinct shared capability.",
    },
    {
        "key": "shared-payment-boundary", "priority": "HIGH",
        "members": ("main-final-1dc37830aca66e9c76a5", "main-final-480f3f5bf9004ee863dd", "main-final-5c733728fdc2f55fc5db", "main-final-46bbc6ce1b6131fd3ce9"),
        "issue": "Shared payment/billing, payment transactions, unified invoices, and work-permit billing have related but non-identical objects and ownership.",
        "decision": "Approve the enterprise payment/billing boundary without collapsing domain-specific billing lifecycles.",
    },
    {
        "key": "workforce-information-boundary", "priority": "MEDIUM",
        "members": ("main-final-4cd92e772022c7c15af1", "main-final-4a083b35b9f358aa11c6", "main-final-649f59a756c9e2a76709"),
        "issue": "Shared workforce data overlaps individual profile and laborer work-history outcomes.",
        "decision": "Confirm whether these are distinct information capabilities or approved specializations.",
    },
    {
        "key": "labor-office-occupation-boundary", "priority": "HIGH",
        "members": ("main-final-69b7823eb3fd0167ceaf", "main-final-33a682efbba460b90582", "main-final-1b0c60fe82bdae1bcbb1"),
        "issue": "Labor Office occupation services span both change and correction lifecycles.",
        "decision": "Assign the channel capability to one/both lifecycle capabilities only after EA boundary approval.",
    },
    {
        "key": "labor-office-certificate-boundary", "priority": "HIGH",
        "members": ("main-final-84457cd004d2ae8ee60b", "main-final-b2f9ec48b041bda9dd79", "main-final-c7b28dda2cf2baf57ce9", "main-final-ea50da4cb787778431a9"),
        "issue": "Labor Office certificate, Labor Office compliance certificate, compliance certificate, and generic enterprise certificate scopes overlap incompletely.",
        "decision": "Confirm the compliance-certificate ownership and whether the generic certificate candidates should be split or consolidated.",
    },
    {
        "key": "establishment-information-boundary", "priority": "MEDIUM",
        "members": ("main-final-cb493dadbf0d3ef53186", "main-final-e24e0a10f6a88ab05bf8"),
        "issue": "Shared establishment information overlaps the owning Module's establishment records lifecycle.",
        "decision": "Confirm shared realization versus a distinct enterprise information capability.",
    },
    {
        "key": "occupation-reference-boundary", "priority": "MEDIUM",
        "members": ("main-final-9bacb74763a42a530b97", "main-final-c37128ba1d32d0475957", "main-final-85fa35692c9dfee63559"),
        "issue": "Shared occupation/skills, occupation reference data, and professional-skills classification overlap but have different outcomes.",
        "decision": "Confirm specialization boundaries and whether any shared reference layer should be consolidated.",
    },
    {
        "key": "nitaqat-boundary", "priority": "MEDIUM",
        "members": ("main-final-abb384dd159a142c1220", "main-final-1a1c84767ec9e7eb1f97", "main-final-169bf6ca1ab99a72aa77"),
        "issue": "Common Nitaqat compliance evidence overlaps Nitaqat calculation and information capabilities.",
        "decision": "Confirm whether compliance is an enterprise parent, a separate ability, or a shared realization.",
    },
)


RELATED_MAIN_IDS = {
    "main-final-46583050e441843c128f", "main-final-9f923a9b2418d9461bd6",
    "main-final-e661b3c5466898413b0d", "main-final-1bead7618b7f678dcc2f",
    "main-final-5f48c677541a164a7552", "main-final-6fddd5a7b504db396cfe",
}

SINGLETON_NAME_OVERRIDES = {
    "main-final-ebc6eb4697d7ceb8883b": "GOSI Workforce and Contract Integration Management",
    "main-final-1b4bde48c0bbe6f7b872": "NIC Workforce Event Integration Management",
    "main-final-78a68034bcecf38b25ae": "Absence Reporting NIC Integration Management",
}

ENTERPRISE_FIELDS = [
    "enterprise_capability_id", "name", "definition", "candidate_status",
    "member_module_keys", "member_main_capability_ids", "member_main_count",
    "unique_linked_icd_documents", "unique_linked_isd_documents",
    "consolidation_rationale", "ambiguity",
]
MAIN_LINK_FIELDS = [
    "module_key", "module_name", "main_capability_id", "main_name", "main_description",
    "original_main_candidate_status", "original_main_source_types",
    "enterprise_capability_id", "enterprise_name", "relationship_type",
    "compact_rationale", "candidate_status",
]
TRACE_FIELDS = [
    "enterprise_capability_id", "enterprise_name", "enterprise_candidate_status",
    "relationship_type", "module_key", "module_name", "main_capability_id", "main_name",
    "original_main_candidate_status", "original_main_source_types",
    "source_type", "page_id", "document_key", "physical_identity", "title",
    "service_keys", "occurrence_ids", "blob_sha256", "source_version",
    "evidence_pointer", "evidence_excerpt", "external_entities",
    "source_mapping_status", "source_mapping_rationale", "classification_signals",
    "unpaired_reason",
]
REVIEW_FIELDS = [
    "review_id", "source_record_id", "review_type", "priority", "module_keys", "main_capability_ids",
    "enterprise_capability_ids", "source_type", "page_id", "document_key",
    "service_or_occurrence_ids", "issue", "rationale", "decision_needed",
    "status", "downstream_impact",
]
COVERAGE_FIELDS = [
    "record_type", "module_key", "module_name", "main_capability_id", "main_name",
    "enterprise_link_count", "enterprise_capability_ids", "linked_icd_unique_count",
    "linked_icd_page_ids", "linked_isd_unique_count", "linked_isd_page_ids",
    "traceability_row_count", "excluded_source_count", "excluded_occurrence_ids",
    "unresolved_source_count", "unresolved_source_ids", "closure_status",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])
    return stream.getvalue().encode("utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _load_inputs(input_root: Path) -> dict[str, list[dict[str, str]]]:
    if {path.name for path in input_root.glob("*.csv")} != set(INPUT_HASHES):
        raise ValueError("019E_FINAL_INPUT_FILE_SET_MISMATCH")
    actual_hashes = {name: _sha256(input_root / name) for name in INPUT_HASHES}
    if actual_hashes != INPUT_HASHES:
        raise ValueError(f"019E_FINAL_INPUT_HASH_MISMATCH:{actual_hashes}")
    data = {name: _read_csv(input_root / name) for name in INPUT_HASHES}
    counts = {
        "modules": len(data["module_coverage.csv"]),
        "mains": len(data["main_capabilities.csv"]),
        "icd_links": len(data["main_icd_links.csv"]),
        "isd_links": len(data["main_isd_links.csv"]),
        "exclusions": len(data["excluded_sources.csv"]),
        "exceptions": len(data["coverage_exceptions.csv"]),
    }
    if counts != EXPECTED:
        raise ValueError(f"019E_FINAL_INPUT_COUNT_MISMATCH:{counts}")
    mains = data["main_capabilities.csv"]
    main_ids = {row["main_capability_id"] for row in mains}
    if len(main_ids) != EXPECTED["mains"]:
        raise ValueError("019E_FINAL_MAIN_ID_DUPLICATE")
    declared = {member for group in MERGE_GROUPS.values() for member in group["members"]}
    declared.update(member for review in BOUNDARY_REVIEWS for member in review["members"])
    declared.update(RELATED_MAIN_IDS)
    if not declared <= main_ids:
        raise ValueError(f"CONSOLIDATION_REGISTRY_UNKNOWN_MAIN:{sorted(declared - main_ids)}")
    memberships = [member for group in MERGE_GROUPS.values() for member in group["members"]]
    if len(memberships) != len(set(memberships)):
        raise ValueError("CONSOLIDATION_MEMBER_OVERLAP")
    main_by_id = {row["main_capability_id"]: row for row in mains}
    for source_name in ("main_icd_links.csv", "main_isd_links.csv"):
        for row in data[source_name]:
            main = main_by_id.get(row["main_capability_id"])
            if not main or main["module_key"] != row["module_key"]:
                raise ValueError(f"019E_FINAL_DANGLING_SOURCE_LINK:{source_name}")
    linked_by_main: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for source_type, source_name in (("ICD", "main_icd_links.csv"), ("ISD", "main_isd_links.csv")):
        for row in data[source_name]:
            linked_by_main[row["main_capability_id"]].add((source_type, row["page_id"]))
    if any(len(linked_by_main[row["main_capability_id"]]) != int(row["linked_document_count"]) for row in mains):
        raise ValueError("019E_FINAL_MAIN_LINK_COUNT_MISMATCH")
    if {row["page_id"] for row in data["coverage_exceptions.csv"]} != EXPECTED_EXCEPTION_PAGES:
        raise ValueError("019E_FINAL_EXCEPTION_IDENTITY_MISMATCH")
    return data


def _enterprise_id(key: str) -> str:
    return _stable_id("enterprise-capability", key)


def _build_rows(data: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, Any]]]:
    mains = data["main_capabilities.csv"]
    main_by_id = {row["main_capability_id"]: row for row in mains}
    group_by_member = {
        member: key for key, group in MERGE_GROUPS.items() for member in group["members"]
    }
    review_by_member: dict[str, list[str]] = defaultdict(list)
    for review in BOUNDARY_REVIEWS:
        for member in review["members"]:
            review_by_member[member].append(review["key"])

    candidates: dict[str, list[dict[str, str]]] = defaultdict(list)
    for main in mains:
        candidate_key = group_by_member.get(main["main_capability_id"], f"main:{main['main_capability_id']}")
        candidates[candidate_key].append(main)
    original_name_counts = Counter(rows[0]["name"] for key, rows in candidates.items() if key.startswith("main:"))

    enterprise_rows, main_link_rows = [], []
    assignment: dict[str, dict[str, str]] = {}
    for candidate_key, members in sorted(candidates.items()):
        if candidate_key in MERGE_GROUPS:
            group = MERGE_GROUPS[candidate_key]
            name, definition = group["name"], group["definition"]
            rationale = group["rationale"]
            relationship = "equivalent_consolidation"
        else:
            main = members[0]
            name = SINGLETON_NAME_OVERRIDES.get(main["main_capability_id"], main["name"])
            if main["main_capability_id"] not in SINGLETON_NAME_OVERRIDES and original_name_counts[name] > 1:
                name = f"{main['module_name']} {name}"
            definition = main["description"]
            if review_by_member[main["main_capability_id"]]:
                relationship = "requires_ea_decision"
                rationale = "Retained as a separate candidate because indexed metadata does not resolve the queued enterprise boundary."
            elif main["main_capability_id"] in RELATED_MAIN_IDS:
                relationship = "related_but_distinct"
                rationale = "Related enterprise theme retained separately because its business object, provider, or ownership scope is distinct."
            else:
                relationship = "module_specific"
                rationale = "No positively evidenced equivalent Main exists in another Module; preserve the Module-specific boundary."
        enterprise_id = _enterprise_id(candidate_key)
        member_ids = {row["main_capability_id"] for row in members}
        icd_pages = {row["page_id"] for row in data["main_icd_links.csv"] if row["main_capability_id"] in member_ids}
        isd_pages = {row["page_id"] for row in data["main_isd_links.csv"] if row["main_capability_id"] in member_ids}
        ambiguity_keys = sorted({key for member in member_ids for key in review_by_member[member]})
        candidate_status = "requires_ea_decision" if ambiguity_keys else "candidate"
        enterprise_rows.append({
            "enterprise_capability_id": enterprise_id, "name": name, "definition": definition,
            "candidate_status": candidate_status,
            "member_module_keys": ";".join(sorted({row["module_key"] for row in members})),
            "member_main_capability_ids": ";".join(sorted(member_ids)),
            "member_main_count": len(members),
            "unique_linked_icd_documents": len(icd_pages),
            "unique_linked_isd_documents": len(isd_pages),
            "consolidation_rationale": rationale,
            "ambiguity": ";".join(ambiguity_keys),
        })
        for main in members:
            row_relationship = relationship
            row_rationale = rationale
            if candidate_key not in MERGE_GROUPS and review_by_member[main["main_capability_id"]]:
                row_relationship = "requires_ea_decision"
            link = {
                "module_key": main["module_key"], "module_name": main["module_name"],
                "main_capability_id": main["main_capability_id"], "main_name": main["name"],
                "main_description": main["description"], "enterprise_capability_id": enterprise_id,
                "original_main_candidate_status": main["candidate_status"],
                "original_main_source_types": main["source_types"],
                "enterprise_name": name, "relationship_type": row_relationship,
                "compact_rationale": row_rationale, "candidate_status": candidate_status,
            }
            main_link_rows.append(link)
            assignment[main["main_capability_id"]] = link

    trace_rows = []
    for source_type, source_name in (("ICD", "main_icd_links.csv"), ("ISD", "main_isd_links.csv")):
        for source in data[source_name]:
            link = assignment[source["main_capability_id"]]
            trace_rows.append({
                "enterprise_capability_id": link["enterprise_capability_id"],
                "enterprise_name": link["enterprise_name"],
                "enterprise_candidate_status": link["candidate_status"],
                "relationship_type": link["relationship_type"],
                "module_key": source["module_key"], "module_name": source["module_name"],
                "main_capability_id": source["main_capability_id"], "main_name": link["main_name"],
                "original_main_candidate_status": link["original_main_candidate_status"],
                "original_main_source_types": link["original_main_source_types"],
                "source_type": source_type,
                **{field: source.get(field, "") for field in (
                    "page_id", "document_key", "physical_identity", "title", "service_keys",
                    "occurrence_ids", "blob_sha256", "source_version", "evidence_pointer",
                    "evidence_excerpt", "external_entities",
                )},
                "source_mapping_status": source["mapping_status"],
                "source_mapping_rationale": source["mapping_rationale"],
                "classification_signals": source.get("classification_signals", ""),
                "unpaired_reason": source.get("unpaired_reason", ""),
            })

    review_rows = []
    for review in BOUNDARY_REVIEWS:
        members = [main_by_id[member] for member in review["members"]]
        review_rows.append({
            "review_id": _stable_id("review-019f", review["key"]),
            "source_record_id": "",
            "review_type": "CONSOLIDATION_BOUNDARY", "priority": review["priority"],
            "module_keys": ";".join(sorted({row["module_key"] for row in members})),
            "main_capability_ids": ";".join(review["members"]),
            "enterprise_capability_ids": ";".join(sorted({assignment[row["main_capability_id"]]["enterprise_capability_id"] for row in members})),
            "source_type": "", "page_id": "", "document_key": "", "service_or_occurrence_ids": "",
            "issue": review["issue"],
            "rationale": "019-E-FINAL names/descriptions show related semantics but do not prove equivalent enterprise ownership.",
            "decision_needed": review["decision"], "status": "EA_REVIEW_REQUIRED",
            "downstream_impact": "Canonical API capability attribution must preserve these alternatives until the Enterprise boundary is approved.",
        })
    for exception in data["coverage_exceptions.csv"]:
        review_rows.append({
            "review_id": _stable_id("review-019f-gap", exception["exception_id"]),
            "source_record_id": exception["exception_id"],
            "review_type": "UNRESOLVED_SOURCE_CARRY_FORWARD", "priority": "HIGH",
            "module_keys": exception["module_key"], "main_capability_ids": "",
            "enterprise_capability_ids": "", "source_type": exception["source_type"],
            "page_id": exception["page_id"], "document_key": exception["document_key"],
            "service_or_occurrence_ids": f"{exception['service_keys']} | {exception['occurrence_ids']}",
            "issue": exception["issue_type"], "rationale": exception["precise_reason"],
            "decision_needed": "Resolve source evidence before assigning any Enterprise Capability.",
            "status": exception["status"],
            "downstream_impact": "Unclassified source may leave Canonical API capability mapping unresolved later.",
        })
    for excluded in data["excluded_sources.csv"]:
        review_rows.append({
            "review_id": _stable_id("review-019f-excluded", excluded["exclusion_id"]),
            "source_record_id": excluded["exclusion_id"],
            "review_type": "SOURCE_EXCLUSION_CARRY_FORWARD", "priority": "LOW",
            "module_keys": excluded["module_key"], "main_capability_ids": "",
            "enterprise_capability_ids": "", "source_type": excluded["source_type"],
            "page_id": excluded["page_id"], "document_key": excluded["document_key"],
            "service_or_occurrence_ids": f"{excluded['service_key']} | {excluded['occurrence_id']}",
            "issue": f"Source-declared {excluded['source_marker']}",
            "rationale": excluded["exclusion_reason"],
            "decision_needed": "Retain outside active candidate links; do not infer verified runtime retirement.",
            "status": "CARRIED_FORWARD_EXCLUDED_NOT_RUNTIME_PROVEN",
            "downstream_impact": "Excluded source remains auditable and cannot silently contribute an Enterprise link.",
        })

    traces_by_main: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in trace_rows:
        traces_by_main[trace["main_capability_id"]].append(trace)
    coverage_rows = []
    for main in mains:
        traces = traces_by_main[main["main_capability_id"]]
        icd_pages = sorted({row["page_id"] for row in traces if row["source_type"] == "ICD"})
        isd_pages = sorted({row["page_id"] for row in traces if row["source_type"] == "ISD"})
        link = assignment[main["main_capability_id"]]
        coverage_rows.append({
            "record_type": "MAIN_CLOSURE", "module_key": main["module_key"],
            "module_name": main["module_name"], "main_capability_id": main["main_capability_id"],
            "main_name": main["name"], "enterprise_link_count": 1,
            "enterprise_capability_ids": link["enterprise_capability_id"],
            "linked_icd_unique_count": len(icd_pages), "linked_icd_page_ids": ";".join(icd_pages),
            "linked_isd_unique_count": len(isd_pages), "linked_isd_page_ids": ";".join(isd_pages),
            "traceability_row_count": len(traces), "excluded_source_count": 0,
            "excluded_occurrence_ids": "", "unresolved_source_count": 0,
            "unresolved_source_ids": "", "closure_status": "MAIN_ENTERPRISE_LINKED",
        })
    modules = data["module_coverage.csv"]
    for module in modules:
        exclusions = [row for row in data["excluded_sources.csv"] if row["module_key"] == module["module_key"]]
        exceptions = [row for row in data["coverage_exceptions.csv"] if row["module_key"] == module["module_key"]]
        coverage_rows.append({
            "record_type": "MODULE_SOURCE_CARRY_FORWARD", "module_key": module["module_key"],
            "module_name": module["module_name"], "main_capability_id": "", "main_name": "",
            "enterprise_link_count": 0, "enterprise_capability_ids": "",
            "linked_icd_unique_count": 0, "linked_icd_page_ids": "",
            "linked_isd_unique_count": 0, "linked_isd_page_ids": "", "traceability_row_count": 0,
            "excluded_source_count": len(exclusions),
            "excluded_occurrence_ids": ";".join(sorted(row["occurrence_id"] for row in exclusions)),
            "unresolved_source_count": len(exceptions),
            "unresolved_source_ids": ";".join(sorted(f"{row['source_type']}:{row['page_id']}:{row['document_key']}" for row in exceptions)),
            "closure_status": "SOURCE_GAPS_CARRIED_FORWARD" if exclusions or exceptions else "NO_SOURCE_GAPS",
        })

    return {
        "enterprise_capabilities.csv": sorted(enterprise_rows, key=lambda row: (row["name"], row["enterprise_capability_id"])),
        "main_enterprise_links.csv": sorted(main_link_rows, key=lambda row: (row["module_key"], row["main_capability_id"])),
        "enterprise_source_traceability.csv": sorted(trace_rows, key=lambda row: (row["module_key"], row["source_type"], row["page_id"], row["main_capability_id"])),
        "review_queue.csv": sorted(review_rows, key=lambda row: (row["review_type"], row["priority"], row["review_id"])),
        "coverage_reconciliation.csv": sorted(coverage_rows, key=lambda row: (row["module_key"], row["record_type"], row["main_capability_id"])),
    }


def _validate_outputs(data: dict[str, list[dict[str, str]]], rows: dict[str, list[dict[str, Any]]]) -> None:
    enterprise = rows["enterprise_capabilities.csv"]
    links = rows["main_enterprise_links.csv"]
    traces = rows["enterprise_source_traceability.csv"]
    review = rows["review_queue.csv"]
    coverage = rows["coverage_reconciliation.csv"]
    main_ids = {row["main_capability_id"] for row in data["main_capabilities.csv"]}
    if len(links) != len(main_ids) or {row["main_capability_id"] for row in links} != main_ids:
        raise ValueError("MAIN_ENTERPRISE_CLOSURE_MISMATCH")
    enterprise_ids = {row["enterprise_capability_id"] for row in enterprise}
    if len(enterprise_ids) != len(enterprise) or any(row["enterprise_capability_id"] not in enterprise_ids for row in links):
        raise ValueError("ENTERPRISE_REFERENTIAL_INTEGRITY_FAILURE")
    source_keys = {
        (source_type, row["main_capability_id"], row["page_id"], row["document_key"], row["service_keys"], row["occurrence_ids"])
        for source_type, name in (("ICD", "main_icd_links.csv"), ("ISD", "main_isd_links.csv"))
        for row in data[name]
    }
    trace_keys = {
        (row["source_type"], row["main_capability_id"], row["page_id"], row["document_key"], row["service_keys"], row["occurrence_ids"])
        for row in traces
    }
    if trace_keys != source_keys or len(traces) != len(source_keys):
        raise ValueError("SOURCE_TRACEABILITY_IDENTITY_MISMATCH")
    main_coverage = [row for row in coverage if row["record_type"] == "MAIN_CLOSURE"]
    module_coverage = [row for row in coverage if row["record_type"] == "MODULE_SOURCE_CARRY_FORWARD"]
    if len(main_coverage) != EXPECTED["mains"] or len(module_coverage) != EXPECTED["modules"]:
        raise ValueError("COVERAGE_RECONCILIATION_CLOSURE_MISMATCH")
    if sum(int(row["excluded_source_count"]) for row in module_coverage) != EXPECTED["exclusions"]:
        raise ValueError("EXCLUSION_CARRY_FORWARD_MISMATCH")
    if sum(int(row["unresolved_source_count"]) for row in module_coverage) != EXPECTED["exceptions"]:
        raise ValueError("EXCEPTION_CARRY_FORWARD_MISMATCH")
    review_types = Counter(row["review_type"] for row in review)
    expected_review_types = Counter({
        key: value for key, value in {
            "CONSOLIDATION_BOUNDARY": len(BOUNDARY_REVIEWS),
            "SOURCE_EXCLUSION_CARRY_FORWARD": EXPECTED["exclusions"],
            "UNRESOLVED_SOURCE_CARRY_FORWARD": EXPECTED["exceptions"],
        }.items() if value
    })
    if review_types != expected_review_types:
        raise ValueError(f"REVIEW_QUEUE_CLOSURE_MISMATCH:{dict(review_types)}")
    if any("/" in row["name"] or len(row["name"].split()) < 2 for row in enterprise):
        raise ValueError("INVALID_ENTERPRISE_CAPABILITY_NAME")


def _summary(data: dict[str, list[dict[str, str]]], rows: dict[str, list[dict[str, Any]]]) -> bytes:
    enterprise = rows["enterprise_capabilities.csv"]
    links = rows["main_enterprise_links.csv"]
    traces = rows["enterprise_source_traceability.csv"]
    relationship_counts = Counter(row["relationship_type"] for row in links)
    merged = [row for row in enterprise if int(row["member_main_count"]) > 1]
    unique_icd = len({row["physical_identity"] for row in traces if row["source_type"] == "ICD"})
    unique_isd = len({row["physical_identity"] for row in traces if row["source_type"] == "ISD"})
    icd_example = next(row for row in traces if row["source_type"] == "ICD")
    isd_example = next(row for row in traces if row["source_type"] == "ISD")
    exception_lines = [
        f"- `{row['module_key']}` {row['source_type']} page `{row['page_id']}` / `{row['document_key']}` — {row['issue_type']}: {row['precise_reason']}"
        for row in data["coverage_exceptions.csv"]
    ]
    exclusion_groups: dict[str, list[str]] = defaultdict(list)
    for row in data["excluded_sources.csv"]:
        exclusion_groups[row["module_key"]].append(
            f"{row['source_type']}:{row['page_id']}:{row['document_key']}:{row['source_marker']}"
        )
    exclusion_lines = [
        f"- `{module}` ({len(identities)}): " + "; ".join(f"`{identity}`" for identity in sorted(identities))
        for module, identities in sorted(exclusion_groups.items())
    ]
    merge_lines = [
        f"- **{row['name']}** — {row['member_module_keys']} / {row['member_main_capability_ids']}; "
        f"{row['unique_linked_icd_documents']} ICD and {row['unique_linked_isd_documents']} ISD documents. {row['consolidation_rationale']}"
        for row in merged
    ]
    boundary_lines = [
        f"- `{review['key']}` ({review['priority']}): {review['issue']} Decision: {review['decision']}"
        for review in BOUNDARY_REVIEWS
    ]
    text = (
        "# Phase 6 Task 019-F review summary\n\n"
        "## Consolidation closure\n\n"
        f"- All {EXPECTED['mains']} accepted Module-local Main identities across {EXPECTED['modules']} Modules have exactly one additive Enterprise candidate link; no 019-E-FINAL row was changed.\n"
        f"- Proposed Enterprise inventory: {len(enterprise)} candidates. Relationship rows: "
        + ", ".join(f"{key}={value}" for key, value in sorted(relationship_counts.items())) + ".\n"
        f"- Source traceability preserves {EXPECTED['icd_links']} ICD link rows over {unique_icd} physical identities and {EXPECTED['isd_links']} unpaired ISD link rows over {unique_isd} physical identities, with original Module, Main, page/document, Service, occurrence, hash, version, and evidence pointers.\n"
        f"- Review queue: {len(BOUNDARY_REVIEWS)} consolidation boundaries, {EXPECTED['exceptions']} unresolved-source carry-forwards, and {EXPECTED['exclusions']} source-exclusion carry-forwards. Enterprise names and boundaries remain candidates pending EA review.\n\n"
        "## Positively supported consolidations\n\n" + "\n".join(merge_lines) + "\n\n"
        "## Boundary decisions queued early\n\n" + "\n".join(boundary_lines) + "\n\n"
        "## Direct trace examples\n\n"
        f"- ICD: `{icd_example['module_key']}` → `{icd_example['page_id']}` / `{icd_example['service_keys']}` → `{icd_example['main_capability_id']}` → `{icd_example['enterprise_capability_id']}`, evidence `{icd_example['evidence_pointer']}`.\n"
        f"- Unpaired ISD: `{isd_example['module_key']}` → `{isd_example['page_id']}` / `{isd_example['service_keys']}` → `{isd_example['main_capability_id']}` → `{isd_example['enterprise_capability_id']}`, evidence `{isd_example['evidence_pointer']}`.\n\n"
        "## Unresolved sources carried forward unchanged\n\n" + "\n".join(exception_lines) + "\n\n"
        "Each may leave future Canonical API capability attribution unresolved; no Enterprise link was invented.\n\n"
        "## Explicit source exclusions retained\n\n" + "\n".join(exclusion_lines) + "\n\n"
        "These markers are source declarations only and do not prove runtime retirement.\n\n"
        "## Validation and stop\n\n"
        "- PASS: accepted input hashes and 32-Module/136-Main closure validated; trace projection exactly equals the authoritative 019-E-FINAL link identities; unique-document coverage was not inflated.\n"
        "- PASS: five unresolved sources and all 25 exclusions remain separately identifiable; no source document, parser/cache, API, endpoint, Business Function, Sub Capability, or Kong artifact was read or created.\n"
        "- Final status: `ENTERPRISE_CAPABILITY_CANDIDATES_COMPLETE_WITH_EA_DECISIONS`; STOP at `EA_REVIEW_019F`.\n"
    )
    return text.encode("utf-8")


def build_enterprise_consolidation(
    root: Path, input_root: Path | None = None, index_root: Path | None = None,
    report_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    input_root = (input_root or root / INPUT_ROOT).resolve()
    index_root = (index_root or root / OUTPUT_INDEX_ROOT).resolve()
    report_root = (report_root or root / OUTPUT_REPORT_ROOT).resolve()
    before = {name: _sha256(input_root / name) for name in INPUT_HASHES}
    data = _load_inputs(input_root)
    rows = _build_rows(data)
    _validate_outputs(data, rows)
    fields = {
        "enterprise_capabilities.csv": ENTERPRISE_FIELDS,
        "main_enterprise_links.csv": MAIN_LINK_FIELDS,
        "enterprise_source_traceability.csv": TRACE_FIELDS,
        "review_queue.csv": REVIEW_FIELDS,
        "coverage_reconciliation.csv": COVERAGE_FIELDS,
    }
    payloads = {name: _csv_bytes(rows[name], fields[name]) for name in fields}
    summary = _summary(data, rows)
    for name, payload in payloads.items():
        _atomic_write(index_root / name, payload)
    _atomic_write(report_root / "review_summary.md", summary)
    after = {name: _sha256(input_root / name) for name in INPUT_HASHES}
    if before != after:
        raise ValueError("019E_FINAL_INPUT_MUTATED")
    return {
        "counts": {
            "enterprise_capabilities": len(rows["enterprise_capabilities.csv"]),
            "main_enterprise_links": len(rows["main_enterprise_links.csv"]),
            "traceability_rows": len(rows["enterprise_source_traceability.csv"]),
            "review_queue": len(rows["review_queue.csv"]),
            "coverage_reconciliation": len(rows["coverage_reconciliation.csv"]),
        },
        "hashes": {
            **{name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
            "review_summary.md": hashlib.sha256(summary).hexdigest(),
        },
        "input_hashes": before, "status": "EA_REVIEW_019F",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-F index-only Enterprise Capability consolidation")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--report-root", type=Path)
    args = parser.parse_args()
    result = build_enterprise_consolidation(args.root, args.input_root, args.index_root, args.report_root)
    import json
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
