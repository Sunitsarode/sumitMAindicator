"""
Signal Evaluator - Evaluates entry/exit conditions
ENHANCED: Now supports both combined AND individual supertrend checking
"""
from utils.logging_config import logger
from utils.config_manager import config

# ============================================
# ENTRY CONDITIONS WITH FULL OPTIONS
# ============================================
"""
SUPERTREND OPTIONS:

COMBINED (Current - checks all 6 supertrends together):
- 'supertrend': Score 0-100 (all 6 combined)
- 'supertrend_points': Raw count 0-6
- 'supertrend_flip': 'bullish'/'bearish' (ANY of 6 flipped)

INDIVIDUAL (New - check specific supertrends):
For 1m timeframe:
- 'st_7_3_direction': 1 (bullish) or -1 (bearish)
- 'st_7_3_flip': 'bullish' or 'bearish' or None
- 'st_10_2_direction': 1 or -1
- 'st_10_2_flip': 'bullish' or 'bearish' or None

For 5m timeframe: (access via data_5m)
- Same keys: st_7_3_direction, st_7_3_flip, etc.

For 1h timeframe: (access via data_1h)
- Same keys: st_7_3_direction, st_7_3_flip, etc.

EXAMPLES:

# Use combined (original way):
'supertrend': {'operator': '>', 'value': 50}
'supertrend_flip': 'bullish'

# Use individual ST(7,3) only:
'st_7_3_direction': {'operator': '==', 'value': 1}
'st_7_3_flip': 'bullish'

# Use individual ST(10,2) only:
'st_10_2_direction': {'operator': '==', 'value': 1}

# Require BOTH individual STs to be bullish:
'st_7_3_direction': {'operator': '==', 'value': 1},
'st_10_2_direction': {'operator': '==', 'value': 1}

# Mix: Combined score + specific flip:
'supertrend': {'operator': '>', 'value': 50},
'st_7_3_flip': 'bullish'
"""

# ============================================
# LONG ENTRY CONDITIONS
# ============================================
LONG_CONDITIONS = {
    '1m': {
        'rsi': {'operator': '>', 'value': 30},
        'supertrend': {'operator': '>', 'value': 50},
        'supertrend_flip': 'bullish',
        'buy_signal_count': {'operator': '>', 'value': 12},
        
        # NEW: Individual supertrend examples (commented out - uncomment to use)
        # 'st_7_3_direction': {'operator': '==', 'value': 1},  # ST(7,3) must be bullish
        # 'st_7_3_flip': 'bullish',  # ST(7,3) just flipped bullish
        # 'st_10_2_direction': {'operator': '==', 'value': 1},  # ST(10,2) must be bullish
        # 'st_10_2_flip': 'bullish',  # ST(10,2) just flipped bullish
    },
    '5m': {
        'rsi': {'operator': '>', 'value': 35},
        'sumit_ma': {'operator': '>', 'value': 40},
        'buy_signal_count': {'operator': '>', 'value': 10},
        
        # NEW: 5m individual supertrend examples
        # 'st_7_3_direction': {'operator': '==', 'value': 1},
    },
    '1h': {
        'sumit_ma': {'operator': '>', 'value': 30},
        
        # NEW: 1h individual supertrend examples
        # 'st_10_2_direction': {'operator': '==', 'value': 1},
    },
    'cross': {
        'type': 'GOLDEN',
        'cross_avg_max': 40
    }
}

# ============================================
# SHORT ENTRY CONDITIONS
# ============================================
SHORT_CONDITIONS = {
    '1m': {
        'rsi': {'operator': '<', 'value': 70},
        'supertrend': {'operator': '<', 'value': 50},
        'supertrend_flip': 'bearish',
        'sell_signal_count': {'operator': '>', 'value': 12},
        
        # NEW: Individual supertrend examples (commented out)
        # 'st_7_3_direction': {'operator': '==', 'value': -1},  # ST(7,3) must be bearish
        # 'st_7_3_flip': 'bearish',
        # 'st_10_2_direction': {'operator': '==', 'value': -1},
    },
    '5m': {
        'rsi': {'operator': '<', 'value': 65},
        'sumit_ma': {'operator': '<', 'value': 60},
        'sell_signal_count': {'operator': '>', 'value': 10},
    },
    '1h': {
        'sumit_ma': {'operator': '<', 'value': 70},
    },
    'cross': {
        'type': 'DEATH',
        'cross_avg_min': 60
    }
}


# ============================================
# EVALUATION LOGIC (Updated to handle individual ST)
# ============================================

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

def evaluate_indicator_conditions(rules, data):
    """
    Evaluate indicator conditions for a timeframe
    ENHANCED: Now handles individual supertrend conditions
    """
    try:
        for indicator, condition in rules.items():
            # Handle supertrend_flip specially (combined)
            if indicator == 'supertrend_flip':
                if condition == 'bullish' and not data.get('supertrend_bullish_flip', False):
                    return False
                if condition == 'bearish' and not data.get('supertrend_bearish_flip', False):
                    return False
                continue
            
            # NEW: Handle individual ST flips (st_7_3_flip, st_10_2_flip)
            if indicator.endswith('_flip'):
                actual_flip = data.get(indicator)
                if condition == 'bullish' and actual_flip != 'bullish':
                    return False
                if condition == 'bearish' and actual_flip != 'bearish':
                    return False
                continue
            
            # Handle dict format from config or inline
            if isinstance(condition, dict):
                op = condition.get('operator')
                value = condition.get('value')
            # Handle tuple format (backward compatibility)
            elif isinstance(condition, tuple):
                op, value = condition
            else:
                continue
            
            actual = data.get(indicator, 50)
            
            # Handle None values for individual ST (not available yet)
            if actual is None:
                logger.warning(f"Indicator {indicator} not available in data")
                return False
            
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