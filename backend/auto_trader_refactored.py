"""
AUTO TRADER - Refactored with Modular Design
"""
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logging_config import logger
from utils.config_manager import config
from utils.cache import get_cache
from trading.trade_manager import trade_manager
from trading.position_manager import (
    get_indicator_values, calculate_trailing_sl, 
    open_trade, close_trade
)
from trading.signal_evaluator import (
    check_long_conditions, check_short_conditions, get_cross_info
)
from utils.notifications import notification_manager

def process_symbol(symbol):
    """Process trading logic for a single symbol"""
    try:
        # Get cached data
        cache_1m = get_cache(symbol, '1m')
        cache_5m = get_cache(symbol, '5m')
        cache_1h = get_cache(symbol, '1h')
        
        if cache_1m is None or len(cache_1m) < 2:
            logger.warning(f"Insufficient 1m data for {symbol}")
            return
        
        # Keep only last MAX_CANDLES_IN_MEMORY to save memory
        if len(cache_1m) > config.MAX_CANDLES_IN_MEMORY:
            cache_1m = cache_1m.tail(config.MAX_CANDLES_IN_MEMORY)
        
        # Get current and previous candle data
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
        
        # Load trade data
        data = trade_manager.load_data(symbol)
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
            close_trade(symbol, data, pos_id, price, timestamp, reason, candle_dict)
        
        # Check entry conditions
        long_ok, long_reason = check_long_conditions(curr_1m, prev_1m, data_5m, data_1h)
        short_ok, short_reason = check_short_conditions(curr_1m, prev_1m, data_5m, data_1h)
        
        if long_ok:
            strength = f"LONG (ST:{curr_1m['supertrend_points']}/6, BUY:{curr_1m['buy_signal_count']}/18)"
            open_trade(symbol, data, 'LONG', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
        elif short_ok:
            strength = f"SHORT (ST:{curr_1m['supertrend_points']}/6, SELL:{curr_1m['sell_signal_count']}/18)"
            open_trade(symbol, data, 'SHORT', strength, price, timestamp, 'CUSTOM', candle_dict, cross_info)
        
        # Save data
        trade_manager.save_data(symbol, data)
        
        # Rate limiting
        if config.RATE_LIMIT_DELAY_MS > 0:
            time.sleep(config.RATE_LIMIT_DELAY_MS / 1000.0)
        
    except Exception as e:
        logger.error(f"Critical error processing {symbol}: {e}", exc_info=True)
        # Send error notification
        notification_manager.send_error_alert(f"Error processing {symbol}: {str(e)}")

def run_auto_trader():
    """Main auto trader loop with optional parallel processing"""
    try:
        logger.info(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto Trader Running")
        
        symbols = config.SYMBOLS
        
        if config.PARALLEL_SYMBOL_PROCESSING and len(symbols) > 1:
            # Process symbols in parallel
            with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
                futures = {executor.submit(process_symbol, symbol): symbol for symbol in symbols}
                
                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {e}", exc_info=True)
        else:
            # Process symbols sequentially
            for symbol in symbols:
                try:
                    process_symbol(symbol)
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol}: {e}", exc_info=True)
                    continue
                    
    except Exception as e:
        logger.critical(f"❌ Critical error in auto trader: {e}", exc_info=True)
        notification_manager.send_error_alert(f"Critical auto trader error: {str(e)}")

if __name__ == '__main__':
    run_auto_trader()
