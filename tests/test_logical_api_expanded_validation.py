from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "tests/evidence/task-017/expanded-validation"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_counts_are_bounded_distinct_and_not_padded() -> None:
    records = jsonl(EVIDENCE / "expanded_sample_register.jsonl")
    assert len(records) == 46
    origins = Counter(v["sample_origin"] for v in records)
    assert origins == {"ORIGINAL_MOCK_ANCHOR": 10, "EXPANDED_TASK016_PAIR": 32, "EXPANDED_MULTI_OPERATION_API": 4}
    member_ids = [m["task014_operation_id"] for v in records for m in v["members"]]
    assert len(member_ids) == len(set(member_ids)) == 98
    pair_signatures = [tuple(sorted(m["task014_operation_id"] for m in v["members"])) for v in records if v["sample_origin"] == "EXPANDED_TASK016_PAIR"]
    assert len(pair_signatures) == len(set(pair_signatures)) == 32


def test_original_ten_are_immutable_anchors_with_prior_status_preserved() -> None:
    original_path = ROOT / "tests/evidence/task-017/mock/representative_boundary_cases.jsonl"
    originals = {v["boundary_case_id"]: v for v in jsonl(original_path)}
    records = [v for v in jsonl(EVIDENCE / "expanded_sample_register.jsonl") if v["sample_origin"] == "ORIGINAL_MOCK_ANCHOR"]
    manifest = json.loads((EVIDENCE / "build_manifest.json").read_text())
    assert manifest["original_mock_fingerprint"]["sha256"] == digest(original_path)
    for record in records:
        source = originals[record["original_mock_case_id"]]
        assert record["original_mock_disposition"] == source["disposition"]
        assert record["original_anchor_record_sha256"] == hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        assert {m["task014_operation_id"] for m in record["members"]} == {m["task014_operation_id"] for m in source["candidate_members"]}


def test_member_ids_and_provenance_are_exact_accepted_records() -> None:
    operations = {v["semantic_operation_inventory_id"]: v for v in jsonl(ROOT / "indexes/semantic_operation_inventory.jsonl")}
    observed = {v["observed_function_id"]: v for v in jsonl(ROOT / "indexes/observed_function_inventory.jsonl")}
    for record in jsonl(EVIDENCE / "expanded_sample_register.jsonl"):
        for member in record["members"]:
            operation = operations[member["task014_operation_id"]]
            observation = observed[member["task015_observed_function_id"]]
            assert operation["canonical_api_id"] == member["canonical_api_id"]
            assert observation["task014_operation_record_id"] == member["task014_operation_id"]
            assert operation["source_provenance"] == member["source_provenance"]
            assert len(member["source_provenance"]["source_sha256"]) == 64


def test_rubric_and_three_axes_are_complete_and_independent() -> None:
    allowed = {"SUPPORTED", "CONTRADICTED", "NOT_EVIDENCED"}
    sufficiency = Counter()
    for record in jsonl(EVIDENCE / "expanded_sample_register.jsonl"):
        assert set(record["candidate_rubric"]) == {f"R{i}" for i in range(1, 8)}
        for value in record["candidate_rubric"].values():
            assert value["status"] in allowed and value["rationale"] and isinstance(value["evidence_refs"], list)
        for member in record["members"]:
            assert set(member["membership_rubric"]) == {f"R{i}" for i in range(1, 8)}
            assert all(v["status"] in allowed for v in member["membership_rubric"].values())
        axes = record["result_axes"]
        assert axes["technical_validation"] == "PASS"
        assert axes["architect_acceptance"] == "PENDING"
        sufficiency[axes["evidence_sufficiency"]] += 1
    assert sufficiency == {"INSUFFICIENT": 23, "PARTIAL": 19, "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY": 3, "SUPPORTED_SEPARATE": 1}


def test_required_strata_and_named_leads_are_present() -> None:
    records = jsonl(EVIDENCE / "expanded_sample_register.jsonl")
    strata = Counter(tag for v in records for tag in v["strata"])
    assert strata["DIFFERENT_ACTIONS"] >= 6 and strata["DIVERGENT_EXPOSURE"] >= 6
    assert strata["NEGATIVE_CONTROL"] >= 5 and strata["VERSION_VARIANT"] >= 5
    assert strata["MULTI_OPERATION_API"] >= 4 and strata["PRODUCT_CONTEXT"] >= 4
    named = [v for v in records if "NAMED_LEAD" in v["strata"]]
    assert len(named) == 6
    names = {m["api_name"] for v in named for m in v["members"]}
    assert {"user-management-privilege", "user-management", "getbasiccrinformation", "mcichangehistory", "verifyviolatedestablishment", "verifysaudizationcertificatevalidity", "osh-getcategorybyid", "getcategorybyid", "employeeauthind-v2", "contractauthenticationindicator", "qiwa-streaming-v2", "qiwa-streaming"} <= names


