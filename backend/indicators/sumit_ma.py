import pandas as pd
import numpy as np

def calculate_sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_sumit_ma(df, ma1=3, ma2=21, ma3=101, ma4=201, ath_atl_data=None):
    """
    UPDATED Sumit MA Price Position Indicator
    
    Special MAs:
    - MA 3 High: SMA of High prices
    - MA 3 Low: SMA of Low prices
    
    OHLC/4 based MAs (19 total):
    3, 9, 15, 21, 27, 31, 37, 51, 65, 81, 101, 121, 131, 151, 171, 201, 251, 301
    
    Score Logic:
    - Count how many MAs are BELOW current price
    - Score = (MAs_below / Total_MAs) × 100
    - Score 100 = Price above ALL MAs (strongest bullish)
    - Score 0 = Price below ALL MAs (strongest bearish)
    
    Returns DataFrame with sumit_ma_score and ratio scores
    """
    
    # Calculate OHLC/4 (typical price)
    ohlc4 = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    # Define all MA periods for OHLC/4
    ma_periods = [3, 9, 15, 21, 27, 31, 37, 51, 65, 81, 101, 121, 131, 151, 171, 201, 251, 301]
    
    # Calculate all MAs
    mas = {}
    
    # Special MAs: MA 3 High and MA 3 Low
    mas['MA_3_High'] = calculate_sma(df['High'], 3)
    mas['MA_3_Low'] = calculate_sma(df['Low'], 3)
    
    # OHLC/4 based MAs
    for period in ma_periods:
        mas[f'MA_{period}'] = calculate_sma(ohlc4, period)
    
    # Total MAs = 2 (High/Low) + 18 (OHLC/4) = 20
    total_mas = 2 + len(ma_periods)
    
    # Create result DataFrame
    result = pd.DataFrame(index=df.index)
    result['sumit_ma_score'] = pd.Series(dtype=float)
    result['sumit_ratio1_score'] = pd.Series(dtype=float)  # Short-term
    result['sumit_ratio2_score'] = pd.Series(dtype=float)  # Mid-term
    result['sumit_ratio3_score'] = pd.Series(dtype=float)  # Long-term
    
    # Find valid points (where longest MA exists - 301)
    max_period = max(ma_periods)
    valid_mask = pd.Series([True] * len(df), index=df.index)
    for ma_name, ma_series in mas.items():
        valid_mask = valid_mask & ~ma_series.isna()
    
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        print(f"⚠ Sumit MA: No valid data points (need at least {max_period} candles)")
        return result
    
    print(f"✓ Sumit MA (UPDATED): Processing {valid_count} valid data points")
    print(f"  Total MAs: {total_mas} (2 special + {len(ma_periods)} OHLC/4)")
    
    # Group MAs for ratio scores
    # Short-term: MA 3H, 3L, 3, 9, 15, 21, 27, 31 (8 MAs)
    short_term_mas = ['MA_3_High', 'MA_3_Low', 'MA_3', 'MA_9', 'MA_15', 'MA_21', 'MA_27', 'MA_31']
    
    # Mid-term: MA 37, 51, 65, 81, 101, 121 (6 MAs)
    mid_term_mas = ['MA_37', 'MA_51', 'MA_65', 'MA_81', 'MA_101', 'MA_121']
    
    # Long-term: MA 131, 151, 171, 201, 251, 301 (6 MAs)
    long_term_mas = ['MA_131', 'MA_151', 'MA_171', 'MA_201', 'MA_251', 'MA_301']
    
    # Calculate score for each valid point
    for idx in df.index[valid_mask]:
        current_price = df.loc[idx, 'Close']
        
        # Count how many MAs are below current price
        mas_below = 0
        for ma_name, ma_series in mas.items():
            if current_price > ma_series[idx]:
                mas_below += 1
        
        # Overall score (0-100)
        score = (mas_below / total_mas) * 100
        result.loc[idx, 'sumit_ma_score'] = score
        
        # Short-term score
        short_below = sum(1 for ma in short_term_mas if current_price > mas[ma][idx])
        result.loc[idx, 'sumit_ratio1_score'] = (short_below / len(short_term_mas)) * 100
        
        # Mid-term score
        mid_below = sum(1 for ma in mid_term_mas if current_price > mas[ma][idx])
        result.loc[idx, 'sumit_ratio2_score'] = (mid_below / len(mid_term_mas)) * 100
        
        # Long-term score
        long_below = sum(1 for ma in long_term_mas if current_price > mas[ma][idx])
        result.loc[idx, 'sumit_ratio3_score'] = (long_below / len(long_term_mas)) * 100
    
    # Debug output
    if valid_count > 0:
        last_idx = result.index[valid_mask][-1]
        last_price = df.loc[last_idx, 'Close']
        
        print(f"  Last valid point:")
        print(f"    Current Price: ${last_price:.2f}")
        print(f"    Short-term Score (8 MAs): {result.loc[last_idx, 'sumit_ratio1_score']:.1f}")
        print(f"    Mid-term Score (6 MAs): {result.loc[last_idx, 'sumit_ratio2_score']:.1f}")
        print(f"    Long-term Score (6 MAs): {result.loc[last_idx, 'sumit_ratio3_score']:.1f}")
        print(f"    Overall Score ({total_mas} MAs): {result.loc[last_idx, 'sumit_ma_score']:.1f}")
        
        # Show key MA positions
        print(f"  Key MA Positions vs Price (${last_price:.2f}):")
        key_mas = ['MA_3_High', 'MA_3_Low', 'MA_21', 'MA_51', 'MA_101', 'MA_201', 'MA_301']
        for ma_name in key_mas:
            ma_val = mas[ma_name][last_idx]
            position = "BELOW" if last_price > ma_val else "ABOVE"
            diff_pct = ((last_price - ma_val) / ma_val) * 100
            print(f"    {ma_name:>12}: ${ma_val:>10.2f} ({position} price by {abs(diff_pct):>5.2f}%)")
    
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


