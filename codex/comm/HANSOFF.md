# Codex Handoff

## Task executed

Phase 3 — Task 010: CodeGraph Explorer / Visualization.

## Prompt file used

`codex/comm/prompts/phase-3-010-codegraph-explorer-visualization.md`

## Summary of what was done

- Built a lightweight, read-only local explorer over the accepted Task 009 CodeGraph indexes.
- Added canonical-ID, exact-name, and case-insensitive name/title substring search with approved object-type filtering.
- Added incoming, outgoing, and both-direction targeted neighborhoods at depths 1–3 with approved relationship filters.
- Added a self-contained directed SVG view with node types/labels, relationship labels, selected node/edge state, active controls, one-node expansion, reset, and clear.
- Added allowlisted node and edge detail projections with accepted Task 008 provenance drill-down and registry-only/dual evidence labels.
- Enforced deterministic limits of 80 nodes and 120 edges with a visible warning and no silent truncation.
- Preserved isolated nodes and all accepted graph semantics; no node, edge, direction, identity, relationship, or provenance was inferred or mutated.

## Explorer implementation structure

- `codegraph_explorer/explorer.py`: read-only query layer, safe projections, deterministic visualization cap, JSON endpoints, and standard-library local HTTP server.
- `codegraph_explorer/static/index.html`: self-contained HTML/CSS/JavaScript SVG review interface; no CDN or hosted dependency.
- `codegraph_explorer/__init__.py`: public explorer API.
- `codegraph_explorer/__main__.py`: local module entry point.
- `tests/test_codegraph_explorer.py`: focused synthetic, HTTP smoke, and full-corpus acceptance tests.
- `tests/evidence/task-010/generate_explorer_evidence.py`: deterministic review-evidence generator.

## Exact run command

```text
.venv/bin/python -m codegraph_explorer
```

Open `http://127.0.0.1:8765`. The explorer binds only to loopback by default.

## Dependencies introduced

None. The server uses the Python standard library, and the visual explorer is self-contained.

## Graph indexes consumed

- `indexes/codegraph_nodes.jsonl`: 4,718 nodes.
- `indexes/codegraph_edges.jsonl`: 9,589 edges.
- `indexes/codegraph_adjacency.jsonl`: accepted incoming/outgoing adjacency.
- `indexes/relationship_index.jsonl`: provenance drill-down only.

Normal explorer operation does not scan raw `staging/`.

## Search, traversal, and filter capabilities

- Search: canonical ID, exact name, case-insensitive name/title substring, and approved object type.
- Traversal: incoming, outgoing, or both; depth 1, 2, or 3 only.
- Relationship filters: the ten accepted Task 008 relationship types only.
- View controls: select start node, select node/edge, expand one selected node, reset to start node, and clear.
- Ordering: canonical IDs and relationship IDs are returned deterministically.
- Every Application-centered view is labeled **Structural reachability, not runtime consumption.**

## Visualization size limit

The default cap is 80 nodes and 120 edges. When the complete candidate neighborhood exceeds either cap, the explorer returns a deterministic subset and displays an explicit warning telling the reviewer to reduce depth or filter scope. Candidate and returned counts are exposed separately.

## Node and edge details

Node details expose only canonical object ID, approved object type, label/name/title/version, APIC object ID/self URL where accepted, incoming/outgoing counts, and the Phase 2 canonical record reference.

Edge details expose relationship ID/type, canonical source/target IDs and types, evidence state, evidence-source category, Task 008 relationship pointer, contributing occurrence IDs, and accepted source paths/pointers. Raw references and arbitrary source payload fields are not exposed.

## Provenance drill-down

The explorer loads the accepted Task 008 relationship record by exact relationship ID and projects only allowlisted provenance. It distinguishes `registry_only`, `dual`, and `authoritative_only` only when the accepted evidence-source categories support that label. No provenance category is invented.

## Review examples

