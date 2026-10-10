# Seasonal visa v2 contract and function assessment

- Comparison: `logical-function-comparison:sha256:706e85d0d327316a9992b7cf5d221400f7ba9b84c2090a78341de519234fbf02`.
- Proposal status: `POSSIBLE_SAME_LOGICAL_FUNCTION`; this is not approval of sameness, duplication, substitution, version precedence, retirement, or runtime equivalence.
- Both operations are `POST /searchseasvisareq` and have the same provisional Task 015 wording, `search seasonal visa requests`.
- Both carry API-shared candidate backend context only. The common configured target identity used for blocking does not prove either operation's runtime egress.
- The API versions differ (`1.0.1` versus `1.0.0`), but version labels do not establish replacement order.

## Actual safe request-shape differences

- `/0/resolved/properties/SearchSeasonalVisaRequestsRq/resolved/properties/Body/resolved/properties/SortBy`: PRESENT vs MISSING (PRESENCE_DIFFERENCE).

## Material response-shape differences

- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/InsertDate/type`: number vs integer (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/IssuedVisasList/resolved/properties/IssuedVisaInfo/items/resolved/properties/VisaExpiryDateGregorian/type`: number vs string (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/IssuedVisasList/resolved/properties/IssuedVisaInfo/items/resolved/properties/VisaExpiryDateHijri/type`: number vs string (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestSequence/type`: integer vs string (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequestYear/type`: integer vs string (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/required/0`: RequesterUserId vs RequesterIdNo (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/RequesterDetails/resolved/required/1`: RequesterIdNo vs RequesteUserId (VALUE_DIFFERENCE).
- `/0/schemas/0/resolved/properties/SearchSeasonalVisaRequestsRs/resolved/properties/Body/resolved/properties/SeasonalVisaList/resolved/properties/SeasonalVisa/items/resolved/properties/VisaIssuedDate/type`: number vs string (VALUE_DIFFERENCE).

The safe comparison found 30 response-shape differences in total, including field presence, required-list and type differences. Descriptions, examples and data values were omitted. The evidence supports review of a possible common apparent search function with different contracts; it does not support automatic merging or safe replacement.
