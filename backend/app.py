from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from routes.dashboard import dashboard_bp
from routes.symbol import symbol_bp
from routes.trades import trades_bp
from utils.scheduler import update_all_data, fetch_initial_data
from auto_trader import run_auto_trader  # NEW
import json
import atexit

app = Flask(__name__)
CORS(app)

with open('config.json', 'r') as f:
    config = json.load(f)

app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(symbol_bp, url_prefix='/api/symbol')
app.register_blueprint(trades_bp, url_prefix='/api/trades')

# Fetch initial historical data ONCE at startup
print("\n" + "="*50)
print("🚀 STARTING TRADING DASHBOARD + AUTO TRADER")
print("="*50)
fetch_initial_data()

# Setup scheduler
scheduler = BackgroundScheduler()

# Job 1: Update market data
scheduler.add_job(
    func=update_all_data,
    trigger="interval",
    minutes=config.get('updateIntervalMinutes', 1),
    id='update_data'
)

# Job 2: Auto trader - runs every 30 seconds
scheduler.add_job(
    func=run_auto_trader,
    trigger="interval",
    seconds=30,
    id='auto_trader'
)

scheduler.start()
print("✅ Auto Trader Started - Running every 30 seconds")

atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    return jsonify({
        "status": "Trading Dashboard API Running",
        "version": "1.0",
        "auto_trader": "ACTIVE"
    })

if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')  # host=0.0.0.0 for server access
