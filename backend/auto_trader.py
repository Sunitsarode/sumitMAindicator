"""
AUTO TRADER - Updated with Sumit MA Signals and New Supertrend Logic
"""
import json
import os
from datetime import datetime
from utils.cache import get_cache

# ============== TRADING CONFIG (% BASED) ==============
TRADING_CONFIG = {
    'MAX_OPEN_POSITIONS': 3,
    'INITIAL_SL_PERCENT': 1,
    'TRAILING_SL_PERCENT': 0.5,
    'PROFIT_TARGET_PERCENT': 2,
    'MIN_SIGNAL_GAP_SECONDS': 60,
    'CROSS_NEARBY_THRESHOLD': 2.0,
}

TRADES_DIR = 'trade_data'

# ============== CUSTOM ENTRY CONDITIONS ==============

LONG_CONDITIONS = {
    '1m': {
        'rsi': ('>', 30),
        'supertrend': ('>', 50),
        'supertrend_flip': 'bullish',  # NEW: Check for bullish flip
        'buy_signal_count': ('>', 12),  # NEW: Price above >12 MAs
    },
    '5m': {
        'rsi': ('>', 35),
        'sumit_ma': ('>', 40),
        'buy_signal_count': ('>', 10),  # NEW
    },
    '1h': {
        'sumit_ma': ('>', 30),
    },
    'cross': {
        'type': 'GOLDEN',
        'cross_avg_max': 40,
    }
}

SHORT_CONDITIONS = {
    '1m': {
        'rsi': ('<', 70),
        'supertrend': ('<', 50),
        'supertrend_flip': 'bearish',  # NEW: Check for bearish flip
        'sell_signal_count': ('>', 12),  # NEW: Price below >12 MAs
    },
    '5m': {
        'rsi': ('<', 65),
        'sumit_ma': ('<', 60),
        'sell_signal_count': ('>', 10),  # NEW
    },
    '1h': {
        'sumit_ma': ('<', 70),
    },
    'cross': {
        'type': 'DEATH',
        'cross_avg_min': 60,
    }
}

# ============== HELPER FUNCTIONS ==============

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
    return {'trades': [], 'openPositions': [], 'totalPL': 0, 'totalPLPercent': 0}

def save_data(symbol, data):
    ensure_dir()
    filepath = get_filepath(symbol)
    data['lastUpdate'] = datetime.now().isoformat()
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_indicator_values(candle):
    """Extract all indicator values from candle"""
    return {
        'rsi': float(candle.get('rsi_score', 50) or 50),
        'macd': float(candle.get('macd_score', 50) or 50),
        'adx': float(candle.get('adx_score', 50) or 50),
        'supertrend': float(candle.get('supertrend_score', 50) or 50),
        'supertrend_points': int(candle.get('supertrend_points', 3) or 3),
        'supertrend_bullish_flip': bool(candle.get('supertrend_bullish_flip', False)),
        'supertrend_bearish_flip': bool(candle.get('supertrend_bearish_flip', False)),
        'sumit_ma': float(candle.get('sumit_ma_score', 50) or 50),
        'buy_signal_count': int(candle.get('buy_signal_count', 0) or 0),
        'sell_signal_count': int(candle.get('sell_signal_count', 0) or 0),
        'cross_avg': float(candle.get('cross_avg_score', 0) or 0),
        'cross_sma9': float(candle.get('cross_sma9', 0) or 0),
        'cross_sma21': float(candle.get('cross_sma21', 0) or 0),
        'price': float(candle.get('Close', 0) or 0),
    }

# ============== CROSS DETECTION ==============

def detect_cross(curr, prev):
    curr_sma9 = curr.get('cross_sma9', 0)
    curr_sma21 = curr.get('cross_sma21', 0)
    prev_sma9 = prev.get('cross_sma9', 0)
    prev_sma21 = prev.get('cross_sma21', 0)
    
    if not all([curr_sma9, curr_sma21, prev_sma9, prev_sma21]):
        return None
    
    golden_cross = (prev_sma9 <= prev_sma21) and (curr_sma9 > curr_sma21)
    death_cross = (prev_sma9 >= prev_sma21) and (curr_sma9 < curr_sma21)
    
    if golden_cross:
        return 'GOLDEN'
    if death_cross:
        return 'DEATH'
    return None

