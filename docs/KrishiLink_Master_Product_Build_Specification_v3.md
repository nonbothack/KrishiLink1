**KRISHILINK 3.0**

**MASTER PRODUCT, BUSINESS, UX, ENGINEERING & BUILD SPECIFICATION**

From price discovery and demand matching to verified trade execution, fulfillment, settlement, trust, analytics, and government-ready reporting

> **Purpose:** This document is designed to survive context-window limits. It is both a product strategy document and a master implementation prompt for an AI coding agent working inside the existing KrishiLink repository.
>
> **Evidence policy:** Repository-specific facts in this document are based on direct inspection of the supplied KrishiLink1-main archive. External market claims are based on official or first-party sources checked on 1 September 2026. Proposed features are explicitly labelled as proposed; they are not described as existing capabilities.
>
> **Important constraint:** Do not interpret the phrase “better than competitors” as “copy every feature.” KrishiLink must be better at a narrow, valuable job: turning buyer demand and fragmented agricultural supply into transparent, executable, traceable trades without pretending to own infrastructure it does not own.

# Document map

- 1\. Non-negotiable product thesis and definition of done

- 2\. Verified audit of the supplied repository

- 3\. Neutral competitive landscape and lessons worth copying

- 4\. User problems, jobs-to-be-done, and target market

- 5\. Product operating model: demand -\> supply -\> trade -\> fulfillment -\> settlement

- 6\. Complete role architecture for farmer, buyer, FPO, transporter, QC partner, operator, admin, and future government users

- 7\. End-to-end workflows and state machines

- 8\. Detailed screen-by-screen UX and information architecture

- 9\. Data model and backend evolution plan

- 10\. API and event-contract plan

- 11\. Payments, logistics, QC, documents, disputes, and compliance boundaries

- 12\. Matching and procurement intelligence

- 13\. Notifications, action queues, and operational control tower

- 14\. Trust, reputation, provenance, and fraud-resistance model

- 15\. Government/FPO readiness without premature bureaucracy

- 16\. Monetisation and business-model hypotheses

- 17\. MVP -\> pilot -\> scale roadmap and what explicitly NOT to build

- 18\. Quality, security, observability, reliability, and anti-hallucination controls

- 19\. Acceptance tests and evidence gates

- 20\. Master coding-agent prompt and phase-by-phase execution prompts

- 21\. Competitive feature matrix and research references

# 1. Product thesis: what KrishiLink is actually supposed to become

KrishiLink is not primarily a listing website. It should become a transaction-execution network for agricultural procurement. The core job is: a buyer states a real requirement; KrishiLink discovers or assembles suitable supply; the parties agree on commercial terms; quality, logistics, payment, documents, and acceptance are coordinated; every material event is recorded; and the trade reaches a measurable outcome.

## 1.1 The core promise

BUYER NEED

-\> structured requirement

-\> supply discovery / aggregation

-\> explainable match

-\> negotiation

-\> trade agreement

-\> payment commitment through an appropriate partner

-\> quality / weighment evidence

-\> transport assignment

-\> pickup proof

-\> in-transit status

-\> delivery / acceptance

-\> settlement / payout status

-\> dispute path when needed

-\> completed trade record

-\> reputation + analytics

## 1.2 The non-negotiable user outcomes

- Farmer outcome: better-informed selling decisions, access to legitimate demand, lower uncertainty after accepting a deal, visible progress, and transparent expected net realization.

- FPO outcome: ability to aggregate member supply, satisfy larger buyer requirements, manage allocations, and maintain auditable records of member-level fulfilment without forcing members to become software experts.

- Buyer outcome: faster sourcing of the exact quantity/quality/time requirement, clearer landed cost, lower counterparty uncertainty, and fewer manual coordination steps.

- Operator outcome: one queue of exceptions and actions rather than manually reading every transaction.

- Government / public-institution outcome: aggregated, auditable market and trade signals with controlled access, while respecting privacy and avoiding claims that the platform is itself an official government system unless formally integrated.

## 1.3 What is not a defensible USP

- “We show mandi prices.” e-NAM already provides electronic market information and price/quality capabilities.

- “We connect farmers and buyers.” Multiple agri-commerce companies do this.

- “We provide logistics.” Existing platforms already integrate logistics or operate physical supply chains.

- “We provide quality verification and payments.” Existing platforms already expose these workflows.

- “We use AI.” AI is a means, not a value proposition.

- “We have a trust score.” A score without reliable transaction history is cosmetic and can be misleading.

## 1.4 The stronger differentiation hypothesis

The working differentiation hypothesis is not that KrishiLink invents a new category. It is that KrishiLink can be unusually good at orchestrating fragmented agricultural supply into executable B2B trades, with a simple farmer/FPO experience, demand-first procurement, transparent net realization, strong trade-room workflow, and a persistent digital trade record. This hypothesis must be validated with real buyers and FPOs before it is treated as a business truth.

## 1.5 North Star

Primary North Star: completed trade value, paired with completion quality. A trade should count as successful only when the commercial outcome is recorded: quantity delivered/accepted, payment state is known, and unresolved dispute status is absent. Secondary measures include requirement fill rate, time-to-match, on-time delivery, dispute rate, repeat purchase rate, repeat seller rate, net-realization improvement versus the relevant comparison point, and manual operator intervention rate.

# 2. Verified repository audit: what exists versus what must be built

> **Scope:** This audit is based on the supplied ZIP archive, not a live deployment. It does not prove that production integrations are active, credentials exist, external webhooks are configured, or that deployed UI matches the archive.

## 2.1 Confirmed architecture from repository

| **Area**                | **Observed in repository**                                                               | **Status for product**                                       |
|-------------------------|------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Frontend                | React/Vite SPA, route-based pages, Tailwind/Lucide, Leaflet map, dashboard layouts       | Existing foundation; workflow depth incomplete               |
| Backend                 | FastAPI, SQLAlchemy 2.0, Pydantic, modular routers/services                              | Existing foundation                                          |
| Database                | PostgreSQL/PostGIS intended, SQLite-compatible test path, Alembic migrations             | Existing foundation                                          |
| Caching / rate limiting | Redis with fallback pattern documented                                                   | Existing foundation                                          |
| Async jobs              | Celery/outbox described in docs; worker/beat architecture exists in repository materials | Operational verification still required                      |
| Object storage          | S3/R2-compatible adapter for uploads/presigned URLs                                      | Existing adapter; business workflows need expansion          |
| Observability           | OpenTelemetry, structured logs, request IDs, metrics                                     | Existing foundation                                          |
| Roles                   | farmer, buyer, fpo, admin, operator in data model                                        | Existing; transporter/QC provider not first-class user roles |

## 2.2 Confirmed core data objects

| **Entity**                                             | **Observed fields / purpose**                                                                                | **Current gap**                                                                                                   |
|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| User                                                   | identity, phone/email, location, district/state, role, verification, active state                            | Profile completeness, onboarding/KYC detail, consent and notification preferences                                 |
| FarmerProfile                                          | land area, primary crops, encrypted bank/IFSC fields                                                         | Need business-safe payout onboarding and verification workflow                                                    |
| BuyerProfile                                           | business name/type, license, crops, quantity range, preferred grade, rating, transaction count, geolocation  | Need requirement-centric procurement workspace and organization/user structure                                    |
| FPOProfile                                             | organization name, registration number, member count, land, crops                                            | Need member/aggregation workflow and allocation visibility                                                        |
| Crop / CropVariety                                     | canonical crop catalog, language fields                                                                      | Need commodity-specific quality and unit metadata                                                                 |
| Market / PriceSource / IngestionRun / PriceObservation | market coordinates and price provenance fields                                                               | Need freshness policies, source health UX, and no synthetic claims                                                |
| Lot                                                    | crop, grade, quantity, asking price, reference price, location, dates, status                                | Need photos, quality claims/evidence, packaging, availability constraints, lot provenance, seller-facing workflow |
| BuyerRequirement                                       | crop, variety, grade, min/max quantity, target price, radius, dates, delivery, storage, quality requirements | Strong foundation; needs UI and fulfillment-aware matching                                                        |
| Match / MatchRuleSet                                   | component scores, final score, explanation, ruleset version                                                  | Needs demand-side matching and landed-cost / reliability features                                                 |
| Offer                                                  | quantity, price, message, expiry, parent counter-offer                                                       | Needs richer contract terms and communication context                                                             |
| Reservation                                            | lot, buyer, offer, quantity, active/expired/consumed/cancelled                                               | Needs expiry UX and clear conversion into trade                                                                   |
| Transaction / TransactionItem                          | gross value, transport/storage/fees/net realization, status                                                  | Needs a true trade-room model and event history                                                                   |
| Payment                                                | provider/reference/amount/status                                                                             | Currently model only; actual production provider workflow not evidenced                                           |
| Delivery                                               | transaction, pickup/delivery geo, distance, estimated cost, status                                           | Needs transporter assignment, checkpoints, proof, ETA, exception management                                       |
| StorageFacility                                        | capacity, location, services, contact, verification status                                                   | Needs availability booking and contract/confirmation workflow                                                     |
| Dispute / Evidence                                     | lifecycle, operator, evidence file metadata                                                                  | Needs structured reason codes, SLA, evidence checklist, resolution accounting                                     |
| Notification / OutboxEvent                             | persistent notifications and transactional outbox                                                            | Needs expanded trade milestone templates and user action queue                                                    |

## 2.3 Confirmed backend workflows that are only partial product workflows

- Offer acceptance creates a reservation and can lead to transaction creation. The repository has row-level locking/idempotency protections.

- Transaction status transitions are explicitly controlled through an allowed-transition map; roles are checked for transitions.

- Matching is explainable and uses a 7-factor score in the present implementation: crop, grade, quantity, distance, price, time, verification.

- Price observations store source/provenance fields such as source ID, source URL, retrieval time, parser version, normalization version, raw payload hash, and quality status.

- Disputes have access-control protections around evidence and structured status changes.

- Notifications use an outbox pattern to avoid losing events when the main transaction commits.

## 2.4 Confirmed gaps that materially block a real product

