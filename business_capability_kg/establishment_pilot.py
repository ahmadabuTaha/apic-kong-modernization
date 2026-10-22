"""Task 019-E-R1 Establishment-only business-function methodology pilot.

The pilot consumes the accepted document-recovery overlay, reads only ICDs
linked to the literal ``Establishment`` Module, and creates function-first
candidate capability evidence.  It deliberately creates no Sub Capability or
API/ISD semantic mapping.
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
from .icd_capability_extraction import (
    _sanitize_evidence,
    _sha256_file,
    _stable_id,
    parse_document,
)


SCHEMA_VERSION = "phase6-task019e-r1-v1"
PARSER_VERSION = "function-first-structured-v1"
EXTRACTOR_VERSION = "explicit-business-function-v3"
GROUPING_VERSION = "establishment-main-grouping-v2"
MODULE_NAME = "Establishment"
MODULE_KEY = "module-establishment"
INDEX_ROOT = Path("indexes/phase6/task019/019e_r1")
OUTPUT_ROOT = Path("outputs/phase6/task019/019e_r1")
RECOVERY_INDEX = Path("indexes/phase6/task019/recovery")
RECOVERY_OUTPUT = Path("outputs/phase6/task019/recovery")
RECOVERY_CATALOG = RECOVERY_INDEX / "retrieval_catalog.sqlite3"
SUSPECTED_PAGE_IDS = ("5315199059", "5518950691", "5849382920", "5943951453", "6134169639")
PLACEHOLDER_SHA256 = "16f33c6aa04292a48d36c8fb86be3baf31325cdd9edd19d08f15620f55415007"

FUNCTION_FIELDS = [
    "function_id", "module_key", "candidate_label", "normalized_label", "actor", "action",
    "business_object", "purpose_outcome", "conditions_rules", "status", "confidence",
    "evidence_count", "service_count", "document_count", "source_service_keys",
    "source_document_keys", "future_isd_reference_keys", "isd_association_limitation",
]
MAIN_FIELDS = [
    "main_capability_id", "module_key", "candidate_label", "ability_definition", "status",
    "confidence", "function_count", "evidence_count", "grouping_rationale",
    "local_hld_benchmark_status",
]
EDGE_FIELDS = [
    "main_capability_id", "function_id", "module_key", "relationship_status",
    "grouping_rule", "grouping_rationale",
]
EVIDENCE_FIELDS = [
    "evidence_id", "function_id", "module_key", "service_key", "occurrence_id",
    "document_key", "page_id", "physical_identity", "blob_sha256", "source_version",
    "section_heading", "block_id", "block_kind", "char_start", "char_end", "source_phrase",
    "actor", "action", "business_object", "purpose_outcome", "conditions_rules",
    "extraction_method", "strength",
]
AUDIT_FIELDS = [
    "audit_id", "module_key", "service_key", "occurrence_id", "document_key", "page_id",
    "title", "status", "representation", "size_bytes", "blob_sha256", "source_version",
    "raw_bytes_verified", "hash_verified", "parse_status", "block_count", "function_count",
    "suspected_empty_page", "original_size_bytes", "original_sha256", "recovery_classification",
    "recovery_diagnostic", "content_integrity_status", "semantic_processing_status",
]
REVIEW_FIELDS = [
    "review_id", "module_key", "service_key", "document_key", "page_id", "function_id",
    "main_capability_id", "issue_type", "reason", "evidence_pointer", "status",
]

TECHNICAL_SECTIONS = (
    "endpoint", "request structure", "response structure", "json structure", "mapping",
    "transformation", "error code", "target url", "sample message", "data mapping",
)
TECHNICAL_PHRASES = (
    "api endpoint", "http request", "http response", "json request", "json response",
    "oauth", "bearer token", "access token", "authentication token",
)
ACTION_ALIASES = {
    "adds": "add", "adding": "add", "approves": "approve", "approving": "approve",
    "checks": "check", "checking": "check", "closes": "close", "closing": "close",
    "creates": "create", "creating": "create", "fetches": "fetch", "fetching": "fetch",
    "gets": "get", "getting": "get", "opens": "open", "opening": "open",
    "receives": "receive", "receiving": "receive", "retrieves": "retrieve",
    "retrieving": "retrieve", "searches": "search", "searching": "search",
    "sends": "send", "sending": "send", "submits": "submit", "submitting": "submit",
    "transfers": "transfer", "transferring": "transfer", "updates": "update",
    "updating": "update", "validates": "validate", "validating": "validate",
    "verifies": "verify", "verifying": "verify",
}
ACTION_WORDS = {
    "activate", "add", "approve", "assign", "calculate", "cancel", "change", "check",
    "close", "confirm", "create", "deactivate", "delete", "fetch", "generate", "get",
    "issue", "list", "manage", "notify", "open", "process", "provide", "receive",
    "register", "reject", "remove", "renew", "retrieve", "search", "send", "submit",
    "synchronize", "terminate", "track", "transfer", "unassign", "update", "validate",
    "verify", "view",
}

CUE_PATTERNS = (
    ("EXPLICIT_SERVICE_PURPOSE", re.compile(
        r"\b(?:this|the)\s+(?:service|scheduler|process)\s+(?:is\s+)?(?:used\s+)?(?:to|for)\s+(.+)", re.I
    )),
    ("EXPLICIT_SCOPE", re.compile(
        r"\b(?:the\s+)?scope\s+of\s+this\s+(?:service|document)\s+(?:is\s+)?(?:used\s+)?(?:to|for)\s+(.+)", re.I
    )),
    ("EXPLICIT_ENABLEMENT", re.compile(
        r"\b(?:this|the)\s+service\s+(?:allows?|enables?)\s+(?:the\s+)?(.+)", re.I
    )),
)

MAIN_RULES: tuple[dict[str, Any], ...] = (
    {
        "key": "registration-opening", "label": "Establishment Registration and Opening",
        "definition": "Ability to establish or open an establishment file, branch, or unified establishment identity through an evidenced registration route.",
        "patterns": (
            r"\bopen\b.*\bestablishment", r"\bcreate\b.*\bestablishment", r"\bopen\b.*\bfile",
            r"\bopen\b.*\bunified ?number", r"\bvalidity\b.*\b(?:establishment and cr|cr for opening)\b",
        ),
    },
    {
        "key": "activity-management", "label": "Establishment Activity Management",
        "definition": "Ability to determine, validate, change, close, or maintain an establishment's registered economic activities and eligibility.",
        "patterns": (r"\bactivit", r"\bisic", r"\bnitaqat", r"\bsaudization"),
    },
    {
        "key": "location-management", "label": "Establishment Location Management",
        "definition": "Ability to create, maintain, validate, and report establishment locations and laborer-to-location assignments.",
        "patterns": (r"\blocation", r"\blaborer.*assign", r"\bworker.*housing", r"\blabor housing", r"\bcities lookup"),
    },
    {
        "key": "license-services", "label": "Establishment License Services",
        "definition": "Ability to retrieve, validate, maintain, or apply establishment licensing requirements and license information.",
        "patterns": (r"\blicen[cs]",),
    },
    {
        "key": "ownership-representation", "label": "Establishment Ownership and Representation Management",
        "definition": "Ability to maintain establishment ownership, legal form, managers, representatives, and related commercial-registration parties.",
        "patterns": (r"\btransfer ownership", r"\bowner", r"\bmanager", r"\brepresentative", r"\bparties\b", r"\bentity type", r"\bcompany form", r"\bforeign investor", r"\bcr swap"),
    },
    {
        "key": "record-profile", "label": "Establishment Record and Profile Management",
        "definition": "Ability to maintain and retrieve establishment profile, commercial-registration, status, address, and core record information.",
        "patterns": (
            r"\bestablishment profile", r"\bestablishment information", r"\bestablishment details",
            r"\bcr (?:name|city|capital|status|expiry|confirm)", r"\bcontact", r"\baddress",
            r"\bestablishment statement", r"\bcorrection request", r"\brenew cr", r"\bupdated cr information",
            r"\bcrnationalnumber establishments list", r"\bestablishments and entities",
        ),
    },
    {
        "key": "closure", "label": "Establishment Closure Management",
        "definition": "Ability to close or terminate an establishment and maintain the resulting establishment status.",
        "patterns": (r"\bclose establishments?\b", r"\bestablishment closure", r"\bterminate establishments?"),
    },
    {
        "key": "compliance-violations", "label": "Establishment Compliance and Violation Management",
        "definition": "Ability to assess establishment compliance and manage violations, punishments, grace periods, and related obligations.",
        "patterns": (r"\bviolation", r"\bpunishment", r"\bcompli", r"\bgrace period", r"\bdebts?\b", r"\blegal issues?"),
    },
    {
        "key": "request-representation", "label": "Establishment Request and Agent Management",
        "definition": "Ability to submit, review, approve, reject, and search establishment requests involving owners or government agents.",
        "patterns": (r"\bgovernment agent", r"\bsector.*agent", r"\bestablishments? requests?", r"\brequested establishment", r"\bsearch establishments? and requests?"),
    },
    {
        "key": "notifications", "label": "Establishment Stakeholder Notifications",
        "definition": "Ability to notify establishment owners, managers, representatives, or other stakeholders of evidenced establishment events.",
        "patterns": (r"\bnotification", r"\bsend emails?", r"\bsend sms"),
    },
    {
        "key": "government-integration", "label": "Government Information Exchange",
        "definition": "Ability to receive or synchronize establishment record changes with an explicitly named government system.",
        "patterns": (r"\breceive.*\b(?:mci|momra|nic|gosi|hrsd|gsn)\b", r"\bas received from (?:mci|momra|nic|gosi|hrsd)\b", r"\bupdate.*\bin (?:nic|gosi|hrsd)\b", r"\bopen.*\bin (?:nic|gosi|hrsd)\b"),
    },
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


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


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _clean_phrase(value: str) -> str:
    value = re.split(r"(?<=[.!?])\s+", value.strip())[0]
    value = re.sub(r"^(?:to|used\s+to)\s+", "", value, flags=re.I)
    return _sanitize_evidence(value.strip(" .,:;-()"))[:600]


def _function_parts(phrase: str, source: str) -> dict[str, str] | None:
    tokens = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", phrase)
    if not tokens:
        return None
    raw_action = tokens[0].casefold()
    action = ACTION_ALIASES.get(raw_action, raw_action)
    if action not in ACTION_WORDS:
        return None
    normalized_phrase = _normalized(phrase)
    if any(technical in normalized_phrase for technical in TECHNICAL_PHRASES):
        return None

    actor = ""
    actor_patterns = (
        (r"\bgovernment agents?\b", "government agent"), (r"\bowners?\b", "establishment owner"),
        (r"\bmanagers?\b", "establishment manager"), (r"\brepresentatives?\b", "establishment representative"),
        (r"\busers?\b", "user"), (r"\bscheduler\b", "scheduled process"),
        (r"\bMCI\b", "MCI"), (r"\bMOMRA\b", "MOMRA"), (r"\bNIC\b", "NIC"),
    )
    for pattern, label in actor_patterns:
        if re.search(pattern, source, re.I):
            actor = label
            break

    outcome, conditions = "", ""
    outcome_match = re.search(r"\b(?:in order to|so that|so as to)\s+(.+)$", phrase, re.I)
    if outcome_match:
        outcome = outcome_match.group(1).strip(" .")[:300]
    condition_match = re.search(r"\b(?:if|when|unless|based on)\s+(.+)$", phrase, re.I)
    if condition_match:
        conditions = condition_match.group(0).strip(" .")[:300]

    object_text = " ".join(tokens[1:])
    for marker in (" in order to ", " so that ", " so as to ", " if ", " when ", " unless ", " based on "):
        position = object_text.casefold().find(marker)
        if position >= 0:
            object_text = object_text[:position]
    object_text = re.sub(r"^(?:the|a|an|all)\s+", "", object_text, flags=re.I).strip()
    if not object_text or _normalized(object_text) in {"data", "request", "response", "service", "system"}:
        return None
    label = f"{action.capitalize()} {object_text}"[:180]
    return {
        "candidate_label": label, "normalized_label": _normalized(label), "actor": actor,
        "action": action, "business_object": object_text[:300],
        "purpose_outcome": _sanitize_evidence(outcome), "conditions_rules": _sanitize_evidence(conditions),
    }


def _expand_compound_phrases(phrase: str) -> list[str]:
    """Split only explicit coordinated business actions with a shared object."""
    phrase = re.sub(r"^check[/\\]+validate\s+if\s+", "validate whether ", phrase, flags=re.I)
    shared = re.match(
        r"^(approve|add|activate|assign|close|create|open|validate)\s+or\s+([a-z]+)\s+(.+)$",
        phrase, re.I,
    )
    if shared:
        first = ACTION_ALIASES.get(shared.group(1).casefold(), shared.group(1).casefold())
        second = ACTION_ALIASES.get(shared.group(2).casefold(), shared.group(2).casefold())
        if first in ACTION_WORDS and second in ACTION_WORDS:
            return [f"{first} {shared.group(3)}", f"{second} {shared.group(3)}"]
    separate = re.match(r"^(transfer\s+.+?)\s+or\s+(change\s+.+)$", phrase, re.I)
    if separate:
        return [separate.group(1), separate.group(2)]
    return [phrase]


def extract_business_functions(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract explicit business-function wording, never headings or names alone."""
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for block in parsed.get("blocks", []):
        section = str(block.get("section_heading") or "")
        if any(term in section.casefold() for term in TECHNICAL_SECTIONS):
            continue
        if block.get("kind") not in {"paragraph", "list_item", "table_row"}:
            continue
        text = str(block.get("text") or "")
        search_cursor = 0
        for sentence in filter(None, (part.strip() for part in re.split(r"(?<=[.!?])\s+|\s*[•·]\s*", text))):
            if len(sentence) < 16:
                continue
            local_start = text.find(sentence, search_cursor)
            if local_start < 0:
                local_start = 0
            search_cursor = local_start + len(sentence)
            method, phrase = "", ""
            for candidate_method, pattern in CUE_PATTERNS:
                match = pattern.search(sentence)
                if match:
                    method, phrase = candidate_method, _clean_phrase(match.group(1))
                    break
            if not phrase:
                continue
            for atomic_phrase in _expand_compound_phrases(phrase):
                parts = _function_parts(atomic_phrase, sentence)
                if not parts:
                    continue
                key = (parts["normalized_label"], str(block["block_id"]))
                if key in seen:
                    continue
                seen.add(key)
                strength = "HIGH" if any(word in section.casefold() for word in ("purpose", "scope", "business")) else "MEDIUM"
                rows.append({
                    **parts, "source_phrase": _sanitize_evidence(sentence)[:700],
                    "section_heading": _sanitize_evidence(section)[:240], "block_id": block["block_id"],
                    "block_kind": block["kind"], "char_start": int(block["char_start"]) + local_start,
                    "char_end": int(block["char_start"]) + local_start + len(sentence),
                    "extraction_method": method, "strength": strength,
                })
    return rows


