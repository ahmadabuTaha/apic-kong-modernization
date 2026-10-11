"""Additive Task 016 semantic refinement over the frozen full candidate index."""

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

from observed_function.full_inventory import _redact_text


RULES_VERSION = "task016-focused-semantic-refinement-v1"
PAIR_OUTPUT = Path("indexes/task016_semantic_refinement_pairs.jsonl")
SUGGESTION_OUTPUT = Path("indexes/task016_semantic_refinement_divergent_suggestions.jsonl")
FOCUSED_OUTPUT = Path("indexes/task016_semantic_refinement_focused_cases.jsonl")
MANIFEST_OUTPUT = Path("indexes/task016_semantic_refinement_manifest.json")

VERB_PATTERNS = {
    "approve": r"\bapprov(?:e|ed|al|ing)\b",
    "reject": r"\breject(?:ed|ion|ing)?\b",
    "cancel": r"\bcancel(?:led|ed|lation|ation|ing)?\b",
    "terminate": r"\bterminat(?:e|ed|ion|ing)\b",
    "activate": r"(?<!de)\bactivat(?:e|ed|ion|ing)\b",
    "deactivate": r"\bdeactivat(?:e|ed|ion|ing)\b",
    "create": r"\bcreat(?:e|ed|ion|ing)\b",
    "retrieve": r"\bretriev(?:e|ed|al|ing)\b|\bget\b",
    "search": r"\bsearch(?:ed|ing)?\b",
    "validate": r"\bvalidat(?:e|ed|ion|ing)\b",
    "update": r"\bupdat(?:e|ed|ing)\b",
    "generate": r"\bgenerat(?:e|ed|ion|ing)\b",
    "delete": r"\bdelet(?:e|ed|ion|ing)\b",
    "submit": r"\bsubmit(?:ted|tal|ting)?\b",
    "issue": r"\bissu(?:e|ed|ance|ing)\b",
    "open": r"\bopen(?:ed|ing)?\b",
    "close": r"\bclos(?:e|ed|ing)\b",
    "enable": r"\benabl(?:e|ed|ing)\b",
    "disable": r"\bdisabl(?:e|ed|ing)\b",
    "read": r"\bread(?:ing)?\b",
    "write": r"\bwrit(?:e|ing|ten)\b",
    "list": r"\blist(?:ed|ing)?\b",
}
GENERIC_OBJECT = {"request", "requests", "service", "services", "api", "data", "details", "information", "by", "for", "from", "to", "or", "and", "the", "a", "an", "id", "number", "process"}
DISTINCT_ACTIONS = set(VERB_PATTERNS)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:sha256:{_hash(parts)}"


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def _write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text("".join(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")
    os.replace(temporary, path)


def _fingerprint(path: Path, root: Path, count: int | None = None) -> dict[str, Any]:
    result = {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    if count is not None:
        result["record_count"] = count
    return result


def _words(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _actions(value: str | None) -> list[str]:
    text = _words(value)
    return sorted(action for action, pattern in VERB_PATTERNS.items() if re.search(pattern, text))


def _object_tokens(value: str | None) -> list[str]:
    return sorted({token for token in _words(value).split() if len(token) > 1 and token not in GENERIC_OBJECT and token not in DISTINCT_ACTIONS and not token.isdigit()})


def _semantic_evidence(observed: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    facts = observed["source_facts"]
    provenance = operation["source_provenance"]
    fields = (
        ("SOURCE_SUMMARY", facts.get("summary"), provenance["source_pointer"] + "/summary"),
        ("SOURCE_DESCRIPTION", facts.get("description"), provenance["source_pointer"] + "/description"),
        ("SOURCE_OPERATION_ID", facts.get("operation_id"), provenance["source_pointer"] + "/operationId"),
        ("SOURCE_PATH", facts.get("exact_path"), provenance["source_pointer"]),
        ("API_NAME", observed["parent_api"].get("identity_name"), "API_IDENTITY_NAME"),
    )
    signals = []
    for evidence_type, value, pointer in fields:
        actions = _actions(value)
        if actions:
            signals.append({"evidence_type": evidence_type, "actions": actions, "source_path": provenance["source_path"], "source_pointer": pointer, "value_sha256": _hash(value)})
    documented = sorted({action for value in signals if value["evidence_type"] in {"SOURCE_SUMMARY", "SOURCE_DESCRIPTION"} for action in value["actions"]})
    structural_counts = Counter(action for value in signals if value["evidence_type"] in {"SOURCE_OPERATION_ID", "SOURCE_PATH", "API_NAME"} for action in value["actions"])
    corroborated = sorted(action for action, count in structural_counts.items() if count >= 2)
    supported = documented or corroborated
    provisional = observed["candidate_observed_function"].get("action_verb")
    source_action_union = sorted({action for value in signals for action in value["actions"]})
    contradiction = bool(documented and corroborated and set(documented).isdisjoint(corroborated))
    if provisional in DISTINCT_ACTIONS and supported and provisional not in supported:
        contradiction = True
    support = "DOCUMENTED_ACTION" if documented else "STRUCTURALLY_CORROBORATED_PROVISIONAL" if corroborated else "NAME_OR_SINGLE_SIGNAL_ONLY" if signals else "NOT_EVIDENCED"
    object_phrase = observed["candidate_observed_function"].get("business_object_or_resource_phrase")
    return {
        "task015_provisional_action": provisional,
        "task015_provisional_object": object_phrase,
        "task015_interpretation_status": observed["interpretation_status"],
        "supported_action_categories": supported,
        "source_action_union": source_action_union,
        "action_support": support,
        "action_evidence_conflict": contradiction,
        "object_tokens": _object_tokens(object_phrase),
        "direct_evidence": signals,
    }


def _backend_projection(operation: dict[str, Any], resolution: dict[str, dict[str, Any]], graph_by_api: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    exact = operation.get("configured_backend_facts", [])
    candidate = operation.get("candidate_inherited_backend_context", [])
    values = exact or candidate
    projected = []
    for value in values:
        resolved = resolution.get(value.get("target_observation_id"), {})
        projected.append({
            "target_observation_id": value.get("target_observation_id"),
            "configured_http_method": resolved.get("http_verb"),
            "safe_backend_operation_path": value.get("safe_target_path_or_template") or resolved.get("normalized_target_path") or resolved.get("target_path_suffix_or_template"),
            "resolution_status": value.get("resolution_status") or resolved.get("resolution_status"),
            "configuration_scope": "CONFIGURED_OPERATION_SCOPED" if exact else "CONFIGURED_API_SHARED_CANDIDATE",
            "source_path": value.get("source_path"), "source_pointer": value.get("source_pointer"),
        })
    resolved_operation = bool(exact and projected and all(v["resolution_status"] == "RESOLVED" and v["safe_backend_operation_path"] for v in projected))
    certainty = "RESOLVED_OPERATION_SEMANTICS" if resolved_operation else "CONFIGURED_OPERATION_SCOPED" if exact else "CONFIGURED_API_SHARED_CANDIDATE" if candidate else "NOT_EVIDENCED"
    graph_edges = (graph_by_api or {}).get(operation["canonical_api_id"], [])
    return {
        "certainty": certainty, "configured_operations": projected,
        "codegraph_dependency_context": [{
            "relationship_id": value["relationship_id"], "target_canonical_identity_record_id": value["target_canonical_identity_record_id"],
            "scope_classifications": value.get("scope_classifications", []), "operation_scopes": value.get("operation_scopes", []),
            "evidence_state": value.get("evidence_state"),
        } for value in graph_edges],
        "runtime_egress_proven": False,
    }


def _refinement(left: dict[str, Any], right: dict[str, Any], pair: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    positive: list[str] = []
    negative: list[str] = []
    left_actions, right_actions = set(left["supported_action_categories"]), set(right["supported_action_categories"])
    left_objects, right_objects = set(left["object_tokens"]), set(right["object_tokens"])
    object_overlap = sorted(left_objects & right_objects)
    object_union = left_objects | right_objects
    object_alignment = bool(left_objects and right_objects and (left_objects == right_objects or len(object_overlap) / len(object_union) >= 0.6))
    if object_alignment:
        positive.append("BUSINESS_OBJECT_ALIGNED")
    elif object_overlap:
        positive.append("PARTIAL_OBJECT_TOKEN_OVERLAP_SUPPORTING_SIGNAL_ONLY")
    if left_actions and left_actions == right_actions:
        positive.append("SUPPORTED_BUSINESS_ACTION_SET_EQUAL")
    if pair["contract_compatibility"] == "STRUCTURALLY_EQUAL_IN_COMPARED_SHAPES":
        positive.append("REQUEST_RESPONSE_SHAPES_EQUAL_SUPPORTING_SIGNAL_ONLY")
    if pair["signals"].get("shared_backend_observation_ids"):
        positive.append("SHARED_BACKEND_OBSERVATION_SUPPORTING_SIGNAL_ONLY")
    if left["action_evidence_conflict"] or right["action_evidence_conflict"]:
        negative.append("SOURCE_ACTION_SIGNALS_CONFLICT")
    if left_actions and right_actions and left_actions.isdisjoint(right_actions):
        negative.append("SUPPORTED_BUSINESS_ACTIONS_DIFFER")
    if not object_alignment:
        negative.append("BUSINESS_OBJECT_ALIGNMENT_NOT_ESTABLISHED")
    if left["task015_interpretation_status"] == "INSUFFICIENT_EVIDENCE" or right["task015_interpretation_status"] == "INSUFFICIENT_EVIDENCE":
        return "SEMANTIC_EVIDENCE_INSUFFICIENT", positive, negative + ["TASK015_SIDE_INSUFFICIENT"]
    if left["action_evidence_conflict"] or right["action_evidence_conflict"]:
        return "CONFLICTING_SEMANTICS_REVIEW", positive, negative
    if left_actions and right_actions and left_actions.isdisjoint(right_actions) and object_alignment:
        return "DIFFERENT_BUSINESS_ACTION_SUPPORTED", positive, negative
    if left_actions and left_actions == right_actions and object_alignment:
        return "POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE", positive, negative
    if not left_actions and not right_actions:
        return "SEMANTIC_EVIDENCE_INSUFFICIENT", positive, negative + ["SUPPORTED_ACTION_NOT_EVIDENCED"]
    if pair["contract_compatibility"] == "STRUCTURALLY_EQUAL_IN_COMPARED_SHAPES" or pair["signals"].get("shared_backend_observation_ids"):
        return "STRUCTURAL_SIMILARITY_ONLY", positive, negative
    return "CONFLICTING_SEMANTICS_REVIEW", positive, negative


def _focused_backend(root: Path, operation: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    document = yaml.load((root / operation["source_provenance"]["source_path"]).read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    assembly = (document.get("x-ibm-configuration") or {}).get("assembly") or {}
    selector_matches: list[str] = []
    invocation_pointers: list[str] = []
    transformation_pointers: list[dict[str, str]] = []
    branch_pointers: list[dict[str, str]] = []
    rewrite_pointers: list[str] = []
    scripts: list[str] = []
    transforms = {"map", "xslt", "parse", "json-to-xml", "xml-to-json", "set-variable"}
    branches = {"operation-switch", "switch", "case", "otherwise", "if"}

    def contains_selector(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        operations = value.get("operations")
        return isinstance(operations, list) and any(
            isinstance(v, dict) and str(v.get("verb", "")).upper() == operation["method"] and v.get("path") == operation["exact_path"]
            for v in operations
        )

    def visit(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            if contains_selector(value):
                selector_matches.append(pointer + "/operations")
            for key, child in sorted(value.items()):
                child_pointer = f"{pointer}/{key}"
                lowered = str(key).lower()
                if lowered == "invoke":
                    invocation_pointers.append(child_pointer)
                if lowered in transforms:
                    transformation_pointers.append({"policy": lowered, "source_pointer": child_pointer})
                if lowered in branches:
                    branch_pointers.append({"policy": lowered, "source_pointer": child_pointer})
                if lowered in {"rewrite", "set-path", "url-rewrite"}:
                    rewrite_pointers.append(child_pointer)
                if lowered == "gatewayscript":
                    scripts.append(child_pointer)
                visit(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")

    visit(assembly, "/x-ibm-configuration/assembly")
    certainty = baseline["certainty"]
    if selector_matches and baseline["configured_operations"] and all(v["resolution_status"] == "RESOLVED" and v["safe_backend_operation_path"] for v in baseline["configured_operations"]):
        certainty = "RESOLVED_OPERATION_SEMANTICS"
    return {
        **baseline,
        "certainty": certainty,
        "matching_operation_selector_pointers": sorted(selector_matches),
        "assembly_invoke_pointers": sorted(invocation_pointers),
        "branch_pointers": branch_pointers,
        "rewrite_pointers": sorted(rewrite_pointers),
        "transformation_pointers": transformation_pointers,
        "gatewayscript_pointers": sorted(scripts),
        "gatewayscript_behavior_interpreted": False,
        "dispatch_values_and_script_bodies_omitted": True,
    }


def _side_case(root: Path, side: dict[str, Any], operation: dict[str, Any], observed: dict[str, Any], semantic: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    safe_summary, summary_redacted = _redact_text(observed["source_facts"].get("summary"))
    safe_description, description_redacted = _redact_text(observed["source_facts"].get("description"))
    return {
        "canonical_api_id": side["canonical_api_id"], "api_name": side["api_name"],
        "task014_operation_id": side["task014_operation_id"], "task015_observed_function_id": side["task015_observed_function_id"],
        "method": operation["method"], "exact_path": operation["exact_path"], "normalized_path": operation["contract"]["normalized_path_shape"],
        "business_action_object_evidence": semantic,
        "safe_source_summary": safe_summary, "safe_source_description": safe_description,
        "source_text_redacted": summary_redacted or description_redacted,
        "source_provenance": operation["source_provenance"],
        "request_contract": operation["contract"]["request"], "response_contract": operation["contract"]["responses"],
        "backend_operation_evidence": _focused_backend(root, operation, backend),
        "product_plan_subscription_context": side["product_plan_subscription_context"],
    }


def _select_focused(refined_by_pair: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    names = [
        ("searchseasonalvisarequests", "searchseasonalvisarequests-v2"),
        ("mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry"),
        ("mhrsd-deactivateindustrialestablishment", "mhrsd-activateindustrialestablishment"),
        ("proposals", "ajeer-bulk-contracts"),
        ("updateworkerdata", "cancelvisa"),
        ("qiwa_cancelexternalcontract", "wscancelexternalcontract"),
        ("cancelgsblicense", "cancelgsblicensetip"),
        ("mof-cancelworkpermitbillv2", "mof-cancelworkpermitbill"),
    ]
    existing = {tuple(sorted((v["left"]["api_name"], v["right"]["api_name"]))): pair_id for pair_id, v in refined_by_pair.items()}
    selected = [(existing[tuple(sorted(value))], "MANDATORY_OR_ACTION_AUDIT") for value in names if tuple(sorted(value)) in existing]
    for verdict in ("DIFFERENT_BUSINESS_ACTION_SUPPORTED", "POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE", "STRUCTURAL_SIMILARITY_ONLY", "CONFLICTING_SEMANTICS_REVIEW", "SEMANTIC_EVIDENCE_INSUFFICIENT"):
        match = next((pair_id for pair_id, value in sorted(refined_by_pair.items()) if value["refinement_verdict"] == verdict and pair_id not in {v[0] for v in selected}), None)
        if match:
            selected.append((match, "DISTRIBUTION_CONTROL"))
    operation_scoped = next((pair_id for pair_id, value in sorted(refined_by_pair.items()) if pair_id not in {v[0] for v in selected} and any(value[side]["backend_operation_evidence"]["certainty"] in {"CONFIGURED_OPERATION_SCOPED", "RESOLVED_OPERATION_SEMANTICS"} for side in ("left", "right"))), None)
    if operation_scoped:
        selected.append((operation_scoped, "OPERATION_SCOPED_BACKEND_CONTROL"))
    return selected


def _audit_control(api_names: tuple[str, str], operations: dict[str, dict[str, Any]], observed_values: list[dict[str, Any]], resolution: dict[str, dict[str, Any]], graph_by_api: dict[str, list[dict[str, Any]]], root: Path) -> dict[str, Any] | None:
    found = []
    for name in api_names:
        candidates = [v for v in observed_values if v["parent_api"].get("identity_name") == name]
        if not candidates:
            return None
        obs = sorted(candidates, key=lambda v: v["task014_operation_record_id"])[0]
        operation = operations[obs["task014_operation_record_id"]]
        semantic = _semantic_evidence(obs, operation)
        side = {"canonical_api_id": operation["canonical_api_id"], "api_name": name, "task014_operation_id": operation["semantic_operation_inventory_id"], "task015_observed_function_id": obs["observed_function_id"], "product_plan_subscription_context": {"context_available_in_full_pair_index": False, "operation_consumption_proven": False, "runtime_activity_proven": False}}
        found.append(_side_case(root, side, operation, obs, semantic, _backend_projection(operation, resolution, graph_by_api)))
    return {
        "focused_case_id": _id("task016-semantic-audit-control", *api_names), "case_type": "ACTION_DISAMBIGUATION_CONTROL_NOT_EXISTING_PAIR",
        "prior_comparison_id": None, "refinement_verdict": "DIFFERENT_BUSINESS_ACTION_SUPPORTED",
        "left": found[0], "right": found[1],
        "reason": "Documented approve/reject behavior is distinct from documented cancel behavior; a common request object or command envelope would not establish duplication.",
        "architect_approved_equivalence": False, "runtime_usage_inferred": False,
    }


def build_refinement(root: Path, *, pair_path: Path | None = None, suggestion_path: Path | None = None, focused_path: Path | None = None, manifest_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    pair_path = pair_path or root / PAIR_OUTPUT; suggestion_path = suggestion_path or root / SUGGESTION_OUTPUT
    focused_path = focused_path or root / FOCUSED_OUTPUT; manifest_path = manifest_path or root / MANIFEST_OUTPUT
    inputs = {
        "baseline_pairs": root / "indexes/task016_full_candidate_pairs.jsonl",
        "operation_catalog": root / "indexes/task016_full_operation_catalog.jsonl",
        "operations": root / "indexes/semantic_operation_inventory.jsonl",
        "observed": root / "indexes/observed_function_inventory.jsonl",
        "candidate_cache": root / "indexes/cache/task016_full_candidate_cache.json",
        "backend_resolution": root / "indexes/backend_target_resolution.jsonl",
        "codegraph_nodes": root / "indexes/codegraph_nodes.jsonl",
        "codegraph_edges": root / "indexes/codegraph_edges.jsonl",
        "codegraph_dependency_edges": root / "indexes/codegraph_dependency_edges.jsonl",
        "relationships": root / "indexes/relationship_index.jsonl",
        "implementation": Path(__file__).resolve(),
    }
    pairs = _jsonl(inputs["baseline_pairs"]); catalog = _jsonl(inputs["operation_catalog"])
    operation_values = _jsonl(inputs["operations"]); observed_values = _jsonl(inputs["observed"])
    operations = {v["semantic_operation_inventory_id"]: v for v in operation_values}
    observed = {v["task014_operation_record_id"]: v for v in observed_values}
    resolution = {v["target_observation_id"]: v for v in _jsonl(inputs["backend_resolution"])}
    graph_by_api: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in _jsonl(inputs["codegraph_dependency_edges"]):
        graph_by_api[edge["source_canonical_identity_record_id"]].append(edge)
    if len(pairs) != 1170 or len(catalog) != 2414 or sum(v["candidate_state"] == "NO_BOUNDED_CANDIDATE_FOUND_SINGLETON_VISIBLE" for v in catalog) != 1481:
        raise ValueError("Task 016 frozen baseline reconciliation mismatch")
    refined = []
    for pair in pairs:
        left_id, right_id = pair["left"]["task014_operation_id"], pair["right"]["task014_operation_id"]
        left_semantic = _semantic_evidence(observed[left_id], operations[left_id]); right_semantic = _semantic_evidence(observed[right_id], operations[right_id])
        verdict, positive, negative = _refinement(left_semantic, right_semantic, pair)
        refined.append({
            "refinement_id": _id("task016-semantic-refinement", pair["comparison_id"], RULES_VERSION),
            "rules_version": RULES_VERSION, "prior_comparison_id": pair["comparison_id"], "prior_comparison_status": pair["comparison_status"],
            "candidate_logical_function_id": pair["candidate_logical_function_id"], "refinement_verdict": verdict,
            "identity_hypothesis": "BUSINESS_ACTION_PLUS_BUSINESS_OBJECT_PLUS_BEHAVIORAL_SEMANTICS",
            "left": {"canonical_api_id": pair["left"]["canonical_api_id"], "api_name": pair["left"]["api_name"], "task014_operation_id": left_id, "task015_observed_function_id": pair["left"]["task015_observed_function_id"], "semantic_evidence": left_semantic, "backend_operation_evidence": _backend_projection(operations[left_id], resolution, graph_by_api)},
            "right": {"canonical_api_id": pair["right"]["canonical_api_id"], "api_name": pair["right"]["api_name"], "task014_operation_id": right_id, "task015_observed_function_id": pair["right"]["task015_observed_function_id"], "semantic_evidence": right_semantic, "backend_operation_evidence": _backend_projection(operations[right_id], resolution, graph_by_api)},
            "contract_compatibility_context": pair["contract_compatibility"], "version_context": pair["version_or_variant_relation"],
            "subscription_context_state": pair["subscription_evidence_state"], "positive_evidence": positive, "negative_or_uncertain_evidence": negative,
            "structural_similarity_is_not_functional_identity": True, "prior_record_rewritten": False,
            "architect_approved_equivalence": False, "confirmed_duplicate": False, "merge_or_retirement_authorized": False,
            "runtime_usage_inferred": False, "reviewer_status": "PENDING_REVIEW",
        })
    refined.sort(key=lambda v: v["prior_comparison_id"])
    refined_by_pair = {v["prior_comparison_id"]: v for v in refined}

    cache = json.loads(inputs["candidate_cache"].read_text(encoding="utf-8"))["operation_signal_projection"]
    unpaired = {v["task014_operation_id"] for v in catalog if v["candidate_state"] == "NO_BOUNDED_CANDIDATE_FOUND_SINGLETON_VISIBLE"}
    blocks: dict[tuple[str, tuple[str, ...]], list[str]] = defaultdict(list)
    for operation_id in sorted(unpaired):
        meta = cache[operation_id]
        action, object_tokens = meta.get("action"), tuple(meta.get("object_tokens") or ())
        if action and object_tokens and observed[operation_id]["interpretation_status"] != "INSUFFICIENT_EVIDENCE":
            blocks[(action, object_tokens)].append(operation_id)
    suggestions = []
    for (action, object_tokens), members in sorted(blocks.items()):
        if not 2 <= len(members) <= 10:
            continue
        for left_id, right_id in combinations(sorted(members), 2):
            left_op, right_op = operations[left_id], operations[right_id]
            if left_op["canonical_api_id"] == right_op["canonical_api_id"] or left_op["exact_path"] == right_op["exact_path"]:
                continue
            suggestions.append({
                "suggestion_id": _id("task016-divergent-form-suggestion", left_id, right_id, RULES_VERSION),
                "source": "EXISTING_TASK016_CACHED_ACTION_OBJECT_BLOCK", "action": action, "object_tokens": list(object_tokens),
                "left_task014_operation_id": left_id, "right_task014_operation_id": right_id,
                "left_task015_observed_function_id": observed[left_id]["observed_function_id"], "right_task015_observed_function_id": observed[right_id]["observed_function_id"],
                "left_endpoint": {"method": left_op["method"], "path": left_op["exact_path"]}, "right_endpoint": {"method": right_op["method"], "path": right_op["exact_path"]},
                "status": "BOUNDED_MISSED_CANDIDATE_SUGGESTION_PENDING_REVIEW", "behavioral_identity_proven": False,
            })
            if len(suggestions) >= 25:
                break
        if len(suggestions) >= 25:
            break

    focused = []
    pair_lookup = {v["comparison_id"]: v for v in pairs}
    for comparison_id, selection_reason in _select_focused(refined_by_pair):
        value, pair = refined_by_pair[comparison_id], pair_lookup[comparison_id]
        left_id, right_id = value["left"]["task014_operation_id"], value["right"]["task014_operation_id"]
        focused.append({
            "focused_case_id": _id("task016-focused-case", comparison_id, RULES_VERSION), "case_type": "EXISTING_PAIR_TARGETED_VERIFICATION", "selection_reason": selection_reason,
            "prior_comparison_id": comparison_id, "prior_comparison_status": value["prior_comparison_status"], "refinement_verdict": value["refinement_verdict"],
            "left": _side_case(root, pair["left"], operations[left_id], observed[left_id], value["left"]["semantic_evidence"], value["left"]["backend_operation_evidence"]),
            "right": _side_case(root, pair["right"], operations[right_id], observed[right_id], value["right"]["semantic_evidence"], value["right"]["backend_operation_evidence"]),
            "request_response_comparison": pair["schema_comparison"], "contract_compatibility_context": pair["contract_compatibility"],
            "positive_evidence": value["positive_evidence"], "negative_or_uncertain_evidence": value["negative_or_uncertain_evidence"],
            "product_plan_subscription_is_context_only": True, "architect_approved_equivalence": False, "runtime_usage_inferred": False,
        })
    for names in (("approverejectscrequest", "cancelscrequest"),):
        control = _audit_control(names, operations, observed_values, resolution, graph_by_api, root)
        if control:
            focused.append(control)
    focused.sort(key=lambda v: v["focused_case_id"])
    _write_jsonl(pair_path, refined); _write_jsonl(suggestion_path, suggestions); _write_jsonl(focused_path, focused)
    cross = Counter((v["prior_comparison_status"], v["refinement_verdict"]) for v in refined)
    distribution = Counter(v["refinement_verdict"] for v in refined)
    structurally_equal = [v for v in refined if v["contract_compatibility_context"] == "STRUCTURALLY_EQUAL_IN_COMPARED_SHAPES"]
    manifest = {
        "rules_version": RULES_VERSION, "baseline_pair_count": len(pairs), "refined_pair_count": len(refined),
        "refinement_distribution": dict(sorted(distribution.items())),
        "old_status_by_refinement": [{"prior_status": old, "refinement_verdict": new, "count": count} for (old, new), count in sorted(cross.items())],
        "structurally_equal_pair_count": len(structurally_equal),
        "structurally_equal_not_proven_same_function_count": sum(not v["architect_approved_equivalence"] for v in structurally_equal),
        "unpaired_visible_operation_count": len(unpaired), "divergent_form_suggestion_count": len(suggestions), "focused_case_count": len(focused),
        "all_pairs_performed": False, "baseline_candidate_generation_rerun": False, "approved_duplicate_count": 0,
        "runtime_usage_inferred": False, "staging_modified": False,
        "inputs": {name: _fingerprint(path, root) for name, path in inputs.items()},
        "outputs": {"refined_pairs": _fingerprint(pair_path, root, len(refined)), "suggestions": _fingerprint(suggestion_path, root, len(suggestions)), "focused_cases": _fingerprint(focused_path, root, len(focused))},
    }
    _atomic_json(manifest_path, manifest)
    return {"manifest": manifest, "refined_pairs": refined, "suggestions": suggestions, "focused_cases": focused}
