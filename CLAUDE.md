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

**Loading data** — always use `DataLoader` (alias for `csvReader` in `ict_library`):

```python
from ict_library import DataLoader

loader = DataLoader(timeframe='5T', weeks=52)   # last 52 weeks of 5m bars
nq = loader.read_NQ()   # returns DataFrame with DatetimeIndex
es = loader.read_ES()
ym = loader.read_YM()

# Timeframe strings: '1T'=1m, '5T'=5m, '15T'=15m, '1H'=1h, '4H'=4h, 'D'=daily
```

Always pass `data_dir` when running scripts outside `trading_models/`:
```python
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Data'))
loader = DataLoader(timeframe='5T', data_dir=data_dir)
```

---

## Project Structure

```
ict_trading/
├── Data/
│   ├── es_futures_1m_cleaned.csv
│   ├── nq_futures_1m_cleaned.csv
│   ├── ym_futures_1m_cleaned.csv
│   └── prep/                      # data acquisition scripts (databento)
├── trading_models/
│   ├── ict_library/               # shared library (DataLoader, base classes, ICT utils)
│   ├── backtest/                  # backtesting engine (see Backtesting section)
│   ├── sniper/
│   │   └── daily_bias_sniper.py   # DailyBiasModel + MarketSnapshot
│   ├── liquidity_pools/
│   │   └── swing_points.py        # SwingPointScanner
│   ├── strategies/
│   │   └── notes/                 # structured strategy notes (output of /strategy-from-transcript)
│   ├── examples/
│   └── requirements.txt
└── CLAUDE.md
```

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

**Backtesting module location**: `trading_models/backtest/`

**Walk-forward approach**: Iterate day by day. Compute daily bias once at session open. Apply intraday signals on 5m bars within that day's session window. One trade per day (the model's rule of exclusion limits entries).

---

## Adding a New Strategy

1. Run `/strategy-from-transcript` with the video transcript → review the notes file in `trading_models/strategies/notes/`
2. Create `trading_models/<strategy_name>/<strategy_name>.py` following the model pattern
3. Implement `generate_signal(snapshot)` using the checklist from the notes file
4. Create `trading_models/examples/<strategy_name>_example.py` to verify the model runs
5. Backtest using `trading_models/backtest/` (see backtest module docs)

---

## Key Reference: Existing Plan

`trading_models/.github/prompts/plan-nqBacktestFramework.prompt.md` contains the detailed backtest framework design — consult it when building or extending the backtesting engine.
