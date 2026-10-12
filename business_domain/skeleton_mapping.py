"""Task 018B skeleton-first, operation-level candidate domain mapping.

This module consumes the frozen Task 014/015/017/017A indexes.  It does not
derive a taxonomy: the candidate labels are the eleven labels supplied by the
Enterprise Architect.  Assignments remain provisional and operation scoped.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


RULES_VERSION = "task018b-ea-skeleton-operation-mapping-v1"
STOP_GATE = "EA_REVIEW_BEFORE_DOMAIN_CHANGES_OR_TASK019"
SKELETON = (
    "Visa",
    "Establishment",
    "Contracts",
    "Nitaqat",
    "Payment",
    "Common",
    "User Management",
    "Work Permit",
    "Work Force",
    "Notification",
    "Certificate",
)
OUTPUTS = {
    "operations": Path("indexes/task018b_operation_domain_initial_mapping.jsonl"),
    "apis": Path("indexes/task018b_canonical_api_domain_footprint.jsonl"),
    "objects": Path("indexes/task018b_business_object_candidate_register.jsonl"),
    "manifest": Path("indexes/task018b_domain_skeleton_manifest.json"),
}

CLASSIFICATION_STATUSES = {
    "PRIMARY_CANDIDATE_PROVISIONAL",
    "UNRESOLVED_AMBIGUOUS",
    "UNRESOLVED_INSUFFICIENT_SEMANTICS",
    "TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY",
    "CONFLICTING_SOURCE_EVIDENCE",
}
EVIDENCE_ROLES = {
    "CORE_BUSINESS_OBJECT_CANDIDATE",
    "OBJECT_REFERENCE",
    "DTO_OR_TRANSPORT_MODEL",
    "LOOKUP_OR_VALUE_SET",
    "TECHNICAL_ENVELOPE",
    "BUSINESS_ACTION",
    "STATE_VALUE_CANDIDATE",
}


@dataclass(frozen=True)
class DomainRule:
    label: str
    pattern: re.Pattern[str]
    target_pattern: re.Pattern[str]


def _rx(value: str) -> re.Pattern[str]:
    return re.compile(value, re.I)


# Rules only map evidence to the supplied skeleton; they do not define the
# enterprise meaning, ownership, or boundary of a candidate.
DOMAIN_RULES = (
    DomainRule("Visa", _rx(r"\bvisas?\b"), _rx(r"\bvisas?\b")),
    DomainRule("Establishment", _rx(r"\bestablish(?:ment|ments|ing)?\b|commercial registration|\bcr (?:details|number|information)\b|\bbranches\b"), _rx(r"\bestablish(?:ment|ments|ing)?\b|commercial registration|\bcr (?:details|information)\b")),
    DomainRule("Contracts", _rx(r"\bcontracts?\b|contractual"), _rx(r"\bcontracts?\b|contractual")),
    DomainRule("Nitaqat", _rx(r"\bnitaq(?:at)?\b|saudization|tawteen|locali[sz]ation"), _rx(r"\bnitaq(?:at)?\b|saudization|tawteen|locali[sz]ation")),
    DomainRule("Payment", _rx(r"\bpayments?\b|\bbills?\b|sadad|wallet|cashout|refund|credit"), _rx(r"\bpayments?\b|\bbills?\b|sadad|wallet|cashout|refund|credit")),
    DomainRule("Common", _rx(r"\blookups?\b|reference data|value set|\bcountries\b|\bnationalit(?:y|ies)\b|\bmarital\b|\boccupations?\b|\bcategories\b"), _rx(r"\blookups?\b|reference data|value set|\bcountries\b|\bnationalit(?:y|ies)\b|\bmarital\b|\bcategories\b")),
    DomainRule("User Management", _rx(r"\busers?\b|user account|grant.?access|revoke.?access|\bpermissions?\b|\bprivileges?\b|authenticat|delegat"), _rx(r"\busers?\b|user account|grant.?access|revoke.?access|\bpermissions?\b|\bprivileges?\b|authenticat|delegat")),
    DomainRule("Work Permit", _rx(r"work.?permits?|special permits?|temporary permits?"), _rx(r"work.?permits?|special permits?|temporary permits?")),
    DomainRule("Work Force", _rx(r"\bemployees?\b|\blabou?rers?\b|\bworkers?\b|workforce|change sponsor|change occupation|employment status|salary|training|qualification|runaway"), _rx(r"\bemployees?\b|\blabou?rers?\b|\bworkers?\b|workforce|change sponsor|change occupation|employment status|salary|training|qualification|runaway")),
    DomainRule("Notification", _rx(r"\bnotifications?\b|\bsms\b|text message|e-?mail"), _rx(r"\bnotifications?\b|\bsms\b|text message|e-?mail")),
    DomainRule("Certificate", _rx(r"\bcertificates?\b|accreditation"), _rx(r"\bcertificates?\b|accreditation")),
)

SOURCE_WEIGHTS = {
    "DOCUMENTED_OBJECT": 5,
    "SOURCE_SUMMARY": 4,
    "SOURCE_DESCRIPTION": 4,
    "EXACT_PATH": 2,
    "OPERATION_ID": 2,
    "SOURCE_TAG": 2,
    "SCHEMA_REFERENCE": 1,
}
TECHNICAL = _rx(r"graphql|\bjwt\b|health.?check|cache.?management|rate.?limit|object storage|\bs3\b|streaming|technical utility")
TEST_IDENTITY = _rx(r"(?:^|[-_])(test|poc|mock)(?:$|[-_])")
TEST_CENTER = _rx(r"test.?cent(?:er|re)")
SENSITIVE_NAME = _rx(r"password|passwd|secret|authorization|access.?token|client.?secret|private.?key")
STATE_FIELD = _rx(r"status|state|stage|decision|result")
REFERENCE_FIELD = _rx(r"(?:^|_)(?:id|uuid|number|code)$|(?:Id|ID|Uuid|UUID|Number|Code)$")
TECHNICAL_SCHEMA = _rx(r"error|header|envelope|response.?model|request.?model|result.?model")
LOOKUP_SCHEMA = _rx(r"lookup|reference|value.?set|categor|country|nationalit|marital|occupation")
DOMAIN_OBJECT_SCHEMA = _rx(r"visa|establish|contract|nitaq|payment|bill|wallet|user|permit|employee|labou?r|worker|notification|certificate")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for v in values), encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    try:
        display = path.relative_to(root).as_posix()
    except ValueError:
        display = path.as_posix()
    result: dict[str, Any] = {"path": display, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None:
        result["record_count"] = count
    return result


def _schema_refs(operation: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    contract = operation.get("contract", {})
    for parameter in contract.get("parameters", []):
        refs.update(parameter.get("schema_refs", []))
    for item in contract.get("request", {}).get("content", []):
        refs.update(item.get("schema_refs", []))
    for response in contract.get("responses", []):
        refs.update(response.get("schema_refs", []))
        for item in response.get("content", []):
            refs.update(item.get("schema_refs", []))
    return sorted(ref for ref in refs if isinstance(ref, str))


def _evidence_fields(operation: dict[str, Any], observed: dict[str, Any]) -> list[tuple[str, str]]:
    facts = observed["source_facts"]
    function = observed["candidate_observed_function"]
    fields: list[tuple[str, str]] = []
    for source, value in (
        ("DOCUMENTED_OBJECT", function.get("business_object_or_resource_phrase")),
        ("SOURCE_SUMMARY", facts.get("summary")),
        ("SOURCE_DESCRIPTION", facts.get("description")),
        ("EXACT_PATH", operation.get("exact_path")),
        ("OPERATION_ID", facts.get("operation_id")),
    ):
        if isinstance(value, str) and value.strip():
            fields.append((source, value))
    fields.extend(("SOURCE_TAG", tag) for tag in facts.get("tags", []) if isinstance(tag, str) and tag.strip())
    fields.extend(("SCHEMA_REFERENCE", ref.rsplit("/", 1)[-1]) for ref in _schema_refs(operation))
    return fields


def _candidate_evidence(operation: dict[str, Any], observed: dict[str, Any]) -> list[dict[str, Any]]:
    fields = _evidence_fields(operation, observed)
    values = []
    for rule in DOMAIN_RULES:
        hits = []
        for source, text in fields:
            matches = sorted({match.group(0) for match in rule.pattern.finditer(text)}, key=str.lower)
            if matches:
                hits.append({"evidence_source": source, "matched_terms": matches, "weight": SOURCE_WEIGHTS[source]})
        if hits:
            target_sources = sorted({source for source, text in fields if source in {"DOCUMENTED_OBJECT", "SOURCE_SUMMARY", "SOURCE_DESCRIPTION"} and rule.target_pattern.search(text)})
            values.append({
                "candidate": rule.label,
                "score": sum(hit["weight"] for hit in hits),
                "evidence_hits": hits,
                "target_evidence_sources": target_sources,
            })
    return sorted(values, key=lambda value: (-value["score"], SKELETON.index(value["candidate"])))


def _reference_like(candidate: str, evidence: list[dict[str, Any]], primary: str | None) -> str | None:
    if candidate == "Establishment" and primary and primary != candidate:
        return "Establishment evidence may identify context/reference rather than the business object acted upon."
    if candidate == "Common" and primary and primary != candidate:
        return "Lookup/value wording may describe a referenced value set rather than primary business responsibility."
    if candidate == "User Management" and primary and primary != candidate:
        return "User/delegator wording may identify an actor or reference rather than the business object acted upon."
    sources = {hit["evidence_source"] for hit in evidence}
    if sources <= {"SCHEMA_REFERENCE"}:
        return "Schema-name evidence alone is insufficient for a primary assignment."
    return None


def _assessment(operation: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    candidates = _candidate_evidence(operation, observed)
    fields = _evidence_fields(operation, observed)
    combined = " ".join(text for _, text in fields)
    api_name = operation["current_api_name"]
    explicit_test = bool(TEST_IDENTITY.search(api_name)) and not TEST_CENTER.search(combined)
    technical = observed["candidate_observed_function"].get("operation_nature") == "TECHNICAL_OPERATION" or bool(TECHNICAL.search(combined))
    contradictory = bool(observed.get("contradictory_signals"))
    target_candidates = [value for value in candidates if value["target_evidence_sources"]]
    primary: str | None = None
    reason: str
    status: str
    certainty: str
    if contradictory:
        status, certainty, reason = "CONFLICTING_SOURCE_EVIDENCE", "CONFLICTING", "Task 015 retained contradictory operation evidence; no primary is forced."
    elif (explicit_test or technical) and not target_candidates:
        status, certainty, reason = "TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY", "NOT_APPLICABLE", "Technical/test/POC evidence is explicit and no skeleton business target is supported."
    elif not candidates:
        status, certainty, reason = "UNRESOLVED_INSUFFICIENT_SEMANTICS", "INSUFFICIENT", "No operation-level clue supports any of the eleven skeleton candidates."
    else:
        defensible = [value for value in candidates if any(hit["evidence_source"] != "SCHEMA_REFERENCE" for hit in value["evidence_hits"])]
        ranked_targets = sorted(target_candidates, key=lambda value: (-value["score"], SKELETON.index(value["candidate"])))
        if len(ranked_targets) == 1:
            primary = ranked_targets[0]["candidate"]
        elif len(ranked_targets) > 1 and ranked_targets[0]["score"] >= ranked_targets[1]["score"] + 4:
            primary = ranked_targets[0]["candidate"]
        elif not ranked_targets and len(defensible) == 1:
            primary = defensible[0]["candidate"]
        if primary:
            status = "PRIMARY_CANDIDATE_PROVISIONAL"
            certainty = "DIRECT" if observed["interpretation_status"] == "EXPLICITLY_DESCRIBED" and next(value for value in candidates if value["candidate"] == primary)["target_evidence_sources"] else "PROVISIONAL"
            reason = "Operation-level documented object/action or source metadata supports one provisional skeleton primary; enterprise alignment remains pending."
        else:
            status, certainty, reason = "UNRESOLVED_AMBIGUOUS", "AMBIGUOUS", "Operation evidence supports multiple skeleton candidates without a sufficiently dominant business target."
    alternatives = [value["candidate"] for value in candidates if value["candidate"] != primary]
    counterevidence = []
    for value in candidates:
        if value["candidate"] == primary:
            continue
        limitation = _reference_like(value["candidate"], value["evidence_hits"], primary)
        if limitation:
            counterevidence.append({"candidate": value["candidate"], "reason": limitation})
    review = []
    if status in {"UNRESOLVED_AMBIGUOUS", "CONFLICTING_SOURCE_EVIDENCE"}:
        review.append("EA_OR_BUSINESS_OWNER_BOUNDARY_REVIEW")
    if status == "UNRESOLVED_INSUFFICIENT_SEMANTICS":
        review.append("BUSINESS_PURPOSE_OR_ICD_EVIDENCE_REQUIRED")
    if primary in {"Common", "User Management", "Notification"} or any(value in {"Common", "User Management", "Notification"} for value in alternatives):
        review.append("BUSINESS_DOMAIN_VS_SHARED_OR_TECHNICAL_CAPABILITY_DECISION")
    if primary == "Certificate" or "Certificate" in alternatives:
        review.append("CERTIFICATE_INDEPENDENCE_AND_OWNERSHIP_REVIEW")
    return {
        "classification_status": status,
        "proposed_primary": primary,
        "alternative_candidates": alternatives,
        "certainty": certainty,
        "precise_reason": reason,
        "candidate_evidence": candidates,
        "contradicted_or_limiting_alternatives": counterevidence,
        "review_requirements": sorted(set(review)),
        "technical_or_test_evidence": explicit_test or technical,
        "domain_approved": False,
        "ownership_inferred": False,
    }


def _operation_rows(ledger: list[dict[str, Any]], observed_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    values = []
    for source in ledger:
        observed = observed_by_id[source["task015_observed_function_id"]]
        function = observed["candidate_observed_function"]
        values.append({
            "mapping_id": _stable_id("task018b-operation-domain-mapping", source["task014_operation_id"], RULES_VERSION),
            "task014_operation_id": source["task014_operation_id"],
            "task015_observed_function_id": source["task015_observed_function_id"],
            "canonical_api_id": source["canonical_api_id"],
            "current_api_name": source["current_api_name"],
            "current_api_version": source["current_api_version"],
            "method": source["method"],
            "exact_path": source["exact_path"],
            "source_provenance": source["source_provenance"],
            "documented_clues": {
                "action": function.get("action_verb"),
                "business_object_or_resource_phrase": function.get("business_object_or_resource_phrase"),
                "interpretation_status": observed["interpretation_status"],
                "evidence_strength": observed["evidence_strength"],
                "contradictory_signals": observed.get("contradictory_signals", []),
                "missing_information": observed.get("missing_information", []),
                "confidence_limitations": observed.get("confidence_limitations", []),
            },
            "domain_assessment": _assessment(source, observed),
            "classification_unit": "HTTP_OPERATION",
            "enterprise_alignment": "PENDING",
            "runtime_usage_inferred": False,
            "functional_duplicate_inferred": False,
            "product_or_plan_decision_inferred": False,
        })
    return sorted(values, key=lambda value: value["task014_operation_id"])


def _api_rows(apis: list[dict[str, Any]], operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[operation["canonical_api_id"]].append(operation)
    values = []
    for api in sorted(apis, key=lambda value: value["canonical_api_id"]):
        members = grouped.get(api["canonical_api_id"], [])
        primary = Counter(value["domain_assessment"]["proposed_primary"] for value in members if value["domain_assessment"]["proposed_primary"])
        alternatives = Counter(candidate for value in members for candidate in value["domain_assessment"]["alternative_candidates"])
        statuses = Counter(value["domain_assessment"]["classification_status"] for value in members)
        values.append({
            "footprint_id": _stable_id("task018b-api-domain-footprint", api["canonical_api_id"], RULES_VERSION),
            "canonical_api_id": api["canonical_api_id"],
            "identity_name": api["identity_name"],
            "identity_version": api["identity_version"],
            "protocol": api["protocol"],
            "accepted_source": api["accepted_source"],
            "accepted_operation_count": len(members),
            "source_inventory_operation_count": api["operation_count"],
            "operation_ids": sorted(value["task014_operation_id"] for value in members),
            "primary_candidate_operation_counts": {label: primary[label] for label in SKELETON if primary[label]},
            "alternative_candidate_operation_counts": {label: alternatives[label] for label in SKELETON if alternatives[label]},
            "classification_status_counts": dict(sorted(statuses.items())),
            "unresolved_operation_count": sum(status.startswith("UNRESOLVED") or status == "CONFLICTING_SOURCE_EVIDENCE" for status in (value["domain_assessment"]["classification_status"] for value in members)),
            "technical_or_test_operation_count": statuses["TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY"],
            "coverage_status": "ZERO_OPERATION_OR_UNSUPPORTED_VISIBLE" if not members else "OPERATION_LEDGER_ACCOUNTED",
            "whole_api_domain_assigned": False,
            "enterprise_alignment": "PENDING",
            "domain_approved": False,
        })
    return values


def _targeted_ids(operations: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    strata: list[tuple[str, list[str]]] = []
    strata.append(("CONFLICTING", [value["task014_operation_id"] for value in operations if value["domain_assessment"]["classification_status"] == "CONFLICTING_SOURCE_EVIDENCE"]))
    strata.append(("AMBIGUOUS", [value["task014_operation_id"] for value in operations if value["domain_assessment"]["classification_status"] == "UNRESOLVED_AMBIGUOUS"]))
    strata.append(("BOUNDARY_SENSITIVE", [value["task014_operation_id"] for value in operations if ({value["domain_assessment"]["proposed_primary"]} | set(value["domain_assessment"]["alternative_candidates"])) & {"Common", "User Management", "Notification", "Certificate"}]))
    strata.append(("INSUFFICIENT", [value["task014_operation_id"] for value in operations if value["domain_assessment"]["classification_status"] == "UNRESOLVED_INSUFFICIENT_SEMANTICS"]))
    chosen: list[str] = []
    reasons: dict[str, str] = {}
    for label, ids in strata:
        taken = 0
        for operation_id in sorted(ids):
            if operation_id in reasons:
                continue
            chosen.append(operation_id); reasons[operation_id] = label; taken += 1
            if taken == 40:
                break
    # Balance the three explicitly questioned shared/technical buckets and
    # Certificate, which the EA required to remain independently visible.
    for candidate in ("Common", "User Management", "Notification", "Certificate"):
        taken = 0
        for value in operations:
            assessment = value["domain_assessment"]
            if candidate not in ({assessment["proposed_primary"]} | set(assessment["alternative_candidates"])):
                continue
            operation_id = value["task014_operation_id"]
            if operation_id in reasons:
                continue
            chosen.append(operation_id); reasons[operation_id] = f"BOUNDARY_SENSITIVE_{candidate.upper().replace(' ', '_')}"; taken += 1
            if taken == 8:
                break
    return chosen, reasons


def _resolve_pointer(document: Any, pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise KeyError(pointer)
    value = document
    for token in pointer[2:].split("/"):
        value = value[token.replace("~1", "/").replace("~0", "~")]
    return value


def _schema_role(name: str, schema: dict[str, Any]) -> str:
    if TECHNICAL_SCHEMA.search(name):
        return "TECHNICAL_ENVELOPE"
    if LOOKUP_SCHEMA.search(name) or (isinstance(schema.get("enum"), list)):
        return "LOOKUP_OR_VALUE_SET"
    if DOMAIN_OBJECT_SCHEMA.search(name) and isinstance(schema.get("properties"), dict):
        return "CORE_BUSINESS_OBJECT_CANDIDATE"
    return "DTO_OR_TRANSPORT_MODEL"


def _local_refs(value: Any) -> list[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/"):
            refs.add(reference)
        for child in value.values():
            refs.update(_local_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_local_refs(child))
    return sorted(refs)


def _safe_enum(values: list[Any]) -> list[Any]:
    safe = []
    for value in values[:20]:
        if isinstance(value, (bool, int, float)) or value is None:
            safe.append(value)
        elif isinstance(value, str) and len(value) <= 80 and not SENSITIVE_NAME.search(value):
            safe.append(value)
    return safe


def _object_register(root: Path, selected: list[str], reasons: dict[str, str], operation_by_id: dict[str, dict[str, Any]], semantic_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    documents: dict[str, dict[str, Any]] = {}
    source_hash_mismatch = 0
    source_parse_errors = 0
    unresolved_refs = 0
    for operation_id in selected:
        mapping = operation_by_id[operation_id]
        semantic = semantic_by_id[operation_id]
        provenance = mapping["source_provenance"]
        source_path = root / provenance["source_path"]
        key = provenance["source_path"]
        try:
            actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if actual_hash != provenance["source_sha256"]:
                source_hash_mismatch += 1
                continue
            if key not in documents:
                loaded = yaml.safe_load(source_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("source document is not a mapping")
                documents[key] = loaded
            document = documents[key]
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            source_parse_errors += 1
            continue
        base = {
            "task014_operation_id": operation_id,
            "canonical_api_id": mapping["canonical_api_id"],
            "selection_reason": reasons[operation_id],
            "source_path": provenance["source_path"],
            "operation_source_pointer": provenance["source_pointer"],
            "source_sha256": provenance["source_sha256"],
            "domain_candidates": sorted(({mapping["domain_assessment"]["proposed_primary"]} if mapping["domain_assessment"]["proposed_primary"] else set()) | set(mapping["domain_assessment"]["alternative_candidates"]), key=SKELETON.index),
            "business_ownership_proven": False,
        }
        action = mapping["documented_clues"].get("action")
        if action:
            row = {**base, "evidence_role": "BUSINESS_ACTION", "schema_ref": None, "definition_pointer": provenance["source_pointer"], "evidence_name": action, "field_names": [], "state_values": [], "limitations": ["An operation action is not an end-to-end process or capability."]}
            row["object_evidence_id"] = _stable_id("task018b-object-evidence", operation_id, "BUSINESS_ACTION", action)
            rows.append(row)
        pending = list(_schema_refs(semantic))
        processed: set[str] = set()
        while pending:
            reference = pending.pop(0)
            if reference in processed:
                continue
            processed.add(reference)
            try:
                schema = _resolve_pointer(document, reference)
            except (KeyError, TypeError):
                unresolved_refs += 1
                continue
            if not isinstance(schema, dict):
                unresolved_refs += 1
                continue
            pending.extend(ref for ref in _local_refs(schema) if ref not in processed and ref not in pending)
            name = reference.rsplit("/", 1)[-1]
            properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
            safe_fields = sorted(field for field in properties if not SENSITIVE_NAME.search(field))[:30]
            role = _schema_role(name, schema)
            row = {**base, "evidence_role": role, "schema_ref": reference, "definition_pointer": reference[1:], "evidence_name": name, "field_names": safe_fields, "sensitive_field_name_count_omitted": sum(bool(SENSITIVE_NAME.search(field)) for field in properties), "state_values": [], "limitations": ["Schema naming and shape are evidence candidates, not proof of a business object, lifecycle, or owner."]}
            row["object_evidence_id"] = _stable_id("task018b-object-evidence", operation_id, role, reference)
            rows.append(row)
            top_enum = schema.get("enum")
            if isinstance(top_enum, list) and (STATE_FIELD.search(name) or role == "LOOKUP_OR_VALUE_SET"):
                enum_role = "STATE_VALUE_CANDIDATE" if STATE_FIELD.search(name) else "LOOKUP_OR_VALUE_SET"
                enum_row = {**base, "evidence_role": enum_role, "schema_ref": reference, "definition_pointer": reference[1:], "evidence_name": name, "field_names": [], "state_values": _safe_enum(top_enum), "state_value_count": len(top_enum), "limitations": ["Enum values are candidates only; no lifecycle, transition, shared owner, or domain boundary is inferred."]}
                enum_row["object_evidence_id"] = _stable_id("task018b-object-evidence", operation_id, enum_role, reference, "enum")
                rows.append(enum_row)
            for field in safe_fields:
                field_schema = properties[field]
                if not isinstance(field_schema, dict):
                    continue
                field_pointer = f"{reference}/properties/{field}"
                if REFERENCE_FIELD.search(field):
                    ref_row = {**base, "evidence_role": "OBJECT_REFERENCE", "schema_ref": reference, "definition_pointer": field_pointer[1:], "evidence_name": field, "field_names": [field], "state_values": [], "limitations": ["Identifier/reference evidence does not establish the primary object or domain owner."]}
                    ref_row["object_evidence_id"] = _stable_id("task018b-object-evidence", operation_id, "OBJECT_REFERENCE", field_pointer)
                    rows.append(ref_row)
                enum = field_schema.get("enum")
                if STATE_FIELD.search(field) and isinstance(enum, list):
                    state_row = {**base, "evidence_role": "STATE_VALUE_CANDIDATE", "schema_ref": reference, "definition_pointer": field_pointer[1:], "evidence_name": field, "field_names": [field], "state_values": _safe_enum(enum), "state_value_count": len(enum), "limitations": ["Enum values are state candidates only; no transition or lifecycle is inferred."]}
                    state_row["object_evidence_id"] = _stable_id("task018b-object-evidence", operation_id, "STATE_VALUE_CANDIDATE", field_pointer)
                    rows.append(state_row)
    rows.sort(key=lambda value: value["object_evidence_id"])
    return rows, {"selected_operation_count": len(selected), "source_document_count": len(documents), "source_hash_mismatch_count": source_hash_mismatch, "source_parse_error_count": source_parse_errors, "unresolved_local_schema_ref_count": unresolved_refs}


def build_skeleton_mapping(root: Path, *, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    root = root.resolve()
    paths = {name: (output_paths or {}).get(name, root / relative) for name, relative in OUTPUTS.items()}
    inputs = {
        "semantic_operations": root / "indexes/semantic_operation_inventory.jsonl",
        "semantic_apis": root / "indexes/semantic_api_inventory.jsonl",
        "observed_functions": root / "indexes/observed_function_inventory.jsonl",
        "task017_ledger": root / "indexes/task017_full_operation_disposition.jsonl",
        "task017a_reviews": root / "indexes/task017a_all_71_architecture_reviews.jsonl",
        "task017a_oversized": root / "indexes/task017a_five_oversized_adjunct.jsonl",
        "task017a_links": root / "indexes/task017a_cross_api_opportunity_links.jsonl",
        "task017a_backlog": root / "indexes/task017a_productization_decision_backlog.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    semantic_operations = _jsonl(inputs["semantic_operations"])
    apis = _jsonl(inputs["semantic_apis"])
    observed = _jsonl(inputs["observed_functions"])
    ledger = _jsonl(inputs["task017_ledger"])
    frozen_counts = (len(semantic_operations), len(apis), len(observed), len(ledger), len(_jsonl(inputs["task017a_reviews"])), len(_jsonl(inputs["task017a_oversized"])), len(_jsonl(inputs["task017a_links"])), len(_jsonl(inputs["task017a_backlog"])))
    if frozen_counts != (2414, 2036, 2414, 2414, 71, 5, 14, 90):
        raise ValueError(f"Task 018B frozen baseline reconciliation mismatch: {frozen_counts}")
    semantic_by_id = {value["semantic_operation_inventory_id"]: value for value in semantic_operations}
    observed_by_id = {value["observed_function_id"]: value for value in observed}
    if set(semantic_by_id) != {value["task014_operation_id"] for value in ledger}:
        raise ValueError("Task 014 operation identities do not reconcile with Task 017 ledger")
    operation_rows = _operation_rows(ledger, observed_by_id)
    api_rows = _api_rows(apis, operation_rows)
    selected, selection_reasons = _targeted_ids(operation_rows)
    operation_by_id = {value["task014_operation_id"]: value for value in operation_rows}
    object_rows, yaml_summary = _object_register(root, selected, selection_reasons, operation_by_id, semantic_by_id)
    _write_jsonl(paths["operations"], operation_rows)
    _write_jsonl(paths["apis"], api_rows)
    _write_jsonl(paths["objects"], object_rows)
    primary_counts = Counter(value["domain_assessment"]["proposed_primary"] for value in operation_rows if value["domain_assessment"]["proposed_primary"])
    alternative_counts = Counter(candidate for value in operation_rows for candidate in value["domain_assessment"]["alternative_candidates"])
    status_counts = Counter(value["domain_assessment"]["classification_status"] for value in operation_rows)
    summary = {
        "operation_count": len(operation_rows),
        "unique_operation_id_count": len({value["task014_operation_id"] for value in operation_rows}),
        "canonical_api_count": len(api_rows),
        "zero_operation_or_unsupported_api_count": sum(not value["accepted_operation_count"] for value in api_rows),
        "skeleton_candidate_count": len(SKELETON),
        "primary_candidate_counts": {label: primary_counts[label] for label in SKELETON},
        "alternative_candidate_counts": {label: alternative_counts[label] for label in SKELETON},
        "classification_status_counts": dict(sorted(status_counts.items())),
        "object_evidence_role_counts": dict(sorted(Counter(value["evidence_role"] for value in object_rows).items())),
        "targeted_yaml": yaml_summary,
        "enterprise_domain_approval_count": 0,
    }
    manifest = {
        "rules_version": RULES_VERSION,
        "scope": "TASK018B_EA_SKELETON_INITIAL_OPERATION_MAPPING",
        "skeleton_candidates": list(SKELETON),
        "skeleton_status": "EA_SUPPLIED_INITIAL_CANDIDATES_NOT_RATIFIED_TAXONOMY",
        "unit_of_classification": "HTTP_OPERATION",
        "summary": summary,
        "guardrails": {
            "api_name_used_as_primary_domain_evidence": False,
            "product_plan_channel_or_backend_used_as_domain_evidence": False,
            "whole_api_classification_performed": False,
            "task018a_taxonomy_reused": False,
            "task017a_records_modified": False,
            "new_domains_invented": False,
            "task019_performed": False,
        },
        "stop_gate": {"position": STOP_GATE, "enterprise_architect_review": "PENDING"},
        "inputs": {name: _fingerprint(path, root) for name, path in inputs.items()},
        "outputs": {
            "operations": _fingerprint(paths["operations"], root, len(operation_rows)),
            "apis": _fingerprint(paths["apis"], root, len(api_rows)),
            "objects": _fingerprint(paths["objects"], root, len(object_rows)),
        },
    }
    _write_json(paths["manifest"], manifest)
    return {"operations": operation_rows, "apis": api_rows, "objects": object_rows, "manifest": manifest}
