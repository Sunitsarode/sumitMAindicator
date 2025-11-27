"""
Position Manager - Handles position operations and calculations
"""
import pandas as pd
from datetime import datetime
from utils.logging_config import logger
from utils.config_manager import config
from utils.notifications import notification_manager

def _safe_int(value, default=0):
    """Safely convert to int"""
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def _safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def get_indicator_values(candle):
    """Extract all indicator values from candle"""
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
        return {
            'rsi': 50, 'macd': 50, 'adx': 50, 'supertrend': 50,
            'supertrend_points': 3, 'supertrend_bullish_flip': False,
            'supertrend_bearish_flip': False, 'sumit_ma': 50,
            'buy_signal_count': 0, 'sell_signal_count': 0,
            'cross_avg': 0, 'cross_sma9': 0, 'cross_sma21': 0, 'price': 0
        }

def calculate_sl_price(entry_price, direction):
    """Calculate stop loss price"""
    try:
        sl_percent = config.INITIAL_SL_PERCENT
        if direction == 'LONG':
            return entry_price * (1 - sl_percent / 100)
        else:
            return entry_price * (1 + sl_percent / 100)
    except Exception as e:
        logger.error(f"Error calculating SL: {e}")
        return entry_price * 0.99

def calculate_trailing_sl(current_price, direction, current_sl):
    """Calculate trailing stop loss"""
    try:
        trail_percent = config.TRAILING_SL_PERCENT
        
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
        target_percent = config.PROFIT_TARGET_PERCENT
        if direction == 'LONG':
            return entry_price * (1 + target_percent / 100)
        else:
            return entry_price * (1 - target_percent / 100)
    except Exception as e:
        logger.error(f"Error calculating profit target: {e}")
        return entry_price * 1.02

def open_trade(symbol, data, direction, strength, price, timestamp, signal_type, candle_dict, cross_info=None):
    """Open a new trade"""
    try:
        from trading.trade_manager import trade_manager
        
        can_open, reason = trade_manager.can_open_position(symbol, direction, timestamp)
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
            'slPercent': config.INITIAL_SL_PERCENT,
            'targetPercent': config.PROFIT_TARGET_PERCENT,
            'highestPL': 0,
            'entryCriteria': entry_criteria,
        }
        
        if cross_info:
            new_position['crossInfo'] = cross_info
        
        data['openPositions'].append(new_position)
        open_count = len(data['openPositions'])
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 OPENED {direction} [{signal_type}] #{open_count}/{config.MAX_OPEN_POSITIONS}")
        logger.info(f"   Entry: {price:.2f} | SL: {sl:.2f} ({config.INITIAL_SL_PERCENT}%) | Target: {target:.2f} ({config.PROFIT_TARGET_PERCENT}%)")
        logger.info(f"   ST Score: {entry_criteria['supertrend']:.0f} ({entry_criteria['supertrend_points']}/6) | BUY: {entry_criteria['buy_signal_count']}/18 | SELL: {entry_criteria['sell_signal_count']}/18")
        logger.info(f"   RSI={entry_criteria['rsi']:.0f} MACD={entry_criteria['macd']:.0f} SMA={entry_criteria['sumit_ma']:.0f}")
        if entry_criteria['supertrend_bullish_flip']:
            logger.info(f"   🔥 SUPERTREND BULLISH FLIP!")
        logger.info(f"{'='*60}\n")
        
        # Send notification
        notification_manager.send_trade_notification(
            symbol=symbol,
            direction=direction,
            action='OPENED',
            price=price,
            details=entry_criteria
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error opening trade: {e}", exc_info=True)
        return False

def close_trade(symbol, data, position_id, exit_price, timestamp, reason, candle_dict):
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
        
        # Send notification
        notification_manager.send_trade_notification(
            symbol=symbol,
            direction=pos['direction'],
            action='CLOSED',
            price=exit_price,
            pl=pl_points,
            reason=reason,
            details=exit_criteria
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error closing trade: {e}", exc_info=True)
        return False
