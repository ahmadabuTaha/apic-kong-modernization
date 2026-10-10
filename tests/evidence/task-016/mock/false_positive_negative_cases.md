# Task 016 mock false-positive and false-negative controls

## False-positive controls

- `logical-function-comparison:sha256:9bd27ebe8d9968fc1631cfdf875e99497edc1800ee646cbea2d16956207f7fda` shares a structural candidate block and path, but provisional source wording distinguishes validating attendance from updating appointment status and the safe request/response shapes differ. Status remains `REVIEW_REQUIRED_CONFLICTING_SIGNALS`.
- `logical-function-comparison:sha256:b4009b1ea20ca82ee22fa61beea004d69f820fc98dc76c5779c7d34fe84f477e` shares path/backend signals while its provisional wording and payload shapes conflict. It is not merged.
- `logical-function-comparison:sha256:92152040f1e8f5a440eb0acaa189939c6f4042eff40ee287968e071c2d5a6052` intentionally uses the same payment-token object with explicit generate versus delete actions. It is `CLEARLY_DIFFERENT_SUPPORTED`, demonstrating that object similarity is insufficient.
- `logical-function-comparison:sha256:65209a5c3d90970aa35bb3f1cae9ba2815e49d3eba751e2b971f5086fa182f7f` separates a health check from token retrieval using explicit path/action/contract evidence. Technical/security endpoints are not forced into a business function.

## Missing-evidence control

- `logical-function-comparison:sha256:91a36c3f75ef0f4e0d82ead0a608b87dee9b22add75e34dab4738759ae9494f4` contains root-path GET operations with insufficient Task 015 evidence. Shared backend/structure does not fill the semantic gap; status is `NOT_COMPARABLE_DUE_TO_MISSING_EVIDENCE`.

## False-negative limits

- Different paths or payload shapes may still represent a common intent behind a façade, adaptor, middleware transform, path rewrite, or versioned contract.
- Schema aliases and field renames can obscure shared intent; equal schema hashes can also hide behavioral differences not represented in configuration.
- Candidate-only backend context and staging configuration do not prove runtime routing. Runtime evidence, named design documentation, or human validation may change a proposal later without reopening frozen identity.
- No full-estate recall claim is made from this ten-pair mock.
