"""
AUTO TRADER - Complete with Custom Conditions, Cross Detection, % based SL/Profit
"""
import json
import os
from datetime import datetime
from utils.cache import get_cache

# ============== TRADING CONFIG (% BASED) ==============
TRADING_CONFIG = {
    'MAX_OPEN_POSITIONS': 3,
    'INITIAL_SL_PERCENT': 1,        # 1% stop loss
    'TRAILING_SL_PERCENT': 0.5,     # 0.5% trailing
    'PROFIT_TARGET_PERCENT': 2,     # 2% profit target
    'MIN_SIGNAL_GAP_SECONDS': 60,
    'CROSS_NEARBY_THRESHOLD': 2.0,  # Points for nearby cross detection
}

TRADES_DIR = 'trade_data'

# ============== INDICATOR RANGES (for reference) ==============
# All scores are normalized to 0-100 scale
#
# rsi:          0-100  (< 30 oversold, > 70 overbought)
# macd:         0-100  (< 50 bearish, > 50 bullish)
# adx:          0-100  (< 25 weak trend, > 50 strong trend)
# supertrend:   0-100  (< 50 bearish, > 50 bullish, 0 or 100 at extremes)
# sumit_ma:     0-100  (% of MAs below price, 0=all above, 100=all below)
# sumit_short:  0-100  (short-term MAs position)
# sumit_mid:    0-100  (mid-term MAs position)
# sumit_long:   0-100  (long-term MAs position)
# cross_avg:    0-100  (average of 1m+5m+1h sumit_ma scores)
# cross_sma9:   0-100  (SMA9 of cross_avg)
# cross_sma21:  0-100  (SMA21 of cross_avg)
# price:        actual price (varies by symbol)

# ============== CUSTOM ENTRY CONDITIONS ==============

LONG_CONDITIONS = {
    '1m': {
        'rsi': ('>', 30),           # Min:0 Max:100 | >30 = not oversold
        'supertrend': ('>', 25),    # Min:0 Max:100 | >25 = slightly bullish
    },
    '5m': {
        'rsi': ('>', 35),           # Min:0 Max:100
        'sumit_ma': ('>', 40),      # Min:0 Max:100 | >40 = price above 40% of MAs
    },
    '1h': {
        'sumit_ma': ('>', 30),      # Min:0 Max:100
    },
    'cross': {
        'type': 'GOLDEN',           # 'GOLDEN', 'DEATH', 'NEARBY_BULL', 'NEARBY_BEAR', None
        'cross_avg_max': 40,        # Min:0 Max:100 | Cross at low levels = better long
    }
}

