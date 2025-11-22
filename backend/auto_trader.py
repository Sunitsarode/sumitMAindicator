"""
AUTO TRADER - Runs 24/7 with Entry/Exit Criteria logging
"""
import json
import os
from datetime import datetime
from utils.cache import get_cache

TRADING_CONFIG = {
    'MAX_OPEN_POSITIONS': 3,
    'INITIAL_SL_POINTS': 20,
    'TRAILING_SL_POINTS': 15,
    'PROFIT_TARGET': 50,
    'MIN_SIGNAL_GAP_SECONDS': 60,
}

TRADES_DIR = 'trade_data'

def ensure_dir():
    if not os.path.exists(TRADES_DIR):
        os.makedirs(TRADES_DIR)

def get_filepath(symbol):
    safe_symbol = symbol.replace('^', '_').replace('-', '_')
    return os.path.join(TRADES_DIR, f'{safe_symbol}_trades.json')

def load_data(symbol):
    ensure_dir()
    filepath = get_filepath(symbol)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            if 'currentPosition' in data and data['currentPosition']:
                if 'openPositions' not in data:
                    data['openPositions'] = [data['currentPosition']]
                del data['currentPosition']
            if 'openPositions' not in data:
                data['openPositions'] = []
            return data
    return {'trades': [], 'openPositions': [], 'totalPL': 0}

def save_data(symbol, data):
    ensure_dir()
    filepath = get_filepath(symbol)
    data['lastUpdate'] = datetime.now().isoformat()
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_indicator_values(candle):
    """Extract all indicator values from candle for logging"""
    return {
        'rsi': float(candle.get('rsi_score', 50) or 50),
        'macd': float(candle.get('macd_score', 50) or 50),
        'adx': float(candle.get('adx_score', 50) or 50),
        'supertrend': float(candle.get('supertrend_score', 50) or 50),
        'sumit_ma': float(candle.get('sumit_ma_score', 50) or 50),
        'sumit_short': float(candle.get('sumit_ratio1_score', 50) or 50),
        'sumit_mid': float(candle.get('sumit_ratio2_score', 50) or 50),
        'sumit_long': float(candle.get('sumit_ratio3_score', 50) or 50),
        'cross_avg': float(candle.get('cross_avg_score', 0) or 0),
        'cross_sma9': float(candle.get('cross_sma9', 0) or 0),
        'cross_sma21': float(candle.get('cross_sma21', 0) or 0),
        'price': float(candle.get('Close', 0) or 0),
    }

def get_signal_strength(candle):
    """Calculate signal from indicator scores"""
    scores = [
        float(candle.get('rsi_score', 50) or 50),
        float(candle.get('macd_score', 50) or 50),
        float(candle.get('adx_score', 50) or 50),
        float(candle.get('supertrend_score', 50) or 50),
        float(candle.get('sumit_ma_score', 50) or 50),
    ]
    avg = sum(scores) / len(scores)
    
    if avg >= 75:
        return {'strength': 'STRONG LONG', 'score': avg, 'direction': 'LONG'}
    if avg >= 60:
        return {'strength': 'LONG', 'score': avg, 'direction': 'LONG'}
    if avg <= 25:
        return {'strength': 'STRONG SHORT', 'score': avg, 'direction': 'SHORT'}
    if avg <= 40:
        return {'strength': 'SHORT', 'score': avg, 'direction': 'SHORT'}
    return {'strength': 'NEUTRAL', 'score': avg, 'direction': None}

def get_sumit_ma_cross_signal(current_candle, prev_candle):
    """Sumit MA Cross Signal Logic"""
    curr_sma9 = float(current_candle.get('cross_sma9', 0) or 0)
    curr_sma21 = float(current_candle.get('cross_sma21', 0) or 0)
    curr_avg = float(current_candle.get('cross_avg_score', 50) or 50)
    prev_sma9 = float(prev_candle.get('cross_sma9', 0) or 0)
    prev_sma21 = float(prev_candle.get('cross_sma21', 0) or 0)
    
    if curr_sma9 == 0 or curr_sma21 == 0 or prev_sma9 == 0 or prev_sma21 == 0:
        return {'direction': None, 'strength': 'NO DATA', 'cross_point': 0}
    
    cross_point = curr_sma9
    downward_cross = (prev_sma9 >= prev_sma21) and (curr_sma9 < curr_sma21)
    upward_cross = (prev_sma9 <= prev_sma21) and (curr_sma9 > curr_sma21)
    
    if downward_cross and cross_point > curr_avg and cross_point > 60:
        return {'direction': 'SHORT', 'strength': 'CROSS SHORT', 'cross_point': cross_point, 'cross_avg': curr_avg, 'sma9': curr_sma9, 'sma21': curr_sma21}
    
    if upward_cross and cross_point < curr_avg and cross_point < 30:
        return {'direction': 'LONG', 'strength': 'CROSS LONG', 'cross_point': cross_point, 'cross_avg': curr_avg, 'sma9': curr_sma9, 'sma21': curr_sma21}
    
    return {'direction': None, 'strength': 'NO CROSS', 'cross_point': cross_point}

