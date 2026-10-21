import csv
import json
from pathlib import Path

from capability_kg.inventory_normalization import (
    CSV_FIELDS,
    EXPECTED_COLUMNS,
    _normalize,
    _render_tables,
    build_common_inventory,
)


ROOT = Path(__file__).resolve().parents[1]


def _fixture(path: Path) -> Path:
    rows = [
        ["Common", "ignored", "One Each", "https://example.test/wiki/spaces/QI/pages/101", "https://example.test/wiki/spaces/QI/pages/201"],
        ["Common", "ignored", "One Plus Two", "https://example.test/wiki/spaces/QI/pages/102", "https://example.test/wiki/spaces/QI/pages/202; https://example.test/wiki/spaces/QI/pages/203"],
        ["Common", "ignored", "ICDs Only", " ref-A ; ;ref-B;ref-A ", ""],
        ["Common", "ignored", "ISD Only", "", "ref-C"],
        ["Common", "ignored", "Neither", "", ""],
        ["Common", "audit-two", "One Each", "https://example.test/wiki/spaces/QI/pages/101/Page-Title", "bad reference value"],
        ["Common", "ignored", "A B", "ref-D", ""],
        ["Common", "ignored", "A-B", "ref-E", ""],
        ["Common!", "ignored", "Other Module", "ref-F", ""],
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)
    return path


def test_fixture_cardinalities_duplicates_blanks_and_collisions(tmp_path: Path) -> None:
    source = _fixture(tmp_path / "services_icd_isd_inventory.csv")
    normalized = _normalize(source, pilot_module=None)
    counts = normalized["counts"]
    assert counts["pilot_source_rows"] == 9
    assert counts["reference_occurrences_before_normalization"] == 14
    assert counts["accepted_reference_occurrences"] == 13
    assert counts["rejected_reference_occurrences"] == 1
    assert counts["duplicate_reference_occurrence"] == 2
    assert counts["identity_collision"] == 11  # every affected row retains an explicit exception
    assert counts["blank_reference"] >= 1
    assert len(normalized["tables"]["source_rows.csv"]) == 9
    one_each = [row for row in normalized["tables"]["services.csv"] if row["service_name"] == "One Each"][0]
    assert one_each["source_row_count"] == 2
    assert one_each["source_row_references"] == "2;7"
    assert len({row["module_key"] for row in normalized["tables"]["modules.csv"]}) == 2
    ab_keys = {
        row["service_key"] for row in normalized["tables"]["services.csv"] if row["service_name"] in {"A B", "A-B"}
    }
    assert len(ab_keys) == 2


def test_common_pilot_only_and_lossless_reference_reconciliation(tmp_path: Path) -> None:
    source = _fixture(tmp_path / "services_icd_isd_inventory.csv")
    normalized = _normalize(source)
    assert {row["module_name"] for row in normalized["tables"]["modules.csv"]} == {"Common"}
    assert normalized["counts"]["pilot_source_rows"] == 8
    assert normalized["counts"]["reference_occurrences_before_normalization"] == (
        normalized["counts"]["accepted_reference_occurrences"] +
        normalized["counts"]["rejected_reference_occurrences"]
    )
    source_rows = normalized["tables"]["source_rows.csv"]
    assert source_rows[0]["raw_sub_module_audit_only"] == "ignored"
    assert all("sub_module" not in field for name, fields in CSV_FIELDS.items() if name != "source_rows.csv" for field in fields)


def test_document_identifiers_are_sanitized_and_edges_retain_occurrences(tmp_path: Path) -> None:
    normalized = _normalize(_fixture(tmp_path / "services_icd_isd_inventory.csv"))
    documents = normalized["tables"]["documents.csv"]
    rendered_public_indexes = b"\n".join(
        value for name, value in _render_tables(normalized).items() if name != "source_rows.csv"
    ).decode("utf-8")
    assert any(row["reference_identifier"] == "confluence_page_id:101" for row in documents)
    assert "https://" not in rendered_public_indexes
    edges_101 = [
        row for row in normalized["tables"]["service_document_edges.csv"]
        if any(doc["document_key"] == row["document_key"] and doc["reference_identifier"] == "confluence_page_id:101"
               for doc in documents)
    ]
    assert len(edges_101) == 2


def test_real_build_is_byte_deterministic_and_manifest_is_valid(tmp_path: Path) -> None:
    first_indexes, first_outputs = tmp_path / "indexes-a", tmp_path / "outputs-a"
    second_indexes, second_outputs = tmp_path / "indexes-b", tmp_path / "outputs-b"
    first = build_common_inventory(ROOT, index_dir=first_indexes, output_dir=first_outputs)
    second = build_common_inventory(ROOT, index_dir=second_indexes, output_dir=second_outputs)
    assert first["deterministic"] is second["deterministic"] is True
    assert {path.name: path.read_bytes() for path in first_indexes.iterdir()} == {
        path.name: path.read_bytes() for path in second_indexes.iterdir()
    }
    assert {path.name: path.read_bytes() for path in first_outputs.iterdir()} == {
        path.name: path.read_bytes() for path in second_outputs.iterdir()
    }
    manifest = json.loads((first_outputs / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scope"] == {"pilot_module": "Common", "sub_module_used_for_identity_or_classification": False}
    assert manifest["validations"]["documents_fetched"] is False
    assert manifest["counts"]["pilot_source_rows"] == len(first["tables"]["source_rows.csv"])


def test_required_headers_are_strict(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("Module,Service,ICD,ISD\nCommon,S,I,D\n", encoding="utf-8")
    try:
        _normalize(source)
    except ValueError as exc:
        assert "Unexpected columns" in str(exc)
    else:
        raise AssertionError("bad headers were accepted")