SHORT_CONDITIONS = {
    '1m': {
        'rsi': ('<', 70),           # Min:0 Max:100 | <70 = not overbought
        'supertrend': ('<', 75),    # Min:0 Max:100 | <75 = slightly bearish
    },
    '5m': {
        'rsi': ('<', 65),           # Min:0 Max:100
        'sumit_ma': ('<', 60),      # Min:0 Max:100 | <60 = price below 40% of MAs
    },
    '1h': {
        'sumit_ma': ('<', 70),      # Min:0 Max:100
    },
    'cross': {
        'type': 'DEATH',            # 'GOLDEN', 'DEATH', 'NEARBY_BULL', 'NEARBY_BEAR', None
        'cross_avg_min': 60,        # Min:0 Max:100 | Cross at high levels = better short
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
        'sumit_ma': float(candle.get('sumit_ma_score', 50) or 50),
        'sumit_short': float(candle.get('sumit_ratio1_score', 50) or 50),
        'sumit_mid': float(candle.get('sumit_ratio2_score', 50) or 50),
        'sumit_long': float(candle.get('sumit_ratio3_score', 50) or 50),
        'cross_avg': float(candle.get('cross_avg_score', 0) or 0),
        'cross_sma9': float(candle.get('cross_sma9', 0) or 0),
        'cross_sma21': float(candle.get('cross_sma21', 0) or 0),
        'price': float(candle.get('Close', 0) or 0),
    }

# ============== CROSS DETECTION ==============

def detect_cross(curr, prev):
    """
    Detect exact crossover points
    Returns: 'GOLDEN' (bullish), 'DEATH' (bearish), or None
    """
    curr_sma9 = curr.get('cross_sma9', 0)
    curr_sma21 = curr.get('cross_sma21', 0)
    prev_sma9 = prev.get('cross_sma9', 0)
    prev_sma21 = prev.get('cross_sma21', 0)
    
    if not all([curr_sma9, curr_sma21, prev_sma9, prev_sma21]):
        return None
    
    # GOLDEN CROSS: SMA9 crosses ABOVE SMA21
    golden_cross = (prev_sma9 <= prev_sma21) and (curr_sma9 > curr_sma21)
    
    # DEATH CROSS: SMA9 crosses BELOW SMA21
    death_cross = (prev_sma9 >= prev_sma21) and (curr_sma9 < curr_sma21)
    
    if golden_cross:
        return 'GOLDEN'
    if death_cross:
        return 'DEATH'
    return None

def detect_nearby_cross(curr, threshold=None):
    """
    Detect if SMA9 and SMA21 are very close (about to cross)
    Returns: ('NEARBY_BULL'/'NEARBY_BEAR'/None, diff)
    """
    if threshold is None:
        threshold = TRADING_CONFIG['CROSS_NEARBY_THRESHOLD']
    
    sma9 = curr.get('cross_sma9', 0)
    sma21 = curr.get('cross_sma21', 0)
    
    if not sma9 or not sma21:
        return None, 0
    
    diff = sma9 - sma21
    
    if abs(diff) <= threshold:
        if diff > 0:
            return 'NEARBY_BULL', diff
        else:
            return 'NEARBY_BEAR', diff
    
    return None, diff

def get_cross_info(curr, prev):
    """Get comprehensive cross information"""
    exact_cross = detect_cross(curr, prev)
    nearby_cross, diff = detect_nearby_cross(curr)
    
    return {
        'exact': exact_cross,
        'nearby': nearby_cross,
        'diff': diff,
        'sma9': curr.get('cross_sma9', 0),
        'sma21': curr.get('cross_sma21', 0),
        'cross_avg': curr.get('cross_avg', 0),
    }

# ============== CONDITION EVALUATION ==============

def evaluate_indicator_conditions(rules, data):
    """Evaluate indicator conditions for a timeframe"""
    for indicator, (op, value) in rules.items():
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
    
    # Check 1m conditions
    if '1m' in LONG_CONDITIONS and LONG_CONDITIONS['1m']:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['1m'], curr_1m):
            return False, "1m conditions not met"
    
    # Check 5m conditions
    if '5m' in LONG_CONDITIONS and LONG_CONDITIONS['5m'] and data_5m:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['5m'], data_5m):
            return False, "5m conditions not met"
    
    # Check 1h conditions
    if '1h' in LONG_CONDITIONS and LONG_CONDITIONS['1h'] and data_1h:
        if not evaluate_indicator_conditions(LONG_CONDITIONS['1h'], data_1h):
            return False, "1h conditions not met"
    
    # Check cross conditions
    if 'cross' in LONG_CONDITIONS and LONG_CONDITIONS['cross'].get('type'):
        cross_config = LONG_CONDITIONS['cross']
        cross_type = cross_config['type']
        
        exact_cross = detect_cross(curr_1m, prev_1m)
        nearby_cross, _ = detect_nearby_cross(curr_1m)
        
        cross_matched = False
        if cross_type == 'GOLDEN' and exact_cross == 'GOLDEN':
            cross_matched = True
        elif cross_type == 'NEARBY_BULL' and nearby_cross == 'NEARBY_BULL':
            cross_matched = True
        elif cross_type in ['GOLDEN', 'NEARBY_BULL'] and (exact_cross == 'GOLDEN' or nearby_cross == 'NEARBY_BULL'):
            cross_matched = True
        
        if not cross_matched:
            return False, "Cross condition not met"
        
        # Check cross_avg level
        if 'cross_avg_max' in cross_config:
            if curr_1m.get('cross_avg', 100) > cross_config['cross_avg_max']:
                return False, f"Cross avg too high (>{cross_config['cross_avg_max']})"
    
    return True, "All conditions met"

