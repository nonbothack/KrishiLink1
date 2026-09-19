# Business data dictionary

| Entity | Meaning | Sensitive notes |
|---|---|---|
| User | Authenticated account and role | Phone/email and security state are private |
| Farmer Profile | Farmer preferences and optional land/crop context | Exact GPS and bank evidence are restricted |
| Buyer Requirement | Buyer demand for a crop/quantity/context | Buyer-private procurement data |
| FPO Member | FPO-managed roster record, not automatically a platform user | Member phone/name are FPO personal data |
| Intake | Member delivery receipt with gross/tare/net and canonical quantity | Immutable/correction history matters |
| Pool | FPO aggregation of persisted contributions | Quantity reconciles to contributions |
| Lot | Marketplace sale unit owned by farmer/FPO | Asking price is not a market observation |
| Offer | Buyer proposal against a lot | Terms and expiry are contractual workflow facts |
| Transaction/Trade | Canonical accepted trade record | Payment may remain unverified |
| TradeEvent | Append-only lifecycle/evidence event | Preserve provenance and actor |
| Grievance | Structured support/dispute case | Raw descriptions/evidence restricted |
| Notification | In-app/outbox event delivered to an authorized user | Payload is privacy-minimized |
| VerificationRecord | Dimension-specific review result | Generic “verified” is not proof |
| AuditLog | Actor/action/entity/request/timestamp evidence | Append-only intent; DB-admin caveat |
