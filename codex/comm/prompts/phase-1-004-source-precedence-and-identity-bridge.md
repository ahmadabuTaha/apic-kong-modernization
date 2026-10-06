# Phase 1 — Task 004: Source Precedence and Identity Bridge Closure

## Objective

Close the remaining identity-bridge gaps from Task 003 using the architecture decision below. This is evidence/design validation only; no implementation.

## Architecture Decision — Source Precedence

- `list.json` / registry summaries are NOT the single source of truth.
- The actual artifacts/configuration present inside the relevant directories under `staging/` are the authoritative AS-IS configuration evidence.
- Registry/list records provide supporting APIC identity, URL, ID, and cross-reference evidence.
- Registry evidence may enrich an authoritative artifact when correlation is deterministic, but must not override artifact content.
- Registry-only evidence remains registry evidence; do not silently promote it to a fully reconstructed configured object.
- Artifact-only evidence remains authoritative configuration evidence; do not discard it because registry evidence is missing.

Do not invent any new taxonomy, status, reason, canonical object type, relationship type, source-copy type, or confidence scale.

## Approved Product API Reference Mapping

Architecture approves the explicit export-root mapping for Product API `$ref` values:

```text
raw absolute $ref
→ locate the exact /staging/ segment
→ preserve the suffix beginning at staging/
→ resolve that suffix relative to the repository/project root
```

Rules:
- preserve the raw `$ref`;
- preserve the mapped repository-relative path;
- do not perform any other path normalization or heuristic rewrite;
- if `/staging/` is absent, repeated, or maps to zero/multiple files, leave unresolved and report it.

## Carry Forward from Task 003

Do not reopen these validated joins unless contradictory evidence is found:
- Application → Consumer Org: 256/256 exact URL joins;
- Credential → Application: 270/270 exact URL joins;
- Subscription → Application: 1,019/1,019 exact URL joins;
- Subscription → Product: 1,019/1,019 exact URL joins;
- Subscription → Product-scoped Plan: 1,019/1,019;
- Product registry API URLs resolve to API registry URLs;
- Product YAML Plan API keys resolve through the same Product-local API map;
- Product → API membership is independent of Subscription and Plan entitlement.

## A. Product Identity Bridge

Treat Product YAML under the Product directory as the authoritative Product configuration artifact. Treat Product registry/list records as APIC management identity/reference evidence.

Validate whether each authoritative Product YAML can be deterministically enriched with one Product registry identity using the combined evidence already observed:
- same object type and directory/catalog context;
- exact Product name;
- exact Product version;
- unique registry candidate;
- exact API membership agreement where available;
- exact Plan-name agreement where available;
- exact Plan-to-API entitlement agreement where available.

Do NOT define a generic rule that name + version alone equals identity.
The bridge must be scoped to this APIC export structure and require uniqueness plus structural corroboration.

Report:
- number of authoritative Product YAML artifacts mapped uniquely;
- number not mapped;
- registry-only Product records;
- any conflicts.

## B. API Artifact Identity Bridge

Treat API definitions under `staging/apis/_catalog` as authoritative API configuration artifacts for the API catalog.
Treat API registry/list records as APIC management identity evidence.

Validate whether each authoritative API definition can be deterministically enriched with one API registry identity using:
- exact API name;
- exact declared version;
- unique registry candidate;
- unique authoritative API-catalog artifact candidate;
- Product registry/API URL membership where available;
- Product YAML `$ref` convergence where available;
- file/structural equality only as corroborating evidence, never as the sole identity key.

Do NOT create a generic name+version merge rule.

Report:
- number of authoritative API definitions mapped uniquely;
- number not mapped;
- registry-only API records;
- any conflicts.

## C. API Copies Under Product Directory

For API-shaped documents under `staging/products/_catalog`:
- do not automatically treat them as separate API artifacts;
- do not automatically treat them as duplicates;
- resolve Product `$ref` to them using the approved `/staging/` mapping;
- compare them to authoritative API definitions only as corroborating/source-occurrence evidence;
- preserve the two known hash-different cases for review;
- determine whether any evidence proves a separate API identity.

Do not invent a new source-copy taxonomy. Describe their role using existing provenance/evidence fields only.

## D. Registry-only / Artifact-only Cases

Validate treatment of:
- 12 Product registry records without Product YAML;
- 36 API registry records without authoritative API-catalog full definition;
- any authoritative artifact with no registry entry.

Apply the source-precedence decision. Missing counterpart remains an explicit evidence gap; do not invent a status.

## E. Resolution Contract Closure

Determine whether the resolver contract can now be considered closed for:
- Consumer Org;
- Application;
- Credential;
- Subscription;
- Product;
- Plan;
- API Artifact;
- Product → API;
- Product → Plan;
- Plan → API;
- Subscription → Application/Product/Plan.

Use only the existing relationship taxonomy:
- `product_contains_api`
- `product_contains_plan`
- `plan_entitles_api`
- `application_belongs_to_consumer_org`
- `credential_belongs_to_application`
- `subscription_belongs_to_application`
- `subscription_targets_product`
- `subscription_uses_plan`
- `api_uses_catalog_property`
- `api_invokes_target`

Do not implement edges in this task.

## Required HANSOFF Content

Update only `codex/comm/HANSOFF.md` and report:
1. whether the source-precedence decision resolves the conceptual conflict from Task 003;
2. Product identity bridge evidence and aggregate mapping results;
3. API identity bridge evidence and aggregate mapping results;
4. Product-location API copy treatment and the two differing cases;
5. validation of the approved `/staging/` export-root mapping;
6. final resolver precedence/order;
7. which Task 003 gaps are now closed;
8. which gaps remain genuinely unresolved;
9. whether Phase 1 implementation is ready from a resolution-contract perspective or still blocked by a concrete evidence gap.

Use plain language for readiness. Do not create new status vocabulary.

## Mandatory Reporting Rule

The only reporting artifact is `codex/comm/HANSOFF.md`.
Do not create any other report/design/result/review/summary Markdown file.

## Non-Goals

Do not implement Python; modify tests; fix Phase 0 fixtures; modify Phase 0; modify staging; generate indexes/outputs; build CodeGraph; create graph edges; normalize URLs; perform semantic duplicate detection; infer runtime usage; classify Domain/Exposure Channel; resolve backends; or map APIC to Kong.

## Stop Condition

Stop after updating `codex/comm/HANSOFF.md` and wait for architecture review.