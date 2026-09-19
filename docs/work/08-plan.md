# Work Packet 08 — FPO Core Pilot Plan

## Verified starting point

The current FPO module has an owner-scoped roster and a simple aggregated-lot helper, but it treats member `ready_quantity_qtl` as mutable inventory. It has no persisted intake ledger, receipt, pool contribution, pool lifecycle, trade-to-member chain, or payout allocation. It therefore cannot prove quantity conservation after pooling or sale.

## Architecture decisions

- Preserve the Packet 05 single-owner FPO model. Members remain FPO records, never auto-created platform users. Multi-user FPO staff authorization is deferred.
- Create an append-only operational chain: member intake → pool contribution → FPO marketplace lot → offer/trade → member trade allocation. All quantities use canonical Decimal quintals while preserving intake quantity/unit.
- Intake net quantity is server-calculated from gross minus tare; corrections create an audited adjustment and are blocked after a committed contribution.
- Pool contribution composition locks at publication. Partial sales allocate trade quantity pro-rata across contributions in deterministic contribution-ID order, with the final allocation receiving the residual cent after Decimal rounding. This preserves quantity and gross-value conservation.
- Buyer surfaces receive only the FPO lot, never member roster/contribution data.

## Verification focus

- Cross-FPO member/intake/pool authorization.
- Gross/tare/net and unit validation; intake idempotency.
- Intake/pool/trade quantity conservation, including an over-allocation attempt and partial sale.
- Trade-to-member chain and allocation gross reconciliation.
- Existing offer, Trade Room and Packet 07 requirement regressions.
