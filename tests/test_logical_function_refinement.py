from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-016/semantic-refinement"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_baseline_pairs_are_refined_exactly_once_without_rewrite() -> None:
    baseline = jsonl(ROOT / "indexes/task016_full_candidate_pairs.jsonl")
    refined = jsonl(ROOT / "indexes/task016_semantic_refinement_pairs.jsonl")
    assert len(baseline) == len(refined) == 1170
    baseline_by_id = {v["comparison_id"]: v for v in baseline}
    assert len(baseline_by_id) == len({v["prior_comparison_id"] for v in refined}) == 1170
    for value in refined:
        prior = baseline_by_id[value["prior_comparison_id"]]
        assert value["prior_comparison_status"] == prior["comparison_status"]
        assert value["candidate_logical_function_id"] == prior["candidate_logical_function_id"]
        assert value["left"]["task014_operation_id"] == prior["left"]["task014_operation_id"]
        assert value["right"]["task014_operation_id"] == prior["right"]["task014_operation_id"]
        assert value["prior_record_rewritten"] is False
        assert value["reviewer_status"] == "PENDING_REVIEW"
        assert not value["architect_approved_equivalence"]
        assert not value["confirmed_duplicate"]
        assert not value["merge_or_retirement_authorized"]
        assert not value["runtime_usage_inferred"]


def test_distribution_cross_tab_structural_controls_and_unpaired_visibility() -> None:
    manifest = json.loads((ROOT / "indexes/task016_semantic_refinement_manifest.json").read_text())
    refined = jsonl(ROOT / "indexes/task016_semantic_refinement_pairs.jsonl")
    assert manifest["refinement_distribution"] == dict(sorted(Counter(v["refinement_verdict"] for v in refined).items()))
    assert set(manifest["refinement_distribution"]) == {
        "STRUCTURAL_SIMILARITY_ONLY", "DIFFERENT_BUSINESS_ACTION_SUPPORTED",
        "POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE", "CONFLICTING_SEMANTICS_REVIEW",
        "SEMANTIC_EVIDENCE_INSUFFICIENT",
    }
    assert sum(v["count"] for v in manifest["old_status_by_refinement"]) == 1170
    assert manifest["structurally_equal_pair_count"] == 717
    assert manifest["structurally_equal_not_proven_same_function_count"] == 717
    assert manifest["unpaired_visible_operation_count"] == 1481
    assert manifest["baseline_candidate_generation_rerun"] is False
    assert manifest["all_pairs_performed"] is False
    assert manifest["approved_duplicate_count"] == 0


def test_hard_different_action_requires_supported_actions_and_aligned_object() -> None:
    refined = jsonl(ROOT / "indexes/task016_semantic_refinement_pairs.jsonl")
    hard = [v for v in refined if v["refinement_verdict"] == "DIFFERENT_BUSINESS_ACTION_SUPPORTED"]
    assert hard
    for value in hard:
        left = value["left"]["semantic_evidence"]
        right = value["right"]["semantic_evidence"]
        assert left["supported_action_categories"]
        assert right["supported_action_categories"]
        assert set(left["supported_action_categories"]).isdisjoint(right["supported_action_categories"])
        assert "BUSINESS_OBJECT_ALIGNED" in value["positive_evidence"]
        assert not left["action_evidence_conflict"]
        assert not right["action_evidence_conflict"]
    focused = jsonl(EVIDENCE / "focused_cases.jsonl")
    control = next(v for v in focused if {v["left"]["api_name"], v["right"]["api_name"]} == {"approverejectscrequest", "cancelscrequest"})
    assert control["case_type"] == "ACTION_DISAMBIGUATION_CONTROL_NOT_EXISTING_PAIR"
    assert control["refinement_verdict"] == "DIFFERENT_BUSINESS_ACTION_SUPPORTED"
    activate = next(v for v in focused if {v["left"]["api_name"], v["right"]["api_name"]} == {"mhrsd-activateindustrialestablishment", "mhrsd-deactivateindustrialestablishment"})
    assert activate["refinement_verdict"] == "SEMANTIC_EVIDENCE_INSUFFICIENT"


