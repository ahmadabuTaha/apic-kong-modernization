# YAML representation and variant options

## Index-only profile

- Canonical API groups with multiple root YAML representations: 1778.
- Groups whose representations all have one SHA-256: 1776.
- Groups with multiple SHA-256 values: 2.
- Groups with more than one authoritative API artifact: 0.
- Representation-count distribution: `{"10": 1, "2": 1482, "3": 226, "4": 26, "5": 8, "6": 24, "7": 8, "8": 1, "9": 2}`.

This is an estate-wide cheap occurrence/hash profile, not an estate-wide semantic comparison. Targeted parsing compared only the two multi-hash groups. Both are `SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS`: their operation contracts and safe assembly-policy shapes match even though bytes differ. A real conflicting same-ID representation was therefore `NOT_EVIDENCED_IN_SAMPLE`. The committed JSONL retains occurrence IDs, source roles, paths, file hashes, fingerprints, operation counts, and exact method/path anchors.

## Proposed classifications

1. `BYTE_IDENTICAL_DUPLICATE_REPRESENTATIONS`: retain every occurrence as provenance; materialize one structural payload.
2. `SEMANTICALLY_EQUIVALENT_STRUCTURAL_VARIANTS`: retain every variant and fingerprint; canonical output may reference one shared structural payload only if the architect approves.
3. `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW`: retain separate variant operation records and provenance; never union, overwrite, or lexically select semantic truth automatically.
4. `COMPETING_AUTHORITATIVE_REPRESENTATIONS`: a source-role conflict requiring review even when structure matches. None occurred in the index profile.

## Options

1. Lexically select the first accepted API YAML. Reject for conflicts because it can silently discard methods, parameters, schemas, or assembly differences.
2. Recommended: canonical API envelope plus retained source variants. Collapse only byte-identical payload storage; preserve equivalent-variant fingerprints; emit per-variant operations and `CONFLICT_REQUIRES_ARCHITECTURE_REVIEW` when fingerprints differ. Do not redefine the Phase 2 canonical ID.
3. Merge all variants. Reject as a default because unioning can invent a contract that no source contains.

The normalized fingerprint includes format, exact method/path, path shape, compact parameter facts, request/response `$ref` values and statuses, and value-free assembly-policy shapes. It does not expand schemas or expose endpoint/credential values. Descriptive presence is recorded separately so text-only differences do not masquerade as contract conflicts.
