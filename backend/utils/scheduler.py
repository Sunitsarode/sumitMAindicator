import json
import pandas as pd
from data.fetcher import fetch_data
from scoring.composite import calculate_all_indicators, calculate_composite_scores
from scoring.smoothing import apply_sma_smoothing
from utils.cache import update_cache

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def fetch_initial_data():
    """Fetch historical data once at startup using fetchOnceCandle periods"""
    config = load_config()
    print(f"\n=== Initial Historical Data Fetch ===")
    print(f"Started at {pd.Timestamp.now()}\n")
    
    for symbol in config['symbols']:
        for interval in config['intervals']:
            try:
                # Use fetchOnceCandle for initial historical data
                period = config['fetchOnceCandle'].get(interval, '7d')
                df = fetch_data(symbol, interval, period)
                
                if df is not None and not df.empty:
                    # Need minimum candles for indicators
                    min_required = 201  # For Sumit MA (MA201)
                    
                    if len(df) < min_required:
                        print(f"⚠ {symbol} at {interval}: Only {len(df)} candles (need {min_required}), processing anyway...")
                    
                    scores = calculate_all_indicators(df, config)
                    scores = calculate_composite_scores(scores, config['timeframeWeights'])
                    scores = apply_sma_smoothing(
                        scores, 
                        config['indicators']['smoothing']['sma9'],
                        config['indicators']['smoothing']['sma21']
                    )
                    
                    combined = df.join(scores)
                    update_cache(symbol, interval, combined)
                    print(f"✓ {symbol} at {interval}: Loaded {len(df)} candles")
                else:
                    print(f"✗ {symbol} at {interval}: No data received")
                
            except Exception as e:
                print(f"✗ {symbol} at {interval}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    print(f"\n=== Initial fetch completed ===\n")

def update_all_data():
    """Background job to update all symbols and intervals"""
    config = load_config()
    print(f"\n[Update] {pd.Timestamp.now()}")
    
    for symbol in config['symbols']:
        for interval in config['intervals']:
            try:
                # Use fetchOnceCandle for updates to maintain historical data
                period = config['fetchOnceCandle'].get(interval, '7d')
                df = fetch_data(symbol, interval, period)
                
                if df is not None and not df.empty:
                    scores = calculate_all_indicators(df, config)
                    scores = calculate_composite_scores(scores, config['timeframeWeights'])
                    scores = apply_sma_smoothing(
                        scores, 
                        config['indicators']['smoothing']['sma9'],
                        config['indicators']['smoothing']['sma21']
                    )
                    
                    combined = df.join(scores)
                    update_cache(symbol, interval, combined)
                    print(f"✓ {symbol}/{interval}: {len(df)} candles")
                
            except Exception as e:
                print(f"✗ {symbol}/{interval}: {str(e)}")
