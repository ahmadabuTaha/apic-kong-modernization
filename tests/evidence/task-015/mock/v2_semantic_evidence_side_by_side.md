# v2 semantic evidence side by side

| Dimension | searchseasonalvisarequests | searchseasonalvisarequests-v2 | Evidence state |
|---|---|---|---|
| Canonical identity | `apic-identity:sha256:3165d30141993d77200c2630b10c29760e0e1c8f6520eb3368a12d6dd484657e` | `apic-identity:sha256:6fa70f88ad990dcda279d38753d1e83806dc591c09b74619e945129c553f2aeb` | Distinct identities |
| API version | `1.0.1` | `1.0.0` | `DIFFERENT` |
| HTTP operation | `POST /searchseasvisareq` | `POST /searchseasvisareq` | `EQUAL` |
| Provisional Observed Function | `search seasonal visa requests` | `search seasonal visa requests` | Similar wording, not a Logical Function conclusion |
| Request contract | Same reference label; shape `ea26b7f17dc9182c7b8bffe86b9c3572899e84125222f74bc2a5ac365b8524bc` | Same reference label; shape `bf653443c106ac043d03f81371bd5122919836b3542c04a68478127842daf10e` | `DIFFERENT` |
| Response contract | HTTP 200; shape `01481532be58e839620181b819ef4c9cd77aafd9d5441bec16fd98a9d20f060d` | HTTP 200; shape `86041b2a38c35814cb131a994010222b9fc6ea4fc913c18d73452e360ae2dfbd` | `DIFFERENT` |
| Backend target identity | `backend-target:sha256:9edc5ce72c9462bb2af910f2d193140014601a8422e60c623ebdf43c842a107f` | `backend-target:sha256:9edc5ce72c9462bb2af910f2d193140014601a8422e60c623ebdf43c842a107f` | `EQUAL` configuration target identity only |
| Backend operation context | API_SHARED, unresolved path, candidate only | API_SHARED, unresolved path, candidate only | Different provenance; no runtime/egress proof |
| Auth/exposure | apiKey; HTTPS marker | apiKey; HTTPS marker | Equal structural markers only |

## Safe targeted request-shape differences

- `/resolved/properties/SearchSeasonalVisaRequestsRq/resolved/properties/Body/resolved/properties/SortBy`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).

## Safe targeted response-shape differences

- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/Email`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/EndorsementId`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/FirstName`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/GovernmentalSector`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/InsertDate/type`: number vs integer (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/IssuedVisasList/resolved/properties/IssuedVisaInfo/items/resolved/properties/VisaExpiryDateGregorian/type`: number vs string (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/IssuedVisasList/resolved/properties/IssuedVisaInfo/items/resolved/properties/VisaExpiryDateHijri/type`: number vs string (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/LastName`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestDetailsList/resolved/properties/RequestDetail/items`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestDetailsList/resolved/properties/RequestDetail/local_ref`: MISSING vs PRESENT (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestDetailsList/resolved/properties/RequestDetail/resolved`: MISSING vs PRESENT (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestDetailsList/resolved/properties/RequestDetail/type`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestId`: MISSING vs PRESENT (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestSequence/type`: integer vs string (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestStatus`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestStatusId`: MISSING vs PRESENT (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestYear/type`: integer vs string (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/properties/RequesteUserId`: MISSING vs PRESENT (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/properties/RequesterUserId`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/required/0`: RequesterUserId vs RequesterIdNo (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/required/1`: RequesterIdNo vs RequesteUserId (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterMobileNumber`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/SeasonalAvailabilityExpirationDate`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/SeasonalAvailabilityExpirationDateHijri`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/SeasonalVisasExpirationDate`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/SeasonalVisasExpirationDateHijri`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/VisaIssuedDate/type`: number vs string (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/required`: 19 vs 13 (LIST_LENGTH_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/required/4`: RequestStatus vs RequestStatusId (VALUE_DIFFERENCE).
- `/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaRequestJobDetails`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).

The safe diff compared locally resolved schema structure and omitted descriptions, examples and values. The left request contains `SortBy` where the right does not. Response differences include presence/absence and type changes; the committed pointers above are evidence, not a semantic-equivalence conclusion. The status remains `POSSIBLE_STRUCTURAL_OVERLAP_REQUIRES_SEMANTIC_VALIDATION`. No functional duplication, replacement/version precedence, shared runtime egress, domain or capability is asserted.
