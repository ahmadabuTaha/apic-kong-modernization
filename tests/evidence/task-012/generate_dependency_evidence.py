"""Generate architecture-review evidence for Phase 4 Task 012."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dependency_discovery import build_dependency_indexes  # noqa: E402


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample(record: dict, scenario: str, interpretation: str) -> dict:
    return {
        "scenario": scenario,
        "dependency_observation_id": record["dependency_observation_id"],
        "canonical_api_id": record["canonical_api_id"],
        "api_name": record["api_name"],
        "api_version": record["api_version"],
        "scope_classification": record["scope_classification"],
        "operation_method": record["operation_method"],
        "operation_path": record["operation_path"],
        "observation_class": record["observation_class"],
        "mechanism_or_policy_name": record["mechanism_or_policy_name"],
        "dependency_role": record["dependency_role"],
        "scheme_or_provider_name": record.get("scheme_or_provider_name"),
        "referenced_catalog_properties": record["referenced_catalog_properties"],
        "referenced_context_tokens": record["referenced_context_tokens"],
        "resolution_status": record["resolution_status"],
        "resolution_reason": record["resolution_reason"],
        "ownership_state": record.get("ownership_state"),
        "normalized_endpoint_key": record.get("normalized_endpoint_key"),
        "source_path": record["source_path"],
        "source_pointer": record["source_pointer"],
        "originating_accepted_index_record_id": record["originating_accepted_index_record_id"],
        "parser_origin": record["parser_origin"],
        "expected_review_interpretation": interpretation,
        "raw_endpoint_or_infrastructure_value_omitted": True,
    }


def _proposal(summary: dict, correlation: dict) -> str:
    counts = summary["observation_counts_by_class"]
    return f"""# Task 012 Dependency Model Proposal

## Decision status

This document is an evidence-derived proposal for architecture review. It does not add canonical object types, relationship types, nodes, or edges.

Observed evidence ≠ proposed dependency model ≠ approved canonical model.

## Observed dependency concepts

- `{counts['BACKEND_INVOCATION']:,}` backend invocation observations reused unchanged from Task 011.
- `{counts['SECURITY_PROVIDER']:,}` OAuth2/OIDC provider or explicit security-endpoint observations from security-definition context.
- `{counts['CONFIGURATION_REFERENCE']:,}` exact Catalog Property or runtime-context references in dependency-bearing expressions.
- `{counts['EXTERNAL_HTTP_DEPENDENCY']:,}` explicit non-`invoke` HTTP policy dependency with ownership validation still required.
- `{counts['UNCLASSIFIED_DEPENDENCY_PATTERN']:,}` JWT/JWK configurations whose observed value shape does not safely prove an external provider or endpoint.
- `{summary['operation_scoped_dependency_observations']:,}` observations retain explicit operation scope; the remainder are API/shared.

No issuer, introspection, or JWKS URL endpoint pattern was proven in the supported corpus shapes. The observed `jws-jwk` values are deliberately not exposed or promoted.

## Proposed canonical object candidates

Subject to explicit architecture approval:

1. **Dependency Endpoint** — an environment-aware, role-qualified endpoint observation; identity must not collapse same-host/different-path endpoints.
2. **Security Provider** — a provider identity distinct from its token, authorization, discovery, introspection, or JWKS endpoints.
3. **Configuration Reference** — an exact symbolic reference identity distinct from its environment-specific resolved value.
4. **Backend Target** — an invocation target candidate preserving API/operation scope and Task 011 resolution state.

These are candidates, not approved canonical types.

## Proposed relationship candidates

Subject to explicit approval:

- API or operation **invokes** Backend Target / Dependency Endpoint.
- API or operation **uses security provider**.
- Security Provider **exposes endpoint role** (token, authorization, discovery, introspection, JWKS).
- Dependency observation **uses configuration reference**.

No relationship should be emitted from hostname similarity, provider-name similarity, or runtime assumptions.

## Scope problem

API-level flattening would lose the 198 operation-scoped observations and could conflate paths or methods. A future design must decide whether operation is a first-class graph object, an edge qualifier, or a provenance/scope structure. Until that decision, operation-scoped observations must remain distinct.

## Identity strategy

