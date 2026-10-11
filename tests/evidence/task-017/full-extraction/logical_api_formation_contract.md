# Task 017 full Logical API formation contract

## Purpose and boundaries

This is a deterministic, source-provenanced **provisional conceptual boundary**
catalog over the accepted Task 014 HTTP operation inventory. A Logical API is
not an APIC API identity, APIC Product, Kong Service, Kong Route, or Kong Product.
Functional-equivalence candidates and Logical API cohesion are separate axes:
distinct actions can belong to one resource/workflow boundary without being
duplicates; a possible same action across APIs does not establish shared cohesion.

Each accepted Task 014 operation appears exactly once in the primary disposition
ledger. Within-current-API proposals use direct operation assertions. Task 016
cross-API comparisons remain candidate references only. No transitive closure,
automatic merge, retirement, Domain, Capability, Kong design, or production
claim is made. Operations with insufficient evidence, singletons, oversized
groups, and API-level gaps remain visible as nonformation outcomes.

## Evidence criteria R1-R7

Each proposal and each direct member assertion records all seven criteria with a
`SUPPORTED`, `CONTRADICTED`, or `NOT_EVIDENCED` status and source references:

| Criterion | Assessment |
|---|---|
| R1 Resource | Explicit/corroborated non-generic resource, workflow, or resource identity. |
| R2 Cohesion | Distinct actions plus a direct resource-path family or evidenced lifecycle/workflow; shared object tokens alone do not suffice. |
| R3 Consumer/authorization/ownership | Product, Plan, and Subscription links remain exposure context; they do not establish actual consumers, owners, roles, or entitlement intent. |
| R4 Contract and variants | Exact method/path, API version, request/response fingerprints, status codes, and security requirements stay visible; compatibility is not inferred. |
| R5 Backend operation | Operation-scoped configuration is distinct from API-shared candidate context and from proven runtime behavior/egress. |
| R6 Counterevidence | A concrete reason not to group, a plausible alternative, and the evidence that could decide are retained. |
| R7 Provenance | Canonical API, Task 014 operation, Task 015 observed-function, Task 016 candidate/refinement IDs, source hashes, and source pointers are traceable. |

For a bounded current-API resource-path family, R1+R2+R7 can support
`SUFFICIENT_FOR_PROVISIONAL_BOUNDARY` even when R3/R5 remain
`NOT_EVIDENCED`. Cross-canonical-API formation is deliberately not automated in
this pass. Generic wrappers, shared schemas, backend/system matches, Product
overlap, and names alone do not establish cohesion.

## Primary membership and competing alternatives

`task017_full_operation_disposition.jsonl` is the sole primary operation
disposition. Each row has one direct proposal link at most. Proposal alternatives
and Task 016 functional candidates remain separately identified; they do not
duplicate primary membership or collapse source operation IDs. A source
operation may retain multiple action intents (including the SC Request
approve/reject operation) without manufacturing source operations.

## Independent result axes

1. `TECHNICAL_VALIDATION` describes deterministic construction, reconciliation,
   frozen-input integrity, and tests only.
2. `EVIDENCE_SUFFICIENCY` is `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`, `PARTIAL`,
   `INSUFFICIENT`, or `SUPPORTED_SEPARATE`.
3. `ARCHITECT_ACCEPTANCE` remains `PENDING` for every proposal.

Technical PASS is not architecture PASS. No proposal has been accepted by the
Enterprise Architect in this output.