| **Gap**                                                 | **Why it matters**                                                                                                                    | **Priority**                      |
|---------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| No real buyer-seller chat/conversation model            | After an offer, users need a controlled communication channel, clarification, and an auditable history.                               | P0                                |
| No first-class transporter workflow                     | A Delivery row alone cannot book, assign, checkpoint, or exception-manage a shipment.                                                 | P0 for physical fulfillment pilot |
| No first-class quality inspection workflow              | Grade A/B/C is not sufficient for real procurement. Buyers need commodity-specific evidence or accepted inspection rules.             | P0 for higher-value trades        |
| Payment is not evidenced as a production integration    | The application can represent payment state but must not imply money is held/released in production without a real regulated partner. | P0                                |
| No full trade room                                      | The major domain entities exist but are fragmented across pages; users do not see one coherent trade journey.                         | P0                                |
| Buyer requirement UI is missing/incomplete              | Demand-side procurement cannot drive the network unless a buyer can publish and manage requirements.                                  | P0                                |
| No proof-of-pickup/delivery workflow                    | Disputes become “he said / she said” without objective evidence.                                                                      | P0                                |
| No business organization model                          | Serious buyers/FPOs need multiple users, roles, and shared records.                                                                   | P1                                |
| No proper document/invoice/contract lifecycle           | B2B trade requires durable commercial artifacts.                                                                                      | P1                                |
| No reliability analytics based on real completed trades | Trust can only be meaningfully measured after history exists.                                                                         | P1                                |
| No operator exception queue                             | An end-to-end marketplace will fail operationally if humans cannot focus on exceptions.                                               | P0                                |

## 2.5 Truth rule for the coding agent

> **Rule:** Never infer “working” from the existence of a database table, route, mock provider, component, or README statement. The agent must verify the actual user journey from UI action through API, persistence, eventing, external side effect, and visible confirmation. Any unverified integration must be shown as “not connected” or “simulation/demo” in the UI.

# 3. Neutral competitive landscape: what already exists and what KrishiLink should learn from it

This section is intentionally neutral. Competitors are not described as “bad” or “behind.” Their existing scale and operating models are useful evidence about what the market already expects. KrishiLink should copy proven interaction patterns where legally and practically appropriate, but should not copy branding, proprietary content, or confidential implementation.

| **Player / system** | **Verified capabilities from first-party or official sources**                                                                                                                        | **Lesson for KrishiLink**                                                                                                      | **Do not imitate blindly**                                                                                               |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| e-NAM               | Electronic trading, buyer registration, real-time market/arrival/quality information, assaying, e-payments, FPO aggregation, logistics module, grievance/dispute mechanisms.          | Market data + quality + trade + FPO aggregation can coexist in one ecosystem; standardised evidence matters.                   | Do not assume KrishiLink can replace the public market infrastructure or use “official” language without formal status.  |
| AgriBazaar          | Marketplace/trading, negotiation, quality testing/QC reports, payments/AgriPay, warehousing, logistics, settlements, international business; describes tracking and dispute handling. | A trade should continue past “order placed.” Payment, quality, logistics, and settlement belong in the same operating journey. | Do not reproduce their infrastructure footprint; do not claim unique features simply because KrishiLink implements them. |
| Arya.ag / Aryadhan  | Integrated aggregation, storage, market linkage and finance; works with farmers/FPOs and has warehouse-receipt financing concepts.                                                    | Storage can be connected to timing/realisation decisions; FPOs are strategic, not peripheral.                                  | Do not build lending/custodial finance before there is a regulated partner and a real business case.                     |
| Ninjacart           | Large physical/digital agri network; focuses on payment risk, quality, logistics, real-time information and point-to-point produce trade.                                             | Operations and information flow matter as much as discovery; reliability is a product.                                         | Do not attempt to replicate a national physical network in the pilot.                                                    |
| WayCool             | Demand-driven supply chain, integration of information/material/money, distribution, logistics and food ecosystem operations.                                                         | Demand can drive procurement more effectively than passive listings; recurring B2B demand is a retention engine.               | Do not become a full distributor/food operator before product-market fit.                                                |
| DeHaat              | Hybrid physical + digital network, advisory, market linkage, FPOs, regional-language support, and large farmer network.                                                               | Farmer adoption may require assisted or physical workflows; software alone is not the whole adoption strategy.                 | Do not turn KrishiLink into a generic super-app with unrelated services.                                                 |
| ONDC                | Open network model, buyer/seller network participants, buyer-side search/matching and multiple frontends; can be integrated by technology providers.                                  | Long-term interoperability may be more powerful than trying to own every interface.                                            | Do not depend on ONDC before the core trade journey works; treat as an integration option, not the product thesis.       |

## 3.1 Copy the workflow principles, not the claims

- Copy e-NAM’s principle of standardised quality evidence and explicit settlement states.

- Copy AgriBazaar’s principle that goods, quality, payment, logistics, and settlement are one transaction story.

- Copy Arya’s principle that storage can be part of post-harvest market decisions and FPO economics.

- Copy Ninjacart’s principle of operational visibility and exception handling.

- Copy WayCool’s demand-driven procurement mindset and recurring requirements.

- Copy DeHaat’s principle that farmer UX must be accessible through local-language and assisted channels.

- Copy ONDC’s interoperability mindset for future network integration, without forcing an open-network architecture prematurely.

## 3.2 Strategic whitespace hypothesis

The most credible whitespace is not a missing feature; it is the combination of a simple farmer/FPO-facing procurement workflow with a buyer-grade execution layer. KrishiLink can aim to make the “messy middle” between discovery and settlement unusually transparent: who committed what, which quantity is reserved, what evidence exists, who is responsible for the next action, whether logistics are on track, and what amount is expected to settle.

# 4. Target users and jobs-to-be-done

## 4.1 Farmer

Primary job: “I have produce to sell. Help me understand what it is worth, find credible demand, choose the best executable option, and know what happens after I accept.”

- See reference prices with date/source context, not a single unexplained number.

- Create a lot with only essential information first, then enrich it with photos/evidence.

- Receive structured buyer interest and negotiate without immediately exposing personal contact information.

- See estimated net realization after known/estimated costs.

- See exactly what KrishiLink needs from them next.

- See pickup, delivery, payment, and dispute status in one place.

- Use assisted FPO/operator flows when self-service is too difficult.

## 4.2 Institutional / commercial buyer

Primary job: “I need a specific crop, quantity, quality, price range, and delivery window. Help me source it and execute it reliably.”

- Create requirements rather than browsing endlessly.

- See partial and full supply matches, including aggregatable supply.

- Compare seller/FPO options on landed cost, quantity, quality evidence, distance, availability, and observed reliability.

- Negotiate with structured commercial terms.

- Track all open trades and exceptions from one procurement workspace.

- Maintain repeat requirements and supplier relationships.

## 4.3 FPO

Primary job: “Aggregate members’ supply, preserve traceability, satisfy larger buyers, and distribute proceeds correctly.”

- Onboard members or at minimum maintain a member-linked supply allocation register.

- Aggregate multiple farm lots into a buyer-facing supply commitment.

- Track which member quantity is allocated, fulfilled, rejected, or pending.

- Keep a clean record for buyer reconciliation and member settlement.

## 4.4 Transporter / logistics partner

Primary job: “Receive jobs I can actually fulfil, know pickup details, report status, and prove delivery.”

- See jobs by corridor, vehicle capacity, commodity, schedule, and compensation.

- Accept/reject with a reason.

- Capture arrival, loading, departure, checkpoint, delay, and delivery events.

- Upload proof and exception evidence.

## 4.5 Quality/inspection provider

Primary job: “Receive an inspection request, collect the required evidence, issue a structured result, and make the result available to authorised participants.”

## 4.6 Operator

Primary job: “Resolve exceptions across many trades without becoming a bottleneck.”

- Work from an action queue ordered by risk and SLA.

- See every critical event and document in one trade context.

- Contact parties through controlled channels.

- Reassign logistics/QC work, request evidence, and escalate disputes.

## 4.7 Government / public institution (future, not MVP)

Potential job: “Observe aggregated market, supply, movement, and service-delivery signals without receiving unnecessary personal data.”

- Public market intelligence where licensing and source rights permit.

- FPO participation and service reach dashboards.

- Anomaly monitoring and grievance statistics.

- Aggregated procurement and supply-gap views.

- Program monitoring with role-based access and exportable reports.

# 5. Product operating model: the full trade lifecycle

1\. Discover market context

2\. Buyer publishes requirement OR farmer/FPO publishes supply

3\. Matching engine scores candidates

4\. Buyer/farmer inspects match explanation

5\. Negotiation / structured offer

6\. Agreement snapshot created

7\. Trade created

8\. Payment commitment through real provider workflow

9\. Quality / quantity verification where required

10\. Logistics plan created

11\. Pickup scheduled

12\. Pickup proof captured

13\. Shipment in transit

14\. Delivery proof captured

15\. Buyer acceptance OR controlled exception

16\. Settlement / payout status

17\. Trade completed

18\. Rating / reliability update

19\. Trade passport becomes permanent record

## 5.1 The Trade Room

The Trade Room is the central product concept. It is the user’s single source of truth for one trade. Every other page should lead back to it. It must be possible to answer these questions without leaving the page: What was agreed? What quantity is committed? How much is this worth? What is the current state? Who must act next? What evidence exists? Where is the produce? What is the payment status? What happens if something goes wrong?

## 5.2 Trade Room information hierarchy

| **Block**        | **Must show**                                                                                                       | **Interaction**                                                  |
|------------------|---------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| Trade header     | Trade ID, commodity, quantity, buyer, seller/FPO, current status, priority/exception badge                          | Open details                                                     |
| Money            | gross value, known costs, estimated net realization, payment state, payout state                                    | View breakdown / provider status                                 |
| Commercial terms | price, quantity, delivery window, quality requirements, packaging, Incoterm-like responsibility fields where needed | View immutable agreement snapshot; controlled amendment workflow |
| Quality          | grade, measured parameters, inspection status, evidence                                                             | View report; request/redo inspection if rules permit             |
| Logistics        | origin, destination, transporter, ETA, pickup/delivery checkpoints                                                  | Track / contact / report exception                               |
| Timeline         | every important system and human event with timestamp and actor                                                     | Filter by category                                               |
| Next action      | single primary action plus owner and deadline                                                                       | Perform action                                                   |
| Documents        | agreement, invoice, QC report, weighment, pickup proof, delivery proof, dispute evidence                            | View/download/upload according to permission                     |
| Communication    | trade-scoped messages                                                                                               | Message / attach evidence / system event                         |

## 5.3 “Next action” principle

Every active trade must expose one highest-priority next action. Examples: “Buyer: complete payment,” “Seller: confirm pickup time,” “Operator: assign transporter,” “QC provider: upload inspection report,” “Buyer: accept delivery or raise a dispute.” This reduces the need for users to understand internal state machines.