def can_open_new_position(data, direction, timestamp):
    open_positions = data.get('openPositions', [])
    if len(open_positions) >= TRADING_CONFIG['MAX_OPEN_POSITIONS']:
        return False, "Max positions reached"
    
    now = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if 'Z' in timestamp else datetime.fromisoformat(timestamp)
    for pos in open_positions:
        if pos['direction'] == direction:
            return False, "Same direction position exists"
        entry_time = datetime.fromisoformat(pos['entryTime'].replace('Z', '+00:00')) if 'Z' in pos['entryTime'] else datetime.fromisoformat(pos['entryTime'])
        if (now - entry_time).total_seconds() < TRADING_CONFIG['MIN_SIGNAL_GAP_SECONDS']:
            return False, "Too soon after last entry"
    return True, "OK"

def open_trade(data, signal, price, timestamp, signal_type, candle_dict):
    """Open new trade with entry criteria"""
    can_open, reason = can_open_new_position(data, signal['direction'], timestamp)
    if not can_open:
        return False
    
    sl = price - TRADING_CONFIG['INITIAL_SL_POINTS'] if signal['direction'] == 'LONG' else price + TRADING_CONFIG['INITIAL_SL_POINTS']
    
    # Capture entry criteria (indicator values at entry)
    entry_criteria = get_indicator_values(candle_dict)
    
    new_position = {
        'id': int(datetime.now().timestamp() * 1000),
        'direction': signal['direction'],
        'strength': signal['strength'],
        'score': signal.get('score', signal.get('cross_point', 0)),
        'signalType': signal_type,
        'entryPrice': price,
        'entryTime': timestamp,
        'stopLoss': sl,
        'highestPL': 0,
        'entryCriteria': entry_criteria,  # Store entry indicators
    }
    
    if 'cross_point' in signal:
        new_position['crossPoint'] = signal['cross_point']
        new_position['crossAvg'] = signal.get('cross_avg', 0)
    
    data['openPositions'].append(new_position)
    open_count = len(data['openPositions'])
    
    print(f"📈 OPENED {signal['direction']} [{signal_type}] #{open_count}/{TRADING_CONFIG['MAX_OPEN_POSITIONS']} @ {price:.2f} | SL: {sl:.2f}")
    print(f"   Entry: RSI={entry_criteria['rsi']:.0f} MACD={entry_criteria['macd']:.0f} ADX={entry_criteria['adx']:.0f} ST={entry_criteria['supertrend']:.0f} SMA={entry_criteria['sumit_ma']:.0f}")
    if entry_criteria['cross_sma9'] > 0:
        print(f"   Cross: Avg={entry_criteria['cross_avg']:.1f} SMA9={entry_criteria['cross_sma9']:.1f} SMA21={entry_criteria['cross_sma21']:.1f}")
    
    return True

def close_trade(data, position_id, exit_price, timestamp, reason, candle_dict):
    """Close trade with exit criteria"""
    open_positions = data.get('openPositions', [])
    pos = None
    pos_idx = None
    
    for i, p in enumerate(open_positions):
        if p['id'] == position_id:
            pos = p
            pos_idx = i
            break
    
    if pos is None:
        return False
    
    pl = exit_price - pos['entryPrice'] if pos['direction'] == 'LONG' else pos['entryPrice'] - exit_price
    
    # Capture exit criteria (indicator values at exit)
    exit_criteria = get_indicator_values(candle_dict)
    
    trade = {
        'id': pos['id'],
        'timestamp': timestamp,
        'entryTime': pos['entryTime'],
        'direction': pos['direction'],
        'strength': pos['strength'],
        'score': pos['score'],
        'signalType': pos.get('signalType', 'INDICATOR'),
        'entryPrice': pos['entryPrice'],
        'exitPrice': exit_price,
        'pl': pl,
        'reason': reason,
        'entryCriteria': pos.get('entryCriteria', {}),  # Entry indicators
        'exitCriteria': exit_criteria,  # Exit indicators
    }
    
    data['trades'].insert(0, trade)
    data['totalPL'] += pl
    data['openPositions'].pop(pos_idx)
    
    emoji = "✅" if pl > 0 else "❌"
    remaining = len(data['openPositions'])
    print(f"{emoji} CLOSED {pos['direction']} @ {exit_price:.2f} | P/L: {pl:+.2f} | Reason: {reason} | Open: {remaining}")
    print(f"   Exit: RSI={exit_criteria['rsi']:.0f} MACD={exit_criteria['macd']:.0f} ADX={exit_criteria['adx']:.0f} ST={exit_criteria['supertrend']:.0f} SMA={exit_criteria['sumit_ma']:.0f}")
    print(f"   Total P/L: {data['totalPL']:.2f}")
    
    return True