- Endpoint identity should be based on normalized scheme/host/port/path plus dependency role and environment scope when proven—not hostname alone.
- Security Provider identity should use explicit APIC provider/scheme evidence and environment/catalog context; provider identity must remain distinct from endpoint identity.
- Symbolic references should retain exact case-sensitive token identity and link to resolved environment values only through provenance.
- Symbolic and resolved targets must not be merged when resolution is missing, protected, ambiguous, or runtime-parameterized.
- Same provider with multiple endpoint roles must remain one provider candidate with role-qualified endpoint candidates only after explicit approval.

## Evidence and provenance rules

A future graph node or edge should require:

1. an accepted canonical API identity;
2. an exact source pointer or accepted Task 011 observation ID;
3. a supported context-specific parser pattern;
4. a non-secret safe identity key;
5. explicit resolution/evidence state and confidence;
6. preserved API/shared or operation scope;
7. no hostname-only ownership inference.

Unresolved and unclassified observations remain evidence records, not graph objects, unless architects define an explicit unresolved-node policy.

## Correlation findings

- `{correlation['apis_with_backend_and_security_dependencies']:,}` APIs have both backend and security observations.
- `{correlation['distinct_security_provider_references']:,}` distinct explicit provider references were observed; `{correlation['security_provider_references_shared_by_multiple_apis']:,}` are shared by multiple APIs.
- `{correlation['distinct_configuration_tokens']:,}` exact configuration tokens were observed; `{correlation['configuration_tokens_shared_by_multiple_apis']:,}` are shared by multiple APIs.
- `{correlation['distinct_resolved_endpoint_keys']:,}` safe normalized endpoint keys were observed; `{correlation['resolved_endpoint_keys_shared_by_multiple_apis']:,}` are shared by multiple APIs.

Shared dependencies are structural correlation only and do not imply duplicate business capability.

## Unresolved architecture questions

1. Should operations become canonical nodes, edge qualifiers, or provenance-only scope?
2. Which proposed candidates become approved canonical types?
3. What environment/catalog fields are mandatory in provider and endpoint identity?
4. Should unresolved symbolic targets ever become graph nodes?
5. How should one provider with multiple endpoint roles be modeled?
6. Should configuration references be graph nodes or edge provenance?
7. What evidence threshold authorizes an `EXTERNAL_HTTP_DEPENDENCY` candidate when ownership is unvalidated?
8. How should protected configuration references be represented without leaking or hashing secrets?

## Enrichment authorization recommendation