def get_cross_info(curr, prev):
    exact_cross = detect_cross(curr, prev)
    
    return {
        'exact': exact_cross,
        'sma9': curr.get('cross_sma9', 0),
        'sma21': curr.get('cross_sma21', 0),
        'cross_avg': curr.get('cross_avg', 0),
    }

# ============== CONDITION EVALUATION ==============

def evaluate_indicator_conditions(rules, data):
    """Evaluate indicator conditions for a timeframe"""
    for indicator, condition in rules.items():
        # Handle supertrend_flip specially
        if indicator == 'supertrend_flip':
            if condition == 'bullish' and not data.get('supertrend_bullish_flip', False):
                return False
            if condition == 'bearish' and not data.get('supertrend_bearish_flip', False):
                return False
            continue
        
        # Handle standard operators
        if isinstance(condition, tuple):
            op, value = condition
            actual = data.get(indicator, 50)
            
            if op == '>' and not (actual > value):
                return False
            if op == '<' and not (actual < value):
                return False
            if op == '>=' and not (actual >= value):
                return False
            if op == '<=' and not (actual <= value):
                return False
            if op == '==' and not (actual == value):
                return False
    
    return True

def check_long_conditions(curr_1m, prev_1m, data_5m, data_1h):
    """Check all LONG entry conditions"""
    
    if '1m' in LONG_CONDITIONS and LONG_CONDITIONS['1m']:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['1m'], curr_1m):
            return False, "1m conditions not met"
    
    if '5m' in LONG_CONDITIONS and LONG_CONDITIONS['5m'] and data_5m:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['5m'], data_5m):
            return False, "5m conditions not met"
    
    if '1h' in LONG_CONDITIONS and LONG_CONDITIONS['1h'] and data_1h:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['1h'], data_1h):
            return False, "1h conditions not met"
    
    if 'cross' in LONG_CONDITIONS and LONG_CONDITIONS['cross'].get('type'):
        cross_config = LONG_CONDITIONS['cross']
        cross_type = cross_config['type']
        
        exact_cross = detect_cross(curr_1m, prev_1m)
        
        if cross_type == 'GOLDEN' and exact_cross != 'GOLDEN':
            return False, "Cross condition not met"
        
        if 'cross_avg_max' in cross_config:
            if curr_1m.get('cross_avg', 100) > cross_config['cross_avg_max']:
                return False, f"Cross avg too high (>{cross_config['cross_avg_max']})"
    
    return True, "All conditions met"

def check_short_conditions(curr_1m, prev_1m, data_5m, data_1h):
    """Check all SHORT entry conditions"""
    
    if '1m' in SHORT_CONDITIONS and SHORT_CONDITIONS['1m']:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['1m'], curr_1m):
            return False, "1m conditions not met"
    
    if '5m' in SHORT_CONDITIONS and SHORT_CONDITIONS['5m'] and data_5m:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['5m'], data_5m):
            return False, "5m conditions not met"
    
    if '1h' in SHORT_CONDITIONS and SHORT_CONDITIONS['1h'] and data_1h:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['1h'], data_1h):
            return False, "1h conditions not met"
    
    if 'cross' in SHORT_CONDITIONS and SHORT_CONDITIONS['cross'].get('type'):
        cross_config = SHORT_CONDITIONS['cross']
        cross_type = cross_config['type']
        
        exact_cross = detect_cross(curr_1m, prev_1m)
        
        if cross_type == 'DEATH' and exact_cross != 'DEATH':
            return False, "Cross condition not met"
        
        if 'cross_avg_min' in cross_config:
            if curr_1m.get('cross_avg', 0) < cross_config['cross_avg_min']:
                return False, f"Cross avg too low (<{cross_config['cross_avg_min']})"
    
    return True, "All conditions met"

# ============== POSITION MANAGEMENT ==============

def calculate_sl_price(entry_price, direction):
    sl_percent = TRADING_CONFIG['INITIAL_SL_PERCENT']
    if direction == 'LONG':
        return entry_price * (1 - sl_percent / 100)
    else:
        return entry_price * (1 + sl_percent / 100)