# 6. Detailed role architecture and permissions

| **Role**                   | **Can see**                                                                                      | **Can create**                                            | **Can change**                                                                                     | **Cannot**                                                                 |
|----------------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Farmer                     | own profile, own lots, own offers, own trades, authorised buyer details, payment/delivery status | lots, responses, evidence, support tickets                | own lot availability, negotiation responses, selected delivery data, acceptance where role permits | view unrelated users, alter immutable trade history, claim verified status |
| Buyer                      | public/authorised supply, own requirements, own offers/trades, seller/FPO verification summary   | requirements, offers, disputes, acceptance                | requirements, offers, delivery acceptance                                                          | alter seller evidence or platform-generated payment facts                  |
| FPO                        | organisation, member-linked supply where authorised, own requirements/trades                     | aggregate lots, allocations, requirements, member records | allocation state, trade operations                                                                 | view other FPO members without permissions                                 |
| Transporter                | assigned/eligible jobs, route details needed for fulfilment                                      | acceptance, checkpoints, evidence, exceptions             | delivery status fields assigned to transporter                                                     | change commercial price or payment state                                   |
| QC Provider                | assigned inspections and required lot/trade evidence                                             | inspection reports, measurements, files                   | inspection draft before finalisation                                                               | change buyer/seller commercial terms                                       |
| Operator                   | operationally necessary trades and queues                                                        | service tasks, internal notes, assignments                | logistics/QC assignment, supported state transitions, escalation                                   | edit immutable source evidence or fabricate external status                |
| Admin                      | system-wide operational/security view subject to least privilege                                 | configuration and controlled moderation                   | user verification, controlled rule activation, dispute resolution                                  | access secrets or payment credentials through ordinary UI                  |
| Government viewer (future) | aggregated or explicitly authorised datasets                                                     | reports/queries                                           | approved program metadata                                                                          | personal data outside authorised scope                                     |

## 6.1 Organisation model proposal

Before serious B2B rollout, buyers and FPOs should be able to represent an organisation with multiple users and role permissions. The current single-user BuyerProfile/FPOProfile approach is a valid prototype foundation but will become restrictive. The proposed model is Organization -\> Members -\> Roles -\> Requirements/Lots/Trades. This should be introduced deliberately, with migration compatibility, rather than replacing the current model in one destructive rewrite.

# 7. State machines and lifecycle rules

## 7.1 Supply lot state

DRAFT

-\> PUBLISHED

-\> PARTIALLY_ALLOCATED

-\> RESERVED / SOLD

-\> FULFILLED

Alternative exits:

DRAFT -\> CANCELLED

PUBLISHED -\> EXPIRED

PUBLISHED -\> CANCELLED

RESERVED -\> CANCELLED / EXPIRED

PARTIALLY_ALLOCATED -\> CANCELLED (remaining quantity only)

## 7.2 Offer state

PENDING -\> COUNTERED -\> PENDING (new offer version)

PENDING -\> ACCEPTED

PENDING -\> REJECTED

PENDING -\> EXPIRED

PENDING -\> CANCELLED

The UI must show the offer chain clearly. A counter-offer is a new version linked to the prior version, not an overwrite of history.

## 7.3 Trade state

CREATED

-\> PAYMENT_PENDING

-\> PAYMENT_CONFIRMED

-\> PROCESSING

-\> READY_FOR_DISPATCH

-\> IN_TRANSIT

-\> DELIVERED

-\> COMPLETED

Exception path:

any operational state -\> DISPUTED

DISPUTED -\> RESOLVED / CANCELLED

Cancellation/refund must be explicit and policy-driven.

## 7.4 Logistics state proposal

REQUESTED

-\> QUOTING

-\> ASSIGNED

-\> PICKUP_SCHEDULED

-\> ARRIVED_FOR_PICKUP

-\> LOADING

-\> PICKED_UP

-\> IN_TRANSIT

-\> ARRIVED_AT_DESTINATION

-\> DELIVERED

Exception side paths:

ASSIGNED -\> REASSIGNMENT_REQUIRED

IN_TRANSIT -\> DELAYED / INCIDENT

Any relevant stage -\> CANCELLED with reason

## 7.5 Quality state proposal

NOT_REQUIRED

REQUESTED

ASSIGNED

SAMPLE_COLLECTED

IN_TESTING

REPORT_DRAFT

PASSED / FAILED / CONDITIONAL

FINALISED

A failed inspection must not silently become a passed inspection.

## 7.6 Payment state proposal

NOT_REQUIRED

INITIATED

PENDING

SUCCESS / FAILED

REFUND_PENDING

REFUNDED

SETTLEMENT_PENDING

SETTLED

Provider webhooks are the source of truth for provider-side state.

KrishiLink stores a reconciled platform state plus provider reference.

## 7.7 State-machine rule

> **Hard requirement:** Every state transition must have: actor, timestamp, source, reason (where applicable), previous state, new state, and idempotent event handling. No direct “set status” mutation should bypass a domain transition service.

# 8. Screen-by-screen product specification

## 8.1 Public landing page

- Position around completed agricultural trades and reliable procurement, not generic “marketplace” language.

- Show two primary paths: “I want to sell” and “I need to buy.”

- Explain the trade lifecycle visually: demand/supply -\> agreement -\> verification -\> fulfillment -\> settlement.

- Show market data provenance and freshness when displaying prices.

- Never display invented testimonials, statistics, partner logos, government seals, or live-price claims unless sourced and verified.

## 8.2 Farmer home

TOP PRIORITY

Action required: 2

Active trades: 3

Expected net value in active trades: Rs. ...

MARKET SNAPSHOT

Wheat / Onion / Tomato cards with source date + source label

BUYER DEMAND NEAR YOU

3 requirements match your crop

MY LOTS

Draft / published / partially allocated / sold

RECENT ACTIVITY

Offer -\> payment -\> pickup -\> delivery updates

## 8.3 Sell produce

- Progressive form: crop -\> quantity -\> grade -\> price -\> location -\> availability -\> evidence -\> optional details.

- Reference-price card beside asking price, with freshness/source.

- Net-realization preview: show only known costs and clearly label estimates.

- Photo upload and evidence should be optional for basic listing but strongly encouraged for high-value trades.

- After creation, offer an immediate “View matching buyers” action.

## 8.4 Buyer procurement home

OPEN REQUIREMENTS

\- Requirement / crop / quantity / target price / delivery date / fill %

OPEN TRADES

\- Current stage / landed cost / exception

SUPPLY GAP

\- “You need 1,000 QTL; 640 QTL confirmed; 360 QTL to source”

RECOMMENDED SUPPLY

\- Full matches first, then aggregatable partial matches

ACTION QUEUE

\- Review quote / select suppliers / confirm inspection / accept delivery

## 8.5 Create requirement

- Commodity and variety.

- Minimum and target quantity; optionally maximum quantity.

- Target price or range, if buyer wants price guidance.

- Quality/grade and commodity-specific requirements.

- Origin radius or preferred sourcing geography.

- Required pickup/delivery windows.

- Packaging/transport/storage requirements.

- Whether partial fulfillment is acceptable.

- Whether KrishiLink may aggregate across multiple farmers/FPOs.

## 8.6 Supply assembly workspace

This is a major proposed feature. The buyer requirement screen should let the buyer see “full fill,” “partial fill,” and “aggregated plan.” A plan could contain several suppliers and show total quantity, blended price, estimated logistics, quality evidence status, and concentration risk. It must never present an algorithmic plan as guaranteed until suppliers actually commit.

## 8.7 Matches

Replace a simple “score card” with a procurement explanation. Example: “92% fit: crop and delivery window match; quantity covers 70% of your target; price is 4% above target; seller has 18 completed trades with 94% on-time history.” Every metric must identify whether it is observed, calculated, inferred, or missing.

## 8.8 Offers and negotiation

- Conversation-style offer history with version numbers.

- Structured terms displayed next to free-text message.

- Expiry countdown only when an actual expiry exists.

- Accept / counter / reject actions with validation.

- After acceptance: one obvious “Create Trade” or “Continue to Trade” transition, not a dead-end.

## 8.9 Trade room

- Persistent header with current state and next action.

- Commercial terms snapshot.

- Cost and net-realization panel.

- Quality panel.

- Logistics panel and checkpoint map.

- Payment panel with provider status, not invented escrow language.

- Documents/evidence area.

- Trade-scoped chat.

- Audit timeline.

- Dispute control with structured reason codes.

## 8.10 Operator control tower

| **Queue**            | **Example condition**                             | **Operator action**                      |
|----------------------|---------------------------------------------------|------------------------------------------|
| Payment exceptions   | Provider webhook mismatch or long-pending payment | Reconcile / escalate to payment provider |
| QC exceptions        | Inspection not assigned near deadline             | Assign provider / contact seller         |
| Logistics exceptions | No transporter, delayed pickup, route incident    | Assign/reassign / request status         |
| Trade exceptions     | Stalled state beyond SLA                          | Investigate trade timeline               |
| Disputes             | New or escalated disputes                         | Review evidence / resolve / escalate     |
| Verification         | High-value buyer/seller not verified              | Request documents / approve / reject     |
| Data health          | Stale price source / ingestion failure            | Mark data freshness, fix source adapter  |

## 8.11 Government/public analytics (future)

- Aggregated price and trade-volume trends where data rights permit.

- Supply-demand gap by crop and district.

- FPO participation and fulfilment performance.

- Logistics service availability / delay trends.

- Dispute reason distributions.

- Exportable reports and API access with privacy controls.

- Explicitly separate platform-generated analytics from official government statistics.

# 9. Communication design

Communication is not a side feature. It is the missing bridge after discovery. The minimum viable model is trade-scoped conversation: seller and buyer can communicate after a legitimate interest/offer exists; each message is associated with a trade or offer context; attachments are stored with permissions; system events are visually distinct from human messages.

## 9.1 Conversation rules

- No unrestricted platform-wide chat in the first release.

- No automatic exposure of personal phone numbers before a defined stage.

- Every message has sender, timestamp, trade/offer context, and optional attachment.

- System events are immutable and cannot be edited by users.

- Abuse/report controls exist.

- Support staff can access conversations only under role-based permissions and audit logging.

## 9.2 Contact sharing strategy

The product can eventually allow controlled contact exchange or masked calling after a trade reaches a defined stage. This should be configurable and audited. Do not assume WhatsApp or telephony integration is free; treat it as a partner/integration decision.

## 9.3 Message templates

- Buyer clarification request

- Seller availability confirmation

- Price counter-proposal

