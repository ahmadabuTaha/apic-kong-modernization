import hashlib
import json
from pathlib import Path

from identity_resolver import OUTPUT_RELATIVE_PATH, ResolverLookups, resolve_identities
from identity_resolver.resolver import resolve_records


def _record(
    record_id: str,
    object_type: str,
    path: str,
    *,
    family: str = "APIC_COLLECTION",
    pointer: str = "",
    apic_id: str | None = None,
    url: str | None = None,
    name: str | None = None,
    version: str | None = None,
    org: str | None = "org-url",
    catalog: str | None = "catalog-url",
    **extra: object,
) -> dict:
    value = {
        "extracted_record_id": record_id,
        "canonical_object_type_candidate": object_type,
        "extraction_status": "EXTRACTED",
        "failure_reasons": [],
        "source_relative_path": path,
        "source_sha256": hashlib.sha256(record_id.encode()).hexdigest(),
        "source_schema_family": family,
        "source_object_pointer": pointer,
        "apic_object_id": apic_id,
        "apic_object_url": url,
        "name": name,
        "title": name,
        "version": version,
        "org_url": org,
        "catalog_url": catalog,
    }
    value.update(extra)
    return value


def _complete_evidence() -> list[dict]:
    api_url = "https://apic.example/catalogs/c/apis/api-1"
    product_url = "https://apic.example/catalogs/c/products/product-1"
    consumer_url = "https://apic.example/consumer-orgs/consumer-1"
    app_url = "https://apic.example/apps/app-1"
    copy_path = "staging/products/_catalog/pet_1.0.0.yaml"
    product_artifact = _record(
        "product-artifact",
        "product",
        "staging/products/_catalog/pet-product_1.0.0.yaml",
        family="APIC_PRODUCT",
        name="pet-product",
        version="1.0.0",
        org=None,
        catalog=None,
        api_references=[
            {
                "api_key": "pet-key",
                "raw_ref": "/export/staging/products/_catalog/pet_1.0.0.yaml",
                "mapped_source_relative_path": copy_path,
            }
        ],
    )
    product_registry = _record(
        "product-registry",
        "product",
        "staging/products/_catalog/_list.json",
        pointer="/results/0",
        apic_id="product-1",
        url=product_url,
        name="pet-product",
        version="1.0.0",
        api_urls=[api_url],
    )
    return [
        _record(
            "api-artifact",
            "api_artifact",
            "staging/apis/_catalog/pet_1.0.0.yaml",
            family="OPENAPI_DOCUMENT",
            name="pet",
            version="1.0.0",
            org=None,
            catalog=None,
        ),
        _record(
            "api-registry",
            "api_artifact",
            "staging/apis/_catalog/_list.json",
            pointer="/results/0",
            apic_id="api-1",
            url=api_url,
            name="pet",
            version="1.0.0",
        ),
        _record(
            "api-copy",
            "api_artifact",
            copy_path,
            family="OPENAPI_DOCUMENT",
            name="pet",
            version="1.0.0",
            org=None,
            catalog=None,
        ),
        _record(
            "unreferenced-copy",
            "api_artifact",
            "staging/products/_catalog/orphan_1.0.0.yaml",
            family="OPENAPI_DOCUMENT",
            name="pet",
            version="1.0.0",
            org=None,
            catalog=None,
        ),
        product_artifact,
        product_registry,
        _record(
            "artifact-plan",
            "plan",
            product_artifact["source_relative_path"],
            family="APIC_PRODUCT",
            pointer="/plans/default",
            name="default",
            org=None,
            catalog=None,
            parent_extracted_record_id="product-artifact",
            plan_key="default",
            api_keys=["pet-key"],
        ),
        _record(
            "registry-plan",
            "plan",
            product_registry["source_relative_path"],
            pointer="/results/0/plans/0",
            name="default",
            parent_extracted_record_id="product-registry",
            plan_key="default",
            api_references=[
                {
                    "apic_object_id": "api-1",
                    "apic_object_url": api_url,
                    "name": "pet",
                    "version": "1.0.0",
                }
            ],
        ),
        _record(
            "consumer-detail",
            "consumer_org",
            "staging/consumer-orgs/consumer.json",
            family="APIC_RESOURCE",
            apic_id="consumer-1",
            url=consumer_url,
            name="consumer",
        ),
        _record(
            "consumer-list",
            "consumer_org",
            "staging/consumer-orgs/_list.json",
            pointer="/results/0",
            apic_id="consumer-1",
            url=consumer_url,
            name="consumer",
        ),
        _record(
            "application",
            "application",
            "staging/apps/apps.json",
            apic_id="app-1",
            url=app_url,
            name="app",
            consumer_org_url=consumer_url,
        ),
        _record(
            "credential",
            "credential",
            "staging/credentials/credentials.json",
            apic_id="credential-1",
            url=f"{app_url}/credentials/credential-1",
            name="credential",
            app_url=app_url,
            consumer_org_url=consumer_url,
            client_id_present=True,
            hashed_secret_present=True,
        ),
        _record(
            "subscription",
            "subscription",
            "staging/subscriptions/subscriptions.json",
            apic_id="subscription-1",
            url=f"{app_url}/subscriptions/subscription-1",
            name="subscription",
            app_url=app_url,
            consumer_org_url=consumer_url,
            product_url=product_url,
            plan="default",
        ),
        _record(
            "registry-only-api",
            "api_artifact",
            "staging/apis/_catalog/_list.json",
            pointer="/results/1",
            apic_id="api-2",
            url="https://apic.example/catalogs/c/apis/api-2",
            name="registry-only-api",
            version="1.0.0",
        ),
        _record(
            "registry-only-product",
            "product",
            "staging/products/_catalog/_list.json",
            pointer="/results/1",
            apic_id="product-2",
            url="https://apic.example/catalogs/c/products/product-2",
            name="registry-only-product",
            version="1.0.0",
            api_urls=[],
        ),
        _record(
            "registry-only-plan",
            "plan",
            "staging/products/_catalog/_list.json",
            pointer="/results/1/plans/0",
            name="basic",
            parent_extracted_record_id="registry-only-product",
            plan_key="basic",
            api_references=[],
        ),
    ]


