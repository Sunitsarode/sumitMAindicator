"""
Trade Manager - Handles position management and persistence
"""
import json
import os
import threading
from datetime import datetime
from utils.logging_config import logger
from utils.config_manager import config

class TradeManager:
    """Manages trade data persistence and position tracking"""
    
    def __init__(self, trades_dir='trade_data'):
        self.trades_dir = trades_dir
        self.file_lock = threading.Lock()
        self._ensure_dir()
    
    def _ensure_dir(self):
        """Ensure trade data directory exists"""
        try:
            if not os.path.exists(self.trades_dir):
                os.makedirs(self.trades_dir)
                logger.info(f"Created directory: {self.trades_dir}")
        except Exception as e:
            logger.error(f"Failed to create directory {self.trades_dir}: {e}")
            raise
    
    def _get_filepath(self, symbol):
        """Get filepath for symbol's trade data"""
        safe_symbol = symbol.replace('^', '_').replace('-', '_')
        return os.path.join(self.trades_dir, f'{safe_symbol}_trades.json')
    
    def load_data(self, symbol):
        """Load trade data for symbol with thread-safe file access"""
        self._ensure_dir()
        filepath = self._get_filepath(symbol)
        
        with self.file_lock:
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
    
    def save_data(self, symbol, data):
        """Save trade data with atomic write and thread safety"""
        self._ensure_dir()
        filepath = self._get_filepath(symbol)
        temp_filepath = f"{filepath}.tmp.{threading.get_ident()}"
        
        with self.file_lock:
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
    
    def get_open_position_count(self, symbol):
        """Get count of open positions"""
        data = self.load_data(symbol)
        return len(data.get('openPositions', []))
    
    def can_open_position(self, symbol, direction, timestamp):
        """Check if new position can be opened"""
        try:
            data = self.load_data(symbol)
            open_positions = data.get('openPositions', [])
            
            # Check max positions
            if len(open_positions) >= config.MAX_OPEN_POSITIONS:
                return False, "Max positions reached"
            
            # Check for same direction position
            now = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if 'Z' in timestamp else datetime.fromisoformat(timestamp)
            for pos in open_positions:
                if pos['direction'] == direction:
                    return False, "Same direction position exists"
                
                entry_time = datetime.fromisoformat(pos['entryTime'].replace('Z', '+00:00')) if 'Z' in pos['entryTime'] else datetime.fromisoformat(pos['entryTime'])
                if (now - entry_time).total_seconds() < config.MIN_SIGNAL_GAP_SECONDS:
                    return False, "Too soon after last entry"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error checking if can open position: {e}")
            return False, f"Error: {str(e)}"
    
    def calculate_daily_stats(self, symbol):
        """Calculate daily trading statistics"""
        try:
            data = self.load_data(symbol)
            trades = data.get('trades', [])
            
            today = datetime.now().date().isoformat()
            
            # Filter today's trades
            today_trades = [t for t in trades if t.get('timestamp', '').startswith(today)]
            
            if not today_trades:
                return {
                    'date': today,
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'totalPL': 0,
                    'winRate': 0
                }
            
            wins = [t for t in today_trades if t.get('pl', 0) > 0]
            losses = [t for t in today_trades if t.get('pl', 0) <= 0]
            total_pl = sum(t.get('pl', 0) for t in today_trades)
            
            return {
                'date': today,
                'trades': len(today_trades),
                'wins': len(wins),
                'losses': len(losses),
                'totalPL': total_pl,
                'winRate': (len(wins) / len(today_trades) * 100) if today_trades else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating daily stats: {e}")
            return {}

# Global instance
trade_manager = TradeManager()
