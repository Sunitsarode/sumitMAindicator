import pandas as pd
import numpy as np
from indicators.rsi import calculate_rsi, score_rsi
from indicators.macd import calculate_macd, score_macd
from indicators.adx import calculate_adx, score_adx
from indicators.supertrend import calculate_supertrend, score_supertrend
from indicators.sumit_ma import calculate_sumit_ma

def calculate_all_indicators(df, config):
    """Calculate all indicators and return scored DataFrame with error handling"""
    
    # Minimum data requirements
    min_required = max(
        config['indicators']['rsi']['period'],
        config['indicators']['adx']['period'],
        config['indicators']['sumit_ma']['ma201'],
        max([st['period'] for st in config['indicators']['supertrend']])
    )
    
    scores = pd.DataFrame(index=df.index)
    
    # Initialize with neutral scores
    scores['rsi_score'] = 50.0
    scores['macd_score'] = 50.0
    scores['adx_score'] = 50.0
    scores['supertrend_score'] = 50.0
    scores['sumit_ma_score'] = 50.0
    
    if len(df) < min_required:
        print(f"⚠ Warning: Only {len(df)} candles available, need {min_required} for full indicators")
    
    # RSI - needs 14+ candles
    try:
        if len(df) >= config['indicators']['rsi']['period']:
            rsi = calculate_rsi(df, config['indicators']['rsi']['period'])
            scores['rsi_score'] = rsi.apply(score_rsi)
    except Exception as e:
        print(f"RSI calculation error: {e}")
    
    # MACD - needs 26+ candles
    try:
        if len(df) >= 26:
            macd = calculate_macd(df)
            scores['macd_score'] = macd['MACD_diff'].apply(score_macd)
    except Exception as e:
        print(f"MACD calculation error: {e}")
    
    # ADX - needs 14+ candles
    try:
        if len(df) >= config['indicators']['adx']['period']:
            adx_data = calculate_adx(df, config['indicators']['adx']['period'])
            scores['adx_score'] = adx_data.apply(
                lambda row: score_adx(row['ADX'], row['DI_plus'], row['DI_minus']), 
                axis=1
            )
    except Exception as e:
        print(f"ADX calculation error: {e}")
    
    # Supertrend - needs period+ candles
    try:
        st1_config = config['indicators']['supertrend'][0]
        st2_config = config['indicators']['supertrend'][1]
        
        max_st_period = max(st1_config['period'], st2_config['period'])
        
        if len(df) >= max_st_period:
            st1 = calculate_supertrend(df, st1_config['period'], st1_config['multiplier'])
            st2 = calculate_supertrend(df, st2_config['period'], st2_config['multiplier'])
            
            scores['supertrend_score'] = pd.Series(
                [score_supertrend(
                    st1['direction'].iloc[i] if i < len(st1) else np.nan, 
                    st2['direction'].iloc[i] if i < len(st2) else np.nan
                ) for i in range(len(df))],
                index=df.index
            )
    except Exception as e:
        print(f"Supertrend calculation error: {e}")
    
    # Sumit MA - needs 201+ candles
    try:
        if len(df) >= config['indicators']['sumit_ma']['ma201']:
            sumit_scores = calculate_sumit_ma(
                df,
                config['indicators']['sumit_ma']['ma9'],
                config['indicators']['sumit_ma']['ma51'],
                config['indicators']['sumit_ma']['ma101'],
                config['indicators']['sumit_ma']['ma201']
            )
            scores['sumit_ma_score'] = sumit_scores
            print(f"✓ Sumit MA: {sumit_scores.notna().sum()} valid scores")
        else:
            print(f"⚠ Sumit MA skipped: {len(df)} candles < 201 required")
    except Exception as e:
        print(f"✗ Sumit MA calculation error: {e}")
        import traceback
        traceback.print_exc()
    
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
