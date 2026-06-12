"""
Daily Bias Model Example
=========================

Demonstrates how to use the DailyBiasModel to analyze market conditions
and determine if a setup is actionable based on ICT methodology.
"""

import sys
import os

from ict import DailyBiasModel, MarketSnapshot, DataLoader
import pandas as pd


def main():
    # Get data directory path (relative to script location)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
    
    # Load intraday data (5-minute) for the last 2 weeks
    intraday_loader = DataLoader(timeframe='5T', weeks=2, data_dir=data_dir)
    nq_5m = intraday_loader.read_NQ()
    es_5m = intraday_loader.read_ES()
    ym_5m = intraday_loader.read_YM()
    
    # Load higher timeframe data (Daily) for context
    daily_loader = DataLoader(timeframe='D', weeks=12, data_dir=data_dir)
    nq_daily = daily_loader.read_NQ()
    
    print(f"Loaded NQ 5m data: {len(nq_5m)} candles")
    print(f"Loaded NQ daily data: {len(nq_daily)} candles")
    print(f"Analysis date: {nq_5m.index.max()}\n")
    
    # Create market snapshot with correlated instruments
    snapshot = MarketSnapshot(
        df=nq_5m,
        correlated={
            'NQ': nq_5m.tail(100),  # Last 100 candles for SMT analysis
            'ES': es_5m.tail(100),
            'YM': ym_5m.tail(100)
        },
        higher_timeframe_df=nq_daily
    )
    
    # Initialize and run daily bias model
    model = DailyBiasModel()
    result = model.generate_bias(snapshot)
    
    # Display results
    print("=" * 60)
    print("DAILY BIAS ANALYSIS")
    print("=" * 60)
    
    print(f"\n📊 Daily Structure: {result['bias']}")
    print(f"🎯 Stop Hunt: {result['stop_hunt']}")
    print(f"📈 SMT Divergence: {'✓ Confirmed' if result['smt'] else '✗ Not detected'}")
    print(f"🔄 Structure Shift: {'✓ Confirmed' if result['structure_shift'] else '✗ Not confirmed'}")
    
    print(f"\n💰 Liquidity Targets:")
    print(f"   High: {result['targets']['high']:.2f}")
    print(f"   Low: {result['targets']['low']:.2f}")
    
    print(f"\n{'✅ TRADE SETUP VALID' if result['actionable'] else '❌ NO TRADE - Missing components'}")
    
    print(f"\n📋 Checklist:")
    for i, check in enumerate(result['checks'], 1):
        print(f"   {i}. {check}")
    
    print("\n" + "=" * 60)
    
    if not result['actionable']:
        print("\n⚠️  Rule of Exclusion Applied:")
        print("   All components must align for actionable setup.")
        print("   Missing: ", end="")
        
        missing = []
        if result['bias'] == "Neutral / Wait":
            missing.append("clear daily bias")
        if not result['stop_hunt']:
            missing.append("stop hunt")
        if not result['smt']:
            missing.append("SMT divergence")
        if not result['structure_shift']:
            missing.append("structure shift")
        
        print(", ".join(missing))


if __name__ == "__main__":
    main()
