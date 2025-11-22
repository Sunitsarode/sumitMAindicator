"""
AUTO TRADER - Runs 24/7 on server without browser
Supports multiple open positions with Sumit MA Cross signals
"""
import json
import os
from datetime import datetime
from utils.cache import get_cache

# Config
TRADING_CONFIG = {
    'MAX_OPEN_POSITIONS': 1,
    'INITIAL_SL_POINTS': 50,
    'TRAILING_SL_POINTS': 15,
    'PROFIT_TARGET': 100,
    'MIN_SIGNAL_GAP_SECONDS': 300,
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
    """
    Sumit MA Cross Signal Logic:
    
    SHORT: SMA9 crosses SMA21 downward AND crossing_point > cross_avg AND crossing_point > 60
    LONG:  SMA9 crosses SMA21 upward AND crossing_point < cross_avg AND crossing_point < 30
    
    Returns: {'direction': 'LONG'/'SHORT'/None, 'strength': str, 'cross_point': float}
    """
    # Get current values
    curr_sma9 = float(current_candle.get('cross_sma9', 0) or 0)
    curr_sma21 = float(current_candle.get('cross_sma21', 0) or 0)
    curr_avg = float(current_candle.get('cross_avg_score', 50) or 50)
    
    # Get previous values
    prev_sma9 = float(prev_candle.get('cross_sma9', 0) or 0)
    prev_sma21 = float(prev_candle.get('cross_sma21', 0) or 0)
    
    # Skip if no valid data
    if curr_sma9 == 0 or curr_sma21 == 0 or prev_sma9 == 0 or prev_sma21 == 0:
        return {'direction': None, 'strength': 'NO DATA', 'cross_point': 0}
    
    # Calculate crossing point (average of SMA9 at cross)
    cross_point = curr_sma9
    
    # Detect crossover
    # Downward cross: prev SMA9 >= prev SMA21 AND curr SMA9 < curr SMA21
    downward_cross = (prev_sma9 >= prev_sma21) and (curr_sma9 < curr_sma21)
    
    # Upward cross: prev SMA9 <= prev SMA21 AND curr SMA9 > curr SMA21
    upward_cross = (prev_sma9 <= prev_sma21) and (curr_sma9 > curr_sma21)
    
    # SHORT Signal: Downward cross + cross_point > cross_avg + cross_point > 60
    if downward_cross and cross_point > curr_avg and cross_point > 60:
        return {
            'direction': 'SHORT',
            'strength': 'CROSS SHORT',
            'cross_point': cross_point,
            'cross_avg': curr_avg,
            'sma9': curr_sma9,
            'sma21': curr_sma21
        }
    
    # LONG Signal: Upward cross + cross_point < cross_avg + cross_point < 30
    if upward_cross and cross_point < curr_avg and cross_point < 30:
        return {
            'direction': 'LONG',
            'strength': 'CROSS LONG',
            'cross_point': cross_point,
            'cross_avg': curr_avg,
            'sma9': curr_sma9,
            'sma21': curr_sma21
        }
    
    return {'direction': None, 'strength': 'NO CROSS', 'cross_point': cross_point}

def can_open_new_position(data, direction, timestamp):
    """Check if we can open a new position"""
    open_positions = data.get('openPositions', [])
    
    if len(open_positions) >= TRADING_CONFIG['MAX_OPEN_POSITIONS']:
        return False, "Max positions reached"
    
    now = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if 'Z' in timestamp else datetime.fromisoformat(timestamp)
    for pos in open_positions:
        if pos['direction'] == direction:
            return False, "Same direction position exists"
        
        entry_time = datetime.fromisoformat(pos['entryTime'].replace('Z', '+00:00')) if 'Z' in pos['entryTime'] else datetime.fromisoformat(pos['entryTime'])
        gap = (now - entry_time).total_seconds()
        if gap < TRADING_CONFIG['MIN_SIGNAL_GAP_SECONDS']:
            return False, "Too soon after last entry"
    
    return True, "OK"

def open_trade(data, signal, price, timestamp, signal_type='INDICATOR'):
    """Open new trade"""
    can_open, reason = can_open_new_position(data, signal['direction'], timestamp)
    if not can_open:
        return False
    
    sl = price - TRADING_CONFIG['INITIAL_SL_POINTS'] if signal['direction'] == 'LONG' else price + TRADING_CONFIG['INITIAL_SL_POINTS']
    
    new_position = {
        'id': int(datetime.now().timestamp() * 1000),
        'direction': signal['direction'],
        'strength': signal['strength'],
        'score': signal.get('score', signal.get('cross_point', 0)),
        'signalType': signal_type,  # 'INDICATOR' or 'CROSS'
        'entryPrice': price,
        'entryTime': timestamp,
        'stopLoss': sl,
        'highestPL': 0
    }
    
    # Add cross details if available
    if 'cross_point' in signal:
        new_position['crossPoint'] = signal['cross_point']
        new_position['crossAvg'] = signal.get('cross_avg', 0)
    
    data['openPositions'].append(new_position)
    open_count = len(data['openPositions'])
    
    print(f"📈 OPENED {signal['direction']} [{signal_type}] #{open_count}/{TRADING_CONFIG['MAX_OPEN_POSITIONS']} @ {price:.2f} | SL: {sl:.2f} | {signal['strength']}")
    if 'cross_point' in signal:
        print(f"   Cross Point: {signal['cross_point']:.2f} | Cross Avg: {signal.get('cross_avg', 0):.2f}")
    
    return True

def close_trade(data, position_id, exit_price, timestamp, reason):
    """Close specific trade by ID"""
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
        'reason': reason
    }
    
    data['trades'].insert(0, trade)
    data['totalPL'] += pl
    data['openPositions'].pop(pos_idx)
    
    emoji = "✅" if pl > 0 else "❌"
    remaining = len(data['openPositions'])
    print(f"{emoji} CLOSED {pos['direction']} @ {exit_price:.2f} | P/L: {pl:+.2f} | Reason: {reason} | Open: {remaining} | Total P/L: {data['totalPL']:.2f}")
    return True

