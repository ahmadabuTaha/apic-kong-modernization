"""Task 019-E module-first ICD capability candidate discovery.

The pipeline consumes only the accepted Task 019-D local retrieval catalog and
selected cached ICD bytes. It creates review candidates, never approved
capabilities, API mappings, or cross-module merges.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .document_cache import CATALOG_NAME, DocumentCatalog


SCHEMA_VERSION = "phase6-task019e-capability-v1"
PARSER_VERSION = "structured-html-v1"
EXTRACTOR_VERSION = "explicit-function-v1"
RULES_VERSION = "module-local-capability-v3"
INDEX_ROOT = Path("indexes/phase6/task019/019e")
OUTPUT_ROOT = Path("outputs/phase6/task019/019e")
BASELINE_019D_INDEX = Path("indexes/phase6/task019/019d")
BASELINE_019D_OUTPUT = Path("outputs/phase6/task019/019d")
EXPECTED = {"modules": 32, "services": 952, "icd_occurrences": 988, "icd_blobs": 981}

PARSE_FIELDS = [
    "module_key", "service_key", "occurrence_id", "document_key", "physical_identity",
    "blob_sha256", "source_version", "parse_status", "block_count", "function_count",
    "cache_status", "gap_reason",
]
MAIN_FIELDS = [
    "main_capability_id", "module_key", "candidate_label", "normalized_label", "status",
    "confidence", "sub_capability_count", "evidence_count", "rationale",
]
SUB_FIELDS = [
    "sub_capability_id", "main_capability_id", "module_key", "candidate_label",
    "normalized_label", "status", "confidence", "evidence_count", "service_count",
    "document_count", "rationale",
]
EVIDENCE_FIELDS = [
    "evidence_id", "module_key", "main_capability_id", "sub_capability_id", "document_key",
    "physical_identity", "blob_sha256", "source_version", "section_heading", "block_id",
    "block_kind", "char_start", "char_end", "source_wording", "extraction_method", "strength",
]
EDGE_FIELDS = [
    "module_key", "main_capability_id", "sub_capability_id", "service_key", "occurrence_id",
    "document_key", "physical_identity", "blob_sha256", "evidence_id",
]
REVIEW_FIELDS = [
    "review_id", "module_key", "service_key", "document_key", "issue_type", "reason",
    "evidence_pointer", "status",
]
COMPLETION_FIELDS = [
    "module_key", "module_name", "completion_status", "service_count", "services_without_icd",
    "icd_expected_occurrences", "icd_available_occurrences", "unique_icd_blobs",
    "icd_processed_blobs", "icd_failed_blobs", "main_capability_count", "sub_capability_count",
    "evidence_count", "review_count", "evidence_closure", "source_signature", "checkpoint_hash",
]
CROSS_FIELDS = [
    "candidate_id", "observation_type", "normalized_label", "module_a", "module_b",
    "sub_capability_a", "sub_capability_b", "evidence_count_a", "evidence_count_b", "status",
]

BLOCK_TAGS = {"p": "paragraph", "li": "list_item", "h1": "heading", "h2": "heading", "h3": "heading", "h4": "heading", "h5": "heading", "h6": "heading"}
TECHNICAL_SECTIONS = (
    "endpoint", "json structure", "request structure", "response structure", "mapping",
    "transformation", "error code", "annex", "target url", "sample message", "data mapping",
)
TECHNICAL_FUNCTION_TERMS = (
    "api endpoint", "access token", "bearer token", "oauth", "http request",
    "http response", "json request", "json response", "service authentication",
)
ACTION_WORDS = {
    "activate", "add", "approve", "assign", "calculate", "cancel", "change", "check", "close",
    "complete", "confirm", "create", "deactivate", "delete", "download", "extend", "fetch",
    "generate", "get", "initiate", "issue", "list", "maintain", "manage", "notify", "open",
    "pay", "process", "provide", "query", "receive", "register", "reject", "renew", "request",
    "retrieve", "search", "send", "submit", "synchronize", "terminate", "track", "transfer",
    "update", "upload", "validate", "verify", "view",
}
GERUND_MAP = {
    "activating": "activate", "adding": "add", "approving": "approve", "assigning": "assign",
    "calculating": "calculate", "cancelling": "cancel", "changing": "change", "checking": "check",
    "creating": "create", "deactivating": "deactivate", "deleting": "delete",
    "generating": "generate", "getting": "get", "issuing": "issue", "listing": "list",
    "managing": "manage", "notifying": "notify", "processing": "process", "registering": "register",
    "rejecting": "reject", "renewing": "renew", "retrieving": "retrieve", "searching": "search",
    "submitting": "submit", "terminating": "terminate", "tracking": "track",
    "transferring": "transfer", "updating": "update", "validating": "validate", "verifying": "verify",
}
CUE_PATTERNS = [
    re.compile(r"\b(?:this|the)\s+service\s+(?:is\s+used\s+to|allows?|enables?|provides?\s+(?:the\s+ability\s+to)?|will|shall)\s+(.+)", re.I),
    re.compile(r"\b(?:purpose|scope)\s+(?:of\s+this\s+service\s+)?(?:is|includes?)\s+(?:to\s+)?(.+)", re.I),
    re.compile(r"\bused\s+(?:to|for)\s+(.+)", re.I),
]


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _stable_id(prefix: str, *parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(value).hexdigest()[:20]}"


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _sanitize_evidence(value: str) -> str:
    value = re.sub(r"https?://\S+", "[URL_REDACTED]", value, flags=re.I)
    value = re.sub(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value, flags=re.I)
    value = re.sub(
        r"\b(password|secret|api[_ -]?key|access[_ -]?token|authorization)\s*[:=]\s*[^\s,;]+",
        lambda match: f"{match.group(1)}=[REDACTED]", value, flags=re.I,
    )
    return _normalize_space(value)


def _normalized_label(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


class StructuredHTMLParser(HTMLParser):
    """Small deterministic block parser retaining headings and table rows."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, Any]] = []
        self.section = ""
        self.active_tag: str | None = None
        self.active_text: list[str] = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.cell_text: list[str] = []
        self.row_cells: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag == "table":
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_row, self.row_cells = True, []
        elif tag in {"td", "th"} and self.in_row:
            self.in_cell, self.cell_text = True, []
        elif tag == "br":
            if self.in_cell:
                self.cell_text.append(" ")
            elif self.active_tag:
                self.active_text.append(" ")
        elif tag in BLOCK_TAGS and not self.in_table and self.active_tag is None:
            self.active_tag, self.active_text = tag, []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_text.append(data)
        elif self.active_tag:
            self.active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in {"td", "th"} and self.in_cell:
            self.row_cells.append(_sanitize_evidence("".join(self.cell_text)))
            self.in_cell, self.cell_text = False, []
        elif tag == "tr" and self.in_row:
            cells = [cell for cell in self.row_cells if cell]
            if cells:
                self._append("table_row", " | ".join(cells), cells)
            self.in_row, self.row_cells = False, []
        elif tag == "table":
            self.in_table = False
        elif tag == self.active_tag:
            text = _sanitize_evidence("".join(self.active_text))
            if text:
                kind = BLOCK_TAGS[tag]
                self._append(kind, text)
                if kind == "heading":
                    self.section = text
            self.active_tag, self.active_text = None, []

    def _append(self, kind: str, text: str, cells: list[str] | None = None) -> None:
        if not text:
            return
        self.blocks.append({"kind": kind, "section_heading": self.section, "text": text, "cells": cells or []})


