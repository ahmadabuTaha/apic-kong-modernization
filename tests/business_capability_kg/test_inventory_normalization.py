import hashlib
import json
import subprocess
import sys
from pathlib import Path

import capability_kg.inventory_normalization as legacy
import business_capability_kg.inventory_normalization as phase6


ROOT = Path(__file__).resolve().parents[2]
BASELINE_INDEX = ROOT / "indexes/capability_kg/015a"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_legacy_imports_forward_to_owned_phase6_implementation() -> None:
    assert legacy.build_common_inventory is phase6.build_common_inventory
    assert legacy._normalize is phase6._normalize
    assert legacy.main is phase6.legacy_main


def test_consolidation_copies_accepted_baseline_without_reparsing(tmp_path: Path, monkeypatch) -> None:
    def forbidden_normalizer(*args: object, **kwargs: object) -> None:
        raise AssertionError("Task 019-A must not rerun accepted normalization")

    monkeypatch.setattr(phase6, "_normalize", forbidden_normalizer)
    result = phase6.consolidate_accepted_baseline(ROOT, tmp_path / "indexes", tmp_path / "outputs")
    manifest = result["manifest"]
    assert manifest["source_baseline"] == "Capability-KG/015-A"
    assert manifest["status"] == "EA_REVIEW_TASK019A"
    assert manifest["counts"]["pilot_source_rows"] == 116
    assert manifest["counts"]["services"] == 116
    assert manifest["counts"]["accepted_reference_occurrences"] == 225
    assert manifest["validations"]["normalizer_rerun"] is False
    for name in phase6.CSV_FIELDS:
        assert (tmp_path / "indexes" / name).read_bytes() == (BASELINE_INDEX / name).read_bytes()


def test_consolidation_is_deterministic_and_preserves_historical_files(tmp_path: Path) -> None:
    protected = [
        *sorted(BASELINE_INDEX.iterdir()),
        ROOT / "outputs/capability_kg/015a/manifest.json",
        ROOT / "outputs/capability_kg/015a/validation_summary.md",
        ROOT / "outputs/services_icd_isd_inventory.csv",
    ]
    before = {path: _hash(path) for path in protected}
    phase6.consolidate_accepted_baseline(ROOT, tmp_path / "index-a", tmp_path / "output-a")
    phase6.consolidate_accepted_baseline(ROOT, tmp_path / "index-b", tmp_path / "output-b")
    assert {path.name: path.read_bytes() for path in (tmp_path / "index-a").iterdir()} == {
        path.name: path.read_bytes() for path in (tmp_path / "index-b").iterdir()
    }
    assert {path.name: path.read_bytes() for path in (tmp_path / "output-a").iterdir()} == {
        path.name: path.read_bytes() for path in (tmp_path / "output-b").iterdir()
    }
    assert before == {path: _hash(path) for path in protected}


def test_phase6_cli_uses_task_scoped_destinations(tmp_path: Path) -> None:
    index_dir, output_dir = tmp_path / "indexes", tmp_path / "outputs"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "business_capability_kg",
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
    assert json.loads(completed.stdout)["accepted_reference_occurrences"] == 225
    assert {path.name for path in index_dir.iterdir()} == set(phase6.CSV_FIELDS)
    assert {path.name for path in output_dir.iterdir()} == {"manifest.json", "validation_summary.md"}


def test_legacy_cli_remains_source_equivalent(tmp_path: Path) -> None:
    index_dir, output_dir = tmp_path / "legacy-indexes", tmp_path / "legacy-outputs"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "capability_kg",
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
    assert json.loads(completed.stdout)["pilot_source_rows"] == 116
    for name in phase6.CSV_FIELDS:
        assert (index_dir / name).read_bytes() == (BASELINE_INDEX / name).read_bytes()


def test_manifest_mapping_and_roadmap_are_bounded_to_019a(tmp_path: Path) -> None:
    result = phase6.consolidate_accepted_baseline(ROOT, tmp_path / "indexes", tmp_path / "outputs")
    manifest = result["manifest"]
    assert manifest["path_mapping"]["indexes_new"] == "indexes/phase6/task019/019a"
    assert manifest["path_mapping"]["outputs_new"] == "outputs/phase6/task019/019a"
    assert all(item["byte_equal"] and item["semantic_equal"] for item in manifest["files"].values())
    summary = result["summary"].decode("utf-8")
    assert "019-B document acquisition" in summary
    assert "not authorization to implement later tasks" in summary
    assert "No document fetch" in summary
