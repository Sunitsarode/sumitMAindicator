from datetime import datetime

MARKET_DATA_CACHE = {}
LAST_UPDATE = {}

def update_cache(symbol, interval, data):
    """Update cache for a specific symbol and interval"""
    if symbol not in MARKET_DATA_CACHE:
        MARKET_DATA_CACHE[symbol] = {}
    
    MARKET_DATA_CACHE[symbol][interval] = data
    LAST_UPDATE[f"{symbol}_{interval}"] = datetime.now()

def get_cache(symbol, interval=None):
    """Retrieve cached data"""
    if symbol not in MARKET_DATA_CACHE:
        return None
    
    if interval:
        return MARKET_DATA_CACHE[symbol].get(interval)
    
    return MARKET_DATA_CACHE[symbol]

def get_all_cache():
    """Get entire cache"""
    return MARKET_DATA_CACHE