- Quality question

- Pickup coordination

- Delay notification

- Delivery acceptance request

- Dispute evidence request

# 10. Quality, quantity, provenance, and Trade Passport

## 10.1 Quality is commodity-specific

Do not hard-code a universal definition of Grade A/B/C beyond the current prototype constraint. For real procurement, the system needs a commodity-quality schema that can vary by crop and by the applicable standard or buyer specification. The schema should support required, optional, measured, declared, and verified fields.

## 10.2 Proposed Trade Passport

Every completed trade should have a persistent digital record. This is not claimed as a uniquely invented market category; it is the product’s internal organizing concept.

| **Section**        | **Contents**                                                                     |
|--------------------|----------------------------------------------------------------------------------|
| Identity           | trade ID, lot IDs, agreement version, participants                               |
| Commercial         | quantity, unit, price, fees, known/estimated costs, delivery responsibility      |
| Quality            | declared quality, inspected measurements, provider/report references             |
| Logistics          | origin, destination, transporter, checkpoints, exceptions, proofs                |
| Money              | payment references, status history, settlement status                            |
| Communication      | relevant structured messages and acknowledgements, subject to retention policy   |
| Evidence           | documents, photos, hashes, timestamps, uploader identity                         |
| Outcome            | delivered quantity, accepted/rejected quantity, dispute outcome, completion time |
| Reputation signals | derived metrics used after sufficient history exists                             |

## 10.3 Evidence integrity

- Store original file hash.

- Store uploader ID and timestamp.

- Store the related entity (lot/trade/delivery/dispute).

- Never silently replace an uploaded evidence file; version or supersede it.

- Keep metadata minimal and privacy-aware.

- Use signed URLs/presigned URLs for access; do not expose storage keys as public URLs.

## 10.4 Weighment

For commodities where weight at pickup or delivery matters, capture planned quantity, pickup weight, delivery weight, tolerance rules, and supporting evidence. Do not invent tolerance percentages universally. They should be configurable by commodity/trade terms.

# 11. Logistics product design

## 11.1 Minimum viable operational model

Do not launch as a nationwide truck marketplace. Start with approved logistics partners or operator-created bookings. The software should nevertheless model the full workflow so the provider can be swapped later.

## 11.2 Transport request

| **Field group** | **Examples**                                                       |
|-----------------|--------------------------------------------------------------------|
| Cargo           | commodity, quantity, packaging, declared weight                    |
| Route           | pickup geolocation, destination, route distance                    |
| Schedule        | pickup window, delivery window                                     |
| Vehicle         | required capacity, vehicle class, temperature needs where relevant |
| Commercial      | quote, included costs, who pays freight, cancellation rule         |
| Evidence        | vehicle identity, pickup proof, delivery proof                     |
| Status          | requested -\> assigned -\> pickup -\> transit -\> delivered        |

## 11.3 Tracking

Real-time GPS should be optional initially. A reliable milestone model is more important than a flashy map. If GPS is added later, every location signal should clearly indicate source, freshness, and accuracy. Never show a truck on the map merely because the UI inferred a route.

## 11.4 Exception-first logistics

- No transporter assigned by deadline.

- Transporter accepts then cancels.

- Vehicle arrives late.

- Pickup quantity differs materially from plan.

- Vehicle incident / breakdown.

- Weather or road event affects route.

- Destination refuses delivery.

- Delivery quantity/quality mismatch.

# 12. Payment and settlement architecture: safe boundaries

> **Critical:** The repository currently has a Payment model and transaction states, but that does not establish that KrishiLink is a regulated payment aggregator or that funds are actually escrowed by KrishiLink. Production money movement must be implemented with an appropriate regulated payment partner/bank arrangement and reconciled through provider webhooks and backend controls.

## 12.1 Platform architecture

KrishiLink Trade

-\> Payment Service Adapter

-\> licensed/appropriate payment provider

-\> provider webhook

-\> Payment Reconciliation Service

-\> transaction state transition

-\> notification / audit / operator queue

## 12.2 Never do these

- Do not call a database payment record “money held by KrishiLink.”

- Do not fake success when a provider call fails.

- Do not trust a client-side success callback as final settlement evidence.

- Do not expose secret provider credentials to the frontend.

- Do not build a wallet or custodial balance system unless the legal/regulatory model is explicitly designed and reviewed.

## 12.3 Payment adapter contract

PaymentAdapter.create_payment(trade, payer, amount) -\> provider reference

PaymentAdapter.get_payment(reference) -\> provider status

PaymentAdapter.verify_webhook(request) -\> verified event

PaymentAdapter.refund(reference, amount, reason) -\> provider reference

PaymentAdapter.reconcile(reference) -\> authoritative status

## 12.4 Reconciliation

Every successful provider event must be idempotent. The system should be able to reconcile an internal “pending” payment with provider reality. Build a periodic reconciliation job only after a real provider is selected.

# 13. Matching and procurement intelligence

## 13.1 Existing matching engine

The supplied implementation has a seven-factor score: crop, grade, quantity, distance, price, time, and verification, with explainable component scores and a versioned ruleset. This is a useful prototype. Do not discard it.

## 13.2 Required evolution

The engine should become demand-aware and fulfillment-aware. A buyer requirement can be partially fulfilled by several lots. The result should be explainable and should distinguish feasibility from attractiveness.

## 13.3 Proposed score dimensions

| **Dimension**        | **Meaning**                                         | **Data quality rule**                                        |
|----------------------|-----------------------------------------------------|--------------------------------------------------------------|
| Commodity fit        | Exact commodity/variety compatibility               | Canonical crop/variety mapping required                      |
| Quality fit          | Declared/verified properties against requirement    | Verified \> declared \> unknown; never treat unknown as pass |
| Quantity fit         | Can this lot or cluster meet the target?            | Distinguish exact/full/partial fit                           |
| Price fit            | Distance from buyer target or seller asking price   | Show actual difference; do not imply savings                 |
| Landed-cost fit      | Estimated total cost to destination                 | Mark transport/fees as estimates until booked                |
| Time fit             | Supply and delivery windows                         | Hard incompatibilities should be blockers                    |
| Distance / route fit | Practical route proximity                           | Distance is not the same as logistics quote                  |
| Reliability          | Observed completed-trade performance                | Only compute after sufficient data; show sample size         |
| Verification         | Identity/business verification                      | Verification status must be evidence-backed                  |
| Concentration risk   | Too much of one requirement sourced from one seller | Useful for larger procurement                                |

## 13.4 Hard constraint vs soft score

A core improvement is to separate hard constraints from ranking. Example: a requirement for 1,000 QTL by 10 Sept should not rank a supplier whose earliest availability is 20 Sept as “65% good.” It should be an explicit incompatibility. Then softer factors such as price and distance rank the feasible candidates.

## 13.5 Aggregation algorithm concept

INPUT

buyer requirement R

candidate supply lots L1..Ln

constraints C

cost model K

risk limits Q

OUTPUT

one or more supply plans

PLAN = subset(L)

subject to:

total quantity \>= required minimum

every hard quality constraint passes

delivery window feasible

seller/lot availability not overallocated

optional risk/concentration limits

rank plans by:

landed cost

quality confidence

delivery confidence

supplier reliability

operational complexity

## 13.6 AI usage

AI can help parse free-text buyer requirements, summarise differences between supplier plans, explain why a match is recommended, and assist operators. AI must not silently fabricate market prices, inventory, provider status, quality values, delivery ETA, or legal status. Structured system fields remain authoritative.

# 14. Market intelligence and data provenance

## 14.1 Price data principles

- Always show observation date.

- Show market/source context.

- Show whether the number is modal/min/max when relevant.

- Show freshness and ingestion health when the value is used for decisions.

- Keep source URLs/IDs internally.

- Do not create synthetic historical records and present them as observed market history.

## 14.2 Price page

The price page should evolve from “chart” into a decision surface: “What is happening near me?”, “How does this compare to other markets?”, and “What might this imply for my current trade?” The last section must be clearly labelled as a calculated scenario rather than a forecast unless an independently validated model exists.

## 14.3 Source-health dashboard

- Last successful ingestion per source.

- Records fetched / accepted / rejected.

- Parser version.

- Error message when a source fails.

- Staleness threshold.

- Fallback behavior: show stale data with warning rather than fabricate new data.

# 15. Trust, verification, fraud-resistance, and reputation

## 15.1 Verification ladder

- Identity/account verified.

- Business/FPO documents verified where applicable.

- Bank/payout details verified through an appropriate process.

- Trade history established.

- Operational reliability observed.

- Optional high-value trade verification.

## 15.2 Do not create fake trust

A green badge should mean something. Define each badge, its source, refresh cadence, and revocation rule. “Verified” must never be a decorative label generated from account creation alone.

## 15.3 Reputation metrics

| **Metric**          | **Definition**                                         | **Minimum-data policy**                     |
|---------------------|--------------------------------------------------------|---------------------------------------------|
| Completed trades    | Trades reaching completed outcome                      | Always show count                           |
| On-time delivery    | Trades delivered within agreed window                  | Show numerator/denominator                  |
| Quantity accuracy   | Delivered vs agreed quantity within contract tolerance | Commodity/trade-rule aware                  |
| Payment reliability | Buyer payment obligations completed as required        | Only for observable platform payment states |
| Dispute rate        | Trades with formal disputes / completed trades         | Show sample size                            |
| Acceptance rate     | Accepted offers that convert to completed trades       | Separate seller/buyer role                  |

## 15.4 Abuse and fraud controls

- Rate-limit high-risk mutations.

- Use idempotency keys for money/critical state creation.

- Lock allocations during acceptance.

- Detect repeated cancellation / non-payment patterns.

- Flag impossible price or quantity combinations for review without blocking legitimate trades automatically.

- Keep immutable audit history.

# 16. FPO aggregation as a major real-world use case

FPOs are not just another role. They can solve a marketplace liquidity problem because buyers often need scale while individual farmers have fragmented quantities. e-NAM itself describes FPOs as aggregators of member produce and notes their ability to sell one or multiple lots. That makes FPO-first procurement a credible direction, not a speculative add-on.

## 16.1 Aggregation flow

Buyer requirement: 1,000 QTL

\|

v

KrishiLink sourcing plan

\|

+-------+-------+-------+

v v v v

FPO A Farm B Farm C FPO D

300 120 180 450 QTL

\| \| \| \|

+-------+-------+--------+

v

1,050 QTL planned

\|

v

1,000 QTL committed

\|

v

coordinated fulfillment