def test_backend_operation_scope_and_codegraph_context_do_not_infer_runtime() -> None:
    refined = jsonl(ROOT / "indexes/task016_semantic_refinement_pairs.jsonl")
    certainties = Counter()
    operation_scoped = []
    for value in refined:
        for side in ("left", "right"):
            backend = value[side]["backend_operation_evidence"]
            certainties[backend["certainty"]] += 1
            assert backend["certainty"] in {"CONFIGURED_API_SHARED_CANDIDATE", "CONFIGURED_OPERATION_SCOPED", "RESOLVED_OPERATION_SEMANTICS", "NOT_EVIDENCED"}
            assert backend["runtime_egress_proven"] is False
            for edge in backend["codegraph_dependency_context"]:
                assert edge["relationship_id"].startswith("api-invokes-target:sha256:")
                assert edge["target_canonical_identity_record_id"].startswith("backend-target:sha256:")
            if backend["certainty"] in {"CONFIGURED_OPERATION_SCOPED", "RESOLVED_OPERATION_SEMANTICS"}:
                operation_scoped.append(backend)
    assert certainties["CONFIGURED_API_SHARED_CANDIDATE"] > 0
    assert certainties["NOT_EVIDENCED"] > 0
    assert operation_scoped
    focused = jsonl(EVIDENCE / "focused_cases.jsonl")
    scoped_case = next(v for v in focused if v.get("selection_reason") == "OPERATION_SCOPED_BACKEND_CONTROL")
    assert any(scoped_case[side]["backend_operation_evidence"]["certainty"] in {"CONFIGURED_OPERATION_SCOPED", "RESOLVED_OPERATION_SEMANTICS"} for side in ("left", "right"))
    for value in focused:
        for side in ("left", "right"):
            backend = value[side]["backend_operation_evidence"]
            assert backend["gatewayscript_behavior_interpreted"] is False
            assert backend["dispatch_values_and_script_bodies_omitted"] is True


def test_mandatory_seasonal_employment_and_divergent_form_checks() -> None:
    focused = jsonl(EVIDENCE / "focused_cases.jsonl")
    seasonal = next(v for v in focused if {v["left"]["api_name"], v["right"]["api_name"]} == {"searchseasonalvisarequests", "searchseasonalvisarequests-v2"})
    assert seasonal["refinement_verdict"] == "POTENTIAL_SAME_BEHAVIOR_DIFFERENT_EXPOSURE"
    assert any(v["pointer"].endswith("/SortBy") for v in seasonal["request_response_comparison"]["request_differences"])
    employment = next(v for v in focused if {v["left"]["api_name"], v["right"]["api_name"]} == {"mcsemploymentstatusenquiry_querycenter", "mcsemploymentstatusenquiry"})
    assert employment["refinement_verdict"] == "SEMANTIC_EVIDENCE_INSUFFICIENT"
    distribution = json.loads((EVIDENCE / "pair_refinement_distribution.json").read_text())
    suggestions = jsonl(ROOT / "indexes/task016_semantic_refinement_divergent_suggestions.jsonl")
    assert distribution["divergent_form_suggestion_count"] == len(suggestions)
    assert distribution["unpaired_visible_operation_count"] == 1481
    assert distribution["complete_recall_claimed"] is False


def test_evidence_regeneration_is_deterministic_redacted_and_frozen_safe() -> None:
    frozen = [
        ROOT / "semantic_inventory/full_inventory.py", ROOT / "observed_function/full_inventory.py",
        ROOT / "logical_function/full_inventory.py", ROOT / "indexes/semantic_operation_inventory.jsonl",
        ROOT / "indexes/observed_function_inventory.jsonl", ROOT / "indexes/task016_full_candidate_pairs.jsonl",
        ROOT / "indexes/task016_full_operation_catalog.jsonl",
    ]
    before = {path: digest(path) for path in frozen}
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_refinement_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {path.name: digest(path) for path in EVIDENCE.iterdir() if path.is_file()}
    assert before == {path: digest(path) for path in frozen}
    text = "\n".join(path.read_text(encoding="utf-8") for path in EVIDENCE.iterdir() if path.suffix in {".json", ".jsonl", ".md", ".txt"})
    assert not re.search(r"https?://", text, re.I)
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", text)


def test_local_outputs_exclude_known_credentials_hosts_and_approval_claims() -> None:
    paths = [ROOT / "indexes/task016_semantic_refinement_pairs.jsonl", ROOT / "indexes/task016_semantic_refinement_focused_cases.jsonl"]
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
