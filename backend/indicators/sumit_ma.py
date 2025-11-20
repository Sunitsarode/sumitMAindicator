import pandas as pd
import numpy as np

def calculate_sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_sumit_ma(df, ma1=3, ma2=21, ma3=101, ma4=201, ath_atl_data=None):
    """
    Calculate Sumit MA Indicator using ATH/ATL Normalized MA Ratios:
    Ratio1 = (MA-1 / MA-2) / (ATH / ATL)
    Ratio2 = (MA-2 / MA-3) / (ATH / ATL)
    Ratio3 = (MA-3 / MA-4) / (ATH / ATL)
    
    Returns DataFrame with 3 ratio scores (0-100 each) normalized by ATH/ATL
    """
    sma1 = calculate_sma(df['Close'], ma1)
    sma2 = calculate_sma(df['Close'], ma2)
    sma3 = calculate_sma(df['Close'], ma3)
    sma4 = calculate_sma(df['Close'], ma4)
    
    # Calculate raw ratios
    ratio1 = sma1 / sma2    # Short-term
    ratio2 = sma2 / sma3    # Mid-term
    ratio3 = sma3 / sma4    # Long-term
    
    result = pd.DataFrame(index=df.index)
    
    # Initialize with default values
    result['sumit_ratio1_score'] = pd.Series(dtype=float)
    result['sumit_ratio2_score'] = pd.Series(dtype=float)
    result['sumit_ratio3_score'] = pd.Series(dtype=float)
    result['sumit_ma_score'] = pd.Series(dtype=float)
    
    # Valid mask - only calculate where all MAs exist
    valid_mask = ~(ratio1.isna() | ratio2.isna() | ratio3.isna())
    
    if not valid_mask.any():
        return result
    
    # Get ATH/ATL data if provided
    if ath_atl_data:
        ath_atl_ratio = ath_atl_data['ath_atl_ratio']
        sensitivity = ath_atl_data['sensitivity']
        
        # Normalize ratios by ATH/ATL
        norm_ratio1 = ratio1 / ath_atl_ratio
        norm_ratio2 = ratio2 / ath_atl_ratio
        norm_ratio3 = ratio3 / ath_atl_ratio
        
        # Convert normalized ratios to scores (0-100)
        # Score = 50 + ((Normalized_Ratio - 1) × Sensitivity)
        result.loc[valid_mask, 'sumit_ratio1_score'] = (
            50 + ((norm_ratio1[valid_mask] - 1) * sensitivity)
        ).clip(0, 100)
        
        result.loc[valid_mask, 'sumit_ratio2_score'] = (
            50 + ((norm_ratio2[valid_mask] - 1) * sensitivity)
        ).clip(0, 100)
        
        result.loc[valid_mask, 'sumit_ratio3_score'] = (
            50 + ((norm_ratio3[valid_mask] - 1) * sensitivity)
        ).clip(0, 100)
        
    else:
        # Fallback: Use old method without ATH/ATL normalization
        multiplier = 5000
        
        result.loc[valid_mask, 'sumit_ratio1_score'] = (
            50 + ((ratio1[valid_mask] - 1) * multiplier)
        ).clip(0, 100)
        
        result.loc[valid_mask, 'sumit_ratio2_score'] = (
            50 + ((ratio2[valid_mask] - 1) * multiplier)
        ).clip(0, 100)
        
        result.loc[valid_mask, 'sumit_ratio3_score'] = (
            50 + ((ratio3[valid_mask] - 1) * multiplier)
        ).clip(0, 100)
    
    # Average of all three ratios
    result.loc[valid_mask, 'sumit_ma_score'] = (
        result.loc[valid_mask, 'sumit_ratio1_score'] + 
        result.loc[valid_mask, 'sumit_ratio2_score'] + 
        result.loc[valid_mask, 'sumit_ratio3_score']
    ) / 3
    
    return result