## 16.2 Member-level traceability

- Member ID / internal member reference.

- Member lot/quantity contribution.

- Allocation to buyer trade.

- Quantity picked up/accepted.

- Member payout record only where appropriate and consented.

- FPO retains control of member financial disbursal where the business/legal relationship requires it.

## 16.3 Why this improves product-market fit

A buyer requirement can create demand that individual farmers cannot fulfil alone. An FPO can turn KrishiLink from a classifieds directory into an execution system. The platform also gains a natural onboarding channel because one FPO can bring many producers into the network.

# 17. Government / public-sector value: credible, not exaggerated

Government value should be treated as a downstream opportunity, not the reason to build a bloated first version. A useful public-sector system needs reliable data, documented definitions, privacy boundaries, auditability, and role-based access. “Government-ready” should mean the platform can generate trustworthy structured records and reports, not that the government will automatically adopt it.

## 17.1 Potential government use cases

- Aggregated crop demand and supply dashboards by district/market.

- FPO and smallholder market-access monitoring.

- Trade bottleneck analysis: quality, transport, payment, dispute patterns.

- Service-provider availability and performance analytics.

- Pilot procurement programs where the government is the buyer or coordinator and appropriate procurement rules are followed.

- Early-warning dashboards for supply gaps where validated data supports such analysis.

## 17.2 Interoperability strategy

Design exports and APIs so KrishiLink can interoperate later with open networks, government datasets, or enterprise systems. Do not build a proprietary closed world. At minimum, all major records should have stable public/partner-safe identifiers, timestamps, source metadata, and versioned schemas.

## 17.3 Privacy boundary

Government dashboards should default to aggregated data. Personally identifiable information, financial details, private messages, and precise household-level location must never leak into public analytics merely because the backend stores them.

# 18. Business model and unit-economics hypotheses

The product must eventually pay for its operating costs. But pricing should not be chosen before the operating model is understood. The first pilot should prove that users are willing to transact before aggressive monetisation.

## 18.1 Candidate revenue streams

| **Model**                      | **What user pays for**                                                | **When it makes sense**                         | **Risk**                                                    |
|--------------------------------|-----------------------------------------------------------------------|-------------------------------------------------|-------------------------------------------------------------|
| Transaction fee                | Successful trade execution                                            | After repeat usage is established               | Can create fee resistance or push users off-platform        |
| Buyer procurement subscription | Priority workflow, analytics, saved requirements, supplier management | Once buyers use KrishiLink repeatedly           | Requires meaningful B2B value                               |
| Logistics service margin       | Coordination fee on fulfilled transport                               | When KrishiLink actually adds operational value | Thin margins / operational complexity                       |
| QC/inspection coordination fee | Convenience and evidence workflow                                     | For buyers who need documented quality          | Requires partner network and quality governance             |
| Enterprise/FPO software fee    | Advanced team controls/reporting                                      | For larger organisations                        | Do not charge for basics needed to create network liquidity |
| Data/analytics products        | Aggregated market or procurement intelligence                         | After data scale and rights are established     | Privacy/data-rights/commercialisation risk                  |

## 18.2 Avoid

- Pay-to-win matching where higher-paying users automatically receive worse/hidden neutrality.

- Opaque fees revealed only at settlement.

- Charging farmers before proving that the platform creates enough value.

- Holding customer funds as a business model without proper regulatory structure.

# 19. What to build first, second, later, and never unless validated

## 19.1 P0: complete one real trade loop

1.  Buyer can create a requirement.

2.  Farmer/FPO can publish a lot.

3.  Matching produces explainable candidates.

4.  Buyer can make an offer and counter.

5.  Both parties can communicate inside trade context.

6.  Accepted offer creates a trade room.

7.  Trade has a clear current state and next action.

8.  Payment integration is real or explicitly sandboxed, never falsely represented.

9.  Transport request can be created and assigned operationally.

10. Pickup/delivery proof can be captured.

11. Buyer can accept delivery or open a structured dispute.

12. Trade can reach completed/settled state with evidence.

13. Notifications and operator exception queue work end-to-end.

## 19.2 P1: make the loop scalable

- Organization accounts for buyers/FPOs.

- FPO member allocation.

- Commodity-specific quality schemas.

- Document/invoice generation.

- Recurring buyer requirements.

- Reliability metrics with sample sizes.

- Supplier management.

- More logistics-provider automation.

- Support/CRM features for operators.

## 19.3 P2: network effects and intelligence

- Supply-plan optimisation across multiple suppliers.

- Predictive demand only after validated historical data.

- Storage decision support.

- Partner finance integrations.

- Open-network integrations such as ONDC where commercially relevant.

- Government/public analytics interfaces.

## 19.4 Explicitly do NOT build now

- National truck marketplace.

- KrishiLink-owned warehouses.

- KrishiLink-owned lending/custody/wallet infrastructure.

- A giant farmer social network.

- Generic AI chatbot as the main feature.

- Satellite crop forecasting before transaction fundamentals work.

- Dozens of crops and regions before a local pilot works.

- Complex blockchain layer; use ordinary tamper-evident audit mechanisms unless a real requirement proves otherwise.

# 20. Pilot strategy and validation plan

## 20.1 Pilot hypothesis

A narrow corridor and commodity should be used to learn whether buyers will repeatedly source through KrishiLink and whether farmers/FPOs perceive measurable value. A Nashik-centric crop pilot is a practical starting hypothesis because the current repository is already oriented around Maharashtra/APMC data, but the specific commodity must be chosen based on real partner interviews and actual local supply/demand.

## 20.2 Pilot cohort

- 3-5 institutional buyers.

- 1-3 FPOs.

- 10-20 farmers initially if FPO supply is also included.

- 5-10 transport partners or operator-managed transport capacity.

- 1-2 quality/inspection partners as needed for the selected commodity.

- One small operations team capable of manually handling exceptions.

## 20.3 Evidence to collect

- How long it takes a buyer to source a requirement.

- How much of the requirement KrishiLink can fill.

- Difference between initial expected and actual landed cost.

- On-time pickup/delivery.

- Payment completion time.

- Dispute causes.

- Manual intervention per trade.

- Repeat usage within 30/60/90 days.

- Farmer/FPO net-realization perception and actual comparison where measurable.

## 20.4 Pilot success is not downloads

A successful pilot means real counterparties complete real trades with less friction than their existing process. If users will not transact because they do not trust one another, adding more screens will not solve the problem. The product may need partnerships, assisted onboarding, guarantees, or service operations. The build plan must allow those findings to change the feature roadmap.

# 21. Engineering architecture and evolution plan

## 21.1 Preserve the good foundation

- Keep FastAPI/SQLAlchemy/PostGIS unless profiling or deployment evidence proves a change necessary.

- Keep the existing idempotency pattern.

- Keep transaction row locking for lot allocation.

- Keep source provenance for price observations.

- Keep the transactional outbox pattern.

- Keep audit logs and request IDs.

- Keep modular backend boundaries.

## 21.2 Introduce domain services rather than route logic

TradeService

OfferService

RequirementService

MatchingService

SupplyPlanService

PaymentService / PaymentAdapter

LogisticsService

QualityService

DocumentService

ConversationService

DisputeService

ReputationService

NotificationService

AuditService

## 21.3 Proposed new core entities

| **Entity**                | **Purpose**                                     | **Priority**                   |
|---------------------------|-------------------------------------------------|--------------------------------|
| Organization              | Multi-user buyer/FPO account                    | P1                             |
| OrganizationMember        | Role and access control                         | P1                             |
| Conversation              | Trade/offer-scoped chat container               | P0                             |
| Message                   | Human/system message with attachment references | P0                             |
| TradeEvent                | Immutable normalized event timeline             | P0                             |
| TradeTermSnapshot         | Immutable accepted commercial terms             | P0                             |
| TransportRequest          | Operational logistics request                   | P0                             |
| TransportAssignment       | Specific transporter/vehicle assignment         | P0/P1                          |
| LogisticsCheckpoint       | Pickup/transit/delivery evidence point          | P0                             |
| QualityInspection         | Inspection request/result lifecycle             | P0/P1 based on pilot commodity |
| QualityMeasurement        | Structured commodity-specific measurements      | P1                             |
| Document                  | Invoice/contract/report/proof metadata          | P1                             |
| SupplyPlan                | Buyer requirement fulfilment plan across lots   | P1                             |
| SupplyPlanItem            | Lot/FPO allocation within supply plan           | P1                             |
| Rating / ReputationMetric | Post-trade feedback and derived reliability     | P1                             |
| ServiceProvider           | Transport/QC/warehouse partner registry         | P1                             |

## 21.4 Migration strategy

Existing Transaction should not be discarded. The new Trade object can wrap or coexist with the existing transaction record, depending on migration complexity. A safe route is: preserve existing API compatibility; introduce Trade as the orchestration aggregate; map old transactions into trades; progressively move UI and new workflows to TradeService. Do not run a destructive database rewrite just to create cleaner names.

# 22. API contract roadmap

## 22.1 Proposed endpoints

| **Domain**   | **Examples**                                                                                                                                  |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Requirements | POST /requirements, GET /requirements, GET /requirements/{id}, PATCH /requirements/{id}, POST /requirements/{id}/plans                        |
| Supply       | POST /lots, GET /lots, GET /lots/{id}, PATCH /lots/{id}, POST /lots/{id}/evidence                                                             |
| Matching     | GET /matches, POST /matches/refresh, GET /matches/{id}/explanation, POST /requirements/{id}/matches                                           |
| Offers       | POST /offers, POST /offers/{id}/counter, POST /offers/{id}/accept, POST /offers/{id}/reject, GET /offers/{id}/history                         |
| Trades       | POST /trades, GET /trades, GET /trades/{id}, POST /trades/{id}/transition, GET /trades/{id}/timeline                                          |
| Conversation | POST /trades/{id}/messages, GET /trades/{id}/messages, POST /messages/{id}/attachments, POST /messages/{id}/report                            |
| Payments     | POST /trades/{id}/payment-intent, GET /payments/{id}, POST /payments/webhook, POST /payments/{id}/reconcile                                   |
| Logistics    | POST /trades/{id}/transport-request, GET /transport-requests, POST /transport-requests/{id}/accept, POST /transport-requests/{id}/checkpoints |
| Quality      | POST /trades/{id}/inspections, GET /inspections/{id}, POST /inspections/{id}/measurements, POST /inspections/{id}/finalise                    |
| Documents    | POST /trades/{id}/documents, GET /trades/{id}/documents/{document_id}                                                                         |
| Disputes     | POST /trades/{id}/disputes, GET /disputes/{id}, POST /disputes/{id}/evidence, POST /disputes/{id}/decision                                    |
| Operator     | GET /operator/queue, POST /operator/tasks/{id}/assign, POST /operator/tasks/{id}/resolve                                                      |

