# Task 017A diverse deep dives

Selected proposal cases: **14**; bounded cross-API controls: **2**. All decisions remain EA `PENDING`.

## nic-prtissuespecialpermit 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:749a82d348e566260648ed73b7c06ff51dd4d3d9b01548083d28ec01bc1a3f68`; prior evidence: `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`.
- Recommendation: `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`. R1+R2+R7 remain supported with distinct actions on one explicit resource path family.
- Positive evidence: Accepted API nic-prtissuespecialpermit contains 3 exact operations; evidenced actions=['delete', 'issue'] and resources=['special permit'].
- Counterevidence: 2 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /special-permit` — actions `['issue']`, resource `special permit`; source `staging/apis/_catalog/nic-prtissuespecialpermit_1.0.0.yaml#/paths/~1special-permit/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/3` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `DELETE /special-permit/{permitNo}` — actions `['delete']`, resource `special permit`; source `staging/apis/_catalog/nic-prtissuespecialpermit_1.0.0.yaml#/paths/~1special-permit~1{permitNo}/delete`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/3` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /special-permit/{permitNo}` — actions `['issue']`, resource `special permit`; source `staging/apis/_catalog/nic-prtissuespecialpermit_1.0.0.yaml#/paths/~1special-permit~1{permitNo}/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/3` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=SUPPORTED, R2=SUPPORTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## mhrsd-submitsaudicertificate 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:8a1f06e977c530046055a09950b973b2bcd6c71edd96032acccf1387f98f09ce`; prior evidence: `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`.
- Recommendation: `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`. R1+R2+R7 remain supported with distinct actions on one explicit resource path family.
- Positive evidence: Accepted API mhrsd-submitsaudicertificate contains 2 exact operations; evidenced actions=['retrieve', 'submit'] and resources=['saudi certificate'].
- Counterevidence: 2 exact paths expose separate path responsibilities; 2 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /saudi-certificate` — actions `['submit']`, resource `saudi certificate`; source `staging/apis/_catalog/mhrsd-submitsaudicertificate_1.0.0.yaml#/paths/~1saudi-certificate/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /saudi-certificate/{certificateId}` — actions `['retrieve']`, resource `saudi certificate`; source `staging/apis/_catalog/mhrsd-submitsaudicertificate_1.0.0.yaml#/paths/~1saudi-certificate~1{certificateId}/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=SUPPORTED, R2=SUPPORTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## nic-submitrunawayrequest 2.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:9f803a60a91c3d36a836082007aa5689eb456a49eccbca8c90e63a32c7f6ea82`; prior evidence: `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`.
- Recommendation: `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`. R1+R2+R7 remain supported with distinct actions on one explicit resource path family.
- Positive evidence: Accepted API nic-submitrunawayrequest contains 3 exact operations; evidenced actions=['retrieve', 'submit', 'validate'] and resources=['runaway'].
- Counterevidence: 2 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `GET /run-away/{runAwayId}/request` — actions `['retrieve']`, resource `runaway`; source `staging/apis/_catalog/nic-submitrunawayrequest_2.0.0.yaml#/paths/~1run-away~1{runAwayId}~1request/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `POST /run-away/{runAwayId}/request` — actions `['submit']`, resource `runaway`; source `staging/apis/_catalog/nic-submitrunawayrequest_2.0.0.yaml#/paths/~1run-away~1{runAwayId}~1request/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `POST /run-away/{runAwayId}/request-validation` — actions `['validate']`, resource `runaway`; source `staging/apis/_catalog/nic-submitrunawayrequest_2.0.0.yaml#/paths/~1run-away~1{runAwayId}~1request-validation/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=SUPPORTED, R2=SUPPORTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## mhrsd-raiseobjectionrequest 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:b76cdde3ec3c354373fa3cc9e131e01eae8adf8d13aa0ce39ea27b3a2558ece0`; prior evidence: `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`.
- Recommendation: `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`. R1+R2+R7 remain supported with distinct actions on one explicit resource path family.
- Positive evidence: Accepted API mhrsd-raiseobjectionrequest contains 2 exact operations; evidenced actions=['create', 'retrieve'] and resources=['objection'].
- Counterevidence: 2 exact paths expose separate path responsibilities; 2 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /objection-request` — actions `['create']`, resource `objection`; source `staging/apis/_catalog/mhrsd-raiseobjectionrequest_1.0.0.yaml#/paths/~1objection-request/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /objection-request/{referenceNumber}` — actions `['retrieve']`, resource `objection`; source `staging/apis/_catalog/mhrsd-raiseobjectionrequest_1.0.0.yaml#/paths/~1objection-request~1{referenceNumber}/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=SUPPORTED, R2=SUPPORTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## nic-submitvisa 2.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:bfd3efab591b53cec46efb357d797ea8c7f1d09e72d7e8978ff8890d20761a7a`; prior evidence: `SUFFICIENT_FOR_PROVISIONAL_BOUNDARY`.
- Recommendation: `RETAIN_PROVISIONAL_COHESIVE_BOUNDARY`. R1+R2+R7 remain supported with distinct actions on one explicit resource path family.
- Positive evidence: Accepted API nic-submitvisa contains 3 exact operations; evidenced actions=['cancel', 'retrieve', 'submit'] and resources=['visa'].
- Counterevidence: 2 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `PROVISIONAL_REUSABLE_RESOURCE_CANDIDATE_NOT_A_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /establishment/{establishmentId}/visa` — actions `['submit']`, resource `visa`; source `staging/apis/_catalog/nic-submitvisa_2.0.0.yaml#/paths/~1establishment~1{establishmentId}~1visa/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `DELETE /establishment/{establishmentId}/visa/{borderNumber}` — actions `['cancel']`, resource `visa`; source `staging/apis/_catalog/nic-submitvisa_2.0.0.yaml#/paths/~1establishment~1{establishmentId}~1visa~1{borderNumber}/delete`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /establishment/{establishmentId}/visa/{borderNumber}` — actions `['retrieve']`, resource `visa`; source `staging/apis/_catalog/nic-submitvisa_2.0.0.yaml#/paths/~1establishment~1{establishmentId}~1visa~1{borderNumber}/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=SUPPORTED, R2=SUPPORTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## getlookups 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:0106e7c9e66e72c84c9578b38f2282a4e4f6f643f766e7ba57d3035454d9cf12`; prior evidence: `PARTIAL`.
- Recommendation: `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`. Direct paths identify 5 disjoint resource/responsibility subsets; unmatched members remain unresolved.
- Positive evidence: Accepted API getlookups contains 10 exact operations; evidenced actions=['list', 'retrieve'] and resources=['lookups'].
- Counterevidence: 9/10 members lack supported actions; 5 exact paths expose separate path responsibilities; 2 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `GET /getcountries` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getcountries/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getcountries` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getcountries/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /getembassies` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getembassies/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getembassies` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getembassies/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /getlookups` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getlookups/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getlookups` — actions `['list', 'retrieve']`, resource `lookups`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getlookups/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /getmaritalstatus` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getmaritalstatus/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getmaritalstatus` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getmaritalstatus/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /getoccupations` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getoccupations/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getoccupations` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getlookups_1.0.0.yaml#/paths/~1getoccupations/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/5` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=CONTRADICTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## mcs-rest-services 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:031efdf88d5d623541fcec8cc151ac4f6ef9dc0b3c6f08f4c904c225b29b0e18`; prior evidence: `PARTIAL`.
- Recommendation: `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`. Direct paths identify 3 disjoint resource/responsibility subsets; unmatched members remain unresolved.
- Positive evidence: Accepted API mcs-rest-services contains 3 exact operations; evidenced actions=['retrieve'] and resources=['employee historical info', 'employee info', 'employee qualification'].
- Counterevidence: resource signals diverge across ['employee historical info', 'employee info', 'employee qualification']; 3 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /get-employee-historical-info2` — actions `['retrieve']`, resource `employee historical info`; source `staging/apis/_catalog/mcs-rest-services_1.0.0.yaml#/paths/~1get-employee-historical-info2/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `POST /get-employee-info2` — actions `['retrieve']`, resource `employee info`; source `staging/apis/_catalog/mcs-rest-services_1.0.0.yaml#/paths/~1get-employee-info2/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `POST /get-employee-qualifications2` — actions `['retrieve']`, resource `employee qualification`; source `staging/apis/_catalog/mcs-rest-services_1.0.0.yaml#/paths/~1get-employee-qualifications2/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=CONTRADICTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## takamol-svp-apis-v1 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:040f0d52ac12de7d3094732c03a7ed1f4a420649709a1fd6af5330c8dd65c827`; prior evidence: `PARTIAL`.
- Recommendation: `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`. Direct paths identify 2 disjoint resource/responsibility subsets; unmatched members remain unresolved.
- Positive evidence: Accepted API takamol-svp-apis-v1 contains 7 exact operations; evidenced actions=['list', 'retrieve', 'update'] and resources=['categories', 'labors', 'occupations with not general category', 'test center status', 'test centers', 'web labors', 'web labors professional accreditation status'].
- Counterevidence: resource signals diverge across ['categories', 'labors', 'occupations with not general category', 'test center status', 'test centers', 'web labors']; 7 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `GET /web_service/categories` — actions `['list']`, resource `categories`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1categories/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /web_service/international_labors` — actions `['list']`, resource `labors`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1international_labors/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /web_service/labors` — actions `['retrieve']`, resource `web labors`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1labors/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /web_service/labors/professional_accreditation_status` — actions `['retrieve']`, resource `web labors professional accreditation status`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1labors~1professional_accreditation_status/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /web_service/occupations` — actions `['list']`, resource `occupations with not general category`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1occupations/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `POST /web_service/test_center_status_requests` — actions `['update']`, resource `test center status`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1test_center_status_requests/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /web_service/test_centers` — actions `['list']`, resource `test centers`; source `staging/apis/_catalog/takamol-svp-apis-v1_1.0.0.yaml#/paths/~1web_service~1test_centers/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=NOT_EVIDENCED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## kyan-user-validation 3.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:4b49c7df6eed5b1ac5eb264f0266192a29b5d11d81f87ec1058a595a5d96d16b`; prior evidence: `PARTIAL`.
- Recommendation: `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`. Direct paths identify 2 disjoint resource/responsibility subsets; unmatched members remain unresolved.
- Positive evidence: Accepted API kyan-user-validation contains 3 exact operations; evidenced actions=['retrieve'] and resources=['national id for user type 1 based on', 'test'].
- Counterevidence: resource signals diverge across ['national id for user type 1 based on', 'test']; 1/3 members lack supported actions; 3 exact paths expose separate path responsibilities; 3 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /test` — actions `['NONE']`, resource `test`; source `staging/apis/_catalog/kyan-user-validation_3.0.0.yaml#/paths/~1test/post`; security `['oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /verifydelegator` — actions `['retrieve']`, resource `national id for user type 1 based on`; source `staging/apis/_catalog/kyan-user-validation_3.0.0.yaml#/paths/~1verifydelegator/get`; security `['oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).
  - `GET /verifyowner` — actions `['retrieve']`, resource `national id for user type 1 based on`; source `staging/apis/_catalog/kyan-user-validation_3.0.0.yaml#/paths/~1verifyowner/get`; security `['oauth2']`; backend operation-scoped/candidate counts `0/2` (runtime not proven); Product/Plan counts `2/2` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=CONTRADICTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## adminmanagement-supportcentre 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:d7b1f2f44d227a7323055bad6578d2be08bc3c67c7ea93ff4cf40924ff768761`; prior evidence: `PARTIAL`.
