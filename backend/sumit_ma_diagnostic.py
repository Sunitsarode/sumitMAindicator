"""
Test new Sumit MA logic - Price position relative to 10 MAs
Usage: python test_new_sumit_ma.py
"""

import pandas as pd
import numpy as np
import yfinance as yf

def calculate_sma(series, period):
    return series.rolling(window=period).mean()

def test_new_sumit_logic():
    print("="*70)
    print("NEW SUMIT MA LOGIC TEST")
    print("="*70)
    
    # Test parameters
    symbol = "^NSEI"
    interval = "5m"
    period = "15d"
    
    print(f"\n1. Fetching {symbol} data ({interval}, {period})...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        print("ERROR: No data!")
        return
    
    print(f"   ✓ Got {len(df)} candles")
    print(f"   Price range: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    
    # Define 10 MAs
    ma_periods = [3, 9, 15, 21, 27, 51, 81, 101, 151, 201]
    
    print(f"\n2. Calculating 10 Moving Averages...")
    mas = {}
    for period in ma_periods:
        mas[f'MA_{period}'] = calculate_sma(df['Close'], period)
        valid_count = mas[f'MA_{period}'].notna().sum()
        print(f"   MA-{period:>3}: {valid_count} valid values")
    
    # Find valid points
    valid_mask = pd.Series([True] * len(df), index=df.index)
    for ma_series in mas.values():
        valid_mask = valid_mask & ~ma_series.isna()
    
    valid_count = valid_mask.sum()
    print(f"\n   Total valid points (all MAs exist): {valid_count}")
    
    if valid_count == 0:
        print("   ERROR: Not enough data for MA-201")
        return
    
    # Calculate scores
    print(f"\n3. Calculating Position Scores...")
    scores = pd.DataFrame(index=df.index)
    scores['overall'] = 0.0
    scores['short_term'] = 0.0
    scores['mid_term'] = 0.0
    scores['long_term'] = 0.0
    
    for idx in df.index[valid_mask]:
        current_price = df.loc[idx, 'Close']
        
        # Overall: all 10 MAs
        mas_below = sum(1 for ma in mas.values() if current_price > ma[idx])
        scores.loc[idx, 'overall'] = (mas_below / 10) * 100
        
        # Short-term: MA 3,9,15,21
        short_below = sum(1 for p in ma_periods[:4] if current_price > mas[f'MA_{p}'][idx])
        scores.loc[idx, 'short_term'] = (short_below / 4) * 100
        
        # Mid-term: MA 27,51,81,101
        mid_below = sum(1 for p in ma_periods[4:8] if current_price > mas[f'MA_{p}'][idx])
        scores.loc[idx, 'mid_term'] = (mid_below / 4) * 100
        
        # Long-term: MA 151,201
        long_below = sum(1 for p in ma_periods[8:] if current_price > mas[f'MA_{p}'][idx])
        scores.loc[idx, 'long_term'] = (long_below / 2) * 100
    
    # Show last data point details
    print(f"\n4. Last Candle Analysis:")
    last_idx = df.index[valid_mask][-1]
    last_price = df.loc[last_idx, 'Close']
    
    print(f"   Timestamp: {last_idx.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Current Price: ${last_price:.2f}")
    print(f"\n   MA Positions:")
    print(f"   {'-'*60}")
    print(f"   {'MA Period':<12} {'Value':<12} {'Position':<10} {'Diff %'}")
    print(f"   {'-'*60}")
    
    for period in ma_periods:
        ma_val = mas[f'MA_{period}'][last_idx]
        if last_price > ma_val:
            position = "✓ BELOW"
            color = ""
        else:
            position = "✗ ABOVE"
            color = ""
        diff_pct = ((last_price - ma_val) / ma_val) * 100
        print(f"   MA-{period:<8} ${ma_val:<11.2f} {position:<10} {diff_pct:>+6.2f}%")
    
    # Show scores
    print(f"\n5. Scores:")
    print(f"   {'-'*40}")
    print(f"   Short-term (MA 3-21):   {scores.loc[last_idx, 'short_term']:>6.1f}/100")
    print(f"   Mid-term (MA 27-101):   {scores.loc[last_idx, 'mid_term']:>6.1f}/100")
    print(f"   Long-term (MA 151-201): {scores.loc[last_idx, 'long_term']:>6.1f}/100")
    print(f"   {'-'*40}")
    print(f"   OVERALL SCORE:          {scores.loc[last_idx, 'overall']:>6.1f}/100")
    
    # Interpret
    overall_score = scores.loc[last_idx, 'overall']
    
    if overall_score >= 90:
        signal = "🚀 STRONG LONG"
        desc = "Price above 90%+ MAs - powerful uptrend"
    elif overall_score >= 70:
        signal = "📈 LONG"
        desc = "Price above 70%+ MAs - solid uptrend"
    elif overall_score >= 60:
        signal = "↗️  WEAK LONG"
        desc = "Price above 60%+ MAs - weak uptrend"
    elif overall_score >= 40:
        signal = "➡️  NEUTRAL"
        desc = "Price mixed - consolidation"
    elif overall_score >= 30:
        signal = "↘️  WEAK SHORT"
        desc = "Price below 60%+ MAs - weak downtrend"
    elif overall_score >= 10:
        signal = "📉 SHORT"
        desc = "Price below 70%+ MAs - solid downtrend"
    else:
        signal = "💥 STRONG SHORT"
        desc = "Price below 90%+ MAs - powerful downtrend"
    
    print(f"\n6. Trading Signal:")
    print(f"   {'-'*40}")
    print(f"   {signal}")
    print(f"   {desc}")
    print(f"   {'-'*40}")
    
    # Show last 10 scores
    print(f"\n7. Last 10 Score History:")
    print(f"   {'-'*70}")
    print(f"   {'Time':<12} {'Price':<10} {'Short':<8} {'Mid':<8} {'Long':<8} {'Overall'}")
    print(f"   {'-'*70}")
    
    last_10 = df.index[valid_mask][-10:]
    for idx in last_10:
        time_str = idx.strftime("%H:%M")
        price = df.loc[idx, 'Close']
        short = scores.loc[idx, 'short_term']
        mid = scores.loc[idx, 'mid_term']
        long = scores.loc[idx, 'long_term']
        overall = scores.loc[idx, 'overall']
        print(f"   {time_str:<12} ${price:<9.2f} {short:<7.1f} {mid:<7.1f} {long:<7.1f} {overall:<7.1f}")
    
    # Statistics
    valid_scores = scores[valid_mask]
    print(f"\n8. Score Statistics:")
    print(f"   Overall: Min={valid_scores['overall'].min():.1f}, Max={valid_scores['overall'].max():.1f}, Mean={valid_scores['overall'].mean():.1f}")
    print(f"   Short:   Min={valid_scores['short_term'].min():.1f}, Max={valid_scores['short_term'].max():.1f}, Mean={valid_scores['short_term'].mean():.1f}")
    print(f"   Mid:     Min={valid_scores['mid_term'].min():.1f}, Max={valid_scores['mid_term'].max():.1f}, Mean={valid_scores['mid_term'].mean():.1f}")
    print(f"   Long:    Min={valid_scores['long_term'].min():.1f}, Max={valid_scores['long_term'].max():.1f}, Mean={valid_scores['long_term'].mean():.1f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_new_sumit_logic()
