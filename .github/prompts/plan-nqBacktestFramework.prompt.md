# Plan: Build NQ Backtest Framework for Daily Bias Model

**Overview**: Create a backtester that runs the DailyBiasModel across historical NQ 1-minute data, tracking entries/exits, position P&L, and performance metrics. The system will walk forward through time, validating each trading signal against the model's "rule of exclusion" (all checks must pass simultaneously).

## Steps

1. Create `backtest.py` with a `Backtester` class that orchestrates: load NQ/ES/YM data via `DataLoader`, generate daily bias signals for each date, and track position entries/exits with P&L.

2. Implement position lifecycle: entry at signal (with stop/target from liquidity levels), track intraday execution, exit at target/stop/EOD, and calculate trade P&L with optional slippage/commissions.

3. Build walk-forward engine: iterate through daily windows, recalculate daily bias once per day, apply intraday signals across multiple timeframes (configurable 5m/15m/1h), and append results to a trades ledger.

4. Add performance reporting: summary stats (total P&L, win rate, max drawdown, Sharpe ratio), daily/monthly return attribution, and a trade-by-trade CSV export for analysis.

5. Create `run_backtest.py` entry script that configures parameters (date range, timeframe, position size, slippage), runs the backtest, and generates plots/reports.

6. Add optional tear-sheet generation: visualize equity curve, drawdown, monthly returns, and win/loss distribution to validate strategy performance.

## Further Considerations

1. **Timeframe selection**: Should backtest run on 5m, 15m, 1h, or all? Recommend starting with 5m (closest to original model design) then optimizing.

2. **Position sizing**: Fixed $ per trade, fixed # of contracts (ES micro = 1 tick=$5, NQ micro = 1 tick=$20), or ATR-based? Suggest starting with 1 micro contract for simplicity.

3. **Slippage/commissions**: Apply fixed slippage (e.g., 2 ticks) and per-trade commission (e.g., $5)? Recommend including both for realistic P&L.

## Data Available

- **NQ**: 2010-06-06 to 2025-11-17 (1-minute bars)
- **ES**: 2010-06-06 to 2025-11-17 (1-minute bars)
- **YM**: 2010-06-06 to 2025-11-17 (1-minute bars)
- Format: OHLCV with datetime index
- Accessible via: `DataLoader(timeframe='5T').read_NQ()` etc.

## Model Architecture Reference

**DailyBiasModel Components** (all must be True to trade):
1. Daily candle structure (bias direction: Bullish/Bearish/Neutral)
2. Stop hunt detection (prior day high/low sweep)
3. SMT divergence (intermarket confirmation)
4. Market structure shift (50-candle swing analysis)
5. Liquidity targets (300-candle range analysis)

**Output**: `{'bias': str, 'stop_hunt': str|None, 'smt': bool, 'structure_shift': bool, 'targets': dict, 'actionable': bool}`

## Implementation Notes

- Use `MarketSnapshot` dataclass to pass multi-instrument data to model
- SwingPointScanner can identify entry/exit levels from historical structure
- Walk-forward: daily bias calculated once per day, reused for all intraday candles
- Position tracking: entry price, target, stop, entry time, exit time, exit price, P&L
- Metrics: Total P&L, Win Rate, Max Drawdown, Sharpe Ratio, Consecutive wins/losses