- Recommendation: `SPLIT_INTO_EVIDENCED_SUB_BOUNDARIES`. Direct paths identify 3 disjoint resource/responsibility subsets; unmatched members remain unresolved.
- Positive evidence: Accepted API adminmanagement-supportcentre contains 8 exact operations; evidenced actions=['activate', 'create', 'list'] and resources=['block', 'dsn', 'dsn inactive', 'queries'].
- Counterevidence: resource signals diverge across ['block', 'dsn', 'dsn inactive', 'queries']; 3/8 members lack supported actions; 8 exact paths expose separate path responsibilities.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `SEPARATE_RESOURCE_POLICY_OR_CONSUMER_BOUNDARY_CONSIDERATIONS_NOT_PRODUCTS`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `POST /dsn/activate` — actions `['activate']`, resource `dsn`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1dsn~1activate/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /dsn/inactive/list` — actions `['list']`, resource `dsn inactive`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1dsn~1inactive~1list/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /dsn/insert` — actions `['create']`, resource `dsn`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1dsn~1insert/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /queries/approve-reject` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1queries~1approve-reject/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /queries/inactive` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1queries~1inactive/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /queries/insert` — actions `['create']`, resource `queries`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1queries~1insert/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /users/account/activate-block` — actions `['activate']`, resource `block`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1users~1account~1activate-block/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /users/details` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/adminmanagement-supportcentre_1.0.0.yaml#/paths/~1users~1details/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `1/0` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=CONTRADICTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=SUPPORTED, R6=SUPPORTED, R7=SUPPORTED.

## ajeer-bulk-contracts 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:4ec7e106c3f62fead62d407e74bad12fe6bef44252580a7def05c0dd7b32bbc8`; prior evidence: `PARTIAL`.
- Recommendation: `REQUIRES_TARGETED_EVIDENCE`. Concrete lifecycle, resource-responsibility, owner, or consumer evidence is required to decide cohesion versus split.
- Positive evidence: Accepted API ajeer-bulk-contracts contains 4 exact operations; evidenced actions=['cancel', 'retrieve', 'update'] and resources=['contract uuid'].
- Counterevidence: 1/4 members lack supported actions; 3 exact paths expose separate path responsibilities.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `DEFER_PRODUCTIZATION_BOUNDARY_PENDING_NAMED_EVIDENCE`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `GET /` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/ajeer-bulk-contracts_1.0.0.yaml#/paths/~1/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /{contractUuid}` — actions `['retrieve']`, resource `contract uuid`; source `staging/apis/_catalog/ajeer-bulk-contracts_1.0.0.yaml#/paths/~1{contractUuid}/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PUT /{contractUuid}` — actions `['update']`, resource `contract uuid`; source `staging/apis/_catalog/ajeer-bulk-contracts_1.0.0.yaml#/paths/~1{contractUuid}/put`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PATCH /{contractUuid}/cancel` — actions `['cancel']`, resource `contract uuid`; source `staging/apis/_catalog/ajeer-bulk-contracts_1.0.0.yaml#/paths/~1{contractUuid}~1cancel/patch`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=CONTRADICTED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## qiwa-streaming-v2 2.0.1

