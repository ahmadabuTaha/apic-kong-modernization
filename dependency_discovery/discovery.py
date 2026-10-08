"""Evidence-driven dependency discovery without canonical graph mutation."""

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


PARSER_VERSION = "phase4-dependency-parser-v2"
CACHE_SCHEMA_VERSION = "phase4-dependency-cache-v1"
DEPENDENCY_INDEX_PATH = Path("indexes/api_dependency_observations.jsonl")
PATTERN_INDEX_PATH = Path("indexes/dependency_pattern_inventory.json")
CACHE_PATH = Path("indexes/cache/phase4_dependency_discovery_cache.sqlite3")
TOKEN_PATTERN = re.compile(r"\$\(([^()]+)\)")
RUNTIME_PATTERN = re.compile(r"\$\{[^{}]+\}|\{\{[^{}]+\}\}")
SECRET_QUERY_PATTERN = re.compile(
    r"(?:password|passwd|secret|token|api[-_]?key|access[-_]?key|client[-_]?secret)",
    re.IGNORECASE,
)
RUNTIME_PREFIXES = ("request.", "message.", "api.", "context.", "env.", "session.")
SECURITY_ENDPOINT_FIELDS = {
    "tokenUrl": "TOKEN_ENDPOINT",
    "authorizationUrl": "AUTHORIZATION_ENDPOINT",
    "openIdConnectUrl": "OPENID_CONNECT_DISCOVERY_ENDPOINT",
    "introspectionUrl": "INTROSPECTION_ENDPOINT",
    "introspectionEndpoint": "INTROSPECTION_ENDPOINT",
    "jwksUri": "JWKS_ENDPOINT",
    "jwks_uri": "JWKS_ENDPOINT",
    "issuer": "ISSUER_REFERENCE",
}


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode()
    return f"{prefix}:sha256:{_hash_bytes(encoded)}"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for item in values
        ),
        encoding="utf-8",
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _escape(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _sanitize(value: Any) -> tuple[str | None, list[str]]:
    if not isinstance(value, str):
        return None, ["non_string_value_not_exposed"]
    text = value.strip()
    reasons: list[str] = []
    try:
        parsed = urlsplit(text)
    except ValueError:
        return "[REDACTED_UNSAFE_VALUE]", ["invalid_url_structure"]
    if parsed.scheme and (parsed.username is not None or parsed.password is not None):
        host = parsed.hostname or ""
        try:
            if parsed.port:
                host += f":{parsed.port}"
        except ValueError:
            pass
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


def _tokens(value: str | None) -> list[str]:
    return sorted(set(TOKEN_PATTERN.findall(value or "")))


def _runtime_token(value: str) -> bool:
    folded = value.casefold()
    return any(folded.startswith(prefix) for prefix in RUNTIME_PREFIXES)


def _normalized_endpoint_key(value: str | None) -> str | None:
    if not value or "$" in value or "{{" in value:
        return None
    try:
        parsed = urlsplit(value if "://" in value else f"//{value}")
        host = (parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError:
        return None
    if not host:
        return None
    material = f"{parsed.scheme.casefold()}|{host}|{port or ''}|{parsed.path or '/'}"
    return f"endpoint-key:sha256:{_hash_bytes(material.encode())}"


def _property_lookup(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        name = record.get("exact_property_name")
        if name:
            result[name].append(record)
    return dict(result)


def _resolve_reference(
    value: str | None, lookup: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    safe, redactions = _sanitize(value)
    tokens = _tokens(safe)
    context_tokens = [token for token in tokens if _runtime_token(token)]
    property_tokens = [token for token in tokens if token not in context_tokens]
    resolved = safe
    lookups = []
    for token in property_tokens:
        records = lookup.get(token, [])
        ids = sorted(item["catalog_property_record_id"] for item in records)
        safe_values = {item.get("safe_value") for item in records if item.get("safe_value") is not None}
        cardinalities = {item.get("lookup_cardinality") for item in records}
        if not records:
            status, reason, replacement = "MISSING", "unresolved_due_to_missing_catalog_property", None
        elif "conflicting_multiple_values" in cardinalities or len(safe_values) > 1:
            status, reason, replacement = "AMBIGUOUS", "ambiguous_due_to_conflicting_catalog_property_values", None
        elif len(safe_values) == 1 and all(item.get("safe_value") is not None for item in records):
            status, reason, replacement = "RESOLVED", "exact_catalog_property_match", next(iter(safe_values))
            resolved = (resolved or "").replace(f"$({token})", replacement)
        else:
            status, reason, replacement = "PROTECTED_OR_REDACTED", "unresolved_due_to_protected_catalog_property_value", None
        lookups.append(
            {
                "token": token,
                "lookup_status": status,
                "reason": reason,
                "catalog_property_record_ids": ids,
            }
        )
    statuses = {item["lookup_status"] for item in lookups}
    has_runtime = bool(context_tokens or (safe and RUNTIME_PATTERN.search(safe)))
    if "AMBIGUOUS" in statuses:
        resolution_status, reason, resolved_value = "AMBIGUOUS", "ambiguous_security_or_endpoint_configuration", None
    elif statuses & {"MISSING", "PROTECTED_OR_REDACTED"} or has_runtime:
        resolution_status, reason, resolved_value = "UNRESOLVED", "unresolved_or_parameterized_dependency_reference", None
    else:
        resolution_status, reason, resolved_value = "RESOLVED", "explicit_reference_resolved", resolved
    return {
        "safe_raw_reference": safe,
        "resolved_safe_endpoint_or_target": resolved_value,
        "referenced_catalog_properties": property_tokens,
        "referenced_context_tokens": context_tokens,
        "property_lookup_results": lookups,
        "resolution_status": resolution_status,
        "resolution_reason": reason,
        "redaction_reasons": redactions,
        "normalized_endpoint_key": _normalized_endpoint_key(resolved_value),
    }


def _pattern(
    path_pattern: str,
    mechanism: str,
    observation_class: str,
    support: str,
    source_pointer: str,
) -> dict[str, Any]:
    return {
        "path_pattern": re.sub(r"/\d+(?=/|$)", "/*", path_pattern),
        "mechanism_name": mechanism,
        "observation_class": observation_class,
        "parser_support_status": support,
        "source_pointer": source_pointer,
    }


def extract_dependency_candidates(document: Any) -> dict[str, list[dict[str, Any]]]:
    """Extract only observed security/provider and non-invoke endpoint contexts."""

    candidates: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []

    def add_candidate(
        *,
        pointer: str,
        path_pattern: str,
        mechanism: str,
        observation_class: str,
        role: str,
        value: Any,
        scheme_name: str | None = None,
        reason: str | None = None,
    ) -> None:
        safe, redactions = _sanitize(value)
        candidates.append(
            {
                "source_pointer": pointer,
                "path_pattern": path_pattern,
                "mechanism_name": mechanism,
                "observation_class": observation_class,
                "dependency_role": role,
                "scheme_or_provider_name": scheme_name,
                "safe_value": safe,
                "redaction_reasons": redactions,
                "unclassified_reason": reason,
            }
        )
        patterns.append(_pattern(path_pattern, mechanism, observation_class, "SUPPORTED", pointer))

    def security_scheme(
        name: str, scheme: Any, pointer: str, pattern_root: str
    ) -> None:
        if not isinstance(scheme, dict):
            patterns.append(_pattern(pattern_root, "security-scheme", "UNCLASSIFIED_DEPENDENCY_PATTERN", "UNSUPPORTED_SHAPE", pointer))
            add_candidate(
                pointer=pointer,
                path_pattern=pattern_root,
                mechanism="security-scheme",
                observation_class="UNCLASSIFIED_DEPENDENCY_PATTERN",
                role="UNSUPPORTED_SECURITY_SCHEME",
                value=None,
                scheme_name=name,
                reason="unclassified_due_to_unsupported_security_scheme_shape",
            )
            return
        scheme_type = str(scheme.get("type", "")).casefold()
        oauth_like = scheme_type in {"oauth2", "openidconnect"} or any(
            key in scheme for key in ("flows", "tokenUrl", "authorizationUrl", "openIdConnectUrl")
        )
        if not oauth_like:
            patterns.append(_pattern(pattern_root, scheme_type or "security-scheme", "UNCLASSIFIED_DEPENDENCY_PATTERN", "NON_DEPENDENCY_SECURITY_SCHEME", pointer))
            return
        provider = scheme.get("x-ibm-oauth-provider") or name
        provider_role = "OIDC_PROVIDER_REFERENCE" if scheme_type == "openidconnect" else "OAUTH2_PROVIDER_REFERENCE"
        add_candidate(
            pointer=pointer,
            path_pattern=pattern_root,
            mechanism=scheme_type or "oauth2",
            observation_class="SECURITY_PROVIDER",
            role=provider_role,
            value=provider,
            scheme_name=name,
        )

        def endpoints(value: Any, current: str, pattern: str) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    child = f"{current}/{_escape(key)}"
                    child_pattern = f"{pattern}/{_escape(key)}"
                    if key in SECURITY_ENDPOINT_FIELDS:
                        add_candidate(
                            pointer=child,
                            path_pattern=child_pattern,
                            mechanism=scheme_type or "oauth2",
                            observation_class="SECURITY_PROVIDER",
                            role=SECURITY_ENDPOINT_FIELDS[key],
                            value=item,
                            scheme_name=name,
                        )
                    else:
                        endpoints(item, child, child_pattern)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    endpoints(item, f"{current}/{index}", f"{pattern}/*")

        endpoints(scheme, pointer, pattern_root)

    def walk(value: Any, pointer: str = "", scope: list[dict[str, Any]] | None = None) -> None:
        if isinstance(value, dict):
            if "operations" in value and "execute" in value:
                scopes = []
                if isinstance(value["operations"], list):
                    for item in value["operations"]:
                        if isinstance(item, dict):
                            scopes.append({"method": item.get("verb"), "path": item.get("path")})
                walk(value["execute"], f"{pointer}/execute", scopes or scope)
                for key, item in value.items():
                    if key not in {"operations", "execute"}:
                        walk(item, f"{pointer}/{_escape(key)}", scope)
                return
            for key, item in value.items():
                child = f"{pointer}/{_escape(key)}"
                if key in {"securityDefinitions", "securitySchemes"} and isinstance(item, dict):
                    base_pattern = f"{child}/*"
                    for name, scheme in sorted(item.items(), key=lambda pair: str(pair[0])):
                        security_scheme(str(name), scheme, f"{child}/{_escape(name)}", base_pattern)
                    continue
                if key in {"jwt-validate", "validate-jwt"} and isinstance(item, dict):
                    jwk_key = next((field for field in ("jws-jwk", "jwks", "jwks-uri", "jwksUri") if field in item), None)
                    if jwk_key:
                        add_candidate(
                            pointer=f"{child}/{_escape(jwk_key)}",
                            path_pattern=f"{child}/{_escape(jwk_key)}",
                            mechanism=key,
                            observation_class="UNCLASSIFIED_DEPENDENCY_PATTERN",
                            role="JWK_CONFIGURATION",
                            value=None,
                            reason="unclassified_due_to_unsupported_security_scheme_shape",
                        )
                if isinstance(item, list) and key in {"execute", "catch"}:
                    for index, wrapper in enumerate(item):
                        if isinstance(wrapper, dict):
                            for policy, body in wrapper.items():
                                if policy != "invoke" and isinstance(body, dict) and isinstance(body.get("target-url"), str):
                                    add_candidate(
                                        pointer=f"{child}/{index}/{_escape(policy)}/target-url",
                                        path_pattern=f"{child}/*/{_escape(policy)}/target-url",
                                        mechanism=policy,
                                        observation_class="EXTERNAL_HTTP_DEPENDENCY",
                                        role="POLICY_HTTP_ENDPOINT",
                                        value=body["target-url"],
                                        reason="ownership_validation_required",
                                    )
                walk(item, child, scope)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{pointer}/{index}", scope)

    walk(document)
    candidates.sort(key=lambda item: (item["source_pointer"], item["dependency_role"], item.get("scheme_or_provider_name") or ""))
    patterns.sort(key=lambda item: (item["path_pattern"], item["mechanism_name"], item["source_pointer"]))
    return {"candidates": candidates, "patterns": patterns}


class DependencyCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS parsed_sources (source_path TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, parser_version TEXT NOT NULL, candidates_json TEXT NOT NULL, patterns_json TEXT NOT NULL)"
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO metadata VALUES('cache_schema_version',?)", (CACHE_SCHEMA_VERSION,)
        )
        self.connection.commit()

    def get(self, path: str, sha: str) -> dict[str, list[dict[str, Any]]] | None:
        row = self.connection.execute(
            "SELECT candidates_json,patterns_json FROM parsed_sources WHERE source_path=? AND source_sha256=? AND parser_version=?",
            (path, sha, PARSER_VERSION),
        ).fetchone()
        return {"candidates": json.loads(row[0]), "patterns": json.loads(row[1])} if row else None

    def put(self, path: str, sha: str, parsed: dict[str, list[dict[str, Any]]]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO parsed_sources VALUES(?,?,?,?,?)",
            (
                path,
                sha,
                PARSER_VERSION,
                json.dumps(parsed["candidates"], sort_keys=True, separators=(",", ":")),
                json.dumps(parsed["patterns"], sort_keys=True, separators=(",", ":")),
            ),
        )

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()


def _source_for_api(api: dict[str, Any], root: Path) -> Path | None:
    candidates = sorted(
        {
            item["source_relative_path"]
            for item in api.get("source_evidence", [])
            if item.get("source_relative_path", "").startswith("staging/apis/")
            and item["source_relative_path"].endswith((".yaml", ".yml"))
            and (root / item["source_relative_path"]).is_file()
        }
    )
    if not candidates:
        return None
    if len(candidates) != 1:
        raise ValueError(f"API {api['canonical_identity_record_id']} has multiple accepted YAML sources")
    return root / candidates[0]


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _scope_fields(operation_scope: Any) -> tuple[str, str | None, str | None]:
    if isinstance(operation_scope, list) and len(operation_scope) == 1:
        item = operation_scope[0]
        return "OPERATION_SCOPED", item.get("verb") or item.get("method"), item.get("path")
    if operation_scope:
        return "OPERATION_SCOPED", None, None
    return "API_SHARED", None, None


def _base_record(
    api: dict[str, Any],
    *,
    observation_id: str,
    observation_class: str,
    mechanism: str,
    role: str,
    scope: str,
    method: str | None,
    path: str | None,
    source_path: str,
    source_pointer: str,
    source_sha: str,
    origin_id: str | None,
    parser_origin: str,
) -> dict[str, Any]:
    return {
        "dependency_observation_id": observation_id,
        "canonical_api_id": api["canonical_identity_record_id"],
        "api_name": api.get("name"),
        "api_version": api.get("version"),
        "scope_classification": scope,
        "operation_method": method,
        "operation_path": path,
        "observation_class": observation_class,
        "mechanism_or_policy_name": mechanism,
        "dependency_role": role,
        "source_path": source_path,
        "source_pointer": source_pointer,
        "source_sha256": source_sha,
        "originating_accepted_index_record_id": origin_id,
        "parser_origin": parser_origin,
        "evidence_state": "EXPLICIT_CONFIGURATION_EVIDENCE",
        "confidence": "HIGH",
    }


def _backend_records(
    task011: list[dict[str, Any]], identities: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []
    for item in task011:
        api = identities[item["canonical_api_id"]]
        scope, method, path = _scope_fields(item.get("operation_scope"))
        observation_id = _stable_id("api-dependency", "task011", item["target_observation_id"], "backend")
        record = _base_record(
            api,
            observation_id=observation_id,
            observation_class="BACKEND_INVOCATION",
            mechanism=item["invocation_mechanism"],
            role="BACKEND_TARGET",
            scope=scope,
            method=method,
            path=path,
            source_path=item["source_path"],
            source_pointer=item["source_pointer"],
            source_sha=item["source_sha256"],
            origin_id=item["target_observation_id"],
            parser_origin="TASK_011_REUSE",
        )
        record.update(
            {
                "safe_raw_expression_or_value_reference": item["original_safe_target_expression"],
                "resolved_safe_endpoint_or_target": item["resolved_safe_target_expression"],
                "referenced_catalog_properties": [
                    token for token in item["symbolic_property_tokens"] if token not in item.get("runtime_parameter_tokens", [])
                ],
                "referenced_context_tokens": item.get("runtime_parameter_tokens", []),
                "resolution_status": item["resolution_status"],
                "resolution_reason": item["resolution_reason"],
                "normalized_endpoint_key": _normalized_endpoint_key(item["resolved_safe_target_expression"]),
                "ownership_state": None,
            }
        )
        records.append(record)
        patterns.append(
            {
                **_pattern(
                    re.sub(r"/\d+(?=/|$)", "/*", item["source_pointer"]),
                    item["invocation_mechanism"],
                    "BACKEND_INVOCATION",
                    "REUSED_TASK_011",
                    item["source_pointer"],
                ),
                "canonical_api_id": item["canonical_api_id"],
                "resolution_status": item["resolution_status"],
                "parser_origin": "TASK_011_REUSE",
            }
        )
        lookup_by_token = {
            lookup["symbolic_property_name"]: lookup for lookup in item.get("property_lookup_results", [])
        }
        for token in item["symbolic_property_tokens"]:
            runtime = token in item.get("runtime_parameter_tokens", [])
            lookup = lookup_by_token.get(token)
            config_status = "UNRESOLVED" if runtime else (lookup or {}).get("lookup_status", "UNRESOLVED")
            config_reason = "runtime_context_reference" if runtime else (lookup or {}).get("reason", "unresolved_configuration_reference")
            config_id = _stable_id("api-dependency", "task011", item["target_observation_id"], "configuration", token)
            config = _base_record(
                api,
                observation_id=config_id,
                observation_class="CONFIGURATION_REFERENCE",
                mechanism="invoke.target-url",
                role="RUNTIME_CONTEXT_REFERENCE" if runtime else "CATALOG_PROPERTY_REFERENCE",
                scope=scope,
                method=method,
                path=path,
                source_path=item["source_path"],
                source_pointer=item["source_pointer"],
                source_sha=item["source_sha256"],
                origin_id=item["target_observation_id"],
                parser_origin="TASK_011_REUSE",
            )
            config.update(
                {
                    "safe_raw_expression_or_value_reference": token,
                    "resolved_safe_endpoint_or_target": None,
                    "referenced_catalog_properties": [] if runtime else [token],
                    "referenced_context_tokens": [token] if runtime else [],
                    "resolution_status": "RESOLVED" if config_status == "RESOLVED" else ("AMBIGUOUS" if config_status == "AMBIGUOUS" else "UNRESOLVED"),
                    "resolution_reason": config_reason,
                    "normalized_endpoint_key": None,
                    "ownership_state": None,
                }
            )
            records.append(config)
    return records, patterns


def _aggregate_patterns(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in events:
        key = (
            item["path_pattern"],
            item["mechanism_name"],
            item["observation_class"],
            item["parser_support_status"],
            item.get("parser_origin", "TASK_012_PARSED"),
        )
        groups[key].append(item)
    result = []
    for key in sorted(groups):
        values = groups[key]
        api_ids = {item.get("canonical_api_id") for item in values if item.get("canonical_api_id")}
        result.append(
            {
                "exact_path_pattern": key[0],
                "mechanism_name": key[1],
                "observation_class": key[2],
                "parser_support_status": key[3],
                "parser_origin": key[4],
                "api_count": len(api_ids),
                "observation_count": len(values),
                "resolution_state_counts": dict(sorted(Counter(item.get("resolution_status", "NOT_APPLICABLE") for item in values).items())),
                "representative_source_pointers": sorted({item["source_pointer"] for item in values})[:3],
            }
        )
    return result


def build_dependency_indexes(
    root: Path,
    *,
    phase2_path: Path | None = None,
    task011_path: Path | None = None,
    property_index_path: Path | None = None,
    dependency_index_path: Path | None = None,
    pattern_index_path: Path | None = None,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    phase2_path = phase2_path or root / "indexes/apic_identity_resolution.json"
    task011_path = task011_path or root / "indexes/backend_target_resolution.jsonl"
    property_index_path = property_index_path or root / "indexes/catalog_properties.jsonl"
    dependency_index_path = dependency_index_path or root / DEPENDENCY_INDEX_PATH
    pattern_index_path = pattern_index_path or root / PATTERN_INDEX_PATH
    cache_path = cache_path or root / CACHE_PATH
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    apis = sorted(
        (item for item in phase2["canonical_identity_records"] if item["canonical_object_type"] == "api_artifact"),
        key=lambda item: item["canonical_identity_record_id"],
    )
    identities = {item["canonical_identity_record_id"]: item for item in apis}
    task011 = _load_jsonl(task011_path)
    properties = _load_jsonl(property_index_path)
    lookup = _property_lookup(properties)
    records, pattern_events = _backend_records(task011, identities)
    stats = Counter()
    cache = DependencyCache(cache_path)
    try:
        for api in apis:
            source = _source_for_api(api, root)
            if source is None:
                stats["apis_without_yaml"] += 1
                continue
            relative = source.relative_to(root).as_posix()
            source_sha = _hash_file(source)
            parsed = cache.get(relative, source_sha)
            if parsed is None:
                stats["cache_misses"] += 1
                stats["files_parsed"] += 1
                document = yaml.load(source.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
                parsed = extract_dependency_candidates(document)
                cache.put(relative, source_sha, parsed)
            else:
                stats["cache_hits"] += 1
            candidate_pattern_keys = {
                (
                    _pattern(
                        item["path_pattern"],
                        item["mechanism_name"],
                        item["observation_class"],
                        "SUPPORTED",
                        item["source_pointer"],
                    )["path_pattern"],
                    item["mechanism_name"],
                    item["observation_class"],
                    item["source_pointer"],
                )
                for item in parsed["candidates"]
            }
            for event in parsed["patterns"]:
                event_key = (
                    event["path_pattern"],
                    event["mechanism_name"],
                    event["observation_class"],
                    event["source_pointer"],
                )
                if event_key not in candidate_pattern_keys:
                    pattern_events.append(
                        {
                            **event,
                            "canonical_api_id": api["canonical_identity_record_id"],
                            "parser_origin": "TASK_012_PARSED",
                        }
                    )
            for candidate in parsed["candidates"]:
                resolved = _resolve_reference(candidate["safe_value"], lookup)
                if candidate["observation_class"] == "UNCLASSIFIED_DEPENDENCY_PATTERN":
                    resolved.update(
                        {
                            "resolution_status": "UNRESOLVED",
                            "resolution_reason": candidate["unclassified_reason"],
                            "resolved_safe_endpoint_or_target": None,
                            "normalized_endpoint_key": None,
                        }
                    )
                role = candidate["dependency_role"]
                observation_id = _stable_id(
                    "api-dependency",
                    api["canonical_identity_record_id"],
                    relative,
                    candidate["source_pointer"],
                    candidate["observation_class"],
                    role,
                )
                record = _base_record(
                    api,
                    observation_id=observation_id,
                    observation_class=candidate["observation_class"],
                    mechanism=candidate["mechanism_name"],
                    role=role,
                    scope="API_SHARED",
                    method=None,
                    path=None,
                    source_path=relative,
                    source_pointer=candidate["source_pointer"],
                    source_sha=source_sha,
                    origin_id=None,
                    parser_origin="TASK_012_PARSED",
                )
                record.update(
                    {
                        "scheme_or_provider_name": candidate["scheme_or_provider_name"],
                        "safe_raw_expression_or_value_reference": resolved["safe_raw_reference"],
                        "resolved_safe_endpoint_or_target": resolved["resolved_safe_endpoint_or_target"],
                        "referenced_catalog_properties": resolved["referenced_catalog_properties"],
                        "referenced_context_tokens": resolved["referenced_context_tokens"],
                        "property_lookup_results": resolved["property_lookup_results"],
                        "resolution_status": resolved["resolution_status"],
                        "resolution_reason": resolved["resolution_reason"],
                        "redaction_reasons": sorted(set(candidate["redaction_reasons"] + resolved["redaction_reasons"])),
                        "normalized_endpoint_key": resolved["normalized_endpoint_key"],
                        "ownership_state": "ownership_validation_required" if candidate["observation_class"] == "EXTERNAL_HTTP_DEPENDENCY" else None,
                    }
                )
                records.append(record)
                pattern_events.append(
                    {
                        **_pattern(
                            candidate["path_pattern"],
                            candidate["mechanism_name"],
                            candidate["observation_class"],
                            "SUPPORTED",
                            candidate["source_pointer"],
                        ),
                        "canonical_api_id": api["canonical_identity_record_id"],
                        "resolution_status": resolved["resolution_status"],
                        "parser_origin": "TASK_012_PARSED",
                    }
                )
                for token in resolved["referenced_catalog_properties"] + resolved["referenced_context_tokens"]:
                    runtime = token in resolved["referenced_context_tokens"]
                    lookup_result = next((item for item in resolved["property_lookup_results"] if item["token"] == token), None)
                    config_id = _stable_id("api-dependency", observation_id, "configuration", token)
                    config = _base_record(
                        api,
                        observation_id=config_id,
                        observation_class="CONFIGURATION_REFERENCE",
                        mechanism=candidate["mechanism_name"],
                        role="RUNTIME_CONTEXT_REFERENCE" if runtime else "CATALOG_PROPERTY_REFERENCE",
                        scope="API_SHARED",
                        method=None,
                        path=None,
                        source_path=relative,
                        source_pointer=candidate["source_pointer"],
                        source_sha=source_sha,
                        origin_id=observation_id,
                        parser_origin="TASK_012_PARSED",
                    )
                    status = "UNRESOLVED" if runtime else (lookup_result or {}).get("lookup_status", "UNRESOLVED")
                    config.update(
                        {
                            "safe_raw_expression_or_value_reference": token,
                            "resolved_safe_endpoint_or_target": None,
                            "referenced_catalog_properties": [] if runtime else [token],
                            "referenced_context_tokens": [token] if runtime else [],
                            "resolution_status": "RESOLVED" if status == "RESOLVED" else ("AMBIGUOUS" if status == "AMBIGUOUS" else "UNRESOLVED"),
                            "resolution_reason": "runtime_context_reference" if runtime else (lookup_result or {}).get("reason", "unresolved_configuration_reference"),
                            "normalized_endpoint_key": None,
                            "ownership_state": None,
                        }
                    )
                    records.append(config)
    finally:
        cache.close()

    unique = {item["dependency_observation_id"]: item for item in records}
    if len(unique) != len(records):
        raise ValueError("duplicate deterministic dependency observation ID")
    records = sorted(unique.values(), key=lambda item: item["dependency_observation_id"])
    inventory = _aggregate_patterns(pattern_events)
    _write_jsonl(dependency_index_path, records)
    _write_json(pattern_index_path, inventory)

    by_class = Counter(item["observation_class"] for item in records)
    api_classes: dict[str, set[str]] = defaultdict(set)
    for item in records:
        api_classes[item["canonical_api_id"]].add(item["observation_class"])
    security_apis = {item["canonical_api_id"] for item in records if item["observation_class"] == "SECURITY_PROVIDER"}
    external_apis = {item["canonical_api_id"] for item in records if item["observation_class"] == "EXTERNAL_HTTP_DEPENDENCY"}
    config_apis = {item["canonical_api_id"] for item in records if item["observation_class"] == "CONFIGURATION_REFERENCE"}
    backend_apis = {item["canonical_api_id"] for item in records if item["observation_class"] == "BACKEND_INVOCATION"}
    unresolved_reasons = Counter(
        item["resolution_reason"] for item in records if item["resolution_status"] != "RESOLVED"
    )

    provider_groups: dict[str, set[str]] = defaultdict(set)
    token_groups: dict[str, set[str]] = defaultdict(set)
    endpoint_groups: dict[str, set[str]] = defaultdict(set)
    for item in records:
        if item["observation_class"] == "SECURITY_PROVIDER" and item["dependency_role"].endswith("PROVIDER_REFERENCE"):
            provider_groups[item.get("safe_raw_expression_or_value_reference") or "[missing]"].add(item["canonical_api_id"])
        if item["observation_class"] == "CONFIGURATION_REFERENCE":
            token_groups[item["safe_raw_expression_or_value_reference"]].add(item["canonical_api_id"])
        if item.get("normalized_endpoint_key"):
            endpoint_groups[item["normalized_endpoint_key"]].add(item["canonical_api_id"])
    backend_counts = Counter(item["canonical_api_id"] for item in records if item["observation_class"] == "BACKEND_INVOCATION")
    correlation = {
        "distinct_security_provider_references": len(provider_groups),
        "security_provider_references_shared_by_multiple_apis": sum(len(value) > 1 for value in provider_groups.values()),
        "maximum_apis_sharing_one_security_provider_reference": max((len(value) for value in provider_groups.values()), default=0),
        "distinct_configuration_tokens": len(token_groups),
        "configuration_tokens_shared_by_multiple_apis": sum(len(value) > 1 for value in token_groups.values()),
        "maximum_apis_sharing_one_configuration_token": max((len(value) for value in token_groups.values()), default=0),
        "distinct_resolved_endpoint_keys": len(endpoint_groups),
        "resolved_endpoint_keys_shared_by_multiple_apis": sum(len(value) > 1 for value in endpoint_groups.values()),
        "maximum_apis_sharing_one_resolved_endpoint_key": max((len(value) for value in endpoint_groups.values()), default=0),
        "apis_with_backend_and_security_dependencies": len(backend_apis & security_apis),
        "apis_with_multiple_backend_targets": sum(value > 1 for value in backend_counts.values()),
        "apis_with_operation_scoped_dependencies": len({item["canonical_api_id"] for item in records if item["scope_classification"] == "OPERATION_SCOPED"}),
    }
    summary = {
        "total_canonical_apis": len(apis),
        "apis_accounted_for": len(apis),
        "apis_represented_by_task011_backend_observations": len(backend_apis),
        "apis_with_security_provider_observations": len(security_apis),
        "apis_with_external_http_dependency_observations": len(external_apis),
        "apis_with_configuration_reference_observations": len(config_apis),
        "apis_with_multiple_dependency_classes": sum(len(value) > 1 for value in api_classes.values()),
        "apis_with_no_supported_dependency_observation": len(apis) - len(api_classes),
        "operation_scoped_dependency_observations": sum(item["scope_classification"] == "OPERATION_SCOPED" for item in records),
        "api_shared_dependency_observations": sum(item["scope_classification"] == "API_SHARED" for item in records),
        "total_dependency_observations": len(records),
        "observation_counts_by_class": dict(sorted(by_class.items())),
        "unresolved_observation_counts_by_exact_reason": dict(sorted(unresolved_reasons.items())),
        "task011_backend_observations_loaded": len(task011),
        "task011_backend_yaml_reparse_count": 0,
        "apis_without_accepted_yaml_source": stats["apis_without_yaml"],
    }
    output = {
        "dependency_index_path": _display_path(dependency_index_path, root),
        "dependency_index_sha256": _hash_file(dependency_index_path),
        "pattern_index_path": _display_path(pattern_index_path, root),
        "pattern_index_sha256": _hash_file(pattern_index_path),
    }
    return {
        "summary": summary,
        "inventory": inventory,
        "correlation": correlation,
        "cache": {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "parser_version": PARSER_VERSION,
            "cache_path": _display_path(cache_path, root),
            "files_parsed": stats["files_parsed"],
            "cache_hits": stats["cache_hits"],
            "cache_misses": stats["cache_misses"],
            "build_seconds": round(time.perf_counter() - started, 6),
        },
        "output": output,
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--dependency-index", type=Path)
    parser.add_argument("--pattern-index", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = build_dependency_indexes(
        root,
        dependency_index_path=args.dependency_index,
        pattern_index_path=args.pattern_index,
        cache_path=args.cache,
    )
    result.pop("records")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
