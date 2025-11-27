"""
Logging Configuration with Rotation
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from utils.config_manager import config

def setup_logging():
    """Setup logging with rotation"""
    
    if not config.ENABLE_LOGS:
        # Disable all logging except CRITICAL
        logging.basicConfig(level=logging.CRITICAL)
        return logging.getLogger(__name__)
    
    # Create logger
    logger = logging.getLogger('trading_dashboard')
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    max_bytes = config.MAX_LOG_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=max_bytes,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging configured: Level={config.LOG_LEVEL}, File={config.LOG_FILE}, MaxSize={config.MAX_LOG_SIZE_MB}MB, Backups={config.LOG_BACKUP_COUNT}")
    
    return logger

# Setup logging on import
logger = setup_logging()
