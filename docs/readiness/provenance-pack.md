# Data provenance pack

| Dataset/domain | Authority and lineage | Truthful coverage statement |
|---|---|---|
| Crop registry | canonical application registry with aliases/units; Packet 03 decisions | active/tradable rows are governed; no duplicate frontend catalogue |
| Markets/outlets | source identity, license status, coordinate confidence and review state | verified coverage may be small; OSM candidates are not automatically outlets |
| Official prices | persisted reported observations with source, report date, fetch time and parser/version | reported/latest, not real-time or guaranteed sale price |
| Trades | user-created lots/offers and accepted canonical trade events | platform history only; payment/quality provider evidence remains distinct |
| Verification | dimension-specific evidence/provider/manual review records | absent/unconfigured provider is not verified |
| Intelligence | Packet 11 evidence/eligibility/abstention methodology | sparse segments remain unavailable; no synthetic production metrics |

Source licenses, retrieval cadence and parser versions must be preserved with each ingestion configuration. The repository does not approve an unverified APMC file merely because it is present locally.
