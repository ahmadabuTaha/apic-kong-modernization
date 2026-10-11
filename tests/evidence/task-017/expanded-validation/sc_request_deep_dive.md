# SC Request boundary deep dive

This anchor contains exactly two APIC source operations. The first source operation documents both approve and reject intents; those are two logical intents carried by one source operation, not three manufactured APIC operations. The second source operation documents cancel.

| Source API | Front-end operation | Supported intents | Request refs / response shape | Configured backend | Accepted Product IDs / relationships | Accepted Plan IDs / relationships |
|---|---|---|---|---|---|---|
| approverejectscrequest | POST `/apprejscreq` | approve, reject | #/definitions/ApproveRejectSCRequestRq_MessageType / 816ff2aad61fcd5dbd5517a80bdc21e5b92fbf571d83f9c5ff4aa5b1fc81312e | CONFIGURED_API_SHARED_CANDIDATE: /sc/apprejscreq | apic-identity:sha256:b43d240aa3d47b8cb1c05b8758d88902787920e64179b0142cd0742f4652d886; relationships: apic-relationship:sha256:93d21bbf4c33c46f91c4b224286b022e4010a37dd36d1698fd193b34f20ba2be | apic-identity:sha256:740d847bc10ba9aa79ed07bc3db7e701125af532ba929eafa242ec2aa16ace25; relationships: apic-relationship:sha256:9b4773a921f2c366579ecfb193a637d9875d0d7fb361d91f4b0391a601999cd2 |
| cancelscrequest | POST `/cancelscreq` | cancel | #/definitions/CancelSCRequestRq_MessageType / a8df6c4feac0805ff7edb2067b495eee378acf4720b4ff26752dfc4b3414c16c | CONFIGURED_API_SHARED_CANDIDATE: /sc/cancelscreq | apic-identity:sha256:e83996f412c4e4084257951dd867bad144e336572d11128e7eb593b72c5220a0; relationships: apic-relationship:sha256:128d1bc8f710a8649590f56076c4b9ef92bc9014453016a1c6783e52f7f9c806 | apic-identity:sha256:b8e0ba925726d8d418f11b5ac1d25e92c41d37b1abed1850a3ea64c3495a6144; relationships: apic-relationship:sha256:c172f3464ee2111e4beef05e126a00a656445bdf74873a5c3e0a3bf2f6aa1049 |

Both configured backend paths (`/sc/apprejscreq` and `/sc/cancelscreq`) are resolved configuration observations but have `CONFIGURED_API_SHARED_CANDIDATE` scope. They are different paths and do not prove backend behavioral equivalence or actual calls. The accepted Product and Plan IDs and relationship pointers are distinct exposure context. They do not prove common consumers, entitlement intent, owner, release path, active deployment, or production traffic.

## Why provisional cohesion is possible

The direct descriptions and paths support approve/reject/cancel action signals around an SC Request object. A **Unified SC Request Actions** boundary could give consumers one resource-oriented conceptual surface while retaining three distinct logical actions and the two original source-operation identities.

## Why architectural PASS is unavailable

No accepted evidence establishes that decision and cancellation share one lifecycle owner, consumer population, authorization model, entitlement, release cadence, or backend operation. Different front-end schemas, backend paths, Products, and Plans are material counterevidence. Technical validation PASS only proves that this evidence was reproduced correctly; the evidence-sufficiency result is `PARTIAL` and architect acceptance remains `PENDING`.

## Plausible alternative

A **Decision API** could contain approve/reject, while a separate **Cancellation API** owns cancel. That is reasonable if roles, owners, entitlement, audit controls, release cadence, or downstream behavior differ. The unified boundary becomes more reasonable only with authoritative workflow ownership, common consumer intent, authorization and lifecycle evidence; the split becomes more reasonable if those sources prove separation. None is inferred here.