def calculate_sumit_ma_cross(data_1m, data_5m, data_1h, sma9_period=9, sma21_period=21):
    """
    Calculate cross-timeframe Sumit MA average score with SMA crossover
    
    Args:
        data_1m: DataFrame with sumit_ma_score for 1min
        data_5m: DataFrame with sumit_ma_score for 5min
        data_1h: DataFrame with sumit_ma_score for 1hr
        sma9_period: Fast SMA period (default 9)
        sma21_period: Slow SMA period (default 21)
    
    Returns:
        DataFrame with cross_avg_score, cross_sma9, cross_sma21
    """
    # Align all timeframes by timestamp
    df_1m = data_1m[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_1m'})
    df_5m = data_5m[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_5m'})
    df_1h = data_1h[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_1h'})
    
    # Merge on index (timestamp)
    combined = df_1m.join(df_5m, how='outer').join(df_1h, how='outer')
    combined = combined.ffill()  # Forward fill missing values
    
    # Calculate average of all 3 timeframes
    combined['cross_avg_score'] = (
        combined['score_1m'] + 
        combined['score_5m'] + 
        combined['score_1h']
    ) / 3
    
    # Calculate SMA9 and SMA21 of the average
    combined['cross_sma9'] = combined['cross_avg_score'].rolling(window=sma9_period).mean()
    combined['cross_sma21'] = combined['cross_avg_score'].rolling(window=sma21_period).mean()
    
    return combined[['cross_avg_score', 'cross_sma9', 'cross_sma21']]


# Example usage and testing
if __name__ == "__main__":
    import yfinance as yf
    
    print("="*60)
    print("TESTING UPDATED SUMIT MA LOGIC")
    print("="*60)
    
    # Fetch test data
    symbol = "^NSEI"
    print(f"\nFetching {symbol} data (5min, 60 days for 301 MA)...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="60d", interval="5m")
    
    if df.empty:
        print("ERROR: No data fetched!")
    else:
        print(f"✓ Got {len(df)} candles\n")
        
        # Calculate new Sumit MA
        result = calculate_sumit_ma(df)
        
        # Show last 10 scores
        print("\nLast 10 Scores:")
        print("-" * 100)
        print(f"{'Timestamp':<20} {'Price':<10} {'Short(8)':<10} {'Mid(6)':<10} {'Long(6)':<10} {'Overall':<10} {'Signal'}")
        print("-" * 100)
        
        valid_data = result[result['sumit_ma_score'].notna()].tail(10)
        for idx in valid_data.index:
            timestamp = idx.strftime("%Y-%m-%d %H:%M")
            price = df.loc[idx, 'Close']
            short = result.loc[idx, 'sumit_ratio1_score']
            mid = result.loc[idx, 'sumit_ratio2_score']
            long = result.loc[idx, 'sumit_ratio3_score']
            overall = result.loc[idx, 'sumit_ma_score']
            
            signal, strength, _ = interpret_sumit_score(overall)
            
            print(f"{timestamp:<20} ${price:<9.2f} {short:<9.1f} {mid:<9.1f} {long:<9.1f} {overall:<9.1f} {signal}")
        
        print("-" * 100)
        
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
