# AGENTS — KrishiLink 4.0

## Master Engineering & Codex Execution Reference

> **AUTHORITATIVE REPOSITORY INSTRUCTIONS**
>
> This file defines how AI coding agents must work inside KrishiLink.
>
> Read this file before modifying any code.

---

# 1. CRITICAL REOPENING INSTRUCTIONS

Whenever starting, resuming, or continuing work on KrishiLink:

1. Read this `AGENTS.md` completely.
2. Read `PROGRESS_TRACKER.md`.
3. Read `docs/PRODUCTION_ENGINEERING_SPEC.md` if it still exists and contains relevant historical engineering context.
4. Read:

   * `docs/krishilink-v4/MASTER_SPEC.md`
5. If a work packet has been assigned, read that packet completely from:

   * `docs/krishilink-v4/work-packets/`
6. Inspect the actual repository before assuming documentation is correct.
7. Search for existing implementations before creating replacements.

Repository code is evidence of the current implementation.

`MASTER_SPEC.md` defines the intended product direction.

The assigned work packet defines the current implementation scope.

---

# 2. SOURCE-OF-TRUTH PRIORITY

If instructions conflict, use this priority:

1. User's latest explicit instruction
2. Current assigned work packet
3. This `AGENTS.md`
4. `docs/krishilink-v4/MASTER_SPEC.md`
5. Approved architecture decisions / ADRs
6. `PROGRESS_TRACKER.md`
7. Existing implementation
8. Older READMEs/comments/documentation

Never silently resolve a serious contradiction.

If a contradiction affects architecture, data integrity, security, money, authorization, or destructive migrations:

* document it;
* stop that affected portion;
* continue only with unaffected work;
* report the conflict clearly.

---

# 3. GIT AND BRANCH RULES — CRITICAL

## Working branch

All development work must target:

```text
abdulrehman
```

Never intentionally modify or push directly to:

```text
main
master
```

unless the user explicitly instructs otherwise.

Before making changes, verify:

```bash
git branch --show-current
git status
```

Expected branch:

```text
abdulrehman
```

If another branch is checked out, switch to `abdulrehman` before implementation unless the user explicitly instructed otherwise.

---

## NO AUTOMATIC COMMITS OR PUSHES

### Never automatically:

* run `git commit`;
* run `git push`;
* create a pull request;
* merge branches;
* rebase remote branches;
* force-push;
* tag a release;
* publish a deployment.

Do NOT commit or push merely because a task is finished.

Leave completed changes in the working tree for user review.

Only commit when the user explicitly says something equivalent to:

```text
commit these changes
```

Only push when the user explicitly says something equivalent to:

```text
push this
push to GitHub
push to abdulrehman
```

When the user explicitly asks for a push, push only to:

```text
origin/abdulrehman
```

unless they explicitly name another branch.

Example:

```bash
git push origin abdulrehman
```

Never infer permission to push from:

* previous tasks;
* an old `PROGRESS_TRACKER`;
* an old AGENTS instruction;
* successful tests;
* a completed work packet;
* a request to "finish", "implement", or "fix" something.

**Push permission must be explicit in the current user instruction.**

---

# 4. DO NOT BLINDLY REWRITE THE APPLICATION

Preserve the current architecture unless the assigned packet explicitly requires a justified change.

Current architecture:

## Backend

```text
backend/app/
```

FastAPI application using:

```text
app.main
app/core/
app/modules/<domain>/
```

Typical module structure:

```text
models.py
schemas.py
repository.py
service.py
router.py
```

Where a repository layer is not yet present, follow the existing module architecture rather than introducing arbitrary patterns.

---

## Frontend

```text
frontend/
```

React + Vite.

Do not migrate frameworks merely because another framework looks preferable.

Framework migration requires:

* explicit architectural justification;
* measured benefit;
* migration plan;
* user approval if it creates broad repository changes.

---

## Database

Primary production database:

```text
PostgreSQL + PostGIS
```

Spatial coordinates use:

```text
GEOGRAPHY(POINT, 4326)
```

SQLite compatibility may exist for automated tests.

Do not destroy test compatibility unnecessarily.

---

## Legacy backend

Ignore legacy Flask implementation unless explicitly required for migration/reference:

```text
backend/routes/
backend/services/
flask_app_legacy.py
```

Do not resurrect legacy Flask architecture.

---

# 5. KRISHILINK 4.0 MASTER SPECIFICATION

Authoritative product specification:

```text
docs/krishilink-v4/MASTER_SPEC.md
```

Implementation packets:

```text
docs/krishilink-v4/work-packets/
```

Do NOT attempt to implement the entire master specification in one task.

Work packet boundaries exist specifically to prevent:

* context drift;
* unnecessary rewrites;
* agent loops;
* massive unreviewable diffs;
* regressions;
* half-implemented features.

When assigned one work packet:

> Execute that packet only.

Do not automatically begin the next packet.

---

# 6. WORK-PACKET EXECUTION PROTOCOL

Before implementing a packet:

1. Read this file.
2. Read `PROGRESS_TRACKER.md`.
3. Read the assigned packet completely.
4. Read only relevant linked sections of `MASTER_SPEC.md`.
5. Inspect the current code.
6. Search for existing implementations.
7. Identify dependencies.
8. Identify regressions/risks.
9. Form an implementation plan.
10. Implement only the packet scope.

At packet completion, return exactly one status:

```text
PASS
PASS_WITH_EXTERNAL_DEPENDENCY
BLOCKED
FAIL
```

Then report:

1. Summary
2. What changed
3. Files changed
4. Database migrations
5. Tests executed
6. Test results
7. Security impact
8. Accessibility impact
9. Performance impact
10. Remaining technical debt
11. External dependencies
12. Risks
13. Recommended next packet

Then STOP.

Do not begin the next packet.

---

# 7. CORE PRODUCT LAWS

## LAW 1 — Minimum Input, Maximum Output

A farmer must never type information the system can reliably determine.

Prefer:

* location from GPS/profile;
* crop from history/profile;
* nearby markets from coordinates;
* price from official reported data;
* unit defaults;
* remembered preferences;
* prefilled transaction context.

Returning-farmer target:

```text
List a lot in approximately 3 taps and 0 typed characters
```

where technically and safely feasible.

---

## LAW 2 — Nothing Without Purpose

Every visible element must either:

1. answer a user question; or
2. move the user toward a useful action.

Avoid decorative complexity.

Every:

* button must work;
* link must resolve;
* filter must filter;
* tab must have purpose;
* card must provide useful information;
* action must produce truthful feedback.

---

## LAW 3 — Progressive Disclosure

Do not overwhelm farmers.

The first viewport should prioritize:

1. what their crop is worth;
2. nearest/best relevant market opportunity;
3. urgent action;
4. recommended next action.

Advanced analytics should appear progressively.

Farmer screens should be simpler than buyer/FPO/admin screens.

---

# 8. USER EXPERIENCE TARGET

Design farmer experiences assuming:

```text
Device: low/mid-range Android
Viewport: start testing at 360 × 640
Connectivity: intermittent mobile data
Digital literacy: potentially low
Language: English / Hindi / Marathi
Email availability: not guaranteed
GPS permission: not guaranteed
Phone ownership: possibly shared
```

Every critical farmer workflow must remain usable if:

* GPS is denied;
* network quality is poor;
* data is stale;
* the farmer has no email;
* the farmer prefers Hindi/Marathi;
* the user makes mistakes.

Never hide critical information behind sophisticated UI patterns.

---

# 9. PRODUCT TRUTH RULE

Never present synthetic or unverifiable information as production truth.

Production UI must never fabricate:

* mandi prices;
* transactions;
* buyers;
* FPOs;
* certifications;
* verification states;
* UTR/RRN/payment IDs;
* market locations;
* trust scores;
* user counts;
* statistics;
* government endorsements;
* demand levels;
* arrival volumes;
* forecast accuracy.