def calculate_trailing_sl(current_price, direction, current_sl):
    trail_percent = TRADING_CONFIG['TRAILING_SL_PERCENT']
    
    if direction == 'LONG':
        new_sl = current_price * (1 - trail_percent / 100)
        return max(new_sl, current_sl)
    else:
        new_sl = current_price * (1 + trail_percent / 100)
        return min(new_sl, current_sl)

def calculate_profit_target(entry_price, direction):
    target_percent = TRADING_CONFIG['PROFIT_TARGET_PERCENT']
    if direction == 'LONG':
        return entry_price * (1 + target_percent / 100)
    else:
        return entry_price * (1 - target_percent / 100)

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

def open_trade(data, direction, strength, price, timestamp, signal_type, candle_dict, cross_info=None):
    can_open, reason = can_open_new_position(data, direction, timestamp)
    if not can_open:
        return False
    
    sl = calculate_sl_price(price, direction)
    target = calculate_profit_target(price, direction)
    entry_criteria = get_indicator_values(candle_dict)
    
    new_position = {
        'id': int(datetime.now().timestamp() * 1000),
        'direction': direction,
        'strength': strength,
        'signalType': signal_type,
        'entryPrice': price,
        'entryTime': timestamp,
        'stopLoss': sl,
        'profitTarget': target,
        'slPercent': TRADING_CONFIG['INITIAL_SL_PERCENT'],
        'targetPercent': TRADING_CONFIG['PROFIT_TARGET_PERCENT'],
        'highestPL': 0,
        'entryCriteria': entry_criteria,
    }
    
    if cross_info:
        new_position['crossInfo'] = cross_info
    
    data['openPositions'].append(new_position)
    open_count = len(data['openPositions'])
    
    print(f"\n{'='*60}")
    print(f"📈 OPENED {direction} [{signal_type}] #{open_count}/{TRADING_CONFIG['MAX_OPEN_POSITIONS']}")
    print(f"   Entry: {price:.2f} | SL: {sl:.2f} ({TRADING_CONFIG['INITIAL_SL_PERCENT']}%) | Target: {target:.2f} ({TRADING_CONFIG['PROFIT_TARGET_PERCENT']}%)")
    print(f"   ST Score: {entry_criteria['supertrend']:.0f} ({entry_criteria['supertrend_points']}/6) | BUY: {entry_criteria['buy_signal_count']}/18 | SELL: {entry_criteria['sell_signal_count']}/18")
    print(f"   RSI={entry_criteria['rsi']:.0f} MACD={entry_criteria['macd']:.0f} SMA={entry_criteria['sumit_ma']:.0f}")
    if entry_criteria['supertrend_bullish_flip']:
        print(f"   🔥 SUPERTREND BULLISH FLIP!")
    print(f"{'='*60}\n")
    
    return True

def close_trade(data, position_id, exit_price, timestamp, reason, candle_dict):
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
    
    if pos['direction'] == 'LONG':
        pl_points = exit_price - pos['entryPrice']
    else:
        pl_points = pos['entryPrice'] - exit_price
    
    pl_percent = (pl_points / pos['entryPrice']) * 100
    
    exit_criteria = get_indicator_values(candle_dict)
    
    trade = {
        'id': pos['id'],
        'timestamp': timestamp,
        'entryTime': pos['entryTime'],
        'direction': pos['direction'],
        'strength': pos['strength'],
        'signalType': pos.get('signalType', 'CUSTOM'),
        'entryPrice': pos['entryPrice'],
        'exitPrice': exit_price,
        'pl': pl_points,
        'plPercent': pl_percent,
        'reason': reason,
        'entryCriteria': pos.get('entryCriteria', {}),
        'exitCriteria': exit_criteria,
        'crossInfo': pos.get('crossInfo'),
    }
    
    data['trades'].insert(0, trade)
    data['totalPL'] = data.get('totalPL', 0) + pl_points
    data['totalPLPercent'] = data.get('totalPLPercent', 0) + pl_percent
    data['openPositions'].pop(pos_idx)
    
    emoji = "✅" if pl_points > 0 else "❌"
    remaining = len(data['openPositions'])
    
    print(f"\n{'='*60}")
    print(f"{emoji} CLOSED {pos['direction']} | Reason: {reason}")
    print(f"   Entry: {pos['entryPrice']:.2f} → Exit: {exit_price:.2f}")
    print(f"   P/L: {pl_points:+.2f} pts ({pl_percent:+.2f}%)")
    print(f"   Exit ST: {exit_criteria['supertrend']:.0f} ({exit_criteria['supertrend_points']}/6) | BUY: {exit_criteria['buy_signal_count']}/18 | SELL: {exit_criteria['sell_signal_count']}/18")
    if exit_criteria['supertrend_bearish_flip'] and pos['direction'] == 'LONG':
        print(f"   🔻 SUPERTREND BEARISH FLIP!")
    print(f"   Remaining: {remaining} | Total P/L: {data['totalPL']:.2f} ({data['totalPLPercent']:.2f}%)")
    print(f"{'='*60}\n")
    
    return True

