from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime

trades_bp = Blueprint('trades', __name__)

# Directory to store trade data
TRADES_DIR = 'trade_data'

def ensure_dir():
    if not os.path.exists(TRADES_DIR):
        os.makedirs(TRADES_DIR)

def get_filepath(symbol):
    # Replace invalid filename chars
    safe_symbol = symbol.replace('^', '_').replace('-', '_')
    return os.path.join(TRADES_DIR, f'{safe_symbol}_trades.json')

@trades_bp.route('/save', methods=['POST'])
def save_trades():
    """Save trades and current position to file"""
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        ensure_dir()
        filepath = get_filepath(symbol)
        
        save_data = {
            'symbol': symbol,
            'trades': data.get('trades', []),
            'currentPosition': data.get('currentPosition'),
            'totalPL': data.get('totalPL', 0),
            'lastUpdate': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return jsonify({'status': 'saved', 'file': filepath})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/load/<symbol>', methods=['GET'])
def load_trades(symbol):
    """Load trades and current position from file"""
    try:
        ensure_dir()
        filepath = get_filepath(symbol)
        
        if not os.path.exists(filepath):
            return jsonify(None)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/report/<symbol>', methods=['GET'])
def get_report(symbol):
    """Generate trading report"""
    try:
        ensure_dir()
        filepath = get_filepath(symbol)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'No data found'}), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        trades = data.get('trades', [])
        total_pl = data.get('totalPL', 0)
        
        # Calculate stats
        wins = [t for t in trades if t.get('pl', 0) > 0]
        losses = [t for t in trades if t.get('pl', 0) <= 0]
        
        report = {
            'symbol': symbol,
            'totalTrades': len(trades),
            'totalPL': total_pl,
            'wins': len(wins),
            'losses': len(losses),
            'winRate': (len(wins) / len(trades) * 100) if trades else 0,
            'avgWin': sum(t['pl'] for t in wins) / len(wins) if wins else 0,
            'avgLoss': sum(t['pl'] for t in losses) / len(losses) if losses else 0,
            'largestWin': max((t['pl'] for t in wins), default=0),
            'largestLoss': min((t['pl'] for t in losses), default=0),
            'currentPosition': data.get('currentPosition'),
            'lastUpdate': data.get('lastUpdate'),
            'trades': trades[:50]  # Last 50 trades
        }
        
        return jsonify(report)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/clear/<symbol>', methods=['DELETE'])
def clear_trades(symbol):
    """Clear all trade data for symbol"""
    try:
        filepath = get_filepath(symbol)
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'status': 'cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
