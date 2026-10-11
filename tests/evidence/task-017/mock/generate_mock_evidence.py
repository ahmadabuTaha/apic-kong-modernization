from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[4]
EVIDENCE = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from logical_api.mock import build_mock  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value, sort_keys=True, indent=2) + "\n")


def write_jsonl(path: Path, values: list[dict]) -> None:
    write(path, "".join(json.dumps(v, sort_keys=True, separators=(",", ":")) + "\n" for v in values))


result = build_mock(ROOT)
cases = result["cases"]
queue = result["review_queue"]
write_jsonl(EVIDENCE / "representative_boundary_cases.jsonl", cases)
write_jsonl(EVIDENCE / "review_queue.jsonl", queue)

write(EVIDENCE / "logical_api_formation_contract.md", """# Task 017 representative logical API formation contract

This contract applies only to the bounded representative mock. A Logical API is a provisional TO-BE conceptual resource or workflow boundary. It is neither an APIC API or Product nor a Kong Service, Route, or Product.

## Identity and membership

`logical_api_candidate_id` is a deterministic hash of the case key and sorted Task 014 member operation IDs. Every member retains its accepted canonical API ID, Task 014 operation ID, Task 015 observed-function ID, Task 016 references when applicable, endpoint, contract, source pointer, source hash, and source-variant fingerprint. Membership is an explicit star edge from the candidate to each operation. Non-formation controls retain candidate members but mark membership `NOT_ASSERTED_NONFORMATION_CASE`.

## Independent relations

`FUNCTIONAL_EQUIVALENCE_CANDIDATE` asks whether operations may perform the same action, object, and behavioral intent. It never collapses IDs and remains unapproved. `LOGICAL_API_COHESION` asks whether distinct operations belong to one consumer-facing resource or workflow. Related actions such as approve, reject, cancel, submit, and update remain distinct logical operations. Pairwise evidence is never transitively closed.

Contract compatibility, backend certainty, AS-IS Product/Plan context, runtime evidence, and migration safety remain separate fields. API-shared configured routes are not promoted to operation semantics. Product relationships provide exposure context only; a Product never becomes a Logical API by default.

## Status model

- `COHESIVE_LOGICAL_API_CANDIDATE`: bounded evidence supports a provisional boundary; architect review remains required.
- `PARTIAL_OR_VARIANT_BOUNDARY_REVIEW`: cohesion is plausible but version, contract, consumer, or unresolved-member differences affect the boundary.
- `INSUFFICIENT_EVIDENCE_TO_FORM`: no membership is asserted; targeted evidence is required.
- `SEPARATE_LOGICAL_APIS_SUPPORTED`: evidence supports separate boundaries; no consolidation is proposed.

All labels are business-neutral resource/workflow labels, not Domain or Capability assignments. No status approves equivalence, production use, migration, retirement, or Kong topology.
""")

write(EVIDENCE / "grouping_false_positive_controls.md", """# Task 017 grouping false-positive controls

- Approve, reject, and cancel may be cohesive around an SC request, but remain distinct actions. One source endpoint bundles approve/reject; that is preserved rather than split into invented source operations or treated as duplication.
- Structurally equal WPS response wrappers and shared configured backend candidates are supporting context only. One undocumented action prevents formation.
- The appointment-status case demonstrates that shared paths, shapes, or routes cannot override conflicting behavioral evidence.
- API-shared backend configuration is never promoted to resolved operation semantics. Runtime calls are never inferred.
- Seasonal-visa version labels and contract differences are retained. Version family does not prove interchangeability, consumer equivalence, or retirement safety.
- Pairwise functional hypotheses are not transitively closed. Membership edges are direct candidate-to-operation assertions; unresolved members cannot raise group certainty.
- APIC Product/Plan/Subscription links remain AS-IS exposure context and never define the conceptual group.
- System health and token issuance are separate technical intents even though both are technical endpoints.
- Generic names, root paths, schemas, and response envelopes cannot establish a business-facing resource boundary.
""")

dispositions = Counter(v["disposition"] for v in cases)
category_coverage = {
    "same_object_distinct_actions": "EVIDENCED",
    "different_names_paths_possible_same_intent": "EVIDENCED",
    "seasonal_visa_version_variants": "EVIDENCED",
    "employment_status_insufficient_backend_semantics": "EVIDENCED",
    "multiple_operations_one_canonical_api": "EVIDENCED",
    "one_candidate_boundary_several_canonical_apis": "EVIDENCED",
    "shared_backend_or_wrapper_negative_control": "EVIDENCED",
    "technical_or_security_endpoint": "EVIDENCED",
    "ambiguity_control": "EVIDENCED",
    "shared_path_or_schema_false_positive": "EVIDENCED",
}
write_json(EVIDENCE / "coverage_and_nonformation_report.json", {
    "scope": "REPRESENTATIVE_MOCK_ONLY",
    "case_count": len(cases),
    "member_occurrence_count": sum(len(v["candidate_members"]) for v in cases),
    "unique_task014_member_count": len({m["task014_operation_id"] for v in cases for m in v["candidate_members"]}),
    "canonical_api_count": len({m["canonical_api_id"] for v in cases for m in v["candidate_members"]}),
    "dispositions": dict(sorted(dispositions.items())),
    "nonformation_case_count": dispositions["INSUFFICIENT_EVIDENCE_TO_FORM"] + dispositions["SEPARATE_LOGICAL_APIS_SUPPORTED"],
    "category_coverage": category_coverage,
    "full_estate_coverage_claimed": False,
    "task016_pair_recall_reassessed": False,
    "frozen_phases_reopened": False,
    "raw_staging_reads_for_task017": 0,
    "known_limitations": [
        "Production usage and consumer intent are not proven by configuration.",
        "CI/CD and release traceability remain unavailable for consolidation or retirement decisions.",
        "Configured API-shared backends do not establish operation-level semantics.",
        "The sample is not statistically representative and does not estimate full-estate group counts."
    ],
})

write(EVIDENCE / "commands_and_results.txt", """Task 017 representative mock deterministic build and validation

.venv/bin/python tests/evidence/task-017/mock/generate_mock_evidence.py
RESULT: PASS - generated 10 bounded cases and 10 review items from frozen indexes.

.venv/bin/pytest tests/test_logical_api_mock.py
RESULT: PASS - deterministic identity, frozen safety, relation separation, and guardrail controls.

.venv/bin/pytest
RESULT: 90 passed, 5 known Phase 0 fixture setup errors. The loopback explorer test passed when rerun with local socket permission.
""")

artifact_names = [
    "logical_api_formation_contract.md", "representative_boundary_cases.jsonl",
    "grouping_false_positive_controls.md", "coverage_and_nonformation_report.json",
    "review_queue.jsonl", "commands_and_results.txt",
]
write_json(EVIDENCE / "build_manifest.json", {
    "rules_version": result["manifest"]["rules_version"],
    "scope": "REPRESENTATIVE_MOCK_ONLY",
    "case_count": len(cases),
    "review_item_count": len(queue),
    "input_fingerprints": result["manifest"]["inputs"],
    "local_ignored_index_outputs": result["manifest"]["outputs"],
    "evidence_artifacts": {name: {"sha256": digest(EVIDENCE / name), "bytes": (EVIDENCE / name).stat().st_size} for name in artifact_names},
    "deterministic_generation": True,
    "staging_modified": False,
    "full_estate_formation_performed": False,
})
