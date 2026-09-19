# KrishiLink government and enterprise readiness pack

**Assessment posture:** engineering readiness evidence for review. This pack is not a certification, legal opinion, signed SLA, VAPT report, or production go-live approval.

## How to read the status

- `IMPLEMENTED_AND_TESTED` — code and a local automated check exist.
- `IMPLEMENTED_NOT_EXTERNALLY_VERIFIED` — code exists, but the required deployment/provider/manual evidence was unavailable here.
- `PARTIAL` — a bounded capability exists with material gaps.
- `DOCUMENTED_ONLY` — the procedure or target is described, not measured.
- `EXTERNAL_DEPENDENCY` — an external provider, infrastructure, legal decision or assessor is required.
- `NOT_IMPLEMENTED` — no production capability exists.

The words **prepared for assessment** are intentional. KrishiLink does not claim GIGW, STQC, CERT-In, DPDP, ISO, SOC 2 or any other certification.

## Evidence index

| Review area | Artifact |
|---|---|
| Government controls and wording | [government-readiness-matrix.md](government-readiness-matrix.md) |
| Accessibility/GIGW evidence | [accessibility-matrix.md](accessibility-matrix.md) |
| Application security | [application-security-matrix.md](application-security-matrix.md) |
| VAPT preparation | [vapt-checklist.md](vapt-checklist.md) |
| Incident operations | [incident-process.md](incident-process.md) |
| Personal-data inventory | [data-processing-inventory.md](data-processing-inventory.md) |
| Deployment and tenancy | [deployment-architecture.md](deployment-architecture.md) |
| Environment/configuration | [configuration-inventory.md](configuration-inventory.md) |
| APIs and integration | [api-catalogue.md](api-catalogue.md) |
| Export and exit | [exit-and-portability.md](exit-and-portability.md) |
| Business data dictionary | [data-dictionary.md](data-dictionary.md) |
| Backups and restore | [backup-architecture.md](backup-architecture.md), [../runbooks/database-restore.md](../runbooks/database-restore.md) |
| DR, dependencies and SLOs | [dr-bcp.md](dr-bcp.md), [dependency-matrix.md](dependency-matrix.md), [slo-sla.md](slo-sla.md) |
| Capacity and cost assumptions | [capacity-and-cost-model.md](capacity-and-cost-model.md) |
| Procurement questionnaire | [procurement-security-questionnaire.md](procurement-security-questionnaire.md) |
| Provenance and providers | [provider-inventory.md](provider-inventory.md), [provenance-pack.md](provenance-pack.md) |
| Dependency/licence review | [dependency-review.md](dependency-review.md) |
| UAT and handover | [UAT-plan.md](UAT-plan.md), [KT-plan.md](KT-plan.md), [operations-manual.md](operations-manual.md) |
| Release/change readiness | [release-management.md](release-management.md), [deployment-acceptance-checklist.md](deployment-acceptance-checklist.md) |
| Machine-checkable index | [readiness-manifest.json](readiness-manifest.json) |

## Supported deployment position

The current application is a logically scoped modular monolith. It has account and FPO ownership checks, but **no database-level institutional tenancy and no `tenant_id`**. Shared multi-institution SaaS is therefore not supported by this packet. The safe institutional profile is a dedicated deployment with a separate database, secrets, object storage, Redis and environment. A future tenant model requires a separately approved architecture and migration.

## Important external evidence still required

Live PostgreSQL/PostGIS migration and lock rehearsal, Redis/Celery/object-storage verification, backup and restore drill, load testing, VAPT, manual accessibility/TalkBack review, provider contracts, staff MFA/SSO decisions, legal review and any STQC/GIGW assessment remain external or later-packet work.
