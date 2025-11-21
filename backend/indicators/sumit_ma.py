import pandas as pd
import numpy as np

def calculate_sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_sumit_ma(df, ma1=3, ma2=21, ma3=101, ma4=201, ath_atl_data=None):
    """
    NEW LOGIC: Sumit MA Price Position Indicator
    
    Calculates where current candle close is positioned relative to 10 MAs:
    MA-1: 3, MA-2: 9, MA-3: 15, MA-4: 21, MA-5: 27
    MA-6: 51, MA-7: 81, MA-8: 101, MA-9: 151, MA-10: 201
    
    Score Logic:
    - Count how many MAs are BELOW current price
    - Score = (MAs_below / Total_MAs) × 100
    - Score 100 = Price above ALL MAs (strongest bullish)
    - Score 50 = Price at middle of MA range (neutral)
    - Score 0 = Price below ALL MAs (strongest bearish)
    
    Returns DataFrame with single 'sumit_ma_score' column (0-100)
    """
    
    # Define 10 MAs
    ma_periods = [3, 9, 15, 21, 27, 51, 81, 101, 151, 201]
    
    # Calculate all MAs
    mas = {}
    for period in ma_periods:
        mas[f'MA_{period}'] = calculate_sma(df['Close'], period)
    
    # Create result DataFrame
    result = pd.DataFrame(index=df.index)
    result['sumit_ma_score'] = pd.Series(dtype=float)
    
    # For legacy compatibility, also create ratio scores (will be same as main score)
    result['sumit_ratio1_score'] = pd.Series(dtype=float)
    result['sumit_ratio2_score'] = pd.Series(dtype=float)
    result['sumit_ratio3_score'] = pd.Series(dtype=float)
    
    # Find valid points (where all MAs exist)
    valid_mask = pd.Series([True] * len(df), index=df.index)
    for ma_name, ma_series in mas.items():
        valid_mask = valid_mask & ~ma_series.isna()
    
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        print(f"⚠ Sumit MA: No valid data points (need at least 201 candles)")
        return result
    
    print(f"✓ Sumit MA (NEW LOGIC): Processing {valid_count} valid data points")
    print(f"  Method: Price position relative to 10 MAs")
    
    # Calculate score for each valid point
    for idx in df.index[valid_mask]:
        current_price = df.loc[idx, 'Close']
        
        # Count how many MAs are below current price
        mas_below = 0
        for ma_name, ma_series in mas.items():
            if current_price > ma_series[idx]:
                mas_below += 1
        
        # Calculate score (0-100)
        score = (mas_below / len(ma_periods)) * 100
        result.loc[idx, 'sumit_ma_score'] = score
        
        # For 3-line display, split into short/mid/long term groups
        # Short-term: MA 3,9,15,21 (first 4 MAs)
        short_mas_below = sum(1 for p in ma_periods[:4] if current_price > mas[f'MA_{p}'][idx])
        result.loc[idx, 'sumit_ratio1_score'] = (short_mas_below / 4) * 100
        
        # Mid-term: MA 27,51,81,101 (middle 4 MAs)
        mid_mas_below = sum(1 for p in ma_periods[4:8] if current_price > mas[f'MA_{p}'][idx])
        result.loc[idx, 'sumit_ratio2_score'] = (mid_mas_below / 4) * 100
        
        # Long-term: MA 151,201 (last 2 MAs)
        long_mas_below = sum(1 for p in ma_periods[8:] if current_price > mas[f'MA_{p}'][idx])
        result.loc[idx, 'sumit_ratio3_score'] = (long_mas_below / 2) * 100
    
    # Debug output
    if valid_count > 0:
        last_idx = result.index[valid_mask][-1]
        last_price = df.loc[last_idx, 'Close']
        
        print(f"  Last valid point:")
        print(f"    Current Price: ${last_price:.2f}")
        print(f"    Short-term Score (MA 3-21): {result.loc[last_idx, 'sumit_ratio1_score']:.1f}")
        print(f"    Mid-term Score (MA 27-101): {result.loc[last_idx, 'sumit_ratio2_score']:.1f}")
        print(f"    Long-term Score (MA 151-201): {result.loc[last_idx, 'sumit_ratio3_score']:.1f}")
        print(f"    Overall Score: {result.loc[last_idx, 'sumit_ma_score']:.1f}")
        
        # Show MA positions
        print(f"  MA Positions vs Price:")
        for period in ma_periods:
            ma_val = mas[f'MA_{period}'][last_idx]
            position = "BELOW" if last_price > ma_val else "ABOVE"
            diff_pct = ((last_price - ma_val) / ma_val) * 100
            print(f"    MA-{period:>3}: ${ma_val:>8.2f} ({position} price by {abs(diff_pct):>5.2f}%)")
    
    return result


