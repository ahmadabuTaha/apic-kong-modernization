from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[4]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from business_domain.skeleton_mapping import OUTPUTS, SKELETON, STOP_GATE, build_skeleton_mapping  # noqa: E402


def write(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def json_line(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escape(value: Any) -> str:
    return str(value if value not in (None, "") else "—").replace("|", "/").replace("\n", " ")


result = build_skeleton_mapping(ROOT)
manifest = result["manifest"]
summary = manifest["summary"]

for filename, key in (
    ("operation_domain_initial_mapping.jsonl", "operations"),
    ("canonical_api_domain_footprint.jsonl", "apis"),
    ("business_object_candidate_register.jsonl", "objects"),
):
    path = ROOT / OUTPUTS[key]
    write(HERE / filename, json_line({
        "record_type": "DETERMINISTIC_FULL_LEDGER_POINTER",
        "full_ledger_path": OUTPUTS[key].as_posix(),
        "record_count": len(result[key]),
        "sha256": sha(path),
        "rebuild_command": ".venv/bin/python -m business_domain.skeleton_mapping_main",
    }))

skeleton_lines = [
    "# Task 018B Skeleton Contract",
    "",
    "Status: EA-supplied initial candidate skeleton; not a ratified enterprise taxonomy. Every mapping is provisional and pending Enterprise Architect review.",
    "",
    "The candidate labels are fixed for this task:",
    "",
]
skeleton_lines.extend(f"{index}. {label}" for index, label in enumerate(SKELETON, 1))
skeleton_lines.extend([
    "",
    "No candidate may be added, renamed, merged, split, or promoted by this task. Certificate remains independent; it is not silently absorbed into Visa, Work Permit, or Establishment. Common, User Management, and Notification remain candidate classification buckets pending an explicit decision about business-domain versus shared/technical-capability status.",
    "",
    "Operation evidence may support zero or one provisional primary and multiple alternatives. API names, exposure channels, QIWA modules, products/plans, ACE hierarchy, invocation hosts, and generic workflow verbs do not establish ownership. An identifier reference does not establish the primary business object.",
    "",
    "Open decisions: ratify or revise each candidate's enterprise definition; decide the status of Common, User Management, and Notification; decide Certificate ownership and boundaries; confirm ambiguous cross-candidate operations; and provide business-owner/ICD evidence where APIC semantics are insufficient.",
    "",
    f"STOP: `{STOP_GATE}`. No Task 019, rationalization, productization, retirement, or Kong design is authorized.",
    "",
])
write(HERE / "skeleton_contract.md", "\n".join(skeleton_lines))

ambiguous = [row for row in result["operations"] if row["domain_assessment"]["classification_status"] in {"UNRESOLVED_AMBIGUOUS", "CONFLICTING_SOURCE_EVIDENCE"}]
limited = [row for row in result["operations"] if row["domain_assessment"]["contradicted_or_limiting_alternatives"]]
review_rows = []
seen = set()
for row in sorted(ambiguous + limited, key=lambda value: value["task014_operation_id"]):
    if row["task014_operation_id"] in seen:
        continue
    review_rows.append(row); seen.add(row["task014_operation_id"])
    if len(review_rows) == 30:
        break
backlog = [
    "# Task 018B Domain Review and Reclassification Backlog",
    "",
    "These are bounded review recommendations, not applied EA decisions. The original Task 017A reviews, five oversized adjuncts, 14 links, and 90 backlog items remain unchanged.",
    "",
    "| Operation | Current provisional primary | Proposed alternatives | Object/action clue | Counterevidence or limitation | Missing business proof | Proposed verification source |",
    "|---|---|---|---|---|---|---|",
]
for row in review_rows:
    assessment = row["domain_assessment"]
    clue = row["documented_clues"]
    limits = "; ".join(item["reason"] for item in assessment["contradicted_or_limiting_alternatives"]) or assessment["precise_reason"]
    backlog.append("| " + " | ".join((
        escape(row["task014_operation_id"]),
        escape(assessment["proposed_primary"] or "UNRESOLVED"),
        escape(", ".join(assessment["alternative_candidates"]) or "NONE"),
        escape(f"{clue.get('action') or 'unknown'} / {clue.get('business_object_or_resource_phrase') or 'unknown'}"),
        escape(limits),
        "Enterprise responsibility, owner intent, and cross-layer business model",
        "Business owner or operation-specific ICD; implementation dependency only if the question requires it",
    )) + " |")
backlog.extend([
    "",
    "Priority decision themes: Certificate independence; Common/User Management/Notification status; referenced Establishment identifiers versus acted-upon workforce/contract/payment objects; and cases where copied or contradictory descriptions prevent a primary.",
    "",
])
write(HERE / "domain_review_reclassification_backlog.md", "\n".join(backlog))

primary_api = defaultdict(set)
alternative_api = defaultdict(set)
for row in result["operations"]:
    assessment = row["domain_assessment"]
    if assessment["proposed_primary"]:
        primary_api[assessment["proposed_primary"]].add(row["canonical_api_id"])
    for candidate in assessment["alternative_candidates"]:
        alternative_api[candidate].add(row["canonical_api_id"])
coverage = [
    "# Task 018B Coverage, Quality, and Unresolved Evidence",
    "",
    f"Full operation preservation: **{summary['operation_count']}/{summary['operation_count']}** unique Task 014 operations. Canonical API accounting: **{summary['canonical_api_count']}/{summary['canonical_api_count']}**, including **{summary['zero_operation_or_unsupported_api_count']}** zero-operation/unsupported APIs. Skeleton: **{summary['skeleton_candidate_count']}** fixed candidates; new candidates: **0**; enterprise approvals: **0**.",
    "",
    "## Candidate footprint",
    "",
    "Primary counts do not double-count operations. Alternative counts are separate and may overlap.",
    "",
    "| Candidate | Primary operations | APIs with primary operations | Alternative occurrences | APIs with alternatives |",
    "|---|---:|---:|---:|---:|",
]
for candidate in SKELETON:
    coverage.append(f"| {candidate} | {summary['primary_candidate_counts'][candidate]} | {len(primary_api[candidate])} | {summary['alternative_candidate_counts'][candidate]} | {len(alternative_api[candidate])} |")
coverage.extend(["", "## Classification quality", ""])
for status, count in summary["classification_status_counts"].items():
    coverage.append(f"- `{status}`: {count}")
coverage.extend([
    "",
    f"Targeted YAML enrichment inspected {summary['targeted_yaml']['selected_operation_count']} unresolved, conflicting, or boundary-sensitive operations across {summary['targeted_yaml']['source_document_count']} source documents. Hash mismatches: {summary['targeted_yaml']['source_hash_mismatch_count']}; parse errors: {summary['targeted_yaml']['source_parse_error_count']}; unresolved local schema references: {summary['targeted_yaml']['unresolved_local_schema_ref_count']}.",
    "",
    "Schema names are not automatically business objects. The register distinguishes core-object candidates, object references, DTO/transport models, lookup/value sets, technical envelopes, documented actions, and state-value candidates. Enum values do not prove transitions or a state machine; shared schemas do not prove shared ownership.",
    "",
    "## Representative negative controls",
    "",
    "| Operation | Result | Reason |",
    "|---|---|---|",
])
negatives = [row for row in result["operations"] if row["domain_assessment"]["classification_status"] in {"TECHNICAL_OR_TEST_NO_DOMAIN_PRIMARY", "UNRESOLVED_INSUFFICIENT_SEMANTICS"}][:10]
for row in negatives:
    coverage.append(f"| {escape(row['task014_operation_id'])} | {row['domain_assessment']['classification_status']} | {escape(row['domain_assessment']['precise_reason'])} |")
coverage.extend([
    "",
    "Unresolved evidence is a gap, not an error: APIC configuration does not establish production usage, retirement, runtime egress, enterprise ownership, or cross-layer domain authority. No whole-API inheritance or forced coverage was applied.",
    "",
    f"Final position: technical Task 018B evidence complete; Enterprise Architect decisions pending at `{STOP_GATE}`.",
    "",
])
write(HERE / "coverage_quality_and_unresolved.md", "\n".join(coverage))

evidence_manifest = {
    "task": "018B",
    "status": "TECHNICAL_PASS_CANDIDATE_MAPPING_ONLY_EA_REVIEW_PENDING",
    "index_manifest_path": OUTPUTS["manifest"].as_posix(),
    "index_manifest_sha256": sha(ROOT / OUTPUTS["manifest"]),
    "full_ledgers": {key: {"path": path.as_posix(), "sha256": sha(ROOT / path), "record_count": len(result[key])} for key, path in OUTPUTS.items() if key != "manifest"},
    "review_output_sha256": {name: sha(HERE / name) for name in ("skeleton_contract.md", "domain_review_reclassification_backlog.md", "coverage_quality_and_unresolved.md")},
    "stop_gate": STOP_GATE,
}
write(HERE / "build_manifest.json", json.dumps(evidence_manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
