# Task 014 full semantic inventory contract v2

- Canonical API identity remains the envelope and join anchor; operations remain inventory records, not graph nodes.
- Every accepted canonical API receives exactly one API inventory record, including registry-only and unsupported states.
- Root source occurrences are grouped by SHA-256. Byte-identical representations reuse one parsed payload. Different-hash variants retain occurrence, role, path, hash, and structural fingerprint. Equivalent variants reuse one semantic payload; conflicts retain distinct payload/operation identities and `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW`.
- Operation v2 IDs use canonical API ID, structural variant fingerprint, exact method, and exact path. `legacy_semantic_operation_inventory_id_v1` preserves migration traceability for the six-API mock contract.
- Backend facts are `CONFIGURED_API_SHARED` or `EVIDENCED_OPERATION_SCOPED`. Possible inherited per-operation context is a separate `CANDIDATE_INHERITED_CONTEXT` layer with `CANDIDATE_ONLY`, exact provenance, and explicit false values for proven egress/runtime use.
- Requests and responses retain content types, status codes, references, and hashes of deterministic safely resolved local schema shapes. Reference labels alone do not establish schema equality.
- Product/Plan connections are AS-IS accepted relationships. The 113 unresolved Product-location occurrences remain unresolved diagnostic evidence and are not attached as accepted relationships.
- Structural-overlap candidates require a shared backend block plus operation-contract evidence, remain bounded, retain separate canonical IDs, and have only `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION` status.
- Cache entries include source occurrence/hash fingerprint, extractor/schema version, and accepted backend/relationship/unresolved-evidence dependency fingerprint. Writes are atomic and invalidation reasons are explicit.
- No functional duplication, Logical API, business domain, capability, runtime use, or Kong target is inferred.