def interpret_sumit_score(score):
    """
    Interpret Sumit MA score for trading decisions
    
    Returns: (signal, strength, description)
    """
    if score >= 90:
        return ("STRONG LONG", "Very Strong", "Price above 90%+ MAs - powerful uptrend")
    elif score >= 70:
        return ("LONG", "Strong", "Price above 70%+ MAs - solid uptrend")
    elif score >= 60:
        return ("LONG", "Moderate", "Price above 60%+ MAs - weak uptrend")
    elif score >= 40:
        return ("NEUTRAL", "Weak", "Price mixed around MAs - consolidation")
    elif score >= 30:
        return ("SHORT", "Moderate", "Price below 60%+ MAs - weak downtrend")
    elif score >= 10:
        return ("SHORT", "Strong", "Price below 70%+ MAs - solid downtrend")
    else:
        return ("STRONG SHORT", "Very Strong", "Price below 90%+ MAs - powerful downtrend")


# Example usage and testing
if __name__ == "__main__":
    import yfinance as yf
    
    print("="*60)
    print("TESTING NEW SUMIT MA LOGIC")
    print("="*60)
    
    # Fetch test data
    symbol = "^NSEI"
    print(f"\nFetching {symbol} data (5min, 15 days)...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="15d", interval="5m")
    
    if df.empty:
        print("ERROR: No data fetched!")
    else:
        print(f"✓ Got {len(df)} candles\n")
        
        # Calculate new Sumit MA
        result = calculate_sumit_ma(df)
        
        # Show last 10 scores
        print("\nLast 10 Scores:")
        print("-" * 80)
        print(f"{'Timestamp':<20} {'Price':<10} {'Short':<8} {'Mid':<8} {'Long':<8} {'Overall':<8} {'Signal'}")
        print("-" * 80)
        
        valid_data = result[result['sumit_ma_score'].notna()].tail(10)
        for idx in valid_data.index:
            timestamp = idx.strftime("%Y-%m-%d %H:%M")
            price = df.loc[idx, 'Close']
            short = result.loc[idx, 'sumit_ratio1_score']
            mid = result.loc[idx, 'sumit_ratio2_score']
            long = result.loc[idx, 'sumit_ratio3_score']
            overall = result.loc[idx, 'sumit_ma_score']
            
            signal, strength, _ = interpret_sumit_score(overall)
            
            print(f"{timestamp:<20} ${price:<9.2f} {short:<7.1f} {mid:<7.1f} {long:<7.1f} {overall:<7.1f} {signal}")
        
        print("-" * 80)
        
        # Final interpretation
        last_score = valid_data.iloc[-1]['sumit_ma_score']
        signal, strength, description = interpret_sumit_score(last_score)
        
        print(f"\n{'='*60}")
        print(f"CURRENT TRADING SIGNAL")
        print(f"{'='*60}")
        print(f"Score: {last_score:.1f}/100")
        print(f"Signal: {signal}")
        print(f"Strength: {strength}")
        print(f"Description: {description}")
        print(f"{'='*60}")
