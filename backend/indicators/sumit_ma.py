import pandas as pd
import numpy as np
from ta.trend import SMAIndicator

def calculate_sumit_ma(df, ma1=3, ma2=21, ma3=101, ma4=201, ath_atl_data=None):
    """
    UPDATED Sumit MA Price Position Indicator using TA library
    
    Special MAs:
    - MA 3 High: SMA of High prices
    - MA 3 Low: SMA of Low prices
    
    OHLC/4 based MAs (18 total):
    3, 9, 15, 21, 27, 31, 37, 51, 65, 81, 101, 121, 131, 151, 171, 201, 251, 301
    
    Score Logic:
    - Count how many MAs are BELOW current price
    - Score = (MAs_below / Total_MAs) × 100
    
    Returns DataFrame with sumit_ma_score and ratio scores
    """
    
    # Calculate OHLC/4 (typical price)
    ohlc4 = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    # Define all MA periods for OHLC/4
    ma_periods = [3, 9, 15, 21, 27, 31, 37, 51, 65, 81, 101, 121, 131, 151, 171, 201, 251, 301]
    
    # Calculate all MAs using TA library
    mas = {}
    
    # Special MAs: MA 3 High and MA 3 Low using SMAIndicator
    mas['MA_3_High'] = SMAIndicator(close=df['High'], window=3).sma_indicator()
    mas['MA_3_Low'] = SMAIndicator(close=df['Low'], window=3).sma_indicator()
    
    # OHLC/4 based MAs
    for period in ma_periods:
        mas[f'MA_{period}'] = SMAIndicator(close=ohlc4, window=period).sma_indicator()
    
    # Total MAs = 2 (High/Low) + 18 (OHLC/4) = 20
    total_mas = 2 + len(ma_periods)
    
    # Create result DataFrame
    result = pd.DataFrame(index=df.index)
    result['sumit_ma_score'] = pd.Series(dtype=float)
    result['sumit_ratio1_score'] = pd.Series(dtype=float)
    result['sumit_ratio2_score'] = pd.Series(dtype=float)
    result['sumit_ratio3_score'] = pd.Series(dtype=float)
    
    # Find valid points (where longest MA exists - 301)
    max_period = max(ma_periods)
    valid_mask = pd.Series([True] * len(df), index=df.index)
    for ma_name, ma_series in mas.items():
        valid_mask = valid_mask & ~ma_series.isna()
    
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        print(f"⚠ Sumit MA: No valid data points (need at least {max_period} candles)")
        return result
    
    print(f"✓ Sumit MA: Processing {valid_count} valid data points")
    print(f"  Total MAs: {total_mas} (2 special + {len(ma_periods)} OHLC/4)")
    
    # Group MAs for ratio scores
    short_term_mas = ['MA_3_High', 'MA_3_Low', 'MA_3', 'MA_9', 'MA_15', 'MA_21', 'MA_27', 'MA_31']
    mid_term_mas = ['MA_37', 'MA_51', 'MA_65', 'MA_81', 'MA_101', 'MA_121']
    long_term_mas = ['MA_131', 'MA_151', 'MA_171', 'MA_201', 'MA_251', 'MA_301']
    
    # Calculate score for each valid point
    for idx in df.index[valid_mask]:
        current_price = df.loc[idx, 'Close']
        
        # Count MAs below current price
        mas_below = sum(1 for ma_series in mas.values() if current_price > ma_series[idx])
        
        # Overall score (0-100)
        result.loc[idx, 'sumit_ma_score'] = (mas_below / total_mas) * 100
        
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
        print(f"    Price: ${last_price:.2f}")
        print(f"    Short (8 MAs): {result.loc[last_idx, 'sumit_ratio1_score']:.1f}")
        print(f"    Mid (6 MAs): {result.loc[last_idx, 'sumit_ratio2_score']:.1f}")
        print(f"    Long (6 MAs): {result.loc[last_idx, 'sumit_ratio3_score']:.1f}")
        print(f"    Overall: {result.loc[last_idx, 'sumit_ma_score']:.1f}")
    
    return result


