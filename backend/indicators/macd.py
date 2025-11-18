import pandas as pd
from ta.trend import MACD

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD indicator using ta library"""
    macd_indicator = MACD(
        close=df['Close'],
        window_slow=slow,
        window_fast=fast,
        window_sign=signal
    )
    
    result = pd.DataFrame(index=df.index)
    result['MACD'] = macd_indicator.macd()
    result['MACD_signal'] = macd_indicator.macd_signal()
    result['MACD_diff'] = macd_indicator.macd_diff()
    
    return result

def score_macd(macd_histogram):
    """
    MACD Score: 50 + (Histogram × 5), capped at 0-100
    >50 = bullish, <50 = bearish
    """
    if pd.isna(macd_histogram):
        return 50.0
    score = 50 + (float(macd_histogram) * 5)
    return max(0, min(100, score))