- API-centered: API `apic-identity:sha256:0009ee4eeece2430096ec9be843777a8e4258c260de73c9f9fb702bc865a55ce` shows three nodes and two incoming Product/Plan edges with Task 008 provenance.
- Product-centered: Product `apic-identity:sha256:00a9ee8fd6539fb17d371dc3f561e3cf84b2cf2532437282f2232686f858c2a0` shows contained API, contained Plan, and Plan-entitled API across three accepted edges.
- Application-centered: Application `apic-identity:sha256:0206b436e7ceda8c411d6c213c735ffd84269dcedb7185054952dae274aaff6e` reaches its Consumer Org, Subscriptions, Products, contextual Plans, and APIs. Its broad depth-3 review produces a deterministic 80-node/79-edge subset and a visible size warning. This is structural reachability, not runtime consumption.
- Registry-only: Relationship `apic-relationship:sha256:000cc1a3eccda006c3df18fc1303405334f58cc15f1ad243d8b1c7bd68332a32` is shown as `registry_only` from accepted provenance.
- Isolated node: Consumer Org `apic-identity:sha256:144297969f8be24c16542f4ccfc516d77025ecb282f147252a13217beec1b2f7` displays alone with zero edges; no relationship is inferred.

## Files created

- `codegraph_explorer/__init__.py`
- `codegraph_explorer/__main__.py`
- `codegraph_explorer/explorer.py`
- `codegraph_explorer/static/index.html`
- `tests/test_codegraph_explorer.py`
- `tests/evidence/task-010/generate_explorer_evidence.py`
- `tests/evidence/task-010/explorer_acceptance.json`
- `tests/evidence/task-010/visual_review_samples.jsonl`
- `tests/evidence/task-010/commands_and_results.txt`

## Files modified

- `codex/comm/HANSOFF.md`

## Tests executed

- Exact local startup command and loopback `/health` request.
- Two deterministic evidence-generation runs with SHA-256 comparison.
- `.venv/bin/pytest tests/test_codegraph_explorer.py -q`
- `.venv/bin/pytest -q`
- Python compilation checks.
- `git diff --check`.
- Frozen-component and graph-index checks.
- Full `staging/` hash snapshot comparison.
- Full-corpus credential source-value comparison against all explorer projections.

## Test results

- Explorer startup and UI load: **passed**.
- Focused Task 010 tests: **5 passed**.
- Acceptance evidence: **PASS**.
- Repeated evidence outputs: **byte-identical**.
- Graph counts observed: **4,718 nodes / 9,589 edges**.
- Credential redaction: **passed**; 540 source credential values checked, zero exposed.
- Task 007 exclusion: **passed**; all 113 unresolved occurrence IDs remain absent from graph IDs.
- Frozen Task 009 graph hashes and `staging/`: **unchanged**.
- Repository-wide suite: **27 passed, 5 setup errors**. The five errors remain the known frozen Phase 0 fixture-packaging issue because `tests/fixtures/repository_profile/staging` is absent. No Task 010 test failed.

## Generated artifacts

- `tests/evidence/task-010/explorer_acceptance.json` — SHA-256 `cfcaead1fe5e2d20c15ca67f4e48ca309970337525179d88301ff19b53179a96`.
- `tests/evidence/task-010/visual_review_samples.jsonl` — five deterministic scenarios; SHA-256 `4242e13d902120fe401401845d6948b23970f035424a1ec87e84bae26a1f2917`.
- `tests/evidence/task-010/commands_and_results.txt` — startup, tests, immutability, and redaction results.
- No artifact under `staging/`, `indexes/`, or `outputs/` was created or modified.

## Important findings

- The accepted graph can be reviewed locally without a graph database, framework, external service, or new dependency.
- Accepted registry-only and dual provenance can be distinguished without exposing raw source payloads.
- Broad Application-centered depth-3 views can exceed the visual cap; the explorer makes this explicit and supports narrowing by depth and relationship type.
- All 21 accepted isolated nodes remain reviewable without inferred repair edges.
- No reproducible defect was found in a frozen component.

## Unresolved issues

- The 113 Task 007 Product-location occurrences remain unresolved and correctly excluded.
- The five repository-wide Phase 0 setup errors remain unresolved because the frozen fixture directory is absent.
- `api_uses_catalog_property` and `api_invokes_target` have no accepted edges to display in the current graph.

## Assumptions

- Task 009 CodeGraph indexes and Task 008 relationship provenance are the authoritative read-only inputs.
- Evidence labels are derived only from accepted `evidence_source_categories`.
- A deterministic capped neighborhood is preferable to full-graph rendering, provided truncation is visible and reviewer controls can narrow the view.
- APIC object IDs/self URLs already present in accepted graph nodes are approved structural metadata; credential payload values are not.

## Deviations from the prompt

None.

## Recommended next step

Accept Phase 3 Task 010 as PASS and use the local explorer for Integration Architect and Enterprise Architect review. Do not begin another task until `CURRENT_TASKS.md` is updated externally.

## Final status

PASS
