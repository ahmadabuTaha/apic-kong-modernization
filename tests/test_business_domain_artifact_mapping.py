import csv
import json
from pathlib import Path

import business_domain.artifact_mapping as mapping
from business_domain.artifact_mapping import DOMAIN_REGISTRY, MODULE_RULES, OUTPUT_FILES, build_artifact_first_mapping


ROOT = Path(__file__).resolve().parents[1]


def _by_name(rows: list[dict], name: str) -> list[dict]:
    return [row for row in rows if row["artifact_name"].casefold() == name.casefold()]


def _normalized_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.pop("cache_telemetry")
    for output in value["outputs"].values():
        output.pop("path", None)
    return value


def test_exact_registry_source_and_inventory_closure(tmp_path: Path) -> None:
    result = build_artifact_first_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    assert len(result["registry"]) == 15 == len(DOMAIN_REGISTRY)
    assert [row["domain_name"] for row in result["registry"]][-5:] == ["TIP", "User Management", "Notification", "LO", "Utilities"]
    assert len(result["crosswalk"]) == 30 == len(MODULE_RULES)
    assert len(result["parents"]) == 993
    assert len(result["apis"]) == 2036 == len({row["canonical_api_id"] for row in result["apis"]})
    assert len(result["operations"]) == 2414 == len({row["operation_record_id"] for row in result["operations"]})
    assert len(result["zero"]) == 41
    assert set(OUTPUT_FILES) - {"coverage", "manifest"} <= set(result["manifest"]["outputs"])


def test_required_artifact_first_acceptance_scenarios(tmp_path: Path) -> None:
    result = build_artifact_first_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    apis = result["apis"]
    assert _by_name(apis, "user-management")[0]["primary_as_is_domain_candidate"] == "User Management"
    assert _by_name(apis, "user-management-privilege")[0]["primary_as_is_domain_candidate"] == "User Management"
    payment = _by_name(apis, "getpaymentdetails-v2")[0]
    assert payment["primary_as_is_domain_candidate"] == "Payment"
    assert payment["qiwa_relationship_certainty"] == "NO_MATCH"
    gosi = _by_name(apis, "gosi-generateaccesstoken")[0]
    assert gosi["primary_as_is_domain_candidate"] == "Utilities"
    assert _by_name(result["operations"], "gosi-generateaccesstoken")[0]["primary_as_is_domain_candidate"] == "Utilities"
    assert _by_name(result["operations"], "submitoccupationcorrectionrequest")[0]["primary_as_is_domain_candidate"] == "Occupation"
    assert _by_name(result["operations"], "getgosicontractslist")[0]["primary_as_is_domain_candidate"] == "Contracts"


def test_tip_lo_multidimensional_and_send_reports_controls(tmp_path: Path) -> None:
    result = build_artifact_first_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    qaas_contracts = [row for row in result["apis"] if row["artifact_name"].startswith("qaas_") and
                      row["underlying_functional_domain_candidate"] == "Contracts"]
    assert qaas_contracts and all(row["primary_as_is_domain_candidate"] == "TIP" for row in qaas_contracts)
    assert any(row["primary_as_is_domain_candidate"] == "LO" for row in result["apis"])
    send = _by_name(result["operations"], "sendqiwareports")
    assert send and not send[0]["primary_as_is_domain_candidate"]
    assert send[0]["configured_branch_count"] == 63
    assert all(row["runtime_use_proven"] == "false" and row["enterprise_domain_ratified"] == "false" for row in result["operations"])


def test_schema_direction_lifecycle_and_common_utility_separation(tmp_path: Path) -> None:
    result = build_artifact_first_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    assert {row["direction"] for row in result["schema"]} >= {"REQUEST", "RESPONSE"}
    assert all(row["ownership_limitation"] for row in result["schema"])
    assert result["poc_test"] and all(row["retirement_approved"] == "false" for row in result["poc_test"])
    assert all(row["api_lifecycle_purpose"] not in {row[1] for row in DOMAIN_REGISTRY} for row in result["apis"])
    assert any(row["common_reuse_classification"] == "COMMON_BY_5_PLUS_REUSE_RULE" for row in result["parents"])
    assert any(row["primary_as_is_domain_candidate"] == "Utilities" for row in result["utilities_common"])
    assert any(row["primary_as_is_domain_candidate"] == "Common" for row in result["utilities_common"])


