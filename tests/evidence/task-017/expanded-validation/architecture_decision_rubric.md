# Task 017 expanded boundary decision rubric

This is a proposal for consistent review, not an enterprise standard. It applies only to this bounded validation sample. A conceptual Logical API is neither functional equivalence nor an APIC Product nor a Kong topology.

## Per-boundary and per-membership criteria

- **R1 — resource:** an identified and adequately supported business object, resource, or workflow.
- **R2 — cohesion:** supported distinct actions plus direct evidence of a coherent lifecycle, workflow, or resource responsibility. Object-token, schema, backend, name, or Product overlap alone cannot satisfy R1 and R2.
- **R3 — consumer boundary:** consumer exposure, ownership, authorization, and entitlement intent. Accepted Product/Plan/subscription links are context; they do not prove actual consumers, ownership, calls, or one boundary.
- **R4 — contract:** exact/base path, method, version, security, shape, and transformation differences are preserved. Compatibility is never inferred.
- **R5 — backend:** operation-level configured evidence is distinguished from API-shared candidates. Neither proves runtime egress.
- **R6 — counterevidence:** every proposal states a reason not to group, an alternative boundary, and discriminating missing evidence.
- **R7 — provenance:** exact accepted IDs, pointers, hashes, and scope certainty remain traceable.

Each criterion is `SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED`. `NOT_EVIDENCED` stays explicit and cannot be upgraded by structural similarity.

## Three independent result axes

1. **Technical validation:** `PASS` or `FAIL` means only deterministic build/tests, stable IDs, reproduction, and source integrity.
2. **Evidence sufficiency:** `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`, `PARTIAL`, `INSUFFICIENT`, or `SUPPORTED_SEPARATE` summarizes R1–R7. It is not architecture approval.
3. **Architect acceptance:** always `PENDING` in this sample until an explicit Enterprise Architect decision.

Functional-equivalence candidates never collapse member IDs. Pairwise A~B and B~C are not closed into A~C. Original ten mock records are immutable anchors; their prior dispositions are preserved separately from the expanded review finding.
