---
name: rules-of-engagement
aliases: [ROE, rules of engagement 1-6, OB candidate rules]
category: orderblocks
related: [gap-vi-entry, cycle-order-flow]
ict_refs: [order-block, liquidity-sweep-stop-hunt, change-in-state-of-delivery]
source_coverage: partial-public   # 6 rules exist; rules quoted publicly are listed below, remainder paywalled
parameters:
  rule_qualify: "an orderblock candidate must raid a high or low (anticipating the internal liquidity sweep)"
  rule_entry_bullish: "trade the candle following the down candle that trades back to the orderblock candidate"
detection: not-implemented
---

# Rules of Engagement (Orderblock Rules)

CM Academy's mechanical orderblock playbook — six numbered rules (the publicly quoted
ones below; the full set is in his paywalled material):

1. **Qualification — the raid rule**: an orderblock *candidate* only counts if the
   candle (or its leg) **raided a high or low** — i.e., the block was formed in the
   act of sweeping liquidity. A last-down-candle that took out a prior low before the
   up-move is a candidate; one that didn't is not. (Stricter than the base ICT OB
   definition, which requires only displacement after the block — Kishane requires
   the sweep *by* the block.)
2. **Entry — the return rule (bullish)**: when price trades back **down** to the
   candidate, you do not buy the touch — you **trade the candle *following* the down
   candle that returns to the block**. The return candle must finish; the next
   candle's behavior (holding/turning at the block) is the trigger. Mirror for
   bearish.
3. **Refinement — gap/VI override**: if the candidate's range contains a gap or
   volume imbalance, the entry level moves to the gap
   ([gap-vi-entry](gap-vi-entry.md)).

The shape is ICT-compatible (OB + sweep + confirmation candle) but packaged as hard
eligibility rules — well suited to direct codification.

## Detection Rules

- Candidate filter: ICT-library order-block detector + require
  `block_candle (or block leg) swept a registered pool/swing` (raid flag).
- Bullish entry trigger: detect the first down candle that trades into the candidate
  zone after formation; arm on its close; enter on the **next** candle (market on
  open, or on that candle taking the return candle's high — config).
- Invalidation: close through the far side of the candidate before/at the return.
- Log per-trade: raid type (which pool the block raided), return depth into the zone,
  trigger-candle direction.

## Sources

- [CM Academy outline & quoted rules — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
- [The Currency Merchant Patreon — patreon.com](https://www.patreon.com/TheCurrencyMerchant/about)
