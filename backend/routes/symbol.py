from flask import Blueprint, jsonify
from utils.cache import get_cache

symbol_bp = Blueprint('symbol', __name__)

@symbol_bp.route('/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """Get all data for a specific symbol"""
    data = get_cache(symbol)
    
    if not data:
        return jsonify({'error': 'Symbol not found'}), 404
    
    response = {}
    for interval, df in data.items():
        response[interval] = df.tail(200).to_dict('records')
    
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
            latest[interval] = df.iloc[-1].to_dict()
    
    return jsonify(latest)
