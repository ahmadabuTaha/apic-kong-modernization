# Task 012 Dependency Model Proposal

## Decision status

This document is an evidence-derived proposal for architecture review. It does not add canonical object types, relationship types, nodes, or edges.

Observed evidence ≠ proposed dependency model ≠ approved canonical model.

## Observed dependency concepts

- `2,334` backend invocation observations reused unchanged from Task 011.
- `2,329` OAuth2/OIDC provider or explicit security-endpoint observations from security-definition context.
- `4,147` exact Catalog Property or runtime-context references in dependency-bearing expressions.
- `1` explicit non-`invoke` HTTP policy dependency with ownership validation still required.
- `3` JWT/JWK configurations whose observed value shape does not safely prove an external provider or endpoint.
- `198` observations retain explicit operation scope; the remainder are API/shared.

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

- `1,158` APIs have both backend and security observations.
- `3` distinct explicit provider references were observed; `2` are shared by multiple APIs.
- `442` exact configuration tokens were observed; `262` are shared by multiple APIs.
- `1,151` safe normalized endpoint keys were observed; `159` are shared by multiple APIs.

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