## 22.2 API rules

- All mutation endpoints require authentication and explicit role/ownership checks.

- Critical mutations support idempotency keys.

- Errors are explicit and truthful; no success wrapper around failed downstream operations.

- Every response has stable machine-readable status and human-safe message.

- Pagination is cursor- or page-based consistently.

- Long-running operations return operation/job identifiers when needed.

- External-provider references are never exposed unless safe and intended.

# 23. Notifications and action-center architecture

Notifications should stop being passive badges and become an action system. Every trade milestone should produce a notification only when the user has something useful to know or do. Avoid notification spam.

## 23.1 Notification priority

| **Priority**    | **Examples**                                                           | **Channel**                      |
|-----------------|------------------------------------------------------------------------|----------------------------------|
| Critical        | payment mismatch, delivery refusal, high-value dispute, security event | in-app + configured channel      |
| Action required | accept offer, confirm pickup, upload QC report                         | in-app + optional SMS/email/push |
| Informational   | trade created, truck departed, delivery completed                      | in-app                           |
| Digest          | market summary, recurring buyer demand                                 | in-app/email digest              |

## 23.2 Action queue

Dashboard should surface tasks sorted by urgency and impact. The user should never need to open notifications one by one to discover what requires action.

# 24. Security, privacy, and compliance guardrails

- Maintain least-privilege access to transactions and evidence.

- Keep payment details tokenized or provider-hosted; do not store unnecessary financial secrets.

- Use secure presigned uploads and validate MIME/type/size.

- Audit state changes and administrative decisions.

- Rate-limit authentication, offers, evidence uploads, and payment-related actions.

- Protect against IDOR on lot, transaction, dispute, message, and document endpoints.

- Add anti-abuse controls for repeated offer spam.

- Define retention policies for messages, evidence, and documents.

- Separate public analytics from private participant data.

- Treat government integrations as formal interfaces with explicit data-sharing agreements, not as an assumption.

## 24.1 Payment regulatory boundary

RBI materials establish that payment aggregation is regulated and can involve merchant onboarding, escrow operations, security and other requirements. The exact current legal model must be reviewed with counsel and the chosen payment provider before launch. This document therefore requires an adapter architecture rather than a homemade wallet/escrow system.

# 25. Observability and operational reliability

## 25.1 Per-trade observability

- trade_id correlation ID across logs, events, payments, logistics, and notifications.

- state-transition audit entry for every transition.

- provider reference for external payment events.

- job ID for async work.

- source timestamp for external data.

- operator action record when humans intervene.

## 25.2 Service-level objectives for pilot

Define realistic pilot SLOs after observing actual workloads. The first release should at minimum expose internal measures for API error rate, webhook reconciliation lag, stale market data, notification delivery failures, stuck trades, and open operator queues. Do not promise public SLA numbers that the deployment does not support.

# 26. Testing strategy: user journey is the real test

## 26.1 P0 E2E journey

14. Create buyer and seller accounts with appropriate verification state.

15. Buyer creates requirement.

16. Seller creates lot.

17. Matching returns seller/requirement compatibility with explanation.

18. Buyer sends offer.

19. Seller counters.

20. Buyer accepts.

21. Trade is created exactly once despite retry.

22. Conversation exists and messages are correctly scoped.

23. Payment provider sandbox or controlled test adapter reports a real test status.

24. Transport request is created and assigned.

25. Pickup checkpoint is recorded with evidence.

26. Transit checkpoint is recorded.

27. Delivery checkpoint is recorded.

28. Buyer accepts delivery.

29. Payment settlement state is reconciled.

30. Trade reaches COMPLETED.

31. Ratings/reputation inputs are generated.

32. Trade passport is viewable by authorised parties.

## 26.2 Failure-path E2E tests

- Buyer retries accept request twice -\> no duplicate allocation/trade.

- Payment provider returns failure -\> trade stays unpaid; no fake success.

- Payment provider webhook arrives twice -\> idempotent.

- Transporter cancels -\> operator queue receives task.

- Delivery quantity mismatch -\> buyer can choose accept-with-variance or dispute according to trade rules.

- QC failure -\> status reflects failure; no silent continuation.

- Unauthorized user tries to view another trade -\> 403/404 according to chosen security policy.

- Operator attempts forbidden commercial term change -\> denied and audited.

- Data source goes stale -\> UI warns; no synthetic replacement presented as live data.

## 26.3 Definition of done

> **A feature is done only when:** the UI, API, persistence, authorization, error states, events/notifications, tests, observability, and deployment configuration are all coherent. A placeholder route, mock result, dead-end CTA, or visually polished but nonfunctional screen is not complete.

# 27. Anti-hallucination and truthfulness protocol for the coding agent

## 27.1 Evidence classes

| **Class**                | **Meaning**                                      | **Allowed wording**              |
|--------------------------|--------------------------------------------------|----------------------------------|
| R1 - Repository verified | Observed directly in supplied source code/config | “Exists in repository”           |
| R2 - External verified   | Supported by official/first-party source         | “Official source states…”        |
| P1 - Proposed            | New design recommendation                        | “Proposed” / “To build”          |
| A1 - Assumption          | Needs user/partner validation                    | “Assumption / validate in pilot” |
| U1 - Unknown             | Not verified                                     | “Unknown / do not claim”         |

## 27.2 Mandatory behavior

- Before editing architecture, inspect the existing implementation and tests.

- Search for an existing service/entity before creating a duplicate.

- When a desired external integration is missing, add an adapter and explicit unconfigured state rather than fake data.

- Do not delete working production-hardening controls simply to simplify implementation.

- When a requirement is ambiguous, choose the smallest safe behavior consistent with the documented product contract.

- Keep an implementation ledger: what was verified, added, changed, deferred, and blocked.

# 28. Master coding-agent prompt

Copy the following block into the coding agent. It intentionally uses imperative language and is meant to be executable as a persistent project instruction. The agent should read this document plus the repository before changing code.

You are the lead product engineer, product designer, QA engineer, and technical operator for KrishiLink 3.0.

MISSION

Transform the existing KrishiLink repository into a truthful, production-oriented agricultural trade-execution platform. The goal is NOT to add random features or build a generic marketplace. The goal is to make one complete agricultural procurement/trade journey work end-to-end and then scale it.

PRODUCT THESIS

KrishiLink should help buyers publish real procurement requirements, discover/aggregate suitable supply from farmers and FPOs, negotiate transparent terms, create a durable trade, coordinate payment/quality/logistics, track fulfillment, resolve exceptions, settle the trade, and preserve a digital Trade Passport.

IMPORTANT: Do not claim that generic marketplace + logistics + quality + payments is a unique invention. Existing systems already cover major parts of this. Differentiate by execution quality, demand-driven procurement, transparent net realization, simple farmer/FPO UX, strong trade-room workflow, and a durable transaction record.

FIRST RULE: AUDIT BEFORE MODIFYING

1\. Inspect the complete repository structure.

2\. Read AGENTS.md, README.md, PROJECT_OVERVIEW.md, PROGRESS_TRACKER.md and docs/\*.md that affect architecture or deployment.

3\. Inspect backend/app/models.py and every relevant router/service/schema/test file.

4\. Inspect every frontend page, route, shared component, API service, auth flow, and state management hook.

5\. Run the current test suite, lint, type checks, and frontend build before major changes.

6\. Record actual findings. Do not rely on README claims when the source code disagrees.

7\. Identify which flows are real, which are partial, which are mocks, and which are missing.

TRUTHFULNESS / NO-HALLUCINATION RULES

\- Never create fake fallback data that makes a failed integration appear successful.

\- Never say payment is escrowed unless an actual configured payment partner and verified flow support that statement.

\- Never fabricate market prices, delivery statuses, quality results, user verification, or government affiliation.

\- Never claim a partner integration exists unless credentials/configuration and a successful test prove it.

\- Mark unconfigured external integrations explicitly in UI and logs.

\- Never use a UI badge such as “Verified” without a defined evidence source and verification status.

\- Any algorithmic estimate must be labelled estimate/calculation, not fact.

\- Any prediction must be clearly labelled prediction and only enabled after validation.

PRESERVE THE GOOD FOUNDATION

\- Do not rewrite the FastAPI/SQLAlchemy/PostGIS foundation without evidence.

\- Preserve idempotency and concurrency protections.

\- Preserve transactional outbox architecture.

\- Preserve provenance fields for market data.

\- Preserve audit logs, request IDs, rate limiting, and access-control protections.

\- Preserve the current modular backend structure.

\- Do not delete legacy files unless explicitly justified; do not route production behavior through deprecated Flask code.

PRIMARY PRODUCT ORDER OF OPERATIONS

P0 = complete one trade.

P1 = make the trade repeatable and operable at small scale.

P2 = optimize network effects and analytics.

Do not jump to P2 before P0 is real.

P0 FUNCTIONAL JOURNEY

1\. Buyer creates a structured requirement.

2\. Farmer/FPO creates supply lot.

3\. Matching returns explainable candidates.

4\. Buyer can inspect match reasons.

5\. Buyer creates an offer.

6\. Seller can counter-offer.

7\. Both parties can communicate inside trade/offer context.

8\. Acceptance creates exactly one durable trade.

9\. Trade Room shows one source of truth and a next action.

10\. Payment flow is real or explicitly sandboxed through an adapter; no fake success.

11\. Quality workflow is invoked when required by trade configuration.

12\. Transport request is created and assigned through an operational workflow.

13\. Pickup evidence is captured.

14\. In-transit milestone is captured.

15\. Delivery evidence is captured.

16\. Buyer accepts or raises a structured dispute.

17\. Payment/settlement state is reconciled.

18\. Trade completes.

19\. Notifications, audit timeline, and operator queue reflect the journey.

20\. Trade Passport is available to authorised participants.

CORE CONCEPTS TO IMPLEMENT

\- Buyer Requirement

\- Supply Lot

\- Match

\- Offer / Counter-offer

\- Trade

\- Trade Term Snapshot

\- Conversation / Message

\- Payment

\- Quality Inspection

\- Transport Request / Assignment / Checkpoints

\- Documents / Evidence

\- Dispute

\- Trade Event / Audit Timeline

