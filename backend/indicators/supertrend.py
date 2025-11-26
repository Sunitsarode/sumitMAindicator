import pandas as pd
import numpy as np
import pandas_ta as ta

# =============================================================
# SUPERTREND USING PANDAS_TA
# =============================================================

def apply_supertrend(df, period, multiplier):
    """
    Apply Supertrend using pandas_ta with flip detection
    Returns modified dataframe with supertrend columns
    """
    df = df.copy()
    
    # Calculate Supertrend using pandas_ta
    supertrend_df = df.ta.supertrend(length=period, multiplier=multiplier)

    # --- Defensive check ---
    # If supertrend_df is None or empty, it means calculation failed (likely not enough data)
    if supertrend_df is None or supertrend_df.empty:
        # Return original df with empty columns to avoid downstream errors
        df[f"st_{period}_{multiplier}"] = np.nan
        df[f"dir_{period}_{multiplier}"] = np.nan
        df[f"long_{period}_{multiplier}"] = np.nan
        df[f"short_{period}_{multiplier}"] = np.nan
        df[f"flip_{period}_{multiplier}"] = 0
        df[f"bullish_flip_{period}_{multiplier}"] = 0
        df[f"bearish_flip_{period}_{multiplier}"] = 0
        return df
    
    # Find column names, handling variations like '.0' suffix
    def find_col(prefix):
        exact_match = f"{prefix}_{period}_{multiplier}"
        if f"{exact_match}.0" in supertrend_df.columns:
            return f"{exact_match}.0"
        return exact_match if exact_match in supertrend_df.columns else None

    supert_col, supertd_col, supertl_col, superts_col = (
        find_col('SUPERT'), find_col('SUPERTd'), find_col('SUPERTl'), find_col('SUPERTs')
    )
    
    # If columns not found, return empty columns
    if not all([supert_col, supertd_col, supertl_col, superts_col]):
        df[f"st_{period}_{multiplier}"] = np.nan
        df[f"dir_{period}_{multiplier}"] = np.nan
        df[f"long_{period}_{multiplier}"] = np.nan
        df[f"short_{period}_{multiplier}"] = np.nan
        df[f"flip_{period}_{multiplier}"] = 0
        df[f"bullish_flip_{period}_{multiplier}"] = 0
        df[f"bearish_flip_{period}_{multiplier}"] = 0
        return df
    
    # Map to our naming convention
    df[f"st_{period}_{multiplier}"] = supertrend_df[supert_col]
    df[f"dir_{period}_{multiplier}"] = supertrend_df[supertd_col]
    df[f"long_{period}_{multiplier}"] = supertrend_df[supertl_col]
    df[f"short_{period}_{multiplier}"] = supertrend_df[superts_col]
    
    # Flip detection (direction change)
    df[f"flip_{period}_{multiplier}"] = df[f"dir_{period}_{multiplier}"].diff().fillna(0)
    
    # Bullish flip: direction changes from -1 to 1 (diff = 2)
    df[f"bullish_flip_{period}_{multiplier}"] = (df[f"flip_{period}_{multiplier}"] == 2).astype(int)
    
    # Bearish flip: direction changes from 1 to -1 (diff = -2)
    df[f"bearish_flip_{period}_{multiplier}"] = (df[f"flip_{period}_{multiplier}"] == -2).astype(int)
    
    return df