def test_cold_warm_byte_equality_and_stage_cache(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cold_dir, warm_dir = tmp_path / "cold", tmp_path / "warm"
    cold = build_artifact_first_mapping(ROOT, cold_dir, cache)
    warm = build_artifact_first_mapping(ROOT, warm_dir, cache)
    assert cold["manifest"]["cache_telemetry"]["cache_miss_count"] == 12
    assert warm["manifest"]["cache_telemetry"]["cache_hit_count"] == 12
    assert warm["manifest"]["cache_telemetry"]["stages_rebuilt"] == []
    assert {path.name: path.read_bytes() for path in cold_dir.glob("*.csv")} == {
        path.name: path.read_bytes() for path in warm_dir.glob("*.csv")
    }
    assert (cold_dir / "coverage_report.md").read_bytes() == (warm_dir / "coverage_report.md").read_bytes()
    assert _normalized_manifest(cold_dir / "manifest.json") == _normalized_manifest(warm_dir / "manifest.json")


def test_rule_and_source_keys_are_independent(tmp_path: Path, monkeypatch) -> None:
    cache = tmp_path / "cache"
    build_artifact_first_mapping(ROOT, tmp_path / "base", cache)
    monkeypatch.setattr(mapping, "RULES_VERSION", "task018f-artifact-first-domain-mapping-test-rule")
    changed = build_artifact_first_mapping(ROOT, tmp_path / "changed", cache)
    rebuilt = set(changed["manifest"]["cache_telemetry"]["stages_rebuilt"])
    assert rebuilt == {
        "domain_module_crosswalk", "qiwa_parent_module_lookup", "domain_anchor_registry",
        "api_domain_evidence_cache", "operation_domain_evidence_cache",
    }
    assert changed["manifest"]["cache_telemetry"]["targeted_yaml_files_read"] == 0


def test_csv_schema_and_single_yaml_invalidation_are_stage_local(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    build_artifact_first_mapping(ROOT, tmp_path / "base", cache)
    changed_csv = tmp_path / "Qiwa_Modules_Services.csv"
    changed_csv.write_bytes((ROOT / "neo4j/csv/Qiwa_Modules_Services.csv").read_bytes() + b"\n")
    csv_run = build_artifact_first_mapping(ROOT, tmp_path / "csv", cache, {"qiwa_csv": changed_csv})
    assert set(csv_run["manifest"]["cache_telemetry"]["stages_rebuilt"]) == {
        "domain_module_crosswalk", "qiwa_parent_module_lookup", "artifact_parent_edges", "operation_parent_edges",
        "api_domain_evidence_cache", "operation_domain_evidence_cache",
    }
    changed_schema = tmp_path / "schema.jsonl"
    changed_schema.write_bytes((ROOT / "indexes/task018b_business_object_candidate_register.jsonl").read_bytes() + b"\n")
    schema_run = build_artifact_first_mapping(
        ROOT, tmp_path / "schema", cache, {"qiwa_csv": changed_csv, "schema_clues": changed_schema}
    )
    assert schema_run["manifest"]["cache_telemetry"]["stages_rebuilt"] == [
        "schema_business_object_clues", "api_domain_evidence_cache", "operation_domain_evidence_cache"
    ]
    assert mapping._key("branches", "yaml-a", parser=True) != mapping._key("branches", "yaml-b", parser=True)
    assert mapping._key("artifacts", "api-index") == mapping._key("artifacts", "api-index")


def test_outputs_are_secret_safe_and_do_not_import_old_labels(tmp_path: Path) -> None:
    result = build_artifact_first_mapping(ROOT, tmp_path / "out", tmp_path / "cache")
    assert result["manifest"]["independence"] == {
        "prior_task_domain_labels_used": False,
        "task018b_schema_labels_used": False,
        "task018b_factual_schema_extraction_used": True,
        "artifact_first": True,
    }
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "out").iterdir())
    assert "resolved_safe_target_expression" not in rendered
    assert "X-IBM-Client-Secret" not in rendered
    assert "http://" not in rendered and "https://" not in rendered
    assert not any("task018e" in str(path) for path in result["manifest"]["inputs"].values())
