from __future__ import annotations

import csv
import json
from pathlib import Path

from business_domain.independent_mapping import (
    DOMAINS,
    INPUTS,
    MODULE_RULES,
    _shared_reuse,
    build_independent_mapping,
    build_module_crosswalk,
    classify_identity_outcome,
    enrich_backend,
)


ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_crosswalk_closes_actual_modules_and_exact_13_area_vocabulary() -> None:
    rows = _read_csv(ROOT / "neo4j/csv/Qiwa_Modules_Services.csv")
    crosswalk = build_module_crosswalk(rows)
    assert len(crosswalk) == 30
    assert {row["source_qiwa_module"] for row in crosswalk} == {row["Module_Name"] for row in rows}
    assert set(DOMAINS) == {
        "Establishment", "Contracts", "Visa", "WorkForce", "Work Permit", "Payment",
        "Occupation", "Nitaqat", "Certificate", "Common", "TIP", "User Management", "Notification",
    }
    assert next(row for row in crosswalk if row["source_qiwa_module"] == "LO")["mapping_status"] == "MODULE_MAPPING_UNRESOLVED"
    assert next(row for row in crosswalk if row["source_qiwa_module"] == "TIP")["mapping_status"] == "MODULE_MAPPING_REVIEW_REQUIRED"


def test_backend_host_platform_is_independent_from_dynamic_path_resolution() -> None:
    prop = {
        "catalog-property:test": {
            "catalog_property_record_id": "catalog-property:test",
            "safe_value": "http://work.ace.svc.cluster.local:7800",
            "value_classification": "SAFE_NON_SECRET",
        }
    }
    dynamic = enrich_backend({
        "normalized_host_or_value_key": None, "runtime_parameter_tokens": ["request.path"],
        "property_lookup_results": [{"lookup_status": "RESOLVED", "symbolic_property_name": "ace-work", "property_record_ids": ["catalog-property:test"]}],
    }, prop)
    assert (dynamic["_platform"], dynamic["_target_resolution"]) == ("ACE_BACKEND", "PARTIALLY_RESOLVED_DYNAMIC_PATH")
    external = enrich_backend({"normalized_host_or_value_key": "external.example.invalid", "runtime_parameter_tokens": [], "property_lookup_results": []}, {})
    unresolved = enrich_backend({"normalized_host_or_value_key": None, "runtime_parameter_tokens": [], "property_lookup_results": []}, {})
    assert external["_platform"] == "EXTERNAL_VIA_DATAPOWER"
    assert unresolved["_platform"] == "PLATFORM_UNRESOLVED"


def test_true_ambiguity_is_distinct_from_no_match_and_multibranch() -> None:
    assert classify_identity_outcome(set()) == "NO_MATCH_EVIDENCED"
    assert classify_identity_outcome({"one"}) == "CONFIRMED_EXPLICIT_ROUTE"
    assert classify_identity_outcome({"one", "two"}) == "AMBIGUOUS_IDENTITY"
    assert classify_identity_outcome(set(), contradictory=True) == "CONTRADICTORY_EVIDENCE"


def test_common_reuse_threshold_dedupes_repeated_rows_from_same_module() -> None:
    modules = ["EFM", "Contract Mgmt", "Visa Mgmt", "ET", "Work Permit"]
    rows = []
    row_id = 1
    for module in modules:
        rows.append({"ID": str(row_id), "Service_Name": "SharedFive", "Type": "API-HTTP", "Parent_Service": f"Parent{row_id}", "Module_Name": module})
        row_id += 1
    rows.extend([
        {"ID": str(row_id), "Service_Name": "SharedFour", "Type": "DP", "Parent_Service": "A", "Module_Name": module}
        for module in modules[:4]
    ])
    row_id += 4
    rows.extend([
        {"ID": str(row_id), "Service_Name": "RepeatedLocal", "Type": "SP", "Parent_Service": "P1", "Module_Name": "EFM"},
        {"ID": str(row_id + 1), "Service_Name": "RepeatedLocal", "Type": "SP", "Parent_Service": "P2", "Module_Name": "EFM"},
    ])
    crosswalk = {
        module: {"candidate_enterprise_business_domain": MODULE_RULES[module][0], "mapping_status": MODULE_RULES[module][1]}
        for module in modules
    }
    reuse, _ = _shared_reuse(rows, {}, crosswalk)
    by_name = {row["original_service_names"]: row for row in reuse}
    assert by_name["SharedFive"]["shared_reuse_classification"] == "COMMON_BY_REUSE_RULE"
    assert by_name["SharedFour"]["shared_reuse_classification"] == "CROSS_MODULE_SHARED_ORIGIN_RETAINED"
    assert by_name["RepeatedLocal"]["distinct_consuming_module_count"] == 1
    assert by_name["RepeatedLocal"]["shared_reuse_classification"] == "MODULE_LOCAL"


