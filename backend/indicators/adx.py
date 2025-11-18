import pandas as pd
from ta.trend import ADXIndicator

def calculate_adx(df, period=14):
    """Calculate ADX with +DI and -DI using ta library"""
    adx_indicator = ADXIndicator(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=period
    )
    
    result = pd.DataFrame(index=df.index)
    result['ADX'] = adx_indicator.adx()
    result['DI_plus'] = adx_indicator.adx_pos()
    result['DI_minus'] = adx_indicator.adx_neg()
    
    return result

def score_adx(adx_value, plus_di, minus_di):
    """
    ADX Score:
    - If +DI > -DI (bullish): Score = ADX value
    - If -DI > +DI (bearish): Score = 100 - ADX value
    """
    if pd.isna(adx_value) or pd.isna(plus_di) or pd.isna(minus_di):
        return 50.0
    
    adx_val = float(adx_value)
    
    if plus_di > minus_di:
        return min(100, adx_val)
    else:
        return max(0, 100 - adx_val)
