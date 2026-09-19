# PostgreSQL backup/restore evidence

**Status: PASS — isolated rehearsal.**

Inside the disposable PostgreSQL 15.8 container:

1. `pg_dump -Fc` created `/tmp/krishilink-15a.dump` from `krishilink`.
2. A clean `krishilink_restore_15a` database was created.
3. `pg_restore --exit-on-error` completed successfully.
4. Public table counts matched: source `63`, restored `63`.
5. The restore database and dump were removed after verification.

This verifies the mechanical custom-format backup/restore path. It does not
establish a production RPO/RTO, encrypted off-host retention, or a populated
business-data recovery rehearsal.
