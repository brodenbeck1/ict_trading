'''
should it be OHLC or OLHC
locate stophunt - d1 internal high/low external high low
                  session liquidity pool asia or london or ny
Daily bias checklist (sequential)

Define expected daily candle structure: Bearish = Open High Low Close (OHLC), Bullish = Open Low High Close (OLHC). Decide which is more probable given recent untested highs/lows and current context (fair value gaps, previous day ranges).
Identify stop hunts already occurred pre‑session (Asia, London, pre‑market): External high/low taken? Internal range liquidity pool swept? Session highs/lows swept?
If no meaningful stop hunt yet, wait for liquidity engineering (a run on a prior high/low) before forming bias.
Map remaining liquidity targets: Next draw on liquidity (untouched session lows/highs, internal range pools, external range highs/lows, fair value gaps).
Require SMT (intermarket divergence) at the level that forms the turning point (stop hunt area or internal/external liquidity pool) to validate reversal intent.
Confirm market structure alignment: After SMT + stop hunt, does lower time frame structure shift toward the draw (e.g., break of short‑term swing, displacement through FVG)?
Filter by higher‑timeframe context: Within or rejecting daily / 4H fair value gaps, flat body opens (devil’s mark), prior day range boundaries.
News filter: On non‑news days wait for first 15‑minute candle print before committing; on news days adjust for volatility or stand aside.
Rule of exclusion: If any critical component missing (validated stop hunt + SMT + structure + clear liquidity target), do nothing.
Execution only when daily bias (expected candle form) aligns with intraday setup and liquidity path.
Key components definitions

External range high/low: Major swing extremes (previous significant daily highs/lows).
Internal range liquidity pool: Consolidation range highs/lows formed after an external move (targets during retracements).
Stop hunt: Liquidity sweep beyond a prior high/low that quickly reverses.
SMT divergence: One correlated index takes a high/low while others fail (or prints lower high vs higher high) signaling potential reversal.
Draw on liquidity: Next logical pool price is attracted to (untouched highs/lows, gaps).
Fair Value Gap (FVG): Imbalance zone; used as reaction/continuation level, often hosts SMT.
Flat body open (devil’s mark): Prior flat open level acting as magnet/reversal zone.
Decision tree (condensed)

Has a stop hunt occurred? If yes → look for SMT at that level. If SMT confirmed → define next liquidity draw → wait for structure shift → execute toward draw. If no stop hunt → wait.
Candle expectation: If multiple consecutive highs taken without daily lows violated → anticipate bearish (Open High Low Close) retracement into internal liquidity before external continuation; inverse for sustained lows without highs.
Invalid trade if SMT absent at proposed reversal point.
'''

import pandas as pd
from dataclasses import dataclass

@dataclass
class MarketSnapshot:
    df: pd.DataFrame            # 1m or 5m data with columns: open, high, low, close, volume
    correlated: dict            # {'NASDAQ': df2, 'SP500': df3, ...} for SMT checks
    higher_timeframe_df: pd.DataFrame  # e.g. 4H or Daily for context

class DailyBiasModel:
    def __init__(self):
        self.checks = []

    def log(self, item):
        self.checks.append(item)

    def expected_daily_structure(self, daily_df: pd.DataFrame):
        # Simple heuristic example
        recent = daily_df.tail(5)
        took_highs = (recent.high.diff() > 0).sum()
        took_lows = (recent.low.diff() < 0).sum()
        if took_highs and not took_lows:
            bias = "Bearish OHLC (Open High Low Close)"
        elif took_lows and not took_highs:
            bias = "Bullish OLHC (Open Low High Close)"
        else:
            bias = "Neutral / Wait"
        self.log(f"Daily candle expectation: {bias}")
        return bias

    def detect_stop_hunt(self, intraday_df: pd.DataFrame, prior_extremes):
        # prior_extremes: dict {'high': level, 'low': level}
        hunt = None
        if intraday_df.high.max() > prior_extremes['high']:
            hunt = "High sweep"
        elif intraday_df.low.min() < prior_extremes['low']:
            hunt = "Low sweep"
        self.log(f"Stop hunt: {hunt}")
        return hunt

    def smt_divergence(self, correlated: dict, kind="high"):
        # Very simplified: one makes new high/low others do not
        highs = {k: v.high.max() for k, v in correlated.items()}
        lows = {k: v.low.min() for k, v in correlated.items()}
        if kind == "high":
            top = max(highs.values())
            count = sum(1 for h in highs.values() if h == top)
            if count == 1:
                self.log("SMT divergence at highs")
                return True
        else:
            bottom = min(lows.values())
            count = sum(1 for l in lows.values() if l == bottom)
            if count == 1:
                self.log("SMT divergence at lows")
                return True
        self.log("No SMT divergence")
        return False

    def structure_shift(self, intraday_df: pd.DataFrame):
        # Placeholder: detect break of lower high or higher low
        recent = intraday_df.tail(50)
        # naive: last close below previous swing low
        shifted = recent.close.iloc[-1] < recent.low.rolling(10).min().iloc[-2]
        self.log(f"Structure shift: {shifted}")
        return shifted

    def next_liquidity(self, df: pd.DataFrame):
        # Target untouched extremes inside recent range
        recent = df.tail(300)
        target_low = recent.low.min()
        target_high = recent.high.max()
        self.log(f"Liquidity targets: High {target_high}, Low {target_low}")
        return {'high': target_high, 'low': target_low}

    def generate_bias(self, snapshot: MarketSnapshot):
        daily_bias = self.expected_daily_structure(snapshot.higher_timeframe_df)
        prior_extremes = {
            'high': snapshot.higher_timeframe_df.high.iloc[-2],
            'low': snapshot.higher_timeframe_df.low.iloc[-2]
        }
        hunt = self.detect_stop_hunt(snapshot.df, prior_extremes)
        smt = self.smt_divergence(snapshot.correlated, "high" if hunt == "High sweep" else "low")
        targets = self.next_liquidity(snapshot.df)
        shift = self.structure_shift(snapshot.df)

        actionable = all([
            daily_bias != "Neutral / Wait",
            hunt is not None,
            smt,
            shift
        ])

        return {
            'bias': daily_bias,
            'stop_hunt': hunt,
            'smt': smt,
            'structure_shift': shift,
            'targets': targets,
            'checks': self.checks,
            'actionable': actionable
        }