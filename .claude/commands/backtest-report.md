# Backtest Report

Run a model's backtest and open the interactive multi-timeframe Plotly report.

**Usage:**
- `/backtest-report` — run the default FVG-sweep / 2022-model backtest and open the report
- `/backtest-report <runner>` — run a specific backtest runner in `backtests/` (e.g. `fvg_sweep_backtest.py`)

## Instructions

You are running a backtest for the ICT Trading project and rendering its interactive report.

### Step 1 — Identify the runner

If `$ARGUMENTS` names a file in `backtests/`, use it. Otherwise default to `backtests/fvg_sweep_backtest.py`.
List `backtests/*.py` if you're unsure which runners exist.

### Step 2 — Run it

Use the repo venv: `.venv/bin/python backtests/<runner>.py`.
The runner loads data via `DataLoader` (pass `data_dir` = repo `Data/`), evaluates the model
walk-forward, writes the trade-log CSV + static equity PNG to `results/<name>/`, and writes
`results/<name>/<name>_report.html`.

The full NQ run loads ~1M 1m rows and takes about a minute. Run it and report the
summary stats (trades, win rate, P&L, profit factor, drawdown) when it finishes.

### Step 3 — Open the report

`open results/<name>/<name>_report.html` (macOS). The page has a dropdown to switch between the
Overview (equity + stats) and each trade; every trade shows three candlestick panels (daily / 15m / 3m)
with toggleable legend groups:
- **Entry/Stop/Target** and **FVG** — on by default
- **Sweep** and **MSS** — collapsed by default; toggle to see the pool box, touch markers, and structure break

The Sweep group includes:
- An **Opening Range box** on the 3m panel (when the swept pool is OR-high/OR-low)
- A **diamond marker** on the candle that created the pool extreme
- **Pool touch markers** on 15m for REH/REL clusters, or on the daily for PDH/PDL

### Codebase layout

```
backtests/
  fvg_sweep_backtest.py   — Model2022 runner; model-specific only:
                              build_snapshot    — slices df_1m into df_3m / df_15m / df_daily
                              trade_panels      — windowed DataFrames per timeframe for the report
                              signal_to_marks   — translates signal dict into Mark overlays
                              run_backtest()    — main walk-forward loop
  plot_trades.py          — Shared utilities imported by ALL runners:
                              localize_to, eod_utc        — timezone helpers
                              simulate_fill / exit        — limit order + stop/target simulation
                              calc_pnl_pts                — P&L calculation
                              compute_stats, print_stats  — trade statistics
                              plot_equity_curve           — static equity curve PNG
                              draw_candles, ts_to_x       — matplotlib candlestick primitives
                              plot_trade                  — per-trade matplotlib PNG (CLI tool)
src/ict/backtest/
  report.py               — model-agnostic Plotly HTML engine (Mark, TradeViz, build_report)
```

### Adding the report to a new model's runner

1. `from ict.backtest import Mark, TradeViz, build_report`
2. `from plot_trades import simulate_fill, simulate_exit, calc_pnl_pts, compute_stats, print_stats, plot_equity_curve, localize_to`
3. Write `build_snapshot(df_1m, session_ts) -> ModelSnapshot` for your model's data slicing.
4. Write `signal_to_marks(signal, fill, exit_info) -> list[Mark]` — one `Mark` per overlay
   (`kind` = `'level'` | `'zone'` | `'marker'`), tagged with a legend `group` and `panel` key.
   Set `default_on=False` for groups that should start collapsed.
5. Write `trade_panels(snap, session_ts) -> {tf_key: windowed_df}`. Include the session day bar
   in the daily panel (resample from the intraday df and concat).
6. Collect `TradeViz(label, panels, marks, pnl)` per filled trade, then call
   `build_report(trades, panel_order, out_path, title, equity=<cumsum series>, stats=<dict>)`.

See `backtests/fvg_sweep_backtest.py` for the reference implementation.