Synthetic data is permitted for:

* unit tests;
* integration tests;
* E2E tests;
* local development;
* explicitly isolated demo environments.

Synthetic/demo data must be clearly separated from production.

A demo environment must visibly indicate:

```text
DEMO — synthetic data
```

where applicable.

Synthetic data must never silently enter production databases.

---

# 10. MARKET PRICE TERMINOLOGY

Do not describe daily government mandi observations as real-time/live unless the upstream source is genuinely real-time.

Prefer:

```text
Latest official price
Reported today
Latest reported mandi rate
```

Every displayed market price should preserve:

* source;
* `price_date`;
* market/outlet;
* crop/commodity;
* variety/grade when available;
* unit;
* fetched timestamp internally.

Do not replace unavailable official data with fabricated sample prices.

If upstream data is unavailable:

* show the latest genuine observation;
* show its actual date;
* indicate stale status where appropriate.

---

# 11. LOCATION AND OUTLET TRUTH

Never assume every map result is a valid agricultural selling point.

Outlet data must preserve provenance.

Examples of sources may include:

* AGMARKNET/data.gov.in;
* APMC datasets;
* eNAM;
* LGD;
* WDRA;
* state agriculture departments;
* verified partners;
* manually reviewed locations;
* OpenStreetMap-derived candidates.

OpenStreetMap candidates must not automatically become trusted selling outlets.

Generic OSM entities such as:

```text
building=warehouse
landuse=farmyard
amenity=marketplace
```

are candidates, not proof that a farmer can sell produce there.

Use:

* provenance;
* verification status;
* confidence;
* review queues;
* deduplication.

Approximate locations must be labelled as approximate.

---

# 12. FRONTEND RULES

Frontend must:

* use real backend APIs;
* show truthful loading/error/empty/stale states;
* never silently switch to `demoData`;
* maintain responsive behaviour;
* maintain keyboard accessibility;
* support English/Hindi/Marathi;
* avoid duplicated domain logic;
* avoid financial calculations that disagree with backend authority.

Async surfaces should support appropriate states:

```text
loading
success
empty
error
stale
offline
```

as applicable.

---

# 13. BACKEND RULES

FastAPI backend remains authoritative for:

* authentication;
* authorization;
* role checks;
* prices/data normalization;
* money calculations;
* unit normalization;
* verification;
* trade state;
* offer state;
* settlement state;
* trust computation;
* audit records;
* sensitive business rules.

Never rely on frontend role restrictions for security.

---

# 14. SERVICE / DOMAIN RULES

No substantial business logic in route handlers.

Preferred flow:

```text
Router
  ↓
Service
  ↓
Repository / persistence abstraction
  ↓
Database
```

Where existing code uses a slightly different established pattern, preserve consistency unless the work packet specifically changes it.

Critical domains must expose controlled state transitions.

Examples:

```text
Lot
Offer
Trade
Payment
Verification
Storage Booking
Grievance
```

Do not modify state arbitrarily from random routes/components.

---

# 15. DATABASE RULES

Schema changes use:

```text
Alembic
```

Never manual production DDL.

For financial data:

```text
NUMERIC / Decimal
```

Never binary floating point.

Critical quantity/price calculations must use canonical units.

Spatial queries should use PostGIS where available.

Every mutation requiring accountability should create appropriate audit history.

Migrations must:

* be reversible where reasonable;
* preserve production data;
* avoid destructive transformations without explicit justification;
* be tested against realistic existing schemas.

---

# 16. AUTHORIZATION AND SECURITY

Enforce authorization server-side.

Threat model includes:

* account takeover;
* OTP abuse;
* duplicate accounts;
* fake buyers;
* fake verification;
* IDOR/BOLA;
* forged payment evidence;
* GPS spoofing;
* offer spam;
* collusion;
* quality manipulation;
* trust-score gaming;
* webhook replay;
* malicious file uploads;
* scraping;
* support/admin abuse;
* denial-of-service.

Never expose:

