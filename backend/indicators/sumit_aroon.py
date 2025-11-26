import pandas as pd
import numpy as np
from ta.trend import AroonIndicator, SMAIndicator

def calculate_sumit_aroon(df, period=25):
    """
    Calculate Aroon Indicator
    
    Aroon Up: ((period - periods since highest high) / period) * 100
    Aroon Down: ((period - periods since lowest low) / period) * 100
    
    Aroon Score = (Aroon Up + Aroon Down) / 2
    
    Returns DataFrame with aroon_up, aroon_down, aroon_score
    """
    aroon = AroonIndicator(
        high=df['High'],
        low=df['Low'],
        window=period
    )
    
    result = pd.DataFrame(index=df.index)
    result['aroon_up'] = aroon.aroon_up()
    result['aroon_down'] = aroon.aroon_down()
    
    # Aroon Score: Average of Up and Down
    result['aroon_score'] = (result['aroon_up'] + result['aroon_down']) / 2
    
    # Aroon Oscillator: Up - Down (optional, for trend strength)
    result['aroon_oscillator'] = result['aroon_up'] - result['aroon_down']
    
    return result


def score_aroon(aroon_up, aroon_down):
    """
    Score Aroon for trading signals (0-100 scale)
    
    Logic:
    - If Aroon Up > 70 and Aroon Down < 30: Strong bullish (score near 100)
    - If Aroon Down > 70 and Aroon Up < 30: Strong bearish (score near 0)
    - Otherwise: proportional to (Aroon Up / (Aroon Up + Aroon Down))
    """
    if pd.isna(aroon_up) or pd.isna(aroon_down):
        return 50.0
    
    # Normalize to 0-100 based on Aroon Up dominance
    total = aroon_up + aroon_down
    if total == 0:
        return 50.0
    
    score = (aroon_up / total) * 100
    return float(score)


def calculate_aroon_cross(data_1m, data_5m, data_1h, sma9_period=9):
    """
    Calculate cross-timeframe Aroon average score with SMA9
    
    Returns DataFrame with:
    - aroon_avg_score: Average of 1m, 5m, 1h aroon scores
    - aroon_sma9: SMA9 of average
    """
    # Align all timeframes by timestamp
    df_1m = data_1m[['aroon_score']].rename(columns={'aroon_score': 'aroon_1m'})
    df_5m = data_5m[['aroon_score']].rename(columns={'aroon_score': 'aroon_5m'})
    df_1h = data_1h[['aroon_score']].rename(columns={'aroon_score': 'aroon_1h'})
    
    # Merge on index (timestamp)
    combined = df_1m.join(df_5m, how='outer').join(df_1h, how='outer')
    combined = combined.ffill()
    
    # Calculate average of all 3 timeframes
    combined['aroon_avg_score'] = (
        combined['aroon_1m'] + 
        combined['aroon_5m'] + 
        combined['aroon_1h']
    ) / 3
    
    # Calculate SMA9 using SMAIndicator
    combined['aroon_sma9'] = SMAIndicator(
        close=combined['aroon_avg_score'], 
        window=sma9_period
    ).sma_indicator()
    
    return combined[['aroon_1m', 'aroon_5m', 'aroon_1h', 'aroon_avg_score', 'aroon_sma9']]


def interpret_aroon(aroon_up, aroon_down):
    """
    Interpret Aroon values for trading signals
    """
    if aroon_up > 70 and aroon_down < 30:
        return ("STRONG LONG", "Strong uptrend")
    elif aroon_up > 50 and aroon_down < 50:
        return ("LONG", "Uptrend emerging")
    elif aroon_down > 70 and aroon_up < 30:
        return ("STRONG SHORT", "Strong downtrend")
    elif aroon_down > 50 and aroon_up < 50:
        return ("SHORT", "Downtrend emerging")
    else:
        return ("NEUTRAL", "No clear trend")