def sumit_ma_signals(df):
    """
    NEW SUMIT MA SIGNAL LOGIC
    
    Counts BUY and SELL signals based on price position relative to 18 MAs
    (excludes MA 3 High and MA 3 Low)
    
    BUY Signal: Price > MA (counts 0-18)
    SELL Signal: Price < MA (counts 0-18)
    
    Returns DataFrame with buy_signal_count, sell_signal_count
    """
    
    # Calculate OHLC/4 (typical price)
    ohlc4 = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    # Define 18 MA periods for OHLC/4 (excluding MA 3 High/Low)
    ma_periods = [3, 9, 15, 21, 27, 31, 37, 51, 65, 81, 101, 121, 131, 151, 171, 201, 251, 301]
    
    # Calculate all 18 MAs
    mas = {}
    for period in ma_periods:
        mas[f'MA_{period}'] = SMAIndicator(close=ohlc4, window=period).sma_indicator()
    
    # Create result DataFrame
    result = pd.DataFrame(index=df.index)
    result['buy_signal_count'] = 0
    result['sell_signal_count'] = 0
    
    # Find valid points (where longest MA exists - 301)
    max_period = max(ma_periods)
    valid_mask = pd.Series([True] * len(df), index=df.index)
    for ma_series in mas.values():
        valid_mask = valid_mask & ~ma_series.isna()
    
    valid_count = valid_mask.sum()
    
    if valid_count == 0:
        print(f"⚠ Sumit MA Signals: No valid data points (need at least {max_period} candles)")
        return result
    
    print(f"✓ Sumit MA Signals: Processing {valid_count} valid data points")
    print(f"  Using 18 MAs (OHLC/4 based)")
    
    # Calculate signals for each valid point
    for idx in df.index[valid_mask]:
        current_price = df.loc[idx, 'Close']
        
        buy_count = 0
        sell_count = 0
        
        for ma_name, ma_series in mas.items():
            ma_value = ma_series[idx]
            
            if current_price > ma_value:
                buy_count += 1
            elif current_price < ma_value:
                sell_count += 1
            # If equal, don't count either way
        
        result.loc[idx, 'buy_signal_count'] = buy_count
        result.loc[idx, 'sell_signal_count'] = sell_count
    
    # Debug output
    if valid_count > 0:
        last_idx = result.index[valid_mask][-1]
        last_price = df.loc[last_idx, 'Close']
        last_buy = result.loc[last_idx, 'buy_signal_count']
        last_sell = result.loc[last_idx, 'sell_signal_count']
        
        print(f"  Last valid point:")
        print(f"    Price: ${last_price:.2f}")
        print(f"    BUY Signals: {last_buy}/18")
        print(f"    SELL Signals: {last_sell}/18")
        
        if last_buy > 12:
            print(f"    Signal: STRONG BUY (>{last_buy}/18 MAs below price)")
        elif last_buy > 9:
            print(f"    Signal: BUY ({last_buy}/18 MAs below price)")
        elif last_sell > 12:
            print(f"    Signal: STRONG SELL (>{last_sell}/18 MAs above price)")
        elif last_sell > 9:
            print(f"    Signal: SELL ({last_sell}/18 MAs above price)")
        else:
            print(f"    Signal: NEUTRAL")
    
    return result


def interpret_sumit_score(score):
    """Interpret Sumit MA score for trading decisions"""
    if score >= 90:
        return ("STRONG LONG", "Very Strong", "Price above 90%+ MAs")
    elif score >= 70:
        return ("LONG", "Strong", "Price above 70%+ MAs")
    elif score >= 60:
        return ("LONG", "Moderate", "Price above 60%+ MAs")
    elif score >= 40:
        return ("NEUTRAL", "Weak", "Price mixed around MAs")
    elif score >= 30:
        return ("SHORT", "Moderate", "Price below 60%+ MAs")
    elif score >= 10:
        return ("SHORT", "Strong", "Price below 70%+ MAs")
    else:
        return ("STRONG SHORT", "Very Strong", "Price below 90%+ MAs")


def calculate_sumit_ma_cross(data_1m, data_5m, data_1h, sma9_period=9, sma21_period=21):
    """
    Calculate cross-timeframe Sumit MA average score with SMA crossover using TA library
    """
    # Align all timeframes by timestamp
    df_1m = data_1m[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_1m'})
    df_5m = data_5m[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_5m'})
    df_1h = data_1h[['sumit_ma_score']].rename(columns={'sumit_ma_score': 'score_1h'})
    
    # Merge on index (timestamp)
    combined = df_1m.join(df_5m, how='outer').join(df_1h, how='outer')
    combined = combined.ffill()
    
    # Calculate average of all 3 timeframes
    combined['cross_avg_score'] = (
        combined['score_1m'] + 
        combined['score_5m'] + 
        combined['score_1h']
    ) / 3
    
    # Calculate SMA9 and SMA21 using TA library
    combined['cross_sma9'] = SMAIndicator(
        close=combined['cross_avg_score'], 
        window=sma9_period
    ).sma_indicator()
    
    combined['cross_sma21'] = SMAIndicator(
        close=combined['cross_avg_score'], 
        window=sma21_period
    ).sma_indicator()
    
    return combined[['cross_avg_score', 'cross_sma9', 'cross_sma21']]
