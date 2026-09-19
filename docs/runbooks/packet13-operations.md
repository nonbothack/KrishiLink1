# KrishiLink operations runbooks

These runbooks are safe checks only. Staff must use the typed operational endpoints and preserve the audit trail. Do not edit database rows directly, replay trade/payment commands, expose provider secrets, or mark a participant report as provider verification.

## Price ingestion failure

Check source configuration, last attempt/report date and the bounded provider error category. Preserve historical observations. Re-run only the approved scoped ingestion task after its rate floor and source contract permit it; escalate repeated failures.

## Redis or outbox backlog

Inspect backlog age and failed event category. Confirm the worker is available. Use the notification-only retry endpoint for eligible delivery events. Never replay a completed event or a domain mutation.

## SMS/OTP provider failure

Check provider state and recent failure category. Keep login fail-closed when the provider is unconfigured. Do not use arbitrary destination relay or expose OTP values.

## Web Push degradation

Inspect configured state and aggregate attempt outcomes. Disable Web Push if needed; in-app notifications remain canonical. Do not copy endpoint or encryption-key fields into tickets.

## Evidence/storage failure

Check safe evidence metadata and provider status. Do not make private objects public or ask support to bypass signed access controls.

## Payment-provider outage

Keep participant-reported payment state labelled as such. Do not mark bank/provider verified, create a UTR, or mutate agreed trade terms.

## Suspected account takeover

Use the support context projection, record the reason, revoke the user session family with step-up authentication, and create/assign a review signal. Keep the account's history and audit evidence intact.
