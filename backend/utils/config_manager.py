"""
Configuration Manager - Loads from .env and config.json
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from .env and config.json"""
        
        # Flask settings
        self.FLASK_ENV = os.getenv('FLASK_ENV', 'production')
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        
        # Load config.json for complex settings
        try:
            with open('config.json', 'r') as f:
                json_config = json.load(f)
        except FileNotFoundError:
            print("Warning: config.json not found, using defaults")
            json_config = {}
        
        # Symbols - prefer env var, fallback to config.json
        symbols_env = os.getenv('SYMBOLS')
        if symbols_env:
            self.SYMBOLS = [s.strip() for s in symbols_env.split(',')]
        else:
            self.SYMBOLS = json_config.get('symbols', ['BTC-USD'])
        
        # Intervals
        self.INTERVALS = json_config.get('intervals', ['1m', '5m', '1h'])
        
        # Update intervals
        self.UPDATE_INTERVAL_MINUTES = int(os.getenv('UPDATE_INTERVAL_MINUTES', 
                                            json_config.get('updateIntervalMinutes', 1)))
        self.AUTO_TRADER_INTERVAL_SECONDS = int(os.getenv('AUTO_TRADER_INTERVAL_SECONDS', 
                                                json_config.get('trading', {}).get('autoTraderIntervalSeconds', 30)))
        
        # Notifications
        self.NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.NOTIFICATION_METHOD = os.getenv('NOTIFICATION_METHOD', 'telegram')
        
        # Logging
        self.ENABLE_LOGS = os.getenv('ENABLE_LOGS', 'true').lower() == 'true'
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'auto_trader.log')
        self.MAX_LOG_SIZE_MB = int(os.getenv('MAX_LOG_SIZE_MB', 10))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
        
        # Trading settings
        trading_config = json_config.get('trading', {})
        self.MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', 
                                       trading_config.get('MAX_OPEN_POSITIONS', 3)))
        self.INITIAL_SL_PERCENT = float(os.getenv('INITIAL_SL_PERCENT', 
                                        trading_config.get('INITIAL_SL_PERCENT', 1)))
        self.TRAILING_SL_PERCENT = float(os.getenv('TRAILING_SL_PERCENT', 
                                         trading_config.get('TRAILING_SL_PERCENT', 0.5)))
        self.PROFIT_TARGET_PERCENT = float(os.getenv('PROFIT_TARGET_PERCENT', 
                                           trading_config.get('PROFIT_TARGET_PERCENT', 2)))
        self.MIN_SIGNAL_GAP_SECONDS = int(os.getenv('MIN_SIGNAL_GAP_SECONDS', 
                                          trading_config.get('MIN_SIGNAL_GAP_SECONDS', 60)))
        
        # Performance settings
        self.MAX_CANDLES_IN_MEMORY = int(os.getenv('MAX_CANDLES_IN_MEMORY', 200))
        self.PARALLEL_SYMBOL_PROCESSING = os.getenv('PARALLEL_SYMBOL_PROCESSING', 'true').lower() == 'true'
        self.RATE_LIMIT_DELAY_MS = int(os.getenv('RATE_LIMIT_DELAY_MS', 200))
        
        # Indicators (from config.json)
        self.INDICATORS = json_config.get('indicators', {})
        
        # Entry conditions (from config.json)
        self.ENTRY_CONDITIONS = json_config.get('entryConditions', {})
        
        # Timeframe weights (from config.json)
        self.TIMEFRAME_WEIGHTS = json_config.get('timeframeWeights', {
            '1m': 0.33, '5m': 0.33, '1h': 0.33
        })
        
        # Candles per interval (from config.json)
        self.CANDLES_PER_INTERVAL = json_config.get('candlesPerInterval', {
            '1m': '1d', '5m': '1d', '1h': '1d'
        })
        
        self.FETCH_ONCE_CANDLE = json_config.get('fetchOnceCandle', {
            '1m': '2d', '5m': '15d', '1h': '100d'
        })
        
        # Timezone
        self.TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    
    def get_trading_config(self):
        """Get trading configuration as dict"""
        return {
            'MAX_OPEN_POSITIONS': self.MAX_OPEN_POSITIONS,
            'INITIAL_SL_PERCENT': self.INITIAL_SL_PERCENT,
            'TRAILING_SL_PERCENT': self.TRAILING_SL_PERCENT,
            'PROFIT_TARGET_PERCENT': self.PROFIT_TARGET_PERCENT,
            'MIN_SIGNAL_GAP_SECONDS': self.MIN_SIGNAL_GAP_SECONDS,
        }

# Global config instance
config = Config()