def test_lookup_uses_exact_url_and_apic_id_with_compatible_scope() -> None:
    records = _complete_evidence()
    lookups = ResolverLookups(records)
    assert [value["extracted_record_id"] for value in lookups.exact_self_url(
        "https://apic.example/consumer-orgs/consumer-1", "consumer_org"
    )] == ["consumer-list", "consumer-detail"]
    assert [value["extracted_record_id"] for value in lookups.compatible_id_scope(
        "application", "app-1", org_url="org-url", catalog_url="catalog-url"
    )] == ["application"]
    assert lookups.compatible_id_scope(
        "application", "app-1", org_url="different-org", catalog_url="catalog-url"
    ) == []


def test_scoped_bridges_contextual_plans_and_exact_references() -> None:
    result = resolve_records(_complete_evidence())
    summary = result["summary"]
    assert summary["api_bridge"] == {
        "authoritative_count": 1,
        "resolved": 1,
        "unresolved": 0,
        "registry_only": 1,
        "artifact_only": 0,
    }
    assert summary["product_bridge"] == {
        "authoritative_count": 1,
        "resolved": 1,
        "unresolved": 0,
        "registry_only": 1,
        "artifact_only": 0,
    }
    assert summary["product_api_refs"] == {"RESOLVED": 1}
    assert summary["plan_api_refs"] == {"RESOLVED": 1}
    assert summary["reference_resolutions"] == {
        "application_consumer_org_url": {"RESOLVED": 1},
        "credential_app_url": {"RESOLVED": 1},
        "subscription_app_url": {"RESOLVED": 1},
        "subscription_plan": {"RESOLVED": 1},
        "subscription_product_url": {"RESOLVED": 1},
    }
    assert summary["canonical_identity_counts"]["consumer_org"] == 1
    assert summary["canonical_identity_counts"]["plan"] == 2
    assert summary["unresolved_product_location_api_occurrences"] == 1
    assert result["unresolved_occurrences"][0]["extracted_record_id"] == "unreferenced-copy"

    api = next(
        value
        for value in result["canonical_identity_records"]
        if value["canonical_object_type"] == "api_artifact"
        and value["apic_object_id"] == "api-1"
    )
    assert api["authoritative_artifact_occurrence_ids"] == ["api-artifact"]
    assert api["product_location_occurrence_ids"] == ["api-copy"]


