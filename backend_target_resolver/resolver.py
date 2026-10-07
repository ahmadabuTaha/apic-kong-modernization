"""Deterministic catalog-property indexing, target extraction, and SQLite caching."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml


PARSER_VERSION = "phase4-target-parser-v2"
CACHE_SCHEMA_VERSION = "phase4-resolution-cache-v1"
PROPERTY_INDEX_PATH = Path("indexes/catalog_properties.jsonl")
TARGET_INDEX_PATH = Path("indexes/backend_target_resolution.jsonl")
CACHE_PATH = Path("indexes/cache/phase4_resolution_cache.sqlite3")
TOKEN_PATTERN = re.compile(r"\$\(([^()]+)\)")
RUNTIME_PATTERN = re.compile(r"\$\{[^{}]+\}|\{\{[^{}]+\}\}")
SECRET_NAME_PATTERN = re.compile(
    r"(?:password|passwd|secret|token|api[-_]?key|private[-_]?key|credential|client[-_]?secret)",
    re.IGNORECASE,
)
SECRET_QUERY_PATTERN = re.compile(
    r"(?:password|passwd|secret|token|api[-_]?key|access[-_]?key|client[-_]?secret)",
    re.IGNORECASE,
)
RUNTIME_TOKEN_PREFIXES = (
    "request.",
    "message.",
    "api.",
    "context.",
    "env.",
    "session.",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return f"{prefix}:sha256:{_sha256_bytes(payload.encode())}"


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _is_protected(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().casefold() in {
        "1",
        "true",
        "yes",
        "protected",
        "encrypted",
    }


def _has_url_credentials(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return True
    return bool(parsed.scheme and (parsed.username is not None or parsed.password is not None))


def _safe_property_value(name: str, value: Any, protected: Any) -> tuple[str, str | None, str | None]:
    if _is_protected(protected):
        return "PROTECTED", None, "protected_flag_set"
    if not isinstance(value, str) or not value.strip():
        return "UNAVAILABLE", None, "missing_or_non_string_value"
    if SECRET_NAME_PATTERN.search(name):
        return "REDACTED_SECRET_LIKE", None, "secret_like_property_name"
    if _has_url_credentials(value):
        return "REDACTED_SECRET_LIKE", None, "credentials_embedded_in_url"
    return "SAFE_NON_SECRET", value.strip(), None


def index_catalog_properties(
    properties_path: Path,
    *,
    source_label: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    raw = properties_path.read_bytes()
    source_sha = _sha256_bytes(raw)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"catalog properties file is malformed JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("catalogProperties"), list):
        raise ValueError("catalog properties file must contain a catalogProperties array")

    source_name = source_label or properties_path.as_posix()
    prepared: list[dict[str, Any]] = []
    grouped_raw: dict[str, list[tuple[int, Any, str, str | None, str | None]]] = defaultdict(list)
    malformed_count = 0
    for index, item in enumerate(payload["catalogProperties"]):
        pointer = f"/catalogProperties/{index}"
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
            malformed_count += 1
            prepared.append(
                {
                    "catalog_property_record_id": _stable_id("catalog-property", pointer),
                    "exact_property_name": None,
                    "normalized_lookup_name": None,
                    "value_classification": "MALFORMED",
                    "protected_value_state": "UNKNOWN",
                    "safe_value": None,
                    "redaction_reason": "malformed_property_record",
                    "lookup_cardinality": "malformed_record",
                    "source_file": source_name,
                    "source_json_pointer": pointer,
                    "source_file_sha256": source_sha,
                    "evidence_state": "EXPLICIT_SOURCE_EVIDENCE",
                    "confidence": "HIGH",
                }
            )
            continue
        name = item["name"].strip()
        classification, safe_value, reason = _safe_property_value(
            name, item.get("value"), item.get("protected")
        )
        grouped_raw[name].append((index, item.get("value"), classification, safe_value, reason))

    cardinality: dict[str, str] = {}
    for name, values in grouped_raw.items():
        classifications = {item[2] for item in values}
        raw_values = {item[1] for item in values if isinstance(item[1], str)}
        if classifications & {"PROTECTED", "REDACTED_SECRET_LIKE", "UNAVAILABLE"}:
            cardinality[name] = "protected_or_unavailable_value"
        elif len(raw_values) > 1:
            cardinality[name] = "conflicting_multiple_values"
        elif len(values) > 1:
            cardinality[name] = "repeated_same_value"
        else:
            cardinality[name] = "unique_exact_value"

    for name in sorted(grouped_raw):
        for index, _raw_value, classification, safe_value, reason in grouped_raw[name]:
            prepared.append(
                {
                    "catalog_property_record_id": _stable_id(
                        "catalog-property", source_name, index, name
                    ),
                    "exact_property_name": name,
                    "normalized_lookup_name": name,
                    "value_classification": classification,
                    "protected_value_state": (
                        "PROTECTED" if classification == "PROTECTED" else "NOT_PROTECTED"
                    ),
                    "safe_value": safe_value,
                    "redaction_reason": reason,
                    "lookup_cardinality": cardinality[name],
                    "source_file": source_name,
                    "source_json_pointer": f"/catalogProperties/{index}",
                    "source_file_sha256": source_sha,
                    "evidence_state": "EXPLICIT_SOURCE_EVIDENCE",
                    "confidence": "HIGH",
                }
            )
    prepared.sort(
        key=lambda item: (
            item.get("normalized_lookup_name") or "",
            item["source_json_pointer"],
            item["catalog_property_record_id"],
        )
    )
    lookup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in prepared:
        if item["exact_property_name"] is not None:
            lookup[item["exact_property_name"]].append(item)
    counts = Counter(cardinality.values())
    summary = {
        "source_file": source_name,
        "source_file_sha256": source_sha,
        "observed_top_level_keys": sorted(payload),
        "catalog_property_record_count": len(payload["catalogProperties"]),
        "indexed_record_count": len(prepared),
        "distinct_exact_property_name_count": len(grouped_raw),
        "malformed_record_count": malformed_count,
        "unique_exact_value_name_count": counts["unique_exact_value"],
        "repeated_same_value_name_count": counts["repeated_same_value"],
        "conflicting_multiple_values_name_count": counts["conflicting_multiple_values"],
        "protected_or_unavailable_name_count": counts["protected_or_unavailable_value"],
        "safe_value_record_count": sum(item["safe_value"] is not None for item in prepared),
        "protected_record_count": sum(item["value_classification"] == "PROTECTED" for item in prepared),
        "secret_like_redacted_record_count": sum(item["value_classification"] == "REDACTED_SECRET_LIKE" for item in prepared),
    }
    return prepared, dict(lookup), summary


def extract_symbolic_tokens(expression: str) -> list[str]:
    return sorted(set(TOKEN_PATTERN.findall(expression)))


def _sanitize_expression(value: str) -> tuple[str, list[str]]:
    text = value.strip()
    reasons: list[str] = []
    try:
        parsed = urlsplit(text)
    except ValueError:
        return "[REDACTED_UNSAFE_TARGET_EXPRESSION]", ["invalid_url_structure"]
    if parsed.scheme and (parsed.username is not None or parsed.password is not None):
        host = parsed.hostname or ""
        if parsed.port:
            host += f":{parsed.port}"
        text = urlunsplit((parsed.scheme, f"redacted@{host}", parsed.path, parsed.query, parsed.fragment))
        reasons.append("embedded_url_credentials_redacted")
        parsed = urlsplit(text)
    if parsed.query:
        query = []
        changed = False
        for key, item in parse_qsl(parsed.query, keep_blank_values=True):
            if SECRET_QUERY_PATTERN.search(key):
                query.append((key, "[REDACTED]"))
                changed = True
            else:
                query.append((key, item))
        if changed:
            text = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
            reasons.append("secret_like_query_parameter_redacted")
    return text, reasons


def _lookup_token(
    token: str, lookup: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    records = lookup.get(token, [])
    if not records:
        return {
            "symbolic_property_name": token,
            "lookup_status": "MISSING",
            "property_record_ids": [],
            "safe_value": None,
            "reason": "unresolved_due_to_missing_catalog_property",
        }
    kinds = {item["lookup_cardinality"] for item in records}
    record_ids = sorted(item["catalog_property_record_id"] for item in records)
    if "conflicting_multiple_values" in kinds:
        return {
            "symbolic_property_name": token,
            "lookup_status": "AMBIGUOUS",
            "property_record_ids": record_ids,
            "safe_value": None,
            "reason": "ambiguous_due_to_conflicting_catalog_property_values",
        }
    safe_values = {item["safe_value"] for item in records if item["safe_value"] is not None}
    if len(safe_values) == 1 and not any(
        item["value_classification"] in {"PROTECTED", "REDACTED_SECRET_LIKE", "UNAVAILABLE"}
        for item in records
    ):
        return {
            "symbolic_property_name": token,
            "lookup_status": "RESOLVED",
            "property_record_ids": record_ids,
            "safe_value": next(iter(safe_values)),
            "reason": "exact_catalog_property_match",
        }
    return {
        "symbolic_property_name": token,
        "lookup_status": "PROTECTED_OR_REDACTED",
        "property_record_ids": record_ids,
        "safe_value": None,
        "reason": "unresolved_due_to_protected_catalog_property_value",
    }


def _runtime_token(token: str) -> bool:
    folded = token.casefold()
    return any(folded.startswith(prefix) for prefix in RUNTIME_TOKEN_PREFIXES)


def _normalize_target(value: str | None) -> dict[str, str | int | None]:
    result: dict[str, str | int | None] = {
        "normalized_scheme": None,
        "normalized_host_or_value_key": None,
        "normalized_port": None,
        "normalized_target_path": None,
    }
    if not value or "$" in value or "{{" in value:
        return result
    candidate = value.strip()
    parsed = urlsplit(candidate if "://" in candidate else f"//{candidate}")
    result["normalized_scheme"] = parsed.scheme or None
    result["normalized_host_or_value_key"] = (parsed.hostname or "").casefold() or None
    try:
        result["normalized_port"] = parsed.port
    except ValueError:
        result["normalized_port"] = None
    result["normalized_target_path"] = parsed.path or "/"
    return result


def _path_suffix_or_template(expression: str | None) -> str | None:
    if not expression:
        return None
    without_tokens = TOKEN_PATTERN.sub("", expression)
    if "://" in without_tokens:
        try:
            return urlsplit(without_tokens).path or "/"
        except ValueError:
            return None
    slash = without_tokens.find("/")
    return without_tokens[slash:] if slash >= 0 else None


def resolve_target_expression(
    expression: Any,
    property_lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    if not isinstance(expression, str):
        return {
            "original_safe_target_expression": None,
            "target_expression_redaction_reasons": [],
            "symbolic_property_tokens": [],
            "property_lookup_results": [],
            "resolved_safe_target_expression": None,
            "target_classification": "UNSUPPORTED_EXPRESSION_SHAPE",
            "resolution_status": "UNRESOLVED",
            "resolution_reason": "unclassified_due_to_unsupported_target_expression_shape",
            "target_path_suffix_or_template": None,
            **_normalize_target(None),
        }
    safe_expression, redactions = _sanitize_expression(expression)
    tokens = extract_symbolic_tokens(safe_expression)
    runtime_tokens = [token for token in tokens if _runtime_token(token)]
    catalog_tokens = [token for token in tokens if token not in runtime_tokens]
    lookups = [_lookup_token(token, property_lookup) for token in catalog_tokens]
    resolved = safe_expression
    for result in lookups:
        if result["lookup_status"] == "RESOLVED":
            resolved = resolved.replace(
                f"$({result['symbolic_property_name']})", result["safe_value"]
            )
    has_runtime = bool(runtime_tokens or RUNTIME_PATTERN.search(resolved))
    statuses = {item["lookup_status"] for item in lookups}
    unresolved_tokens = statuses & {"MISSING", "AMBIGUOUS", "PROTECTED_OR_REDACTED"}
    resolved_value: str | None = None
    if not tokens and not has_runtime:
        classification, status, reason = "STATIC_LITERAL", "RESOLVED", "static_literal_target"
    elif has_runtime and not catalog_tokens:
        classification, status, reason = "RUNTIME_PARAMETERIZED", "UNRESOLVED", "unresolved_due_to_runtime_parameterization"
    elif unresolved_tokens or has_runtime:
        if "AMBIGUOUS" in statuses and not ({"MISSING", "PROTECTED_OR_REDACTED"} & statuses) and not has_runtime:
            classification, status, reason = "CATALOG_PROPERTY_AMBIGUOUS", "AMBIGUOUS", "ambiguous_due_to_conflicting_catalog_property_values"
        elif len(catalog_tokens) == 1 and not has_runtime and statuses == {"MISSING"}:
            classification, status, reason = "CATALOG_PROPERTY_UNRESOLVED", "UNRESOLVED", "unresolved_due_to_missing_catalog_property"
        elif len(catalog_tokens) == 1 and not has_runtime and statuses == {"PROTECTED_OR_REDACTED"}:
            classification, status, reason = "CATALOG_PROPERTY_UNRESOLVED", "UNRESOLVED", "unresolved_due_to_protected_catalog_property_value"
        else:
            classification, status = "MIXED_PARAMETERIZED", "UNRESOLVED"
            reason = "partially_resolved_target_expression"
        resolved_value = None
    else:
        classification, status, reason = "CATALOG_PROPERTY_RESOLVED", "RESOLVED", "all_catalog_properties_resolved_exactly"
        resolved_value = resolved
    if not (unresolved_tokens or has_runtime):
        resolved_value = resolved
    return {
        "original_safe_target_expression": safe_expression,
        "target_expression_redaction_reasons": redactions,
        "symbolic_property_tokens": tokens,
        "runtime_parameter_tokens": runtime_tokens,
        "property_lookup_results": [
            {key: value for key, value in item.items() if key != "safe_value"}
            for item in lookups
        ],
        "resolved_safe_target_expression": resolved_value,
        "target_classification": classification,
        "resolution_status": status,
        "resolution_reason": reason,
        "target_path_suffix_or_template": _path_suffix_or_template(safe_expression),
        **_normalize_target(resolved_value),
    }


def _escape_pointer(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _operation_scope(value: Any) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    scopes = []
    for operation in value:
        if isinstance(operation, dict):
            scopes.append(
                {
                    "verb": operation.get("verb"),
                    "path": operation.get("path"),
                    "operation_id": operation.get("operationId") or operation.get("operation-id"),
                }
            )
    return scopes or None


def extract_target_observations(document: Any) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    def walk(value: Any, pointer: str, scope: list[dict[str, Any]] | None) -> None:
        if isinstance(value, dict):
            if "operations" in value and "execute" in value:
                local_scope = _operation_scope(value.get("operations")) or scope
                walk(value["execute"], f"{pointer}/execute", local_scope)
                for key, item in value.items():
                    if key not in {"operations", "execute"}:
                        walk(item, f"{pointer}/{_escape_pointer(key)}", scope)
                return
            for key, item in value.items():
                child = f"{pointer}/{_escape_pointer(key)}"
                if key == "invoke" and isinstance(item, dict) and (
                    "target-url" in item or "target_url" in item
                ):
                    target_key = "target-url" if "target-url" in item else "target_url"
                    raw_target = item.get(target_key)
                    if isinstance(raw_target, str):
                        safe_target, redactions = _sanitize_expression(raw_target)
                    else:
                        safe_target, redactions = None, []
                    observations.append(
                        {
                            "source_pointer": f"{child}/{target_key}",
                            "operation_scope": scope,
                            "invocation_mechanism": "invoke",
                            "invoke_title": item.get("title"),
                            "http_verb": item.get("verb"),
                            "backend_type": item.get("backend-type"),
                            "safe_target_expression": safe_target,
                            "target_expression_type": type(raw_target).__name__,
                            "target_expression_redaction_reasons": redactions,
                            "invoke_shape": f"invoke.{target_key}",
                        }
                    )
                    for nested_key, nested in item.items():
                        if nested_key != target_key:
                            walk(nested, f"{child}/{_escape_pointer(nested_key)}", scope)
                else:
                    walk(item, child, scope)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{pointer}/{index}", scope)

    walk(document, "", None)
    observations.sort(key=lambda item: item["source_pointer"])
    return observations


class ResolutionCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS cache_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS parsed_sources (source_path TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, parser_version TEXT NOT NULL, observations_json TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS resolved_apis (canonical_api_id TEXT PRIMARY KEY, source_path TEXT NOT NULL, source_sha256 TEXT NOT NULL, parser_version TEXT NOT NULL, property_sha256 TEXT NOT NULL, records_json TEXT NOT NULL)"
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO cache_metadata(key,value) VALUES('cache_schema_version',?)",
            (CACHE_SCHEMA_VERSION,),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def parsed(self, source_path: str, source_sha: str) -> list[dict[str, Any]] | None:
        row = self.connection.execute(
            "SELECT observations_json FROM parsed_sources WHERE source_path=? AND source_sha256=? AND parser_version=?",
            (source_path, source_sha, PARSER_VERSION),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put_parsed(self, source_path: str, source_sha: str, observations: list[dict[str, Any]]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO parsed_sources VALUES(?,?,?,?)",
            (source_path, source_sha, PARSER_VERSION, json.dumps(observations, sort_keys=True, separators=(",", ":"))),
        )

    def resolved(self, api_id: str, source_path: str, source_sha: str, property_sha: str) -> list[dict[str, Any]] | None:
        row = self.connection.execute(
            "SELECT records_json FROM resolved_apis WHERE canonical_api_id=? AND source_path=? AND source_sha256=? AND parser_version=? AND property_sha256=?",
            (api_id, source_path, source_sha, PARSER_VERSION, property_sha),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put_resolved(self, api_id: str, source_path: str, source_sha: str, property_sha: str, records: list[dict[str, Any]]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO resolved_apis VALUES(?,?,?,?,?,?)",
            (api_id, source_path, source_sha, PARSER_VERSION, property_sha, json.dumps(records, sort_keys=True, separators=(",", ":"))),
        )

    def commit(self) -> None:
        self.connection.commit()


def _api_source(api: dict[str, Any], root: Path) -> Path | None:
    candidates = sorted(
        {
            item["source_relative_path"]
            for item in api.get("source_evidence", [])
            if item.get("source_relative_path", "").startswith("staging/apis/")
            and item["source_relative_path"].endswith((".yaml", ".yml"))
        }
    )
    existing = [root / item for item in candidates if (root / item).is_file()]
    if not existing:
        return None
    if len(existing) != 1:
        raise ValueError(
            f"canonical API {api['canonical_identity_record_id']} requires exactly one accepted API YAML source; found {len(existing)}"
        )
    return existing[0]


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_api(
    api: dict[str, Any],
    source_relative_path: str,
    source_sha: str,
    observations: list[dict[str, Any]],
    property_lookup: dict[str, list[dict[str, Any]]],
    property_sha: str,
) -> list[dict[str, Any]]:
    records = []
    for observation in observations:
        resolved = resolve_target_expression(
            observation["safe_target_expression"], property_lookup
        )
        resolved["target_expression_redaction_reasons"] = sorted(
            set(resolved["target_expression_redaction_reasons"])
            | set(observation["target_expression_redaction_reasons"])
        )
        observation_id = _stable_id(
            "backend-target-observation",
            api["canonical_identity_record_id"],
            source_relative_path,
            observation["source_pointer"],
        )
        records.append(
            {
                "target_observation_id": observation_id,
                "canonical_api_id": api["canonical_identity_record_id"],
                "api_name": api.get("name"),
                "api_version": api.get("version"),
                "source_path": source_relative_path,
                "source_pointer": observation["source_pointer"],
                "operation_scope": observation["operation_scope"],
                "scope_classification": "OPERATION_SCOPED" if observation["operation_scope"] else "API_SHARED",
                "invocation_mechanism": observation["invocation_mechanism"],
                "invoke_shape": observation["invoke_shape"],
                "invoke_title": observation["invoke_title"],
                "http_verb": observation["http_verb"],
                "backend_type": observation["backend_type"],
                **resolved,
                "evidence_state": "EXPLICIT_CONFIGURATION_EVIDENCE",
                "confidence": "HIGH",
                "source_sha256": source_sha,
                "catalog_property_file_sha256": property_sha,
                "cache_fingerprint": {
                    "parser_version": PARSER_VERSION,
                    "source_sha256": source_sha,
                    "catalog_property_file_sha256": property_sha,
                },
            }
        )
    return records


def build_resolution_indexes(
    root: Path,
    *,
    phase2_path: Path | None = None,
    properties_path: Path | None = None,
    property_index_path: Path | None = None,
    target_index_path: Path | None = None,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    phase2_path = phase2_path or root / "indexes/apic_identity_resolution.json"
    properties_path = properties_path or root / "staging/config/catalog-properties.json"
    property_index_path = property_index_path or root / PROPERTY_INDEX_PATH
    target_index_path = target_index_path or root / TARGET_INDEX_PATH
    cache_path = cache_path or root / CACHE_PATH
    property_started = time.perf_counter()
    try:
        property_source_label = properties_path.relative_to(root).as_posix()
    except ValueError:
        property_source_label = properties_path.as_posix()
    property_records, property_lookup, property_summary = index_catalog_properties(
        properties_path, source_label=property_source_label
    )
    property_parse_seconds = time.perf_counter() - property_started
    _write_jsonl(property_index_path, property_records)
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    apis = sorted(
        (
            item
            for item in phase2["canonical_identity_records"]
            if item["canonical_object_type"] == "api_artifact"
        ),
        key=lambda item: item["canonical_identity_record_id"],
    )
    property_sha = property_summary["source_file_sha256"]
    cache = ResolutionCache(cache_path)
    records: list[dict[str, Any]] = []
    stats = Counter()
    try:
        for api in apis:
            source = _api_source(api, root)
            if source is None:
                stats["apis_without_accepted_yaml_source"] += 1
                continue
            relative = source.relative_to(root).as_posix()
            source_sha = _sha256_file(source)
            cached_records = cache.resolved(
                api["canonical_identity_record_id"], relative, source_sha, property_sha
            )
            if cached_records is not None:
                stats["resolution_cache_hits"] += 1
                records.extend(cached_records)
                continue
            stats["resolution_cache_misses"] += 1
            observations = cache.parsed(relative, source_sha)
            if observations is None:
                stats["files_parsed"] += 1
                document = yaml.load(source.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
                observations = extract_target_observations(document)
                cache.put_parsed(relative, source_sha, observations)
            else:
                stats["parsed_source_cache_hits"] += 1
            api_records = _resolve_api(
                api, relative, source_sha, observations, property_lookup, property_sha
            )
            cache.put_resolved(
                api["canonical_identity_record_id"], relative, source_sha, property_sha, api_records
            )
            records.extend(api_records)
        cache.commit()
    finally:
        cache.close()
    records.sort(key=lambda item: item["target_observation_id"])
    _write_jsonl(target_index_path, records)
    apis_with_observations = {item["canonical_api_id"] for item in records}
    api_observation_counts = Counter(item["canonical_api_id"] for item in records)
    classification_counts = Counter(item["target_classification"] for item in records)
    status_counts = Counter(item["resolution_status"] for item in records)
    reason_counts = Counter(item["resolution_reason"] for item in records)
    property_referenced = [item for item in records if item["symbolic_property_tokens"]]
    lookup_statuses = {
        item["target_observation_id"]: {
            lookup["lookup_status"] for lookup in item["property_lookup_results"]
        }
        for item in records
    }
    result = {
        "property_summary": property_summary,
        "target_summary": {
            "total_canonical_apis": len(apis),
            "apis_inspected": len(apis),
            "apis_served_entirely_from_resolution_cache": stats["resolution_cache_hits"],
            "apis_requiring_resolution": stats["resolution_cache_misses"],
            "apis_without_accepted_yaml_source": stats["apis_without_accepted_yaml_source"],
            "apis_with_target_observations": len(apis_with_observations),
            "apis_with_no_explicit_target_observation": len(apis) - len(apis_with_observations),
            "total_target_observations": len(records),
            "property_referenced_observations": len(property_referenced),
            "fully_property_resolved_observations": classification_counts["CATALOG_PROPERTY_RESOLVED"],
            "missing_property_observations": sum("MISSING" in value for value in lookup_statuses.values()),
            "ambiguous_property_observations": sum("AMBIGUOUS" in value for value in lookup_statuses.values()),
            "protected_property_observations": sum("PROTECTED_OR_REDACTED" in value for value in lookup_statuses.values()),
            "runtime_parameterized_observations": sum(
                bool(item["runtime_parameter_tokens"])
                or item["target_classification"] == "RUNTIME_PARAMETERIZED"
                for item in records
            ),
            "static_literal_observations": classification_counts["STATIC_LITERAL"],
            "apis_with_multiple_target_observations": sum(value > 1 for value in api_observation_counts.values()),
            "api_shared_observations": sum(item["scope_classification"] == "API_SHARED" for item in records),
            "operation_scoped_observations": sum(item["scope_classification"] == "OPERATION_SCOPED" for item in records),
            "target_classification_counts": dict(sorted(classification_counts.items())),
            "resolution_status_counts": dict(sorted(status_counts.items())),
            "resolution_reason_counts": dict(sorted(reason_counts.items())),
        },
        "pattern_inventory": {
            "invoke_shape_counts": dict(sorted(Counter(item["invoke_shape"] for item in records).items())),
            "target_value_shape_counts": dict(sorted(classification_counts.items())),
            "scope_counts": dict(sorted(Counter(item["scope_classification"] for item in records).items())),
            "symbolic_token_count_per_observation": dict(sorted(Counter(str(len(item["symbolic_property_tokens"])) for item in records).items())),
            "backend_type_presence": dict(sorted(Counter("present" if item["backend_type"] is not None else "absent" for item in records).items())),
            "http_verb_presence": dict(sorted(Counter("present" if item["http_verb"] is not None else "absent" for item in records).items())),
        },
        "cache": {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "parser_version": PARSER_VERSION,
            "cache_path": _display_path(cache_path, root),
            "property_file_parse_seconds": round(property_parse_seconds, 6),
            "build_seconds": round(time.perf_counter() - started, 6),
            "files_parsed": stats["files_parsed"],
            "parsed_source_cache_hits": stats["parsed_source_cache_hits"],
            "resolution_cache_hits": stats["resolution_cache_hits"],
            "resolution_cache_misses": stats["resolution_cache_misses"],
        },
        "output": {
            "property_index_path": _display_path(property_index_path, root),
            "property_index_sha256": _sha256_file(property_index_path),
            "target_index_path": _display_path(target_index_path, root),
            "target_index_sha256": _sha256_file(target_index_path),
        },
        "records": records,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--phase2", type=Path)
    parser.add_argument("--properties", type=Path)
    parser.add_argument("--property-index", type=Path)
    parser.add_argument("--target-index", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = build_resolution_indexes(
        root,
        phase2_path=args.phase2,
        properties_path=args.properties,
        property_index_path=args.property_index,
        target_index_path=args.target_index,
        cache_path=args.cache,
    )
    result.pop("records")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
