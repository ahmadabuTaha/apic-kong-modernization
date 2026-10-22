"""Task 019-E-R2 direct Establishment Main Capability to ICD mapping.

This is intentionally a bounded, corpus-reviewed mapping rather than a new
generic extraction pipeline.  It reuses the accepted recovery catalog and the
existing structured-document parser, reads every Establishment ICD directly,
and emits only Main Capability candidates, Main-to-ICD links, and coverage
exceptions.  It never derives Business Functions or Sub Capabilities.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .document_cache import DocumentCatalog
from .icd_capability_extraction import _sanitize_evidence, _sha256_file, _stable_id, parse_document


MODULE_KEY = "module-establishment"
MODULE_NAME = "Establishment"
RECOVERY_INDEX = Path("indexes/phase6/task019/recovery")
RECOVERY_OUTPUT = Path("outputs/phase6/task019/recovery")
RECOVERY_CATALOG = RECOVERY_INDEX / "retrieval_catalog.sqlite3"
INDEX_ROOT = Path("indexes/phase6/task019/019e_r2")
OUTPUT_ROOT = Path("outputs/phase6/task019/019e_r2")

MAIN_FIELDS = ["main_capability_id", "label", "short_definition", "candidate_status"]
LINK_FIELDS = [
    "main_capability_id", "page_id", "document_key", "physical_identity", "title",
    "source_service_keys", "occurrence_ids", "blob_sha256", "source_version",
    "evidence_pointer", "evidence_excerpt", "mapping_status", "mapping_rationale",
]
EXCEPTION_FIELDS = [
    "exception_id", "exception_type", "service_key", "document_type", "page_id",
    "document_key", "title", "inspected_evidence_pointer", "precise_reason", "status",
]

MAIN_CAPABILITIES: dict[str, tuple[str, str]] = {
    "registration-opening": (
        "Establishment Registration and Opening",
        "Open establishment files, branches, or unified identities through evidenced registration routes.",
    ),
    "activity-management": (
        "Establishment Activity and Classification Management",
        "Maintain establishment economic activities, classifications, eligibility, and related Nitaqat context.",
    ),
    "location-management": (
        "Establishment Location and Labor Assignment Management",
        "Create and maintain establishment locations and laborer-to-location assignments.",
    ),
    "license-management": (
        "Establishment License Management",
        "Retrieve, validate, link, and maintain licenses associated with an establishment.",
    ),
    "ownership-representation": (
        "Establishment Ownership, Legal Form, and Representation Management",
        "Maintain owners, ownership transfers, managers, parties, legal form, and representatives.",
    ),
    "record-hierarchy": (
        "Establishment Record and Commercial Registration Management",
        "Maintain establishment profile, hierarchy, unified-number, and commercial-registration records.",
    ),
    "request-agent": (
        "Establishment Request and Government Agent Management",
        "Submit, review, search, approve, or reject establishment requests involving agents and owners.",
    ),
    "closure": (
        "Establishment Closure Management",
        "Close establishments and maintain closure outcomes arising from commercial-registration status.",
    ),
    "compliance-violation": (
        "Establishment Compliance, Violation, and Punishment Management",
        "Assess compliance and manage violations, punishments, supervision, grace periods, and related obligations.",
    ),
    "logo-management": (
        "Establishment Logo Management",
        "Add, retrieve, and update an establishment logo.",
    ),
    "stakeholder-notification": (
        "Establishment Stakeholder Notification",
        "Notify owners, managers, or representatives about establishment events.",
    ),
}

# Direct corpus decisions made after inspection of the recovered document
# narratives. Page identities, not names, are the stable classification keys.
PAGES_BY_CAPABILITY: dict[str, tuple[str, ...]] = {
    "registration-opening": (
        "6048907298", "3694166278", "3245211779", "3707994130", "3698098593",
        "3711041654", "3855548417", "3625812053", "3855777822", "4410834983",
        "5120131530", "5518950691", "5849382920", "5943951453", "5111054370", "5213388805",
        "5854953519", "2795569225",
    ),
    "activity-management": (
        "4306928194", "3654025630", "4960486318", "3720872046", "3654025258",
        "3929604097", "3953229825", "3945594881", "3945562113", "5962727522",
        "3654025672", "5264932881", "3114958917", "3707044080", "3656319057",
        "3410591873", "4138991632", "5803409409", "5241077773", "3716776124",
        "3906633729",
    ),
    "location-management": (
        "3954081821", "5910954017", "3674406974", "3554869309", "3555721311",
        "3740106937", "3747741704", "3357900868", "3403874395", "4727406649",
        "6669468351", "6286934017", "3713433710", "4434362402", "3950116871",
        "6215335937",
    ),
    "license-management": (
        "4611801236", "5974130698", "6134169639", "3694166278", "3250159702",
        "6144622593", "4469358656", "4818141186", "5195038752", "4904353793",
        "4303781892", "3301998678",
    ),
    "ownership-representation": (
        "2805530681", "3249700927", "4138959277", "5228134466", "4149837838",
        "5253365761", "5537988674", "4147773441", "5204082701", "5439226404",
        "4742184961", "4112515155", "5313888257", "5227184186", "5921767504",
        "4349263916", "6012928070",
    ),
    "record-hierarchy": (
        "6236012607", "6430359607", "3698000406", "3645341969", "4665638913", "5315199059",
        "4132732960", "5095784510", "5120425985", "4149706788", "4151542155",
        "5276237825", "5213225041", "4151869441", "5131534337", "4410343516",
        "5219057666", "5241012231", "4149706760", "5195595793", "4151542188",
        "5213192197", "5437718607", "4147773471", "5115052033", "5803573249",
        "4768399408", "5149458443", "4014604437", "5855248385", "4828463170", "5256709217",
        "3691216955", "4904353793", "3855810584", "3855777793", "3743809778",
        "5827788807", "5245502567",
    ),
    "request-agent": (
        "4109697171", "2971467779", "3906338817", "4109435173", "2933818029",
        "4104258100",
    ),
    "closure": ("6578340012", "4151542188"),
    "compliance-violation": (
        "5321064557", "4495147488", "6335594609", "6684770376", "6250528820",
        "5460787201", "6310232211", "4541939879", "5450301441", "4223369975",
        "4820926465", "6317637657", "933625864", "932937780", "932806750",
        "936444077",
    ),
    "logo-management": ("4110549791", "4110582503", "4111073316"),
    "stakeholder-notification": ("3879960577", "4203806731"),
}

EVIDENCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "registration-opening": (r"\bopen", r"\bcreate a new establishment", r"\bestablishment file"),
    "activity-management": (r"\bactivit", r"\bisic", r"\bnitaqat", r"\bsaudization"),
    "location-management": (r"\blocation", r"\blaborer", r"\bcities lookup"),
    "license-management": (r"\blicen[cs]" ,),
    "ownership-representation": (r"\bownership", r"\bowner", r"\bmanager", r"\bparties", r"\bentity type", r"\bforeign investor", r"\biqama"),
    "record-hierarchy": (
        r"\bcr\b", r"\bcrnationalnumber", r"\bcommercial registration", r"\bprofile",
        r"\bunified ?number", r"\bcontact", r"\bfarming establishments?", r"\bcity based",
        r"\bupdate establishments? in", r"\bestablishment (?:statement|status|information|as main)",
    ),
    "request-agent": (r"\bgovernment agent", r"\bestablishments? requests?", r"\bsearch all establishments and requests"),
    "closure": (r"\bclose (?:an )?establishments?", r"\bclosure"),
    "compliance-violation": (r"\bviolation", r"\bpunishment", r"\bgrace period", r"\blegal issues", r"\bcompliant", r"\bsubsequent supervision"),
    "logo-management": (r"\blogo",),
    "stakeholder-notification": (r"\bemail notification", r"\bnotify"),
}

# Mapped documents whose own metadata/narrative needs explicit EA attention.
MAPPED_AMBIGUITIES: dict[str, str] = {
    "3694166278": "The narrative retrieves TGA license information while a separate scope statement says it opens a file without CR for external entities; both candidate links are retained.",
    "4306928194": "The title says Cancel GSB License while the purpose and scope describe closing an establishment activity; mapping follows the body semantics.",
    "5149458443": "The title says Workers Housing Licenses Scheduler while the body says it receives updated CR information from MCI; mapping follows the body semantics.",
    "5213225041": "The title says Update Company Form while the body describes CR capital updates; mapping follows the body semantics.",
    "5437718607": "The title says Update Owner Data while the body describes CR name updates; mapping follows the body semantics.",
    "5213388805": "The catalog classifies this occurrence as ICD although the source title contains 'ICD- ISD'; the recovered metadata type is preserved and the body supports establishment opening.",
    "5245502567": "The title says Transfer Ownership Engine while the scheduler scope describes routing general CR-detail update requests; mapping follows the body as Record and Commercial Registration Management.",
    "4904353793": "The narrative explicitly updates licenses and/or CR records according to activity requirements; both direct candidate links are retained for review.",
    "4151542188": "The narrative closes an establishment and updates its status from MCI CR status; Closure and Record links are both retained.",
}

FLAGGED_SERVICE_INPUT = (
    "module-establishment::service-get-farming-establishments-by-owner",
    "module-establishment::service-update-cr-details",
    "module-establishment::service-establishment-logo-icds",
    "module-establishment::service-terminate-establishments-punishments-icd",
    "module-establishment::service-establishment-logo-icds",
    "module-establishment::service-update-cr-detailsv2",
    "module-establishment::service-mci-swap-cr",
    "module-establishment::service-manage-establishment-license",
    "module-establishment::service-mci-swap-cr-v2",
    "module-establishment::service-violation-management-interface-specification-documents",
    "module-establishment::service-manual-cr-swap-v2",
    "module-establishment::service-momra-auto-push-utility",
    "module-establishment::service-push-mecca-locations-changes-scheduler",
    "module-establishment::service-transfer-ownership-engine-schedularv2",
    "module-establishment::service-push-subsequent-supervision-license",
    "module-establishment::service-mci-update-cr-cityv2",
    "module-establishment::service-get-subsequent-supervision-notification",
    "module-establishment::service-establishment-logo-isds",
    "module-establishment::service-establishment-logo-icds",
    "module-establishment::service-set-establishment-as-a-main-hrsd",
    "module-establishment::service-transfer-ownership-engine-schedular",
    "module-establishment::service-manual-cr-swap",
)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _validated_recovery(root: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = root / RECOVERY_OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "phase6-document-recovery-v1":
        raise ValueError("RECOVERY_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("status") != "EA_REVIEW_DOCUMENT_RECOVERY":
        raise ValueError("RECOVERY_STATUS_MISMATCH")
    catalog_path = root / RECOVERY_CATALOG
    catalog = manifest["catalog"]
    if catalog_path.stat().st_size != int(catalog["size_bytes"]) or _sha256_file(catalog_path) != catalog["sha256"]:
        raise ValueError("RECOVERY_CATALOG_INTEGRITY_MISMATCH")
    return catalog_path, manifest


def _main_id(key: str) -> str:
    return _stable_id("main-r2", MODULE_KEY, key)


def _page_assignments() -> dict[str, tuple[str, ...]]:
    assignments: dict[str, list[str]] = defaultdict(list)
    for capability_key, pages in PAGES_BY_CAPABILITY.items():
        if capability_key not in MAIN_CAPABILITIES:
            raise ValueError(f"UNKNOWN_MAIN_CAPABILITY:{capability_key}")
        for page_id in pages:
            if capability_key in assignments[page_id]:
                raise ValueError(f"DUPLICATE_PAGE_MAIN_ASSIGNMENT:{page_id}:{capability_key}")
            assignments[page_id].append(capability_key)
    return {page_id: tuple(keys) for page_id, keys in assignments.items()}


def _semantic_blocks(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    narrative: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    for block in parsed.get("blocks", []):
        text = str(block.get("text") or "").strip()
        if len(text) < 15 or block.get("kind") == "heading":
            continue
        lower = text.casefold()
        section = str(block.get("section_heading") or "").casefold()
        if block.get("kind") in {"paragraph", "list_item", "table_row"}:
            fallback.append(block)
        if (
            any(token in lower for token in (
                "this service", "this scheduler", "this utility", "the scope", "the purpose",
                "this purpose", "to allow", "service retrieves",
            ))
            or any(token in section for token in ("purpose", "scope", "introduction", "overview"))
        ):
            narrative.append(block)
    return narrative or fallback


def _evidence_for(capability_key: str, parsed: dict[str, Any]) -> dict[str, Any] | None:
    blocks = _semantic_blocks(parsed)
    for pattern in EVIDENCE_PATTERNS[capability_key]:
        for block in blocks:
            if re.search(pattern, str(block.get("text") or ""), re.I):
                return block
    return None


def _exception(
    exception_type: str, service_key: str, reason: str, *, document_type: str = "",
    page_id: str = "", document_key: str = "", title: str = "", pointer: str = "",
    status: str = "EA_REVIEW_REQUIRED",
) -> dict[str, str]:
    return {
        "exception_id": _stable_id("exception-r2", exception_type, service_key, page_id, document_key),
        "exception_type": exception_type, "service_key": service_key, "document_type": document_type,
        "page_id": page_id, "document_key": document_key, "title": title,
        "inspected_evidence_pointer": pointer, "precise_reason": reason, "status": status,
    }


def build_main_icd_mapping(
    root: Path, index_root: Path | None = None, output_root: Path | None = None
) -> dict[str, Any]:
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    catalog_path, recovery_manifest = _validated_recovery(root)
    assignments = _page_assignments()
    main_rows = [
        {
            "main_capability_id": _main_id(key), "label": label,
            "short_definition": definition, "candidate_status": "candidate",
        }
        for key, (label, definition) in sorted(MAIN_CAPABILITIES.items(), key=lambda item: item[1][0])
    ]
    link_rows: list[dict[str, Any]] = []
    exceptions: list[dict[str, str]] = []
    parsed_count = 0

    with DocumentCatalog(root, catalog_path) as catalog:
        modules = [row for row in catalog.list_modules() if row["module_name"] == MODULE_NAME]
        if len(modules) != 1 or modules[0]["module_key"] != MODULE_KEY:
            raise ValueError("LITERAL_ESTABLISHMENT_MODULE_NOT_FOUND")
        services = catalog.list_services(MODULE_KEY)
        icd_occurrences = catalog.list_documents(MODULE_KEY, document_type="ICD")
        isd_occurrences = catalog.list_documents(MODULE_KEY, document_type="ISD")
        if len(services) != 142 or len(icd_occurrences) != 149:
            raise ValueError(f"ESTABLISHMENT_SCOPE_MISMATCH:{len(services)}:{len(icd_occurrences)}")

        icds_by_page: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in icd_occurrences:
            icds_by_page[row["page_id"]].append(row)
        if set(assignments) != set(icds_by_page):
            missing = sorted(set(icds_by_page) - set(assignments))
            fabricated = sorted(set(assignments) - set(icds_by_page))
            raise ValueError(f"ICD_MAPPING_CLOSURE_MISMATCH:missing={missing}:fabricated={fabricated}")

        for page_id in sorted(icds_by_page):
            occurrences = icds_by_page[page_id]
            document_keys = {row["document_key"] for row in occurrences}
            physical = {row["physical_identity"] for row in occurrences}
            hashes = {row["blob_sha256"] for row in occurrences}
            if len(document_keys) != 1 or len(physical) != 1 or len(hashes) != 1:
                raise ValueError(f"PAGE_IDENTITY_CONFLICT:{page_id}")
            document = occurrences[0]
            result, body = catalog.load_document(document["document_key"])
            if body is None:
                exceptions.append(_exception(
                    "UNRESOLVED_ICD_CONTENT", document["service_key"],
                    f"Recovered ICD could not be read: {result['status']}", document_type="ICD",
                    page_id=page_id, document_key=document["document_key"], title=document["title"],
                    pointer=document["blob_sha256"],
                ))
                continue
            parsed = parse_document(body, document["mime_type"])
            parsed_count += 1
            if parsed.get("parse_status") != "PARSED":
                exceptions.append(_exception(
                    "UNRESOLVED_ICD_CONTENT", document["service_key"],
                    f"Recovered ICD parse status is {parsed.get('parse_status')}: {parsed.get('gap_reason', '')}",
                    document_type="ICD", page_id=page_id, document_key=document["document_key"],
                    title=document["title"], pointer=document["blob_sha256"],
                ))
                continue

            for capability_key in assignments[page_id]:
                evidence = _evidence_for(capability_key, parsed)
                if evidence is None:
                    exceptions.append(_exception(
                        "UNRESOLVED_ICD_EVIDENCE", document["service_key"],
                        f"Direct corpus decision for {MAIN_CAPABILITIES[capability_key][0]} lacks a matching narrative evidence block",
                        document_type="ICD", page_id=page_id, document_key=document["document_key"],
                        title=document["title"], pointer=document["blob_sha256"],
                    ))
                    continue
                services_for_page = sorted({row["service_key"] for row in occurrences})
                occurrence_ids = sorted({row["occurrence_id"] for row in occurrences})
                pointer = f"page:{page_id}#{evidence['block_id']}:{evidence['char_start']}-{evidence['char_end']}"
                ambiguity = MAPPED_AMBIGUITIES.get(page_id, "")
                link_rows.append({
                    "main_capability_id": _main_id(capability_key), "page_id": page_id,
                    "document_key": document["document_key"], "physical_identity": document["physical_identity"],
                    "title": document["title"], "source_service_keys": ";".join(services_for_page),
                    "occurrence_ids": ";".join(occurrence_ids), "blob_sha256": document["blob_sha256"],
                    "source_version": document["source_version"], "evidence_pointer": pointer,
                    "evidence_excerpt": _sanitize_evidence(str(evidence["text"]))[:500],
                    "mapping_status": "needs_review" if ambiguity else "candidate",
                    "mapping_rationale": ambiguity or (
                        f"Recovered ICD narrative directly evidences {MAIN_CAPABILITIES[capability_key][0]}; EA approval pending"
                    ),
                })
            if page_id in MAPPED_AMBIGUITIES:
                exceptions.append(_exception(
                    "MAPPED_WITH_SOURCE_AMBIGUITY", document["service_key"], MAPPED_AMBIGUITIES[page_id],
                    document_type="ICD", page_id=page_id, document_key=document["document_key"],
                    title=document["title"], pointer=f"page:{page_id}", status="MAPPED_NEEDS_EA_REVIEW",
                ))

        icd_services = {row["service_key"] for row in icd_occurrences}
        isds_by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in isd_occurrences:
            isds_by_service[row["service_key"]].append(row)
        for service in services:
            if service["service_key"] in icd_services:
                continue
            isds = sorted(isds_by_service.get(service["service_key"], []), key=lambda row: row["page_id"])
            reason = "Service has ISD reference(s) but no ICD in the recovery effective catalog; no ICD capability link was invented"
            if not isds:
                reason = "Service has neither ICD nor ISD in the recovery effective catalog"
            exceptions.append(_exception(
                "ISD_ONLY_NO_ICD" if isds else "NO_DOCUMENT_REFERENCE", service["service_key"], reason,
                document_type="ISD" if isds else "", page_id=";".join(row["page_id"] for row in isds),
                document_key=";".join(row["document_key"] for row in isds),
                title=";".join(row["title"] for row in isds),
                pointer=";".join(f"page:{row['page_id']}" for row in isds),
            ))

        service_keys = {row["service_key"] for row in services}
        flagged_rows: list[dict[str, Any]] = []
        mapped_pages_now = {row["page_id"] for row in link_rows}
        for service_key in dict.fromkeys(FLAGGED_SERVICE_INPUT):
            if service_key not in service_keys:
                flagged_rows.append({"service_key": service_key, "disposition": "REFERENCE_RESOLUTION_DEFECT", "icd_pages": [], "isd_pages": []})
                exceptions.append(_exception(
                    "FLAGGED_REFERENCE_RESOLUTION_DEFECT", service_key,
                    "EA-flagged service identifier does not resolve in the recovery effective catalog",
                ))
                continue
            icd_pages = sorted({row["page_id"] for row in icd_occurrences if row["service_key"] == service_key})
            isd_pages = sorted({row["page_id"] for row in isd_occurrences if row["service_key"] == service_key})
            if not icd_pages:
                disposition = "ISD_ONLY_NO_ICD"
            elif set(icd_pages).issubset(mapped_pages_now):
                disposition = "ICD_PRESENT_AND_MAPPED"
            else:
                disposition = "ICD_PRESENT_MAPPING_UNRESOLVED"
            flagged_rows.append({
                "service_key": service_key,
                "disposition": disposition,
                "icd_pages": icd_pages, "isd_pages": isd_pages,
            })

    link_rows.sort(key=lambda row: (row["main_capability_id"], row["page_id"], row["document_key"]))
    exceptions = sorted({row["exception_id"]: row for row in exceptions}.values(), key=lambda row: row["exception_id"])
    linked_pages = {row["page_id"] for row in link_rows}
    unresolved_icd_pages = sorted(set(assignments) - linked_pages)
    if unresolved_icd_pages:
        # Every unresolved page must already have an explicit evidence/content exception.
        excepted_pages = {
            page for row in exceptions if row["exception_type"].startswith("UNRESOLVED_ICD")
            for page in row["page_id"].split(";") if page
        }
        if set(unresolved_icd_pages) - excepted_pages:
            raise ValueError(f"SILENT_UNRESOLVED_ICD:{sorted(set(unresolved_icd_pages) - excepted_pages)}")

    payloads = {
        "main_capabilities.csv": _csv_bytes(main_rows, MAIN_FIELDS),
        "main_icd_links.csv": _csv_bytes(link_rows, LINK_FIELDS),
        "coverage_exceptions.csv": _csv_bytes(exceptions, EXCEPTION_FIELDS),
    }
    for name, content in payloads.items():
        _atomic_write(index_root / name, content)

    duplicate_counts = {key: count for key, count in Counter(FLAGGED_SERVICE_INPUT).items() if count > 1}
    ambiguity_count = sum(row["exception_type"] == "MAPPED_WITH_SOURCE_AMBIGUITY" for row in exceptions)
    no_icd_count = sum(row["exception_type"] == "ISD_ONLY_NO_ICD" for row in exceptions)
    samples = []
    sample_pages = ("5518950691", "5315199059", "4110549791", "6286934017", "5450301441")
    main_labels = {_main_id(key): value[0] for key, value in MAIN_CAPABILITIES.items()}
    for page_id in sample_pages:
        for row in link_rows:
            if row["page_id"] == page_id:
                samples.append(
                    f"- `{main_labels[row['main_capability_id']]}` ← page `{page_id}` / "
                    f"`{row['document_key']}`: “{row['evidence_excerpt']}”"
                )
                break

    flagged_lines = []
    for row in flagged_rows:
        flagged_lines.append(
            f"- `{row['service_key']}` — **{row['disposition']}**; "
            f"ICD pages: {', '.join(f'`{page}`' for page in row['icd_pages']) or 'none'}; "
            f"ISD pages: {', '.join(f'`{page}`' for page in row['isd_pages']) or 'none'}."
        )
    distribution = Counter(row["main_capability_id"] for row in link_rows)
    distribution_lines = [
        f"- {row['label']}: {distribution[row['main_capability_id']]} linked ICD documents."
        for row in main_rows
    ]
    summary = (
        "# Phase 6 Task 019-E-R2 review summary\n\n"
        "## Coverage and status\n\n"
        f"- Exact scope: literal `{MODULE_NAME}` only; {len(services)} services, "
        f"{len(icd_occurrences)} ICD occurrences, {len(assignments)} unique ICD/page identities.\n"
        f"- Direct mapping: {len(linked_pages)} unique ICDs mapped, {len(unresolved_icd_pages)} unresolved ICDs, "
        f"{len(link_rows)} Main↔ICD links, and {len(main_rows)} Main candidates. Multiple links do not inflate ICD coverage.\n"
        f"- Exceptions: {no_icd_count} ISD-only/no-ICD services and {ambiguity_count} mapped source ambiguities. "
        "Exceptions remain EA review items; candidate mapping is not architectural acceptance.\n"
        f"- Every recovered ICD body was read and parsed directly ({parsed_count}/{len(assignments)}); classification did not use the R1 qualification results.\n"
        "- No Business Function or Sub Capability inventory was produced or used; no ISD body was parsed.\n\n"
        "## Main candidate distribution\n\n" + "\n".join(distribution_lines) + "\n\n"
        "## EA-flagged service reconciliation\n\n"
        f"- Input list: {len(FLAGGED_SERVICE_INPUT)} entries, {len(set(FLAGGED_SERVICE_INPUT))} distinct identifiers, "
        f"{sum(duplicate_counts.values()) - len(duplicate_counts)} repeated entries beyond the first. "
        f"Duplicate detail: `{next(iter(duplicate_counts))}` appears {next(iter(duplicate_counts.values()))} times.\n"
        + "\n".join(flagged_lines) + "\n\n"
        "## Real mapping examples\n\n" + "\n".join(samples) + "\n\n"
        "## Ambiguity and focused checks\n\n"
        f"- Mapped ambiguity rows: {ambiguity_count}; exact pages and reasons are in `coverage_exceptions.csv`.\n"
        f"- Unresolved ICD pages: {', '.join(f'`{page}`' for page in unresolved_icd_pages) or 'none'}. "
        "Zero unresolved is a measured corpus result, not EA acceptance.\n"
        "- Checks passed: exact catalog page closure, no fabricated page IDs, no duplicate coverage inflation, "
        "evidence pointer on every link, all flagged identifiers reconciled, and recovery baseline unchanged.\n"
        "- No live Confluence, acquisition, new cache/parser framework, other Module, ISD semantics, API mapping, or full repository regression was used.\n"
        "- Final status: `CANDIDATE_MAPPING_COMPLETE_WITH_REVIEW_EXCEPTIONS`; STOP at `EA_REVIEW_019E_R2`.\n"
    ).encode("utf-8")
    _atomic_write(output_root / "review_summary.md", summary)
    return {
        "counts": {
            "services": len(services), "icd_occurrences": len(icd_occurrences),
            "unique_icds": len(assignments), "mapped_unique_icds": len(linked_pages),
            "unresolved_icds": len(unresolved_icd_pages), "main_capabilities": len(main_rows),
            "main_icd_links": len(link_rows), "coverage_exceptions": len(exceptions),
            "flagged_input_entries": len(FLAGGED_SERVICE_INPUT),
            "flagged_distinct_services": len(set(FLAGGED_SERVICE_INPUT)),
        },
        "hashes": {
            **{name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()},
            "review_summary.md": hashlib.sha256(summary).hexdigest(),
            "recovery_catalog": recovery_manifest["catalog"]["sha256"],
        },
        "status": "EA_REVIEW_019E_R2",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-E-R2 Establishment Main-to-ICD mapping")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(
        build_main_icd_mapping(args.root, args.index_root, args.output_root),
        indent=2, sort_keys=True,
    ))


if __name__ == "__main__":
    main()