def test_full_build_is_independent_complete_deterministic_and_secret_safe(tmp_path: Path) -> None:
    assert all("018b" not in str(path).lower() and "018c" not in str(path).lower() for path in INPUTS.values())
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    first = build_independent_mapping(ROOT, first_dir)
    second = build_independent_mapping(ROOT, second_dir)
    assert len(first["operations"]) == 2414 == len({row["operation_record_id"] for row in first["operations"]})
    assert first["manifest"]["summary"]["canonical_api_count"] == 2036
    assert len(first["zero_apis"]) == 41
    assert first["manifest"]["independence"] == {"task018b_inputs_used": False, "task018c_inputs_used": False, "historical_outcomes_used_as_labels": False}
    for filename in first["manifest"]["outputs"]:
        if filename == "reviewer":
            continue
        actual = first["manifest"]["outputs"][filename]["path"]
        name = Path(actual).name
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in first_dir.iterdir())
    assert "resolved_safe_target_expression" not in rendered
    assert "safe_value" not in rendered
    assert "X-IBM-Client-Secret" not in rendered
    assert "http://" not in rendered and "https://" not in rendered


def test_named_validation_anchors_preserve_ownership_without_inventing_joins(tmp_path: Path) -> None:
    result = build_independent_mapping(ROOT, tmp_path)
    operations = result["operations"]
    by_name: dict[str, list[dict]] = {}
    for row in operations:
        by_name.setdefault(row["canonical_api_name"], []).append(row)

    report = by_name["sendqiwareports"][0]
    assert report["match_and_evidence_status"] == "MULTI_BRANCH_CONFIRMED"
    assert report["operation_business_domain_candidate"] == ""
    report_branches = [row for row in result["branches"] if row["operation_record_id"] == report["operation_record_id"]]
    assert len(report_branches) > 1
    assert any("SubmitOccupationCorrectionRequestRq" in row["branch_selector_or_flag"] for row in report_branches)

    occupation = by_name["submitoccupationcorrectionrequest"][0]
    contracts = next(row for row in by_name["getgosicontractslist"] if row["operation_id"] == "GetGosiContractsList")
    establishment = by_name["updateestablishmentcontactaddress"][0]
    visa = by_name["validateissueestablishingvisas"][0]
    permit = by_name["submitworkpermitrequest"][0]
    assert occupation["operation_business_domain_candidate"] == "" and occupation["candidate_domain_alternatives"] == "Occupation"
    assert contracts["operation_business_domain_candidate"] == "" and contracts["candidate_domain_alternatives"] == "Contracts"
    assert establishment["candidate_domain_alternatives"] == "Establishment"
    assert visa["candidate_domain_alternatives"] == "Visa"
    assert permit["candidate_domain_alternatives"] == "Work Permit"
    permit_types = {row["child_type"] for row in result["matches"] if row["operation_record_id"] == permit["operation_record_id"]}
    assert {"API-HTTP", "DP"} <= permit_types


def test_generic_route_name_matches_never_become_confirmed_without_switch_identifier(tmp_path: Path) -> None:
    result = build_independent_mapping(ROOT, tmp_path)
    confirmed = [row for row in result["matches"] if row["join_category"].startswith("CONFIRMED")]
    assert confirmed
    assert all("exact switch root flag" in row["match_limitations"] for row in confirmed)
    candidates = [row for row in result["matches"] if row["join_category"] == "CANDIDATE_NAME_MATCH"]
    assert candidates
    assert all("CSV has no route evidence" in row["match_limitations"] or "DP correlation" in row["match_limitations"] for row in candidates)


def test_tip_exposure_is_configuration_based_and_does_not_replace_domain(tmp_path: Path) -> None:
    result = build_independent_mapping(ROOT, tmp_path)
    confirmed = [row for row in result["tip"] if row["tip_exposure_status"] == "TIP_EXPOSURE_CONFIRMED"]
    candidates = [row for row in result["tip"] if row["tip_exposure_status"] == "TIP_EXPOSURE_CANDIDATE"]
    assert confirmed and candidates
    assert all(row["tip_exposure_evidence_refs"] for row in confirmed)
    assert any(row["independent_business_domain_candidate"] != "TIP" for row in confirmed)
    assert all(row["multi_channel_preserved"] == "true" for row in result["tip"])


def test_outputs_separate_true_ambiguity_from_unmatched(tmp_path: Path) -> None:
    result = build_independent_mapping(ROOT, tmp_path)
    assert len(result["unmatched"]) == sum(not any(
        match["operation_record_id"] == row["operation_record_id"] and match["join_category"].startswith("CONFIRMED")
        for match in result["matches"]
    ) for row in result["operations"])
    assert all(row["match_and_evidence_status"] in {"AMBIGUOUS_IDENTITY", "CONTRADICTORY_EVIDENCE"} for row in result["ambiguous"])
    assert len(result["summary"]) == 15
    assert [row["classification_area"] for row in result["summary"][:13]] == list(DOMAINS)
