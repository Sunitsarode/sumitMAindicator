from flask import Blueprint, jsonify
from utils.cache import get_all_cache
import json

dashboard_bp = Blueprint('dashboard', __name__)

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

@dashboard_bp.route('', methods=['GET'])
def get_dashboard():
    """Get overview of all symbols with latest scores"""
    cache = get_all_cache()
    config = load_config()
    
    dashboard_data = []
    
    for symbol in config['symbols']:
        if symbol in cache:
            symbol_data = {
                'symbol': symbol,
                'intervals': {}
            }
            
            for interval in config['intervals']:
                if interval in cache[symbol]:
                    df = cache[symbol][interval]
                    if len(df) > 0:
                        latest = df.iloc[-1]
                        
                        symbol_data['intervals'][interval] = {
                            'price': float(latest['Close']),
                            'rsi_score': float(latest.get('rsi_score', 50)),
                            'macd_score': float(latest.get('macd_score', 50)),
                            'adx_score': float(latest.get('adx_score', 50)),
                            'supertrend_score': float(latest.get('supertrend_score', 50)),
                            'avg_score': float(latest.get('avg_score', 50)),
                            'weighted_avg_score': float(latest.get('weighted_avg_score', 50))
                        }
            
            dashboard_data.append(symbol_data)
    
    return jsonify(dashboard_data)
