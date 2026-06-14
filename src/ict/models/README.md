# Models

Full trading strategies, grouped by author (`ict/`, `romeo/`, `merchant/`), plus the reusable `intermediate/` compositions they share.

> Referenced from `CLAUDE.md`. Read this when writing a new model or adding a new strategy. The three-layer placement rules and the code/semantic-layer sync rule live in `CLAUDE.md` itself.

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
