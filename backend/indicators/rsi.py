import pandas as pd
from ta.momentum import RSIIndicator

def calculate_rsi(df, period=14):
    """Calculate RSI indicator using ta library"""
    rsi_indicator = RSIIndicator(close=df['Close'], window=period)
    return rsi_indicator.rsi()

def score_rsi(rsi_value):
    """
    RSI Score: Direct RSI value (0-100)
    Extreme zones: >70 (overbought), <30 (oversold)
    """
    if pd.isna(rsi_value):
        return 50.0
    return max(0, min(100, float(rsi_value)))
