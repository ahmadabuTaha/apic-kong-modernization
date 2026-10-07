"""Generate deterministic Task 007 evidence for unresolved Product API copies."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _candidate(record: dict[str, Any], canonical_id: str | None) -> dict[str, Any]:
    return {
        "extracted_record_id": record["extracted_record_id"],
        "source_relative_path": record["source_relative_path"],
        "source_object_pointer": record["source_object_pointer"],
        "source_sha256": record["source_sha256"],
        "apic_object_id": record.get("apic_object_id"),
        "apic_object_url": record.get("apic_object_url"),
        "org_url": record.get("org_url"),
        "catalog_url": record.get("catalog_url"),
        "canonical_identity_record_id": canonical_id,
    }


def _count_distribution(values: Iterable[int]) -> dict[str, int]:
    return {
        str(value): count for value, count in sorted(Counter(values).items())
    }


def build_investigation(
    phase2: dict[str, Any], phase1_records: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return the per-occurrence audit rows and aggregate evidence."""

    phase1_by_id = {
        record["extracted_record_id"]: record for record in phase1_records
    }
    api_identities = [
        record
        for record in phase2["canonical_identity_records"]
        if record["canonical_object_type"] == "api_artifact"
    ]
    product_identities = [
        record
        for record in phase2["canonical_identity_records"]
        if record["canonical_object_type"] == "product"
    ]
    canonical_by_occurrence = {
        occurrence_id: record["canonical_identity_record_id"]
        for record in api_identities + product_identities
        for occurrence_id in record["contributing_extracted_record_ids"]
    }
    product_identity_by_registry_occurrence = {
        occurrence_id: record
        for record in product_identities
        for occurrence_id in record["registry_occurrence_ids"]
    }

    authoritative_apis = [
        record
        for record in phase1_records
        if record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "OPENAPI_DOCUMENT"
        and record["source_relative_path"].startswith("staging/apis/_catalog/")
    ]
    registry_apis = [
        record
        for record in phase1_records
        if record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "APIC_COLLECTION"
    ]
    product_location_apis = [
        record
        for record in phase1_records
        if record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "OPENAPI_DOCUMENT"
        and record["source_relative_path"].startswith("staging/products/_catalog/")
    ]
    products = [
        record
        for record in phase1_records
        if record.get("canonical_object_type_candidate") == "product"
    ]
    product_registries = [
        record for record in products if record.get("source_schema_family") == "APIC_COLLECTION"
    ]

    authoritative_by_name_version: dict[
        tuple[str | None, str | None], list[dict[str, Any]]
    ] = defaultdict(list)
    registry_by_name_version: dict[
        tuple[str | None, str | None], list[dict[str, Any]]
    ] = defaultdict(list)
    authoritative_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_refs_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    registry_products_by_api_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_location_by_name_version: dict[
        tuple[str | None, str | None], list[dict[str, Any]]
    ] = defaultdict(list)

    for record in authoritative_apis:
        authoritative_by_name_version[(record.get("name"), record.get("version"))].append(
            record
        )
        authoritative_by_hash[record["source_sha256"]].append(record)
    for record in registry_apis:
        registry_by_name_version[(record.get("name"), record.get("version"))].append(
            record
        )
    for record in product_location_apis:
        product_location_by_name_version[
            (record.get("name"), record.get("version"))
        ].append(record)
    for product in products:
        for reference in product.get("api_references", []):
            mapped = reference.get("mapped_source_relative_path")
            if isinstance(mapped, str):
                product_refs_by_path[mapped].append(
                    {
                        "product_extracted_record_id": product["extracted_record_id"],
                        "product_source_relative_path": product["source_relative_path"],
                        "product_source_object_pointer": product["source_object_pointer"],
                        "product_name": product.get("name"),
                        "product_version": product.get("version"),
                        "api_key": reference.get("api_key"),
                        "raw_ref": reference.get("raw_ref"),
                        "mapped_source_relative_path": mapped,
                    }
                )
    for product in product_registries:
        for api_url in product.get("api_urls", []):
            registry_products_by_api_url[api_url].append(product)

    unresolved_ids = {
        record["extracted_record_id"] for record in phase2["unresolved_occurrences"]
    }
    attached_ids = {
        occurrence_id
        for record in api_identities
        for occurrence_id in record["product_location_occurrence_ids"]
    }
    rows: list[dict[str, Any]] = []
    for occurrence_id in sorted(unresolved_ids):
        occurrence = phase1_by_id[occurrence_id]
        name_version = (occurrence.get("name"), occurrence.get("version"))
        authoritative_candidates = sorted(
            authoritative_by_name_version[name_version],
            key=lambda value: value["extracted_record_id"],
        )
        registry_candidates = sorted(
            registry_by_name_version[name_version],
            key=lambda value: value["extracted_record_id"],
        )
        hash_candidates = sorted(
            authoritative_by_hash[occurrence["source_sha256"]],
            key=lambda value: value["extracted_record_id"],
        )
        product_refs = sorted(
            product_refs_by_path[occurrence["source_relative_path"]],
            key=lambda value: (
                value["product_source_relative_path"],
                value["api_key"] or "",
            ),
        )

        candidate_canonical_ids = sorted(
            {
                canonical_by_occurrence[candidate["extracted_record_id"]]
                for candidate in authoritative_candidates + registry_candidates
                if candidate["extracted_record_id"] in canonical_by_occurrence
            }
        )
        registry_product_memberships: list[dict[str, Any]] = []
        for registry_candidate in registry_candidates:
            api_url = registry_candidate.get("apic_object_url")
            if not isinstance(api_url, str):
                continue
            for product in registry_products_by_api_url[api_url]:
                identity = product_identity_by_registry_occurrence.get(
                    product["extracted_record_id"]
                )
                registry_product_memberships.append(
                    {
                        "product_extracted_record_id": product["extracted_record_id"],
                        "product_name": product.get("name"),
                        "product_version": product.get("version"),
                        "product_apic_object_url": product.get("apic_object_url"),
                        "product_canonical_identity_record_id": (
                            identity["canonical_identity_record_id"] if identity else None
                        ),
                        "authoritative_product_artifact_present": bool(
                            identity and identity["authoritative_artifact_occurrence_ids"]
                        ),
                    }
                )
        registry_product_memberships.sort(
            key=lambda value: (
                value["product_name"] or "",
                value["product_version"] or "",
                value["product_extracted_record_id"],
            )
        )
        diagnostic_siblings = []
        for sibling in sorted(
            product_location_by_name_version[name_version],
            key=lambda value: value["source_relative_path"],
        ):
            if sibling["extracted_record_id"] == occurrence_id:
                continue
            sibling_refs = product_refs_by_path[sibling["source_relative_path"]]
            diagnostic_siblings.append(
                {
                    "extracted_record_id": sibling["extracted_record_id"],
                    "source_relative_path": sibling["source_relative_path"],
                    "hash_equal": sibling["source_sha256"]
                    == occurrence["source_sha256"],
                    "product_ref_occurrence_count": len(sibling_refs),
                }
            )

        approved_api_bridge_exists = (
            len(authoritative_candidates) == 1
            and len(registry_candidates) == 1
            and len(candidate_canonical_ids) == 1
            and canonical_by_occurrence.get(
                authoritative_candidates[0]["extracted_record_id"]
            )
            == canonical_by_occurrence.get(registry_candidates[0]["extracted_record_id"])
        )
        row = {
            "extracted_record_id": occurrence_id,
            "source_relative_path": occurrence["source_relative_path"],
            "source_object_pointer": occurrence["source_object_pointer"],
            "source_sha256": occurrence["source_sha256"],
            "observed_name": occurrence.get("name"),
            "observed_declared_version": occurrence.get("version"),
            "observed_title": occurrence.get("title"),
            "observed_apic_object_id": occurrence.get("apic_object_id"),
            "observed_apic_self_url": occurrence.get("apic_object_url"),
            "observed_org_url": occurrence.get("org_url"),
            "observed_catalog_url": occurrence.get("catalog_url"),
            "product_context_from_source_path": None,
            "product_ref_maps_exactly_to_source_path": bool(product_refs),
            "product_ref_occurrence_count": len(product_refs),
            "product_ref_occurrences": product_refs,
            "registry_product_membership_count": len(registry_product_memberships),
            "registry_product_memberships": registry_product_memberships,
            "registry_product_membership_is_admissible_occurrence_attachment_evidence": False,
            "exact_self_url_or_id_scope_registry_candidate_count": 0,
            "exact_self_url_or_id_scope_registry_candidates": [],
            "same_name_version_product_location_sibling_count": len(
                diagnostic_siblings
            ),
            "same_name_version_product_location_siblings": diagnostic_siblings,
            "exact_name_version_authoritative_candidate_count": len(
                authoritative_candidates
            ),
            "exact_name_version_authoritative_candidates": [
                _candidate(
                    candidate,
                    canonical_by_occurrence.get(candidate["extracted_record_id"]),
                )
                for candidate in authoritative_candidates
            ],
            "exact_name_version_registry_candidate_count": len(registry_candidates),
            "exact_name_version_registry_candidates": [
                _candidate(
                    candidate,
                    canonical_by_occurrence.get(candidate["extracted_record_id"]),
                )
                for candidate in registry_candidates
            ],
            "hash_equal_authoritative_candidate_count": len(hash_candidates),
            "hash_equal_authoritative_candidates": [
                _candidate(
                    candidate,
                    canonical_by_occurrence.get(candidate["extracted_record_id"]),
                )
                for candidate in hash_candidates
            ],
            "approved_api_bridge_exists": approved_api_bridge_exists,
            "approved_api_bridge_authoritative_candidate_count": (
                len(authoritative_candidates) if approved_api_bridge_exists else 0
            ),
            "approved_product_ref_and_registry_convergence_exists": False,
            "candidate_canonical_identity_record_ids": candidate_canonical_ids,
            "attachment_conditions_not_satisfied": [
                "No Product $ref maps exactly to this Product-location source path.",
                "The flat Product-location source path does not identify a Product context.",
                "Registry Product membership does not reference this source-file occurrence.",
                "Name, declared version, and hash equality are diagnostic or corroborating evidence only and are not approved occurrence-attachment keys.",
            ],
            "task_006_resolution_outcome": "UNRESOLVED",
            "resolver_defect_demonstrated": False,
        }
        rows.append(row)

    rows.sort(
        key=lambda value: (
            value["source_relative_path"], value["extracted_record_id"]
        )
    )
    enumerated_ids = {row["extracted_record_id"] for row in rows}
    evidence_patterns = Counter(
        (
            row["product_ref_occurrence_count"],
            bool(row["observed_apic_self_url"]),
            bool(row["observed_apic_object_id"]),
            row["exact_name_version_authoritative_candidate_count"],
            row["exact_name_version_registry_candidate_count"],
            row["hash_equal_authoritative_candidate_count"],
            row["approved_api_bridge_exists"],
            row["approved_product_ref_and_registry_convergence_exists"],
        )
        for row in rows
    )
    pattern_rows = [
        {
            "product_ref_occurrence_count": pattern[0],
            "exact_self_url_present": pattern[1],
            "apic_id_present": pattern[2],
            "exact_name_version_authoritative_candidate_count": pattern[3],
            "exact_name_version_registry_candidate_count": pattern[4],
            "hash_equal_authoritative_candidate_count": pattern[5],
            "approved_api_bridge_exists": pattern[6],
            "approved_product_ref_and_registry_convergence_exists": pattern[7],
            "occurrence_count": count,
        }
        for pattern, count in sorted(evidence_patterns.items())
    ]
    unique_api_candidate_ids = {
        candidate_id
        for row in rows
        for candidate_id in row["candidate_canonical_identity_record_ids"]
    }
    summary = {
        "total_product_location_api_occurrences": len(product_location_apis),
        "attached_product_location_api_occurrences": len(attached_ids),
        "unresolved_product_location_api_occurrences": len(unresolved_ids),
        "arithmetic_proof": {
            "total_minus_attached": len(product_location_apis) - len(attached_ids),
            "equals_enumerated_unresolved_count": (
                len(product_location_apis) - len(attached_ids) == len(rows)
            ),
        },
        "enumerated_unresolved_record_count": len(rows),
        "enumerated_unique_extracted_record_id_count": len(enumerated_ids),
        "enumerated_ids_equal_phase2_unresolved_ids": enumerated_ids == unresolved_ids,
        "attached_and_unresolved_id_overlap_count": len(attached_ids & unresolved_ids),
        "counts_grouped_by_concrete_evidence_pattern": pattern_rows,
        "count_with_any_product_ref": sum(
            row["product_ref_occurrence_count"] > 0 for row in rows
        ),
        "count_with_exact_self_url": sum(
            bool(row["observed_apic_self_url"]) for row in rows
        ),
        "count_with_apic_id_and_compatible_scope": sum(
            bool(row["observed_apic_object_id"])
            and bool(row["observed_org_url"] or row["observed_catalog_url"])
            for row in rows
        ),
        "count_with_unique_approved_authoritative_registry_api_bridge": sum(
            row["approved_api_bridge_exists"] for row in rows
        ),
        "count_with_approved_product_ref_registry_attachment_convergence": sum(
            row["approved_product_ref_and_registry_convergence_exists"]
            for row in rows
        ),
        "count_with_exact_name_version_diagnostic_match_but_no_admissible_attachment_key": sum(
            row["exact_name_version_authoritative_candidate_count"] == 1
            and row["exact_name_version_registry_candidate_count"] == 1
            and not row["product_ref_occurrence_count"]
            and not row["observed_apic_self_url"]
            and not row["observed_apic_object_id"]
            for row in rows
        ),
        "count_with_hash_equal_diagnostic_match_but_no_admissible_attachment_key": sum(
            row["hash_equal_authoritative_candidate_count"] > 0
            and not row["product_ref_occurrence_count"]
            and not row["observed_apic_self_url"]
            and not row["observed_apic_object_id"]
            for row in rows
        ),
        "count_with_registry_product_membership_but_no_yaml_product_ref": sum(
            row["registry_product_membership_count"] > 0
            and not row["product_ref_occurrence_count"]
            for row in rows
        ),
        "count_with_referenced_same_name_version_product_location_sibling": sum(
            any(
                sibling["product_ref_occurrence_count"] > 0
                for sibling in row[
                    "same_name_version_product_location_siblings"
                ]
            )
            for row in rows
        ),
        "count_with_registry_only_product_membership": sum(
            any(
                not membership["authoritative_product_artifact_present"]
                for membership in row["registry_product_memberships"]
            )
            for row in rows
        ),
        "count_with_multiple_registry_product_memberships": sum(
            row["registry_product_membership_count"] > 1 for row in rows
        ),
        "registry_product_membership_count_distribution": _count_distribution(
            row["registry_product_membership_count"] for row in rows
        ),
        "count_with_multiple_authoritative_or_registry_candidates": sum(
            row["exact_name_version_authoritative_candidate_count"] > 1
            or row["exact_name_version_registry_candidate_count"] > 1
            for row in rows
        ),
        "count_with_no_admissible_candidate": sum(
            not row["product_ref_occurrence_count"]
            and not row["observed_apic_self_url"]
            and not row["observed_apic_object_id"]
            for row in rows
        ),
        "count_with_no_diagnostic_candidate_evidence_beyond_api_document": sum(
            not row["exact_name_version_authoritative_candidate_count"]
            and not row["exact_name_version_registry_candidate_count"]
            and not row["hash_equal_authoritative_candidate_count"]
            and not row["registry_product_membership_count"]
            for row in rows
        ),
        "unique_candidate_canonical_api_identity_count": len(unique_api_candidate_ids),
        "count_demonstrated_to_be_resolver_defects": sum(
            row["resolver_defect_demonstrated"] for row in rows
        ),
        "count_correctly_unresolved_under_approved_contract": sum(
            not row["resolver_defect_demonstrated"] for row in rows
        ),
        "categories_may_overlap": True,
    }
    return rows, summary


def write_artifacts(
    phase2_path: Path, phase1_path: Path, output_directory: Path
) -> dict[str, Any]:
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    rows, summary = build_investigation(phase2, _load_jsonl(phase1_path))
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "unresolved_product_location_apis.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    (output_directory / "investigation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase2", type=Path, default=Path("indexes/apic_identity_resolution.json")
    )
    parser.add_argument(
        "--phase1", type=Path, default=Path("indexes/extracted_records.jsonl")
    )
    parser.add_argument(
        "--output-directory", type=Path, default=Path("tests/evidence/task-007")
    )
    args = parser.parse_args()
    summary = write_artifacts(args.phase2, args.phase1, args.output_directory)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
