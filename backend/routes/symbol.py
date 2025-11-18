from flask import Blueprint, jsonify
from utils.cache import get_cache
import numpy as np
import pandas as pd

symbol_bp = Blueprint('symbol', __name__)

def clean_nan_values(obj):
    """Replace NaN, Infinity with None for valid JSON"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    return obj

@symbol_bp.route('/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """Get all data for a specific symbol"""
    data = get_cache(symbol)
    
    if not data:
        return jsonify({'error': 'Symbol not found'}), 404
    
    response = {}
    for interval, df in data.items():
        # Reset index to include datetime as a column
        df_copy = df.tail(200).copy()
        df_copy['Datetime'] = df_copy.index.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert to dict and replace NaN with None
        records = df_copy.replace([np.nan, np.inf, -np.inf], None).to_dict('records')
        response[interval] = records
    
    return jsonify(response)

@symbol_bp.route('/<symbol>/latest', methods=['GET'])
def get_latest(symbol):
    """Get latest scores for a symbol"""
    data = get_cache(symbol)
    
    if not data:
        return jsonify({'error': 'Symbol not found'}), 404
    
    latest = {}
    for interval, df in data.items():
        if len(df) > 0:
            # Get last row and replace NaN
            last_row = df.iloc[-1].replace([np.nan, np.inf, -np.inf], None).to_dict()
            latest[interval] = last_row
    
    return jsonify(latest)
