import csv
import json
from pathlib import Path

import business_domain.topdown_mapping as mapping
from business_domain.topdown_mapping import (
    DOMAIN_REGISTRY,
    GENERIC_KEYS,
    MODULE_RULES,
    _hash,
    _key,
    _technical_key,
    build_topdown_mapping,
    normalize,
)


ROOT = Path(__file__).resolve().parents[1]


def _csv_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.glob("*.csv")}


def _normalized_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.pop("cache_telemetry")
    for output in value["outputs"].values():
        output.pop("path", None)
    return value


def test_registry_crosswalk_and_parent_inventory_close_source_vocabulary(tmp_path: Path) -> None:
    result = build_topdown_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    assert len(result["registry"]) == 14 == len(DOMAIN_REGISTRY)
    assert [row["ea_area_code"] for row in result["registry"]] == [f"D{number:02d}" for number in range(1, 15)]
    assert len(result["crosswalk"]) == 30 == len(MODULE_RULES)
    assert {row["source_module_name"] for row in result["crosswalk"]} == set(MODULE_RULES)
    decease = next(row for row in result["crosswalk"] if row["source_module_name"] == "Decease Mgmt")
    assert (decease["ea_area_name"], decease["mapping_method"]) == ("WorkForce", "EA_EXPLICIT")
    assert all(row["source_row_ids"] and row["source_reference"] for row in result["parents"])


def test_full_coverage_named_anchors_and_parallel_dimensions(tmp_path: Path) -> None:
    result = build_topdown_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    ledger = result["ledger"]
    assert len(ledger) == 2414 == len({row["operation_record_id"] for row in ledger})
    assert result["manifest"]["coverage"]["canonical_api_count"] == 2036
    assert len(result["zero"]) == 41

    by_api = {}
    for row in ledger:
        by_api.setdefault(row["canonical_api_name"], []).append(row)
    assert by_api["submitoccupationcorrectionrequest"][0]["primary_domain_candidate"] == "Occupation"
    assert {row["primary_domain_candidate"] for row in by_api["getgosicontractslist"]} == {"Contracts"}
    assert by_api["submitworkpermitrequest"][0]["primary_domain_candidate"] == "Work Permit"
    assert by_api["updateestablishmentcontactaddress"][0]["name_match_tier"] == "N5_SUPPORTING_NAME_PATH_CANDIDATE"
    assert by_api["validateissueestablishingvisas"][0]["primary_domain_candidate"] == "Visa"
    report = by_api["sendqiwareports"][0]
    report_branches = [row for row in result["branches"] if row["operation_record_id"] == report["operation_record_id"]]
    assert len(report_branches) > 1
    assert len({domain for row in report_branches for domain in row["origin_domain_candidates"].split("|") if domain}) > 1
    assert report["primary_domain_candidate"] == ""

    assert any(row["tip_exposure_status"] == "TIP_EXPOSURE_CONFIRMED" and row["tip_exposure_evidence_refs"] for row in result["tip"])
    assert any(row["lo_as_is_status"] == "LO_AS_IS_CONFIRMED" for row in result["lo"])
    assert all(row["runtime_usage_proven"] == "false" and row["enterprise_domain_ratified"] == "false" for row in ledger)


def test_common_thresholds_generic_negative_control_and_multifunction_inheritance(tmp_path: Path) -> None:
    result = build_topdown_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    by_count = {int(row["distinct_consuming_module_count"]): row["shared_reuse_classification"] for row in result["shared"]}
    assert by_count[1] == "MODULE_LOCAL"
    assert by_count[4] == "CROSS_MODULE_SHARED_ORIGIN_RETAINED"
    assert by_count[5] == "COMMON_BY_REUSE_RULE"
    assert all(not (normalize(row["operation_name"]) in GENERIC_KEYS and row["name_match_tier"] != "NO_NAME_MATCH") for row in result["ledger"])
    inherited_multi = [row for row in result["ledger"] if "INHERITED_ARTIFACT_CANDIDATE_REQUIRES_OPERATION_REVIEW" in row["unresolved_or_review_flags"]]
    assert inherited_multi
    assert all(not row["primary_domain_candidate"] for row in inherited_multi)


def test_cold_warm_csv_determinism_and_equivalent_manifest(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cold_out, warm_out = tmp_path / "cold", tmp_path / "warm"
    cold = build_topdown_mapping(ROOT, cold_out, cache)
    warm = build_topdown_mapping(ROOT, warm_out, cache)
    assert cold["manifest"]["cache_telemetry"]["cache_miss_count"] == 8
    assert warm["manifest"]["cache_telemetry"]["cache_hit_count"] == 8
    assert warm["manifest"]["cache_telemetry"]["stages_rebuilt"] == []
    assert _csv_bytes(cold_out) == _csv_bytes(warm_out)
    assert (cold_out / "coverage_report.md").read_bytes() == (warm_out / "coverage_report.md").read_bytes()
    assert _normalized_manifest(cold_out / "manifest.json") == _normalized_manifest(warm_out / "manifest.json")


def test_changed_csv_and_mapping_invalidate_only_descendants(tmp_path: Path, monkeypatch) -> None:
    cache = tmp_path / "cache"
    build_topdown_mapping(ROOT, tmp_path / "base", cache)
    changed_csv = tmp_path / "Qiwa_Modules_Services.csv"
    changed_csv.write_bytes((ROOT / "neo4j/csv/Qiwa_Modules_Services.csv").read_bytes() + b"\n")
    changed = build_topdown_mapping(ROOT, tmp_path / "changed", cache, {"qiwa_csv": changed_csv})
    assert set(changed["manifest"]["cache_telemetry"]["stages_rebuilt"]) == {"crosswalk", "parents", "artifact_matches", "operation_matches"}
    assert changed["manifest"]["cache_telemetry"]["cache_hit_count"] == 4

    monkeypatch.setattr(mapping, "RULES_VERSION", "task018e-top-down-domain-mapping-test-change")
    mapped = build_topdown_mapping(ROOT, tmp_path / "mapping", cache, {"qiwa_csv": changed_csv})
    assert set(mapped["manifest"]["cache_telemetry"]["stages_rebuilt"]) == {"crosswalk", "parents"}
    assert mapped["manifest"]["cache_telemetry"]["targeted_yaml_files_read"] == 0


def test_single_yaml_hash_changes_only_assembly_key() -> None:
    source = ROOT / "staging/apis/_catalog/sendqiwareports_3.0.0.yaml"
    original = _hash(source)
    changed = "0" * 64 if original != "0" * 64 else "1" * 64
    assert _technical_key("assembly_branches", original) != _technical_key("assembly_branches", changed)
    assert _technical_key("backends", "backend", "catalog") == _technical_key("backends", "backend", "catalog")
    assert _key("crosswalk", "csv") != _technical_key("assembly_branches", "csv")


def test_outputs_are_secret_safe_and_do_not_read_prior_candidate_outputs(tmp_path: Path) -> None:
    result = build_topdown_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    assert result["manifest"]["independence"] == {
        "task018b_inputs_used": False, "task018c_inputs_used": False, "task018d_inputs_used": False,
        "prior_candidate_assignments_used": False,
    }
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "out").iterdir())
    assert "resolved_safe_target_expression" not in rendered
    assert "safe_value" not in rendered
    assert "X-IBM-Client-Secret" not in rendered
    assert "http://" not in rendered and "https://" not in rendered