def test_sc_request_is_two_sources_three_intents_and_partial_only() -> None:
    sc = next(v for v in jsonl(EVIDENCE / "expanded_sample_register.jsonl") if v["candidate_boundary_label"] == "SC Request Workflow")
    assert len(sc["members"]) == 2
    assert {m["api_name"] for m in sc["members"]} == {"approverejectscrequest", "cancelscrequest"}
    assert {a for m in sc["members"] for a in m["supported_actions"]} == {"approve", "reject", "cancel"}
    assert {p for m in sc["members"] for p in m["backend"]["configured_paths"]} == {"/sc/apprejscreq", "/sc/cancelscreq"}
    assert all(m["backend"]["certainty"] == "CONFIGURED_API_SHARED_CANDIDATE" for m in sc["members"])
    assert len({tuple(m["product_plan_subscription_context"]["accepted_product_ids"]) for m in sc["members"]}) == 2
    assert len({tuple(m["product_plan_subscription_context"]["accepted_plan_ids"]) for m in sc["members"]}) == 2
    assert sc["result_axes"] == {"technical_validation": "PASS", "evidence_sufficiency": "PARTIAL", "architect_acceptance": "PENDING"}
    text = (EVIDENCE / "sc_request_deep_dive.md").read_text()
    assert "Unified SC Request Actions" in text and "Decision API" in text and "Cancellation API" in text


def test_false_positive_controls_do_not_promote_similarity_or_transitivity() -> None:
    records = jsonl(EVIDENCE / "expanded_sample_register.jsonl")
    negative = [v for v in records if "NEGATIVE_CONTROL" in v["strata"]]
    assert len(negative) >= 5
    assert all(v["result_axes"]["evidence_sufficiency"] in {"INSUFFICIENT", "SUPPORTED_SEPARATE"} for v in negative)
    for record in records:
        assert record["functional_equivalence_approved"] is False
        assert record["member_ids_collapsed"] is False
        assert record["transitive_equivalence_inferred"] is False
        assert record["product_is_logical_api"] is False
        assert all(m["backend"]["runtime_egress_proven"] is False for m in record["members"])
        if {"SHARED_SCHEMA", "SHARED_PATH", "COPIED_SEMANTICS"} & set(record["strata"]):
            assert record["result_axes"]["evidence_sufficiency"] != "SUFFICIENT_FOR_PROVISIONAL_BOUNDARY"


def test_no_unauthorized_architecture_or_production_claims() -> None:
    for record in jsonl(EVIDENCE / "expanded_sample_register.jsonl"):
        assert record["domain_assignment"] is None and record["capability_assignment"] is None
        assert record["kong_topology"] is None and record["retirement_decision"] is None
        assert record["production_usage_inferred"] is False
        assert all(m["product_is_logical_api"] is False and m["runtime_activity_proven"] is False for m in record["members"])
    coverage = json.loads((EVIDENCE / "sample_coverage_and_gaps.json").read_text())
    assert coverage["full_estate_coverage_claimed"] is False
    assert all(v["met"] for v in coverage["requirements"].values())


def test_regeneration_is_deterministic_redacted_and_frozen_safe() -> None:
    frozen = [ROOT / "tests/evidence/task-017/mock/representative_boundary_cases.jsonl", ROOT / "indexes/semantic_api_inventory.jsonl", ROOT / "indexes/semantic_operation_inventory.jsonl", ROOT / "indexes/observed_function_inventory.jsonl", ROOT / "indexes/task016_semantic_refinement_pairs.jsonl", ROOT / "indexes/task016_full_candidate_pairs.jsonl"]
    before = {path: digest(path) for path in frozen}
    command = [str(ROOT / ".venv/bin/python"), str(EVIDENCE / "generate_expanded_evidence.py")]
    subprocess.run(command, cwd=ROOT, check=True)
    first = {p.name: digest(p) for p in EVIDENCE.iterdir() if p.is_file()}
    subprocess.run(command, cwd=ROOT, check=True)
    assert first == {p.name: digest(p) for p in EVIDENCE.iterdir() if p.is_file()}
    assert before == {path: digest(path) for path in frozen}
    payload = b"".join(p.read_bytes() for p in EVIDENCE.iterdir() if p.is_file())
    assert b"http://" not in payload.lower() and b"https://" not in payload.lower()
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,;]+", payload.decode("utf-8"))
