import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from business_capability_kg.inventory_normalization import (
    CSV_FIELDS,
    EXPECTED_COLUMNS,
    MODULE_COVERAGE_FIELDS,
    _normalize,
    build_all_modules_inventory,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/services_icd_isd_inventory.csv"
COMMON_BASELINE = ROOT / "indexes/capability_kg/015a"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(path: Path) -> Path:
    rows = [
        ["Alpha", "ignored-a", "Shared Name", "ref-a; ;ref-b", ""],
        ["Alpha", "ignored-b", "Zero Docs", "", ""],
        ["Beta", "ignored-a", "Shared Name", "ref-a", "ref-c;bad reference"],
        ["Beta", "ignored-a", "A B", "ref-d", ""],
        ["Beta", "ignored-a", "A-B", "ref-e", ""],
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)
    return path


def test_all_module_fixture_preserves_cardinality_scope_and_diagnostics(tmp_path: Path) -> None:
    result = _normalize(_fixture(tmp_path / "inventory.csv"), pilot_module=None)
    assert result["counts"]["pilot_source_rows"] == 5
    assert result["counts"]["modules"] == 2
    assert result["counts"]["reference_occurrences_before_normalization"] == 7
    assert result["counts"]["accepted_reference_occurrences"] == 6
    assert result["counts"]["rejected_reference_occurrences"] == 1
    shared = [row for row in result["tables"]["services.csv"] if row["service_name"] == "Shared Name"]
    assert len(shared) == 2
    assert len({row["service_key"] for row in shared}) == 2
    assert result["counts"]["identity_collision"] == 2
    assert result["counts"]["blank_reference"] >= 1
    assert result["counts"]["invalid_reference_format"] == 1
    assert all("raw_sub_module" not in field for name, fields in CSV_FIELDS.items()
               if name != "source_rows.csv" for field in fields)


def test_literal_module_labels_remain_distinct_when_normalized_keys_collide(tmp_path: Path) -> None:
    source = tmp_path / "literal-modules.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows([
            ["Module A", "ignored", "Same Service", "ref-a", ""],
            [" Module A ", "ignored", "Same Service", "ref-b", ""],
        ])
    result = _normalize(source, pilot_module=None)
    assert {row["module_name"] for row in result["tables"]["modules.csv"]} == {"Module A", " Module A "}
    assert len({row["module_key"] for row in result["tables"]["modules.csv"]}) == 2
    assert result["counts"]["identity_collision"] == 2


def test_real_full_coverage_and_module_index(tmp_path: Path) -> None:
    result = build_all_modules_inventory(ROOT, index_dir=tmp_path / "indexes", output_dir=tmp_path / "outputs")
    manifest = result["manifest"]
    counts = manifest["counts"]
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    assert counts["source_data_rows"] == counts["processed_source_rows"] == len(source_rows) == 952
    assert counts["modules"] == len({row["Module"] for row in source_rows}) == 32
    assert counts["services"] == 952
    assert counts["source_reference_occurrences"] == 1941
    assert counts["accepted_reference_occurrences"] + counts["rejected_reference_occurrences"] == 1941
    assert counts["icd_reference_occurrences"] + counts["isd_reference_occurrences"] == 1941
    assert manifest["validations"]["module_coverage_closure"] is True
    assert [row["module_name"] for row in result["tables"]["modules.csv"]] == sorted(
        {row["Module"] for row in source_rows}, key=lambda name: next(
            item["module_key"] for item in result["tables"]["modules.csv"] if item["module_name"] == name
        )
    )
    with (tmp_path / "indexes/module_coverage.csv").open(encoding="utf-8", newline="") as stream:
        coverage = list(csv.DictReader(stream))
        assert stream.closed is False
    assert len(coverage) == 32
    assert list(coverage[0]) == MODULE_COVERAGE_FIELDS
    assert sum(int(row["source_row_count"]) for row in coverage) == 952


def test_common_regression_compares_every_accepted_index(tmp_path: Path) -> None:
    result = build_all_modules_inventory(ROOT, index_dir=tmp_path / "indexes", output_dir=tmp_path / "outputs")
    regression = result["manifest"]["common_regression"]
    assert regression["status"] == "PASS"
    assert regression["counts"] == {"source_rows": 116, "services": 116, "reference_occurrences": 225}
    assert set(regression["files"]) == set(CSV_FIELDS)
    assert all(item["byte_equal"] for item in regression["files"].values())
    assert all(_hash(COMMON_BASELINE / name) == item["projected_sha256"]
               for name, item in regression["files"].items())


def test_two_runs_are_byte_identical_and_outputs_are_sanitized(tmp_path: Path) -> None:
    source_hash = _hash(SOURCE)
    first_index, first_output = tmp_path / "index-a", tmp_path / "output-a"
    second_index, second_output = tmp_path / "index-b", tmp_path / "output-b"
    first = build_all_modules_inventory(ROOT, index_dir=first_index, output_dir=first_output)
    second = build_all_modules_inventory(ROOT, index_dir=second_index, output_dir=second_output)
    assert {path.name: path.read_bytes() for path in first_index.iterdir()} == {
        path.name: path.read_bytes() for path in second_index.iterdir()
    }
    assert {path.name: path.read_bytes() for path in first_output.iterdir()} == {
        path.name: path.read_bytes() for path in second_output.iterdir()
    }
    public_text = "\n".join(
        path.read_text(encoding="utf-8") for path in [*first_index.iterdir(), *first_output.iterdir()]
        if path.name != "source_rows.csv"
    )
    assert "http://" not in public_text and "https://" not in public_text
    assert "password" not in public_text.casefold() and "client_secret" not in public_text.casefold()
    assert first["manifest"] == second["manifest"]
    assert _hash(SOURCE) == source_hash


def test_all_modules_cli_and_manifest_hashes(tmp_path: Path) -> None:
    index_dir, output_dir = tmp_path / "indexes", tmp_path / "outputs"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "business_capability_kg.all_modules_inventory",
            "--root",
            str(ROOT),
            "--index-dir",
            str(index_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["modules"] == 32
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["outputs"].items():
        local = index_dir / Path(relative).name if "/indexes/" in f"/{relative}" else output_dir / Path(relative).name
        assert _hash(local) == expected
    assert manifest["input"]["parse_count"] == 1
    assert manifest["scope"]["pilot_filter"] is None