# ============== MAIN PROCESSING ==============

def process_symbol(symbol):
    cache_1m = get_cache(symbol, '1m')
    cache_5m = get_cache(symbol, '5m')
    cache_1h = get_cache(symbol, '1h')
    
    if cache_1m is None or len(cache_1m) < 2:
        return
    
    curr_1m = get_indicator_values(cache_1m.iloc[-1].to_dict())
    prev_1m = get_indicator_values(cache_1m.iloc[-2].to_dict())
    
    data_5m = get_indicator_values(cache_5m.iloc[-1].to_dict()) if cache_5m is not None and len(cache_5m) > 0 else {}
    data_1h = get_indicator_values(cache_1h.iloc[-1].to_dict()) if cache_1h is not None and len(cache_1h) > 0 else {}
    
    price = curr_1m['price']
    timestamp = datetime.now().isoformat()
    candle_dict = cache_1m.iloc[-1].to_dict()
    
    cross_info = get_cross_info(curr_1m, prev_1m)
    
    data = load_data(symbol)
    open_positions = data.get('openPositions', [])
    
    positions_to_close = []
    
    for pos in open_positions:
        if pos['direction'] == 'LONG':
            pl_points = price - pos['entryPrice']
            hit_sl = price <= pos['stopLoss']
            hit_target = price >= pos.get('profitTarget', pos['entryPrice'] * 1.02)
        else:
            pl_points = pos['entryPrice'] - price
            hit_sl = price >= pos['stopLoss']
            hit_target = price <= pos.get('profitTarget', pos['entryPrice'] * 0.98)
        
        pl_percent = (pl_points / pos['entryPrice']) * 100
        
        if pl_percent > 0:
            new_sl = calculate_trailing_sl(price, pos['direction'], pos['stopLoss'])
            if new_sl != pos['stopLoss']:
                pos['stopLoss'] = new_sl
                pos['highestPL'] = max(pl_percent, pos.get('highestPL', 0))
        
        if hit_sl:
            positions_to_close.append((pos['id'], 'SL'))
            continue
        
        if hit_target:
            positions_to_close.append((pos['id'], 'PROFIT'))
            continue
        
        if cross_info['exact']:
            if pos['direction'] == 'LONG' and cross_info['exact'] == 'DEATH':
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
            elif pos['direction'] == 'SHORT' and cross_info['exact'] == 'GOLDEN':
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
    
    for pos_id, reason in positions_to_close:
        close_trade(data, pos_id, price, timestamp, reason, candle_dict)
    
    long_ok, long_reason = check_long_conditions(curr_1m, prev_1m, data_5m, data_1h)
    short_ok, short_reason = check_short_conditions(curr_1m, prev_1m, data_5m, data_1h)
    
    if long_ok:
        strength = f"LONG (ST:{curr_1m['supertrend_points']}/6, BUY:{curr_1m['buy_signal_count']}/18)"
        open_trade(data, 'LONG', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
    elif short_ok:
        strength = f"SHORT (ST:{curr_1m['supertrend_points']}/6, SELL:{curr_1m['sell_signal_count']}/18)"
        open_trade(data, 'SHORT', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
    
    save_data(symbol, data)

def run_auto_trader():
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto Trader")
    
    for symbol in config['symbols']:
        try:
            process_symbol(symbol)
        except Exception as e:
            print(f"❌ Error {symbol}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    run_auto_trader()
