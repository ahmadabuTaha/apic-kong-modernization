"""Deterministic, evidence-first Task 016 full candidate discovery.

This module creates review candidates.  It never approves logical sameness, merges
operations, or interprets configured/staging evidence as runtime activity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import yaml

from observed_function.mock import _schema_differences
from .mock import _request_shapes, _response_shapes


RULES_VERSION = "task016-logical-function-full-v1"
BLOCK_MEMBER_CAP = 40
PER_OPERATION_CANDIDATE_CAP = 20
GENERIC = {"api", "service", "services", "request", "response", "get", "post", "put", "delete", "patch", "v1", "v2", "v3", "the", "a", "an", "for", "of", "to", "and", "by", "id"}
OPPOSITE_ACTIONS = {
    frozenset(("create", "delete")), frozenset(("generate", "delete")),
    frozenset(("retrieve", "delete")), frozenset(("search", "delete")),
    frozenset(("validate", "update")), frozenset(("open", "close")),
    frozenset(("enable", "disable")), frozenset(("approve", "reject")),
}

OUTPUTS = {
    "operation_catalog": Path("indexes/task016_full_operation_catalog.jsonl"),
    "candidate_pairs": Path("indexes/task016_full_candidate_pairs.jsonl"),
    "candidate_groups": Path("indexes/task016_full_candidate_groups.jsonl"),
    "version_families": Path("indexes/task016_full_version_variant_families.jsonl"),
    "review_queue": Path("indexes/task016_full_review_queue.jsonl"),
    "block_diagnostics": Path("indexes/task016_full_candidate_blocks.jsonl"),
    "cache": Path("indexes/cache/task016_full_candidate_cache.json"),
    "manifest": Path("indexes/task016_full_manifest.json"),
}


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for v in values), encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    result = {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None:
        result["record_count"] = count
    return result


def _tokens(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    split = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return tuple(sorted({v for v in re.findall(r"[a-z0-9]+", split.lower()) if len(v) > 1 and v not in GENERIC and not v.isdigit()}))


def _version_key(name: str) -> str:
    value = name.lower().replace("_", "-")
    value = re.sub(r"(?:-?v(?:ersion)?-?\d+(?:-\d+)*)$", "", value)
    value = re.sub(r"(?:-\d+){2,3}$", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def _schema_hashes(operation: dict[str, Any], kind: str) -> tuple[str, ...]:
    if kind == "request":
        values = operation["contract"]["request"].get("content", [])
        return tuple(sorted({v["schema_shape_sha256"] for v in values if v.get("schema_shape_sha256")}))
    values = operation["contract"].get("responses", [])
    return tuple(sorted({v["schema_shape_sha256"] for v in values if v.get("schema_shape_sha256") and str(v.get("status", "")).startswith("2")}))


def _backend_ids(operation: dict[str, Any]) -> tuple[str, ...]:
    values = operation.get("configured_backend_facts", []) + operation.get("candidate_inherited_backend_context", [])
    return tuple(sorted({v["target_observation_id"] for v in values if v.get("target_observation_id")}))


def _policy_context(document: dict[str, Any]) -> dict[str, Any]:
    assembly = (document.get("x-ibm-configuration") or {}).get("assembly") or {}
    transformations = {"map", "gatewayscript", "xslt", "set-variable", "parse", "json-to-xml", "xml-to-json"}
    branches = {"switch", "operation-switch", "if", "case", "otherwise"}
    transform_pointers: list[dict[str, str]] = []
    branch_pointers: list[dict[str, str]] = []
    flag_pointers: list[str] = []

    def visit(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            for key, child in sorted(value.items()):
                child_pointer = f"{pointer}/{key}"
                lowered = str(key).lower()
                if lowered in transformations:
                    transform_pointers.append({"policy": lowered, "source_pointer": child_pointer})
                if lowered in branches:
                    branch_pointers.append({"policy": lowered, "source_pointer": child_pointer})
                if "feature" in lowered and "flag" in lowered:
                    flag_pointers.append(child_pointer)
                visit(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")

    visit(assembly, "/x-ibm-configuration/assembly")
    return {
        "transformation_policies": transform_pointers,
        "conditional_routing_policies": branch_pointers,
        "feature_flag_source_pointers": sorted(flag_pointers),
        "feature_flag_evidence_status": "FEATURE_FLAG_EVIDENCED_CONFIGURATION" if flag_pointers else "FEATURE_FLAG_NOT_EVIDENCED",
        "scope": "API_ASSEMBLY_CONTEXT_NOT_PROVEN_OPERATION_EXECUTION",
        "raw_values_omitted": True,
    }


class SourceCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.documents: dict[str, dict[str, Any]] = {}

    def operation(self, value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        relative = value["source_provenance"]["source_path"]
        if relative not in self.documents:
            self.documents[relative] = yaml.load((self.root / relative).read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
        document = self.documents[relative]
        payload = document["paths"][value["exact_path"]][value["method"].lower()]
        return document, payload


def _relationship_context(apis: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in relationships:
        by_type[relation["relationship_type"]].append(relation)
    product_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    plan_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_plan: dict[tuple[str, str], dict[str, Any]] = {}
    for value in by_type["product_contains_api"]:
        product_api[value["target_canonical_identity_record_id"]].append(value)
    for value in by_type["plan_entitles_api"]:
        plan_api[value["target_canonical_identity_record_id"]].append(value)
    for value in by_type["product_contains_plan"]:
        product_plan[(value["source_canonical_identity_record_id"], value["target_canonical_identity_record_id"])] = value
    sub_product = {v["source_canonical_identity_record_id"]: v for v in by_type["subscription_targets_product"]}
    sub_plan = {v["source_canonical_identity_record_id"]: v for v in by_type["subscription_uses_plan"]}
    sub_app = {v["source_canonical_identity_record_id"]: v for v in by_type["subscription_belongs_to_application"]}
    result: dict[str, dict[str, Any]] = {}
    for api in apis:
        api_id = api["canonical_api_id"]
        products = product_api.get(api_id, [])
        plans = plan_api.get(api_id, [])
        product_ids = {v["source_canonical_identity_record_id"] for v in products}
        plan_ids = {v["source_canonical_identity_record_id"] for v in plans}
        joins = []
        for subscription_id in sorted(set(sub_product) & set(sub_plan) & set(sub_app)):
            product_rel, plan_rel, app_rel = sub_product[subscription_id], sub_plan[subscription_id], sub_app[subscription_id]
            product_id = product_rel["target_canonical_identity_record_id"]
            plan_id = plan_rel["target_canonical_identity_record_id"]
            if product_id in product_ids and plan_id in plan_ids and (product_id, plan_id) in product_plan:
                product_api_rel = next(v for v in products if v["source_canonical_identity_record_id"] == product_id)
                plan_api_rel = next(v for v in plans if v["source_canonical_identity_record_id"] == plan_id)
                joins.append({
                    "subscription_relationship_id": product_rel["relationship_id"],
                    "plan_relationship_id": plan_rel["relationship_id"],
                    "application_relationship_id": app_rel["relationship_id"],
                    "product_plan_relationship_id": product_plan[(product_id, plan_id)]["relationship_id"],
                    "product_api_relationship_id": product_api_rel["relationship_id"],
                    "plan_api_relationship_id": plan_api_rel["relationship_id"],
                    "product_canonical_id": product_id,
                    "plan_canonical_id": plan_id,
                })
        unresolved = api.get("unresolved_product_location_occurrences", [])
        state = "AVAILABLE" if joins else "UNRESOLVED_RELATIONSHIP" if unresolved else "NOT_EVIDENCED_IN_ACCEPTED_SOURCE"
        result[api_id] = {
            "subscription_evidence_state": state,
            "accepted_product_relationship_ids": sorted(v["relationship_id"] for v in products),
            "accepted_plan_relationship_ids": sorted(v["relationship_id"] for v in plans),
            "accepted_product_ids": sorted(product_ids),
            "accepted_plan_ids": sorted(plan_ids),
            "subscription_join_count": len(joins),
            "subscription_join_relationships": joins,
            "unresolved_product_location_occurrence_count": len(unresolved),
            "consumer_identifiers_omitted": True,
            "scope": "SUBSCRIPTION_TO_PRODUCT_PLAN_THEN_ACCEPTED_PRODUCT_PLAN_TO_API_INDIRECT_CONTEXT",
            "catalog_space_context": "NOT_SEPARATELY_EVIDENCED_IN_ACCEPTED_RELATIONSHIP_INDEX",
            "operation_consumption_proven": False,
            "runtime_activity_proven": False,
        }
    return result


def _pair_signals(left: dict[str, Any], right: dict[str, Any], metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    lo, ro = metadata[left["semantic_operation_inventory_id"]], metadata[right["semantic_operation_inventory_id"]]
    object_overlap = sorted(set(lo["object_tokens"]) & set(ro["object_tokens"]))
    signals = {
        "exact_provisional_wording": bool(lo["phrase"] and lo["phrase"] == ro["phrase"]),
        "same_action_object": bool(lo["action"] and lo["action"] == ro["action"] and lo["object_tokens"] == ro["object_tokens"]),
        "shared_object_tokens": object_overlap,
        "same_method": left["method"] == right["method"],
        "same_normalized_path": left["contract"]["normalized_path_shape"] == right["contract"]["normalized_path_shape"],
        "shared_request_schema_hashes": sorted(set(lo["request_hashes"]) & set(ro["request_hashes"])),
        "shared_response_schema_hashes": sorted(set(lo["response_hashes"]) & set(ro["response_hashes"])),
        "shared_backend_observation_ids": sorted(set(lo["backend_ids"]) & set(ro["backend_ids"])),
        "same_version_family_key": bool(lo["version_key"] and lo["version_key"] == ro["version_key"]),
    }
    signals["signal_dimension_count"] = sum(bool(v) for k, v in signals.items() if k != "same_method")
    return signals


def _candidate_pool(operations: list[dict[str, Any]], observed: dict[str, dict[str, Any]], apis: dict[str, dict[str, Any]], structural: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], set[str]], list[dict[str, Any]], dict[str, dict[str, Any]], set[tuple[str, str]]]:
    metadata: dict[str, dict[str, Any]] = {}
    blocks: dict[tuple[str, str], list[str]] = defaultdict(list)
    operation_by_api_shape: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    by_id = {v["semantic_operation_inventory_id"]: v for v in operations}
    for operation in operations:
        oid = operation["semantic_operation_inventory_id"]
        obs = observed[oid]
        phrase = obs["candidate_observed_function"].get("concise_description") or ""
        action = obs["candidate_observed_function"].get("action_verb") or ""
        object_tokens = _tokens(obs["candidate_observed_function"].get("business_object_or_resource_phrase"))
        meta = {
            "phrase": phrase.lower().strip(), "action": action.lower().strip(), "object_tokens": object_tokens,
            "word_tokens": _tokens(phrase), "request_hashes": _schema_hashes(operation, "request"),
            "response_hashes": _schema_hashes(operation, "response"), "backend_ids": _backend_ids(operation),
            "version_key": _version_key(apis[operation["canonical_api_id"]]["identity_name"]),
        }
        metadata[oid] = meta
        if len(meta["word_tokens"]) >= 2:
            blocks[("WORDING", meta["phrase"])].append(oid)
        if action and object_tokens:
            blocks[("ACTION_OBJECT", action + ":" + "|".join(object_tokens))].append(oid)
        path = operation["contract"]["normalized_path_shape"]
        if path not in {"/", "/{parameter}"}:
            blocks[("METHOD_PATH", operation["method"] + ":" + path)].append(oid)
        for token in object_tokens:
            blocks[("OBJECT_TOKEN", token)].append(oid)
        for value in meta["request_hashes"]:
            blocks[("REQUEST_SCHEMA", value)].append(oid)
        for value in meta["response_hashes"]:
            blocks[("RESPONSE_SCHEMA", value)].append(oid)
        for value in meta["backend_ids"]:
            blocks[("BACKEND_OBSERVATION", value)].append(oid)
        if meta["version_key"]:
            blocks[("VERSION_FAMILY", meta["version_key"])].append(oid)
        operation_by_api_shape[(operation["canonical_api_id"], operation["method"], path)].append(oid)
    pair_sources: dict[tuple[str, str], set[str]] = defaultdict(set)
    diagnostics = []
    for (kind, key), members in sorted(blocks.items()):
        unique = sorted(set(members))
        oversized = len(unique) > BLOCK_MEMBER_CAP
        admitted = [] if oversized else unique
        for left_id, right_id in combinations(admitted, 2):
            if by_id[left_id]["canonical_api_id"] != by_id[right_id]["canonical_api_id"]:
                pair_sources[tuple(sorted((left_id, right_id)))].add(kind)
        diagnostics.append({
            "block_id": _id("task016-block", kind, key), "block_type": kind,
            "safe_block_key_sha256": hashlib.sha256(key.encode()).hexdigest(), "member_count": len(unique),
            "member_cap": BLOCK_MEMBER_CAP, "status": "QUEUED_OVERSIZED_NOT_EXPANDED" if oversized else "EXPANDED",
            "generated_cross_api_pair_count": sum(1 for a, b in combinations(admitted, 2) if by_id[a]["canonical_api_id"] != by_id[b]["canonical_api_id"]),
        })
    inherited_pairs: set[tuple[str, str]] = set()
    for candidate in structural:
        candidate_pairs = []
        for shape in candidate.get("matching_method_path_shapes", []):
            lefts = operation_by_api_shape.get((candidate["left_canonical_api_id"], shape["method"], shape["path_shape"]), [])
            rights = operation_by_api_shape.get((candidate["right_canonical_api_id"], shape["method"], shape["path_shape"]), [])
            candidate_pairs.extend(tuple(sorted((left, right))) for left in lefts for right in rights)
        if not candidate_pairs:
            lefts = [v["semantic_operation_inventory_id"] for v in operations if v["canonical_api_id"] == candidate["left_canonical_api_id"]]
            rights = [v["semantic_operation_inventory_id"] for v in operations if v["canonical_api_id"] == candidate["right_canonical_api_id"]]
            candidate_pairs.extend(tuple(sorted((left, right))) for left in lefts for right in rights)
        for pair in candidate_pairs:
            pair_sources[pair].add("INHERITED_TASK014_STRUCTURAL")
            pair_sources[pair].add(candidate["candidate_id"])
            inherited_pairs.add(pair)
    return pair_sources, diagnostics, metadata, inherited_pairs


def _frontend(api: dict[str, Any], operation: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    base_path = document.get("basePath")
    if not isinstance(base_path, str):
        servers = document.get("servers") or []
        base_path = "SERVER_PATH_PRESENT_REDACTED" if servers else None
    return {
        "method": operation["method"], "base_path": base_path, "exact_path": operation["exact_path"],
        "normalized_path": operation["contract"]["normalized_path_shape"], "operation_selector": operation.get("operation_selector"),
        "api_version_label": api.get("identity_version"), "exposure": operation["contract"]["exposure"],
        "auth": operation["contract"]["auth"], "parameters": operation["contract"]["parameters"],
        "request": operation["contract"]["request"], "responses": operation["contract"]["responses"],
    }


def _backend(operation: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    exact = operation.get("configured_backend_facts", [])
    candidate = operation.get("candidate_inherited_backend_context", [])
    def project(value: dict[str, Any]) -> dict[str, Any]:
        return {k: value.get(k) for k in ("target_observation_id", "resolution_status", "safe_target_path_or_template", "source_path", "source_pointer", "configuration_scope", "certainty")}
    return {
        "operation_scoped_configured_facts": [project(v) for v in exact],
        "api_shared_candidate_context": [project(v) for v in candidate],
        "backend_certainty": "OPERATION_SCOPED_CONFIGURED_FACT" if exact else "API_SHARED_CANDIDATE" if candidate else "NO_CONFIGURED_BACKEND_EVIDENCE",
        "assembly_policy_context": policy,
        "runtime_egress_state": "NOT_PROVEN",
        "raw_hosts_and_values_omitted": True,
    }


def _status(left_obs: dict[str, Any], right_obs: dict[str, Any], signals: dict[str, Any], request_diff: list[Any], response_diff: list[Any]) -> str:
    if left_obs["interpretation_status"] == "INSUFFICIENT_EVIDENCE" and right_obs["interpretation_status"] == "INSUFFICIENT_EVIDENCE":
        return "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"
    actions = frozenset((left_obs["candidate_observed_function"].get("action_verb"), right_obs["candidate_observed_function"].get("action_verb")))
    if actions in OPPOSITE_ACTIONS:
        return "CLEARLY_DIFFERENT_SUPPORTED"
    contract_difference = bool(request_diff or response_diff)
    if signals["exact_provisional_wording"] and (signals["same_normalized_path"] or signals["shared_backend_observation_ids"]):
        return "POSSIBLE_SAME_LOGICAL_FUNCTION" if not contract_difference else "REVIEW_REQUIRED_CONFLICTING_SIGNALS"
    if signals["same_action_object"] and signals["same_method"] and signals["signal_dimension_count"] >= 2:
        return "POSSIBLE_SAME_LOGICAL_FUNCTION" if not contract_difference else "REVIEW_REQUIRED_CONFLICTING_SIGNALS"
    return "REVIEW_REQUIRED_CONFLICTING_SIGNALS"


def build_full(root: Path, *, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    root = root.resolve()
    paths = {name: (root / path) for name, path in OUTPUTS.items()}
    if output_paths:
        paths.update(output_paths)
    inputs = {
        "apis": root / "indexes/semantic_api_inventory.jsonl", "operations": root / "indexes/semantic_operation_inventory.jsonl",
        "observed": root / "indexes/observed_function_inventory.jsonl", "structural": root / "indexes/semantic_structural_overlap_candidates.jsonl",
        "relationships": root / "indexes/relationship_index.jsonl", "gaps": root / "indexes/task015_full_gap_impact_register.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    dependency_sha256 = _hash({name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in inputs.items()})
    reusable_names = ("operation_catalog", "candidate_pairs", "candidate_groups", "version_families", "review_queue", "block_diagnostics")
    if paths["cache"].is_file() and paths["manifest"].is_file() and all(paths[name].is_file() for name in reusable_names):
        cache_payload = json.loads(paths["cache"].read_text(encoding="utf-8"))
        existing_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        outputs_match = all(
            hashlib.sha256(paths[name].read_bytes()).hexdigest() == existing_manifest.get("outputs", {}).get(name, {}).get("sha256")
            for name in reusable_names
        )
        if cache_payload.get("rules_version") == RULES_VERSION and cache_payload.get("input_dependency_sha256") == dependency_sha256 and outputs_match:
            return {
                "manifest": existing_manifest,
                "comparisons": _jsonl(paths["candidate_pairs"]), "groups": _jsonl(paths["candidate_groups"]),
                "version_families": _jsonl(paths["version_families"]), "operation_catalog": _jsonl(paths["operation_catalog"]),
                "review_queue": _jsonl(paths["review_queue"]),
            }
    api_values = _jsonl(inputs["apis"]); operations = _jsonl(inputs["operations"]); observed_values = _jsonl(inputs["observed"])
    structural = _jsonl(inputs["structural"]); relationships = _jsonl(inputs["relationships"])
    apis = {v["canonical_api_id"]: v for v in api_values}
    observed = {v["task014_operation_record_id"]: v for v in observed_values}
    if len(operations) != 2414 or set(observed) != {v["semantic_operation_inventory_id"] for v in operations}:
        raise ValueError("frozen Task 014/015 operation coverage mismatch")
    relation_context = _relationship_context(api_values, relationships)
    pair_sources, block_diagnostics, metadata, inherited_pairs = _candidate_pool(operations, observed, apis, structural)
    by_id = {v["semantic_operation_inventory_id"]: v for v in operations}
    eligible: list[tuple[tuple[str, str], dict[str, Any], set[str]]] = []
    for pair, sources in pair_sources.items():
        left, right = by_id[pair[0]], by_id[pair[1]]
        signals = _pair_signals(left, right, metadata)
        inherited = pair in inherited_pairs
        sufficient = inherited or signals["signal_dimension_count"] >= 2 and (
            signals["exact_provisional_wording"] or signals["same_action_object"] or
            len(signals["shared_object_tokens"]) >= 2 or
            signals["same_normalized_path"] and (signals["shared_request_schema_hashes"] or signals["shared_response_schema_hashes"] or signals["shared_backend_observation_ids"])
        )
        if sufficient:
            eligible.append((pair, signals, sources))
    eligible.sort(key=lambda value: (value[0] not in inherited_pairs, -value[1]["signal_dimension_count"], value[0]))
    accepted = []
    fanout = Counter()
    capped = []
    for value in eligible:
        pair = value[0]
        if pair not in inherited_pairs and (fanout[pair[0]] >= PER_OPERATION_CANDIDATE_CAP or fanout[pair[1]] >= PER_OPERATION_CANDIDATE_CAP):
            capped.append(pair)
            continue
        accepted.append(value); fanout[pair[0]] += 1; fanout[pair[1]] += 1
    cache = SourceCache(root)
    comparisons = []
    structural_id_set = {v["candidate_id"] for v in structural}
    for pair, signals, sources in accepted:
        left_op, right_op = by_id[pair[0]], by_id[pair[1]]
        left_api, right_api = apis[left_op["canonical_api_id"]], apis[right_op["canonical_api_id"]]
        left_obs, right_obs = observed[pair[0]], observed[pair[1]]
        left_doc, left_payload = cache.operation(left_op); right_doc, right_payload = cache.operation(right_op)
        left_request = _request_shapes(left_doc, left_payload); right_request = _request_shapes(right_doc, right_payload)
        left_response = _response_shapes(left_doc, left_payload); right_response = _response_shapes(right_doc, right_payload)
        request_diff = _schema_differences(left_request, right_request, limit=120)
        response_diff = _schema_differences(left_response, right_response, limit=120)
        status = _status(left_obs, right_obs, signals, request_diff, response_diff)
        shared_products = sorted(set(relation_context[left_op["canonical_api_id"]]["accepted_product_ids"]) & set(relation_context[right_op["canonical_api_id"]]["accepted_product_ids"]))
        shared_plans = sorted(set(relation_context[left_op["canonical_api_id"]]["accepted_plan_ids"]) & set(relation_context[right_op["canonical_api_id"]]["accepted_plan_ids"]))
        comparison_id = _id("logical-function-comparison-full", *pair, RULES_VERSION)
        comparisons.append({
            "comparison_id": comparison_id, "candidate_logical_function_id": _id("logical-function-candidate-full", comparison_id),
            "rules_version": RULES_VERSION, "comparison_status": status, "status_is_proposal_not_approval": True,
            "candidate_generation": {"block_types": sorted(v for v in sources if v not in structural_id_set), "inherited_task014_candidate_ids": sorted(v for v in sources if v in structural_id_set), "bounded": True},
            "business_intent_hypothesis": "POTENTIAL_SHARED_INTENT_REQUIRES_ARCHITECT_REVIEW" if status != "CLEARLY_DIFFERENT_SUPPORTED" else "DIFFERENT_INTENT_SUPPORTED_FOR_THIS_PAIR",
            "contract_compatibility": "STRUCTURALLY_EQUAL_IN_COMPARED_SHAPES" if not request_diff and not response_diff else "MATERIAL_DIFFERENCES_REQUIRE_REVIEW",
            "backend_certainty": {"left": _backend(left_op, _policy_context(left_doc))["backend_certainty"], "right": _backend(right_op, _policy_context(right_doc))["backend_certainty"]},
            "version_or_variant_relation": "SAME_VERSION_LABEL_NOT_ACTIVITY_PROOF" if left_api.get("identity_version") == right_api.get("identity_version") else "DIFFERENT_VERSION_LABELS_NO_PRECEDENCE_OR_ACTIVITY_INFERENCE",
            "subscription_evidence_state": {"left": relation_context[left_op["canonical_api_id"]]["subscription_evidence_state"], "right": relation_context[right_op["canonical_api_id"]]["subscription_evidence_state"]},
            "runtime_usage_state": "NOT_PROVEN_BY_STAGING_CONFIGURATION_OR_SUBSCRIPTIONS",
            "signals": signals,
            "left": {
                "canonical_api_id": left_op["canonical_api_id"], "api_name": left_api["identity_name"], "task014_operation_id": pair[0], "task015_observed_function_id": left_obs["observed_function_id"],
                "source_provenance": left_op["source_provenance"], "source_variant_fingerprint": left_op["source_variant_fingerprint"],
                "provisional_normalized_action_object": left_obs["candidate_observed_function"], "task015_interpretation_status": left_obs["interpretation_status"],
                "frontend_endpoint": _frontend(left_api, left_op, left_doc), "backend_implementation": _backend(left_op, _policy_context(left_doc)),
                "product_plan_subscription_context": relation_context[left_op["canonical_api_id"]],
            },
            "right": {
                "canonical_api_id": right_op["canonical_api_id"], "api_name": right_api["identity_name"], "task014_operation_id": pair[1], "task015_observed_function_id": right_obs["observed_function_id"],
                "source_provenance": right_op["source_provenance"], "source_variant_fingerprint": right_op["source_variant_fingerprint"],
                "provisional_normalized_action_object": right_obs["candidate_observed_function"], "task015_interpretation_status": right_obs["interpretation_status"],
                "frontend_endpoint": _frontend(right_api, right_op, right_doc), "backend_implementation": _backend(right_op, _policy_context(right_doc)),
                "product_plan_subscription_context": relation_context[right_op["canonical_api_id"]],
            },
            "schema_comparison": {"request_differences": request_diff, "response_differences": response_diff, "difference_limit": 120, "descriptions_examples_and_values_omitted": True},
            "product_plan_comparison": {"shared_product_ids": shared_products, "shared_plan_ids": shared_plans, "same_subscribed_exposure_proven": bool(shared_products and shared_plans), "separate_consumer_or_lifecycle_tracks": "HYPOTHESIS_ONLY_UNLESS_RELATIONSHIP_IDS_SHOW_DIFFERENT_EXPOSURE"},
            "positive_evidence": sorted(k for k, v in signals.items() if k != "signal_dimension_count" and bool(v)),
            "negative_or_uncertain_evidence": ["REQUEST_SCHEMA_DIFFERS"] * bool(request_diff) + ["RESPONSE_SCHEMA_DIFFERS"] * bool(response_diff) + ["TASK015_INTERPRETATION_NOT_CERTIFIED", "RUNTIME_EGRESS_NOT_PROVEN", "PRODUCTION_ACTIVITY_NOT_PROVEN"],
            "reviewer_status": "PENDING_REVIEW", "canonical_apis_merged": False, "operations_collapsed": False,
            "confirmed_duplicate": False, "safe_substitution_asserted": False, "retirement_asserted": False, "production_activity_asserted": False,
        })
    comparisons.sort(key=lambda v: v["comparison_id"])
    compared_ids = {v[side]["task014_operation_id"] for v in comparisons for side in ("left", "right")}
    memberships: dict[str, list[str]] = defaultdict(list)
    for value in comparisons:
        memberships[value["left"]["task014_operation_id"]].append(value["candidate_logical_function_id"])
        memberships[value["right"]["task014_operation_id"]].append(value["candidate_logical_function_id"])
    operation_catalog = []
    for operation in sorted(operations, key=lambda v: v["semantic_operation_inventory_id"]):
        oid = operation["semantic_operation_inventory_id"]
        operation_catalog.append({
            "task014_operation_id": oid, "task015_observed_function_id": observed[oid]["observed_function_id"], "canonical_api_id": operation["canonical_api_id"],
            "candidate_membership_ids": sorted(memberships[oid]), "candidate_state": "BOUNDED_CANDIDATE_FOUND" if oid in compared_ids else "NO_BOUNDED_CANDIDATE_FOUND_SINGLETON_VISIBLE",
            "source_provenance": operation["source_provenance"], "source_variant_fingerprint": operation["source_variant_fingerprint"],
        })
    groups = [{
        "candidate_logical_function_id": v["candidate_logical_function_id"], "comparison_id": v["comparison_id"], "comparison_status": v["comparison_status"],
        "member_operation_ids": [v["left"]["task014_operation_id"], v["right"]["task014_operation_id"]],
        "member_canonical_api_ids": [v["left"]["canonical_api_id"], v["right"]["canonical_api_id"]],
        "membership_provenance": "BOUNDED_MULTI_SIGNAL_CANDIDATE_NOT_ARCHITECT_APPROVED_EQUIVALENCE", "reviewer_status": "PENDING_REVIEW",
    } for v in comparisons]
    version_members: dict[str, set[str]] = defaultdict(set)
    for value in comparisons:
        if value["signals"]["same_version_family_key"] or value["version_or_variant_relation"].startswith("DIFFERENT"):
            key = _version_key(value["left"]["api_name"])
            if key and key == _version_key(value["right"]["api_name"]):
                version_members[key].update((value["left"]["task014_operation_id"], value["right"]["task014_operation_id"]))
    comparisons_by_operation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for value in comparisons:
        comparisons_by_operation[value["left"]["task014_operation_id"]].append(value)
        comparisons_by_operation[value["right"]["task014_operation_id"]].append(value)
    version_families = []
    for key, members in sorted(version_members.items()):
        if len(members) < 2:
            continue
        related = sorted({v["comparison_id"]: v for member in members for v in comparisons_by_operation[member] if v["left"]["task014_operation_id"] in members and v["right"]["task014_operation_id"] in members}.values(), key=lambda v: v["comparison_id"])
        feature_flag = any(
            v[side]["backend_implementation"]["assembly_policy_context"]["feature_flag_evidence_status"] == "FEATURE_FLAG_EVIDENCED_CONFIGURATION"
            for v in related for side in ("left", "right")
        )
        conditional = any(v[side]["backend_implementation"]["assembly_policy_context"]["conditional_routing_policies"] for v in related for side in ("left", "right"))
        version_families.append({
            "version_variant_family_id": _id("task016-version-family", key, sorted(members)), "safe_family_key_sha256": hashlib.sha256(key.encode()).hexdigest(),
            "member_operation_ids": sorted(members), "member_canonical_api_ids": sorted({by_id[v]["canonical_api_id"] for v in members}),
            "version_labels": sorted({str(apis[by_id[v]["canonical_api_id"]].get("identity_version")) for v in members}),
            "version_label_count": len({apis[by_id[v]["canonical_api_id"]].get("identity_version") for v in members}),
            "comparison_ids": [v["comparison_id"] for v in related],
            "frontend_endpoint_shapes": sorted({(by_id[v]["method"], by_id[v]["contract"]["normalized_path_shape"]) for v in members}),
            "contract_compatibility_distribution": dict(sorted(Counter(v["contract_compatibility"] for v in related).items())),
            "feature_flag_evidence_status": "FEATURE_FLAG_EVIDENCED_CONFIGURATION" if feature_flag else "FEATURE_FLAG_NOT_EVIDENCED",
            "conditional_routing_evidenced": conditional,
            "coexistence_reason": "CONFIGURED_CONDITIONAL_CONTEXT_REQUIRES_ARCHITECT_INTERPRETATION" if feature_flag or conditional else "COEXISTENCE_REASON_UNVERIFIED",
            "deployment_order_or_activity_inferred": False, "architect_review_required": True,
        })
    review_queue = [{
        "review_item_id": _id("task016-full-review", v["comparison_id"]), "comparison_id": v["comparison_id"], "candidate_logical_function_id": v["candidate_logical_function_id"],
        "priority": "HIGH" if v["comparison_status"] in {"REVIEW_REQUIRED_CONFLICTING_SIGNALS", "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"} else "NORMAL",
        "question": "Validate business intent separately from contract compatibility, version/variant purpose, and indirect subscription context.",
        "status": "PENDING_REVIEW", "responsible_role": "Integration Architect",
    } for v in comparisons]
    if capped:
        review_queue.append({"review_item_id": _id("task016-full-review", "fanout-cap"), "comparison_id": None, "candidate_logical_function_id": None, "priority": "NORMAL", "question": f"Review {len(capped)} deterministic candidates queued by the per-operation fan-out cap.", "status": "PENDING_REVIEW", "responsible_role": "Integration Architect"})
    for name, values in (("operation_catalog", operation_catalog), ("candidate_pairs", comparisons), ("candidate_groups", groups), ("version_families", version_families), ("review_queue", review_queue), ("block_diagnostics", block_diagnostics)):
        _write_jsonl(paths[name], values)
    cache_payload = {
        "cache_schema": "task016-candidate-signal-cache-v1", "rules_version": RULES_VERSION,
        "input_dependency_sha256": dependency_sha256,
        "operation_signal_projection": {key: value for key, value in sorted(metadata.items())},
        "safe_to_reuse_only_when_dependency_fingerprint_matches": True,
    }
    _write_json(paths["cache"], cache_payload)
    inherited_ids = {candidate_id for v in comparisons for candidate_id in v["candidate_generation"]["inherited_task014_candidate_ids"]}
    manifest = {
        "rules_version": RULES_VERSION, "input_operation_count": len(operations), "operation_catalog_count": len(operation_catalog),
        "candidate_pair_count": len(comparisons), "candidate_group_count": len(groups), "paired_operation_count": len(compared_ids), "unpaired_operation_count": len(operations) - len(compared_ids),
        "original_structural_candidate_count": len(structural), "original_structural_candidates_included": len(inherited_ids), "new_candidate_pair_count": sum(not v["candidate_generation"]["inherited_task014_candidate_ids"] for v in comparisons),
        "status_distribution": dict(sorted(Counter(v["comparison_status"] for v in comparisons).items())),
        "oversized_block_count": sum(v["status"] != "EXPANDED" for v in block_diagnostics), "fanout_capped_candidate_count": len(capped),
        "block_member_cap": BLOCK_MEMBER_CAP, "per_operation_candidate_cap": PER_OPERATION_CANDIDATE_CAP,
        "version_variant_family_count": len(version_families), "review_queue_count": len(review_queue),
        "unresolved_product_location_occurrence_count": sum(v["unresolved_product_location_occurrence_count"] for v in relation_context.values()),
        "all_pairs_performed": False, "complete_business_equivalence_recall_claimed": False, "model_use": "NONE_DETERMINISTIC_RULES_ONLY", "confluence_retrieved": False,
        "inputs": {name: _fingerprint(path, root) for name, path in inputs.items()},
        "targeted_source_document_count": len(cache.documents),
    }
    manifest["outputs"] = {name: _fingerprint(paths[name], root, len(values)) for name, values in (("operation_catalog", operation_catalog), ("candidate_pairs", comparisons), ("candidate_groups", groups), ("version_families", version_families), ("review_queue", review_queue), ("block_diagnostics", block_diagnostics))}
    manifest["outputs"]["cache"] = _fingerprint(paths["cache"], root, len(metadata))
    _write_json(paths["manifest"], manifest)
    return {"manifest": manifest, "comparisons": comparisons, "groups": groups, "version_families": version_families, "operation_catalog": operation_catalog, "review_queue": review_queue}