\- Reputation signals

\- Operator Task / Exception Queue

TRADE ROOM REQUIREMENTS

The Trade Room must answer without navigating away:

\- What was agreed?

\- How much?

\- What is the price and estimated net/landed value?

\- What is the current status?

\- Who must act next?

\- What quality evidence exists?

\- What is the logistics status?

\- What is the payment status?

\- What documents/evidence exist?

\- How can I contact the other party in the allowed channel?

\- What happens if something goes wrong?

NEXT-ACTION PRINCIPLE

Every active trade must expose one highest-priority next action, its owner, and a due time if one exists. Examples:

\- Buyer: complete payment

\- Seller: confirm pickup

\- Operator: assign transporter

\- QC provider: upload report

\- Buyer: accept delivery

\- Operator: resolve payment mismatch

BUYER-FIRST DEMAND WORKFLOW

Build demand as a first-class workflow, not a hidden backend entity.

Buyer requirement fields should include:

\- commodity / variety

\- minimum and target quantity

\- optional maximum quantity

\- target price/range

\- quality requirements

\- sourcing geography

\- required supply window

\- delivery window

\- storage/packaging requirements

\- partial fulfillment allowed or not

\- aggregation allowed or not

SUPPLY ASSEMBLY

Support both direct and aggregated fulfillment.

A buyer requirement may be fulfilled by one lot or multiple lots.

Show:

\- required quantity

\- committed quantity

\- remaining gap

\- seller/FPO breakdown

\- estimated landed cost

\- quality evidence status

\- concentration/risk indicators when enough data exists

Never imply a supply plan is guaranteed until counterparties commit.

MATCHING

Keep the current explainable 7-factor engine as a foundation, but evolve it carefully.

Separate hard constraints from soft ranking.

Hard incompatibility examples:

\- impossible delivery window

\- explicit quality failure

\- inactive lot

\- unavailable quantity

Soft ranking examples:

\- price proximity

\- estimated landed cost

\- reliability

\- distance

\- concentration risk

Use sample sizes for reliability metrics.

Unknown data must not be treated as a successful match.

COMMUNICATION

Do not start with unrestricted site-wide chat.

Use trade/offer-scoped conversation.

Messages must have:

\- sender

\- timestamp

\- context

\- body

\- optional attachments

\- moderation/report capability

System events must be visually distinct and immutable.

Contact sharing should be controlled and configurable.

LOGISTICS

Do not build a giant national truck marketplace in P0.

Implement a provider-neutral operational workflow:

requested -\> quoting/assignment -\> pickup scheduled -\> pickup -\> transit -\> destination -\> delivered

Support exceptions:

\- no provider

\- cancellation

\- delay

\- vehicle incident

\- quantity mismatch

\- destination refusal

Capture evidence and checkpoints.

GPS is optional. Milestone truth is mandatory.

QUALITY

Do not assume A/B/C is enough for real procurement.

Create configurable commodity-quality schemas.

Support:

requested -\> assigned -\> sample collected -\> testing -\> result -\> finalised

Results must distinguish:

\- declared

\- measured

\- verified

\- unknown

A failed inspection cannot silently become a pass.

PAYMENTS

Use an adapter architecture.

The application is not the bank.

Never store unnecessary card credentials.

Use provider references and webhooks.

Webhook processing must be authenticated and idempotent.

Internal transaction states must be reconciled against provider states.

If no provider is configured, show sandbox/test status honestly.

DISPUTES

Any material trade can enter a dispute state.

Dispute screen must show:

\- reason code

\- description

\- disputed quantity/value

\- evidence checklist

\- timeline

\- response deadline if one exists

\- resolution state

Operator/admin actions must be audited.

TRADE PASSPORT

Persist the full trade history:

identity, commercial terms, quality, logistics, payment, documents, evidence, communication summary, exceptions, outcome, and derived reliability metrics.

The Trade Passport is the durable record that makes the platform operationally valuable.

FPO SUPPORT

FPO is a strategic role, not a cosmetic dashboard.

Support aggregation and member-linked quantity allocation.

Do not expose member information outside authorised contexts.

Design for one FPO to help satisfy one buyer requirement across many member lots.

GOVERNMENT READINESS

Do not claim official government status.

Provide clean exports/APIs, source metadata, auditability, aggregated dashboards, privacy controls, and configurable program metadata.

Future integrations may include public networks or government systems only after actual requirements and data-sharing arrangements are known.

UX PRINCIPLES

\- Fewer concepts visible at once.

\- Show current state + next action before history.

\- Progressive disclosure.

\- Plain language for farmers.

\- Business-grade density for buyers/operators.

\- Mobile-friendly interactions.

\- Regional-language-ready labels and content.

\- Never hide cost components.

\- Never hide stale-data warnings.

\- Do not use dark patterns.

HOME DASHBOARD PRINCIPLE

The home page must feel like an operations dashboard, not a brochure.

Farmer:

\- action required

\- active trades

\- market snapshot

\- buyer demand

\- lot status

Buyer:

\- open requirements

\- supply gap

\- active trades

\- supplier recommendations

\- action queue

FPO:

\- member supply

\- aggregated commitments

\- open trades

\- payout/fulfillment view

Operator:

\- exceptions

\- stuck trades

\- payment/QC/logistics queues

\- disputes

DATA / PRICE RULES

Show source, date, freshness, and quality of market data.

Do not present synthetic history as observed history.

When ingestion fails, expose explicit stale/error state.

SECURITY

Audit every critical mutation.

Protect all object access.

Use role + ownership checks.

Keep private documents private.

Rate-limit sensitive actions.

Use secure file uploads and signed access URLs.

ENGINEERING PROCESS

For each feature:

1\. inspect existing code

2\. design smallest compatible change

3\. implement backend/domain logic

4\. update migrations if needed

5\. update API schemas/routes

6\. update frontend flow

7\. add loading/empty/error/success states

8\. add notifications/events

9\. add tests

10\. run lint/type/build/test

11\. manually verify the end-to-end UI path

12\. update documentation and implementation ledger

NO DEAD ENDS

Every CTA must lead to a functional next step or an honest disabled state with reason.

Never leave buttons that only update local UI.

Never show a “completed” badge when only a mock operation happened.

NO DUPLICATED DOMAIN LOGIC

Centralize state transitions and calculations in services.

Do not reimplement payment status logic in multiple frontend components.

Do not duplicate price calculations across pages.

Do not let clients decide authoritative transaction state.

PERFORMANCE

Avoid N+1 queries.

Use appropriate PostGIS indexes.

Paginate lists.

Cache read-heavy reference data carefully.

Do not cache mutable payment/transaction truth without reconciliation.

TESTING

Minimum required before calling P0 done:

\- unit tests for new domain rules

\- API authorization tests

\- concurrency/idempotency tests

\- happy-path E2E

\- payment failure/retry tests

\- logistics exception tests

\- QC failure tests

\- dispute tests

\- frontend build/lint

\- migration upgrade path

DEFINITION OF DONE

A capability is done only when:

\- a user can initiate it from the UI

\- backend validates and persists it

\- permissions work

\- events/notifications work where relevant

\- downstream integrations are real or explicitly sandboxed

\- failure states work

\- tests cover it

\- auditability exists

\- documentation is updated

\- deployment configuration is coherent

PRIORITISATION

P0: complete Trade Room and one real trade.

P1: recurring procurement, FPO aggregation, quality/document maturity, operator tooling.

P2: advanced optimisation, finance partners, network interoperability, government analytics.

DO NOT BUILD YET

\- nationwide logistics marketplace

\- proprietary lending/wallet/escrow custody

\- generic social network

\- generic chatbot as flagship feature

\- unvalidated crop forecasting

\- dozens of integrations before the trade loop works

\- blockchain unless a concrete partner/regulatory/business requirement appears

FINAL BEHAVIOR

When a request from the project owner is underspecified, choose the smallest implementation that moves the end-to-end trade journey forward while preserving truthfulness and backwards compatibility.

If a requested feature would create false real-world claims, implement the interface and adapter boundary but expose the unavailable state honestly.

When competing products already provide a capability, improve usability, integration, explainability, reliability, or focus rather than falsely claiming novelty.

# 29. Phase-by-phase execution prompts

## Phase 0 - Audit and baseline

Audit the entire repo and run all current tests/builds. Produce a machine-readable implementation ledger of existing, partial, mocked, missing, and broken capabilities. Do not change product behavior except to repair clearly broken baseline issues. Output the ledger in docs/IMPLEMENTATION_LEDGER.md and preserve evidence.

## Phase 1 - Trade Room foundation

Implement the Trade aggregate/orchestration layer around the existing Transaction model. Add immutable TradeTermSnapshot and TradeEvent. Create the Trade Room API and frontend route. Migrate the current Orders/Transactions experience into a real trade detail page with current state, next action, commercial terms, money, timeline, and linked entities. Preserve backward compatibility.

## Phase 2 - Buyer Requirements UI

Build the complete buyer demand workflow using the existing BuyerRequirement model. Add create/edit/archive/list/detail pages. Add full/partial/aggregate fulfillment status. Connect requirement matching to visible results. Do not invent buyer demand data.

## Phase 3 - Conversation

Add trade/offer-scoped Conversation and Message models plus API and frontend. Add attachment support through the existing object-storage adapter. Protect every message by trade/participant authorization. Visually distinguish system events from human messages.

## Phase 4 - Real transaction conversion

Make accepted offers convert into durable trades exactly once. Review reservations, lot allocations, and transaction creation for correctness. Remove any dead-end accepted-offer state. Add explicit payment-pending next action.

## Phase 5 - Payment adapter

Implement a provider-neutral PaymentAdapter interface and one sandbox provider or actual provider selected by the project owner. Build webhook verification, idempotency, reconciliation, visible provider status, failure states, and audit events. Never label test/sandbox money as real settlement.

## Phase 6 - Logistics operations

Introduce TransportRequest, Assignment, and Checkpoint workflow. Build operator-managed assignment first. Add farmer/buyer trade-room views and transporter interface if transporter role is enabled. Implement pickup/delivery proof and exception queue.

## Phase 7 - Quality workflow

Create configurable inspection workflow for the pilot commodity. Do not hard-code universal quality standards. Support declared vs measured vs verified values, inspection evidence, fail/pass/conditional outcomes, and buyer visibility.

## Phase 8 - FPO aggregation

Build supply aggregation from multiple member lots into one buyer requirement. Show contribution-level traceability where authorised. Add allocation and fulfilment reconciliation. Keep member financial disbursal semantics separate unless legally/operationally defined.

