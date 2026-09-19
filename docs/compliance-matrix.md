# KrishiLink privacy and identity compliance matrix

**Status:** Engineering review aid, not legal advice. The policy pages shipped in this packet are drafts and are not approved for production use. The matrix describes current code behavior and unresolved work; it does not claim statutory compliance.

## Commencement facts to verify with counsel

The Digital Personal Data Protection Act, 2023 and Digital Personal Data Protection Rules, 2025 have staged commencement. The Central Government's 13 November 2025 notifications set different commencement dates for different provisions. The Act notice brings specified provisions into force on publication, other specified provisions after one year (13 November 2026), and the remaining scheduled provisions after eighteen months (13 May 2027). The Rules notice brings Rules 1, 2 and 17–21 into force on publication, Rule 4 after one year, and Rules 3, 5–16, 22 and 23 after eighteen months. This packet does not infer which obligations apply to a particular KrishiLink deployment from those groups; counsel must map the gazetted schedules to the planned launch date, service role and processing.

Sources: [DPDP Act commencement notification, G.S.R. 843(E)](https://egazette.gov.in/WriteReadData/2025/267647.pdf) · [DPDP Rules commencement notification, G.S.R. 846(E)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf).

## Current controls and decisions

| Area | Verified implementation in this packet | Status and remaining work |
|---|---|---|
| Identity fields | Name and Indian mobile are used for OTP onboarding; email, password, organization and crop preferences are optional by role. New coordinates require explicit consent. | Partial. Reconcile the full field inventory across legacy workflows before launch. |
| Purpose and notice | Versioned Terms and Privacy Notice pages exist in English, Hindi and Marathi and identify themselves as drafts. | Security/production blocker. Organization identity, lawful purposes, sharing, processors, retention, contact and complete terms need counsel and organization approval. Production registration fails closed while both documents are draft. |
| Phone identity | Indian numbers normalize to a unique E.164 identity key. Unambiguous legacy values are backfilled; collisions are preserved and flagged for review. | Partial. Resolve flagged account conflicts through a documented human process; do not merge automatically. |
| OTP authentication | Codes are short-lived, one-use, three-attempt, HMAC-hashed and never written to audit or outbox. OTP challenge storage uses a keyed phone digest rather than the phone itself. Production delivery and abuse limiting fail closed when SMS or Redis is unavailable. | External dependency. Configure and verify an approved SMS route, delivery policy and production Redis. Set and operate a challenge-record retention schedule. |
| Account security | Refresh tokens rotate against a persisted digest; reuse revokes the session family. Browser cookie refresh/logout use strict SameSite cookies, production Secure flags, Origin checks and a CSRF cookie/header. Password reset grants are one-use and stored by digest. | Partial. Staff/admin MFA, session-device management, password-recovery delivery, key rotation and operational incident procedures remain open. |
| Verification | Phone, email, business, GST, bank, identity and organization dimensions are independent records. Legacy `is_verified` is not treated as evidence. Unconfigured adapters return `UNAVAILABLE`. | External dependency. No provider-backed business/GST/bank verification is active; no production claim of verification is supported. |
| Marketing | Separate opt-in record; default off; withdrawal adds a timestamp without erasing acceptance history. | Partial. Confirm messaging systems honor the current state before any marketing use. |
| Location | GPS is requested after user action, recorded as explicit GPS, never used to infer administrative geography, and can be removed. Acceptance and withdrawal are recorded in consent history. Profile responses do not expose coordinates. | Partial. Validate purpose, access controls, retention, backup deletion and downstream copies with counsel and operations. |
| Privacy requests | Authenticated, owner-scoped access/correction/erasure request intake is available and audited. | Partial. Intake does not export, correct or erase data. A staffed workflow, identity check, deadlines, exceptions and completion evidence are required before claiming fulfillment. |
| Children and representatives | No age gate, guardian flow or representative authority process was introduced. | Security/production blocker until the organization and counsel decide applicability and implement the required product path. |
| Retention and deletion | Password-reset tokens are not placed in outbox payloads; location can be cleared; privacy requests are retained as records. | Missing policy. Define data-specific retention, backups, legal holds, account closure and deletion jobs. |
| Audit and observability | OTP audit rows contain outcome categories and challenge IDs, not codes or phone values. Consent records retain user, policy version, source, timestamps and bounded user-agent; raw consent IP is not stored. | Partial. Confirm retention/access controls for audit and user-agent data; ensure other log sinks redact authentication and transaction data. |
| Production activation | Development may expose an OTP only when its explicit setting is enabled. | Security/production blocker until legal pages, provider configurations, Redis and database migrations are approved and verified in production-like infrastructure. |

## Required decisions before production

1. Have Indian privacy and e-commerce counsel map the staged Act/Rules schedule to KrishiLink's exact launch date, data-fiduciary/processor roles, user groups and actual data flows.
2. Confirm the legal entity, contact and grievance channels, user-rights handling, children/guardian approach, consent language and each purpose/retention period.
3. Approve the Terms and Privacy Notice versions, then set effective dates through an audited release process. Do not remove the production registration guard before that review.
4. Select SMS/email and business/bank verification providers, review contracts and transfers, and validate the providers' production failure behavior.
5. Establish deletion/retention jobs and operational owners for OTP challenges, reset grants, logs, backups, privacy requests and closed accounts.
6. Require stronger authentication and recovery controls for privileged staff accounts and define account-conflict resolution for duplicate legacy phones.
