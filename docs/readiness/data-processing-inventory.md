# Data-processing inventory

This inventory is an engineering aid. It does not decide legal basis, fiduciary/processor roles or statutory retention.

| Data class | Purpose/source | Access | Retention/deletion status | Export |
|---|---|---|---|---|
| Phone/email/name/profile | Account and communication; user | Account owner, scoped staff | Policy decision required; account closure workflow needed | Owner export subject to review |
| Location/exact GPS | Explicit nearby-market action; user consent | Owner and bounded domain services | Clear endpoint exists; backups/downstream retention unresolved | Omit exact GPS from institutional export |
| Verification/identity/bank evidence | Review and transaction safety; user/provider | Assigned reviewer only | Legal hold/retention decision required | Excluded by default |
| FPO member records/intakes/pools | Institution operations; FPO owner | FPO owner-scoped | Proposed schedule requires approval | Included in FPO export |
| Lots/offers/trades/allocations | Marketplace/trade record | Parties and scoped staff | Financial/audit preservation dependency | Included when owner-scoped |
| Grievances/evidence | Support/dispute handling; user | Parties/scoped staff | Case/hold decision required | Case export only after authorization |
| Payment references | Participant report/provider evidence | Trade participants/scoped staff | Provider/legal policy required | No secrets; provenance retained |
| Push subscriptions | Explicit notification opt-in; browser | Owner/notification worker | Revoke on unsubscribe; schedule needed | Excluded |
| Audit logs/fraud/support notes | Accountability and operations | Least-privilege staff | Policy/backup/legal hold decision | Bounded safe metadata only |

Optional fields must remain optional. Do not invent legal basis or promise automatic erasure from immutable backups.
