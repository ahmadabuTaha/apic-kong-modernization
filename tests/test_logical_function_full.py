from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from logical_function import build_full


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-016/full-extraction"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_coverage_candidate_discovery_and_bounded_recall() -> None:
    manifest = json.loads((ROOT / "indexes/task016_full_manifest.json").read_text())
    catalog = jsonl(ROOT / "indexes/task016_full_operation_catalog.jsonl")
    pairs = jsonl(ROOT / "indexes/task016_full_candidate_pairs.jsonl")
    assert manifest["input_operation_count"] == manifest["operation_catalog_count"] == len(catalog) == 2414
    assert manifest["paired_operation_count"] + manifest["unpaired_operation_count"] == 2414
    assert len({v["task014_operation_id"] for v in catalog}) == 2414
    assert all(v["candidate_state"] in {"BOUNDED_CANDIDATE_FOUND", "NO_BOUNDED_CANDIDATE_FOUND_SINGLETON_VISIBLE"} for v in catalog)
    assert manifest["candidate_pair_count"] == len(pairs) > 60
    assert manifest["original_structural_candidates_included"] == manifest["original_structural_candidate_count"] == 60
    assert manifest["new_candidate_pair_count"] > 0
    assert manifest["all_pairs_performed"] is False
    assert manifest["complete_business_equivalence_recall_claimed"] is False
    assert manifest["oversized_block_count"] > 0