- Baseline ID: `logical-api-boundary-proposal:sha256:1a081e0cf253181bb921e8a5af4e3c70ddbf44664fbb0050d0be2b9565784c17`; prior evidence: `PARTIAL`.
- Recommendation: `TECHNICAL_OR_TEST_EXPOSURE_REVIEW`. accepted API identity `qiwa-streaming-v2` directly labels a technical/test/POC exposure; this is a lifecycle/policy review, not retirement.
- Positive evidence: Accepted API qiwa-streaming-v2 contains 7 exact operations; evidenced actions=['delete', 'retrieve', 'update'] and resources=['conversation id'].
- Counterevidence: 3/7 members lack supported actions.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `STRUCTURAL_OR_TECHNICAL_LIFECYCLE_CANDIDATE_NOT_A_BUSINESS_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `DELETE /{conversationId}` — actions `['delete']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/delete`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /{conversationId}` — actions `['retrieve']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `HEAD /{conversationId}` — actions `['NONE']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/head`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `OPTIONS /{conversationId}` — actions `['NONE']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/options`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PATCH /{conversationId}` — actions `['update']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/patch`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /{conversationId}` — actions `['NONE']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PUT /{conversationId}` — actions `['update']`, resource `conversation id`; source `staging/apis/_catalog/qiwa-streaming-v2_2.0.1.yaml#/paths/~1{conversationId}/put`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=NOT_EVIDENCED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## graphql_poc 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:003cf2ee1300e6bc50c14e0680ed3c3e7cd5df5c08c7e569f4d46e01e5b11f18`; prior evidence: `PARTIAL`.
- Recommendation: `TECHNICAL_OR_TEST_EXPOSURE_REVIEW`. accepted API identity `graphql_poc` directly labels a technical/test/POC exposure; this is a lifecycle/policy review, not retirement.
- Positive evidence: Accepted API graphql_poc contains 2 exact operations; evidenced actions=['retrieve'] and resources=['graphql'].
- Counterevidence: 1/2 members lack supported actions; 2 contract/security fingerprints differ.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `STRUCTURAL_OR_TECHNICAL_LIFECYCLE_CANDIDATE_NOT_A_BUSINESS_PRODUCT`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `GET /graphql` — actions `['retrieve']`, resource `graphql`; source `staging/apis/_catalog/graphql_poc_1.0.0.yaml#/paths/~1graphql/get`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /graphql` — actions `['NONE']`, resource `graphql`; source `staging/apis/_catalog/graphql_poc_1.0.0.yaml#/paths/~1graphql/post`; security `['apiKey']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=NOT_EVIDENCED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## getunifiednumberworkpermit 1.0.0