def test_name_only_and_failed_product_convergence_do_not_merge() -> None:
    records = _complete_evidence()
    records.extend(
        [
            _record(
                "same-name-consumer-a",
                "consumer_org",
                "staging/consumer-orgs/a.json",
                family="APIC_RESOURCE",
                apic_id="consumer-a",
                url="https://apic.example/consumer-orgs/a",
                name="same-name",
            ),
            _record(
                "same-name-consumer-b",
                "consumer_org",
                "staging/consumer-orgs/b.json",
                family="APIC_RESOURCE",
                apic_id="consumer-b",
                url="https://apic.example/consumer-orgs/b",
                name="same-name",
            ),
        ]
    )
    product_registry = next(
        value for value in records if value["extracted_record_id"] == "product-registry"
    )
    product_registry["api_urls"] = []
    result = resolve_records(records)
    assert result["summary"]["product_bridge"]["resolved"] == 0
    assert result["summary"]["product_bridge"]["unresolved"] == 1
    same_name = [
        value
        for value in result["canonical_identity_records"]
        if value["canonical_object_type"] == "consumer_org" and value["name"] == "same-name"
    ]
    assert len(same_name) == 2


def test_unresolved_ambiguous_and_broken_references_are_preserved() -> None:
    records = _complete_evidence()
    subscription = next(
        value for value in records if value["extracted_record_id"] == "subscription"
    )
    subscription["app_url"] = "https://apic.example/apps/missing"
    subscription["plan"] = None
    # Product registries with the same self URL are one identity, so duplicate
    # source occurrences do not create a false ambiguity.
    duplicate = dict(
        next(value for value in records if value["extracted_record_id"] == "product-registry")
    )
    duplicate["extracted_record_id"] = "product-registry-duplicate"
    duplicate["source_object_pointer"] = "/results/2"
    records.append(duplicate)
    result = resolve_records(records)
    summary = result["summary"]["reference_resolutions"]
    assert summary["subscription_app_url"] == {"BROKEN_REFERENCE": 1}
    assert summary["subscription_plan"] == {"UNRESOLVED": 1}
    product = next(
        value
        for value in result["canonical_identity_records"]
        if value["canonical_object_type"] == "product" and value["apic_object_id"] == "product-1"
    )
    assert product["registry_occurrence_ids"] == [
        "product-registry",
        "product-registry-duplicate",
    ]

    ambiguous_records = _complete_evidence()
    duplicate_copy = dict(
        next(value for value in ambiguous_records if value["extracted_record_id"] == "api-copy")
    )
    duplicate_copy["extracted_record_id"] = "api-copy-duplicate"
    ambiguous_records.append(duplicate_copy)
    ambiguous = resolve_records(ambiguous_records)
    assert ambiguous["summary"]["product_api_refs"] == {"AMBIGUOUS": 1}

    unmapped_records = _complete_evidence()
    product_artifact = next(
        value for value in unmapped_records if value["extracted_record_id"] == "product-artifact"
    )
    product_artifact["api_references"][0]["mapped_source_relative_path"] = None
    unmapped = resolve_records(unmapped_records)
    assert unmapped["summary"]["product_api_refs"] == {"UNRESOLVED": 1}


def test_output_is_deterministic_redacted_and_does_not_touch_staging(tmp_path: Path) -> None:
    project = tmp_path / "project"
    index = project / "indexes/extracted_records.jsonl"
    index.parent.mkdir(parents=True)
    records = _complete_evidence()
    index.write_text(
        "".join(json.dumps(value, sort_keys=True) + "\n" for value in records),
        encoding="utf-8",
    )
    sentinel = project / "staging/sentinel.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("immutable evidence", encoding="utf-8")
    before = hashlib.sha256(sentinel.read_bytes()).hexdigest()

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    assert resolve_identities(index, first_root) == resolve_identities(index, second_root)
    first = (first_root / OUTPUT_RELATIVE_PATH).read_bytes()
    second = (second_root / OUTPUT_RELATIVE_PATH).read_bytes()
    assert first == second
    assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == before
    text = first.decode()
    assert "client_id_present" not in text
    assert "hashed_secret_present" not in text