The evidence is sufficient for architects to decide the taxonomy, identity, scope, and admission rules, but it is **not sufficient by itself to authorize implementation of CodeGraph dependency enrichment**. Explicit Integration Architect and Enterprise Architect approval of the questions above is required first.
"""


def generate(root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task-012-") as temporary:
        temp = Path(temporary)
        cold = build_dependency_indexes(
            root,
            dependency_index_path=temp / "dependencies.jsonl",
            pattern_index_path=temp / "patterns.json",
            cache_path=temp / "cache.sqlite3",
        )
        cold_dependency_hash = _hash(temp / "dependencies.jsonl")
        cold_pattern_hash = _hash(temp / "patterns.json")
        warm = build_dependency_indexes(
            root,
            dependency_index_path=temp / "dependencies.jsonl",
            pattern_index_path=temp / "patterns.json",
            cache_path=temp / "cache.sqlite3",
        )
        warm_dependency_hash = _hash(temp / "dependencies.jsonl")
        warm_pattern_hash = _hash(temp / "patterns.json")
    records = cold.pop("records")
    warm.pop("records")
    summary = cold["summary"]
    inventory = cold["inventory"]
    correlation = cold["correlation"]

    backend = next(item for item in records if item["observation_class"] == "BACKEND_INVOCATION")
    config = next(item for item in records if item["observation_class"] == "CONFIGURATION_REFERENCE" and item["resolution_status"] == "RESOLVED")
    provider = next(item for item in records if item["dependency_role"] == "OAUTH2_PROVIDER_REFERENCE")
    security_endpoint = next(item for item in records if item["dependency_role"] in {"TOKEN_ENDPOINT", "AUTHORIZATION_ENDPOINT", "OPENID_CONNECT_DISCOVERY_ENDPOINT"})
    external = next(item for item in records if item["observation_class"] == "EXTERNAL_HTTP_DEPENDENCY")
    operation = next(item for item in records if item["scope_classification"] == "OPERATION_SCOPED")
    unresolved = next(item for item in records if item["resolution_status"] == "UNRESOLVED" and item["observation_class"] != "UNCLASSIFIED_DEPENDENCY_PATTERN")
    unclassified = next(item for item in records if item["observation_class"] == "UNCLASSIFIED_DEPENDENCY_PATTERN")
    classes_by_api: dict[str, set[str]] = defaultdict(set)
    ids_by_api: dict[str, list[str]] = defaultdict(list)
    for item in records:
        classes_by_api[item["canonical_api_id"]].add(item["observation_class"])
        ids_by_api[item["canonical_api_id"]].append(item["dependency_observation_id"])
    multi_api = next(api_id for api_id in sorted(classes_by_api) if len(classes_by_api[api_id]) > 1)
    multi_record = next(item for item in records if item["canonical_api_id"] == multi_api)

    samples = [
        _sample(backend, "backend_invocation_reused", "Backend observation and resolution state are reused from Task 011 without raw target reparsing."),
        _sample(config, "catalog_property_configuration_dependency", "Exact configuration token is represented as an observation, not a canonical Catalog Property node."),
        _sample(provider, "oauth2_security_provider", "Security-definition context proves a named OAuth2 provider reference without conflating it with endpoint identity."),
        _sample(security_endpoint, "explicit_security_endpoint", "Security-definition endpoint field proves an endpoint role; raw infrastructure value is omitted from committed evidence."),
        _sample(external, "external_http_dependency", "Non-invoke HTTP policy context proves an external dependency observation; ownership remains unvalidated."),
        {
            **_sample(multi_record, "api_with_multiple_dependency_classes", "One API has multiple context-derived dependency classes; this is not a duplicate/capability conclusion."),
            "classes_for_api": sorted(classes_by_api[multi_api]),
            "representative_observation_ids_for_api": sorted(ids_by_api[multi_api])[:8],
        },
        _sample(operation, "operation_scoped_dependency", "Explicit operation method/path scope is preserved from Task 011 evidence."),
        _sample(unresolved, "unresolved_dependency", "Missing/protected/runtime evidence remains explicit; no concrete dependency is fabricated."),
        _sample(unclassified, "unclassified_dependency_pattern", "Observed JWT/JWK configuration is retained with a precise unsupported-shape reason and no key material."),
    ]
    samples.sort(key=lambda item: item["scenario"])

    cache_performance = {
        "cache_schema_version": cold["cache"]["cache_schema_version"],
        "parser_version": cold["cache"]["parser_version"],
        "cold": {
            "build_seconds": cold["cache"]["build_seconds"],
            "files_parsed": cold["cache"]["files_parsed"],
            "cache_hits": cold["cache"]["cache_hits"],
            "cache_misses": cold["cache"]["cache_misses"],
        },
        "warm": {
            "build_seconds": warm["cache"]["build_seconds"],
            "files_reparsed": warm["cache"]["files_parsed"],
            "cache_hits": warm["cache"]["cache_hits"],
            "cache_misses": warm["cache"]["cache_misses"],
        },
        "task011_backend_records_loaded_from_compact_index": summary["task011_backend_observations_loaded"],
        "task011_backend_yaml_reparse_count": summary["task011_backend_yaml_reparse_count"],
        "cold_dependency_index_sha256": cold_dependency_hash,
        "warm_dependency_index_sha256": warm_dependency_hash,
        "cold_pattern_index_sha256": cold_pattern_hash,
        "warm_pattern_index_sha256": warm_pattern_hash,
        "dependency_output_identical": cold_dependency_hash == warm_dependency_hash,
        "pattern_output_identical": cold_pattern_hash == warm_pattern_hash,
        "warm_reparsed_zero_unchanged_files": warm["cache"]["files_parsed"] == 0,
    }
    _write_json(output / "dependency_summary.json", summary)
    _write_json(output / "dependency_pattern_inventory.json", inventory)
    _write_json(output / "dependency_correlation.json", correlation)
    _write_json(output / "cache_performance.json", cache_performance)
    (output / "dependency_samples.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in samples),
        encoding="utf-8",
    )
    (output / "dependency_model_proposal.md").write_text(_proposal(summary, correlation), encoding="utf-8")
    return {
        "summary": summary,
        "correlation": correlation,
        "cache_performance": cache_performance,
        "sample_count": len(samples),
        "overall_pass": all(
            (
                summary["total_canonical_apis"] == 2036,
                summary["task011_backend_observations_loaded"] == 2334,
                summary["task011_backend_yaml_reparse_count"] == 0,
                warm["cache"]["files_parsed"] == 0,
                cold_dependency_hash == warm_dependency_hash,
                cold_pattern_hash == warm_pattern_hash,
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = generate(args.root.resolve(), args.output.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