- Baseline ID: `logical-api-boundary-proposal:sha256:00a8fc813f526bc99a48515ef224826e184085b1bf4bf0549775161fc6f17b35`; prior evidence: `INSUFFICIENT`.
- Recommendation: `KEEP_AS_IS_EXPOSURE_NO_LOGICAL_BOUNDARY_ASSERTION`. No supported action/resource evidence exists beyond current API coexistence.
- Positive evidence: Accepted API getunifiednumberworkpermit contains 6 exact operations; evidenced actions=['NONE'] and resources=['NONE'].
- Counterevidence: 6/6 members lack supported actions.
- Alternative: Retain each operation as its own conceptual boundary pending direct lifecycle, owner, or consumer evidence.
- Productization: `AS_IS_STRUCTURAL_EXPOSURE_ONLY_NOT_A_PRODUCT_CANDIDATE`; gate `AFTER_TASK019_BEFORE_PRODUCTIZATION_DESIGN`.
- Exact operations:

  - `DELETE /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/delete`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `GET /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/get`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `HEAD /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/head`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PATCH /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/patch`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `POST /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/post`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).
  - `PUT /getestablishmentunifiednumber` — actions `['NONE']`, resource `NONE`; source `staging/apis/_catalog/getunifiednumberworkpermit_1.0.0.yaml#/paths/~1getestablishmentunifiednumber/put`; security `['apiKey', 'oauth2']`; backend operation-scoped/candidate counts `0/1` (runtime not proven); Product/Plan counts `1/1` (consumption not proven).

