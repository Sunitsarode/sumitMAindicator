import pandas as pd
import numpy as np

def calculate_supertrend(df, period=10, multiplier=3):
    """
    Calculate Supertrend indicator manually
    Returns DataFrame with 'supertrend' and 'direction' columns
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # Calculate ATR (Average True Range)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate basic upper and lower bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Initialize Supertrend
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    for i in range(period, len(df)):
        if i == period:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
        else:
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif close.iloc[i] < supertrend.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
    
    result = pd.DataFrame(index=df.index)
    result['supertrend'] = supertrend
    result['direction'] = direction
    
    return result

def score_supertrend(st1_direction, st2_direction):
    """
    Supertrend Score:
    - Both uptrend = 100
    - Both downtrend = 0
    - Mixed = 50
    - Adjustment: +15 for uptrend, -15 for downtrend
    """
    if pd.isna(st1_direction) or pd.isna(st2_direction):
        return 50.0
    
    st1 = int(st1_direction)
    st2 = int(st2_direction)
    
    if st1 == 1 and st2 == 1:
        base_score = 100
    elif st1 == -1 and st2 == -1:
        base_score = 0
    else:
        base_score = 50
    
    if st1 == 1:
        base_score += 15
    else:
        base_score -= 15
    
    if st2 == 1:
        base_score += 15
    else:
        base_score -= 15
    
    return max(0, min(100, base_score))
