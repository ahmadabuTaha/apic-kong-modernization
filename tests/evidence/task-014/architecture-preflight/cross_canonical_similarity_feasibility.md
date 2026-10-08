# Cross-canonical structural similarity feasibility

Three targeted pairs retain two different canonical IDs and names, exact source paths/hashes, a shared backend-target identity, matching/differing method/path shapes, and schema-reference overlap. They were selected from compact dependency edges and then parsed only at their accepted API sources.

- `searchseasonalvisarequests` / `searchseasonalvisarequests-v2`: method/path-shape Jaccard 1.0; shared backend target is a candidate signal only; status `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`.
- `WDDSCertificateValidationAPI` / `wdds-certificate-validation-api`: method/path-shape Jaccard 1.0; shared backend target is a candidate signal only; status `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`.
- `proposals` / `ajeer-bulk-contracts`: method/path-shape Jaccard 0.4; shared backend target is a candidate signal only; status `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`.

These are feasibility examples, not duplicate findings. The only allowed status is `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`. Names were not used as proof. Shared backend alone is insufficient; generic CRUD shapes, shared middleware, versioned facades, protocol/channel differences, and dynamic routing create false positives. Path rewrites, schema aliases, indirect references, and assembly transformations create false negatives. Tasks 015–016 must validate observed and logical functions before any business-semantic conclusion.

```json
[
  {
    "apis": [
      {
        "api_name": "searchseasonalvisarequests",
        "canonical_api_id": "apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e",
        "operation_count": 1,
        "source_path": "staging/apis/_catalog/searchseasonalvisarequests_1.0.1.yaml",
        "source_sha256": "2d2885f9010c11de14f5e7517e0b8beb027352878626c7108d4d72b5d054a809"
      },
      {
        "api_name": "searchseasonalvisarequests-v2",
        "canonical_api_id": "apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb",
        "operation_count": 1,
        "source_path": "staging/apis/_catalog/searchseasonalvisarequests-v2_1.0.0.yaml",
        "source_sha256": "1d1c3edc6c49e7f44f40d317aa019da25050ab2297e2985c127c79a162f8d281"
      }
    ],
    "differing_signals": {
      "left_only_method_path_shapes": [],
      "right_only_method_path_shapes": []
    },
    "limitations": [
      "Shared backend does not prove duplication.",
      "Structural similarity does not establish business-semantic equivalence.",
      "No runtime traffic evidence was evaluated."
    ],
    "matching_signals": {
      "method_path_shape_intersection": [
        {
          "method": "post",
          "path_shape": "/searchseasvisareq"
        }
      ],
      "method_path_shape_jaccard": 1.0,
      "schema_reference_intersection": [
        "#/definitions/SearchSeasonalVisaRequestsRq_MessageType",
        "#/definitions/SearchSeasonalVisaRequestsRs_MessageType"
      ],
      "shared_backend_target_id": "backend-target:sha256:9edc5ce72c9462bb2af910f2d193140014601a8422e60c623ebdf43c842a107f"
    },
    "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION"
  },
  {
    "apis": [
      {
        "api_name": "WDDSCertificateValidationAPI",
        "canonical_api_id": "apic-identity:sha256:05afc366ab4881e1a066cf2b1f75881d83596b5ac19bbb2b2b4fdc239f27c201",
        "operation_count": 1,
        "source_path": "staging/apis/_catalog/WDDSCertificateValidationAPI_1.0.0.yaml",
        "source_sha256": "0fdf4aa69a8f647ab145159cd3c8e45016a67893a69d0b321fe8bfbdf80d17c6"
      },
      {
        "api_name": "wdds-certificate-validation-api",
        "canonical_api_id": "apic-identity:sha256:6ee892bf220701b553d4a49282520a6dae2d66e2d3ba5600e20749b13441162d",
        "operation_count": 1,
        "source_path": "staging/apis/_catalog/wdds-certificate-validation-api_1.0.0.yaml",
        "source_sha256": "dfd84ef9c34b26b37f173924c201bc2dada716bf2cf9cf3cca52e56827b0b9ad"
      }
    ],
    "differing_signals": {
      "left_only_method_path_shapes": [],
      "right_only_method_path_shapes": []
    },
    "limitations": [
      "Shared backend does not prove duplication.",
      "Structural similarity does not establish business-semantic equivalence.",
      "No runtime traffic evidence was evaluated."
    ],
    "matching_signals": {
      "method_path_shape_intersection": [
        {
          "method": "post",
          "path_shape": "/api/certificate/validate"
        }
      ],
      "method_path_shape_jaccard": 1.0,
      "schema_reference_intersection": [],
      "shared_backend_target_id": "backend-target:sha256:1eebf982f3d4d4984ad254abbbcdba76e60b5b26643a7e8521067665297cc495"
    },
    "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION"
  },
  {
    "apis": [
      {
        "api_name": "proposals",
        "canonical_api_id": "apic-identity:sha256:0f7a768abf0fdf88824ff5a4b3f1f03ad36592bb2f7c59bc2a2f771297fbfcf7",
        "operation_count": 3,
        "source_path": "staging/apis/_catalog/proposals_1.0.0.yaml",
        "source_sha256": "e67908bacbb1c010d4103dfd463bba38abb0cd94e48084dcb8250a9ce2cd95bc"
      },
      {
        "api_name": "ajeer-bulk-contracts",
        "canonical_api_id": "apic-identity:sha256:c265a4fb25b5c37c1dbd76a0d96ad8357354e04c8403c3ddf15512f4d266a3c0",
        "operation_count": 4,
        "source_path": "staging/apis/_catalog/ajeer-bulk-contracts_1.0.0.yaml",
        "source_sha256": "893968ceec6316e4c647ef706b59d6e37380edf5b39ba51f0d99b32b8331b1be"
      }
    ],
    "differing_signals": {
      "left_only_method_path_shapes": [
        [
          "post",
          "/"
        ]
      ],
      "right_only_method_path_shapes": [
        [
          "patch",
          "/{parameter}/cancel"
        ],
        [
          "put",
          "/{parameter}"
        ]
      ]
    },
    "limitations": [
      "Shared backend does not prove duplication.",
      "Structural similarity does not establish business-semantic equivalence.",
      "No runtime traffic evidence was evaluated."
    ],
    "matching_signals": {
      "method_path_shape_intersection": [
        {
          "method": "get",
          "path_shape": "/"
        },
        {
          "method": "get",
          "path_shape": "/{parameter}"
        }
      ],
      "method_path_shape_jaccard": 0.4,
      "schema_reference_intersection": [],
      "shared_backend_target_id": "backend-target:sha256:2d510af14a89dfb0bda088e6ff8f5cd35b5f31ccc5f3ceeef588aa145aeabb87"
    },
    "status": "POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION"
  }
]
```
