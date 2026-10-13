from __future__ import annotations

import csv
import json
from pathlib import Path

from business_domain.qiwa_mapping import (
    DISTRIBUTION_FIELDS,
    EXPECTED_API_COUNT,
    EXPECTED_OPERATION_COUNT,
    build_qiwa_mapping,
    classify_backend,
    normalize_identity,
)


ROOT = Path(__file__).resolve().parents[1]


def _backend(host: str | None, *, status: str = "RESOLVED", tokens: list[str] | None = None) -> dict:
    return {
        "normalized_host_or_value_key": host,
        "resolution_status": status,
        "runtime_parameter_tokens": tokens or [],
    }


def test_backend_classification_ea_rule_and_dynamic_path() -> None:
    assert classify_backend([_backend("service.ace.svc.cluster.local", tokens=["request.path"])])[:2] == (
        "ACE_BACKEND", "PARTIALLY_RESOLVED_DYNAMIC_PATH"
    )
    assert classify_backend([_backend("external.example.invalid")])[:2] == (
        "EXTERNAL_VIA_DATAPOWER", "FULLY_RESOLVED"
    )
    assert classify_backend([_backend(None, status="UNRESOLVED")])[:2] == (
        "PLATFORM_UNRESOLVED", "UNRESOLVED"
    )
    assert classify_backend([_backend("a.ace.svc"), _backend("external.invalid")])[:2] == (
        "PLATFORM_UNRESOLVED", "CONFIGURATION_CONFLICT"
    )
    partly_missing = _backend("service.ace.svc", status="UNRESOLVED", tokens=["request.path"])
    partly_missing["non_runtime_property_unresolved"] = True
    assert classify_backend([partly_missing])[:2] == ("ACE_BACKEND", "UNRESOLVED")


def test_normalization_is_candidate_only_and_collision_visible() -> None:
    assert normalize_identity("Create_New-Contract ") == "createnewcontract"
    assert normalize_identity("create new contract") == "createnewcontract"


def test_full_estate_outputs_are_complete_deterministic_and_redacted(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = build_qiwa_mapping(ROOT, first_dir)
    second = build_qiwa_mapping(ROOT, second_dir)

    assert len(first["distribution"]) == EXPECTED_OPERATION_COUNT
    assert len({row["operation_record_id"] for row in first["distribution"]}) == EXPECTED_OPERATION_COUNT
    assert first["manifest"]["summary"]["canonical_api_count"] == EXPECTED_API_COUNT
    assert len(first["zero_apis"]) == 41
    api_operation_counts = [
        json.loads(line)["operation_count"]
        for line in (ROOT / "indexes/semantic_api_inventory.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert any(count == 0 for count in api_operation_counts)
    assert any(count == 1 for count in api_operation_counts)
    assert any(count >= 2 for count in api_operation_counts)
    assert len(first["ambiguous"]) == first["manifest"]["summary"]["ambiguous_review_row_count"]

    for name in ("operation_domain_distribution.csv", "domain_distribution_summary.csv", "ambiguous_operations.csv", "apic_qiwa_match_evidence.csv", "zero_operation_apis.csv"):
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()

    with (first_dir / "operation_domain_distribution.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == DISTRIBUTION_FIELDS
    assert len(rows) == EXPECTED_OPERATION_COUNT
    assert [row["operation_record_id"] for row in rows] == sorted(row["operation_record_id"] for row in rows)
    assert all(row["review_required"] == "true" for row in rows)
    assert all(not row["candidate_domain_bucket"] or row["join_tier"].startswith(("J1_", "J2_")) for row in rows)
    assert all(row["candidate_domain_bucket"] == row["source_qiwa_module"] for row in rows if row["candidate_domain_bucket"])
    assert all(row["backend_platform_classification"] == "ACE_BACKEND" for row in rows if row["candidate_domain_bucket"])

    summary = {row["candidate_domain_bucket"]: row for row in first["summary"]}
    source_modules = set(first["manifest"]["source_inventory"]["distinct_modules"])
    assert set(summary) == source_modules | {"Occupations", "TIP", "UNMAPPED"}
    assert summary["TIP"]["bucket_origin"] == "QIWA_CSV_AND_EA_NOMINATED_OVERLAP"
    assert summary["Occupations"]["operation_primary_count"] == 0

    rendered = "\n".join(path.read_text(encoding="utf-8") for path in first_dir.iterdir())
    assert "X-IBM-Client-Secret" not in rendered
    assert "resolved_safe_target_expression" not in rendered
    assert "safe_value" not in rendered
    assert all(row["runtime_egress_proven"] == "false" for row in first["evidence"])


def test_name_only_and_multi_match_cases_are_not_primary(tmp_path: Path) -> None:
    result = build_qiwa_mapping(ROOT, tmp_path)
    name_only = [row for row in result["distribution"] if row["join_tier"] == "J3_NAME_ONLY_CANDIDATE"]
    assert name_only
    assert all(not row["candidate_domain_bucket"] and row["assignment_status"] == "UNASSIGNED" for row in name_only)
    ambiguous = [row for row in result["distribution"] if row["join_tier"] == "JX_AMBIGUOUS"]
    assert ambiguous
    assert all(not row["candidate_domain_bucket"] for row in ambiguous)


def test_manifest_preserves_source_identity_and_018b_independence(tmp_path: Path) -> None:
    before = (ROOT / "indexes/task018b_operation_domain_initial_mapping.jsonl").read_bytes()
    result = build_qiwa_mapping(ROOT, tmp_path)
    after = (ROOT / "indexes/task018b_operation_domain_initial_mapping.jsonl").read_bytes()
    inventory = result["manifest"]["source_inventory"]
    assert inventory["row_count"] == 4437
    assert inventory["unique_id_count"] == 4437
    assert inventory["endpoint_or_url_columns_present"] == []
    assert result["manifest"]["stop_gate"] == "EA_REVIEW_TASK018C"
    assert before == after
    assert json.loads((tmp_path / "manifest.json").read_text())["guardrails"]["enterprise_domain_ratified"] is False
