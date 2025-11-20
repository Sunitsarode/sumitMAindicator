import pandas as pd

# Global storage for ATH/ATL data
ATH_ATL_CACHE = {}

def calculate_ath_atl(df, symbol, interval):
    """
    Calculate ATH, ATL, ratio, and dynamic sensitivity
    Call this ONCE on initial data load
    """
    if df is None or len(df) == 0:
        return None
    
    ath = float(df['High'].max())
    atl = float(df['Low'].min())
    
    if atl == 0:
        return None
    
    ath_atl_ratio = ath / atl
    range_percentage = (ath_atl_ratio - 1) * 100
    
    # Dynamic sensitivity based on range
    if range_percentage < 5:
        sensitivity = 25000
    elif range_percentage < 20:
        sensitivity = 10000
    elif range_percentage < 50:
        sensitivity = 5000
    else:
        sensitivity = 2500
    
    # Store in cache
    key = f"{symbol}_{interval}"
    ATH_ATL_CACHE[key] = {
        'ath': ath,
        'atl': atl,
        'ath_atl_ratio': ath_atl_ratio,
        'sensitivity': sensitivity,
        'range_percentage': range_percentage
    }
    
    print(f"ATH/ATL for {symbol} ({interval}):")
    print(f"  ATH: ${ath:.2f}")
    print(f"  ATL: ${atl:.2f}")
    print(f"  Ratio: {ath_atl_ratio:.4f} ({range_percentage:.2f}% range)")
    print(f"  Dynamic Sensitivity: {sensitivity}")
    
    return ATH_ATL_CACHE[key]

def get_ath_atl(symbol, interval):
    """Get cached ATH/ATL data"""
    key = f"{symbol}_{interval}"
    return ATH_ATL_CACHE.get(key)

def get_all_ath_atl():
    """Get all ATH/ATL cache"""
    return ATH_ATL_CACHE