## Phase 9 - Operator control tower

Build exception-first queues for payments, logistics, QC, disputes, verification, and stuck trades. Add prioritisation, ownership, SLA timestamps where defined, and action completion.

## Phase 10 - Reliability and reputation

After sufficient completed trades exist, implement observable reliability metrics with sample sizes. Do not create arbitrary scores before data exists. Surface metrics in buyer and seller views with definitions.

## Phase 11 - Documents and trade passport

Implement durable document records for agreement, invoice, QC, weighment, pickup, delivery, and dispute evidence. Build Trade Passport view with permissioned downloads and audit history.

## Phase 12 - Pilot hardening

Run synthetic and real pilot workflows, measure friction and failure rates, optimise mobile UX, performance, notification reliability, and operator tooling. Document what real users reject or misunderstand.

## Phase 13 - Interoperability and government readiness

Only after pilot success, add versioned exports/APIs, aggregated dashboards, partner integration boundaries, and potential ONDC/government integration adapters. No claims of official status without formal integration.

# 30. Product acceptance checklist

| **ID** | **Capability**       | **Requirement**                                                                               | **Acceptance evidence**                                                            | **Priority** |
|--------|----------------------|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|--------------|
| P0-01  | Buyer requirement    | A buyer can create a requirement with quantity, quality, geography, and delivery constraints. | Requirement survives refresh; appears in buyer workspace; matching can consume it. | P0           |
| P0-02  | Supply lot           | Farmer/FPO can create a valid lot.                                                            | Lot is persisted, visible, and allocatable.                                        | P0           |
| P0-03  | Match                | System produces explainable candidate matches.                                                | Candidate details identify score components and data provenance.                   | P0           |
| P0-04  | Negotiation          | Offer/counter-offer history is preserved.                                                     | Every version visible with actor/time/terms.                                       | P0           |
| P0-05  | Conversation         | Participants can communicate in trade context.                                                | Unauthorised users cannot read/send messages.                                      | P0           |
| P0-06  | Trade creation       | Accepted offer creates exactly one trade.                                                     | Retry does not duplicate allocation/trade.                                         | P0           |
| P0-07  | Trade Room           | All key transaction information is visible in one place.                                      | Current state, next action, terms, money, logistics, quality, documents, timeline. | P0           |
| P0-08  | Payment              | Payment state is connected to a real/sandbox adapter and truthful.                            | Provider failure cannot produce internal success.                                  | P0           |
| P0-09  | Logistics            | Transport workflow can be assigned and updated.                                               | Pickup and delivery checkpoints are persisted.                                     | P0           |
| P0-10  | Evidence             | Pickup/delivery evidence is uploadable and permissioned.                                      | File hash and uploader metadata persisted.                                         | P0           |
| P0-11  | Acceptance/dispute   | Buyer can accept delivery or open dispute.                                                    | Dispute is visible in trade room and operator queue.                               | P0           |
| P0-12  | Completion           | Trade reaches completed state only after required prerequisites.                              | State transition is guarded and audited.                                           | P0           |
| P0-13  | Notifications        | Important milestones notify the correct role.                                                 | Unread/action counts update correctly.                                             | P0           |
| P0-14  | Operator queue       | Stuck trades and exceptions are visible.                                                      | Queue has actionable items, not just metrics.                                      | P0           |
| P1-01  | FPO aggregation      | Multiple lots can satisfy one requirement.                                                    | Committed and remaining quantities reconcile.                                      | P1           |
| P1-02  | Quality schema       | Pilot commodity has configurable inspection structure.                                        | Declared/measured/verified states are distinct.                                    | P1           |
| P1-03  | Documents            | Trade documents have lifecycle and permissions.                                               | Documents can be uploaded/viewed/downloaded safely.                                | P1           |
| P1-04  | Reliability          | Observed metrics show counts and denominators.                                                | No arbitrary score without data.                                                   | P1           |
| P1-05  | Recurring demand     | Buyer can repeat a requirement.                                                               | System can create or reopen a new sourcing cycle without duplicating trade data.   | P1           |
| P2-01  | Interoperability     | Stable exports and versioned APIs exist.                                                      | Schemas documented and backward compatible.                                        | P2           |
| P2-02  | Government analytics | Aggregated dashboard can be generated without PII leakage.                                    | Automated privacy tests/fixtures pass.                                             | P2           |

# 31. Competitor evidence and reference links

The following sources were checked for the competitive and policy assertions in this document. The list favours official/first-party sources and is intentionally conservative. Market capabilities change; re-verify before using claims in investor or government material.

**e-NAM - FPOs —** [<u>Open source</u>](https://enam.gov.in/stakeholders-Involved/fpos)  
FPO aggregation, member linkage, payment dashboard concepts.

**e-NAM - Traders —** [<u>Open source</u>](https://enam.gov.in/stakeholders-Involved/traders)  
Buyer/trader registration, quality, payments, electronic trading.

**e-NAM - Assaying —** [<u>Open source</u>](https://enam.gov.in/web/commodity/assaying)  
Quality assaying and commodity-specific testing context.

**e-NAM - Registration / Logistics —** [<u>Open source</u>](https://enam.gov.in/resources/registration-guideline)  
Logistics module and onboarding guidance.

**e-NAM - Revised operational guidelines —** [<u>Open source</u>](https://enam.gov.in/web/assest/download/Revised-Operational-Guidelines-of-e-NAM.pdf)  
Trade confirmation, invoice, payment, delivery, settlement, dispute-related operational rules.

**AgriBazaar - Buying / services —** [<u>Open source</u>](https://trade.agribazaar.com/services/buying)  
Payments, financing, quality, warehousing, logistics, settlement.

**AgriBazaar - Marketplace —** [<u>Open source</u>](https://www.agribazaar.com/our-products/marketplace)  
Marketplace/trade workflow and service integration.

**Arya.ag / IFC 2025-26 —** [<u>Open source</u>](https://www.ifc.org/en/pressroom/2026/ifc-and-technology-led-agri-platform-arya-ag-partner-to-boost-farmer-incomes-and-s)  
Scale, storage, market linkage, finance, logistics, FPO ecosystem.

**Aryadhan —** [<u>Open source</u>](https://aryadhan.in/)  
Finance and value-chain relationship with Arya.ag.

**Ninjacart —** [<u>Open source</u>](https://www.ninjacart.in/)  
Network scale, payment/quality/logistics/real-time information focus.

**WayCool logistics/distribution —** [<u>Open source</u>](https://waycool.in/logistic-distribution-solution)  
Demand-driven supply chain and end-to-end operations.

**DeHaat / NITI Frontier Tech —** [<u>Open source</u>](https://frontiertech.niti.gov.in/story/dehaats-ai-enabled-agriculture-network-driving-market-access-and-efficiency-for-1-8-million-farmers/)  
Hybrid digital + physical network and market linkage context.

**ONDC Buyer Network Participants —** [<u>Open source</u>](https://ondc.org/pages/buyer-network-participants.html)  
Buyer-side network participant model and search/match interface principles.

**ONDC Resources —** [<u>Open source</u>](https://ondc.org/pages/resources.html)  
Network governance, technical, financial and participant resources.

**Agriculture Infrastructure Fund guidelines —** [<u>Open source</u>](https://agriinfra.dac.gov.in/Content/DocAttachment/FINALSchemeGuidelinesAIF.pdf)  
Eligibility examples for post-harvest management, e-marketing, warehouses, cold chain, assaying, logistics.

**RBI - Payment Aggregators draft directions press release —** [<u>Open source</u>](https://systemhealth.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx_prid%3D57713%282%29.html)  
KYC, escrow and payment-aggregation regulatory context.

# 32. Appendix: detailed product language and copy guidelines

## 32.1 Core language

| **Avoid**                | **Prefer**                                                                                               |
|--------------------------|----------------------------------------------------------------------------------------------------------|
| Escrowed with KrishiLink | Payment committed / payment confirmed by partner / settlement pending                                    |
| AI says this is best     | Recommended because: crop fit, price fit, quantity fit...                                                |
| Verified farmer          | Identity / business verification status with date/source                                                 |
| Live price               | Latest available observation, with timestamp and source                                                  |
| Guaranteed delivery      | Scheduled / planned delivery; confirmed only when operational evidence exists                            |
| Trust score 93           | 18 completed trades; 94% on-time delivery (observed)                                                     |
| 100% secure              | Use specific security controls and provider certifications where applicable; do not make absolute claims |

## 32.2 Farmer-friendly labels

- What you can earn

- Buyer wants this crop

- Offer received

- Trade confirmed

- Payment status

- Truck status

- What you need to do next

- Problem with this delivery?

## 32.3 Buyer-friendly labels

- Post a requirement

- Supply available

- Build a supply plan

- Estimated landed cost

- Quality evidence

- Supplier reliability

- Fulfilment status

- Accept delivery / raise issue

# 33. Appendix: implementation ledger template

Feature ID: P0-07

Feature: Trade Room

Evidence class: R1/P1

Existing evidence:

\- Transaction model exists

\- Transaction status transitions exist

\- TransactionsPage exists

Missing evidence:

\- durable trade aggregate

\- trade-scoped conversation

\- complete timeline event model

\- logistics checkpoints

\- document bundle

\- next-action engine

Implementation:

\- \[ \] domain service

\- \[ \] DB migration

\- \[ \] API

\- \[ \] frontend

\- \[ \] notifications

\- \[ \] audit

\- \[ \] tests

\- \[ \] deployment config

Truth status:

NOT COMPLETE

Notes:

Do not mark complete until the E2E journey passes.

# 34. Appendix: release gate

33. Repository baseline and migration path are known.

34. No hidden fake data path exists for the release-critical workflow.

35. Critical state transitions are domain-controlled.

36. Role/ownership authorization is tested.

37. Payment behavior is truthful and partner-backed or clearly sandboxed.

38. Trade Room completes the real journey.

39. Operator queue can resolve common exceptions.

40. Evidence is permissioned and auditable.

41. Price data shows source/freshness.

42. Frontend has empty/loading/error states.

43. CI, tests, lint, build, migration checks are green.

44. A pilot operator can explain every active trade from one screen.

# 35. Final product principle

KrishiLink becomes valuable when a farmer or FPO can say “I sold this and I always knew what was happening next,” and a buyer can say “I needed this quantity by this date and KrishiLink helped me source and complete it.” Everything else in the product should reinforce those two outcomes. The platform should become deeper in the execution layer, not wider for the sake of feature count.
