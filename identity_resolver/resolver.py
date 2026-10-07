"""Phase 2 deterministic APIC identity and reference resolver.

This module consumes the frozen Phase 1 occurrence index.  It deliberately
does not construct relationship-graph edges or infer semantic identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


OUTPUT_RELATIVE_PATH = Path("indexes/apic_identity_resolution.json")

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
def _stable_id(object_type: str, identity_key: Any) -> str:
    value = json.dumps(
        [object_type, identity_key], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"apic-identity:sha256:{hashlib.sha256(value).hexdigest()}"


def _record_sort_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        record.get("source_relative_path") or "",
        record.get("source_object_pointer") or "",
        record.get("extracted_record_id") or "",
    )


def _scope_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for field in ("org_url", "catalog_url"):
        a, b = left.get(field), right.get(field)
        if a is not None and b is not None and a != b:
            return False
    return True


class ResolverLookups:
    """Deterministically indexed Phase 1 occurrence evidence."""

    def __init__(self, records: Iterable[dict[str, Any]]) -> None:
        self.records = sorted(records, key=_record_sort_key)
        self.by_record_id = {
            record["extracted_record_id"]: record for record in self.records
        }
        self.by_self_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.by_apic_id: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        self.by_id_scope: dict[
            tuple[str, str, str | None, str | None], list[dict[str, Any]]
        ] = defaultdict(list)
        self.by_source_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.mapped_product_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.plans_by_product_key: dict[tuple[str, str], list[dict[str, Any]]] = (
            defaultdict(list)
        )
        self.product_api_refs: dict[tuple[str, str], list[dict[str, Any]]] = (
            defaultdict(list)
        )

        for record in self.records:
            object_type = record.get("canonical_object_type_candidate")
            url = record.get("apic_object_url")
            apic_id = record.get("apic_object_id")
            if isinstance(url, str):
                self.by_self_url[url].append(record)
            if object_type in APPROVED_OBJECT_TYPES and isinstance(apic_id, str):
                self.by_apic_id[(object_type, apic_id)].append(record)
                self.by_id_scope[
                    (object_type, apic_id, record.get("org_url"), record.get("catalog_url"))
                ].append(record)
            self.by_source_path[record["source_relative_path"]].append(record)
            if object_type == "plan" and isinstance(
                record.get("parent_extracted_record_id"), str
            ):
                key = (record["parent_extracted_record_id"], record.get("plan_key"))
                self.plans_by_product_key[key].append(record)
            if object_type == "product":
                parent_id = record["extracted_record_id"]
                for reference in record.get("api_references", []):
                    api_key = reference.get("api_key")
                    if isinstance(api_key, str):
                        self.product_api_refs[(parent_id, api_key)].append(reference)
                    mapped = reference.get("mapped_source_relative_path")
                    if isinstance(mapped, str):
                        self.mapped_product_refs[mapped].append(reference)

        for lookup in (
            self.by_self_url,
            self.by_apic_id,
            self.by_id_scope,
            self.by_source_path,
            self.plans_by_product_key,
        ):
            for values in lookup.values():
                values.sort(key=_record_sort_key)

    def exact_self_url(self, url: str, object_type: str | None = None) -> list[dict[str, Any]]:
        values = self.by_self_url.get(url, [])
        if object_type is None:
            return list(values)
        return [
            value
            for value in values
            if value.get("canonical_object_type_candidate") == object_type
        ]

    def compatible_id_scope(
        self,
        object_type: str,
        apic_id: str,
        *,
        org_url: str | None,
        catalog_url: str | None,
    ) -> list[dict[str, Any]]:
        probe = {"org_url": org_url, "catalog_url": catalog_url}
        return [
            value
            for value in self.by_apic_id.get((object_type, apic_id), [])
            if _scope_compatible(value, probe)
        ]


def _is_api_catalog_artifact(record: dict[str, Any]) -> bool:
    return (
        record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "OPENAPI_DOCUMENT"
        and record.get("source_relative_path", "").startswith("staging/apis/_catalog/")
    )


def _is_api_registry(record: dict[str, Any]) -> bool:
    return (
        record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "APIC_COLLECTION"
    )


def _is_product_copy(record: dict[str, Any]) -> bool:
    return (
        record.get("canonical_object_type_candidate") == "api_artifact"
        and record.get("source_schema_family") == "OPENAPI_DOCUMENT"
        and record.get("source_relative_path", "").startswith("staging/products/_catalog/")
    )


def _is_product_artifact(record: dict[str, Any]) -> bool:
    return (
        record.get("canonical_object_type_candidate") == "product"
        and record.get("source_schema_family") == "APIC_PRODUCT"
    )


def _is_product_registry(record: dict[str, Any]) -> bool:
    return (
        record.get("canonical_object_type_candidate") == "product"
        and record.get("source_schema_family") == "APIC_COLLECTION"
    )


def _evidence(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "extracted_record_id": record["extracted_record_id"],
        "source_relative_path": record["source_relative_path"],
        "source_object_pointer": record["source_object_pointer"],
    }


def _identity_record(
    object_type: str,
    identity_key: Any,
    occurrences: Iterable[dict[str, Any]],
    *,
    authoritative_ids: Iterable[str] = (),
    registry_ids: Iterable[str] = (),
    product_copy_ids: Iterable[str] = (),
    resolution_state: str = "STRUCTURALLY_CONFIRMED",
) -> dict[str, Any]:
    values = sorted(occurrences, key=_record_sort_key)
    authoritative = sorted(set(authoritative_ids))
    registry = sorted(set(registry_ids))
    copies = sorted(set(product_copy_ids))
    contributing = sorted(
        {value["extracted_record_id"] for value in values}
        | set(authoritative)
        | set(registry)
        | set(copies)
    )
    by_occurrence_id = {value["extracted_record_id"]: value for value in values}

    def observed(field: str) -> Any:
        if field in {"name", "title", "version"}:
            preferred_ids = authoritative + registry
        else:
            preferred_ids = registry + authoritative
        preferred = [
            by_occurrence_id[value]
            for value in preferred_ids
            if value in by_occurrence_id
        ]
        ordered = preferred + [value for value in values if value not in preferred]
        candidates = [value.get(field) for value in ordered if value.get(field) is not None]
        return candidates[0] if candidates else None

    return {
        "canonical_identity_record_id": _stable_id(object_type, identity_key),
        "canonical_object_type": object_type,
        "resolution_state": resolution_state,
        "apic_object_id": observed("apic_object_id"),
        "apic_object_url": observed("apic_object_url"),
        "org_url": observed("org_url"),
        "catalog_url": observed("catalog_url"),
        "name": observed("name"),
        "title": observed("title"),
        "version": observed("version"),
        "authoritative_artifact_occurrence_ids": authoritative,
        "registry_occurrence_ids": registry,
        "product_location_occurrence_ids": copies,
        "contributing_extracted_record_ids": contributing,
        "source_evidence": [_evidence(value) for value in values],
        "references": [],
    }


def _unique_by_name_version(
    records: Iterable[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    result: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if isinstance(record.get("name"), str) and isinstance(record.get("version"), str):
            result[(record["name"], record["version"])].append(record)
    for values in result.values():
        values.sort(key=_record_sort_key)
    return result


def _build_api_bridge(
    artifacts: list[dict[str, Any]], registries: list[dict[str, Any]]
) -> tuple[dict[str, str], set[str]]:
    artifacts_by_key = _unique_by_name_version(artifacts)
    registries_by_key = _unique_by_name_version(registries)
    bridge: dict[str, str] = {}
    unresolved: set[str] = set()
    for artifact in artifacts:
        key = (artifact.get("name"), artifact.get("version"))
        candidates = registries_by_key.get(key, [])
        if len(artifacts_by_key.get(key, [])) == 1 and len(candidates) == 1:
            bridge[artifact["extracted_record_id"]] = candidates[0]["extracted_record_id"]
        else:
            unresolved.add(artifact["extracted_record_id"])
    return bridge, unresolved


def _build_product_bridge(
    artifacts: list[dict[str, Any]],
    registries: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    product_copies_by_path: dict[str, list[dict[str, Any]]],
    api_registries_by_key: dict[tuple[str, str], list[dict[str, Any]]],
) -> tuple[dict[str, str], dict[tuple[str, str], str], set[str]]:
    """Return strict Product bridges and local API-key to APIC URL evidence."""

    artifacts_by_key = _unique_by_name_version(artifacts)
    registries_by_key = _unique_by_name_version(registries)
    plans_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for plan in plans:
        parent = plan.get("parent_extracted_record_id")
        if isinstance(parent, str):
            plans_by_parent[parent].append(plan)

    bridge: dict[str, str] = {}
    local_api_urls: dict[tuple[str, str], str] = {}
    unresolved: set[str] = set()
    for artifact in artifacts:
        artifact_id = artifact["extracted_record_id"]
        key = (artifact.get("name"), artifact.get("version"))
        candidates = registries_by_key.get(key, [])
        if len(artifacts_by_key.get(key, [])) != 1 or len(candidates) != 1:
            unresolved.add(artifact_id)
            continue
        registry = candidates[0]
        candidate_local_urls: dict[str, str] = {}
        valid = True
        for reference in artifact.get("api_references", []):
            mapped = reference.get("mapped_source_relative_path")
            api_key = reference.get("api_key")
            copies = product_copies_by_path.get(mapped, []) if isinstance(mapped, str) else []
            if not isinstance(api_key, str) or len(copies) != 1:
                valid = False
                break
            copy = copies[0]
            api_candidates = api_registries_by_key.get(
                (copy.get("name"), copy.get("version")), []
            )
            if len(api_candidates) != 1 or not isinstance(
                api_candidates[0].get("apic_object_url"), str
            ):
                valid = False
                break
            candidate_local_urls[api_key] = api_candidates[0]["apic_object_url"]

        if not valid or set(candidate_local_urls.values()) != set(registry.get("api_urls", [])):
            unresolved.add(artifact_id)
            continue

        artifact_plans = plans_by_parent.get(artifact_id, [])
        registry_plans = plans_by_parent.get(registry["extracted_record_id"], [])
        artifact_plan_map = {plan.get("plan_key"): plan for plan in artifact_plans}
        registry_plan_map = {plan.get("plan_key"): plan for plan in registry_plans}
        if set(artifact_plan_map) != set(registry_plan_map):
            unresolved.add(artifact_id)
            continue
        for plan_key in sorted(artifact_plan_map):
            artifact_urls = {
                candidate_local_urls[api_key]
                for api_key in artifact_plan_map[plan_key].get("api_keys", [])
                if api_key in candidate_local_urls
            }
            registry_urls = {
                reference.get("apic_object_url")
                for reference in registry_plan_map[plan_key].get("api_references", [])
            }
            if (
                len(artifact_urls) != len(artifact_plan_map[plan_key].get("api_keys", []))
                or artifact_urls != registry_urls
            ):
                valid = False
                break
        if not valid:
            unresolved.add(artifact_id)
            continue
        bridge[artifact_id] = registry["extracted_record_id"]
        for api_key, url in candidate_local_urls.items():
            local_api_urls[(artifact_id, api_key)] = url
    return bridge, local_api_urls, unresolved


def _direct_identity_groups(
    records: list[dict[str, Any]], object_type: str
) -> list[list[dict[str, Any]]]:
    by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    without_url: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if isinstance(record.get("apic_object_url"), str):
            by_url[record["apic_object_url"]].append(record)
        else:
            without_url[
                (record.get("apic_object_id"), record.get("org_url"), record.get("catalog_url"))
            ].append(record)
    groups = [sorted(values, key=_record_sort_key) for _, values in sorted(by_url.items())]
    for _, values in sorted(without_url.items(), key=lambda item: repr(item[0])):
        probe = values[0]
        candidates = [
            group
            for group in groups
            if group[0].get("apic_object_id") == probe.get("apic_object_id")
            and probe.get("apic_object_id") is not None
            and _scope_compatible(group[0], probe)
        ]
        if len(candidates) == 1:
            candidates[0].extend(values)
            candidates[0].sort(key=_record_sort_key)
        else:
            groups.append(values)
    return sorted(groups, key=lambda group: _record_sort_key(group[0]))


def _reference(
    field: str,
    raw_value: Any,
    targets: list[str],
    *,
    mapped_source_relative_path: str | None = None,
    target_occurrence_ids: Iterable[str] = (),
) -> dict[str, Any]:
    if not isinstance(raw_value, str) or not raw_value:
        outcome = "UNRESOLVED"
    elif len(targets) == 1:
        outcome = "RESOLVED"
    elif len(targets) > 1:
        outcome = "AMBIGUOUS"
    else:
        outcome = "BROKEN_REFERENCE"
    result = {
        "field": field,
        "raw_value": raw_value,
        "outcome": outcome,
        "target_canonical_identity_record_ids": sorted(targets),
    }
    if mapped_source_relative_path is not None:
        result["mapped_source_relative_path"] = mapped_source_relative_path
    occurrence_ids = sorted(set(target_occurrence_ids))
    if occurrence_ids:
        result["target_extracted_record_ids"] = occurrence_ids
    return result


def resolve_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve Phase 1 occurrence records into one deterministic index value."""

    lookups = ResolverLookups(records)
    typed = [
        record
        for record in records
        if record.get("canonical_object_type_candidate") in APPROVED_OBJECT_TYPES
    ]
    api_artifacts = [record for record in typed if _is_api_catalog_artifact(record)]
    api_registries = [record for record in typed if _is_api_registry(record)]
    product_copies = [record for record in typed if _is_product_copy(record)]
    product_artifacts = [record for record in typed if _is_product_artifact(record)]
    product_registries = [record for record in typed if _is_product_registry(record)]
    plans = [record for record in typed if record["canonical_object_type_candidate"] == "plan"]

    api_registry_groups = _direct_identity_groups(api_registries, "api_artifact")
    api_registry_representatives = [group[0] for group in api_registry_groups]
    api_registry_representative_by_occurrence = {
        value["extracted_record_id"]: group[0]["extracted_record_id"]
        for group in api_registry_groups
        for value in group
    }
    product_registry_groups = _direct_identity_groups(product_registries, "product")
    product_registry_representatives = [group[0] for group in product_registry_groups]

    api_bridge, unresolved_api_artifacts = _build_api_bridge(
        api_artifacts, api_registry_representatives
    )
    api_registry_by_key = _unique_by_name_version(api_registry_representatives)
    copies_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for copy in product_copies:
        copies_by_path[copy["source_relative_path"]].append(copy)
    product_bridge, product_local_urls, unresolved_product_artifacts = _build_product_bridge(
        product_artifacts,
        product_registry_representatives,
        plans,
        copies_by_path,
        api_registry_by_key,
    )

    by_id = lookups.by_record_id
    identities: list[dict[str, Any]] = []
    occurrence_to_identity: dict[str, str] = {}

    # Products are keyed by their registry URL where available.  Authoritative
    # artifacts remain the configuration evidence in merged records.
    for registry_group in product_registry_groups:
        registry = registry_group[0]
        artifact_ids = sorted(
            artifact_id
            for artifact_id, registry_id in product_bridge.items()
            if registry_id == registry["extracted_record_id"]
        )
        registry_ids = [value["extracted_record_id"] for value in registry_group]
        occurrences = registry_group + [by_id[value] for value in artifact_ids]
        identity = _identity_record(
            "product",
            registry.get("apic_object_url") or registry["extracted_record_id"],
            occurrences,
            authoritative_ids=artifact_ids,
            registry_ids=registry_ids,
        )
        identities.append(identity)
        for occurrence in occurrences:
            occurrence_to_identity[occurrence["extracted_record_id"]] = identity[
                "canonical_identity_record_id"
            ]
    for artifact in product_artifacts:
        if artifact["extracted_record_id"] in product_bridge:
            continue
        identity = _identity_record(
            "product",
            artifact["extracted_record_id"],
            [artifact],
            authoritative_ids=[artifact["extracted_record_id"]],
            resolution_state="UNRESOLVED",
        )
        identities.append(identity)
        occurrence_to_identity[artifact["extracted_record_id"]] = identity[
            "canonical_identity_record_id"
        ]

    # Associate Product-location copies only through a strictly bridged Product
    # API key and the corresponding registry API URL.
    copy_to_api_registry: dict[str, str] = {}
    for product in product_artifacts:
        product_id = product["extracted_record_id"]
        if product_id not in product_bridge:
            continue
        for reference in product.get("api_references", []):
            api_key = reference.get("api_key")
            mapped = reference.get("mapped_source_relative_path")
            url = product_local_urls.get((product_id, api_key))
            copies = copies_by_path.get(mapped, []) if isinstance(mapped, str) else []
            registries = lookups.exact_self_url(url, "api_artifact") if isinstance(url, str) else []
            registry_representatives = {
                api_registry_representative_by_occurrence[candidate["extracted_record_id"]]
                for candidate in registries
                if _is_api_registry(candidate)
            }
            if len(copies) == 1 and len(registry_representatives) == 1:
                copy_to_api_registry[copies[0]["extracted_record_id"]] = next(
                    iter(registry_representatives)
                )

    for registry_group in api_registry_groups:
        registry = registry_group[0]
        artifact_ids = sorted(
            artifact_id
            for artifact_id, registry_id in api_bridge.items()
            if registry_id == registry["extracted_record_id"]
        )
        copy_ids = sorted(
            copy_id
            for copy_id, registry_id in copy_to_api_registry.items()
            if registry_id == registry["extracted_record_id"]
        )
        registry_ids = [value["extracted_record_id"] for value in registry_group]
        occurrences = registry_group + [by_id[value] for value in artifact_ids + copy_ids]
        identity = _identity_record(
            "api_artifact",
            registry.get("apic_object_url") or registry["extracted_record_id"],
            occurrences,
            authoritative_ids=artifact_ids,
            registry_ids=registry_ids,
            product_copy_ids=copy_ids,
        )
        identities.append(identity)
        for occurrence in occurrences:
            occurrence_to_identity[occurrence["extracted_record_id"]] = identity[
                "canonical_identity_record_id"
            ]
    for artifact in api_artifacts:
        if artifact["extracted_record_id"] in api_bridge:
            continue
        identity = _identity_record(
            "api_artifact",
            artifact["extracted_record_id"],
            [artifact],
            authoritative_ids=[artifact["extracted_record_id"]],
            resolution_state="UNRESOLVED",
        )
        identities.append(identity)
        occurrence_to_identity[artifact["extracted_record_id"]] = identity[
            "canonical_identity_record_id"
        ]

    # Plans are identities only inside their resolved Product context.
    plan_identity_by_product_and_key: dict[tuple[str, str], list[str]] = defaultdict(list)
    for product_identity in sorted(
        (value for value in identities if value["canonical_object_type"] == "product"),
        key=lambda value: value["canonical_identity_record_id"],
    ):
        relevant_plans = [
            plan
            for plan in plans
            if plan.get("parent_extracted_record_id")
            in product_identity["contributing_extracted_record_ids"]
        ]
        plans_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for plan in relevant_plans:
            if isinstance(plan.get("plan_key"), str):
                plans_by_key[plan["plan_key"]].append(plan)
        for plan_key, values in sorted(plans_by_key.items()):
            authoritative = [
                value["extracted_record_id"]
                for value in values
                if by_id[value["parent_extracted_record_id"]].get("source_schema_family")
                == "APIC_PRODUCT"
            ]
            registry = [
                value["extracted_record_id"]
                for value in values
                if by_id[value["parent_extracted_record_id"]].get("source_schema_family")
                == "APIC_COLLECTION"
            ]
            identity = _identity_record(
                "plan",
                [product_identity["canonical_identity_record_id"], plan_key],
                values,
                authoritative_ids=authoritative,
                registry_ids=registry,
            )
            identity["parent_product_identity_record_id"] = product_identity[
                "canonical_identity_record_id"
            ]
            identity["plan_key"] = plan_key
            identities.append(identity)
            plan_identity_by_product_and_key[
                (product_identity["canonical_identity_record_id"], plan_key)
            ].append(identity["canonical_identity_record_id"])
            for value in values:
                occurrence_to_identity[value["extracted_record_id"]] = identity[
                    "canonical_identity_record_id"
                ]

    # Resolve all remaining directly identified object types by exact URL first,
    # with ID and compatible scope supporting records that omit a self URL.
    direct_types = (
        "consumer_org",
        "application",
        "credential",
        "subscription",
        "catalog_config",
        "catalog_property",
    )
    for object_type in direct_types:
        candidates = [
            record for record in typed if record["canonical_object_type_candidate"] == object_type
        ]
        for group in _direct_identity_groups(candidates, object_type):
            first = group[0]
            identity_key = first.get("apic_object_url") or [
                first.get("apic_object_id"),
                first.get("org_url"),
                first.get("catalog_url"),
                first["extracted_record_id"] if first.get("apic_object_id") is None else None,
            ]
            registry_ids = [
                value["extracted_record_id"]
                for value in group
                if value.get("source_schema_family") == "APIC_COLLECTION"
            ]
            authoritative_ids = [
                value["extracted_record_id"]
                for value in group
                if value.get("source_schema_family") != "APIC_COLLECTION"
            ]
            identity = _identity_record(
                object_type,
                identity_key,
                group,
                authoritative_ids=authoritative_ids,
                registry_ids=registry_ids,
            )
            identities.append(identity)
            for value in group:
                occurrence_to_identity[value["extracted_record_id"]] = identity[
                    "canonical_identity_record_id"
                ]

    identities.sort(key=lambda value: value["canonical_identity_record_id"])
    identities_by_id = {value["canonical_identity_record_id"]: value for value in identities}
    canonical_by_url: dict[tuple[str, str], list[str]] = defaultdict(list)
    for identity in identities:
        if isinstance(identity.get("apic_object_url"), str):
            canonical_by_url[
                (identity["canonical_object_type"], identity["apic_object_url"])
            ].append(identity["canonical_identity_record_id"])

    reference_counts: Counter[tuple[str, str]] = Counter()
    for record in typed:
        identity_id = occurrence_to_identity.get(record["extracted_record_id"])
        if identity_id is None:
            continue
        identity = identities_by_id[identity_id]
        object_type = record["canonical_object_type_candidate"]
        specs: list[tuple[str, str, str]] = []
        if object_type == "application":
            specs.append(("consumer_org_url", "consumer_org", "consumer_org_url"))
        elif object_type == "credential":
            specs.append(("app_url", "application", "app_url"))
        elif object_type == "subscription":
            specs.extend(
                [
                    ("app_url", "application", "app_url"),
                    ("product_url", "product", "product_url"),
                ]
            )
        for source_field, target_type, output_field in specs:
            raw = record.get(source_field)
            targets = canonical_by_url.get((target_type, raw), []) if isinstance(raw, str) else []
            resolved = _reference(output_field, raw, targets)
            if resolved not in identity["references"]:
                identity["references"].append(resolved)
                relation = {
                    ("application", "consumer_org_url"): "application_consumer_org_url",
                    ("credential", "app_url"): "credential_app_url",
                    ("subscription", "app_url"): "subscription_app_url",
                    ("subscription", "product_url"): "subscription_product_url",
                }[(object_type, output_field)]
                reference_counts[(relation, resolved["outcome"])] += 1
        if object_type == "subscription":
            product_targets = canonical_by_url.get(("product", record.get("product_url")), [])
            plan_targets: list[str] = []
            if len(product_targets) == 1 and isinstance(record.get("plan"), str):
                plan_targets = plan_identity_by_product_and_key.get(
                    (product_targets[0], record["plan"]), []
                )
            plan_reference = _reference("plan", record.get("plan"), plan_targets)
            if plan_reference not in identity["references"]:
                identity["references"].append(plan_reference)
                reference_counts[("subscription_plan", plan_reference["outcome"])] += 1

    # Preserve raw and mapped Product references and resolve the mapped path only.
    product_ref_counts: Counter[str] = Counter()
    plan_api_ref_counts: Counter[str] = Counter()
    for product in product_artifacts:
        identity_id = occurrence_to_identity[product["extracted_record_id"]]
        identity = identities_by_id[identity_id]
        for item in product.get("api_references", []):
            mapped = item.get("mapped_source_relative_path")
            path_matches = [
                value for value in lookups.by_source_path.get(mapped, []) if _is_product_copy(value)
            ] if isinstance(mapped, str) else []
            targets = [
                occurrence_to_identity[value["extracted_record_id"]]
                for value in path_matches
                if value["extracted_record_id"] in occurrence_to_identity
            ]
            # Product $ref resolution itself targets the exact source occurrence;
            # canonical API association is additional evidence when available.
            outcome_targets = [value["extracted_record_id"] for value in path_matches]
            reference = _reference(
                "product_api_ref",
                item.get("raw_ref"),
                outcome_targets,
                mapped_source_relative_path=mapped,
                target_occurrence_ids=outcome_targets,
            )
            if not isinstance(mapped, str):
                reference["outcome"] = "UNRESOLVED"
            reference["api_key"] = item.get("api_key")
            reference["target_canonical_identity_record_ids"] = sorted(set(targets))
            identity["references"].append(reference)
            product_ref_counts[reference["outcome"]] += 1

        product_api_keys = {
            item.get("api_key") for item in product.get("api_references", [])
        }
        for plan in plans:
            if plan.get("parent_extracted_record_id") != product["extracted_record_id"]:
                continue
            plan_identity_id = occurrence_to_identity[plan["extracted_record_id"]]
            plan_identity = identities_by_id[plan_identity_id]
            for api_key in plan.get("api_keys", []):
                target_url = product_local_urls.get((product["extracted_record_id"], api_key))
                api_targets = canonical_by_url.get(("api_artifact", target_url), [])
                if api_key not in product_api_keys:
                    api_targets = []
                reference = _reference("plan_api_key", api_key, api_targets)
                plan_identity["references"].append(reference)
                plan_api_ref_counts[reference["outcome"]] += 1

    for identity in identities:
        identity["references"].sort(
            key=lambda value: (
                value.get("field") or "",
                value.get("raw_value") or "",
                value.get("mapped_source_relative_path") or "",
            )
        )

    unresolved_occurrences = []
    for copy in product_copies:
        if copy["extracted_record_id"] not in occurrence_to_identity:
            unresolved_occurrences.append(
                {
                    "canonical_object_type": "api_artifact",
                    "outcome": "UNRESOLVED",
                    **_evidence(copy),
                }
            )
    unresolved_occurrences.sort(
        key=lambda value: (
            value["source_relative_path"],
            value["source_object_pointer"],
            value["extracted_record_id"],
        )
    )

    canonical_counts = Counter(value["canonical_object_type"] for value in identities)
    registry_only_products = sum(
        not value["authoritative_artifact_occurrence_ids"]
        for value in identities
        if value["canonical_object_type"] == "product" and value["registry_occurrence_ids"]
    )
    registry_only_apis = sum(
        not value["authoritative_artifact_occurrence_ids"]
        for value in identities
        if value["canonical_object_type"] == "api_artifact" and value["registry_occurrence_ids"]
    )
    artifact_only_products = sum(
        not value["registry_occurrence_ids"]
        for value in identities
        if value["canonical_object_type"] == "product"
        and value["authoritative_artifact_occurrence_ids"]
    )
    artifact_only_apis = sum(
        not value["registry_occurrence_ids"]
        for value in identities
        if value["canonical_object_type"] == "api_artifact"
        and value["authoritative_artifact_occurrence_ids"]
    )
    summary = {
        "input_occurrence_count": len(records),
        "typed_input_occurrence_count": len(typed),
        "occurrences_attached_to_canonical_identities": len(occurrence_to_identity),
        "canonical_identity_counts": dict(sorted(canonical_counts.items())),
        "exact_self_url_lookup_key_count": len(lookups.by_self_url),
        "id_scope_lookup_key_count": len(lookups.by_id_scope),
        "product_bridge": {
            "authoritative_count": len(product_artifacts),
            "resolved": len(product_bridge),
            "unresolved": len(unresolved_product_artifacts),
            "registry_only": registry_only_products,
            "artifact_only": artifact_only_products,
        },
        "api_bridge": {
            "authoritative_count": len(api_artifacts),
            "resolved": len(api_bridge),
            "unresolved": len(unresolved_api_artifacts),
            "registry_only": registry_only_apis,
            "artifact_only": artifact_only_apis,
        },
        "product_api_refs": dict(sorted(product_ref_counts.items())),
        "plan_api_refs": dict(sorted(plan_api_ref_counts.items())),
        "reference_resolutions": {
            field: {
                outcome: count
                for (candidate_field, outcome), count in sorted(reference_counts.items())
                if candidate_field == field
            }
            for field in sorted({field for field, _ in reference_counts})
        },
        "unresolved_product_location_api_occurrences": len(unresolved_occurrences),
    }
    return {
        "canonical_identity_records": identities,
        "unresolved_occurrences": unresolved_occurrences,
        "summary": summary,
    }


def resolve_identities(
    extracted_index: Path,
    output_root: Path,
) -> dict[str, Any]:
    records = [
        json.loads(line)
        for line in extracted_index.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = resolve_records(records)
    output_path = output_root / OUTPUT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return result["summary"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("indexes/extracted_records.jsonl"),
        help="Phase 1 extracted occurrence index",
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path("."), help="project/output root"
    )
    args = parser.parse_args(argv)
    summary = resolve_identities(args.input, args.output_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0
