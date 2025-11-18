import pandas as pd
from indicators.rsi import calculate_rsi, score_rsi
from indicators.macd import calculate_macd, score_macd
from indicators.adx import calculate_adx, score_adx
from indicators.supertrend import calculate_supertrend, score_supertrend
from indicators.sumit_ma import calculate_sumit_ma

def calculate_all_indicators(df, config):
    """Calculate all indicators and return scored DataFrame"""
    scores = pd.DataFrame(index=df.index)
    
    # RSI
    rsi = calculate_rsi(df, config['indicators']['rsi']['period'])
    scores['rsi_score'] = rsi.apply(score_rsi)
    
    # MACD
    macd = calculate_macd(df)
    scores['macd_score'] = macd['MACD_diff'].apply(score_macd)
    
    # ADX
    adx_data = calculate_adx(df, config['indicators']['adx']['period'])
    scores['adx_score'] = adx_data.apply(
        lambda row: score_adx(row['ADX'], row['DI_plus'], row['DI_minus']), 
        axis=1
    )
    
    # Supertrend
    st1_config = config['indicators']['supertrend'][0]
    st2_config = config['indicators']['supertrend'][1]
    
    st1 = calculate_supertrend(df, st1_config['period'], st1_config['multiplier'])
    st2 = calculate_supertrend(df, st2_config['period'], st2_config['multiplier'])
    
    scores['supertrend_score'] = pd.Series(
        [score_supertrend(st1['direction'].iloc[i], st2['direction'].iloc[i]) 
         for i in range(len(df))],
        index=df.index
    )
    
    # Sumit MA
    scores['sumit_ma_score'] = calculate_sumit_ma(df)
    
    return scores

def calculate_composite_scores(scores, weights):
    """Calculate average and weighted average composite scores"""
    scores['avg_score'] = (
        scores['rsi_score'] + 
        scores['macd_score'] + 
        scores['adx_score'] + 
        scores['supertrend_score']
    ) / 4
    
    scores['weighted_avg_score'] = (
        scores['rsi_score'] * 0.25 + 
        scores['macd_score'] * 0.25 + 
        scores['adx_score'] * 0.25 + 
        scores['supertrend_score'] * 0.25
    )
    
    return scores
