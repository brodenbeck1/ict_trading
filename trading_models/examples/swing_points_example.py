"""
Swing Points Example
====================

Demonstrates how to use the SwingPointScanner to identify:
- Swing highs and lows
- Recent swing points
- Liquidity levels
- Relative equal highs/lows
"""

import sys
import os

# Add the trading_models directory to Python path to find ict_library
trading_models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, trading_models_dir)

from ict_library import SwingPointScanner, DataLoader


def main():
    # Get data directory path (relative to script location)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Data'))
    
    # Load data for last 4 weeks at 15-minute timeframe
    loader = DataLoader(timeframe='15T', weeks=4, data_dir=data_dir)
    df = loader.read_NQ()
    
    print(f"Loaded {len(df)} candles of NQ data")
    print(f"Date range: {df.index.min()} to {df.index.max()}\n")
    
    # Initialize scanner with lookback of 2 (means 2 candles on each side)
    scanner = SwingPointScanner(df, lookback=2)
    
    # Identify all swings
    df_with_swings = scanner.identify_swings()
    print(f"Swing highs found: {df_with_swings['swing_high'].sum():.0f}")
    print(f"Swing lows found: {df_with_swings['swing_low'].sum():.0f}\n")
    
    # Get recent swing points
    recent_swings = scanner.get_recent_swings(n=10)
    print("Recent 10 swing points:")
    print(recent_swings)
    print()
    
    # Get liquidity levels
    liquidity = scanner.get_liquidity_levels()
    print(f"Buy stops (above swing highs): {len(liquidity['buy_stops'])} levels")
    if liquidity['buy_stops']:
        print(f"  Most recent: {liquidity['buy_stops'][-5:]}")
    
    print(f"\nSell stops (below swing lows): {len(liquidity['sell_stops'])} levels")
    if liquidity['sell_stops']:
        print(f"  Most recent: {liquidity['sell_stops'][-5:]}")
    
    # Find relative equal highs
    rel_equal_highs = scanner.find_relative_equal_highs(tolerance=0.001)
    print(f"\n\nRelative equal highs found: {len(rel_equal_highs)}")
    for i, cluster in enumerate(rel_equal_highs[:5], 1):  # Show first 5
        print(f"  {i}. Price: {cluster['price']:.2f}, Count: {cluster['count']}, "
              f"Range: {cluster['min_price']:.2f} - {cluster['max_price']:.2f}")
    
    # Find relative equal lows
    rel_equal_lows = scanner.find_relative_equal_lows(tolerance=0.001)
    print(f"\nRelative equal lows found: {len(rel_equal_lows)}")
    for i, cluster in enumerate(rel_equal_lows[:5], 1):  # Show first 5
        print(f"  {i}. Price: {cluster['price']:.2f}, Count: {cluster['count']}, "
              f"Range: {cluster['min_price']:.2f} - {cluster['max_price']:.2f}")


if __name__ == "__main__":
    main()
