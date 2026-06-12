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
walk-forward, writes the trade-log CSV + static equity PNG to `results/<name>/`, and — if it
uses the report adapter — writes `results/<name>/<name>_report.html`.

The full NQ run loads ~1M 1m rows and can take a minute. Run it in the background and report the
summary stats (trades, win rate, P&L, profit factor, drawdown) when it finishes.

### Step 3 — Open the report

`open results/<name>/<name>_report.html` (macOS). The page has a dropdown to switch between the
Overview (equity + stats) and each trade; every trade shows a candlestick panel per timeframe with
toggleable legend groups (Entry/Stop/Target and FVG on by default; Sweep, MSS, Bias collapsed).

### Adding the report to another model's runner

The report core (`src/ict/backtest/report.py`) is model-agnostic. To wire a new model:

1. `from ict.backtest import Mark, TradeViz, build_report`
2. Write a `signal_to_marks(signal, fill, exit_info) -> list[Mark]` adapter — one `Mark` per
   overlay (`kind` = `'level'` | `'zone'` | `'marker'`), tagged with a legend `group` and the
   `panel` timeframe key. Set `default_on=False` for groups that should start collapsed.
3. Write a `trade_panels(snap, session_ts) -> {tf_key: windowed_df}` returning the candlestick
   frames for each timeframe.
4. Collect a `TradeViz(label, panels, marks, pnl)` per filled trade, then call
   `build_report(trades, panel_order, out_path, title, equity=<cumsum series>, stats=<dict>)`.

See `backtests/fvg_sweep_backtest.py` for the reference adapter.
