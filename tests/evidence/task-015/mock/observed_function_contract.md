# Task 015 Observed Function mock contract

- An Observed Function is a provisional, evidence-grounded interpretation of one Task 014 HTTP operation. It is not a Logical Function, Logical API, domain, capability, duplicate conclusion, runtime observation, or Kong design.
- Identity is derived from the stable Task 014 operation ID plus the versioned deterministic rules contract. Canonical API ID, exact source method/path, source fingerprint and provenance remain mandatory.
- Candidate wording has an action verb and object/resource phrase only when supported by source description/summary/operationId or multiple independent structural signals. HTTP method alone never supplies a sufficient business meaning.
- Status is one of `EXPLICITLY_DESCRIBED`, `INFERRED_FROM_MULTIPLE_STRUCTURAL_SIGNALS`, `AMBIGUOUS_NEEDS_REVIEW`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_PROTOCOL`, or `REGISTRY_ONLY_NO_OPERATIONS`. The last two are API-level states in this HTTP-operation mock and never fabricate operation records.
- Evidence strength is HIGH, MEDIUM, LOW, or NONE with a reason. Missing fields, contradictions and inherited gaps remain explicit and link to stable gap IDs.
- Exact operation-scoped backend configuration remains a fact. API-shared backend context remains `CANDIDATE_INHERITED_CONTEXT` / `CANDIDATE_ONLY`; neither proves runtime use or operation egress.
- Similar wording under different canonical APIs remains separate. Structural-overlap candidates require human semantic validation and are never confirmed duplicates here.
- Reviewer status starts `PENDING_REVIEW`. Only Integration/Enterprise Architect review may approve or reject interpretations or gap classifications.
- This mock is deterministic and used no language model; model token usage is zero. It does not authorize estate-wide Task 015 extraction.