def process_symbol(symbol):
    """Process trading signals for a symbol"""
    cache = get_cache(symbol, '1m')
    if cache is None or len(cache) < 2:
        return
    
    # Get latest and previous candle
    latest = cache.iloc[-1]
    prev = cache.iloc[-2]
    price = float(latest['Close'])
    timestamp = datetime.now().isoformat()
    
    # Load saved data
    data = load_data(symbol)
    
    # Get both signal types
    indicator_signal = get_signal_strength(latest.to_dict())
    cross_signal = get_sumit_ma_cross_signal(latest.to_dict(), prev.to_dict())
    
    open_positions = data.get('openPositions', [])
    
    # Process each open position
    positions_to_close = []
    
    for pos in open_positions:
        pl = price - pos['entryPrice'] if pos['direction'] == 'LONG' else pos['entryPrice'] - price
        
        # Update trailing SL
        if pl > 0:
            new_sl = price - TRADING_CONFIG['TRAILING_SL_POINTS'] if pos['direction'] == 'LONG' else price + TRADING_CONFIG['TRAILING_SL_POINTS']
            if (pos['direction'] == 'LONG' and new_sl > pos['stopLoss']) or \
               (pos['direction'] == 'SHORT' and new_sl < pos['stopLoss']):
                pos['stopLoss'] = new_sl
                pos['highestPL'] = max(pl, pos.get('highestPL', 0))
        
        # Check SL
        hit_sl = price <= pos['stopLoss'] if pos['direction'] == 'LONG' else price >= pos['stopLoss']
        if hit_sl:
            positions_to_close.append((pos['id'], 'SL'))
            continue
        
        # Check profit target
        if pl >= TRADING_CONFIG['PROFIT_TARGET']:
            positions_to_close.append((pos['id'], 'PROFIT'))
            continue
        
        # Check reversal from CROSS signal (stronger)
        if cross_signal['direction']:
            if (pos['direction'] == 'LONG' and cross_signal['direction'] == 'SHORT') or \
               (pos['direction'] == 'SHORT' and cross_signal['direction'] == 'LONG'):
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
                continue
        
        # Check reversal from indicator (only STRONG)
        if indicator_signal['direction'] and 'STRONG' in indicator_signal['strength']:
            if (pos['direction'] == 'LONG' and indicator_signal['direction'] == 'SHORT') or \
               (pos['direction'] == 'SHORT' and indicator_signal['direction'] == 'LONG'):
                positions_to_close.append((pos['id'], 'REVERSAL'))
    
    # Close marked positions
    for pos_id, reason in positions_to_close:
        close_trade(data, pos_id, price, timestamp, reason)
    
    # Check for new entry - CROSS signal has priority
    if cross_signal['direction']:
        open_trade(data, cross_signal, price, timestamp, 'CROSS')
    # Then check indicator signal
    elif indicator_signal['direction'] and ('STRONG' in indicator_signal['strength'] or indicator_signal['score'] >= 65 or indicator_signal['score'] <= 35):
        open_trade(data, indicator_signal, price, timestamp, 'INDICATOR')
    
    # Save updates
    save_data(symbol, data)

def run_auto_trader():
    """Called by scheduler - processes all symbols"""
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
    """Get current status of all positions"""
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