def parse_html(content: bytes) -> dict[str, Any]:
    try:
        decoded = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        return {"parse_status": "MALFORMED", "gap_reason": f"utf8_decode_error:{error.start}", "blocks": [], "functions": []}
    parser = StructuredHTMLParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception as error:  # HTMLParser extensions can raise on pathological input.
        return {"parse_status": "MALFORMED", "gap_reason": type(error).__name__, "blocks": [], "functions": []}
    blocks, cursor = [], 0
    for ordinal, block in enumerate(parser.blocks, start=1):
        text = block["text"]
        start, end = cursor, cursor + len(text)
        blocks.append({
            **block, "block_id": f"b{ordinal:06d}", "char_start": start, "char_end": end,
            "text_sha256": _sha256_bytes(text.encode("utf-8")),
        })
        cursor = end + 1
    return {
        "parse_status": "PARSED" if blocks else "EMPTY",
        "gap_reason": "" if blocks else "no_supported_text_blocks",
        "blocks": blocks,
    }


def _sentences(text: str) -> list[str]:
    return [part.strip(" -–—:;") for part in re.split(r"(?<=[.!?])\s+|\s*[•·]\s*", text) if part.strip()]


def _clean_phrase(value: str) -> str:
    value = re.split(r"\b(?:this\s+document|the\s+scope\s+of\s+this\s+document)\b", value, maxsplit=1, flags=re.I)[0]
    value = value.strip(" .,:;-()")
    value = re.sub(r"^(?:the\s+)?(?:user|consumer|requester|admin|system)\s+to\s+", "", value, flags=re.I)
    value = re.sub(r"^(?:to\s+)", "", value, flags=re.I)
    words = value.split()
    if words:
        first = re.sub(r"[^A-Za-z]", "", words[0]).casefold()
        if first in GERUND_MAP:
            words[0] = GERUND_MAP[first]
    return _normalize_space(" ".join(words))[:300]