def check_short_conditions(curr_1m, prev_1m, data_5m, data_1h):
    """Check all SHORT entry conditions"""
    
    # Check 1m conditions
    if '1m' in SHORT_CONDITIONS and SHORT_CONDITIONS['1m']:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['1m'], curr_1m):
            return False, "1m conditions not met"
    
    # Check 5m conditions
    if '5m' in SHORT_CONDITIONS and SHORT_CONDITIONS['5m'] and data_5m:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['5m'], data_5m):
            return False, "5m conditions not met"
    
    # Check 1h conditions
    if '1h' in SHORT_CONDITIONS and SHORT_CONDITIONS['1h'] and data_1h:
        if not evaluate_indicator_conditions(SHORT_CONDITIONS['1h'], data_1h):
            return False, "1h conditions not met"
    
    # Check cross conditions
    if 'cross' in SHORT_CONDITIONS and SHORT_CONDITIONS['cross'].get('type'):
        cross_config = SHORT_CONDITIONS['cross']
        cross_type = cross_config['type']
        
        exact_cross = detect_cross(curr_1m, prev_1m)
        nearby_cross, _ = detect_nearby_cross(curr_1m)
        
        cross_matched = False
        if cross_type == 'DEATH' and exact_cross == 'DEATH':
            cross_matched = True
        elif cross_type == 'NEARBY_BEAR' and nearby_cross == 'NEARBY_BEAR':
            cross_matched = True
        elif cross_type in ['DEATH', 'NEARBY_BEAR'] and (exact_cross == 'DEATH' or nearby_cross == 'NEARBY_BEAR'):
            cross_matched = True
        
        if not cross_matched:
            return False, "Cross condition not met"
        
        # Check cross_avg level
        if 'cross_avg_min' in cross_config:
            if curr_1m.get('cross_avg', 0) < cross_config['cross_avg_min']:
                return False, f"Cross avg too low (<{cross_config['cross_avg_min']})"
    
    return True, "All conditions met"

# ============== POSITION MANAGEMENT ==============

def calculate_sl_price(entry_price, direction):
    """Calculate SL price based on %"""
    sl_percent = TRADING_CONFIG['INITIAL_SL_PERCENT']
    if direction == 'LONG':
        return entry_price * (1 - sl_percent / 100)
    else:
        return entry_price * (1 + sl_percent / 100)

def calculate_trailing_sl(current_price, direction, current_sl):
    """Calculate new trailing SL based on %"""
    trail_percent = TRADING_CONFIG['TRAILING_SL_PERCENT']
    
    if direction == 'LONG':
        new_sl = current_price * (1 - trail_percent / 100)
        return max(new_sl, current_sl)  # Only move SL up
    else:
        new_sl = current_price * (1 + trail_percent / 100)
        return min(new_sl, current_sl)  # Only move SL down

def calculate_profit_target(entry_price, direction):
    """Calculate profit target price based on %"""
    target_percent = TRADING_CONFIG['PROFIT_TARGET_PERCENT']
    if direction == 'LONG':
        return entry_price * (1 + target_percent / 100)
    else:
        return entry_price * (1 - target_percent / 100)
    
