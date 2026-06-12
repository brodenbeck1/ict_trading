# ICT Trading — Claude Context

## Project Overview

Futures trading research project implementing ICT (Inner Circle Trader) concepts on ES, NQ, and YM continuous contracts. The workflow is:
1. Extract a trading idea (from video/notes) using `/strategy-from-transcript`
2. Formalize rules into a model class (following the pattern below)
3. Backtest the model against historical 1m data
4. Analyze results and iterate

---

## Data

**Files** (all in `/Data/`):
| File | Instrument | Rows | Date Range |
|---|---|---|---|
| `es_futures_1m_cleaned.csv` | S&P 500 (ES) | ~5.4M | 2010-06-06 → 2025-11-17 |
| `nq_futures_1m_cleaned.csv` | Nasdaq (NQ) | ~5.2M | 2010-06-06 → 2025-11-17 |
| `ym_futures_1m_cleaned.csv` | Dow Jones (YM) | ~5.2M | 2010-06-06 → 2025-11-17 |

**Schema**: `timestamp, rtype, publisher_id, instrument_id, open, high, low, close, volume, symbol`

**Timestamps**: UTC. Market sessions in UTC:
- Asia: 18:00 – 00:00 (previous day's evening)
- London: 03:00 – 08:00
- New York: 13:30 – 20:00 (RTH); 08:00 – 13:30 (pre-market)
- Regular Trading Hours (RTH): 13:30 – 20:00 UTC

**Version control**: the cleaned CSVs and `raw/` downloads are **gitignored** (~1.1 GB, regenerable from the `Data/prep/` databento pipeline); `Data/prep/.env` (API key) is never committed; only `Data/prep/` is tracked. A 1000-row NQ slice lives in `tests/fixtures/` so tests run without the full dataset.

**Loading data** — use `DataLoader` from the installed `ict` package (`pip install -e .` once):

```python
from ict import DataLoader

loader = DataLoader(timeframe='5T', weeks=52, data_dir='Data')   # last 52 weeks of 5m bars
nq = loader.read_NQ()   # returns DataFrame with DatetimeIndex
es = loader.read_ES()
ym = loader.read_YM()

# Timeframe strings: '1T'=1m, '5T'=5m, '15T'=15m, '1H'=1h, '4H'=4h, 'D'=daily
# (legacy 'T'/'H' aliases are normalized internally for pandas >= 2.2)
```

`DataLoader` has no reliable default location — pass `data_dir` pointing at the repo's `Data/`:
```python
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))  # from examples/ or backtests/
loader = DataLoader(timeframe='5T', data_dir=data_dir)
```

---

## Project Structure

```
ict_trading/                              # repo root (git, pyproject.toml, .venv/)
├── Data/                                 # price data — gitignored except prep/ (see Data section)
│   ├── *_futures_1m_cleaned.csv          #   ~1.1 GB cleaned continuous contracts (untracked)
│   ├── raw/                              #   databento .zst downloads (untracked)
│   └── prep/                             #   data acquisition pipeline, databento (TRACKED)
├── knowledge/                            # semantic layer: concept libraries (markdown + YAML frontmatter)
│   ├── ict/                              #   ICT concepts + named models (7 category folders)
│   ├── romeo/                            #   Romeo — Candle Range Theory (CRT)
│   └── currency-merchant/                #   Kishane — Time Theory / 90-min cycles / Rules of Engagement
├── src/ict/                              # the installable package  (pip install -e .)
│   ├── registry.py                       #   @concept decorator + frontmatter loader + lineage graph
│   ├── data/loader.py                    #   DataLoader
│   ├── concepts/                         #   primitive detectors (single-concept, no orchestration)
│   ├── models/intermediate/              #   multi-concept compositions used by full models
│   └── models/{ict,romeo,merchant}/      #   full trading models, grouped by author
├── strategies/notes/                     # human strategy write-ups (output of /strategy-from-transcript)
├── backtests/                            # backtest runner scripts (write outputs to results/)
├── examples/                             # minimal scripts that verify a model runs
├── scripts/                              # utilities: lineage.py, read_data.py, print_daily_bars.py
├── tests/                                # pytest: registry coverage + detector smoke (+ fixtures/)
├── legacy/                               # superseded orphan modules — NOT imported (see legacy/README.md)
├── results/                              # backtest outputs — gitignored
├── pyproject.toml
└── CLAUDE.md
```

**Three-layer architecture** — enforced by where files live:

| Layer | Location | Rule |
|---|---|---|
| **Concept** | `src/ict/concepts/` | Implements exactly one KB concept; no imports from other concepts |
| **Intermediate** | `src/ict/models/intermediate/` | Composes 2+ concepts into a reusable gate/signal (e.g. `daily_bias`) |
| **Model** | `src/ict/models/<author>/` | Full trading strategy; composes concepts + intermediate models |

The markdown in `knowledge/` is the **semantic layer**: one file per concept, each with
frontmatter (`name`, `aliases`, `category`, `related`, `parameters`, `detection`) and a
"Detection Rules" section. `src/ict/registry.py` binds it to code:

- Register a detector with `@concept("<slug>")`.
- Declare dependencies with `@concept("<slug>", depends_on=["other-slug", ...])` — this powers the lineage graph.
- `tests/test_registry_coverage.py` fails if a concept's `detection:` flag and registered detectors disagree.
- Pull default config from frontmatter with `ict.registry.params("<slug>")`.
- Query the dependency tree: `ict.registry.lineage("<slug>")` returns the transitive dict; `ict.registry.mermaid("<slug>")` returns a Mermaid string.
- Regenerate the README diagram: `.venv/bin/python scripts/lineage.py --update-readme`.

> **Code and semantic layer stay in sync — always.** The `knowledge/` markdown is the
> spec; the detector is its implementation. **Whenever a detector's logic changes —
> especially a correction the user gives to detection rules, thresholds, timing, or a
> pool/validity condition — update the matching `knowledge/` file in the *same* change.**
> Reflect the new rule in the "Detection Rules" section (and `parameters:` frontmatter if
> a value changed). A code fix without the corresponding knowledge update is incomplete and
> leaves the spec lying. If a correction spans concepts (e.g. a liquidity rule touching the
> sweep, the opening range, and a model), update every affected file.

---

## Model Pattern

Every trading model follows this structure:

```python
from dataclasses import dataclass
import pandas as pd

@dataclass
class MarketSnapshot:
    df: pd.DataFrame              # primary instrument (1m or resampled)
    correlated: dict              # {'ES': df_es, 'NQ': df_nq, 'YM': df_ym} for SMT
    higher_timeframe_df: pd.DataFrame  # daily or 4H for bias context

class MyModel:
    def __init__(self, config: dict = None):
        self.checks = []
        self.config = config or {}

    def log(self, item: str):
        self.checks.append(item)

    def generate_signal(self, snapshot: MarketSnapshot) -> dict:
        # Return dict with at minimum:
        # { 'actionable': bool, 'direction': 'long'|'short'|None,
        #   'entry': float, 'stop': float, 'target': float, 'checks': list }
        ...
```

**Rule of exclusion**: if any required component is missing, `actionable=False` and no trade is taken. All checklist items must pass simultaneously.

---

## ICT Concepts Glossary

- **SMT divergence**: One correlated index makes a new extreme while others fail — signals reversal intent. Requires all three instruments (ES, NQ, YM) in the `correlated` dict.
- **Stop hunt / liquidity sweep**: Price sweeps beyond a prior high/low then reverses quickly.
- **Fair Value Gap (FVG)**: Three-candle imbalance: body of candle 1 and body of candle 3 don't overlap. Acts as magnet/reaction zone.
- **Draw on liquidity**: The next untested high/low pool price is attracted toward.
- **Market structure shift**: Break of a significant swing high/low on lower timeframe after a stop hunt.
- **OHLC / OLHC candle expectation**: Bearish day = Open→High→Low→Close sequence; Bullish = Open→Low→High→Close.
- **Devil's mark**: A prior flat open level that acts as a magnet.
- **Session liquidity pools**: Asia range high/low, London high/low, pre-market high/low — common stop hunt targets.

---

## Backtesting Conventions

**Framework**: Custom event loop (not backtesting.py or vectorbt — ICT models require multi-instrument simultaneous evaluation that those libraries don't handle cleanly).

**Position sizing**: Fixed 1 contract per trade. Instrument tick values:
- ES (micro MES): 1 tick = 0.25 pts = $1.25 | ES full: $12.50
- NQ (micro MNQ): 1 tick = 0.25 pts = $0.50 | NQ full: $5.00
- YM (micro MYM): 1 tick = 1 pt = $0.50 | YM full: $5.00

**Direction**: Both long and short signals are tested.

**Standard backtest outputs** (all models should produce):
1. Trade log CSV: `entry_time, exit_time, direction, entry_price, exit_price, stop, target, pnl, exit_reason`
2. Stats summary: total P&L, win rate, avg win/loss, profit factor, max drawdown, Sharpe ratio
3. Session breakdown: same stats sliced by Asia / London / NY
4. Equity curve plot

**Backtesting location**: runner scripts in `backtests/` (e.g. `fvg_sweep_backtest.py`); outputs are written to `results/` (gitignored). A reusable engine, when extracted, belongs in `src/ict/backtest/`.

**Walk-forward approach**: Iterate day by day. Compute daily bias once at session open. Apply intraday signals on 5m bars within that day's session window. One trade per day (the model's rule of exclusion limits entries).

---

## Adding a New Strategy

1. Run `/strategy-from-transcript` with the video transcript → review the notes file in `strategies/notes/` (and the relevant concept files under `knowledge/`)
2. Decide the layer for each new piece of logic:
   - **Single primitive** (e.g. a new session range detector) → `src/ict/concepts/<name>.py`, register with `@concept("<slug>")`
   - **Multi-concept gate** reused across models (e.g. a new bias signal) → `src/ict/models/intermediate/<name>.py`
   - **Full strategy** → `src/ict/models/<author>/<name>.py`
3. Register the entry point with `@concept("<slug>", depends_on=["dep-slug", ...])` — list every concept/intermediate it directly calls
4. Create (or update) the matching `knowledge/` markdown file; set `detection: implemented`
5. Implement `generate_signal(snapshot)` using the checklist from the notes file
6. Run `.venv/bin/python scripts/lineage.py --update-readme` to regenerate the README diagram
7. Create `examples/<strategy_name>_example.py` to verify the model runs
8. Backtest with a runner in `backtests/`; outputs land in `results/`

---

## Key Reference: Existing Plan

`.github/prompts/plan-nqBacktestFramework.prompt.md` contains the detailed backtest framework design — consult it when building or extending the backtesting engine.
