---
name: daily-bias
aliases: [bias, directional bias]
category: daily-bias
related: [draw-on-liquidity, weekly-profiles, ohlc-candle-profiles, premium-discount, power-of-three, market-structure, fair-value-gap, killzones, silver-bullet, order-block]
parameters:
  bias_timeframe: "daily (bias must come from the daily chart, not lower TFs)"
  confirmation_timeframe: "4H (structural alignment check; must not contradict daily)"
  signals_required: "order flow + draw on liquidity + 4H structure must align; P/D and prior-day midpoint are reference signals"
  bias_lock: "set pre-session; never switch mid-session after manipulation phase"
  unclear_action: "skip (rule of exclusion — no trade when bias is neutral)"
detection: implemented   # ict.concepts.daily_bias — daily_bias() / daily_bias_components()
---

# Daily Bias

The expected direction of the current daily candle's expansion — bullish (expected to
expand higher) or bearish (expected to expand lower). The bias frames every intraday
decision: which liquidity pool is the day's target, which side of sweeps to fade, and
which direction entries are allowed.

ICT's bias logic is built on three **gate signals**, all read from the **daily** chart
(with 4H as structural confirmation):

1. **Order flow** — are recent daily candles delivering higher (bullish) or lower
   (bearish)? Are down-closed candles being respected as support (bullish order flow)
   or up-closed candles as resistance (bearish)?
2. **Draw on liquidity (DOL)** — which untaken pool (old high/low, relative equal
   highs/lows) is the nearest magnet? The direction of the next major draw is usually
   the direction of the day. See [draw-on-liquidity](draw-on-liquidity.md).
3. **4H structure** — do 4H bars confirm the same directional delivery? If 4H
   structure actively contradicts the daily order flow, the bias is neutral. If 4H
   is indeterminate it abstains (does not veto).

Two additional **reference signals** are computed but are not part of the gate — they
inform entry-zone selection at the model level:

- **Premium/discount** — current price position relative to the dealing range. Shorts
  favor premium arrays; longs favor discount arrays.
- **Prior-day midpoint** — did the prior day close above its own midpoint (bullish
  carry) or below (bearish carry)? A close above the prior day's midpoint or near the
  prior day's high suggests bullish continuation intent.

A common alternation rule: if price just took **internal** range liquidity (filled an
FVG inside the range), the next objective is **external** range liquidity (a range
high/low), and vice versa.

## AMD / Power of Three Context

Daily bias anchors the **Accumulation → Manipulation → Distribution** (AMD) cycle
within each session:

- **Accumulation** — price consolidates near the session open; smart money builds position.
- **Manipulation** — price sweeps the opposing pool (the fake move that runs stops on
  the wrong side). In bearish bias: a run above a buy-side pool. In bullish bias: a
  raid below a sell-side pool.
- **Distribution** — price expands in the bias direction toward the draw.

Framing the session inside AMD ensures entries are taken after the manipulation leg, not
during it.

## Detection Rules

- Compute on the daily timeframe at (or before) the session open; **lock and hold** for
  the day. Never re-evaluate or switch after the manipulation phase begins.
- **Bullish bias** requires ALL of:
  - Daily order flow bullish (net close progression higher over lookback; more up-closed
    than down-closed bars), AND
  - Nearest unmitigated draw is ABOVE current price, AND
  - 4H structure is bullish or neutral (does not show active lower highs/lower lows).
- Mirror for bearish.
- If any gate signal conflicts → bias = neutral → sit out (rule of exclusion).
- **Ranging conditions**: if order flow is neutral (alternating closes, no net
  progression), focus on support/resistance breaks rather than forcing a directional
  bias. A decisive break above an old swing high with follow-through supports a bias
  shift; absent that, remain neutral.
- Expect the day to sweep the *nearer, opposing* pool first (manipulation leg) before
  expanding toward the draw — see [power-of-three](power-of-three.md).

## Trading Application

- In **bullish bias**: seek discount PD arrays (Order Blocks, FVGs at lows) after
  a swing-low raid and MSS confirmation. Do not sell into strength.
- In **bearish bias**: seek premium arrays (Order Blocks, FVGs at highs) after a
  swing-high raid. Do not buy dips prematurely.
- Execute during Kill Zones (London/NY Open) with OTE (Optimal Trade Entry)
  confluences, strictly in the direction of the bias.
- Both **FVGs and Order Blocks** are valid entry arrays — whichever is present at the
  discount/premium zone after the sweep and MSS.
- Target opposing liquidity or the next unfilled imbalance/gap for exits.
- Bias is set pre-session and generally held for the full day; unclear bias = sit out.

## Common Mistakes

- Reading bias from 1H/15M instead of the daily chart → conflicting signals.
- **Switching bias mid-session** after the manipulation sweep (the fake-out IS the
  model; reversing bias here means trading the manipulation, not the distribution).
- Confusing current short-term price direction with bias (e.g., buying into a
  bullish candle that is deep in a bearish-bias session's premium).
- Ignoring DOL or forcing a bias in unclear/consolidating structure.
- Entering every day regardless of whether all signals align.

## Implementation Notes

- **Bias as a directional enum**: represent as `'bullish' | 'bearish' | 'neutral'`.
  Neutral is a first-class outcome, not an error — it means sit out.
- **Auto vs. manual override**: support both computed bias (from the three gate signals)
  and a `force_direction` override that bypasses the gate entirely. The override is
  used for backtesting specific setups without the daily filter.
- **Explicit timeframe parameters**: `bias_timeframe` (default `'1D'`) and
  `confirmation_timeframe` (default `'4H'`) should be config keys, not hard-coded,
  so the window can be audited and changed per instrument.
- **Hard gate in entry logic**: bias is the first filter applied each session. Any
  setup that does not match the bias direction is excluded before sweep/MSS evaluation.
- **Session lock**: bias is computed once (pre-session) and stored in session state.
  Lower-timeframe logic reads the stored value; it never triggers a recompute mid-day.
- **Unclear bias handling**: the current implementation returns `'neutral'` and skips
  the session (`bias_unclear_action: 'skip'`). Alternative values — `'reduce_size'` or
  `'range_mode'` — are valid extensions for ranging environments.
- **Reference signals in logs**: premium/discount zone and prior-day midpoint are
  logged per session alongside the gate result to support walk-forward review and
  backtest transparency, even though they are not part of the gate.
- **4H alignment**: when 4H data is not provided, the 4H signal abstains (`'neutral'`)
  and does not veto an otherwise valid daily bias. When provided, active contradiction
  (4H showing opposite structure) invalidates the bias.
- **Persistence**: store the bias value alongside its component rationale in the session
  state object so backtest reports can reconstruct why each session was skipped or traded.
- **Confluence weighting**: bias is a hard filter, not a weighted score. All gate signals
  must pass; there is no partial credit. Downstream model layers (entry arrays, R:R,
  kill zone timing) may use a scoring approach within the already-gated session.

## Sources

- [What is ICT Daily Bias — innercircletraders.net](https://innercircletraders.net/ict-daily-bias/)
- [ICT Daily Bias Explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-daily-bias-explained/)
- [Daily Bias: Identifying Market Direction — tradingfinder.com](https://tradingfinder.com/education/forex/ict-daily-bias/)
- [ICT Daily Bias mechanical framework — ttrades.com](https://ttrades.com/ict-daily-bias-most-simple-mechanical-framework/)