* API keys;
* database credentials;
* provider secrets;
* JWT signing secrets;
* payment secrets;
* SMS tokens;
* WhatsApp tokens.

Frontend environment variables are public if bundled.

Sensitive provider credentials remain server-side.

---

# 17. EXTERNAL PROVIDER ARCHITECTURE

External integrations should use provider abstractions where practical.

Examples:

```text
PaymentProvider
MessagingProvider
BusinessVerificationProvider
BankVerificationProvider
GeocodingProvider
WeatherProvider
VoiceProvider
FinanceProvider
```

Production must never silently use a mock provider.

If credentials/provider approval are unavailable:

* implement the interface;
* implement truthful pending/manual fallback where appropriate;
* mark the packet `PASS_WITH_EXTERNAL_DEPENDENCY`.

Never fabricate provider success.

---

# 18. FINANCE AND REGULATED FEATURES

Do not assume KrishiLink itself can legally:

* hold funds;
* provide loans;
* provide credit;
* offer escrow;
* perform regulated verification.

Use licensed/regulated partners where required.

If an external regulated dependency is missing:

* do not fake it;
* expose the correct integration boundary;
* document the dependency;
* keep core functionality usable where possible.

---

# 19. ML / PRICE FORECASTING RULES

A forecast must never be shipped merely because a model can generate numbers.

Before prescriptive recommendations such as:

```text
Hold for 9 days
```

the system must support evidence including:

* documented training data;
* lineage;
* time-based split;
* leakage prevention;
* walk-forward validation;
* naive baseline;
* seasonal baseline;
* per-crop evaluation;
* geographic evaluation;
* confidence/interval calibration;
* minimum sample thresholds;
* drift monitoring;
* model versioning;
* abstention rules;
* reproducibility.

If the model cannot reliably outperform the declared baseline:

> show trends/data but do not issue prescriptive sale advice.

Never present forecasts as guarantees.

---

# 20. MARKETPLACE TRUST

Verification dimensions must remain separate.

Do not collapse everything into:

```text
Verified
```

Prefer explicit states:

```text
Phone verified
Business verified
GST verified
Bank verified
Identity verified
```

Trust metrics should be derived from actual platform activity.

Examples:

* completed trades;
* payment timeliness;
* median days to payment;
* dispute rate;
* rejection rate;
* transaction sample size.

Trust scoring must account for sample size.

One transaction at 100% success must not automatically outrank hundreds of trades at slightly lower performance.

---

# 21. TEST REQUIREMENTS

Known historical baseline included:

```text
73 passed
0 failed
0 skipped
```

Do not treat this count as permanently authoritative.

Packet 00 must verify the current baseline.

Primary backend test command:

```bash
python -m pytest -v
```

Additional checks:

```bash
python -m ruff check app
```

Frontend:

```bash
npm run lint
npm run build
```

Run more targeted tests when relevant.

Never claim completion if relevant tests were not run.

Report skipped tests and why.

---

# 22. TESTING EXPECTATIONS

Testing should include appropriate coverage for:

## Unit

* domain rules;
* calculations;
* unit conversion;
* authorization helpers;
* validators;
* utility functions.

## Integration

* API/database interaction;
* auth flows;
* provider boundaries;
* migrations.

## E2E

Critical journeys:

```text
Farmer
Buyer
FPO
Admin/support
```

Important concurrency/race cases include:

* offer accepted while expiring;
* offer withdrawn during acceptance;
* repeated webhook delivery;
* duplicated write request;
* session expiry during transaction;
* two-device updates;
* offline sync;
* migration/rollback behavior.

---

# 23. ACCESSIBILITY

Target:

```text
WCAG 2.2 AA
```

Requirements include:

* keyboard navigation;
* visible focus;
* meaningful labels;
* sufficient contrast;
* screen-reader semantics;
* reduced motion;
* minimum practical tap targets;
* accessible charts/tables;
* correct focus management;
* usable font scaling.

Use existing axe/Playwright coverage and expand rather than replacing it.

