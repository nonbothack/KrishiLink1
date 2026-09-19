# Institutional deployment acceptance checklist

- [ ] approved domain, TLS, CORS and support contacts
- [ ] PostgreSQL/PostGIS, migrations and connection settings rehearsed
- [ ] Redis auth/TLS/persistence decision and Celery/beat health verified
- [ ] private object storage, encryption, lifecycle and malware-scanning decision verified
- [ ] provider credentials/contracts and failure behavior approved
- [ ] Terms/privacy/legal/grievance content approved for the deployment
- [ ] staff MFA/SSO decision made; least-privilege roles tested
- [ ] encrypted backups, checksum, restore rehearsal and RPO/RTO evidence recorded
- [ ] monitoring, alerts, incident contacts and runbooks handed over
- [ ] VAPT/security review and manual accessibility review completed or risk-accepted
- [ ] farmer/buyer/FPO/operator UAT signed by the deployment owner
- [ ] data migration/export and rollback record complete

Completion of this checklist is a deployment gate, not a Packet 14 go-live approval.