def print_live_values(symbol):
    """Print current indicator values for debugging"""
    cache_1m = get_cache(symbol, '1m')
    cache_5m = get_cache(symbol, '5m')
    cache_1h = get_cache(symbol, '1h')
    
    if cache_1m is None or len(cache_1m) < 2:
        print(f"No data for {symbol}")
        return
    
    curr_1m = get_indicator_values(cache_1m.iloc[-1].to_dict())
    prev_1m = get_indicator_values(cache_1m.iloc[-2].to_dict())
    data_5m = get_indicator_values(cache_5m.iloc[-1].to_dict()) if cache_5m is not None and len(cache_5m) > 0 else {}
    data_1h = get_indicator_values(cache_1h.iloc[-1].to_dict()) if cache_1h is not None and len(cache_1h) > 0 else {}
    
    cross_info = get_cross_info(curr_1m, prev_1m)
    
    print(f"\n{'='*70}")
    print(f"📊 LIVE VALUES - {symbol} @ {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}")
    print(f"Price: {curr_1m['price']:.2f}")
    print(f"\n{'─'*70}")
    print(f"{'Indicator':<15} {'1m':<12} {'5m':<12} {'1h':<12} {'Range'}")
    print(f"{'─'*70}")
    print(f"{'RSI':<15} {curr_1m['rsi']:<12.1f} {data_5m.get('rsi', 'N/A'):<12} {data_1h.get('rsi', 'N/A'):<12} 0-100")
    print(f"{'MACD':<15} {curr_1m['macd']:<12.1f} {data_5m.get('macd', 'N/A'):<12} {data_1h.get('macd', 'N/A'):<12} 0-100")
    print(f"{'ADX':<15} {curr_1m['adx']:<12.1f} {data_5m.get('adx', 'N/A'):<12} {data_1h.get('adx', 'N/A'):<12} 0-100")
    print(f"{'Supertrend':<15} {curr_1m['supertrend']:<12.1f} {data_5m.get('supertrend', 'N/A'):<12} {data_1h.get('supertrend', 'N/A'):<12} 0-100")
    print(f"{'Sumit MA':<15} {curr_1m['sumit_ma']:<12.1f} {data_5m.get('sumit_ma', 'N/A'):<12} {data_1h.get('sumit_ma', 'N/A'):<12} 0-100")
    print(f"{'Sumit Short':<15} {curr_1m['sumit_short']:<12.1f} {data_5m.get('sumit_short', 'N/A'):<12} {data_1h.get('sumit_short', 'N/A'):<12} 0-100")
    print(f"{'Sumit Mid':<15} {curr_1m['sumit_mid']:<12.1f} {data_5m.get('sumit_mid', 'N/A'):<12} {data_1h.get('sumit_mid', 'N/A'):<12} 0-100")
    print(f"{'Sumit Long':<15} {curr_1m['sumit_long']:<12.1f} {data_5m.get('sumit_long', 'N/A'):<12} {data_1h.get('sumit_long', 'N/A'):<12} 0-100")
    print(f"{'─'*70}")
    print(f"\n📈 CROSS DATA (1m):")
    print(f"   Cross Avg:  {curr_1m['cross_avg']:.1f}  (0-100)")
    print(f"   Cross SMA9: {curr_1m['cross_sma9']:.1f}  (0-100)")
    print(f"   Cross SMA21:{curr_1m['cross_sma21']:.1f}  (0-100)")
    print(f"   Exact Cross: {cross_info['exact'] or 'None'}")
    print(f"   Nearby Cross: {cross_info['nearby'] or 'None'} (diff: {cross_info['diff']:.2f})")
    print(f"{'='*70}\n")
    
    return curr_1m, data_5m, data_1h, cross_info

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
    """Open new trade with % based SL"""
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
    print(f"   Indicators: RSI={entry_criteria['rsi']:.0f} MACD={entry_criteria['macd']:.0f} ADX={entry_criteria['adx']:.0f} ST={entry_criteria['supertrend']:.0f} SMA={entry_criteria['sumit_ma']:.0f}")
    if cross_info and cross_info.get('exact'):
        print(f"   Cross: {cross_info['exact']} | SMA9={cross_info['sma9']:.1f} SMA21={cross_info['sma21']:.1f} | Avg={cross_info['cross_avg']:.1f}")
    print(f"{'='*60}\n")
    
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
    
    # Calculate P/L in points and %
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
    print(f"   Exit Indicators: RSI={exit_criteria['rsi']:.0f} MACD={exit_criteria['macd']:.0f} ST={exit_criteria['supertrend']:.0f} SMA={exit_criteria['sumit_ma']:.0f}")
    print(f"   Remaining: {remaining} | Total P/L: {data['totalPL']:.2f} ({data['totalPLPercent']:.2f}%)")
    print(f"{'='*60}\n")
    
    return True

