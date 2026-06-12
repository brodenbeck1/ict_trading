"""
Daily Bias Model
================

ICT Daily Bias Checklist Implementation:

Key Components:
- Expected daily candle structure: Bearish (OHLC) vs Bullish (OLHC)
- Stop hunt identification (Asia, London, pre-market liquidity sweeps)
- SMT divergence (intermarket divergence validation)
- Market structure alignment
- Liquidity targets mapping

Decision Flow:
1. Define expected daily structure based on untested highs/lows
2. Identify stop hunts (external/internal range sweeps)
3. Validate with SMT at turning points
4. Confirm structure shift toward liquidity draw
5. Execute only when all components align
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, Optional

from ict.registry import concept


@dataclass
class MarketSnapshot:
    """
    Container for market data across multiple timeframes and instruments.
    
    Attributes:
        df: Primary intraday data (1m or 5m) with OHLCV columns
        correlated: Dict of correlated instruments for SMT checks
        higher_timeframe_df: 4H or Daily data for context
    """
    df: pd.DataFrame
    correlated: Dict[str, pd.DataFrame]
    higher_timeframe_df: pd.DataFrame


@concept("daily-bias")
class DailyBiasModel:
    """
    Implements ICT daily bias methodology for intraday trading decisions.
    
    Uses sequential checklist to validate trade setups:
    - Daily candle structure expectation
    - Stop hunt detection
    - SMT divergence confirmation
    - Market structure shift
    - Liquidity target identification
    """
    
    def __init__(self):
        """Initialize the model with an empty checklist."""
        self.checks = []

    def log(self, item: str):
        """Log a checklist item or observation."""
        self.checks.append(item)

    def expected_daily_structure(self, daily_df: pd.DataFrame) -> str:
        """
        Determine expected daily candle structure based on recent price action.
        
        Args:
            daily_df: Daily timeframe OHLCV data
        
        Returns:
            Bias string: 'Bearish OHLC', 'Bullish OLHC', or 'Neutral / Wait'
        
        Logic:
        - Multiple highs taken without lows → Bearish OHLC retracement expected
        - Multiple lows taken without highs → Bullish OLHC expansion expected
        - Mixed action → Wait for clarity
        """
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

    def detect_stop_hunt(self, intraday_df: pd.DataFrame, prior_extremes: dict) -> Optional[str]:
        """
        Detect if a stop hunt (liquidity sweep) has occurred.
        
        Args:
            intraday_df: Current session intraday data
            prior_extremes: Dict with 'high' and 'low' levels to check
        
        Returns:
            'High sweep', 'Low sweep', or None
        
        Stop Hunt Definition:
        Price briefly violates a prior extreme (high/low) then reverses,
        indicating liquidity has been engineered/swept.
        """
        hunt = None
        if intraday_df.high.max() > prior_extremes['high']:
            hunt = "High sweep"
        elif intraday_df.low.min() < prior_extremes['low']:
            hunt = "Low sweep"
        
        self.log(f"Stop hunt: {hunt}")
        return hunt

    def smt_divergence(self, correlated: Dict[str, pd.DataFrame], kind: str = "high") -> bool:
        """
        Check for Smart Money Technique (SMT) divergence across correlated instruments.
        
        Args:
            correlated: Dict of instrument dataframes (e.g., NQ, ES, YM)
            kind: 'high' or 'low' - type of divergence to check
        
        Returns:
            True if SMT divergence detected
        
        SMT Logic:
        When correlated instruments should move together but ONE makes a new
        high/low while others fail, it signals potential reversal.
        """
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

    def structure_shift(self, intraday_df: pd.DataFrame) -> bool:
        """
        Detect if market structure has shifted toward the liquidity draw.
        
        Args:
            intraday_df: Recent intraday data
        
        Returns:
            True if structure shift detected
        
        Structure Shift:
        Break of recent swing high/low indicating momentum change
        toward the expected liquidity target.
        """
        recent = intraday_df.tail(50)
        # Simplified: check if last close broke below recent swing low
        shifted = recent.close.iloc[-1] < recent.low.rolling(10).min().iloc[-2]
        self.log(f"Structure shift: {shifted}")
        return shifted

    def next_liquidity(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Identify next liquidity targets (untouched extremes).
        
        Args:
            df: Price data
        
        Returns:
            Dict with 'high' and 'low' liquidity targets
        
        Liquidity Targets:
        Untouched highs/lows where stops are resting. Price is
        magnetically drawn to these levels.
        """
        recent = df.tail(300)
        target_low = recent.low.min()
        target_high = recent.high.max()
        self.log(f"Liquidity targets: High {target_high}, Low {target_low}")
        return {'high': target_high, 'low': target_low}

    def generate_bias(self, snapshot: MarketSnapshot) -> dict:
        """
        Generate complete daily bias analysis with actionable signal.
        
        Args:
            snapshot: MarketSnapshot with all required data
        
        Returns:
            Dict containing:
                - bias: Expected daily structure
                - stop_hunt: Hunt detection result
                - smt: SMT divergence result
                - structure_shift: Structure shift confirmation
                - targets: Liquidity targets
                - checks: All logged checklist items
                - actionable: Boolean - trade setup valid
        
        Rule of Exclusion:
        Trade is actionable ONLY when all components align:
        bias + stop hunt + SMT + structure shift
        """
        self.checks = []  # Reset checklist
        
        # Execute checklist
        daily_bias = self.expected_daily_structure(snapshot.higher_timeframe_df)
        
        prior_extremes = {
            'high': snapshot.higher_timeframe_df.high.iloc[-2],
            'low': snapshot.higher_timeframe_df.low.iloc[-2]
        }
        
        hunt = self.detect_stop_hunt(snapshot.df, prior_extremes)
        smt = self.smt_divergence(snapshot.correlated, "high" if hunt == "High sweep" else "low")
        targets = self.next_liquidity(snapshot.df)
        shift = self.structure_shift(snapshot.df)

        # Rule of exclusion: all components must align
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
