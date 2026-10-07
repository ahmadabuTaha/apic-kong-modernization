"""Build deterministic structural edges between canonical APIC identities."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


OUTPUT_RELATIVE_PATH = Path("indexes/relationship_index.jsonl")

APPROVED_RELATIONSHIP_TYPES = (
    "product_contains_api",
    "product_contains_plan",
    "plan_entitles_api",
    "application_belongs_to_consumer_org",
    "credential_belongs_to_application",
    "subscription_belongs_to_application",
    "subscription_targets_product",
    "subscription_uses_plan",
    "api_uses_catalog_property",
    "api_invokes_target",
)

ENDPOINT_TYPES = {
    "product_contains_api": ("product", "api_artifact"),
    "product_contains_plan": ("product", "plan"),
    "plan_entitles_api": ("plan", "api_artifact"),
    "application_belongs_to_consumer_org": ("application", "consumer_org"),
    "credential_belongs_to_application": ("credential", "application"),
    "subscription_belongs_to_application": ("subscription", "application"),
    "subscription_targets_product": ("subscription", "product"),
    "subscription_uses_plan": ("subscription", "plan"),
    "api_uses_catalog_property": ("api_artifact", "catalog_property"),
    "api_invokes_target": ("api_artifact", "api_artifact"),
}

AUTHORITATIVE_ARTIFACT = "authoritative_artifact"
REGISTRY_REFERENCE = "registry_reference"


def _relationship_id(relationship_type: str, source_id: str, target_id: str) -> str:
    value = json.dumps(
        [source_id, relationship_type, target_id], separators=(",", ":")
    ).encode("utf-8")
    return f"apic-relationship:sha256:{hashlib.sha256(value).hexdigest()}"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _evidence_category(record: dict[str, Any]) -> str:
    return (
        REGISTRY_REFERENCE
        if record.get("source_schema_family") == "APIC_COLLECTION"
        else AUTHORITATIVE_ARTIFACT
    )


def _provenance(
    occurrence: dict[str, Any],
    *,
    raw_reference: Any = None,
    mapped_source_relative_path: str | None = None,
    phase2_resolution_outcome: str | None = "RESOLVED",
) -> dict[str, Any]:
    result = {
        "evidence_source_category": _evidence_category(occurrence),
        "extracted_record_id": occurrence["extracted_record_id"],
        "source_relative_path": occurrence["source_relative_path"],
        "source_object_pointer": occurrence["source_object_pointer"],
    }
    if raw_reference is not None:
        result["raw_reference"] = raw_reference
    if mapped_source_relative_path is not None:
        result["mapped_source_relative_path"] = mapped_source_relative_path
    if phase2_resolution_outcome is not None:
        result["phase2_resolution_outcome"] = phase2_resolution_outcome
    return result


class _EdgeAccumulator:
    def __init__(self, identities: dict[str, dict[str, Any]]) -> None:
        self.identities = identities
        self.provenance: dict[
            tuple[str, str, str], dict[str, dict[str, Any]]
        ] = defaultdict(dict)

    def add(
        self,
        relationship_type: str,
        source_id: str,
        target_id: str,
        provenance: Iterable[dict[str, Any]],
    ) -> bool:
        provenance_items = list(provenance)
        if not provenance_items:
            return False
        if relationship_type not in ENDPOINT_TYPES:
            raise ValueError(f"unapproved relationship type: {relationship_type}")
        source = self.identities.get(source_id)
        target = self.identities.get(target_id)
        if source is None or target is None:
            return False
        expected_source, expected_target = ENDPOINT_TYPES[relationship_type]
        if source["canonical_object_type"] != expected_source:
            raise ValueError(
                f"invalid source type for {relationship_type}: "
                f"{source['canonical_object_type']}"
            )
        if target["canonical_object_type"] != expected_target:
            raise ValueError(
                f"invalid target type for {relationship_type}: "
                f"{target['canonical_object_type']}"
            )
        key = (source_id, relationship_type, target_id)
        for item in provenance_items:
            encoded = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            self.provenance[key][encoded] = item
        return True

    def records(self) -> list[dict[str, Any]]:
        result = []
        for (source_id, relationship_type, target_id), values in self.provenance.items():
            source = self.identities[source_id]
            target = self.identities[target_id]
            provenance = [values[key] for key in sorted(values)]
            contributing_ids = sorted(
                {item["extracted_record_id"] for item in provenance}
            )
            result.append(
                {
                    "relationship_id": _relationship_id(
                        relationship_type, source_id, target_id
                    ),
                    "relationship_type": relationship_type,
                    "source_canonical_identity_record_id": source_id,
                    "source_canonical_object_type": source[
                        "canonical_object_type"
                    ],
                    "target_canonical_identity_record_id": target_id,
                    "target_canonical_object_type": target[
                        "canonical_object_type"
                    ],
                    "evidence_state": "STRUCTURALLY_CONFIRMED",
                    "evidence_source_categories": sorted(
                        {item["evidence_source_category"] for item in provenance}
                    ),
                    "contributing_extracted_record_ids": contributing_ids,
                    "provenance": provenance,
                }
            )
        result.sort(
            key=lambda value: (
                value["relationship_type"],
                value["source_canonical_identity_record_id"],
                value["target_canonical_identity_record_id"],
            )
        )
        return result


def _resolve_url(
    canonical_by_url: dict[tuple[str, str], list[str]],
    object_type: str,
    raw_value: Any,
) -> tuple[str, list[str]]:
    if not isinstance(raw_value, str) or not raw_value:
        return "UNRESOLVED", []
    candidates = canonical_by_url.get((object_type, raw_value), [])
    if len(candidates) == 1:
        return "RESOLVED", candidates
    if len(candidates) > 1:
        return "AMBIGUOUS", candidates
    return "BROKEN_REFERENCE", []


def build_relationships(
    phase2: dict[str, Any], phase1_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build canonical structural edges and deterministic validation metadata."""

    identities = {
        record["canonical_identity_record_id"]: record
        for record in phase2["canonical_identity_records"]
    }
    phase1_by_id = {
        record["extracted_record_id"]: record for record in phase1_records
    }
    canonical_by_occurrence = {
        occurrence_id: identity_id
        for identity_id, identity in identities.items()
        for occurrence_id in identity["contributing_extracted_record_ids"]
    }
    canonical_by_url: dict[tuple[str, str], list[str]] = defaultdict(list)
    for identity_id, identity in identities.items():
        url = identity.get("apic_object_url")
        if isinstance(url, str):
            canonical_by_url[(identity["canonical_object_type"], url)].append(
                identity_id
            )
    for values in canonical_by_url.values():
        values.sort()

    excluded = Counter({"UNRESOLVED": len(phase2.get("unresolved_occurrences", []))})
    for identity in identities.values():
        for reference in identity.get("references", []):
            outcome = reference.get("outcome")
            if outcome in {"UNRESOLVED", "AMBIGUOUS", "BROKEN_REFERENCE"}:
                excluded[outcome] += 1

    metrics: Counter[str] = Counter()
    edges = _EdgeAccumulator(identities)

    # Authoritative Product API map references.
    for product_id, product in identities.items():
        if product["canonical_object_type"] != "product":
            continue
        for reference in product.get("references", []):
            if reference.get("field") != "product_api_ref":
                continue
            metrics["product_api_authoritative_references_observed"] += 1
            if reference.get("outcome") != "RESOLVED":
                continue
            target_ids = reference.get("target_canonical_identity_record_ids", [])
            if len(target_ids) != 1:
                continue
            provenance = [
                _provenance(
                    phase1_by_id[occurrence_id],
                    raw_reference=reference.get("raw_value"),
                    mapped_source_relative_path=reference.get(
                        "mapped_source_relative_path"
                    ),
                    phase2_resolution_outcome=reference.get("outcome"),
                )
                for occurrence_id in product[
                    "authoritative_artifact_occurrence_ids"
                ]
                if occurrence_id in phase1_by_id
            ]
            if edges.add(
                "product_contains_api", product_id, target_ids[0], provenance
            ):
                metrics["product_api_authoritative_references_represented"] += 1

    # Direct registry Product membership.
    for occurrence in phase1_records:
        if not (
            occurrence.get("canonical_object_type_candidate") == "product"
            and occurrence.get("source_schema_family") == "APIC_COLLECTION"
        ):
            continue
        source_id = canonical_by_occurrence.get(occurrence["extracted_record_id"])
        for api_url in occurrence.get("api_urls", []):
            metrics["product_api_registry_memberships_observed"] += 1
            outcome, target_ids = _resolve_url(
                canonical_by_url, "api_artifact", api_url
            )
            if outcome != "RESOLVED" or source_id is None:
                excluded[outcome] += 1
                continue
            if edges.add(
                "product_contains_api",
                source_id,
                target_ids[0],
                [
                    _provenance(
                        occurrence,
                        raw_reference=api_url,
                        phase2_resolution_outcome=outcome,
                    )
                ],
            ):
                metrics["product_api_registry_memberships_represented"] += 1

    # Contextual Product to Plan identity containment.
    for plan_id, plan in identities.items():
        if plan["canonical_object_type"] != "plan":
            continue
        metrics["canonical_plan_identities_observed"] += 1
        product_id = plan.get("parent_product_identity_record_id")
        provenance = [
            _provenance(
                phase1_by_id[occurrence_id],
                raw_reference=plan.get("plan_key"),
            )
            for occurrence_id in plan["contributing_extracted_record_ids"]
            if occurrence_id in phase1_by_id
        ]
        if isinstance(product_id, str) and edges.add(
            "product_contains_plan", product_id, plan_id, provenance
        ):
            metrics["canonical_plan_identities_represented"] += 1
        else:
            excluded["UNRESOLVED"] += 1

        # Authoritative Product-local Plan API keys already resolved by Phase 2.
        for reference in plan.get("references", []):
            if reference.get("field") != "plan_api_key":
                continue
            metrics["plan_api_authoritative_references_observed"] += 1
            if reference.get("outcome") != "RESOLVED":
                continue
            target_ids = reference.get("target_canonical_identity_record_ids", [])
            if len(target_ids) != 1:
                continue
            authoritative_occurrences = [
                phase1_by_id[occurrence_id]
                for occurrence_id in plan["authoritative_artifact_occurrence_ids"]
                if occurrence_id in phase1_by_id
            ]
            if edges.add(
                "plan_entitles_api",
                plan_id,
                target_ids[0],
                [
                    _provenance(
                        occurrence,
                        raw_reference=reference.get("raw_value"),
                        phase2_resolution_outcome=reference.get("outcome"),
                    )
                    for occurrence in authoritative_occurrences
                ],
            ):
                metrics["plan_api_authoritative_references_represented"] += 1

    # Registry Product-local Plan API membership.
    for occurrence in phase1_records:
        if not (
            occurrence.get("canonical_object_type_candidate") == "plan"
            and occurrence.get("source_schema_family") == "APIC_COLLECTION"
        ):
            continue
        source_id = canonical_by_occurrence.get(occurrence["extracted_record_id"])
        for reference in occurrence.get("api_references", []):
            metrics["plan_api_registry_references_observed"] += 1
            raw_url = reference.get("apic_object_url")
            outcome, target_ids = _resolve_url(
                canonical_by_url, "api_artifact", raw_url
            )
            if outcome != "RESOLVED" or source_id is None:
                excluded[outcome] += 1
                continue
            if edges.add(
                "plan_entitles_api",
                source_id,
                target_ids[0],
                [
                    _provenance(
                        occurrence,
                        raw_reference=raw_url,
                        phase2_resolution_outcome=outcome,
                    )
                ],
            ):
                metrics["plan_api_registry_references_represented"] += 1

    direct_relationships = {
        ("application", "consumer_org_url"): (
            "application_belongs_to_consumer_org",
            "application_consumer_org_references",
        ),
        ("credential", "app_url"): (
            "credential_belongs_to_application",
            "credential_application_references",
        ),
        ("subscription", "app_url"): (
            "subscription_belongs_to_application",
            "subscription_application_references",
        ),
        ("subscription", "product_url"): (
            "subscription_targets_product",
            "subscription_product_references",
        ),
        ("subscription", "plan"): (
            "subscription_uses_plan",
            "subscription_plan_references",
        ),
    }
    for source_id, identity in identities.items():
        for reference in identity.get("references", []):
            relationship = direct_relationships.get(
                (identity["canonical_object_type"], reference.get("field"))
            )
            if relationship is None:
                continue
            relationship_type, metric_prefix = relationship
            metrics[f"{metric_prefix}_observed"] += 1
            if reference.get("outcome") != "RESOLVED":
                continue
            target_ids = reference.get("target_canonical_identity_record_ids", [])
            if len(target_ids) != 1:
                continue
            provenance_occurrences = [
                phase1_by_id[occurrence_id]
                for occurrence_id in identity["registry_occurrence_ids"]
                if occurrence_id in phase1_by_id
            ]
            if not provenance_occurrences:
                provenance_occurrences = [
                    phase1_by_id[occurrence_id]
                    for occurrence_id in identity[
                        "contributing_extracted_record_ids"
                    ]
                    if occurrence_id in phase1_by_id
                ]
            if edges.add(
                relationship_type,
                source_id,
                target_ids[0],
                [
                    _provenance(
                        occurrence,
                        raw_reference=reference.get("raw_value"),
                        phase2_resolution_outcome=reference.get("outcome"),
                    )
                    for occurrence in provenance_occurrences
                ],
            ):
                metrics[f"{metric_prefix}_represented"] += 1

    edge_records = edges.records()
    counts = Counter(record["relationship_type"] for record in edge_records)
    counts_by_category = Counter(
        category
        for record in edge_records
        for category in record["evidence_source_categories"]
    )
    summary = {
        "total_canonical_edges": len(edge_records),
        "counts_by_relationship_type": {
            relationship_type: counts[relationship_type]
            for relationship_type in APPROVED_RELATIONSHIP_TYPES
        },
        "counts_by_evidence_source_category": dict(
            sorted(counts_by_category.items())
        ),
        "evidence_source_category_counts_may_overlap": True,
        "edges_with_multiple_contributing_source_occurrences": sum(
            len(record["contributing_extracted_record_ids"]) > 1
            for record in edge_records
        ),
        "excluded_evidence_by_resolution_outcome": {
            outcome: excluded[outcome]
            for outcome in ("UNRESOLVED", "AMBIGUOUS", "BROKEN_REFERENCE")
        },
        "task_007_unresolved_product_location_occurrences_excluded": len(
            phase2.get("unresolved_occurrences", [])
        ),
    }
    coverage = {
        "product_contains_api": {
            "canonical_edges": counts["product_contains_api"],
            "authoritative_references_represented": metrics[
                "product_api_authoritative_references_represented"
            ],
            "authoritative_references_observed": metrics[
                "product_api_authoritative_references_observed"
            ],
            "registry_memberships_represented": metrics[
                "product_api_registry_memberships_represented"
            ],
            "registry_memberships_observed": metrics[
                "product_api_registry_memberships_observed"
            ],
        },
        "product_contains_plan": {
            "canonical_edges": counts["product_contains_plan"],
            "canonical_plan_identities_represented": metrics[
                "canonical_plan_identities_represented"
            ],
            "canonical_plan_identities_observed": metrics[
                "canonical_plan_identities_observed"
            ],
        },
        "plan_entitles_api": {
            "canonical_edges": counts["plan_entitles_api"],
            "authoritative_references_represented": metrics[
                "plan_api_authoritative_references_represented"
            ],
            "authoritative_references_observed": metrics[
                "plan_api_authoritative_references_observed"
            ],
            "registry_references_represented": metrics[
                "plan_api_registry_references_represented"
            ],
            "registry_references_observed": metrics[
                "plan_api_registry_references_observed"
            ],
        },
    }
    for _, (relationship_type, metric_prefix) in direct_relationships.items():
        coverage[relationship_type] = {
            "canonical_edges": counts[relationship_type],
            "references_represented": metrics[f"{metric_prefix}_represented"],
            "references_observed": metrics[f"{metric_prefix}_observed"],
        }
    coverage["api_uses_catalog_property"] = {
        "canonical_edges": counts["api_uses_catalog_property"],
        "canonical_catalog_property_identities": sum(
            identity["canonical_object_type"] == "catalog_property"
            for identity in identities.values()
        ),
    }
    coverage["api_invokes_target"] = {
        "canonical_edges": counts["api_invokes_target"],
        "accepted_explicit_target_references": 0,
    }
    coverage["task_007_unresolved_occurrences"] = {
        "promoted_to_edge_provenance": sum(
            occurrence["extracted_record_id"]
            in {
                occurrence_id
                for edge in edge_records
                for occurrence_id in edge["contributing_extracted_record_ids"]
            }
            for occurrence in phase2.get("unresolved_occurrences", [])
        ),
        "observed": len(phase2.get("unresolved_occurrences", [])),
    }
    return {"edges": edge_records, "summary": summary, "coverage": coverage}


def write_relationship_index(
    phase2_path: Path, phase1_path: Path, output_root: Path
) -> dict[str, Any]:
    phase2 = json.loads(phase2_path.read_text(encoding="utf-8"))
    result = build_relationships(phase2, _load_jsonl(phase1_path))
    output_path = output_root / OUTPUT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(
            json.dumps(edge, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for edge in result["edges"]
        ),
        encoding="utf-8",
    )
    return {"summary": result["summary"], "coverage": result["coverage"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase2",
        type=Path,
        default=Path("indexes/apic_identity_resolution.json"),
    )
    parser.add_argument(
        "--phase1", type=Path, default=Path("indexes/extracted_records.jsonl")
    )
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    result = write_relationship_index(args.phase2, args.phase1, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