def test_identity_provenance_dimensions_and_hard_boundaries() -> None:
    operations = {v["semantic_operation_inventory_id"]: v for v in jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")}
    observed = {v["observed_function_id"]: v for v in jsonl(ROOT / "indexes/observed_function_inventory.jsonl")}
    for pair in jsonl(ROOT / "indexes/task016_full_candidate_pairs.jsonl"):
        assert pair["comparison_status"] in {"POSSIBLE_SAME_LOGICAL_FUNCTION", "REVIEW_REQUIRED_CONFLICTING_SIGNALS", "CLEARLY_DIFFERENT_SUPPORTED", "NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE"}
        assert pair["business_intent_hypothesis"]
        assert pair["contract_compatibility"]
        assert pair["backend_certainty"]
        assert pair["version_or_variant_relation"]
        assert pair["subscription_evidence_state"]
        assert pair["runtime_usage_state"] == "NOT_PROVEN_BY_STAGING_CONFIGURATION_OR_SUBSCRIPTIONS"
        assert pair["reviewer_status"] == "PENDING_REVIEW"
        assert not any(pair[key] for key in ("canonical_apis_merged", "operations_collapsed", "confirmed_duplicate", "safe_substitution_asserted", "retirement_asserted", "production_activity_asserted"))
        assert pair["left"]["canonical_api_id"] != pair["right"]["canonical_api_id"]
        for side in ("left", "right"):
            value = pair[side]
            source = operations[value["task014_operation_id"]]
            assert value["source_provenance"] == source["source_provenance"]
            assert value["source_variant_fingerprint"] == source["source_variant_fingerprint"]
            assert observed[value["task015_observed_function_id"]]["task014_operation_record_id"] == value["task014_operation_id"]


def test_subscription_join_uses_only_accepted_relationship_scope() -> None:
    relationships = {v["relationship_id"]: v for v in jsonl(ROOT / "indexes/relationship_index.jsonl")}
    seen_available = False
    for pair in jsonl(ROOT / "indexes/task016_full_candidate_pairs.jsonl"):
        for side in ("left", "right"):
            context = pair[side]["product_plan_subscription_context"]
            assert context["operation_consumption_proven"] is False
            assert context["runtime_activity_proven"] is False
            assert context["consumer_identifiers_omitted"] is True
            assert context["catalog_space_context"] == "NOT_SEPARATELY_EVIDENCED_IN_ACCEPTED_RELATIONSHIP_INDEX"
            for join in context["subscription_join_relationships"]:
                seen_available = True
                expected_types = {
                    "subscription_relationship_id": "subscription_targets_product",
                    "plan_relationship_id": "subscription_uses_plan",
                    "application_relationship_id": "subscription_belongs_to_application",
                    "product_plan_relationship_id": "product_contains_plan",
                    "product_api_relationship_id": "product_contains_api",
                    "plan_api_relationship_id": "plan_entitles_api",
                }
                for field, relationship_type in expected_types.items():
                    assert relationships[join[field]]["relationship_type"] == relationship_type
            if context["subscription_join_count"]:
                assert context["subscription_evidence_state"] == "AVAILABLE"
    assert seen_available
    assert json.loads((ROOT / "indexes/task016_full_manifest.json").read_text())["unresolved_product_location_occurrence_count"] == 113


def test_endpoint_scope_schema_contradictions_and_negative_controls() -> None:
    pairs = jsonl(ROOT / "indexes/task016_full_candidate_pairs.jsonl")
    seasonal = next(v for v in pairs if {v["left"]["api_name"], v["right"]["api_name"]} == {"searchseasonalvisarequests", "searchseasonalvisarequests-v2"})
    assert any(v["pointer"].endswith("/SortBy") for v in seasonal["schema_comparison"]["request_differences"])
    employment = next(v for v in pairs if {v["left"]["api_name"], v["right"]["api_name"]} == {"mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry"})
    assert employment["schema_comparison"]["request_differences"]
    assert any(v["comparison_status"] == "CLEARLY_DIFFERENT_SUPPORTED" for v in pairs)
    for pair in pairs:
        for side in ("left", "right"):
            backend = pair[side]["backend_implementation"]
            assert backend["runtime_egress_state"] == "NOT_PROVEN"
            assert backend["raw_hosts_and_values_omitted"] is True
            if backend["api_shared_candidate_context"] and not backend["operation_scoped_configured_facts"]:
                assert backend["backend_certainty"] == "API_SHARED_CANDIDATE"


def test_version_feature_flag_and_activity_non_inference() -> None:
    families = jsonl(ROOT / "indexes/task016_full_version_variant_families.jsonl")
    assert families
    assert all(v["feature_flag_evidence_status"] in {"FEATURE_FLAG_NOT_EVIDENCED", "FEATURE_FLAG_EVIDENCED_CONFIGURATION"} for v in families)
    assert all(v["deployment_order_or_activity_inferred"] is False for v in families)
    assert all(v["coexistence_reason"] in {"COEXISTENCE_REASON_UNVERIFIED", "CONFIGURED_CONDITIONAL_CONTEXT_REQUIRES_ARCHITECT_INTERPRETATION"} for v in families)
    evidence = jsonl(EVIDENCE / "version_variant_family_assessment.jsonl")
    seasonal = next(v for v in evidence if set(v.get("api_names", [])) == {"searchseasonalvisarequests", "searchseasonalvisarequests-v2"})
    assert any(v["pointer"].endswith("/SortBy") for v in seasonal["request_schema_differences"])
    assert seasonal["replacement_or_activity_inferred"] is False


def test_full_evidence_is_deterministic_secret_safe_and_frozen_inputs_unchanged() -> None:
    frozen = [
        ROOT / "semantic_inventory/full_inventory.py", ROOT / "observed_function/full_inventory.py",
        ROOT / "indexes/semantic_api_inventory.jsonl", ROOT / "indexes/semantic_operation_inventory.jsonl",
        ROOT / "indexes/observed_function_inventory.jsonl", ROOT / "indexes/semantic_structural_overlap_candidates.jsonl",
    ]
    before_frozen = {path: digest(path) for path in frozen}
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_full_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    assert before_frozen == {path: digest(path) for path in frozen}
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md", ".txt"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_local_outputs_exclude_known_credential_values_and_hosts() -> None:
    paths = [ROOT / "indexes/task016_full_candidate_pairs.jsonl", ROOT / "indexes/task016_full_operation_catalog.jsonl", ROOT / "indexes/task016_full_version_variant_families.jsonl"]
    payload = b"".join(path.read_bytes() for path in paths)
    sensitive = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text(encoding="utf-8")).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                if isinstance(item.get(field), str) and item[field]:
                    sensitive.append(item[field].encode())
    assert sensitive
    assert all(value not in payload for value in sensitive)
    assert b"http://" not in payload.lower()
    assert b"https://" not in payload.lower()