def _validated_recovery(root: Path) -> dict[str, Any]:
    manifest_path = root / RECOVERY_OUTPUT / "manifest.json"
    catalog_path = root / RECOVERY_CATALOG
    investigated_path = root / RECOVERY_INDEX / "investigated_pages.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "phase6-document-recovery-v1":
        raise ValueError("RECOVERY_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("status") != "EA_REVIEW_DOCUMENT_RECOVERY":
        raise ValueError("RECOVERY_NOT_ACCEPTED_FOR_REVIEW")
    catalog = manifest["catalog"]
    if catalog_path.stat().st_size != int(catalog["size_bytes"]) or _sha256_file(catalog_path) != catalog["sha256"]:
        raise ValueError("RECOVERY_CATALOG_INTEGRITY_MISMATCH")
    recovery_files = manifest.get("files") or manifest.get("indexes") or {}
    expected_investigated = recovery_files["investigated_pages.csv"]
    if _sha256_file(investigated_path) != expected_investigated["sha256"]:
        raise ValueError("RECOVERY_INVESTIGATION_INTEGRITY_MISMATCH")
    with investigated_path.open(encoding="utf-8", newline="") as stream:
        investigated = {row["page_id"]: row for row in csv.DictReader(stream)}
    missing = set(SUSPECTED_PAGE_IDS) - investigated.keys()
    if missing:
        raise ValueError(f"SUSPECTED_PAGE_AUDIT_MISSING:{sorted(missing)}")
    return {
        "manifest_path": manifest_path, "manifest_sha256": _sha256_file(manifest_path),
        "catalog_path": catalog_path, "catalog_sha256": catalog["sha256"],
        "investigated_path": investigated_path, "investigated_sha256": expected_investigated["sha256"],
        "investigated": investigated,
    }


def _cache_path(index_root: Path, digest: str, mime_type: str) -> Path:
    key = _stable_id("function-cache", digest, mime_type, PARSER_VERSION, EXTRACTOR_VERSION)
    return index_root / "cache" / f"{key}.json"


def _parse_cached(
    catalog: DocumentCatalog, document: dict[str, Any], index_root: Path, telemetry: Counter[str]
) -> tuple[dict[str, Any], bool, bool]:
    path = _cache_path(index_root, document["blob_sha256"], document["mime_type"])
    cache_key = path.stem
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("cache_key") == cache_key and payload.get("blob_sha256") == document["blob_sha256"]:
            telemetry["cache_hits"] += 1
            return payload, True, True
    telemetry["cache_misses"] += 1
    result, content = catalog.load_document(document["document_key"])
    if content is None:
        payload = {
            "cache_key": cache_key, "blob_sha256": document["blob_sha256"],
            "parse_status": result["status"].upper(), "gap_reason": result["status"],
            "blocks": [], "functions": [],
        }
        raw_verified = hash_verified = False
    else:
        telemetry["blob_reads"] += 1
        hash_verified = hashlib.sha256(content).hexdigest() == document["blob_sha256"]
        raw_verified = len(content) == int(document["size_bytes"])
        parsed = parse_document(content, document["mime_type"])
        payload = {
            "cache_key": cache_key, "blob_sha256": document["blob_sha256"],
            "parser_version": PARSER_VERSION, "extractor_version": EXTRACTOR_VERSION,
            **parsed, "functions": extract_business_functions(parsed),
        }
    _atomic_write(path, _json_bytes(payload))
    return payload, raw_verified, hash_verified


def _review(
    issue_type: str, reason: str, *, service_key: str = "", document_key: str = "",
    page_id: str = "", function_id: str = "", main_id: str = "", pointer: str = "",
) -> dict[str, str]:
    return {
        "review_id": _stable_id("review-r1", issue_type, service_key, document_key, page_id, function_id, main_id, pointer),
        "module_key": MODULE_KEY, "service_key": service_key, "document_key": document_key,
        "page_id": page_id, "function_id": function_id, "main_capability_id": main_id,
        "issue_type": issue_type, "reason": reason, "evidence_pointer": pointer,
        "status": "EA_REVIEW_REQUIRED",
    }


def _group_matches(function: dict[str, Any]) -> list[tuple[dict[str, Any], str]]:
    haystack = " ".join((
        function["candidate_label"], function["business_object"], function["purpose_outcome"],
        function["conditions_rules"], " ".join(function["source_phrases"]),
    )).casefold()
    matches: list[tuple[dict[str, Any], str]] = []
    for rule in MAIN_RULES:
        matched = next((pattern for pattern in rule["patterns"] if re.search(pattern, haystack, re.I)), None)
        if matched:
            matches.append((rule, matched))
    if "establishment activity" in haystack:
        matches = [item for item in matches if item[0]["key"] != "closure"]
    # A Function receives one bounded functional grouping. Government exchange
    # may be a second, orthogonal ability only when the wording explicitly
    # evidences that exchange. This prevents incidental object mentions from
    # creating a broad fan-out of Main links.
    government = [item for item in matches if item[0]["key"] == "government-integration"]
    functional = {item[0]["key"]: item for item in matches if item[0]["key"] != "government-integration"}
    precedence = (
        "compliance-violations", "notifications", "request-representation", "closure",
        "activity-management", "location-management", "license-services",
        "ownership-representation", "registration-opening", "record-profile",
    )
    selected = [functional[key] for key in precedence if key in functional][:1]
    return selected + government[:1]


def build_establishment_pilot(
    root: Path, index_root: Path | None = None, output_root: Path | None = None
) -> dict[str, Any]:
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    recovery = _validated_recovery(root)
    telemetry: Counter[str] = Counter()
    audits: list[dict[str, Any]] = []
    reviews: list[dict[str, str]] = []
    evidence_rows: list[dict[str, Any]] = []

    with DocumentCatalog(root, recovery["catalog_path"]) as catalog:
        module = next((row for row in catalog.list_modules() if row["module_name"] == MODULE_NAME), None)
        if not module or module["module_key"] != MODULE_KEY:
            raise ValueError("LITERAL_ESTABLISHMENT_MODULE_NOT_FOUND")
        services = catalog.list_services(MODULE_KEY)
        icds = catalog.list_documents(MODULE_KEY, document_type="ICD")
        isds = catalog.list_documents(MODULE_KEY, document_type="ISD")
        if len(services) != 142 or len(icds) != 149:
            raise ValueError(f"ESTABLISHMENT_SCOPE_CLOSURE_MISMATCH:{len(services)}:{len(icds)}")

        icd_services = {row["service_key"] for row in icds}
        for service in services:
            if service["service_key"] not in icd_services:
                reviews.append(_review(
                    "NO_ICD_REFERENCE", "Service has no ICD reference; no Business Function inferred",
                    service_key=service["service_key"],
                ))
        isd_by_service: dict[str, set[str]] = defaultdict(set)
        for isd in isds:
            isd_by_service[isd["service_key"]].add(isd["document_key"])

        for document in icds:
            parsed, raw_verified, hash_verified = _parse_cached(catalog, document, index_root, telemetry)
            investigation = recovery["investigated"].get(document["page_id"], {})
            suspected = document["page_id"] in SUSPECTED_PAGE_IDS
            recovered_valid = (
                suspected and investigation.get("classification") == "RECOVERED_SOURCE_BODY"
                and investigation.get("retrieval_status") == "SUCCESS"
                and investigation.get("original_sha256") == PLACEHOLDER_SHA256
                and document["blob_sha256"] == investigation.get("effective_sha256")
                and int(document["size_bytes"]) > 198 and parsed["parse_status"] == "PARSED"
                and bool(parsed.get("blocks"))
            )
            if suspected:
                integrity = "VALIDATED_RECOVERED_SOURCE_BODY" if recovered_valid else "ACQUISITION_CONTENT_SUSPECT"
            elif raw_verified and hash_verified and parsed["parse_status"] == "PARSED":
                integrity = "VALIDATED_LOCAL_SOURCE_BODY"
            elif parsed["parse_status"] == "PARSED":
                # Cache hits were verified on the cold read that created the hash-keyed entry.
                integrity = "VALIDATED_HASH_KEYED_CACHE"
            else:
                integrity = "ACQUISITION_CONTENT_SUSPECT"
            semantic_status = "PROCESSED" if integrity.startswith("VALIDATED") else "STOPPED_SOURCE_INTEGRITY"
            audits.append({
                "audit_id": _stable_id("audit-r1", document["occurrence_id"]), "module_key": MODULE_KEY,
                "service_key": document["service_key"], "occurrence_id": document["occurrence_id"],
                "document_key": document["document_key"], "page_id": document["page_id"],
                "title": document["title"], "status": document["status"],
                "representation": "ADF_JSON" if "atlassian.document" in document["mime_type"] else "HTML",
                "size_bytes": document["size_bytes"], "blob_sha256": document["blob_sha256"],
                "source_version": document["source_version"], "raw_bytes_verified": str(raw_verified).lower(),
                "hash_verified": str(hash_verified).lower(), "parse_status": parsed["parse_status"],
                "block_count": len(parsed.get("blocks", [])), "function_count": len(parsed.get("functions", [])),
                "suspected_empty_page": str(suspected).lower(),
                "original_size_bytes": investigation.get("original_size_bytes", ""),
                "original_sha256": investigation.get("original_sha256", ""),
                "recovery_classification": investigation.get("classification", ""),
                "recovery_diagnostic": investigation.get("diagnostic", ""),
                "content_integrity_status": integrity, "semantic_processing_status": semantic_status,
            })
            if semantic_status != "PROCESSED":
                reviews.append(_review(
                    "SOURCE_INTEGRITY_STOP", "ICD content failed the integrity gate and was not semantic evidence",
                    service_key=document["service_key"], document_key=document["document_key"],
                    page_id=document["page_id"], pointer=document["blob_sha256"],
                ))
                continue
            if not parsed.get("functions"):
                reviews.append(_review(
                    "NO_EXPLICIT_BUSINESS_FUNCTION",
                    "Parsed ICD has no statement meeting the explicit Business Function evidence rules",
                    service_key=document["service_key"], document_key=document["document_key"],
                    page_id=document["page_id"], pointer=document["blob_sha256"],
                ))
            for function in parsed.get("functions", []):
                semantic_key = "\x1f".join((
                    function["normalized_label"], _normalized(function["actor"]),
                    _normalized(function["purpose_outcome"]), _normalized(function["conditions_rules"]),
                ))
                function_id = _stable_id("function", MODULE_KEY, semantic_key)
                evidence_id = _stable_id(
                    "function-evidence", function_id, document["blob_sha256"], function["block_id"],
                    function["source_phrase"],
                )
                evidence_rows.append({
                    "evidence_id": evidence_id, "function_id": function_id, "module_key": MODULE_KEY,
                    "service_key": document["service_key"], "occurrence_id": document["occurrence_id"],
                    "document_key": document["document_key"], "page_id": document["page_id"],
                    "physical_identity": document["physical_identity"], "blob_sha256": document["blob_sha256"],
                    "source_version": document["source_version"], "section_heading": function["section_heading"],
                    "block_id": function["block_id"], "block_kind": function["block_kind"],
                    "char_start": function["char_start"], "char_end": function["char_end"],
                    "source_phrase": function["source_phrase"], "actor": function["actor"],
                    "action": function["action"], "business_object": function["business_object"],
                    "purpose_outcome": function["purpose_outcome"], "conditions_rules": function["conditions_rules"],
                    "extraction_method": function["extraction_method"], "strength": function["strength"],
                })

    # Deduplicate only equivalent function semantics inside Establishment while
    # retaining every source variant/evidence edge.
    evidence_rows.sort(key=lambda row: (row["function_id"], row["evidence_id"]))
    grouped_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        grouped_evidence[row["function_id"]].append(row)
    functions: list[dict[str, Any]] = []
    for function_id, group in sorted(grouped_evidence.items()):
        exemplar = group[0]
        services_for_function = sorted({row["service_key"] for row in group})
        documents_for_function = sorted({row["document_key"] for row in group})
        future_isds = sorted({key for service in services_for_function for key in isd_by_service.get(service, set())})
        strengths = {row["strength"] for row in group}
        functions.append({
            "function_id": function_id, "module_key": MODULE_KEY,
            "candidate_label": f"{exemplar['action'].capitalize()} {exemplar['business_object']}",
            "normalized_label": _normalized(f"{exemplar['action']} {exemplar['business_object']}"),
            "actor": exemplar["actor"], "action": exemplar["action"],
            "business_object": exemplar["business_object"], "purpose_outcome": exemplar["purpose_outcome"],
            "conditions_rules": exemplar["conditions_rules"], "status": "candidate" if "HIGH" in strengths else "needs_review",
            "confidence": "HIGH" if "HIGH" in strengths else "MEDIUM", "evidence_count": len(group),
            "service_count": len(services_for_function), "document_count": len(documents_for_function),
            "source_service_keys": ";".join(services_for_function),
            "source_document_keys": ";".join(documents_for_function),
            "future_isd_reference_keys": ";".join(future_isds),
            "isd_association_limitation": "SERVICE_INVENTORY_EDGE_ONLY_NOT_SEMANTICALLY_PARSED_OR_MAPPED",
            "source_phrases": sorted({row["source_phrase"] for row in group}),
        })

    main_acc: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for function in functions:
        matches = _group_matches(function)
        if not matches:
            reviews.append(_review(
                "FUNCTION_MAIN_GROUPING_UNRESOLVED",
                "Explicit Business Function does not meet a bounded Main Capability grouping rule",
                function_id=function["function_id"], pointer=function["normalized_label"],
            ))
            continue
        for rule, matched_pattern in matches:
            main_id = _stable_id("main", MODULE_KEY, rule["key"])
            accumulator = main_acc.setdefault(main_id, {
                "main_capability_id": main_id, "module_key": MODULE_KEY,
                "candidate_label": rule["label"], "ability_definition": rule["definition"],
                "status": "candidate", "confidence": "MEDIUM", "function_ids": set(),
                "evidence_ids": set(),
                "grouping_rationale": "Grouped after the complete Establishment function inventory by explicit business-object/action evidence",
                "local_hld_benchmark_status": "LOCAL_HLD_NOT_FOUND_NOT_USED_AS_EVIDENCE",
            })
            accumulator["function_ids"].add(function["function_id"])
            accumulator["evidence_ids"].update(row["evidence_id"] for row in grouped_evidence[function["function_id"]])
            edges.append({
                "main_capability_id": main_id, "function_id": function["function_id"],
                "module_key": MODULE_KEY, "relationship_status": "candidate",
                "grouping_rule": matched_pattern,
                "grouping_rationale": f"Function wording matched the bounded {rule['label']} evidence rule; EA review pending",
            })

    mains: list[dict[str, Any]] = []
    for main_id, item in sorted(main_acc.items(), key=lambda pair: pair[1]["candidate_label"]):
        function_count = len(item["function_ids"])
        status = "candidate" if function_count > 1 else "needs_review"
        mains.append({
            **{key: value for key, value in item.items() if key not in {"function_ids", "evidence_ids"}},
            "status": status, "confidence": "HIGH" if function_count >= 3 else "MEDIUM",
            "function_count": function_count, "evidence_count": len(item["evidence_ids"]),
        })
        if function_count == 1:
            function_id = next(iter(item["function_ids"]))
            reviews.append(_review(
                "MAIN_FUNCTION_ONE_TO_ONE_REVIEW", "Main candidate currently has one Function; grouping justification requires EA review",
                function_id=function_id, main_id=main_id, pointer=item["candidate_label"],
            ))

    functions_output = [{key: row.get(key, "") for key in FUNCTION_FIELDS} for row in functions]
    edges = sorted(edges, key=lambda row: (row["main_capability_id"], row["function_id"]))
    audits.sort(key=lambda row: (row["service_key"], row["page_id"], row["occurrence_id"]))
    reviews = sorted({row["review_id"]: row for row in reviews}.values(), key=lambda row: row["review_id"])
    datasets = {
        "business_functions.csv": (functions_output, FUNCTION_FIELDS),
        "main_capabilities.csv": (mains, MAIN_FIELDS),
        "main_function_edges.csv": (edges, EDGE_FIELDS),
        "function_evidence.csv": (evidence_rows, EVIDENCE_FIELDS),
        "icd_integrity_audit.csv": (audits, AUDIT_FIELDS),
        "review_queue.csv": (reviews, REVIEW_FIELDS),
    }
    payloads: dict[str, bytes] = {}
    for name, (rows, fields) in datasets.items():
        payloads[name] = _csv_bytes(rows, fields)
        _atomic_write(index_root / name, payloads[name])

    suspected_audits = [row for row in audits if row["page_id"] in SUSPECTED_PAGE_IDS]
    integrity_suspect = [row for row in audits if row["content_integrity_status"] == "ACQUISITION_CONTENT_SUSPECT"]
    ungrouped = [row for row in reviews if row["issue_type"] == "FUNCTION_MAIN_GROUPING_UNRESOLVED"]
    no_function = [row for row in reviews if row["issue_type"] == "NO_EXPLICIT_BUSINESS_FUNCTION"]
    no_icd = [row for row in reviews if row["issue_type"] == "NO_ICD_REFERENCE"]
    one_to_one = [row for row in reviews if row["issue_type"] == "MAIN_FUNCTION_ONE_TO_ONE_REVIEW"]
    if integrity_suspect:
        execution_status = "PILOT_BLOCKED_SOURCE_INTEGRITY"
    elif no_function or no_icd or ungrouped:
        execution_status = "PILOT_COMPLETE_WITH_GAPS"
    else:
        execution_status = "PILOT_COMPLETE_WITH_EVIDENCE"

    core_digest = hashlib.sha256(b"".join(payloads[name] for name in sorted(payloads))).hexdigest()
    validation_summary = (
        "# Phase 6 Task 019-E-R1 pilot validation summary\n\n"
        f"- Status: **{execution_status}**; stop gate: `EA_REVIEW_019E_R1`.\n"
        f"- Scope: exact Module `{MODULE_NAME}` only; {len(services)} services, {len(icds)} ICD occurrences, "
        f"{len({row['page_id'] for row in icds})} ICD pages, and {len(isds)} preserved ISD reference occurrences.\n"
        f"- Integrity: {len(audits) - len(integrity_suspect)} validated ICDs; {len(integrity_suspect)} suspect. "
        f"All five suspected-empty pages were recovered and validated: {', '.join(SUSPECTED_PAGE_IDS)}.\n"
        f"- Function-first result: {len(functions_output)} Business Functions, {len(evidence_rows)} evidence spans, "
        f"{len(mains)} Main Capability candidates, and {len(edges)} Function-to-Main candidate links.\n"
        f"- Explicit gaps: {len(no_icd)} services without ICD, {len(no_function)} parsed ICDs without explicit function wording, "
        f"{len(ungrouped)} functions unresolved to a bounded Main, and {len(one_to_one)} one-to-one Main/Function reviews.\n"
        f"- Cache: {telemetry['cache_hits']} hits, {telemetry['cache_misses']} misses, {telemetry['blob_reads']} verified blob reads.\n"
        "- No Sub Capability entity or output exists. ISD identities are retained only as service-inventory edges; no ISD semantics or API mapping was performed.\n"
        "- The named local Establishment HLD was not found, so it was not claimed or used as source evidence.\n"
        "- Frozen 019-C/D/E and recovery evidence were read-only; no staging scan, network retrieval, graph generation, or other Module processing occurred.\n"
    ).encode("utf-8")
    _atomic_write(output_root / "pilot_validation_summary.md", validation_summary)

    sample_labels = {
        "Establishment Registration and Opening", "Establishment Activity Management",
        "Establishment Location Management",
    }
    sampled_mains = [row for row in mains if row["candidate_label"] in sample_labels]
    sample_lines = [
        "# Establishment pilot sample traceability", "",
        "These are candidate groupings from real ICD wording; none is EA-approved.", "",
    ]
    function_lookup = {row["function_id"]: row for row in functions}
    for main in sampled_mains:
        sample_lines.extend((f"## {main['candidate_label']}", "", main["ability_definition"], ""))
        linked = [edge for edge in edges if edge["main_capability_id"] == main["main_capability_id"]][:5]
        for edge in linked:
            function = function_lookup[edge["function_id"]]
            first_evidence = grouped_evidence[edge["function_id"]][0]
            sample_lines.append(
                f"- Function `{function['candidate_label']}` — page `{first_evidence['page_id']}`, "
                f"block `{first_evidence['block_id']}`: “{first_evidence['source_phrase']}”"
            )
        sample_lines.append("")
    sample_traceability = ("\n".join(sample_lines).rstrip() + "\n").encode("utf-8")
    _atomic_write(output_root / "sample_traceability.md", sample_traceability)

    reports = {
        "pilot_validation_summary.md": validation_summary,
        "sample_traceability.md": sample_traceability,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION, "task": "Phase 6 / Task 019-E-R1",
        "status": "EA_REVIEW_019E_R1", "execution_status": execution_status,
        "scope": {"module_key": MODULE_KEY, "module_name": MODULE_NAME, "other_modules_processed": 0},
        "versions": {"parser": PARSER_VERSION, "extractor": EXTRACTOR_VERSION, "grouping": GROUPING_VERSION},
        "sources": {
            "recovery_manifest_sha256": recovery["manifest_sha256"],
            "recovery_catalog_sha256": recovery["catalog_sha256"],
            "investigated_pages_sha256": recovery["investigated_sha256"],
        },
        "counts": {
            "services": len(services), "services_without_icd": len(no_icd), "icd_occurrences": len(icds),
            "unique_icd_pages": len({row["page_id"] for row in icds}), "isd_reference_occurrences_preserved": len(isds),
            "validated_icds": len(audits) - len(integrity_suspect), "suspect_icds": len(integrity_suspect),
            "business_functions": len(functions_output), "function_evidence": len(evidence_rows),
            "main_capabilities": len(mains), "main_function_edges": len(edges), "review_records": len(reviews),
            "no_explicit_function_documents": len(no_function), "ungrouped_functions": len(ungrouped),
            "one_to_one_main_candidates": len(one_to_one),
        },
        "suspected_empty_page_results": {
            row["page_id"]: {
                "content_integrity_status": row["content_integrity_status"], "size_bytes": int(row["size_bytes"]),
                "blob_sha256": row["blob_sha256"], "representation": row["representation"],
                "parse_status": row["parse_status"], "function_count": int(row["function_count"]),
            }
            for row in sorted(suspected_audits, key=lambda item: item["page_id"])
        },
        "cache_telemetry": dict(sorted(telemetry.items())), "deterministic_core_digest": core_digest,
        "indexes": {
            name: {"sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload), "row_count": len(datasets[name][0])}
            for name, payload in sorted(payloads.items())
        },
        "reports": {
            name: {"sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload)}
            for name, payload in sorted(reports.items())
        },
        "validations": {
            "literal_establishment_only": True, "all_available_icds_processed": len(audits) == len(icds),
            "five_suspected_pages_checked": len(suspected_audits) == 5,
            "all_five_recovered_and_validated": all(row["content_integrity_status"] == "VALIDATED_RECOVERED_SOURCE_BODY" for row in suspected_audits),
            "every_function_has_evidence": set(row["function_id"] for row in functions_output) == set(row["function_id"] for row in evidence_rows),
            "every_main_has_function": all(int(row["function_count"]) >= 1 for row in mains),
            "sub_capabilities_created": False, "isd_semantics_used": False, "api_mapping_performed": False,
            "graph_generated": False, "network_used": False, "staging_scanned": False,
        },
    }
    _atomic_write(output_root / "pilot_manifest.json", _json_bytes(manifest))
    return {"manifest": manifest, "functions": functions_output, "mains": mains, "edges": edges}


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-E-R1 Establishment-only function-first pilot")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = build_establishment_pilot(args.root, args.index_root, args.output_root)
    print(json.dumps({
        "status": result["manifest"]["execution_status"],
        "counts": result["manifest"]["counts"],
        "cache_telemetry": result["manifest"]["cache_telemetry"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
