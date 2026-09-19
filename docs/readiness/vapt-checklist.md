# Pre-VAPT checklist

Before an external test, create a staging deployment with non-production accounts and data. Provide the route/API inventory, role matrix, test credentials through a secure channel, seeded objects for farmer/buyer/FPO/admin/support, and a reset procedure. Never give testers provider secrets, production tokens or real personal data.

Record scope, excluded provider endpoints, abuse/rate-limit limits, evidence retention, severity definitions, remediation owner, retest date and risk acceptance authority. Unit, integration and Playwright tests support the assessment; they do not replace it.
