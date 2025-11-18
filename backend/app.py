from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from routes.dashboard import dashboard_bp
from routes.symbol import symbol_bp
from utils.scheduler import update_all_data, fetch_initial_data
import json
import atexit

app = Flask(__name__)
CORS(app)

with open('config.json', 'r') as f:
    config = json.load(f)

app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(symbol_bp, url_prefix='/api/symbol')

# Fetch initial historical data ONCE at startup
print("\n" + "="*50)
print("🚀 STARTING TRADING DASHBOARD")
print("="*50)
fetch_initial_data()

# Setup scheduler for regular updates
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_all_data,
    trigger="interval",
    minutes=config.get('updateIntervalMinutes', 1)
)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    return jsonify({"status": "Trading Dashboard API Running", "version": "1.0"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