R1-R7 group result: R1=NOT_EVIDENCED, R2=NOT_EVIDENCED, R3=NOT_EVIDENCED, R4=SUPPORTED, R5=NOT_EVIDENCED, R6=SUPPORTED, R7=SUPPORTED.

## Cross-API control: Seasonal Visa Request Search

- Link: `task017a-cross-api-link:sha256:5be5a0b33f1b455d26dd68ee8fede7b395b6aa12ae8cfa7374888967a4df4648`; status `BOUNDED_CROSS_API_ALTERNATIVE_PENDING`.
- Operations: `['semantic-operation-v2:sha256:088205524e81575245aaf18ff417aeefffc6f40d4b7b6b330b38d4774be65819', 'semantic-operation-v2:sha256:7d8f53ed3c35f190c656a73167c4fb3b94b72e6dc3f143455544fb74ac257751']`.
- Exact sources: `['staging/apis/_catalog/searchseasonalvisarequests_1.0.1.yaml#/paths/~1searchseasvisareq/post', 'staging/apis/_catalog/searchseasonalvisarequests-v2_1.0.0.yaml#/paths/~1searchseasvisareq/post']`.
- Positive: ['Task 016 records a possible same behavior hypothesis across versioned exposures.']
- Contrary: ['Material request/response differences and consumer/product context must be reviewed before choosing a boundary.']
- This is an alternative link only: no primary membership, equivalence, transitive inference, or product is created.

## Cross-API control: SC Request Workflow

- Link: `task017a-cross-api-link:sha256:e13eed5c94057177d268fc8c1636bf6a242c7492bbaf826aa7ef07ec3a65c86c`; status `BOUNDED_CROSS_API_ALTERNATIVE_PENDING`.
- Operations: `['semantic-operation-v2:sha256:17369afae2c78b61b5c9a90cb439396f1c2e003f8e8d2511891eca36558f8553', 'semantic-operation-v2:sha256:6262beb0681057700b629ad6eebcca0da2492f937e01ca6e774e0192440f09cb']`.
- Exact sources: `['staging/apis/_catalog/approverejectscrequest_1.0.1.yaml#/paths/~1apprejscreq/post', 'staging/apis/_catalog/cancelscrequest_1.0.0.yaml#/paths/~1cancelscreq/post']`.
- Positive: ['Source description explicitly bundles approve/reject and separately documents cancel on the same SC request resource.']
- Contrary: ['Approve, reject, and cancel are distinct actions; the bundled endpoint does not make them duplicates.']
- This is an alternative link only: no primary membership, equivalence, transitive inference, or product is created.
