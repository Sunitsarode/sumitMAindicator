import pandas as pd
import numpy as np
from ta.trend import SuperTrend

# =============================================================
# APPLY SUPERTREND WITH FLIP DETECTION
# =============================================================
def apply_supertrend(df, period, multiplier):
    """
    Apply Supertrend using ta library with flip detection
    Returns modified dataframe with supertrend columns
    """
    st = SuperTrend(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=period,
        multiplier=multiplier
    )
    
    df[f"st_{period}_{multiplier}"] = st.super_trend()
    df[f"dir_{period}_{multiplier}"] = st.super_trend_direction()
    df[f"long_{period}_{multiplier}"] = st.super_trend_long()
    df[f"short_{period}_{multiplier}"] = st.super_trend_short()
    
    # Flip detection (direction change)
    df[f"flip_{period}_{multiplier}"] = df[f"dir_{period}_{multiplier}"].diff().fillna(0)
    
    # Bullish flip: direction changes from -1 to 1 (diff = 2)
    df[f"bullish_flip_{period}_{multiplier}"] = (df[f"flip_{period}_{multiplier}"] == 2).astype(int)
    
    # Bearish flip: direction changes from 1 to -1 (diff = -2)
    df[f"bearish_flip_{period}_{multiplier}"] = (df[f"flip_{period}_{multiplier}"] == -2).astype(int)
    
    return df

# =============================================================
# SCORE A SINGLE SUPERTREND
# =============================================================
def score_single_supertrend(row, period, multiplier):
    """
    Score individual supertrend:
    - Long trend: +1
    - Short trend: -1
    - Bullish flip: +1 bonus
    - Bearish flip: -1 penalty
    Range: -2 to +2
    """
    long_col = f"long_{period}_{multiplier}"
    flip_col_b = f"bullish_flip_{period}_{multiplier}"
    flip_col_s = f"bearish_flip_{period}_{multiplier}"
    
    score = 0
    
    # Trend score
    if row[long_col]:
        score += 1
    else:
        score -= 1
    
    # Flip bonus/penalty
    if row[flip_col_b] == 1:
        score += 1
    if row[flip_col_s] == 1:
        score -= 1
    
    return score

# =============================================================
# MULTI-TIMEFRAME (MTF) SUPERTREND SCORING
# =============================================================
def calculate_mtf_supertrend_score(
    df_1m,
    df_5m,
    df_1h,
    st_settings=[(7, 3), (10, 2)],
    weights={"1m": 1, "5m": 2, "1h": 4}
):
    """
    Calculate Multi-Timeframe Supertrend Score
    
    Args:
        df_1m, df_5m, df_1h: DataFrames with OHLC data
        st_settings: List of (period, multiplier) tuples
        weights: Timeframe weights (higher = more important)
    
    Returns:
        dict with raw_score, score_0_100
    """
    # Make copies
    df_1m = df_1m.copy()
    df_5m = df_5m.copy()
    df_1h = df_1h.copy()
    
    # Apply each supertrend setting to all timeframes
    for period, mult in st_settings:
        df_1m = apply_supertrend(df_1m, period, mult)
        df_5m = apply_supertrend(df_5m, period, mult)
        df_1h = apply_supertrend(df_1h, period, mult)
    
    # Score each timeframe
    def score_tf(df, tf_label):
        total = 0
        for period, mult in st_settings:
            total += df.apply(lambda row: score_single_supertrend(row, period, mult), axis=1)
        return total * weights[tf_label]
    
    df_1m["tf_score"] = score_tf(df_1m, "1m")
    df_5m["tf_score"] = score_tf(df_5m, "5m")
    df_1h["tf_score"] = score_tf(df_1h, "1h")
    
    # Combine MTF score
    final_score = df_1m["tf_score"].iloc[-1] + df_5m["tf_score"].iloc[-1] + df_1h["tf_score"].iloc[-1]
    
    # Max possible score: (num_supertrends * 2 * weight) per timeframe
    max_score = sum((2 * len(st_settings) * weights[tf]) for tf in ["1m", "5m", "1h"])
    
    # Normalize to 0-100
    final_score_normalized = ((final_score + max_score) / (2 * max_score)) * 100
    
    return {
        "raw_score": final_score,
        "score_0_100": round(final_score_normalized, 2),
    }

# =============================================================
# LEGACY SCORING (FOR COMPATIBILITY)
# =============================================================
def calculate_supertrend(df, period=10, multiplier=3):
    """Legacy function - returns supertrend and direction"""
    st = SuperTrend(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=period,
        multiplier=multiplier
    )
    
    result = pd.DataFrame(index=df.index)
    result['supertrend'] = st.super_trend()
    result['direction'] = st.super_trend_direction()
    
    return result

def score_supertrend(st1_direction, st2_direction):
    """
    Legacy Supertrend Score:
    - Both uptrend = 100
    - Both downtrend = 0
    - Mixed = 50
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
