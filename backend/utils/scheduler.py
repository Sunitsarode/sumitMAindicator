import json
import pandas as pd
from data.fetcher import fetch_data
from scoring.composite import calculate_all_indicators, calculate_composite_scores
from scoring.smoothing import apply_sma_smoothing
from utils.cache import update_cache

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def update_all_data():
    """Background job to update all symbols and intervals"""
    config = load_config()
    print(f"\nUpdating data at {pd.Timestamp.now()}")
    
    for symbol in config['symbols']:
        for interval in config['intervals']:
            try:
                period = config['candlesPerInterval'].get(interval, '1d')
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
                    print(f"✓ Updated {symbol} at {interval} ({len(df)} candles)")
                
            except Exception as e:
                print(f"✗ Error updating {symbol} at {interval}: {str(e)}")
