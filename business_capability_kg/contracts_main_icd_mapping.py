"""Task 019-E-R3 direct Contracts Main Capability to ICD mapping.

The mapper is deliberately corpus-bounded.  It reuses the R2 recovery
validation, document parser, evidence sanitization, stable identifiers, and
atomic CSV writers while keeping Contracts decisions keyed by recovered page
identity.  It does not extract Business Functions or Sub Capabilities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .document_cache import DocumentCatalog
from .establishment_main_icd_mapping import (
    EXCEPTION_FIELDS,
    LINK_FIELDS,
    MAIN_FIELDS,
    RECOVERY_CATALOG,
    _atomic_write,
    _csv_bytes,
    _semantic_blocks,
    _validated_recovery,
)
from .icd_capability_extraction import _sanitize_evidence, _stable_id, parse_document


MODULE_KEY = "module-contracts"
MODULE_NAME = "Contracts"
INDEX_ROOT = Path("indexes/phase6/task019/019e_r3")
OUTPUT_ROOT = Path("outputs/phase6/task019/019e_r3")
EXPECTED_SERVICES = 171
EXPECTED_ICD_OCCURRENCES = 169
RECOVERED_PAGE = "6121750531"
RECOVERED_PAGE_SIZE = 470_298
RECOVERED_PAGE_SHA256 = "6637b8bd1b1e12c731c106d30b7bc30fc122421a4e01fb4d0b19e5aff8591bdb"


MAIN_CAPABILITIES: dict[str, tuple[str, str]] = {
    "employment-lifecycle": (
        "Employment Contract Lifecycle Management",
        "Create, maintain, retrieve, renew, close, and transform employment contracts and their requests.",
    ),
    "template-management": (
        "Contract Template Management",
        "Create, retrieve, update, deactivate, and list reusable employment contract templates.",
    ),
    "termination-management": (
        "Employment Contract Termination Management",
        "Submit, assess, approve, cancel, search, and monitor employment contract termination requests.",
    ),
    "training-management": (
        "Training Contract Lifecycle Management",
        "Create, maintain, retrieve, validate, and terminate training contracts and their supporting reference data.",
    ),
    "external-management": (
        "External Contract Lifecycle Management",
        "Create, maintain, retrieve, approve, and cancel contracts involving external candidates and WorkInSaudi flows.",
    ),
    "validation-eligibility": (
        "Contract Validation and Eligibility Management",
        "Validate contract, laborer, establishment, occupation, and journey eligibility before contract actions.",
    ),
    "wage-management": (
        "Contract Wage Management",
        "Calculate, validate, submit, process, update, and monitor wages associated with contracts.",
    ),
    "authentication-compliance": (
        "Contract Authentication and Compliance Monitoring",
        "Measure contract authentication and handle suspected fake-Saudization contract compliance actions.",
    ),
    "reference-data": (
        "Contract Reference Data Administration",
        "Provide governed contract terms, statuses, locations, occupations, specialties, sections, and related lookup data.",
    ),
    "authority-synchronization": (
        "Contract External Authority Synchronization",
        "Exchange and reconcile contract state with GOSI, HRSD, and MOJ through evidenced integration flows.",
    ),
}


# Direct decisions after reading every recovered Contracts ICD.  Page IDs are
# stable evidence identities; labels and service names are not classification
# keys.  Each page is assigned once unless a later corpus review justifies an
# explicit additional link.
PAGES_BY_CAPABILITY: dict[str, tuple[str, ...]] = {
    "employment-lifecycle": (
        "6130139147", "5491261441", "5355503639", "1148944462",
        "4847501313", "5455151107", "4553539858", "4402642999", "5333156202",
        "6225821697", "1145077994", "5341151233", "6054084609", "6554517691",
        "4267868222", "4295361076", "5348360218", "1159103142", "5339153664",
        "5141299324", "6047498271", "6554517505", "5470519297", "4837113943",
        "4781277455", "4136763393", "5345640577", "3395847342", "4816830466",
        "4011491329", "5352063149", "4817682433", "4818305589", "6092521473",
        "1177583727", "6358204417", "4553605121", "4461002753", "6121750531",
        "5489262641", "4859854851", "5460099170",
    ),
    "template-management": (
        "5095849985", "5336268930", "5097422950", "5097422850", "5339971660",
        "5095751730", "5336138128", "5095784450", "5336138190",
    ),
    "termination-management": (
        "4614455408", "4614422555", "2989621967", "3017638734", "4883054604",
        "1253146703", "4614422529", "6489243864", "4295295684", "4659249153",
        "3831169035", "1092321442", "2989523414", "2989523269", "4471816197",
        "4469194753", "4616519681", "4847730690", "4470636630", "4697523037",
    ),
    "training-management": (
        "5566660631", "5680398337", "5537235094", "5536022569", "5527240705",
        "5527896065", "5576491099", "5572821006", "5867077665", "5637177345",
        "5631737857",
        "5567250940", "5661556748", "5576327182", "5857607682", "5660902011",
        "5652873217", "5645926401", "5645205528", "5576392705", "5655265281",
        "5518568864", "5645172861", "5576491022", "5532418152", "5523144785",
        "5529239684", "5670109216", "5753536513", "5767987213", "5877202945",
        "5904138241", "5905055786", "5565906946", "5863374849", "5525536770",
    ),
    "external-management": (
        "5427724351", "6215172097", "5422678066", "6118539330", "5428936770",
        "5484773423", "5427724495", "6551142451", "5437718529",
    ),
    "validation-eligibility": (
        "4833869862", "4833837266", "5451644969", "6068469761", "6554517774",
        "5516591134", "4399792129", "6854213642", "6041600001",
    ),
    "wage-management": (
        "5101486113", "6426624067", "5324571145", "5326602292", "5322506241",
        "5313790206", "6435733508", "5324571209", "4204494849", "4203642881",
        "4204494893", "6246858774", "5315198977", "5322473473", "5322211410",
    ),
    "authentication-compliance": (
        "4104749057", "4642701313", "6345359361", "6832980242", "4164812801",
        "6431539201",
    ),
    "reference-data": (
        "5489393677", "4859920433", "4864868353", "3947528211", "3404366008",
        "4883251204", "5345640793", "3947528193", "4879319157", "5345280080",
        "5360779307",
    ),
    "authority-synchronization": (
        "6231293953", "5393383438", "5798592538", "3997073409", "4671242241",
        "5478744622", "5388107828", "6135382029", "3808329813", "5348458499",
        "3976265729", "5609652225",
    ),
}


EVIDENCE_PATTERNS: dict[str, tuple[str, ...]] = {
    "employment-lifecycle": (
        r"\bcontracts?\b", r"\bcontract details?\b", r"\bcontract status", r"\bcontract privileges",
        r"\bmissing information\b", r"\bcontact details?\b",
    ),
    "template-management": (r"\btemplates?\b",),
    "termination-management": (
        r"\bterminat", r"\brelease date", r"\bengagement", r"\bterminate contract", r"\btc request",
        r"\blaborers list\b",
    ),
    "training-management": (
        r"\btraining contract", r"\btrainee", r"\btct\b", r"\ballowed occupations\b",
    ),
    "external-management": (
        r"\bexternal contracts?\b", r"\bworkinsaudi\b", r"\bsent contract\b", r"\blist of contracts\b",
    ),
    "validation-eligibility": (r"\bvalidat", r"\beligib", r"\brelatedtoid\b"),
    "wage-management": (
        r"\bwages?\b", r"\bsalary\b", r"\bwage files?\b", r"\bfile data\b",
        r"\bfiledetails cycle\b", r"\bworkers?' data\b",
    ),
    "authentication-compliance": (
        r"\bauthentication\b", r"\bfake saudization\b", r"\bsuspected to be fake\b",
    ),
    "reference-data": (
        r"\blocations?\b", r"\boccupations?\b", r"\bspecialties\b", r"\bstatuses\b",
        r"\bterms\b", r"\bsections\b", r"\bfiles needed to create contracts\b", r"\bworklocations\b",
    ),
    "authority-synchronization": (
        r"\bgosi\b", r"\bhrsd\b", r"\bmoj\b", r"\bmojcontracts", r"\bresend contract",
    ),
}


MAPPED_AMBIGUITIES: dict[str, str] = {
    "4837113943": "The body describes employment contracts created by external entities; Employment Contract Lifecycle Management is retained, while the boundary with External Contract Lifecycle Management requires EA review.",
    "4671242241": "The recovered document has no concise purpose/scope narrative; the body integration steps evidence resending a contract to GOSI, so the synchronization link remains review-required.",
    "6068469761": "The source title is marked *OLD*; the ICD remains mapped from its eligibility narrative without inferring retirement or current runtime use.",
    "6554517505": "The source title is marked *IGNORE*; the ICD remains mapped from its active-contract retrieval narrative without inferring retirement or current runtime use.",
    "4553605121": "The title says Contract Details while the purpose says contact details; surrounding narrative describes contract updates, so the lifecycle link remains review-required.",
    "4461002753": "The title says Contract Details while the purpose says contact details; surrounding narrative describes contract updates, so the lifecycle link remains review-required.",
    "5516591134": "The admission-journey eligibility narrative does not name a contract type; the Contracts-module validation link is retained but its boundary requires EA review.",
}


def _main_id(key: str) -> str:
    return _stable_id("main-r3", MODULE_KEY, key)


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


def _evidence_for(capability_key: str, parsed: dict[str, Any]) -> dict[str, Any] | None:
    blocks = _semantic_blocks(parsed)
    direct_narrative = [
        block for block in blocks
        if any(
            cue in str(block.get("text") or "").casefold()
            for cue in (
                "this service", "this scheduler", "this api", "this queue",
                "the scope of this service", "will be used", "used to",
            )
        )
    ]
    for pattern in EVIDENCE_PATTERNS[capability_key]:
        for block in direct_narrative + [item for item in blocks if item not in direct_narrative]:
            if re.search(pattern, str(block.get("text") or ""), re.I):
                return block
    return None


def _exception(
    exception_type: str, service_key: str, reason: str, *, document_type: str = "",
    page_id: str = "", document_key: str = "", title: str = "", pointer: str = "",
    status: str = "EA_REVIEW_REQUIRED",
) -> dict[str, str]:
    return {
        "exception_id": _stable_id("exception-r3", exception_type, service_key, page_id, document_key),
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
    recovered_page_check = False

    with DocumentCatalog(root, catalog_path) as catalog:
        modules = [row for row in catalog.list_modules() if row["module_name"] == MODULE_NAME]
        if len(modules) != 1 or modules[0]["module_key"] != MODULE_KEY:
            raise ValueError("LITERAL_CONTRACTS_MODULE_NOT_FOUND")
        services = catalog.list_services(MODULE_KEY)
        icd_occurrences = catalog.list_documents(MODULE_KEY, document_type="ICD")
        isd_occurrences = catalog.list_documents(MODULE_KEY, document_type="ISD")
        if len(services) != EXPECTED_SERVICES or len(icd_occurrences) != EXPECTED_ICD_OCCURRENCES:
            raise ValueError(f"CONTRACTS_SCOPE_MISMATCH:{len(services)}:{len(icd_occurrences)}")

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
            if page_id == RECOVERED_PAGE:
                recovered_page_check = (
                    int(document["size_bytes"]) == RECOVERED_PAGE_SIZE
                    and document["blob_sha256"] == RECOVERED_PAGE_SHA256
                )
                if not recovered_page_check:
                    raise ValueError("RECOVERED_PAGE_6121750531_INTEGRITY_MISMATCH")
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
                pointer = f"page:{page_id}#{evidence['block_id']}:{evidence['char_start']}-{evidence['char_end']}"
                ambiguity = MAPPED_AMBIGUITIES.get(page_id, "")
                link_rows.append({
                    "main_capability_id": _main_id(capability_key), "page_id": page_id,
                    "document_key": document["document_key"], "physical_identity": document["physical_identity"],
                    "title": document["title"],
                    "source_service_keys": ";".join(sorted({row["service_key"] for row in occurrences})),
                    "occurrence_ids": ";".join(sorted({row["occurrence_id"] for row in occurrences})),
                    "blob_sha256": document["blob_sha256"], "source_version": document["source_version"],
                    "evidence_pointer": pointer,
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

    link_rows.sort(key=lambda row: (row["main_capability_id"], row["page_id"], row["document_key"]))
    exceptions = sorted({row["exception_id"]: row for row in exceptions}.values(), key=lambda row: row["exception_id"])
    linked_pages = {row["page_id"] for row in link_rows}
    unresolved_icd_pages = sorted(set(assignments) - linked_pages)
    excepted_pages = {
        page for row in exceptions if row["exception_type"].startswith("UNRESOLVED_ICD")
        for page in row["page_id"].split(";") if page
    }
    if set(unresolved_icd_pages) - excepted_pages:
        raise ValueError(f"SILENT_UNRESOLVED_ICD:{sorted(set(unresolved_icd_pages) - excepted_pages)}")
    if not recovered_page_check:
        raise ValueError("RECOVERED_PAGE_6121750531_NOT_INSPECTED")

    payloads = {
        "main_capabilities.csv": _csv_bytes(main_rows, MAIN_FIELDS),
        "main_icd_links.csv": _csv_bytes(link_rows, LINK_FIELDS),
        "coverage_exceptions.csv": _csv_bytes(exceptions, EXCEPTION_FIELDS),
    }
    for name, content in payloads.items():
        _atomic_write(index_root / name, content)

    ambiguity_rows = [row for row in exceptions if row["exception_type"] == "MAPPED_WITH_SOURCE_AMBIGUITY"]
    no_icd_rows = [row for row in exceptions if row["exception_type"] in {"ISD_ONLY_NO_ICD", "NO_DOCUMENT_REFERENCE"}]
    unresolved_rows = [row for row in exceptions if row["exception_type"].startswith("UNRESOLVED_ICD")]
    main_labels = {_main_id(key): value[0] for key, value in MAIN_CAPABILITIES.items()}
    distribution = Counter(row["main_capability_id"] for row in link_rows)
    distribution_lines = [
        f"- {row['label']}: {distribution[row['main_capability_id']]} linked ICD documents."
        for row in main_rows
    ]
    exception_lines = [
        f"- `{row['service_key']}` / page `{row['page_id']}` / `{row['document_key']}` — "
        f"**{row['exception_type']}**: {row['precise_reason']}"
        for row in unresolved_rows + ambiguity_rows
    ] or ["- None."]
    no_icd_lines = [
        f"- `{row['service_key']}` — **{row['exception_type']}**; ISD page(s): `{row['page_id'] or 'none'}`; {row['precise_reason']}"
        for row in no_icd_rows
    ] or ["- None."]
    samples = []
    for page_id in ("6121750531", "5095849985", "4697523037", "5565906946", "3997073409"):
        row = next((item for item in link_rows if item["page_id"] == page_id), None)
        if row:
            samples.append(
                f"- `{main_labels[row['main_capability_id']]}` ← page `{page_id}` / `{row['document_key']}`: "
                f"“{row['evidence_excerpt']}”"
            )

    evidence_pointers_valid = all(
        row["evidence_pointer"].startswith(f"page:{row['page_id']}#b") for row in link_rows
    )
    capability_names_valid = all(
        "/" not in row["label"] and len(row["label"].split()) > 1 for row in main_rows
    )

    summary = (
        "# Phase 6 Task 019-E-R3 review summary\n\n"
        "## Coverage and status\n\n"
        f"- Exact scope: literal `{MODULE_NAME}` only; {len(services)} services, "
        f"{len(icd_occurrences)} ICD occurrences, {len(assignments)} unique ICD/page identities.\n"
        f"- Direct mapping: {len(linked_pages)} unique ICDs mapped, {len(unresolved_icd_pages)} unresolved ICDs, "
        f"{len(link_rows)} Main↔ICD links, and {len(main_rows)} Main candidates.\n"
        f"- Non-ICD service disposition: {sum(row['exception_type'] == 'ISD_ONLY_NO_ICD' for row in no_icd_rows)} ISD-only/no-ICD services and "
        f"{sum(row['exception_type'] == 'NO_DOCUMENT_REFERENCE' for row in no_icd_rows)} services with no ICD or ISD.\n"
        f"- Every recovered ICD body was read and parsed directly ({parsed_count}/{len(assignments)}); no ISD body was parsed.\n"
        f"- Recovered page `{RECOVERED_PAGE}` was read from the {RECOVERED_PAGE_SIZE:,}-byte blob with SHA-256 `{RECOVERED_PAGE_SHA256}`; no 198-byte placeholder was used.\n"
        "- No Business Function or Sub Capability inventory or intermediary was produced. Candidate mapping is not EA approval.\n\n"
        "## Main candidate distribution\n\n" + "\n".join(distribution_lines) + "\n\n"
        "## Unresolved and ambiguous ICD sources\n\n" + "\n".join(exception_lines) + "\n\n"
        "## ISD-only or no-ICD services\n\n" + "\n".join(no_icd_lines) + "\n\n"
        "## Genuine Main-to-ICD evidence examples\n\n" + "\n".join(samples) + "\n\n"
        "## Focused integrity checks\n\n"
        f"- Exact source coverage: PASS — {len(linked_pages) + len(unresolved_icd_pages)}/{len(assignments)} unique ICD identities accounted for.\n"
        f"- Valid evidence pointers: {'PASS' if evidence_pointers_valid else 'FAIL'}.\n"
        f"- Duplicate inflation: PASS — {len(linked_pages)} mapped unique ICDs from {len(link_rows)} links; coverage uses page identity.\n"
        f"- Capability names: {'PASS' if capability_names_valid else 'FAIL'} — meaningful noun phrases, no slash-separated or bare labels.\n"
        f"- Source ambiguity disclosure: {len(ambiguity_rows)} mapped source ambiguities listed above; {len(unresolved_rows)} unresolved ICDs.\n"
        f"- Frozen-input integrity: PASS — validated recovery catalog `{RECOVERY_CATALOG}` SHA-256 `{recovery_manifest['catalog']['sha256']}`; catalog and cached bodies opened read-only.\n"
        "- Scope controls: no network, catalog/cache mutation, old-stage replay, other Module, ISD semantics, API matching, or full-suite run.\n"
        "- Final status: `CANDIDATE_MAPPING_COMPLETE_WITH_REVIEW_EXCEPTIONS`; STOP at `EA_REVIEW_019E_R3`.\n"
    ).encode("utf-8")
    _atomic_write(output_root / "review_summary.md", summary)
    return {
        "counts": {
            "services": len(services), "icd_occurrences": len(icd_occurrences),
            "unique_icds": len(assignments), "mapped_unique_icds": len(linked_pages),
            "unresolved_icds": len(unresolved_icd_pages), "main_capabilities": len(main_rows),
            "main_icd_links": len(link_rows), "coverage_exceptions": len(exceptions),
            "mapped_ambiguities": len(ambiguity_rows), "isd_only_no_icd_services": sum(
                row["exception_type"] == "ISD_ONLY_NO_ICD" for row in no_icd_rows
            ),
        },
        "hashes": {
            **{name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()},
            "review_summary.md": hashlib.sha256(summary).hexdigest(),
            "recovery_catalog": recovery_manifest["catalog"]["sha256"],
        },
        "status": "EA_REVIEW_019E_R3",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-E-R3 Contracts Main-to-ICD mapping")
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
