# ICT Trading Library

A comprehensive Python library for Inner Circle Trader (ICT) trading concepts and strategies.

## 📚 Overview

This library implements core ICT trading concepts including:
- Market structure analysis (swing points, break of structure)
- Liquidity identification and tracking
- Daily bias model with SMT divergence
- Fair value gaps (coming soon)
- Order blocks (coming soon)
- Session-based analysis (coming soon)

## 🏗️ Structure

```
trading_models/
├── ict_library/           # Main library package
│   ├── core/              # Core ICT concepts
│   │   └── market_structure.py
│   ├── models/            # Trading models
│   │   └── daily_bias.py
│   ├── session/           # Session analysis (coming soon)
│   └── utils/             # Utilities
│       └── data_loader.py
├── examples/              # Usage examples
│   ├── swing_points_example.py
│   └── daily_bias_example.py
└── requirements.txt
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

**1. Load Data and Identify Swing Points:**

```python
from ict_library import SwingPointScanner, DataLoader

# Load 4 weeks of 15-minute data
loader = DataLoader(timeframe='15T', weeks=4)
df = loader.read_NQ()

# Identify swing points
scanner = SwingPointScanner(df, lookback=2)
swings = scanner.identify_swings()

# Get liquidity levels
liquidity = scanner.get_liquidity_levels()
print(f"Buy stops: {len(liquidity['buy_stops'])}")
print(f"Sell stops: {len(liquidity['sell_stops'])}")
```

**2. Daily Bias Analysis:**

```python
from ict_library import DailyBiasModel, MarketSnapshot, DataLoader

# Load data
loader_5m = DataLoader(timeframe='5T', weeks=2)
loader_daily = DataLoader(timeframe='D', weeks=12)

# Create market snapshot
snapshot = MarketSnapshot(
    df=loader_5m.read_NQ(),
    correlated={
        'NQ': loader_5m.read_NQ().tail(100),
        'ES': loader_5m.read_ES().tail(100),
        'YM': loader_5m.read_YM().tail(100)
    },
    higher_timeframe_df=loader_daily.read_NQ()
)

# Generate bias
model = DailyBiasModel()
result = model.generate_bias(snapshot)

print(f"Bias: {result['bias']}")
print(f"Actionable: {result['actionable']}")
```

## 📖 Documentation

### Core Modules

#### `SwingPointScanner`

Identifies swing highs and lows using ICT methodology:
- `identify_swings()` - Find all swing points
- `get_recent_swings(n=5)` - Get N most recent swings
- `get_liquidity_levels()` - Extract buy/sell stop levels
- `find_relative_equal_highs/lows()` - Find liquidity clusters

#### `DailyBiasModel`

Implements ICT daily bias checklist:
- Expected daily candle structure (OHLC vs OLHC)
- Stop hunt detection
- SMT divergence validation
- Market structure shift confirmation
- Liquidity target identification

#### `DataLoader`

Load and resample futures data:
- `read_NQ()` - Nasdaq 100 futures
- `read_ES()` - S&P 500 futures
- `read_YM()` - Dow Jones futures
- Flexible timeframe resampling
- Date range filtering

## 📊 Examples

See the `examples/` directory for complete working examples:
- `swing_points_example.py` - Market structure analysis
- `daily_bias_example.py` - Daily bias model

Run examples:
```bash
python examples/swing_points_example.py
python examples/daily_bias_example.py
```

## 🔮 Coming Soon

- Fair Value Gaps (FVG) detection
- Order blocks and breaker blocks
- Break of Structure (BOS) / Change of Character (CHoCH)
- Killzone identification (London/NY)
- Session liquidity analysis
- Optimal Trade Entry (OTE) levels
- Power of Three model

## 📝 Requirements

- Python 3.8+
- pandas
- numpy

## 🤝 Contributing

This is a personal trading library. Feel free to fork and adapt to your needs.

## ⚠️ Disclaimer

This library is for educational and research purposes only. Trading involves substantial risk of loss. Always do your own research and never risk more than you can afford to lose.
