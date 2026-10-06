import hashlib
import json
from pathlib import Path

import yaml

from source_extractor import extract_repository


APPROVED_STATUSES = {"EXTRACTED", "EXTRACTION_PARTIAL", "EXTRACTION_FAILED"}
APPROVED_REASONS = {
    "required_field_missing",
    "unsupported_object_shape",
    "source_artifact_malformed",
    "field_type_mismatch",
}
APPROVED_OBJECT_TYPES = {
    "api_artifact",
    "product",
    "plan",
    "consumer_org",
    "application",
    "credential",
    "subscription",
    "catalog_config",
    "catalog_property",
}
COMMON_FIELDS = {
    "extracted_record_id",
    "canonical_object_type_candidate",
    "extraction_status",
    "failure_reasons",
    "source_relative_path",
    "source_sha256",
    "source_schema_family",
    "source_object_pointer",
    "apic_object_id",
    "apic_object_url",
    "name",
    "title",
    "version",
    "org_url",
    "catalog_url",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _records(output_root: Path) -> list[dict]:
    path = output_root / "indexes/extracted_records.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _build_source(project_root: Path) -> Path:
    source = project_root / "staging"
    api_definition = {
        "swagger": "2.0",
        "info": {"x-ibm-name": "pet", "title": "Pet", "version": "1.0.0"},
        "paths": {},
    }
    _write_yaml(source / "apis/_catalog/pet_1.0.0.yaml", api_definition)
    _write_json(
        source / "apis/_catalog/_list.json",
        {
            "results": [
                {
                    "type": "api",
                    "id": "api-id",
                    "url": "https://management.example/apis/api-id",
                    "name": "pet",
                    "title": "Pet",
                    "version": "1.0.0",
                    "org_url": "https://management.example/orgs/org-id",
                    "catalog_url": "https://management.example/catalogs/catalog-id",
                }
            ],
            "total_results": 1,
        },
    )

    _write_yaml(source / "products/_catalog/pet_1.0.0.yaml", api_definition)
    raw_ref = "/backup/export/staging/products/_catalog/pet_1.0.0.yaml"
    _write_yaml(
        source / "products/_catalog/pet-product_1.0.0.yaml",
        {
            "product": "1.0.0",
            "info": {"name": "pet-product", "title": "Pet Product", "version": "1.0.0"},
            "apis": {"pet-key": {"$ref": raw_ref}},
            "plans": {
                "default-plan": {
                    "title": "Default Plan",
                    "apis": {"pet-key": {}},
                }
            },
        },
    )
    _write_json(
        source / "products/_catalog/_list.json",
        {
            "results": [
                {
                    "type": "product",
                    "id": "product-id",
                    "url": "https://management.example/products/product-id",
                    "name": "pet-product",
                    "title": "Pet Product",
                    "version": "1.0.0",
                    "org_url": "https://management.example/orgs/org-id",
                    "catalog_url": "https://management.example/catalogs/catalog-id",
                    "api_urls": ["https://management.example/apis/api-id"],
                    "plans": [
                        {
                            "name": "default-plan",
                            "title": "Default Plan",
                            "apis": [
                                {
                                    "id": "api-id",
                                    "url": "https://management.example/apis/api-id",
                                    "name": "pet",
                                    "version": "1.0.0",
                                }
                            ],
                        }
                    ],
                }
            ],
            "total_results": 1,
        },
    )

    consumer = {
        "type": "consumer_org",
        "api_version": "2.0.0",
        "id": "consumer-id",
        "url": "https://management.example/consumer-orgs/consumer-id",
        "name": "consumer",
        "title": "Consumer",
        "state": "enabled",
        "org_url": "https://management.example/orgs/org-id",
        "catalog_url": "https://management.example/catalogs/catalog-id",
    }
    _write_json(source / "consumer-orgs/consumer.json", consumer)
    _write_json(
        source / "consumer-orgs/_list.json",
        {"results": [consumer], "total_results": 1},
    )

    app = {
        "type": "app",
        "id": "app-id",
        "url": "https://management.example/apps/app-id",
        "name": "app",
        "title": "App",
        "state": "enabled",
        "lifecycle_state": "production",
        "consumer_org_url": consumer["url"],
        "app_credential_urls": ["https://management.example/apps/app-id/credentials/credential-id"],
        "org_url": consumer["org_url"],
        "catalog_url": consumer["catalog_url"],
    }
    _write_json(source / "apps/consumer__apps.json", {"results": [app], "total_results": 1})

    credential = {
        "type": "credential",
        "id": "credential-id",
        "url": app["app_credential_urls"][0],
        "name": "credential",
        "app_url": app["url"],
        "consumer_org_url": consumer["url"],
        "org_url": consumer["org_url"],
        "catalog_url": consumer["catalog_url"],
        "client_id": "sensitive-client-id-value",
        "client_secret": "sensitive-client-secret-value",
        "client_secret_hashed": "sensitive-hashed-secret-value",
        "unknown_sensitive_payload": "sensitive-unknown-value",
    }
    _write_json(
        source / "credentials/consumer__app__credentials.json",
        {"results": [credential], "total_results": 1},
    )

    subscription = {
        "type": "subscription",
        "id": "subscription-id",
        "url": "https://management.example/subscriptions/subscription-id",
        "name": "subscription",
        "app_url": app["url"],
        "consumer_org_url": consumer["url"],
        "product_url": "https://management.example/products/product-id",
        "plan": "default-plan",
        "org_url": consumer["org_url"],
        "catalog_url": consumer["catalog_url"],
    }
    _write_json(
        source / "subscriptions/consumer__app__subs.json",
        {"results": [subscription], "total_results": 1},
    )

    _write_yaml(
        source / "config/staging.yaml",
        {
            "type": "catalog",
            "api_version": "2.0.0",
            "id": "catalog-id",
            "url": "https://management.example/catalogs/catalog-id",
            "name": "staging",
            "org_url": "https://management.example/orgs/org-id",
        },
    )
    _write_json(source / "config/roles.json", [])
    _write_json(source / "config/malformed.json", {"results": "not-an-array"})
    invalid_json = source / "config/invalid.json"
    invalid_json.write_text('{"results":', encoding="utf-8")

    wsdl = source / "apis/_catalog/pet.wsdl"
    wsdl.write_text(
        '<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" '
        'name="PetService" targetNamespace="urn:pet"/>',
        encoding="utf-8",
    )
    unsupported = source / "notes.md"
    unsupported.write_text("unsupported evidence", encoding="utf-8")
    return source


def test_extracts_deterministic_occurrences_and_preserves_source(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = _build_source(project)
    before = {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source.rglob("*")
        if path.is_file()
    }

    first = tmp_path / "first"
    second = tmp_path / "second"
    first_summary = extract_repository(source, first, project_root=project)
    second_summary = extract_repository(source, second, project_root=project)

    assert first_summary == second_summary
    assert (first / "indexes/extracted_records.jsonl").read_bytes() == (
        second / "indexes/extracted_records.jsonl"
    ).read_bytes()
    records = _records(first)
    assert len({record["extracted_record_id"] for record in records}) == len(records)
    assert all(record["extraction_status"] in APPROVED_STATUSES for record in records)
    assert all(set(record["failure_reasons"]) <= APPROVED_REASONS for record in records)
    assert all(COMMON_FIELDS <= set(record) for record in records)
    assert all(
        record["canonical_object_type_candidate"] in APPROVED_OBJECT_TYPES | {None}
        for record in records
    )

    after = {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_product_refs_plans_and_management_references_are_preserved(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = _build_source(project)
    output = tmp_path / "generated"
    extract_repository(source, output, project_root=project)
    records = _records(output)

    product = next(
        record
        for record in records
        if record["canonical_object_type_candidate"] == "product"
        and record["source_object_pointer"] == ""
    )
    assert product["api_references"] == [
        {
            "api_key": "pet-key",
            "raw_ref": "/backup/export/staging/products/_catalog/pet_1.0.0.yaml",
            "mapped_source_relative_path": "staging/products/_catalog/pet_1.0.0.yaml",
        }
    ]
    plan = next(
        record
        for record in records
        if record["canonical_object_type_candidate"] == "plan"
        and record["source_relative_path"].endswith("pet-product_1.0.0.yaml")
    )
    assert plan["parent_extracted_record_id"] == product["extracted_record_id"]
    assert plan["plan_key"] == "default-plan"
    assert plan["api_keys"] == ["pet-key"]

    application = next(
        record for record in records if record["canonical_object_type_candidate"] == "application"
    )
    credential = next(
        record for record in records if record["canonical_object_type_candidate"] == "credential"
    )
    subscription = next(
        record for record in records if record["canonical_object_type_candidate"] == "subscription"
    )
    assert application["consumer_org_url"].endswith("/consumer-id")
    assert application["app_credential_urls"] == [credential["apic_object_url"]]
    assert credential["app_url"] == application["apic_object_url"]
    assert subscription["app_url"] == application["apic_object_url"]
    assert subscription["consumer_org_url"] == application["consumer_org_url"]
    assert subscription["product_url"].endswith("/product-id")
    assert subscription["plan"] == "default-plan"
    assert sum(
        record["canonical_object_type_candidate"] == "api_artifact" and record["name"] == "pet"
        for record in records
    ) == 3
    assert sum(
        record["canonical_object_type_candidate"] == "product"
        and record["name"] == "pet-product"
        for record in records
    ) == 2


def test_unmappable_product_refs_keep_raw_evidence_without_guessing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = _build_source(project)
    product_path = source / "products/_catalog/pet-product_1.0.0.yaml"
    product = yaml.safe_load(product_path.read_text(encoding="utf-8"))
    product["apis"] = {
        "missing-segment": {"$ref": "/backup/export/products/pet.yaml"},
        "repeated-segment": {
            "$ref": "/backup/staging/products/staging/products/_catalog/pet_1.0.0.yaml"
        },
    }
    _write_yaml(product_path, product)

    output = tmp_path / "generated"
    extract_repository(source, output, project_root=project)
    record = next(
        item
        for item in _records(output)
        if item["canonical_object_type_candidate"] == "product"
        and item["source_object_pointer"] == ""
    )
    assert record["api_references"] == [
        {
            "api_key": "missing-segment",
            "raw_ref": "/backup/export/products/pet.yaml",
            "mapped_source_relative_path": None,
        },
        {
            "api_key": "repeated-segment",
            "raw_ref": "/backup/staging/products/staging/products/_catalog/pet_1.0.0.yaml",
            "mapped_source_relative_path": None,
        },
    ]


def test_credentials_are_allowlisted_and_empty_collections_emit_no_objects(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    source = _build_source(project)
    output = tmp_path / "generated"
    extract_repository(source, output, project_root=project)
    index_text = (output / "indexes/extracted_records.jsonl").read_text(encoding="utf-8")
    for value in (
        "sensitive-client-id-value",
        "sensitive-client-secret-value",
        "sensitive-hashed-secret-value",
        "sensitive-unknown-value",
    ):
        assert value not in index_text

    records = _records(output)
    credential = next(
        record for record in records if record["canonical_object_type_candidate"] == "credential"
    )
    assert credential["client_id_present"] is True
    assert credential["client_secret_present"] is True
    assert credential["hashed_secret_present"] is True
    assert not any(
        record["source_relative_path"] == "staging/config/roles.json" for record in records
    )
    assert not any(
        record["canonical_object_type_candidate"] == "catalog_property" for record in records
    )


def test_wsdl_malformed_and_unsupported_evidence_use_approved_contract(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    source = _build_source(project)
    output = tmp_path / "generated"
    extract_repository(source, output, project_root=project)
    records = _records(output)

    wsdl = next(record for record in records if record["source_relative_path"].endswith("pet.wsdl"))
    assert wsdl["canonical_object_type_candidate"] is None
    assert wsdl["extraction_status"] == "EXTRACTED"
    assert wsdl["definitions_name"] == "PetService"
    assert wsdl["target_namespace"] == "urn:pet"

    malformed = next(
        record for record in records if record["source_relative_path"].endswith("malformed.json")
    )
    assert malformed["extraction_status"] == "EXTRACTION_FAILED"
    assert malformed["failure_reasons"] == ["field_type_mismatch"]

    invalid = next(
        record for record in records if record["source_relative_path"].endswith("invalid.json")
    )
    assert invalid["extraction_status"] == "EXTRACTION_FAILED"
    assert invalid["failure_reasons"] == ["source_artifact_malformed"]

    unsupported = next(
        record for record in records if record["source_relative_path"] == "staging/notes.md"
    )
    assert unsupported["extraction_status"] == "EXTRACTION_FAILED"
    assert unsupported["failure_reasons"] == ["unsupported_object_shape"]
