# ICT Library Examples

This directory contains example scripts demonstrating how to use the ICT trading library.

## Available Examples

### 1. Swing Points Example (`swing_points_example.py`)

Demonstrates market structure analysis:
- Identifying swing highs and lows
- Finding liquidity levels
- Detecting relative equal highs/lows (liquidity clusters)

**Run:**
```bash
python examples/swing_points_example.py
```

### 2. Daily Bias Example (`daily_bias_example.py`)

Demonstrates the ICT daily bias model:
- Expected daily candle structure analysis
- Stop hunt detection
- SMT divergence validation
- Actionable trade setup determination

**Run:**
```bash
python examples/daily_bias_example.py
```

## Requirements

Ensure you have installed the required dependencies:
```bash
pip install -r requirements.txt
```

## Data Requirements

Examples expect data files in `~/Projects/Data/`:
- `nq_futures_1m_cleaned.csv`
- `es_futures_1m_cleaned.csv`
- `ym_futures_1m_cleaned.csv`

Adjust the `data_dir` parameter in DataLoader if your data is in a different location.
