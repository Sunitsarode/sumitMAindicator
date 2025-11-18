import pandas as pd

def calculate_sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_sumit_ma(df, ma9=9, ma51=51, ma101=101, ma201=201):
    """
    Calculate Sumit MA Indicator:
    A = (MA9 + MA51)/2
    B = (MA51 + MA101)/2
    C = (MA101 + MA201)/2
    D = (A+C)/2*B
    
    Returns normalized score 0-100
    """
    sma9 = calculate_sma(df['Close'], ma9)
    sma51 = calculate_sma(df['Close'], ma51)
    sma101 = calculate_sma(df['Close'], ma101)
    sma201 = calculate_sma(df['Close'], ma201)
    
    A = (sma9 + sma51) / 2
    B = (sma51 + sma101) / 2
    C = (sma101 + sma201) / 2
    D = ((A + C) / 2) * B
    
    current_price = df['Close']
    normalized = ((D / current_price) - 0.5) * 100 + 50
    
    return normalized.clip(0, 100)
