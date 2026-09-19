# Government readiness matrix

This is an evidence map, not a conformity certificate. Framework references are pointers for an assessor; the deployment owner must confirm applicability and current guidance.

| Control area | Source/framework | Current evidence | Status | Gap / production action | Owner |
|---|---|---|---|---|---|
| Accessibility target | WCAG 2.2 AA; GIGW 3.0 assessment path | Packet 02 primitives, axe/browser checks, [accessibility matrix](accessibility-matrix.md) | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED | Manual TalkBack, keyboard, zoom and document review; external assessment | Product + accessibility reviewer |
| Public navigation/search/metadata | GIGW readiness topics | Packet 09 public routes, prerender/SEO checks | IMPLEMENTED_AND_TESTED | Verify final domain, broken links and content ownership in UAT | Product |
| Multilingual UI | GIGW language/accessibility expectations | EN/HI/MR catalogue and browser coverage | PARTIAL | Native-speaker and institutional language governance | Product + language reviewers |
| Security headers and sessions | Web security baseline | Nginx/Vercel headers, auth/session tests, threat model | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED | Probe deployed edge and run VAPT | Security |
| Privacy notice/terms | Applicable privacy/e-commerce law | Versioned draft policies, consent records, privacy-request intake | PARTIAL | Counsel approval, retention/legal-basis decisions, fulfillment operations | Legal + privacy owner |
| Auditability | Procurement/security review | AuditLog, request IDs, staff action audit, bounded admin audit route | IMPLEMENTED_AND_TESTED | Confirm retention, access and database-admin controls | Operations |
| Data portability | Open standards/procurement | FPO-owned JSON manifest and bounded CSV export | IMPLEMENTED_AND_TESTED | Validate institution contract and run cross-account export test on PostgreSQL | Engineering |
| Hosting/data residency | Deployment contract | Deployment profile and location checklist | DOCUMENTED_ONLY | Choose region/providers and contractually constrain them | Deployment owner |
| DR/BCP | Procurement/operational assurance | DR plan, restore runbook and targets | DOCUMENTED_ONLY | Live backup/restore and failure drills | SRE |
| Certification | GIGW/STQC/CERT-In/ISO | No certificate or external assessment in repository | NOT_IMPLEMENTED | Engage the required assessor; never infer from tests | Organization |

### Wording rule

Use “prepared for external assessment” and “evidence available.” Do not use “GIGW compliant,” “STQC certified,” “CERT-In compliant,” “DPDP compliant,” “ISO compliant,” or “production ready” as unqualified product claims.
