# CyMed WHO ICD-11 Integration

Real client for the **WHO ICD-11 REST API** (<https://icd.who.int/icdapi>).
The WHO documents the underlying endpoints under the two hosts below and
mandates OAuth2 `client_credentials` for every non-public call.

| Purpose        | Endpoint                                                                          |
| -------------- | --------------------------------------------------------------------------------- |
| OAuth2 token   | `POST https://icdaccessmanagement.who.int/connect/token` (`grant_type=client_credentials`) |
| Linearization  | `https://id.who.int/icd/release/11/{release}/mms` (MMS)                          |
| Foundation     | `https://id.who.int/icd/entity/{entity_id}`                                       |

Required request headers on every call to the ICD-11 API:

- `Authorization: Bearer <token>`
- `API-Version: v2`
- `Accept: application/json`
- `Accept-Language: <bcp47>` (default `en`)

## Environment variables

| Var                     | Required        | Default                                                    | Notes                                             |
| ----------------------- | --------------- | ---------------------------------------------------------- | ------------------------------------------------- |
| `WHO_ICD_CLIENT_ID`     | yes (real API)  | —                                                          | From <https://icdaccessmanagement.who.int/>       |
| `WHO_ICD_CLIENT_SECRET` | yes (real API)  | —                                                          | From <https://icdaccessmanagement.who.int/>       |
| `WHO_ICD_RELEASE`       | no              | `2024-01`                                                  | e.g. `2024-01`, `2023-01`, or `2024-01/mms`       |
| `WHO_ICD_BASE_URL`      | no              | `https://id.who.int/icd`                                   | Change only for on-premise mirror                 |
| `WHO_ICD_TOKEN_URL`     | no              | `https://icdaccessmanagement.who.int/connect/token`         | Change only for on-premise mirror                 |
| `WHO_ICD_SCOPE`         | no              | `icdapi_access`                                            | WHO's documented OAuth2 scope                     |
| `WHO_ICD_TIMEOUT`       | no              | `30`                                                       | Seconds; float accepted                           |

There is **no separate sandbox host** for the ICD-11 API. WHO uses one
production host and controls access via the OAuth2 credentials issued to
the registered application. For local development, WHO also publishes a
[Docker image](https://icd.who.int/icdapi/docs2/APIDoc-Version2/) that
serves the same API offline; point `WHO_ICD_BASE_URL` at that container
and skip token exchange by pointing `WHO_ICD_TOKEN_URL` at its own
`/connect/token` mock.

## Licensing

The WHO ICD-11 API is **free of charge**, but requires:

1. Registration at <https://icdaccessmanagement.who.int/> to receive a
   Client ID + Secret.
2. Acceptance of the [WHO ICD Terms of Use](https://icd.who.int/licenses).
3. Attribution — every UI/report surfacing an ICD-11 code must credit
   the source ("© World Health Organization — ICD-11 (Mortality and
   Morbidity Statistics)").

Do NOT commit real Client IDs or Secrets to the repository.

## Usage

```python
from products.cymed.integrations.whoicd import WHOICDClient

icd = WHOICDClient()  # env-configured
hits = icd.search("acute nasopharyngitis")
for h in hits[:5]:
    print(h["theCode"], h["title"])

entity = icd.linearization("CA00")
info = icd.code_info("CA00")
```

Every I/O method also accepts a keyword-only `client=httpx.Client()` for
dependency injection in tests:

```python
import httpx, respx
from products.cymed.integrations.whoicd import WHOICDClient

with respx.mock(base_url="https://id.who.int") as router:
    router.get("/icd/release/11/2024-01/mms/search").respond(
        200, json={"destinationEntities": [{"theCode": "CA00", "title": "Common cold"}]}
    )
    with httpx.Client() as c:
        icd = WHOICDClient(client_id="x", client_secret="y")
        # Prime the token cache so the search call doesn't hit the real IdP:
        # ...or mock POST /connect/token similarly and call icd.search(..., client=c).
```

## Dependencies

Uses `httpx` (already pinned in `requirements.txt` at
`httpx>=0.27.0,<1.0.0`). No new package needed.

## Errors

All failures — missing credentials, network errors, non-2xx responses,
non-JSON bodies — raise :class:`WHOICDError`. There is no silent
fallback; callers that want mock behaviour should catch the exception
and decide what to do at the call site.
