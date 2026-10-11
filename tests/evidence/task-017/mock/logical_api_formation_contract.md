# Task 017 representative logical API formation contract

This contract applies only to the bounded representative mock. A Logical API is a provisional TO-BE conceptual resource or workflow boundary. It is neither an APIC API or Product nor a Kong Service, Route, or Product.

## Identity and membership

`logical_api_candidate_id` is a deterministic hash of the case key and sorted Task 014 member operation IDs. Every member retains its accepted canonical API ID, Task 014 operation ID, Task 015 observed-function ID, Task 016 references when applicable, endpoint, contract, source pointer, source hash, and source-variant fingerprint. Membership is an explicit star edge from the candidate to each operation. Non-formation controls retain candidate members but mark membership `NOT_ASSERTED_NONFORMATION_CASE`.

## Independent relations

`FUNCTIONAL_EQUIVALENCE_CANDIDATE` asks whether operations may perform the same action, object, and behavioral intent. It never collapses IDs and remains unapproved. `LOGICAL_API_COHESION` asks whether distinct operations belong to one consumer-facing resource or workflow. Related actions such as approve, reject, cancel, submit, and update remain distinct logical operations. Pairwise evidence is never transitively closed.

Contract compatibility, backend certainty, AS-IS Product/Plan context, runtime evidence, and migration safety remain separate fields. API-shared configured routes are not promoted to operation semantics. Product relationships provide exposure context only; a Product never becomes a Logical API by default.

## Status model

- `COHESIVE_LOGICAL_API_CANDIDATE`: bounded evidence supports a provisional boundary; architect review remains required.
- `PARTIAL_OR_VARIANT_BOUNDARY_REVIEW`: cohesion is plausible but version, contract, consumer, or unresolved-member differences affect the boundary.
- `INSUFFICIENT_EVIDENCE_TO_FORM`: no membership is asserted; targeted evidence is required.
- `SEPARATE_LOGICAL_APIS_SUPPORTED`: evidence supports separate boundaries; no consolidation is proposed.

All labels are business-neutral resource/workflow labels, not Domain or Capability assignments. No status approves equivalence, production use, migration, retirement, or Kong topology.