def _capability_labels(phrase: str) -> tuple[str, str] | None:
    tokens = re.findall(r"[A-Za-z0-9]+", phrase)
    if not tokens:
        return None
    first = tokens[0].casefold()
    if first not in ACTION_WORDS:
        return None
    lower = [token.casefold() for token in tokens]
    meaningful = [token for token in lower[1:] if token not in {"a", "an", "the", "all", "and", "or", "of", "for", "to", "from", "with", "by"}]
    if not meaningful or all(token in {"api", "endpoint", "json", "request", "response", "data", "system", "service"} for token in meaningful):
        return None
    sub_label = " ".join(token.capitalize() if not token.isupper() else token for token in tokens[:14])
    action_positions = [index for index, token in enumerate(lower[:4]) if token in ACTION_WORDS]
    start = max(action_positions) + 1 if action_positions else 1
    object_tokens = [
        token for token in tokens[start:start + 8]
        if token.casefold() not in {"a", "an", "the", "all", "and", "or", "of", "for", "to", "from", "with", "by", "details", "information", "list", "data"}
    ]
    if not object_tokens:
        return None
    object_label = " ".join(token.capitalize() if not token.isupper() else token for token in object_tokens)
    main_label = object_label if object_label.casefold().endswith(("management", "processing", "administration")) else f"{object_label} Management"
    return main_label[:120], sub_label[:160]


