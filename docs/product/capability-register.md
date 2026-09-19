# KrishiLink v4 capability register — baseline snapshot

This initial register points to Packet 00's evidence matrix. Owners and product metrics are not assigned in the repository and remain decisions before feature packets.

| Capability | Master problem/persona | Tier | Owner | Dependencies | Metric / launch gate | Current status | Evidence |
|---|---|---|---|---|---|---|---|
| Auth/session/roles | All personas; safe identity and access | Core | Unassigned | Redis, email/SMS OTP partner if passwordless chosen | Auth journey plus object-level 401/403/IDOR tests | PARTIAL / SECURITY BLOCKER | `00-capability-matrix.md`, `00-security-provider-inventory.md` |
| Structured location/outlets | Farmer; nearby substantiated market | Core | Unassigned | Authoritative geography/outlet registry, geocoder | No fabricated coordinates; provenance/coverage gate | BROKEN | Same |
| Official reported prices | Farmer/buyer/FPO; make informed market decision | Core | Unassigned | data.gov.in credential, source SLA | Source/date/market/crop/unit displayed; stale/outage tests | PARTIAL / EXTERNAL DEPENDENCY | Same |
| Farmer dashboard/listing | Farmer; low-effort selling | Core | Unassigned | Auth, crop registry, location, price | 360 px task usability, successful server listing | PARTIAL | Same |
| Buyer discovery/offers | Buyers and farmers; discover and negotiate | Core | Unassigned | Verified buyer profiles and real requirements | No synthetic buyer metrics; offer FSM tests | SECURITY BLOCKER | Same |
| Trade Room/settlement tracking | Farmer/buyer; transparent fulfilment | Core | Unassigned | Agreed terms, payment provider/manual process | Terms must originate from agreement; full transition tests | SECURITY BLOCKER / EXTERNAL DEPENDENCY | Same |
| FPO aggregation | FPO; member pooling and allocation | Core | Unassigned | Member consent/identity, payout allocation | Member ownership, reconciliation and workflow tests | PARTIAL | Same |
| Disputes/support | All transaction roles; preserve remedy path | Core | Unassigned | Operations owner and retention/legal policy | Valid state transitions, owner scoping, evidence scan | PARTIAL | Same |
| Notifications | Core transaction users | Core | Unassigned | Redis/Celery, configured messaging provider | Event delivery retry/dead-letter and no duplicate sends | PARTIAL / EXTERNAL DEPENDENCY | Same |
| Storage booking | Farmer/FPO | Expansion | Unassigned | Verified facilities, booking terms | Facility provenance and reservation FSM | PARTIAL | Same |
| Logistics/quality | Parties in trade | Expansion | Unassigned | Providers, sampling/assay process | Verified service and evidence lifecycle | MISSING | Same |
| Admin/support operations | Operators | Core | Unassigned | Least-privilege policy and runbooks | Audited review/triage flows | PARTIAL / SECURITY BLOCKER | Same |
| i18n/accessibility/low bandwidth | Farmer and shared-device users | Core | Unassigned | Reviewed agricultural glossary, field testing | Three-language critical flow, WCAG/manual checks | PARTIAL | Same |
| Payments, WhatsApp, IVR, regulated verification | Marketplace participants | Partner-dependent | Unassigned | Licensed provider/approvals/legal review | No mock success in production | EXTERNAL DEPENDENCY | Same |
| Government/enterprise profile | Institution/regulator | Government-enterprise | Unassigned | Contract, hosting, GIGW/STQC/security evidence | Contract-specific certification and DR gate | MISSING | Same |
