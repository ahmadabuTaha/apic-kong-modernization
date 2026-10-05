import hashlib
import json
from pathlib import Path

import pytest

from repository_profiler.profiler import profile_repository


FIXTURE_SOURCE = Path(__file__).parent / "fixtures/repository_profile/staging"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def generated(tmp_path: Path) -> tuple[dict, Path]:
    return profile_repository(FIXTURE_SOURCE, tmp_path), tmp_path


def test_smoke_profile_generates_all_artifacts(generated: tuple[dict, Path]) -> None:
    profile, output = generated
    expected = [
        "indexes/file_index.jsonl",
        "outputs/repository_profile/repository_profile.json",
        "outputs/parse_errors/parse_errors.jsonl",
        "outputs/duplicates/exact_duplicate_files.jsonl",
        "outputs/schema_families/schema_families.json",
    ]
    assert all((output / path).is_file() for path in expected)
    assert profile == json.loads(
        (output / "outputs/repository_profile/repository_profile.json").read_text()
    )
    assert profile["total_files"] == 8
    assert profile["yaml_count"] == 3
    assert profile["json_count"] == 4
    assert profile["parse_failure_count"] == 2


def test_index_preserves_provenance_and_file_metadata(generated: tuple[dict, Path]) -> None:
    _, output = generated
    records = read_jsonl(output / "indexes/file_index.jsonl")
    api = next(record for record in records if record["source_path"] == "staging/apis/petstore.yaml")
    source = FIXTURE_SOURCE / "apis/petstore.yaml"
    assert api["relative_source_path"] == "staging/apis/petstore.yaml"
    assert api["source_category"] == "apis"
    assert api["source_folder"] == "staging/apis"
    assert api["file_extension"] == ".yaml"
    assert api["file_size_bytes"] == source.stat().st_size
    assert api["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert api["detected_format"] == "YAML"
    assert api["parse_status"] == "PARSE_OK"
    assert api["schema_family"] == "OPENAPI_DOCUMENT"
    assert api["schema_support_status"] == "SUPPORTED_SCHEMA"


def test_parse_errors_have_explicit_reasons_without_source_content(
    generated: tuple[dict, Path],
) -> None:
    _, output = generated
    errors = read_jsonl(output / "outputs/parse_errors/parse_errors.jsonl")
    assert {error["failure_reason"] for error in errors} == {
        "parse_failed_invalid_json",
        "parse_failed_invalid_yaml",
    }
    assert all(set(error) <= {"source_path", "failure_reason", "line", "column"} for error in errors)


def test_exact_duplicates_are_grouped_by_identical_hash(generated: tuple[dict, Path]) -> None:
    profile, output = generated
    duplicates = read_jsonl(output / "outputs/duplicates/exact_duplicate_files.jsonl")
    assert profile["exact_duplicate_group_count"] == 1
    assert profile["exact_duplicate_file_count"] == 2
    assert {item["source_path"] for item in duplicates} == {
        "staging/apps/apps.json",
        "staging/duplicates/apps-copy.json",
    }
    assert len({item["exact_duplicate_group"] for item in duplicates}) == 1
    assert all(item["status"] == "EXACT_FILE_DUPLICATE" for item in duplicates)
    assert all(item["failure_reason"] == "duplicate_due_to_identical_hash" for item in duplicates)


def test_unsupported_schema_version_is_explicit(tmp_path: Path) -> None:
    source = tmp_path / "staging"
    source.mkdir()
    (source / "future.yaml").write_text('openapi: "4.0.0"\n', encoding="utf-8")
    output = tmp_path / "generated"
    profile_repository(source, output)
    record = read_jsonl(output / "indexes/file_index.jsonl")[0]
    assert record["schema_support_status"] == "UNSUPPORTED_SCHEMA"
    assert record["schema_failure_reason"] == "unsupported_schema_version"


def test_output_cannot_modify_source_tree(tmp_path: Path) -> None:
    source = tmp_path / "staging"
    source.mkdir()
    with pytest.raises(ValueError, match="must not be inside"):
        profile_repository(source, source / "generated")


def test_output_is_deterministic(generated: tuple[dict, Path], tmp_path: Path) -> None:
    _, first = generated
    second = tmp_path / "second"
    profile_repository(FIXTURE_SOURCE, second)
    relative_outputs = [
        "indexes/file_index.jsonl",
        "outputs/repository_profile/repository_profile.json",
        "outputs/parse_errors/parse_errors.jsonl",
        "outputs/duplicates/exact_duplicate_files.jsonl",
        "outputs/schema_families/schema_families.json",
    ]
    for relative in relative_outputs:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