def process_symbol(symbol):
    """Process trading signals for a symbol"""
    cache = get_cache(symbol, '1m')
    if cache is None or len(cache) < 2:
        return
    
    latest = cache.iloc[-1]
    prev = cache.iloc[-2]
    price = float(latest['Close'])
    timestamp = datetime.now().isoformat()
    
    # Convert to dict for easier access
    latest_dict = latest.to_dict()
    prev_dict = prev.to_dict()
    
    data = load_data(symbol)
    
    indicator_signal = get_signal_strength(latest_dict)
    cross_signal = get_sumit_ma_cross_signal(latest_dict, prev_dict)
    
    open_positions = data.get('openPositions', [])
    positions_to_close = []
    
    for pos in open_positions:
        pl = price - pos['entryPrice'] if pos['direction'] == 'LONG' else pos['entryPrice'] - price
        
        if pl > 0:
            new_sl = price - TRADING_CONFIG['TRAILING_SL_POINTS'] if pos['direction'] == 'LONG' else price + TRADING_CONFIG['TRAILING_SL_POINTS']
            if (pos['direction'] == 'LONG' and new_sl > pos['stopLoss']) or (pos['direction'] == 'SHORT' and new_sl < pos['stopLoss']):
                pos['stopLoss'] = new_sl
                pos['highestPL'] = max(pl, pos.get('highestPL', 0))
        
        hit_sl = price <= pos['stopLoss'] if pos['direction'] == 'LONG' else price >= pos['stopLoss']
        if hit_sl:
            positions_to_close.append((pos['id'], 'SL'))
            continue
        
        if pl >= TRADING_CONFIG['PROFIT_TARGET']:
            positions_to_close.append((pos['id'], 'PROFIT'))
            continue
        
        if cross_signal['direction']:
            if (pos['direction'] == 'LONG' and cross_signal['direction'] == 'SHORT') or (pos['direction'] == 'SHORT' and cross_signal['direction'] == 'LONG'):
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
                continue
        
        if indicator_signal['direction'] and 'STRONG' in indicator_signal['strength']:
            if (pos['direction'] == 'LONG' and indicator_signal['direction'] == 'SHORT') or (pos['direction'] == 'SHORT' and indicator_signal['direction'] == 'LONG'):
                positions_to_close.append((pos['id'], 'REVERSAL'))
    
    for pos_id, reason in positions_to_close:
        close_trade(data, pos_id, price, timestamp, reason, latest_dict)
    
    if cross_signal['direction']:
        open_trade(data, cross_signal, price, timestamp, 'CROSS', latest_dict)
    elif indicator_signal['direction'] and ('STRONG' in indicator_signal['strength'] or indicator_signal['score'] >= 65 or indicator_signal['score'] <= 35):
        open_trade(data, indicator_signal, price, timestamp, 'INDICATOR', latest_dict)
    
    save_data(symbol, data)

def run_auto_trader():
    """Called by scheduler"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto Trader | Max Pos: {TRADING_CONFIG['MAX_OPEN_POSITIONS']}")
    
    for symbol in config['symbols']:
        try:
            process_symbol(symbol)
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()

def get_status():
    with open('config.json', 'r') as f:
        config = json.load(f)
    status = {'config': TRADING_CONFIG, 'symbols': {}}
    for symbol in config['symbols']:
        data = load_data(symbol)
        status['symbols'][symbol] = {
            'openPositions': len(data.get('openPositions', [])),
            'totalTrades': len(data.get('trades', [])),
            'totalPL': data.get('totalPL', 0),
            'positions': data.get('openPositions', [])
        }
    return status

if __name__ == '__main__':
    run_auto_trader()