def calculate_mtf_supertrend_score(
    df_1m,
    df_5m,
    df_1h,
    st_settings=[(7, 3), (10, 2)]
):
    """
    NEW SIMPLIFIED Multi-Timeframe Supertrend Score
    
    Logic:
    - 3 timeframes (1m, 5m, 1h)
    - 2 supertrend settings per timeframe
    - Total: 6 supertrends (3 x 2)
    - Each supertrend: Green (bullish) = 1 point, Red (bearish) = 0 points
    - Total points: 0-6
    - Normalized to 0-100: (points / 6) * 100
    
    Returns:
        dict with:
        - total_points (0-6)
        - score_0_100 (0-100)
        - breakdown (dict of each timeframe/setting)
        - bullish_flip (bool)
        - bearish_flip (bool)
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
    
    # Count points for latest candle
    total_points = 0
    breakdown = {
        '1m': {},
        '5m': {},
        '1h': {}
    }
    
    bullish_flips = []
    bearish_flips = []
    
    def process_timeframe(df, tf_name):
        nonlocal total_points
        if df is None or df.empty:
            return

        for period, mult in st_settings:
            dir_col = f"dir_{period}_{mult}"
            bull_flip_col = f"bullish_flip_{period}_{mult}"
            bear_flip_col = f"bearish_flip_{period}_{mult}"

            if dir_col not in df.columns: continue

            direction = df[dir_col].iloc[-1]
            bullish_flip = df[bull_flip_col].iloc[-1]
            bearish_flip = df[bear_flip_col].iloc[-1]

            points = 1 if direction == 1 else 0
            total_points += points

            breakdown[tf_name][f'ST_{period}_{mult}'] = {
                'direction': 'bullish' if direction == 1 else 'bearish',
                'points': points,
                'bullish_flip': bool(bullish_flip),
                'bearish_flip': bool(bearish_flip)
            }

            if bullish_flip:
                bullish_flips.append(f"{tf_name}_ST{period}_{mult}")
            if bearish_flip:
                bearish_flips.append(f"{tf_name}_ST{period}_{mult}")

    process_timeframe(df_1m, '1m')
    process_timeframe(df_5m, '5m')
    process_timeframe(df_1h, '1h')
    
    # Normalize to 0-100
    max_points = 6
    score_normalized = (total_points / max_points) * 100
    
    return {
        "total_points": total_points,
        "score_0_100": round(score_normalized, 2),
        "breakdown": breakdown,
        "bullish_flip": len(bullish_flips) > 0,
        "bearish_flip": len(bearish_flips) > 0,
        "bullish_flip_list": bullish_flips,
        "bearish_flip_list": bearish_flips
    }


def get_supertrend_flip_status(df_1m, st_settings=[(7, 3), (10, 2)]):
    """
    Get flip status for 1m timeframe (for auto trader entry signals)
    
    Returns:
        dict with:
        - has_bullish_flip (bool): Any ST flipped to bullish
        - has_bearish_flip (bool): Any ST flipped to bearish
        - flip_details (list): Details of flips
    """
    df_1m = df_1m.copy()
    
    # Apply supertrends if not already applied
    for period, mult in st_settings:
        if f"bullish_flip_{period}_{mult}" not in df_1m.columns:
            df_1m = apply_supertrend(df_1m, period, mult)
    
    bullish_flips = []
    bearish_flips = []
    
    for period, mult in st_settings:
        if df_1m[f"bullish_flip_{period}_{mult}"].iloc[-1] == 1:
            bullish_flips.append(f"ST{period}_{mult}")
        
        if df_1m[f"bearish_flip_{period}_{mult}"].iloc[-1] == 1:
            bearish_flips.append(f"ST{period}_{mult}")
    
    return {
        'has_bullish_flip': len(bullish_flips) > 0,
        'has_bearish_flip': len(bearish_flips) > 0,
        'bullish_flip_list': bullish_flips,
        'bearish_flip_list': bearish_flips
    }


# =============================================================
# LEGACY FUNCTIONS (for compatibility)
# =============================================================

def calculate_supertrend(df, period=10, multiplier=3):
    """Legacy function - returns supertrend and direction"""
    df = df.copy()
    
    # Calculate using pandas_ta
    supertrend_df = df.ta.supertrend(length=period, multiplier=multiplier)
    
    supert_col = f'SUPERT_{period}_{multiplier}.0'
    supertd_col = f'SUPERTd_{period}_{multiplier}.0'
    
    result = pd.DataFrame(index=df.index)
    result['supertrend'] = supertrend_df[supert_col]
    result['direction'] = supertrend_df[supertd_col]
    
    return result


def score_supertrend(st1_direction, st2_direction):
    """
    Legacy Supertrend Score - DEPRECATED
    Use calculate_mtf_supertrend_score() instead
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
