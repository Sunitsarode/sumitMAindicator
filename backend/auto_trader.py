"""
AUTO TRADER - Fixed with Proper Error Handling & Logging
"""
import json
import os
import logging
import pandas as pd
from datetime import datetime
from utils.cache import get_cache

# ============== LOGGING SETUP ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== TRADING CONFIG (% BASED) ==============
TRADING_CONFIG = {
    'MAX_OPEN_POSITIONS': 3,
    'INITIAL_SL_PERCENT': 1,
    'TRAILING_SL_PERCENT': 0.5,
    'PROFIT_TARGET_PERCENT': 2,
    'MIN_SIGNAL_GAP_SECONDS': 60,
    'CROSS_NEARBY_THRESHOLD': 2.0,
    # NEW: Risk Management
    'ACCOUNT_SIZE': 10000,  # Default account size
    'RISK_PER_TRADE_PERCENT': 1,  # Risk 1% per trade
    'MAX_DAILY_LOSS_PERCENT': 3,  # Max 3% daily loss
    'MAX_DAILY_TRADES': 20,  # Max trades per day
}

TRADES_DIR = 'trade_data'

# ============== CUSTOM ENTRY CONDITIONS ==============

LONG_CONDITIONS = {
    '1m': {
        'rsi': ('>', 30),
        'supertrend': ('>', 50),
        'supertrend_flip': 'bullish',
        'buy_signal_count': ('>', 12),
    },
    '5m': {
        'rsi': ('>', 35),
        'sumit_ma': ('>', 40),
        'buy_signal_count': ('>', 10),
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
        'supertrend_flip': 'bearish',
        'sell_signal_count': ('>', 12),
    },
    '5m': {
        'rsi': ('<', 65),
        'sumit_ma': ('<', 60),
        'sell_signal_count': ('>', 10),
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
    """Ensure trade data directory exists"""
    try:
        if not os.path.exists(TRADES_DIR):
            os.makedirs(TRADES_DIR)
            logger.info(f"Created directory: {TRADES_DIR}")
    except Exception as e:
        logger.error(f"Failed to create directory {TRADES_DIR}: {e}")
        raise

def get_filepath(symbol):
    """Get filepath for symbol's trade data"""
    safe_symbol = symbol.replace('^', '_').replace('-', '_')
    return os.path.join(TRADES_DIR, f'{safe_symbol}_trades.json')

def load_data(symbol):
    """Load trade data for symbol with validation"""
    ensure_dir()
    filepath = get_filepath(symbol)
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Migrate old format
                if 'currentPosition' in data and data['currentPosition']:
                    if 'openPositions' not in data:
                        data['openPositions'] = [data['currentPosition']]
                    del data['currentPosition']
                
                # Ensure required fields
                if 'openPositions' not in data:
                    data['openPositions'] = []
                if 'trades' not in data:
                    data['trades'] = []
                if 'totalPL' not in data:
                    data['totalPL'] = 0
                if 'totalPLPercent' not in data:
                    data['totalPLPercent'] = 0
                if 'dailyStats' not in data:
                    data['dailyStats'] = {}
                
                return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for {symbol}: {e}")
        # Backup corrupted file
        backup_path = f"{filepath}.backup_{int(datetime.now().timestamp())}"
        os.rename(filepath, backup_path)
        logger.info(f"Backed up corrupted file to {backup_path}")
    except Exception as e:
        logger.error(f"Error loading data for {symbol}: {e}")
    
    # Return default structure
    return {
        'trades': [], 
        'openPositions': [], 
        'totalPL': 0, 
        'totalPLPercent': 0,
        'dailyStats': {}
    }

def save_data(symbol, data):
    """Save trade data with atomic write"""
    ensure_dir()
    filepath = get_filepath(symbol)
    temp_filepath = f"{filepath}.tmp"
    
    try:
        data['lastUpdate'] = datetime.now().isoformat()
        
        # Write to temp file first
        with open(temp_filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename
        os.replace(temp_filepath, filepath)
        logger.debug(f"Saved data for {symbol}")
        
    except Exception as e:
        logger.error(f"Failed to save data for {symbol}: {e}")
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise

def _safe_int(value, default=0):
    """Safely convert to int, handling None and NaN."""
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert value to int: {value}, using default: {default}")
        return default

def _safe_float(value, default=0.0):
    """Safely convert to float, handling None and NaN."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert value to float: {value}, using default: {default}")
        return default

def get_indicator_values(candle):
    """Extract all indicator values from candle with validation"""
    try:
        return {
            'rsi': _safe_float(candle.get('rsi_score', 50), 50),
            'macd': _safe_float(candle.get('macd_score', 50), 50),
            'adx': _safe_float(candle.get('adx_score', 50), 50),
            'supertrend': _safe_float(candle.get('supertrend_score', 50), 50),
            'supertrend_points': _safe_int(candle.get('supertrend_points'), 3),
            'supertrend_bullish_flip': bool(candle.get('supertrend_bullish_flip', False)),
            'supertrend_bearish_flip': bool(candle.get('supertrend_bearish_flip', False)),
            'sumit_ma': _safe_float(candle.get('sumit_ma_score', 50), 50),
            'buy_signal_count': _safe_int(candle.get('buy_signal_count'), 0),
            'sell_signal_count': _safe_int(candle.get('sell_signal_count'), 0),
            'cross_avg': _safe_float(candle.get('cross_avg_score', 0), 0),
            'cross_sma9': _safe_float(candle.get('cross_sma9', 0), 0),
            'cross_sma21': _safe_float(candle.get('cross_sma21', 0), 0),
            'price': _safe_float(candle.get('Close', 0), 0),
        }
    except Exception as e:
        logger.error(f"Error extracting indicator values: {e}")
        # Return safe defaults
        return {
            'rsi': 50, 'macd': 50, 'adx': 50, 'supertrend': 50,
            'supertrend_points': 3, 'supertrend_bullish_flip': False,
            'supertrend_bearish_flip': False, 'sumit_ma': 50,
            'buy_signal_count': 0, 'sell_signal_count': 0,
            'cross_avg': 0, 'cross_sma9': 0, 'cross_sma21': 0, 'price': 0
        }

# ============== CROSS DETECTION ==============

def detect_cross(curr, prev):
    """Detect SMA crossovers"""
    try:
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
    except Exception as e:
        logger.error(f"Error detecting cross: {e}")
        return None

def get_cross_info(curr, prev):
    """Get cross information"""
    try:
        exact_cross = detect_cross(curr, prev)
        return {
            'exact': exact_cross,
            'sma9': curr.get('cross_sma9', 0),
            'sma21': curr.get('cross_sma21', 0),
            'cross_avg': curr.get('cross_avg', 0),
        }
    except Exception as e:
        logger.error(f"Error getting cross info: {e}")
        return {'exact': None, 'sma9': 0, 'sma21': 0, 'cross_avg': 0}

# ============== CONDITION EVALUATION ==============

def evaluate_indicator_conditions(rules, data):
    """Evaluate indicator conditions for a timeframe"""
    try:
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
    except Exception as e:
        logger.error(f"Error evaluating conditions: {e}")
        return False

def check_long_conditions(curr_1m, prev_1m, data_5m, data_1h):
    """Check all LONG entry conditions"""
    try:
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
    except Exception as e:
        logger.error(f"Error checking long conditions: {e}")
        return False, f"Error: {str(e)}"

def check_short_conditions(curr_1m, prev_1m, data_5m, data_1h):
    """Check all SHORT entry conditions"""
    try:
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
    except Exception as e:
        logger.error(f"Error checking short conditions: {e}")
        return False, f"Error: {str(e)}"

# ============== POSITION MANAGEMENT ==============

def calculate_sl_price(entry_price, direction):
    """Calculate stop loss price"""
    try:
        sl_percent = TRADING_CONFIG['INITIAL_SL_PERCENT']
        if direction == 'LONG':
            return entry_price * (1 - sl_percent / 100)
        else:
            return entry_price * (1 + sl_percent / 100)
    except Exception as e:
        logger.error(f"Error calculating SL: {e}")
        return entry_price * 0.99  # Default 1% SL

def calculate_trailing_sl(current_price, direction, current_sl):
    """Calculate trailing stop loss"""
    try:
        trail_percent = TRADING_CONFIG['TRAILING_SL_PERCENT']
        
        if direction == 'LONG':
            new_sl = current_price * (1 - trail_percent / 100)
            return max(new_sl, current_sl)
        else:
            new_sl = current_price * (1 + trail_percent / 100)
            return min(new_sl, current_sl)
    except Exception as e:
        logger.error(f"Error calculating trailing SL: {e}")
        return current_sl

def calculate_profit_target(entry_price, direction):
    """Calculate profit target price"""
    try:
        target_percent = TRADING_CONFIG['PROFIT_TARGET_PERCENT']
        if direction == 'LONG':
            return entry_price * (1 + target_percent / 100)
        else:
            return entry_price * (1 - target_percent / 100)
    except Exception as e:
        logger.error(f"Error calculating profit target: {e}")
        return entry_price * 1.02  # Default 2% target

def can_open_new_position(data, direction, timestamp):
    """Check if new position can be opened"""
    try:
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
    except Exception as e:
        logger.error(f"Error checking if can open position: {e}")
        return False, f"Error: {str(e)}"

def open_trade(data, direction, strength, price, timestamp, signal_type, candle_dict, cross_info=None):
    """Open a new trade"""
    try:
        can_open, reason = can_open_new_position(data, direction, timestamp)
        if not can_open:
            logger.debug(f"Cannot open trade: {reason}")
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
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 OPENED {direction} [{signal_type}] #{open_count}/{TRADING_CONFIG['MAX_OPEN_POSITIONS']}")
        logger.info(f"   Entry: {price:.2f} | SL: {sl:.2f} ({TRADING_CONFIG['INITIAL_SL_PERCENT']}%) | Target: {target:.2f} ({TRADING_CONFIG['PROFIT_TARGET_PERCENT']}%)")
        logger.info(f"   ST Score: {entry_criteria['supertrend']:.0f} ({entry_criteria['supertrend_points']}/6) | BUY: {entry_criteria['buy_signal_count']}/18 | SELL: {entry_criteria['sell_signal_count']}/18")
        logger.info(f"   RSI={entry_criteria['rsi']:.0f} MACD={entry_criteria['macd']:.0f} SMA={entry_criteria['sumit_ma']:.0f}")
        if entry_criteria['supertrend_bullish_flip']:
            logger.info(f"   🔥 SUPERTREND BULLISH FLIP!")
        logger.info(f"{'='*60}\n")
        
        return True
    except Exception as e:
        logger.error(f"Error opening trade: {e}", exc_info=True)
        return False

def close_trade(data, position_id, exit_price, timestamp, reason, candle_dict):
    """Close an existing trade"""
    try:
        open_positions = data.get('openPositions', [])
        pos = None
        pos_idx = None
        
        for i, p in enumerate(open_positions):
            if p['id'] == position_id:
                pos = p
                pos_idx = i
                break
        
        if pos is None:
            logger.warning(f"Position {position_id} not found")
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
        
        logger.info(f"\n{'='*60}")
        logger.info(f"{emoji} CLOSED {pos['direction']} | Reason: {reason}")
        logger.info(f"   Entry: {pos['entryPrice']:.2f} → Exit: {exit_price:.2f}")
        logger.info(f"   P/L: {pl_points:+.2f} pts ({pl_percent:+.2f}%)")
        logger.info(f"   Exit ST: {exit_criteria['supertrend']:.0f} ({exit_criteria['supertrend_points']}/6) | BUY: {exit_criteria['buy_signal_count']}/18 | SELL: {exit_criteria['sell_signal_count']}/18")
        if exit_criteria['supertrend_bearish_flip'] and pos['direction'] == 'LONG':
            logger.info(f"   🔻 SUPERTREND BEARISH FLIP!")
        logger.info(f"   Remaining: {remaining} | Total P/L: {data['totalPL']:.2f} ({data['totalPLPercent']:.2f}%)")
        logger.info(f"{'='*60}\n")
        
        return True
    except Exception as e:
        logger.error(f"Error closing trade: {e}", exc_info=True)
        return False

# ============== MAIN PROCESSING ==============

def process_symbol(symbol):
    """Process trading logic for a symbol"""
    try:
        cache_1m = get_cache(symbol, '1m')
        cache_5m = get_cache(symbol, '5m')
        cache_1h = get_cache(symbol, '1h')
        
        if cache_1m is None or len(cache_1m) < 2:
            logger.warning(f"Insufficient 1m data for {symbol}")
            return
        
        curr_1m = get_indicator_values(cache_1m.iloc[-1].to_dict())
        prev_1m = get_indicator_values(cache_1m.iloc[-2].to_dict())
        
        data_5m = get_indicator_values(cache_5m.iloc[-1].to_dict()) if cache_5m is not None and len(cache_5m) > 0 else {}
        data_1h = get_indicator_values(cache_1h.iloc[-1].to_dict()) if cache_1h is not None and len(cache_1h) > 0 else {}
        
        price = curr_1m['price']
        if price <= 0:
            logger.warning(f"Invalid price for {symbol}: {price}")
            return
        
        timestamp = datetime.now().isoformat()
        candle_dict = cache_1m.iloc[-1].to_dict()
        
        cross_info = get_cross_info(curr_1m, prev_1m)
        
        data = load_data(symbol)
        open_positions = data.get('openPositions', [])
        
        positions_to_close = []
        
        # Check exit conditions for open positions
        for pos in open_positions:
            try:
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
                
                # Check exit conditions
                if hit_sl:
                    positions_to_close.append((pos['id'], 'SL'))
                    continue
                
                if hit_target:
                    positions_to_close.append((pos['id'], 'PROFIT'))
                    continue
                
                # Check for cross reversal
                if cross_info['exact']:
                    if pos['direction'] == 'LONG' and cross_info['exact'] == 'DEATH':
                        positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
                    elif pos['direction'] == 'SHORT' and cross_info['exact'] == 'GOLDEN':
                        positions_to_close.append((pos['id'], 'CROSS_REVERSAL'))
            except Exception as e:
                logger.error(f"Error checking exit for position {pos.get('id')}: {e}")
        
        # Close positions
        for pos_id, reason in positions_to_close:
            close_trade(data, pos_id, price, timestamp, reason, candle_dict)
        
        # Check entry conditions
        long_ok, long_reason = check_long_conditions(curr_1m, prev_1m, data_5m, data_1h)
        short_ok, short_reason = check_short_conditions(curr_1m, prev_1m, data_5m, data_1h)
        
        if long_ok:
            strength = f"LONG (ST:{curr_1m['supertrend_points']}/6, BUY:{curr_1m['buy_signal_count']}/18)"
            open_trade(data, 'LONG', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
        elif short_ok:
            strength = f"SHORT (ST:{curr_1m['supertrend_points']}/6, SELL:{curr_1m['sell_signal_count']}/18)"
            open_trade(data, 'SHORT', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
        
        # Save data
        save_data(symbol, data)
        
    except Exception as e:
        logger.error(f"Critical error processing {symbol}: {e}", exc_info=True)

def run_auto_trader():
    """Main auto trader loop"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        logger.info(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto Trader Running")
        
        for symbol in config['symbols']:
            try:
                process_symbol(symbol)
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {e}", exc_info=True)
                # Continue with next symbol
                continue
    except Exception as e:
        logger.critical(f"❌ Critical error in auto trader: {e}", exc_info=True)

if __name__ == '__main__':
    run_auto_trader()
