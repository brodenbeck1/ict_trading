"""
Download DXY (US Dollar Index) data from Yahoo Finance and save to Data/.

Usage:
    python scripts/fetch_dxy.py

Outputs:
    Data/dxy_daily.csv  — daily bars from 2010-01-01 to present
    Data/dxy_1h.csv     — 1h bars for last 730 days (yfinance limit)
"""
import sys
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed — run: pip install yfinance")
    sys.exit(1)

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "Data"
TICKER = "DX-Y.NYB"


def _clean(df: pd.DataFrame, tz: str | None = "UTC") -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.droplevel("Ticker")
    df.index.name = "timestamp"
    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close", "volume"]]
    if tz and df.index.tz is None:
        df.index = df.index.tz_localize(tz)
    elif tz and str(df.index.tz) != tz:
        df.index = df.index.tz_convert(tz)
    return df.sort_index()


def fetch_daily() -> pd.DataFrame:
    print("Fetching DXY daily bars (2010–present)…")
    df = yf.download(TICKER, start="2010-01-01", interval="1d", progress=False)
    df = _clean(df, tz=None)
    out = DATA_DIR / "dxy_daily.csv"
    df.to_csv(out)
    print(f"  Saved {len(df)} rows → {out}")
    return df


def fetch_1h() -> pd.DataFrame:
    print("Fetching DXY 1h bars (last 730 days)…")
    df = yf.download(TICKER, period="730d", interval="1h", progress=False)
    df = _clean(df, tz="UTC")
    out = DATA_DIR / "dxy_1h.csv"
    df.to_csv(out)
    print(f"  Saved {len(df)} rows → {out}")
    return df


if __name__ == "__main__":
    fetch_daily()
    fetch_1h()
    print("Done.")
