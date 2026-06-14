# Charting Conventions

Visual standards for all concept/backtest charts produced in this project.

---

## Liquidity Raids

When drawing a liquidity level (valid pool, HPFS, or any named pool):

| State | Line style | Line end |
|---|---|---|
| **Active** (unraided) | Solid, full opacity | Extends to right edge of chart |
| **Raided** | Dotted/dashed, reduced opacity | Stops at the raid candle |

The raid candle is marked with an **X** at the level price.

**HPFS-specific**: only draw raided HPFS levels if the HPFS formed within **30 bars** before the raid. Older raided levels add clutter without signal value.

---

## Color Palette

| Element | Color |
|---|---|
| Valid buy-side pool | `#58a6ff` (blue) |
| Valid sell-side pool | `#3fb950` (green) |
| Failure string | `#f85149` (red) |
| Weekly open | `#e3b341` (gold, dashed) |
| RB HPFS bearish | `#f0883e` (orange) |
| RB HPFS bullish | `#bc8cff` (purple) |
| OB HPFS bearish | `#79c0ff` (light blue) |
| OB HPFS bullish | `#56d364` (bright green) |
| Background | `#0d1117` |
| Bullish candle | `#26a641` |
| Bearish candle | `#f85149` |

---

## Swing Markers

| Marker | Meaning |
|---|---|
| `^` triangle up | Valid buy-side swing (pool candidate) |
| `v` triangle down | Valid sell-side swing |
| `x` cross | Failure string (already swept prior) |
| `D` diamond | HPFS level candle |
| `\|` pipe | LTC (liquidity-taking candle / swing point) |
| `x` at level | Raid candle (where the level was taken) |

---

## HPFS Types

Show RB and OB HPFS in **separate panels** when comparing types side by side. When showing a single type, one panel is fine.

---

## Bar Numbering

Add bar index labels (every 5th bar) when debugging detector output — helps quickly identify which candle is being discussed.

---

## General

- Dark background (`#0d1117`) for all charts
- Grid lines off
- X-axis ticks at session/day boundaries, not every bar
- Save to `/tmp/` for quick review; move to `analysis/` when including in a write-up