# ============== MAIN PROCESSING ==============

def process_symbol(symbol):
    """Process trading signals for a symbol"""
    # Get all timeframe data
    cache_1m = get_cache(symbol, '1m')
    cache_5m = get_cache(symbol, '5m')
    cache_1h = get_cache(symbol, '1h')
    
    if cache_1m is None or len(cache_1m) < 2:
        return
    
    # Get current and previous candle data
    curr_1m = get_indicator_values(cache_1m.iloc[-1].to_dict())
    prev_1m = get_indicator_values(cache_1m.iloc[-2].to_dict())
    
    data_5m = get_indicator_values(cache_5m.iloc[-1].to_dict()) if cache_5m is not None and len(cache_5m) > 0 else {}
    data_1h = get_indicator_values(cache_1h.iloc[-1].to_dict()) if cache_1h is not None and len(cache_1h) > 0 else {}
    
    price = curr_1m['price']
    timestamp = datetime.now().isoformat()
    candle_dict = cache_1m.iloc[-1].to_dict()
    
    # Get cross info
    cross_info = get_cross_info(curr_1m, prev_1m)
    
    # Load saved data
    data = load_data(symbol)
    open_positions = data.get('openPositions', [])
    
    # Process existing positions
    positions_to_close = []
    
    for pos in open_positions:
        # Calculate current P/L
        if pos['direction'] == 'LONG':
            pl_points = price - pos['entryPrice']
            hit_sl = price <= pos['stopLoss']
            hit_target = price >= pos.get('profitTarget', pos['entryPrice'] * 1.02)
        else:
            pl_points = pos['entryPrice'] - price
            hit_sl = price >= pos['stopLoss']
            hit_target = price <= pos.get('profitTarget', pos['entryPrice'] * 0.98)
        
        pl_percent = (pl_points / pos['entryPrice']) * 100
        
        # Update trailing SL if in profit
        if pl_percent > 0:
            new_sl = calculate_trailing_sl(price, pos['direction'], pos['stopLoss'])
            if new_sl != pos['stopLoss']:
                pos['stopLoss'] = new_sl
                pos['highestPL'] = max(pl_percent, pos.get('highestPL', 0))
        
        # Check SL hit
        if hit_sl:
            positions_to_close.append((pos['id'], 'SL'))
            continue
        
        # Check profit target hit
        if hit_target:
            positions_to_close.append((pos['id'], 'PROFIT'))
            continue
        
        # Check cross reversal
        if cross_info['exact']:
            if pos['direction'] == 'LONG' and cross_info['exact'] == 'DEATH':
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
            elif pos['direction'] == 'SHORT' and cross_info['exact'] == 'GOLDEN':
                positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
    
    # Close marked positions
    for pos_id, reason in positions_to_close:
        close_trade(data, pos_id, price, timestamp, reason, candle_dict)
    
    # Check for new entries
    long_ok, long_reason = check_long_conditions(curr_1m, prev_1m, data_5m, data_1h)
    short_ok, short_reason = check_short_conditions(curr_1m, prev_1m, data_5m, data_1h)
    
    if long_ok:
        strength = f"CUSTOM LONG ({cross_info['exact'] or 'IND'})"
        open_trade(data, 'LONG', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
    elif short_ok:
        strength = f"CUSTOM SHORT ({cross_info['exact'] or 'IND'})"
        open_trade(data, 'SHORT', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
    
    # Save data
    save_data(symbol, data)

def run_auto_trader():
    """Called by scheduler"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto Trader")
    
    for symbol in config['symbols']:
        try:
            # Uncomment below line to see live values every run
            # print_live_values(symbol)
            
            process_symbol(symbol)
        except Exception as e:
            print(f"❌ Error {symbol}: {e}")
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
            'totalPLPercent': data.get('totalPLPercent', 0),
            'positions': data.get('openPositions', [])
        }
    return status

if __name__ == '__main__':
    run_auto_trader()
