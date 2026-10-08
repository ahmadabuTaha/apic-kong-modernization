import hashlib
import json
from pathlib import Path

import pytest

from dependency_discovery import build_dependency_indexes, extract_dependency_candidates


ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "indexes/apic_identity_resolution.json"
TASK011 = ROOT / "indexes/backend_target_resolution.jsonl"
TASK_012_EVIDENCE = ROOT / "tests/evidence/task-012"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_observed_security_shapes_named_provider_endpoints_external_and_unclassified() -> None:
    document = {
        "securityDefinitions": {
            "oauth": {
                "type": "oauth2",
                "flow": "application",
                "x-ibm-oauth-provider": "provider-name",
                "tokenUrl": "$(oauth-host)/token",
                "authorizationUrl": "https://user:password@identity.invalid/auth?token=value",
            },
            "named-only": {"type": "oauth2", "flow": "application", "x-ibm-oauth-provider": "local-provider"},
            "client-id": {"type": "apiKey", "in": "header", "name": "X-Client-ID"},
        },
        "components": {
            "securitySchemes": {
                "oidc": {"type": "openIdConnect", "openIdConnectUrl": "$(oidc-discovery)"}
            }
        },
        "servers": [{"url": "https://public-api.invalid"}],
        "x-ibm-configuration": {
            "assembly": {
                "execute": [
                    {"invoke": {"target-url": "https://must-be-reused-not-parsed.invalid"}},
                    {"websocket-upgrade": {"target-url": "https://socket.invalid/connect"}},
                    {"jwt-validate": {"jws-jwk": "must-not-be-exposed-key-material"}},
                ]
            }
        },
    }
    parsed = extract_dependency_candidates(document)
    roles = [item["dependency_role"] for item in parsed["candidates"]]
    assert roles.count("OAUTH2_PROVIDER_REFERENCE") == 2
    assert "OIDC_PROVIDER_REFERENCE" in roles
    assert "TOKEN_ENDPOINT" in roles
    assert "AUTHORIZATION_ENDPOINT" in roles
    assert "OPENID_CONNECT_DISCOVERY_ENDPOINT" in roles
    assert "POLICY_HTTP_ENDPOINT" in roles
    assert "JWK_CONFIGURATION" in roles
    assert not any(item["mechanism_name"] == "invoke" for item in parsed["candidates"])
    assert not any(item["safe_value"] == "https://public-api.invalid" for item in parsed["candidates"])
    serialized = json.dumps(parsed)
    assert "password" not in serialized
    assert "token=value" not in serialized
    assert "must-not-be-exposed-key-material" not in serialized


def _task011_record() -> dict:
    return {
        "target_observation_id": "task011-target",
        "canonical_api_id": "api-a",
        "api_name": "a",
        "api_version": "1.0.0",
        "source_path": "staging/apis/a.yaml",
        "source_pointer": "/x-ibm-configuration/assembly/execute/0/invoke/target-url",
        "operation_scope": [{"verb": "post", "path": "/items", "operation_id": "create"}],
        "invocation_mechanism": "invoke",
        "original_safe_target_expression": "$(backend)/items",
        "resolved_safe_target_expression": "backend.invalid/items",
        "symbolic_property_tokens": ["backend"],
        "runtime_parameter_tokens": [],
        "property_lookup_results": [
            {
                "symbolic_property_name": "backend",
                "lookup_status": "RESOLVED",
                "property_record_ids": ["property-backend"],
                "reason": "exact_catalog_property_match",
            }
        ],
        "target_classification": "CATALOG_PROPERTY_RESOLVED",
        "resolution_status": "RESOLVED",
        "resolution_reason": "all_catalog_properties_resolved_exactly",
        "source_sha256": "accepted-task011-source-sha",
    }


def _synthetic_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    api_a = """securityDefinitions:
  oauth:
    type: oauth2
    flow: application
    x-ibm-oauth-provider: named-provider
    tokenUrl: $(oauth-host)/token
x-ibm-configuration:
  assembly:
    execute:
    - invoke:
        target-url: https://different-from-task011.invalid
    - websocket-upgrade:
        target-url: https://socket.invalid/connect
"""
    api_b = """securityDefinitions:
  local:
    type: oauth2
    flow: application
    x-ibm-oauth-provider: named-provider-without-endpoint
x-ibm-configuration:
  assembly:
    execute:
    - jwt-validate:
        jws-jwk: private-key-material-must-not-persist
"""
    _write(root / "staging/apis/a.yaml", api_a)
    _write(root / "staging/apis/b.yaml", api_b)
    identities = [
        {
            "canonical_identity_record_id": f"api-{name}",
            "canonical_object_type": "api_artifact",
            "name": name,
            "version": "1.0.0",
            "source_evidence": [{"source_relative_path": f"staging/apis/{name}.yaml"}],
        }
        for name in ("a", "b")
    ]
    _write(root / "indexes/apic_identity_resolution.json", json.dumps({"canonical_identity_records": identities}))
    _write(root / "indexes/backend_target_resolution.jsonl", json.dumps(_task011_record()) + "\n")
    properties = [
        {
            "catalog_property_record_id": "property-backend",
            "exact_property_name": "backend",
            "safe_value": "backend.invalid",
            "lookup_cardinality": "unique_exact_value",
        },
        {
            "catalog_property_record_id": "property-oauth",
            "exact_property_name": "oauth-host",
            "safe_value": "identity.invalid",
            "lookup_cardinality": "unique_exact_value",
        },
    ]
    _write(root / "indexes/catalog_properties.jsonl", "".join(json.dumps(item) + "\n" for item in properties))
    return root