---

# 24. INTERNATIONALIZATION

Initial supported languages:

```text
English
Hindi
Marathi
```

User-facing text should use translation infrastructure.

Avoid hardcoded JSX strings where translation is expected.

Translate:

* forms;
* errors;
* notifications;
* empty states;
* transaction statuses;
* SMS/WhatsApp templates;
* help content;
* accessibility labels.

Never silently display misleading machine translations in production without review for critical agricultural/financial terminology.

---

# 25. PERFORMANCE

Preserve and improve performance deliberately.

Avoid:

* giant initial JS bundles;
* eagerly loading maps/charts;
* unnecessary animation libraries;
* massive unoptimized image sequences;
* rendering thousands of map markers directly;
* excessive API waterfalls.

Use:

* route splitting;
* lazy loading;
* server caching;
* spatial indexes;
* pagination;
* clustering;
* responsive images;
* request deduplication.

Farmer-facing performance on poor mobile connections matters more than decorative complexity.

---

# 26. RELIABILITY / EVENT PROCESSING

Persistent notifications and asynchronous side effects should use reliable patterns.

Where transactional outbox already exists, preserve it.

Critical pattern:

```text
Domain transaction
+
Outbox event
=
same DB transaction
```

Workers must be:

* idempotent;
* retry-safe;
* observable;
* bounded by controlled backoff.

Repeated failures should surface for manual investigation.

---

# 27. OBSERVABILITY

Production systems should expose:

* structured logs;
* request IDs;
* health endpoints;
* price sync health;
* worker health;
* provider health;
* error monitoring;
* performance metrics.

Never display:

```text
Our team has been notified
```

unless an actual monitoring/error-reporting mechanism exists.

---

# 28. ADMIN AND SUPPORT SAFETY

Admin/support interfaces must follow least privilege.

Avoid requiring support staff to:

* edit database rows manually;
* run direct SQL;
* impersonate users invisibly;
* alter transaction history.

Sensitive admin actions require:

* authorization;
* audit logs;
* actor identity;
* reason where appropriate.

---

# 29. DATA PRIVACY

Follow the current applicable Indian privacy/legal requirements defined in the master specification and maintained compliance matrix.

Privacy engineering should support:

* purpose limitation;
* consent records;
* withdrawal;
* access/correction/erasure workflows where applicable;
* retention policies;
* security;
* auditability;
* data export;
* data deletion processes.

Legal text must not be invented by an AI and treated as final legal approval.

Mark legal review dependencies honestly.

---

# 30. GOVERNMENT / ENTERPRISE READINESS

When working on government/institutional scope, consider:

* GIGW requirements;
* accessibility evidence;
* security audit readiness;
* CERT-In-related requirements;
* STQC readiness where applicable;
* DR/BCP;
* API documentation;
* procurement documentation;
* interoperability;
* data portability;
* vendor exit;
* audit trails;
* SLA evidence.

Do not claim certification until actual certification has occurred.

---

# 31. COMMANDS

## Full stack

```bash
docker compose up --build
```

Known development mappings may include:

```text
PostgreSQL: 5435
Redis:      6380
Backend:    8001
Frontend:   5173
```

Verify actual compose configuration rather than blindly relying on historical values.

---

## Backend migrations

From:

```text
backend/
```

run:

```bash
alembic upgrade head
```

---

## Backend development

From:

```text
backend/
```

run:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

---

## Frontend development

From:

```text
frontend/
```

run:

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## Verification

Backend:

```bash
python -m pytest -v
python -m ruff check app
```

Frontend:

```bash
npm run lint
npm run build
```

Run additional packet-specific tests where required.

---

# 32. CURRENT KNOWN ENGINEERING BASELINE

Historical baseline from the previous engineering phase:

```text
Auth
RBAC
Rate limiting
Idempotency
PostGIS
Matching N+1 improvements
Negotiations
Trade / escrow state-machine work
S3 evidence IDOR protection
Truthful market-price trends
Transactional outbox locking
CI hardening
```

