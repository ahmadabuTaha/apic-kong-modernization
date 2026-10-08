from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from semantic_preflight import build_variant_profile, document_signature

ROOT = Path(__file__).parents[1]
OUT = ROOT / "tests/evidence/task-014/architecture-preflight"


def tree_hashes(path: Path) -> dict[str, str]:
    return {value.relative_to(ROOT).as_posix(): hashlib.sha256(value.read_bytes()).hexdigest() for value in path.rglob("*") if value.is_file()}


def test_variant_profile_separates_hash_duplicates_from_structural_equivalence() -> None:
    profile = build_variant_profile(ROOT)
    assert profile["summary"]["canonical_api_groups_with_multiple_root_yaml_representations"] == 1778
    assert profile["summary"]["groups_all_representations_same_sha256"] == 1776
    assert profile["summary"]["groups_with_multiple_sha256_values"] == 2
    assert profile["summary"]["groups_with_multiple_authoritative_api_artifacts"] == 0
    targeted = [value for value in profile["samples"] if value.get("targeted_parse_performed")]
    assert len(targeted) == 2
    assert {value["classification"] for value in targeted} == {"SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS"}


def test_signature_is_structural_and_omits_endpoint_values() -> None:
    signature = document_signature(ROOT / "staging/apis/_catalog/osh_1.0.0.yaml")
    rendered = json.dumps(signature, sort_keys=True)
    assert signature["operation_count"] == 24
    assert "target-url" not in rendered
    assert not re.search(r"https?://", rendered, re.I)


def test_generator_is_deterministic_redacted_and_preserves_frozen_assets() -> None:
    frozen_before = {**tree_hashes(ROOT / "staging"), **tree_hashes(ROOT / "indexes")}
    subprocess.run([str(ROOT / ".venv/bin/python"), str(OUT / "generate_preflight.py")], cwd=ROOT, check=True)
    first = tree_hashes(OUT)
    subprocess.run([str(ROOT / ".venv/bin/python"), str(OUT / "generate_preflight.py")], cwd=ROOT, check=True)
    assert first == tree_hashes(OUT)
    assert frozen_before == {**tree_hashes(ROOT / "staging"), **tree_hashes(ROOT / "indexes")}
    required = {"backend_evidence_options.md", "backend_evidence_samples.jsonl", "yaml_variants_options.md", "yaml_variants_samples.jsonl", "architecture_decisions_pending.md", "cross_canonical_similarity_feasibility.md"}
    assert required <= {value.name for value in OUT.iterdir()}
    text = "\n".join(value.read_text(encoding="utf-8") for value in OUT.iterdir() if value.suffix in {".md", ".jsonl"})
    assert not re.search(r"(?i)(password|passwd|client[_-]?secret|api[_-]?key)\s*[:=]\s*[^\s,;]+", text)
    assert not re.search(r"https?://", text, re.I)
    samples = [json.loads(line) for line in (OUT / "backend_evidence_samples.jsonl").read_text().splitlines()]
    shared = next(value for value in samples if value["case"] == "simple_shared_single_operation")
    assert shared["candidate_architectural_associations"][0]["certainty"] == "CANDIDATE_ONLY"
    assert shared["runtime_usage_proven"] is False