def test_task011_reuse_context_classification_provenance_dedup_and_cache(tmp_path: Path) -> None:
    root = _synthetic_root(tmp_path)
    cold = build_dependency_indexes(root)
    cold_index = (root / "indexes/api_dependency_observations.jsonl").read_bytes()
    records = cold["records"]
    backend = next(item for item in records if item["observation_class"] == "BACKEND_INVOCATION")
    assert backend["originating_accepted_index_record_id"] == "task011-target"
    assert backend["safe_raw_expression_or_value_reference"] == "$(backend)/items"
    assert backend["operation_method"] == "post"
    assert backend["operation_path"] == "/items"
    assert cold["summary"]["task011_backend_yaml_reparse_count"] == 0
    assert not any("different-from-task011" in json.dumps(item) for item in records)
    external = next(item for item in records if item["observation_class"] == "EXTERNAL_HTTP_DEPENDENCY")
    assert external["ownership_state"] == "ownership_validation_required"
    assert external["mechanism_or_policy_name"] == "websocket-upgrade"
    external_pattern = next(
        item
        for item in cold["inventory"]
        if item["mechanism_name"] == "websocket-upgrade"
    )
    assert external_pattern["observation_count"] == 1
    assert external_pattern["resolution_state_counts"] == {"RESOLVED": 1}
    named = [item for item in records if item.get("dependency_role") == "OAUTH2_PROVIDER_REFERENCE"]
    assert any(item["safe_raw_expression_or_value_reference"] == "named-provider-without-endpoint" for item in named)
    assert len({item["dependency_observation_id"] for item in records}) == len(records)
    assert cold["cache"]["files_parsed"] == 2
    assert cold["cache"]["cache_misses"] == 2

    warm = build_dependency_indexes(root)
    assert warm["cache"]["files_parsed"] == 0
    assert warm["cache"]["cache_hits"] == 2
    assert cold_index == (root / "indexes/api_dependency_observations.jsonl").read_bytes()

    with (root / "staging/apis/b.yaml").open("a", encoding="utf-8") as stream:
        stream.write("# source hash changed\n")
    changed = build_dependency_indexes(root)
    assert changed["cache"]["files_parsed"] == 1
    assert changed["cache"]["cache_hits"] == 1
    assert changed["cache"]["cache_misses"] == 1
    cache_bytes = (root / "indexes/cache/phase4_dependency_discovery_cache.sqlite3").read_bytes()
    assert b"private-key-material-must-not-persist" not in cache_bytes


@pytest.mark.skipif(
    not PHASE2.is_file() or not TASK011.is_file(),
    reason="accepted local Phase 4 indexes are required",
)
def test_full_corpus_coverage_redaction_and_frozen_integrity(tmp_path: Path) -> None:
    frozen = [
        ROOT / "indexes/backend_target_resolution.jsonl",
        ROOT / "indexes/catalog_properties.jsonl",
        ROOT / "indexes/relationship_index.jsonl",
        ROOT / "indexes/codegraph_nodes.jsonl",
        ROOT / "indexes/codegraph_edges.jsonl",
        ROOT / "indexes/codegraph_adjacency.jsonl",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    staging_before = _tree_hashes(ROOT / "staging")
    result = build_dependency_indexes(
        ROOT,
        dependency_index_path=tmp_path / "dependencies.jsonl",
        pattern_index_path=tmp_path / "patterns.json",
        cache_path=tmp_path / "cache.sqlite3",
    )
    assert result["summary"]["total_canonical_apis"] == 2036
    assert result["summary"]["apis_accounted_for"] == 2036
    assert result["summary"]["task011_backend_observations_loaded"] == 2334
    assert result["summary"]["task011_backend_yaml_reparse_count"] == 0
    assert result["summary"]["observation_counts_by_class"] == {
        "BACKEND_INVOCATION": 2334,
        "CONFIGURATION_REFERENCE": 4147,
        "EXTERNAL_HTTP_DEPENDENCY": 1,
        "SECURITY_PROVIDER": 2329,
        "UNCLASSIFIED_DEPENDENCY_PATTERN": 3,
    }
    committed = json.loads((TASK_012_EVIDENCE / "dependency_summary.json").read_text())
    assert committed["total_canonical_apis"] == 2036

    outputs = (tmp_path / "dependencies.jsonl").read_bytes() + (tmp_path / "patterns.json").read_bytes() + (tmp_path / "cache.sqlite3").read_bytes()
    sensitive_values = []
    for path in (ROOT / "staging/credentials").glob("*.json"):
        for item in json.loads(path.read_text()).get("results", []):
            for field in ("client_id", "client_secret", "client_secret_hashed"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    sensitive_values.append(value.encode())
    assert sensitive_values
    assert all(value not in outputs for value in sensitive_values)
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    assert staging_before == _tree_hashes(ROOT / "staging")
