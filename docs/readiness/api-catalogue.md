# API catalogue and integration position

The stable application prefix is `/api/v1`. FastAPI generates schemas in non-production at `/api/v1/openapi.json`; production hides interactive documentation unless the deployment deliberately exposes an approved documentation surface.

| Surface | Classification | Notes |
|---|---|---|
| `/api/v1/health`, public market/crop lookup | PUBLIC | Public facts only; freshness/provenance remain part of responses. |
| `/api/v1/auth/*` | PUBLIC entry points | OTP/password policies and rate limits apply. |
| `/api/v1/users`, farmer/buyer/FPO operations | USER_AUTHENTICATED | Object ownership and role checks server-side. |
| `/api/v1/fpo/export` | USER_AUTHENTICATED (FPO owner) | Bounded owner-scoped JSON manifest or one-domain CSV. |
| `/api/v1/admin/*` | INTERNAL/ADMIN | Not a partner API; least-privilege permissions and step-up apply. |
| provider callback routes | INTERNAL PROVIDER | Never reuse as enterprise partner webhooks. |

Pagination is bounded on major list routes. Idempotency applies to consequential writes where implemented. Error envelopes include safe messages and request IDs. There is no enterprise service-account/OAuth client-credentials contract, SCIM or SAML/OIDC SSO today; those are future integration boundaries. Breaking API changes require a versioned migration/deprecation plan; no `/api/v2` is introduced here.