def extract_functions(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    functions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for block in parsed.get("blocks", []):
        section = str(block["section_heading"]).casefold()
        if any(token in section for token in TECHNICAL_SECTIONS):
            continue
        if block["kind"] not in {"paragraph", "list_item", "table_row"}:
            continue
        for sentence in _sentences(block["text"]):
            if len(sentence) < 16:
                continue
            phrase = ""
            for pattern in CUE_PATTERNS:
                match = pattern.search(sentence)
                if match:
                    phrase = _clean_phrase(match.group(1))
                    break
            normalized_phrase = _normalized_label(phrase)
            if any(term in normalized_phrase for term in TECHNICAL_FUNCTION_TERMS):
                continue
            labels = _capability_labels(phrase) if phrase else None
            if not labels:
                continue
            main_label, sub_label = labels
            key = (_normalized_label(sub_label), block["block_id"])
            if key in seen:
                continue
            seen.add(key)
            strength = "HIGH" if any(token in section for token in ("purpose", "scope", "business")) else "MEDIUM"
            functions.append({
                "main_label": main_label, "sub_label": sub_label, "source_wording": _sanitize_evidence(sentence)[:500],
                "section_heading": block["section_heading"], "block_id": block["block_id"],
                "block_kind": block["kind"], "char_start": block["char_start"], "char_end": block["char_end"],
                "strength": strength, "method": "EXPLICIT_SERVICE_FUNCTION_RULE",
            })
    return functions


def _validated_baseline(root: Path, catalog_path: Path | None = None) -> dict[str, Any]:
    manifest_path = root / BASELINE_019D_OUTPUT / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("TASK019D_MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "phase6-task019d-retrieval-v1":
        raise ValueError("TASK019D_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("status") != "EA_REVIEW_TASK019D":
        raise ValueError("TASK019D_BASELINE_NOT_ACCEPTED_FOR_REVIEW")
    catalog_path = (catalog_path or root / BASELINE_019D_INDEX / CATALOG_NAME).resolve()
    if not catalog_path.is_file():
        raise ValueError("TASK019D_CATALOG_MISSING")
    if catalog_path.stat().st_size != int(manifest["catalog"]["size_bytes"]):
        raise ValueError("TASK019D_CATALOG_SIZE_MISMATCH")
    if _sha256_file(catalog_path) != manifest["catalog"]["sha256"]:
        raise ValueError("TASK019D_CATALOG_HASH_MISMATCH")
    counts = manifest["counts"]
    expected_counts = {
        "modules": EXPECTED["modules"], "services": EXPECTED["services"],
        "ICD": EXPECTED["icd_occurrences"],
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise ValueError(f"TASK019D_CATALOG_COUNT_MISMATCH: {key}={counts.get(key)}")
    try:
        with sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True) as connection:
            metadata = dict(connection.execute("SELECT key, value FROM catalog_meta"))
            actual_counts = {
                "modules": connection.execute("SELECT COUNT(*) FROM modules").fetchone()[0],
                "services": connection.execute("SELECT COUNT(*) FROM services").fetchone()[0],
                "ICD": connection.execute(
                    "SELECT COUNT(*) FROM occurrences WHERE document_type='ICD'"
                ).fetchone()[0],
            }
    except sqlite3.Error as error:
        raise ValueError(f"TASK019D_CATALOG_INVALID: {error}") from error
    if metadata.get("schema_version") != manifest["schema_version"]:
        raise ValueError("TASK019D_CATALOG_SCHEMA_MISMATCH")
    if metadata.get("source_signature") != manifest.get("source_signature"):
        raise ValueError("TASK019D_CATALOG_SOURCE_SIGNATURE_MISMATCH")
    if actual_counts != expected_counts:
        raise ValueError(f"TASK019D_CATALOG_INTERNAL_COUNT_MISMATCH: {actual_counts}")
    return {
        "manifest": manifest, "manifest_sha256": _sha256_file(manifest_path),
        "catalog_path": catalog_path, "catalog_sha256": manifest["catalog"]["sha256"],
    }


def _parse_cache_path(index_root: Path, blob_sha256: str) -> Path:
    cache_key = _stable_id("parse", blob_sha256, PARSER_VERSION, EXTRACTOR_VERSION, RULES_VERSION)
    return index_root / "parse_cache" / f"{cache_key}.json"


def _parsed_document(
    catalog: DocumentCatalog,
    document: dict[str, Any],
    index_root: Path,
    telemetry: Counter[str],
) -> dict[str, Any]:
    path = _parse_cache_path(index_root, document["blob_sha256"])
    expected_key = _stable_id(
        "parse", document["blob_sha256"], PARSER_VERSION, EXTRACTOR_VERSION, RULES_VERSION
    )
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("cache_key") == expected_key and payload.get("blob_sha256") == document["blob_sha256"]:
            telemetry["parse_hits"] += 1
            return payload
    telemetry["parse_misses"] += 1
    result, content = catalog.load_document(document["document_key"])
    if content is None:
        payload = {
            "cache_key": expected_key, "blob_sha256": document["blob_sha256"],
            "parse_status": result["status"].upper(), "gap_reason": result["status"],
            "blocks": [], "functions": [],
        }
    else:
        telemetry["blob_body_reads"] += 1
        parsed = parse_html(content)
        parsed["functions"] = extract_functions(parsed)
        payload = {
            "cache_key": expected_key, "blob_sha256": document["blob_sha256"],
            "parser_version": PARSER_VERSION, "extractor_version": EXTRACTOR_VERSION,
            "rules_version": RULES_VERSION, **parsed,
        }
    _atomic_write(path, _json_bytes(payload))
    return payload


def _module_source_signature(
    module: dict[str, Any], services: list[dict[str, Any]], documents: list[dict[str, Any]], baseline: dict[str, Any]
) -> str:
    payload = {
        "module": module,
        "services": [{key: row[key] for key in ("service_key", "service_name")} for row in services],
        "icd_documents": [
            {key: row[key] for key in (
                "occurrence_id", "document_key", "service_key", "physical_identity", "blob_sha256",
                "size_bytes", "source_version", "status", "source_row_number", "reference_ordinal",
            )}
            for row in documents
        ],
        "baseline_catalog_sha256": baseline["catalog_sha256"],
        "parser_version": PARSER_VERSION, "extractor_version": EXTRACTOR_VERSION,
        "rules_version": RULES_VERSION,
    }
    return _sha256_bytes(_json_bytes(payload))


def _review(
    module_key: str, issue_type: str, reason: str, service_key: str = "",
    document_key: str = "", pointer: str = "",
) -> dict[str, Any]:
    return {
        "review_id": _stable_id("review", module_key, issue_type, service_key, document_key, pointer),
        "module_key": module_key, "service_key": service_key, "document_key": document_key,
        "issue_type": issue_type, "reason": reason, "evidence_pointer": pointer,
        "status": "EA_REVIEW_REQUIRED",
    }


def _build_module(
    module: dict[str, Any], services: list[dict[str, Any]], documents: list[dict[str, Any]],
    catalog: DocumentCatalog, index_root: Path, source_signature: str, telemetry: Counter[str],
) -> dict[str, Any]:
    module_key = module["module_key"]
    reviews: list[dict[str, Any]] = []
    service_has_icd = {row["service_key"] for row in documents}
    for service in services:
        if service["service_key"] not in service_has_icd:
            reviews.append(_review(
                module_key, "NO_ICD_REFERENCE", "Service has no ICD reference; no capability inferred",
                service["service_key"],
            ))

    parsed_by_hash: dict[str, dict[str, Any]] = {}
    parse_rows: list[dict[str, Any]] = []
    for document in documents:
        digest = document["blob_sha256"]
        cache_before = telemetry["parse_hits"]
        parsed = parsed_by_hash.get(digest)
        if parsed is None:
            parsed = _parsed_document(catalog, document, index_root, telemetry)
            parsed_by_hash[digest] = parsed
            cache_status = "HIT" if telemetry["parse_hits"] > cache_before else "MISS"
        else:
            cache_status = "MODULE_REUSE"
        parse_rows.append({
            "module_key": module_key, "service_key": document["service_key"],
            "occurrence_id": document["occurrence_id"], "document_key": document["document_key"],
            "physical_identity": document["physical_identity"], "blob_sha256": digest,
            "source_version": document["source_version"], "parse_status": parsed["parse_status"],
            "block_count": len(parsed.get("blocks", [])), "function_count": len(parsed.get("functions", [])),
            "cache_status": cache_status, "gap_reason": parsed.get("gap_reason", ""),
        })
        if parsed["parse_status"] != "PARSED":
            reviews.append(_review(
                module_key, "ICD_PARSE_GAP", parsed.get("gap_reason", parsed["parse_status"]),
                document["service_key"], document["document_key"], digest,
            ))
        elif not parsed.get("functions"):
            reviews.append(_review(
                module_key, "NO_EXPLICIT_BUSINESS_FUNCTION",
                "Parsed ICD contains no function statement meeting conservative evidence rules",
                document["service_key"], document["document_key"], digest,
            ))

    evidence_by_id: dict[str, dict[str, Any]] = {}
    sub_by_key: dict[str, dict[str, Any]] = {}
    edges_by_key: dict[tuple[str, ...], dict[str, Any]] = {}
    # Construct Sub candidates only after every available ICD in the Module has
    # been parsed. Main candidates are assembled from this complete local Sub
    # set below, preserving the mandated module-local ordering.
    for document in documents:
        parsed = parsed_by_hash[document["blob_sha256"]]
        for function in parsed.get("functions", []):
            main_normalized = _normalized_label(function["main_label"])
            sub_normalized = _normalized_label(function["sub_label"])
            main_id = _stable_id("main", module_key, main_normalized)
            sub_key = f"{main_normalized}\x1f{sub_normalized}"
            sub_id = _stable_id("sub", module_key, main_normalized, sub_normalized)
            evidence_id = _stable_id(
                "evidence", module_key, document["blob_sha256"], function["block_id"],
                main_normalized, sub_normalized,
            )
            evidence_by_id.setdefault(evidence_id, {
                "evidence_id": evidence_id, "module_key": module_key,
                "main_capability_id": main_id, "sub_capability_id": sub_id,
                "document_key": document["document_key"], "physical_identity": document["physical_identity"],
                "blob_sha256": document["blob_sha256"], "source_version": document["source_version"],
                "section_heading": function["section_heading"], "block_id": function["block_id"],
                "block_kind": function["block_kind"], "char_start": function["char_start"],
                "char_end": function["char_end"], "source_wording": function["source_wording"],
                "extraction_method": function["method"], "strength": function["strength"],
            })
            sub = sub_by_key.setdefault(sub_key, {
                "sub_capability_id": sub_id, "main_capability_id": main_id, "module_key": module_key,
                "main_candidate_label": function["main_label"], "main_normalized": main_normalized,
                "candidate_label": function["sub_label"], "normalized_label": sub_normalized,
                "status": "candidate" if function["strength"] == "HIGH" else "needs_review",
                "confidence": function["strength"], "evidence_ids": set(), "service_keys": set(),
                "document_keys": set(),
                "rationale": "Normalized from explicit ICD service-function wording; EA approval pending",
            })
            sub["evidence_ids"].add(evidence_id)
            sub["service_keys"].add(document["service_key"])
            sub["document_keys"].add(document["document_key"])
            if function["strength"] == "HIGH":
                sub["confidence"], sub["status"] = "HIGH", "candidate"
            edge_key = (sub_id, document["service_key"], document["occurrence_id"], evidence_id)
            edges_by_key[edge_key] = {
                "module_key": module_key, "main_capability_id": main_id,
                "sub_capability_id": sub_id, "service_key": document["service_key"],
                "occurrence_id": document["occurrence_id"], "document_key": document["document_key"],
                "physical_identity": document["physical_identity"], "blob_sha256": document["blob_sha256"],
                "evidence_id": evidence_id,
            }

    main_by_key: dict[str, dict[str, Any]] = {}
    for sub in sub_by_key.values():
        main = main_by_key.setdefault(sub["main_normalized"], {
            "main_capability_id": sub["main_capability_id"], "module_key": module_key,
            "candidate_label": sub["main_candidate_label"],
            "normalized_label": sub["main_normalized"], "status": "candidate",
            "confidence": sub["confidence"], "sub_ids": set(), "evidence_ids": set(),
            "rationale": "Module-local grouping assembled after complete Sub candidate construction",
        })
        main["sub_ids"].add(sub["sub_capability_id"])
        main["evidence_ids"].update(sub["evidence_ids"])
        if sub["confidence"] == "HIGH":
            main["confidence"] = "HIGH"

    mains = []
    for item in sorted(main_by_key.values(), key=lambda row: (row["normalized_label"], row["main_capability_id"])):
        mains.append({
            **{key: value for key, value in item.items() if key not in {"sub_ids", "evidence_ids"}},
            "sub_capability_count": len(item["sub_ids"]), "evidence_count": len(item["evidence_ids"]),
        })
    subs = []
    for item in sorted(sub_by_key.values(), key=lambda row: (row["normalized_label"], row["sub_capability_id"])):
        subs.append({
            **{key: value for key, value in item.items() if key not in {
                "evidence_ids", "service_keys", "document_keys", "main_candidate_label", "main_normalized",
            }},
            "evidence_count": len(item["evidence_ids"]), "service_count": len(item["service_keys"]),
            "document_count": len(item["document_keys"]),
        })
    evidence = sorted(evidence_by_id.values(), key=lambda row: row["evidence_id"])
    edges = sorted(edges_by_key.values(), key=lambda row: (
        row["sub_capability_id"], row["service_key"], row["occurrence_id"], row["evidence_id"]
    ))
    reviews = sorted({row["review_id"]: row for row in reviews}.values(), key=lambda row: row["review_id"])
    processed = {row["blob_sha256"] for row in parse_rows if row["parse_status"] == "PARSED"}
    failed = {row["blob_sha256"] for row in parse_rows if row["parse_status"] != "PARSED"}
    gaps = bool(reviews)
    completion_status = "MODULE_COMPLETE_WITH_GAPS" if gaps else "MODULE_COMPLETE_WITH_EVIDENCE"
    model = {
        "schema_version": SCHEMA_VERSION, "module": module, "source_signature": source_signature,
        "candidate_status_notice": "EA review input only; no capability boundary is approved",
        "services": services, "icd_parse_status": parse_rows, "main_capabilities": mains,
        "sub_capabilities": subs, "capability_evidence": evidence,
        "capability_service_icd_edges": edges, "review_queue": reviews,
    }
    model_bytes = _json_bytes(model)
    completion = {
        "schema_version": SCHEMA_VERSION, "module_key": module_key, "module_name": module["module_name"],
        "completion_status": completion_status, "service_count": len(services),
        "services_without_icd": len(services) - len(service_has_icd),
        "icd_expected_occurrences": len(documents), "icd_available_occurrences": len(documents),
        "unique_icd_blobs": len({row["blob_sha256"] for row in documents}),
        "icd_processed_blobs": len(processed), "icd_failed_blobs": len(failed),
        "main_capability_count": len(mains), "sub_capability_count": len(subs),
        "evidence_count": len(evidence), "review_count": len(reviews),
        "evidence_closure": len(processed) + len(failed) == len({row["blob_sha256"] for row in documents}),
        "source_signature": source_signature, "model_sha256": _sha256_bytes(model_bytes),
    }
    return {"model": model, "model_bytes": model_bytes, "completion": completion}


def _module_checkpoint_valid(module_root: Path, source_signature: str) -> bool:
    manifest_path = module_root / "module_completion_manifest.json"
    model_path = module_root / "module_capability_model.json"
    if not manifest_path.is_file() or not model_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return (
            manifest["source_signature"] == source_signature
            and manifest["schema_version"] == SCHEMA_VERSION
            and manifest["model_sha256"] == _sha256_file(model_path)
            and manifest["completion_status"] != "MODULE_PARTIAL"
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False


def _completion_row(completion: dict[str, Any], checkpoint_hash: str) -> dict[str, Any]:
    return {
        **{key: completion[key] for key in COMPLETION_FIELDS if key not in {"checkpoint_hash"}},
        "evidence_closure": str(bool(completion["evidence_closure"])).lower(),
        "checkpoint_hash": checkpoint_hash,
    }


def _cross_module_candidates(subs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sub in subs:
        grouped[sub["normalized_label"]].append(sub)
    rows = []
    for normalized, candidates in sorted(grouped.items()):
        candidates.sort(key=lambda row: (row["module_key"], row["sub_capability_id"]))
        for index, left in enumerate(candidates):
            for right in candidates[index + 1:]:
                if left["module_key"] == right["module_key"]:
                    continue
                rows.append({
                    "candidate_id": _stable_id("cross", normalized, left["module_key"], right["module_key"]),
                    "observation_type": "EXACT_NORMALIZED_SUB_LABEL", "normalized_label": normalized,
                    "module_a": left["module_key"], "module_b": right["module_key"],
                    "sub_capability_a": left["sub_capability_id"], "sub_capability_b": right["sub_capability_id"],
                    "evidence_count_a": left["evidence_count"], "evidence_count_b": right["evidence_count"],
                    "status": "EA_COMPARISON_REQUIRED_NO_MERGE",
                })
    return rows


def build_capability_discovery(
    root: Path,
    index_root: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    baseline = _validated_baseline(root)
    telemetry: Counter[str] = Counter()
    all_models: list[dict[str, Any]] = []
    completion_rows: list[dict[str, Any]] = []
    with DocumentCatalog(root, baseline["catalog_path"]) as catalog:
        modules = catalog.list_modules()
        if len(modules) != EXPECTED["modules"]:
            raise ValueError("TASK019E_MODULE_CLOSURE_MISMATCH")
        total_services = 0
        total_icd = 0
        all_icd_hashes: set[str] = set()
        for module in modules:
            module_key = module["module_key"]
            services = catalog.list_services(module_key)
            documents = catalog.list_documents(module_key, document_type="ICD")
            total_services += len(services)
            total_icd += len(documents)
            all_icd_hashes.update(row["blob_sha256"] for row in documents)
            signature = _module_source_signature(module, services, documents, baseline)
            module_root = output_root / "modules" / module_key
            if _module_checkpoint_valid(module_root, signature):
                telemetry["module_checkpoint_hits"] += 1
                model = json.loads((module_root / "module_capability_model.json").read_text(encoding="utf-8"))
                completion = json.loads((module_root / "module_completion_manifest.json").read_text(encoding="utf-8"))
            else:
                telemetry["module_checkpoint_misses"] += 1
                result = _build_module(
                    module, services, documents, catalog, index_root, signature, telemetry
                )
                model, completion = result["model"], result["completion"]
                _atomic_write(module_root / "module_capability_model.json", result["model_bytes"])
                _atomic_write(module_root / "module_completion_manifest.json", _json_bytes(completion))
            all_models.append(model)
            checkpoint_hash = _sha256_file(module_root / "module_completion_manifest.json")
            completion_rows.append(_completion_row(completion, checkpoint_hash))
        if total_services != EXPECTED["services"] or total_icd != EXPECTED["icd_occurrences"]:
            raise ValueError("TASK019E_SERVICE_ICD_CLOSURE_MISMATCH")
        if len(all_icd_hashes) != EXPECTED["icd_blobs"]:
            raise ValueError("TASK019E_ICD_BLOB_CLOSURE_MISMATCH")

    parse_rows = [row for model in all_models for row in model["icd_parse_status"]]
    mains = [row for model in all_models for row in model["main_capabilities"]]
    subs = [row for model in all_models for row in model["sub_capabilities"]]
    evidence = [row for model in all_models for row in model["capability_evidence"]]
    edges = [row for model in all_models for row in model["capability_service_icd_edges"]]
    reviews = [row for model in all_models for row in model["review_queue"]]
    cross = _cross_module_candidates(subs)
    datasets = {
        "icd_parse_status.csv": (parse_rows, PARSE_FIELDS),
        "main_capabilities.csv": (mains, MAIN_FIELDS),
        "sub_capabilities.csv": (subs, SUB_FIELDS),
        "capability_evidence.csv": (evidence, EVIDENCE_FIELDS),
        "capability_service_icd_edges.csv": (edges, EDGE_FIELDS),
        "review_queue.csv": (reviews, REVIEW_FIELDS),
        "module_completion.csv": (completion_rows, COMPLETION_FIELDS),
        "cross_module_review_candidates.csv": (cross, CROSS_FIELDS),
    }
    index_payloads: dict[str, bytes] = {}
    for name, (rows, fields) in datasets.items():
        payload = _csv_bytes(rows, fields)
        index_payloads[name] = payload
        _atomic_write(index_root / name, payload)

    completion_counts = Counter(row["completion_status"] for row in completion_rows)
    coverage_rows = completion_rows
    _atomic_write(output_root / "module_coverage.csv", _csv_bytes(coverage_rows, COMPLETION_FIELDS))
    no_icd_examples = [
        row for row in reviews if row["issue_type"] == "NO_ICD_REFERENCE"
    ]
    examples = {
        "module_to_capabilities": {
            "module_key": all_models[0]["module"]["module_key"],
            "main_capabilities": all_models[0]["main_capabilities"][:2],
            "sub_capabilities": all_models[0]["sub_capabilities"][:3],
        },
        "sub_to_services_icds_evidence": edges[:3],
        "icd_to_candidate_capabilities": [
            row for row in evidence[:3]
        ],
        "no_icd_service": no_icd_examples[0] if no_icd_examples else None,
    }
    _atomic_write(output_root / "retrieval_examples.json", _json_bytes(examples))

    review_types_by_module: dict[str, Counter[str]] = defaultdict(Counter)
    for review in reviews:
        review_types_by_module[review["module_key"]][review["issue_type"]] += 1
    gaps_by_module = [
        {
            "module_key": row["module_key"], "status": row["completion_status"],
            "review_count": row["review_count"],
            "review_types": dict(sorted(review_types_by_module[row["module_key"]].items())),
        }
        for row in completion_rows if row["completion_status"] != "MODULE_COMPLETE_WITH_EVIDENCE"
    ]
    overall = "PARTIAL" if completion_counts["MODULE_PARTIAL"] else "TECHNICAL_PASS_WITH_GAPS" if gaps_by_module else "TECHNICAL_PASS"
    summary = (
        "# Phase 6 Task 019-E validation summary\n\n"
        f"- Execution status: {overall}; processed Modules: {len(completion_rows)}/32.\n"
        f"- Module completion: {dict(sorted(completion_counts.items()))}.\n"
        f"- Coverage: {sum(int(row['service_count']) for row in completion_rows)} services; "
        f"{len(parse_rows)} ICD occurrences; {len(all_icd_hashes)} unique ICD blobs.\n"
        f"- Candidates: {len(mains)} Main; {len(subs)} Sub; {len(evidence)} evidence spans; "
        f"{len(edges)} Service/ICD edges. All remain EA review inputs.\n"
        f"- Review/gap records: {len(reviews)}; cross-module comparison observations: {len(cross)}; no merge performed.\n"
        f"- Cache telemetry: Module checkpoint HIT {telemetry['module_checkpoint_hits']}, MISS {telemetry['module_checkpoint_misses']}; "
        f"parse HIT {telemetry['parse_hits']}, MISS {telemetry['parse_misses']}; blob reads {telemetry['blob_body_reads']}.\n"
        f"- Modules with gaps: {json.dumps(gaps_by_module, sort_keys=True)}.\n"
        "- Candidate derivation required explicit ICD function wording; names, ISDs, prior classifiers and APIs were not candidate sources.\n"
        "- No network, Confluence retrieval, staging scan, API matching, graph construction or downstream 019-F work occurred.\n"
    ).encode("utf-8")
    _atomic_write(output_root / "validation_summary.md", summary)
    report_files = {
        name: output_root / name for name in (
            "module_coverage.csv", "retrieval_examples.json", "validation_summary.md"
        )
    }
    manifest = {
        "schema_version": SCHEMA_VERSION, "task": "Phase 6 / Task 019-E",
        "status": "EA_REVIEW_TASK019E", "execution_status": overall,
        "versions": {
            "parser": PARSER_VERSION, "extractor": EXTRACTOR_VERSION, "rules": RULES_VERSION,
        },
        "baseline": {
            "task019d_manifest_sha256": baseline["manifest_sha256"],
            "task019d_catalog_sha256": baseline["catalog_sha256"],
        },
        "counts": {
            "modules_processed": len(completion_rows), "services": sum(int(row["service_count"]) for row in completion_rows),
            "icd_occurrences": len(parse_rows), "unique_icd_blobs": len(all_icd_hashes),
            "main_capabilities": len(mains), "sub_capabilities": len(subs),
            "evidence_spans": len(evidence), "service_icd_edges": len(edges),
            "review_records": len(reviews), "cross_module_review_candidates": len(cross),
        },
        "module_completion_counts": dict(sorted(completion_counts.items())),
        "cache_telemetry": {
            key: telemetry[key] for key in (
                "module_checkpoint_hits", "module_checkpoint_misses", "parse_hits",
                "parse_misses", "blob_body_reads",
            )
        },
        "indexes": {
            name: {"sha256": _sha256_bytes(payload), "size_bytes": len(payload), "row_count": len(datasets[name][0])}
            for name, payload in sorted(index_payloads.items())
        },
        "reports": {
            name: {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size}
            for name, path in sorted(report_files.items())
        },
        "validations": {
            "all_modules_processed": len(completion_rows) == EXPECTED["modules"],
            "all_services_represented": sum(int(row["service_count"]) for row in completion_rows) == EXPECTED["services"],
            "all_icd_occurrences_reconciled": len(parse_rows) == EXPECTED["icd_occurrences"],
            "candidate_evidence_required": True, "module_first_checkpointed": True,
            "cross_module_merge_performed": False, "isd_semantics_used": False,
            "network_used": False, "staging_scanned": False,
        },
    }
    _atomic_write(output_root / "manifest.json", _json_bytes(manifest))
    return {"manifest": manifest, "completion": completion_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-E module-first ICD capability discovery")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = build_capability_discovery(args.root, args.index_root, args.output_root)
    print(json.dumps({
        "status": result["manifest"]["execution_status"],
        "counts": result["manifest"]["counts"],
        "module_completion_counts": result["manifest"]["module_completion_counts"],
        "cache_telemetry": result["manifest"]["cache_telemetry"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
