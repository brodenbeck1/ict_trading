# Charts

Visual outputs organized by concept. Each concept has its own subfolder.

---

## Folder structure

```
charts/{concept}/{concept}-{instrument}-{date_from_instrument}.png
```

Examples:
```
charts/dxy-weekly-bias/dxy-weekly-bias-DXY-2024-01-07.png
charts/hpfs/hpfs-NQ-2024-06-03.png
charts/pool-validity/pool-validity-NQ-2024-06-03.png
```

- **`{concept}`** — concept slug matching `knowledge/` (e.g. `dxy-weekly-bias`, `hpfs`, `pool-validity`)
- **`{instrument}`** — ticker being charted (e.g. `DXY`, `NQ`, `ES`)
- **`{date_from_instrument}`** — the **start date of the data shown** in the chart (not today's date), format `YYYY-MM-DD`

---

## Subfolders

| Folder | Concept | Script |
|---|---|---|
| `dxy-weekly-bias/` | DXY weekly swing reactions — MSS and CISD at raided pools | `chart_dxy_mss.py`, `chart_dxy_bag.py`, `chart_dxy_dark_pool.py`, `chart_dxy_swing_classification.py` |
| `hpfs/` | High Probability Failure Swing detection (RB and OB variants) | — |
| `ob/` | Order Block — body liquidity sweep + validation candle | `chart_ob.py` |
| `pool-validity/` | Valid liquidity pools and failure string filter | — |

---

## Scripts

Charting scripts live **in this folder** (`charts/`), not in `scripts/`. Run them from the repo root:

```
python charts/chart_ob.py
python charts/chart_dxy_mss.py
```

Each script outputs to its matching subfolder.

---

## Conventions

Follow `scripts/CHARTING.md` for all style rules (colors, raid lines, dark background, etc.).

Charts saved here are for write-ups and reference. Quick exploratory charts go to `/tmp/` first.