Historical test result:

```text
73 passed
0 failed
0 skipped
```

These are **last-known claims**, not permanent truth.

Packet 00 must independently verify them.

Do not assume they still hold after repository changes.

---

# 33. EXISTING CAPABILITY FIRST

Before implementing a replacement:

Search for an existing implementation.

This is especially important for:

```text
authentication
RBAC
market prices
PostGIS proximity
matching
offers
negotiations
trades / Trade Room
storage
reservations
notifications
disputes
idempotency
outbox processing
```

Prefer:

```text
inspect → understand → test → extend
```

over:

```text
ignore → rewrite
```

---

# 34. DO NOT BLINDLY RECOVER MAIN

Older branches may contain useful:

* UI components;
* layouts;
* visual ideas;
* map implementations;
* flows.

But do not wholesale merge old branches merely to recover UI.

Old branches may contain bugs already fixed in `abdulrehman`.

Recover functionality selectively and verify it against current architecture.

---

# 35. SAFE CHANGE DISCIPLINE

Keep diffs focused.

Do not perform unrelated refactors during scoped tasks.

Do not:

* rename hundreds of files without need;
* switch libraries casually;
* rewrite working modules;
* change architecture for stylistic reasons;
* delete working code because it is currently unreachable.

If unreachable functionality is valuable, reconnect it.

---

# 36. COMPLETION IS EVIDENCE-BASED

Do not report:

```text
Implemented successfully
```

without evidence.

Completion reports should connect requirements to verification.

Example:

```text
Requirement:
Farmer cannot access buyer-only dashboard.

Evidence:
Authorization integration test.

Result:
PASS
```

For important claims include:

* test name;
* command;
* result;
* relevant file/module.

---

# 37. UI VERIFICATION

For substantial UI work, verify at minimum:

```text
360 × 640
390 × 844
768 × 1024
1440 × 900
```

Where the environment permits, inspect screenshots.

Verify:

```text
English
Hindi
Marathi
```

Farmer UI must be checked particularly carefully at mobile sizes.

---

# 38. EXTERNAL DEPENDENCIES

Examples:

* real GST verification;
* penny-drop bank verification;
* WhatsApp Business approval;
* payment provider;
* IVR;
* regulated finance;
* external assay;
* logistics partner;
* government certification.

Do not block unrelated core functionality unnecessarily.

Use:

```text
PASS_WITH_EXTERNAL_DEPENDENCY
```

when implementation is complete but activation requires an external organisation/provider.

---

# 39. PROGRESS TRACKER

After meaningful implementation, update:

```text
PROGRESS_TRACKER.md
```

with:

* completed work;
* verified tests;
* unresolved issues;
* next recommended step.

Do not falsely mark externally dependent tasks complete.

---

# 40. FINAL AGENT BEHAVIOUR

For every task:

```text
READ
↓
INSPECT
↓
UNDERSTAND
↓
PLAN
↓
IMPLEMENT SMALL
↓
TEST
↓
REVIEW DIFF
↓
REPORT
↓
STOP
```

Never:

```text
guess
rewrite everything
fake data
hide failing tests
silently change architecture
continue into another packet
commit automatically
push automatically
```

---

# 41. GIT FINAL RULE

Normal task completion ends with:

```text
working tree containing reviewed changes
+
test report
+
NO COMMIT
+
NO PUSH
```

Only when the user explicitly requests a commit:

```text
commit to the currently checked-out abdulrehman branch
```

Only when the user explicitly requests a GitHub push:

```text
push origin abdulrehman
```

Never push to `main` unless the user explicitly overrides this rule.

---

# 42. FINAL PRINCIPLE

KrishiLink is not successful because it has the most features.

It is successful if it gives farmers, buyers and FPOs:

* more trustworthy information;
* less effort;
* better decisions;
* transparent transactions;
* reliable counterparties;
* lower transaction friction;
* complete records;
* confidence that the system tells the truth.

Engineering decisions must serve those outcomes.
