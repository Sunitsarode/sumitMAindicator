from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from routes.dashboard import dashboard_bp
from routes.symbol import symbol_bp
from routes.trades import trades_bp
from utils.scheduler import update_all_data, fetch_initial_data
from auto_trader_refactored import run_auto_trader  # Updated import
from utils.config_manager import config  # New import
from utils.logging_config import logger  # New import
import atexit
import pytz

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(symbol_bp, url_prefix='/api/symbol')
app.register_blueprint(trades_bp, url_prefix='/api/trades')

# Fetch initial historical data ONCE at startup
print("\n" + "="*50)
print("🚀 STARTING TRADING DASHBOARD + AUTO TRADER")
print("="*50)
logger.info("Starting Trading Dashboard")
fetch_initial_data()

# Setup scheduler with timezone
timezone = pytz.timezone(config.TIMEZONE)
scheduler = BackgroundScheduler(timezone=timezone)

# Job 1: Update market data
scheduler.add_job(
    func=update_all_data,
    trigger="interval",
    minutes=config.UPDATE_INTERVAL_MINUTES,
    id='update_data',
    timezone=timezone
)

# Job 2: Auto trader
scheduler.add_job(
    func=run_auto_trader,
    trigger="interval",
    seconds=config.AUTO_TRADER_INTERVAL_SECONDS,
    id='auto_trader',
    timezone=timezone
)

scheduler.start()
logger.info(f"✅ Auto Trader Started - Running every {config.AUTO_TRADER_INTERVAL_SECONDS} seconds")
logger.info(f"✅ Data Updates - Running every {config.UPDATE_INTERVAL_MINUTES} minute(s)")
logger.info(f"✅ Timezone: {config.TIMEZONE}")

atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    return jsonify({
        "status": "Trading Dashboard API Running",
        "version": "2.0",
        "auto_trader": "ACTIVE",
        "timezone": config.TIMEZONE,
        "symbols": config.SYMBOLS,
        "max_positions": config.MAX_OPEN_POSITIONS
    })

if __name__ == '__main__':
    app.run(
        debug=config.FLASK_DEBUG,
        port=config.FLASK_PORT,
        host=config.FLASK_HOST
    )
