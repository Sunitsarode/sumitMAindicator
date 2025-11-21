import json
import pandas as pd
from data.fetcher import fetch_data
from scoring.composite import calculate_all_indicators, calculate_composite_scores
from scoring.smoothing import apply_sma_smoothing
from utils.cache import update_cache
from utils.ath_atl import calculate_ath_atl, get_ath_atl

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)
# REPLACE fetch_initial_data() and update_all_data() in backend/utils/scheduler.py

def fetch_initial_data():
    """Fetch historical data once at startup using fetchOnceCandle periods"""
    config = load_config()
    print(f"\n=== Initial Historical Data Fetch ===")
    print(f"Started at {pd.Timestamp.now()}\n")
    
    for symbol in config['symbols']:
        symbol_data = {}
        
        for interval in config['intervals']:
            try:
                period = config['fetchOnceCandle'].get(interval, '7d')
                df = fetch_data(symbol, interval, period)
                
                if df is not None and not df.empty:
                    ath_atl_data = calculate_ath_atl(df, symbol, interval)
                    
                    scores = calculate_all_indicators(df, config, ath_atl_data)
                    scores = calculate_composite_scores(scores, config['timeframeWeights'])
                    scores = apply_sma_smoothing(
                        scores, 
                        config['indicators']['smoothing']['sma9'],
                        config['indicators']['smoothing']['sma21']
                    )
                    
                    combined = df.join(scores)
                    update_cache(symbol, interval, combined)
                    symbol_data[interval] = combined
                    print(f"✓ {symbol} at {interval}: Loaded {len(df)} candles\n")
                else:
                    print(f"✗ {symbol} at {interval}: No data received")
                
            except Exception as e:
                print(f"✗ {symbol} at {interval}: {str(e)}")
        
        # Calculate cross-timeframe score
        if '1m' in symbol_data and '5m' in symbol_data and '1h' in symbol_data:
            try:
                from indicators.sumit_ma import calculate_sumit_ma_cross
                cross_data = calculate_sumit_ma_cross(
                    symbol_data['1m'],
                    symbol_data['5m'],
                    symbol_data['1h']
                )
                # Store cross data with 1m timeframe
                cached_1m = symbol_data['1m'].copy()
                cached_1m['cross_avg_score'] = cross_data['cross_avg_score']
                cached_1m['cross_sma9'] = cross_data['cross_sma9']
                cached_1m['cross_sma21'] = cross_data['cross_sma21']
                update_cache(symbol, '1m', cached_1m)
                print(f"✓ {symbol}: Cross-timeframe scores calculated\n")
            except Exception as e:
                print(f"✗ {symbol}: Cross-timeframe error: {str(e)}")
                import traceback
                traceback.print_exc()
    
    print(f"\n=== Initial fetch completed ===\n")

def update_all_data():
    """Background job to update all symbols and intervals"""
    config = load_config()
    print(f"\n[Update] {pd.Timestamp.now()}")
    
    for symbol in config['symbols']:
        symbol_data = {}
        
        for interval in config['intervals']:
            try:
                period = config['fetchOnceCandle'].get(interval, '7d')
                df = fetch_data(symbol, interval, period)
                
                if df is not None and not df.empty:
                    from utils.ath_atl import get_ath_atl
                    ath_atl_data = get_ath_atl(symbol, interval)
                    
                    scores = calculate_all_indicators(df, config, ath_atl_data)
                    scores = calculate_composite_scores(scores, config['timeframeWeights'])
                    scores = apply_sma_smoothing(
                        scores, 
                        config['indicators']['smoothing']['sma9'],
                        config['indicators']['smoothing']['sma21']
                    )
                    
                    combined = df.join(scores)
                    update_cache(symbol, interval, combined)
                    symbol_data[interval] = combined
                    print(f"✓ {symbol}/{interval}: {len(df)} candles")
                
            except Exception as e:
                print(f"✗ {symbol}/{interval}: {str(e)}")
        
        # Calculate cross-timeframe score
        if '1m' in symbol_data and '5m' in symbol_data and '1h' in symbol_data:
            try:
                from indicators.sumit_ma import calculate_sumit_ma_cross
                cross_data = calculate_sumit_ma_cross(
                    symbol_data['1m'],
                    symbol_data['5m'],
                    symbol_data['1h']
                )
                cached_1m = symbol_data['1m'].copy()
                cached_1m['cross_avg_score'] = cross_data['cross_avg_score']
                cached_1m['cross_sma9'] = cross_data['cross_sma9']
                cached_1m['cross_sma21'] = cross_data['cross_sma21']



                update_cache(symbol, '1m', cached_1m)
            except Exception as e:
                print(f"✗ {symbol}: Cross error: {str(e)}")
                import traceback
                traceback.print_exc()