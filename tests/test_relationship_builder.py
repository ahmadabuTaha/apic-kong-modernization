import hashlib
import json
from pathlib import Path

import pytest

from relationship_builder import (
    APPROVED_RELATIONSHIP_TYPES,
    OUTPUT_RELATIVE_PATH,
    build_relationships,
    write_relationship_index,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "indexes/extracted_records.jsonl"
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
TASK_008_EVIDENCE = ROOT / "tests/evidence/task-008"


def _occurrence(
    record_id: str,
    object_type: str,
    path: str,
    *,
    family: str = "APIC_COLLECTION",
    pointer: str = "",
    url: str | None = None,
    **extra: object,
) -> dict:
    record = {
        "extracted_record_id": record_id,
        "canonical_object_type_candidate": object_type,
        "source_relative_path": path,
        "source_object_pointer": pointer,
        "source_schema_family": family,
        "source_sha256": hashlib.sha256(record_id.encode()).hexdigest(),
        "apic_object_url": url,
    }
    record.update(extra)
    return record


def _identity(
    identity_id: str,
    object_type: str,
    *,
    url: str | None = None,
    contributing: list[str] | None = None,
    authoritative: list[str] | None = None,
    registry: list[str] | None = None,
    references: list[dict] | None = None,
    **extra: object,
) -> dict:
    value = {
        "canonical_identity_record_id": identity_id,
        "canonical_object_type": object_type,
        "apic_object_url": url,
        "contributing_extracted_record_ids": contributing or [],
        "authoritative_artifact_occurrence_ids": authoritative or [],
        "registry_occurrence_ids": registry or [],
        "product_location_occurrence_ids": [],
        "references": references or [],
    }
    value.update(extra)
    return value


def _resolved(field: str, raw: str, target: str, **extra: object) -> dict:
    value = {
        "field": field,
        "raw_value": raw,
        "outcome": "RESOLVED",
        "target_canonical_identity_record_ids": [target],
    }
    value.update(extra)
    return value


def _synthetic_inputs() -> tuple[dict, list[dict]]:
    api_url = "https://apic.example/apis/api"
    product_url = "https://apic.example/products/product"
    consumer_url = "https://apic.example/consumer-orgs/consumer"
    app_url = "https://apic.example/apps/app"
    phase1 = [
        _occurrence(
            "product-art",
            "product",
            "staging/products/_catalog/product.yaml",
            family="APIC_PRODUCT",
        ),
        _occurrence(
            "product-reg",
            "product",
            "staging/products/_catalog/_list.json",
            pointer="/results/0",
            url=product_url,
            api_urls=[api_url],
        ),
        _occurrence(
            "api-art",
            "api_artifact",
            "staging/apis/_catalog/api.yaml",
            family="OPENAPI_DOCUMENT",
        ),
        _occurrence(
            "api-reg",
            "api_artifact",
            "staging/apis/_catalog/_list.json",
            pointer="/results/0",
            url=api_url,
        ),
        _occurrence(
            "plan-art",
            "plan",
            "staging/products/_catalog/product.yaml",
            family="APIC_PRODUCT",
            pointer="/plans/default",
        ),
        _occurrence(
            "plan-reg",
            "plan",
            "staging/products/_catalog/_list.json",
            pointer="/results/0/plans/0",
            api_references=[{"apic_object_url": api_url}],
        ),
        _occurrence(
            "consumer",
            "consumer_org",
            "staging/consumer-orgs/_list.json",
            url=consumer_url,
        ),
        _occurrence(
            "application",
            "application",
            "staging/apps/apps.json",
            url=app_url,
        ),
        _occurrence(
            "credential",
            "credential",
            "staging/credentials/credentials.json",
            url=f"{app_url}/credentials/credential",
            client_id_present=True,
            hashed_secret_present=True,
        ),
        _occurrence(
            "subscription",
            "subscription",
            "staging/subscriptions/subscriptions.json",
            url=f"{app_url}/subscriptions/subscription",
        ),
        _occurrence(
            "unresolved-copy",
            "api_artifact",
            "staging/products/_catalog/unreferenced.yaml",
            family="OPENAPI_DOCUMENT",
            name="api",
            version="1.0.0",
            source_sha256=hashlib.sha256(b"api-art").hexdigest(),
        ),
        _occurrence(
            "broken-application",
            "application",
            "staging/apps/broken.json",
            url="https://apic.example/apps/broken",
        ),
    ]
    identities = [
        _identity(
            "product",
            "product",
            url=product_url,
            contributing=["product-art", "product-reg"],
            authoritative=["product-art"],
            registry=["product-reg"],
            references=[
                _resolved(
                    "product_api_ref",
                    "/export/staging/products/_catalog/api.yaml",
                    "api",
                    mapped_source_relative_path="staging/products/_catalog/api.yaml",
                )
            ],
        ),
        _identity(
            "api",
            "api_artifact",
            url=api_url,
            contributing=["api-art", "api-reg"],
            authoritative=["api-art"],
            registry=["api-reg"],
        ),
        _identity(
            "plan",
            "plan",
            contributing=["plan-art", "plan-reg"],
            authoritative=["plan-art"],
            registry=["plan-reg"],
            references=[_resolved("plan_api_key", "api-key", "api")],
            parent_product_identity_record_id="product",
            plan_key="default",
        ),
        _identity(
            "consumer",
            "consumer_org",
            url=consumer_url,
            contributing=["consumer"],
            registry=["consumer"],
        ),
        _identity(
            "application",
            "application",
            url=app_url,
            contributing=["application"],
            registry=["application"],
            references=[
                _resolved("consumer_org_url", consumer_url, "consumer")
            ],
        ),
        _identity(
            "credential",
            "credential",
            url=f"{app_url}/credentials/credential",
            contributing=["credential"],
            registry=["credential"],
            references=[_resolved("app_url", app_url, "application")],
        ),
        _identity(
            "subscription",
            "subscription",
            url=f"{app_url}/subscriptions/subscription",
            contributing=["subscription"],
            registry=["subscription"],
            references=[
                _resolved("app_url", app_url, "application"),
                _resolved("product_url", product_url, "product"),
                _resolved("plan", "default", "plan"),
            ],
        ),
        _identity(
            "broken-application",
            "application",
            url="https://apic.example/apps/broken",
            contributing=["broken-application"],
            registry=["broken-application"],
            references=[
                {
                    "field": "consumer_org_url",
                    "raw_value": "https://apic.example/consumer-orgs/missing",
                    "outcome": "BROKEN_REFERENCE",
                    "target_canonical_identity_record_ids": [],
                },
                {
                    "field": "consumer_org_url",
                    "raw_value": "ambiguous",
                    "outcome": "AMBIGUOUS",
                    "target_canonical_identity_record_ids": ["consumer", "other"],
                },
                {
                    "field": "consumer_org_url",
                    "raw_value": None,
                    "outcome": "UNRESOLVED",
                    "target_canonical_identity_record_ids": [],
                },
            ],
        ),
    ]
    phase2 = {
        "canonical_identity_records": identities,
        "unresolved_occurrences": [
            {
                "canonical_object_type": "api_artifact",
                "outcome": "UNRESOLVED",
                "extracted_record_id": "unresolved-copy",
                "source_relative_path": "staging/products/_catalog/unreferenced.yaml",
                "source_object_pointer": "",
            }
        ],
    }
    return phase2, phase1


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_builds_only_approved_canonical_edges_and_deduplicates_provenance() -> None:
    phase2, phase1 = _synthetic_inputs()
    first = build_relationships(phase2, phase1)
    second = build_relationships(phase2, list(reversed(phase1)))

    assert first == second
    assert first["summary"]["total_canonical_edges"] == 8
    assert set(first["summary"]["counts_by_relationship_type"]) == set(
        APPROVED_RELATIONSHIP_TYPES
    )
    expected_nonzero = {
        "product_contains_api",
        "product_contains_plan",
        "plan_entitles_api",
        "application_belongs_to_consumer_org",
        "credential_belongs_to_application",
        "subscription_belongs_to_application",
        "subscription_targets_product",
        "subscription_uses_plan",
    }
    assert {
        relationship_type
        for relationship_type, count in first["summary"][
            "counts_by_relationship_type"
        ].items()
        if count
    } == expected_nonzero

    product_api = next(
        edge
        for edge in first["edges"]
        if edge["relationship_type"] == "product_contains_api"
    )
    assert product_api["source_canonical_identity_record_id"] == "product"
    assert product_api["target_canonical_identity_record_id"] == "api"
    assert product_api["evidence_source_categories"] == [
        "authoritative_artifact",
        "registry_reference",
    ]
    assert product_api["contributing_extracted_record_ids"] == [
        "product-art",
        "product-reg",
    ]
    assert product_api["relationship_id"] == (
        "apic-relationship:sha256:"
        "1f1ef529c9a961c1a321039d39865ef2485bc2c12c113bcee715186e74f29700"
    )


def test_excludes_unresolved_ambiguous_broken_name_and_hash_only_evidence() -> None:
    phase2, phase1 = _synthetic_inputs()
    result = build_relationships(phase2, phase1)
    all_contributors = {
        occurrence_id
        for edge in result["edges"]
        for occurrence_id in edge["contributing_extracted_record_ids"]
    }
    assert "unresolved-copy" not in all_contributors
    assert not any(
        edge["source_canonical_identity_record_id"] == "broken-application"
        for edge in result["edges"]
    )
    assert result["summary"]["excluded_evidence_by_resolution_outcome"] == {
        "UNRESOLVED": 2,
        "AMBIGUOUS": 1,
        "BROKEN_REFERENCE": 1,
    }
    serialized = json.dumps(result, sort_keys=True)
    assert "client_id_present" not in serialized
    assert "hashed_secret_present" not in serialized


@pytest.mark.skipif(
    not PHASE1.is_file() or not PHASE2.is_file(),
    reason="local ignored Phase 1/2 indexes are required for full-corpus validation",
)
def test_full_corpus_is_deterministic_complete_redacted_and_source_safe(
    tmp_path: Path,
) -> None:
    staging = ROOT / "staging"
    before = _tree_hashes(staging)
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = write_relationship_index(PHASE2, PHASE1, first_root)
    second = write_relationship_index(PHASE2, PHASE1, second_root)
    first_bytes = (first_root / OUTPUT_RELATIVE_PATH).read_bytes()
    second_bytes = (second_root / OUTPUT_RELATIVE_PATH).read_bytes()

    assert first == second
    assert first_bytes == second_bytes
    assert first["summary"]["total_canonical_edges"] == 9589
    assert first["summary"]["counts_by_relationship_type"] == {
        "product_contains_api": 2611,
        "product_contains_plan": 596,
        "plan_entitles_api": 2799,
        "application_belongs_to_consumer_org": 256,
        "credential_belongs_to_application": 270,
        "subscription_belongs_to_application": 1019,
        "subscription_targets_product": 1019,
        "subscription_uses_plan": 1019,
        "api_uses_catalog_property": 0,
        "api_invokes_target": 0,
    }
    assert first["coverage"]["task_007_unresolved_occurrences"] == {
        "promoted_to_edge_provenance": 0,
        "observed": 113,
    }
    assert _tree_hashes(staging) == before

    committed_counts = json.loads(
        (TASK_008_EVIDENCE / "relationship_counts.json").read_text(encoding="utf-8")
    )
    committed_coverage = json.loads(
        (TASK_008_EVIDENCE / "relationship_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    assert committed_counts == first["summary"]
    assert committed_coverage == first["coverage"]

    evidence_bytes = first_bytes + b"".join(
        path.read_bytes()
        for path in (
            TASK_008_EVIDENCE / "relationship_counts.json",
            TASK_008_EVIDENCE / "relationship_coverage.json",
            TASK_008_EVIDENCE / "relationship_samples.jsonl",
        )
    )
    sensitive_values: list[bytes] = []
    for path in (staging / "credentials").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    sensitive_values.append(value.encode())
    assert sensitive_values
    assert all(value not in evidence_bytes for value in sensitive_values)
