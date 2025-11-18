import yfinance as yf
import pandas as pd
import json
from datetime import datetime

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def fetch_data(symbol, interval, period):
    """
    Fetch OHLC data from yfinance
    Note: 1m data limited to last 7 days
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"Warning: No data retrieved for {symbol} at {interval}")
            return None
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return df
    
    except Exception as e:
        print(f"Error fetching data for {symbol} at {interval}: {str(e)}")
        return None

def fetch_all_symbols():
    """Fetch data for all configured symbols and intervals"""
    config = load_config()
    data_cache = {}
    
    for symbol in config['symbols']:
        data_cache[symbol] = {}
        
        for interval in config['intervals']:
            period = config['candlesPerInterval'].get(interval, '1d')
            df = fetch_data(symbol, interval, period)
            
            if df is not None:
                data_cache[symbol][interval] = df
                print(f"Fetched {len(df)} candles for {symbol} at {interval}")
    
    return data_cache
