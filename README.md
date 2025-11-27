# Trading Dashboard

Multi-timeframe technical analysis dashboard with custom indicators.

## ✨ Features
- Real-time data from yfinance
- Multiple timeframe analysis (1m, 5m, 1h)
- Custom scoring system (0-100 scale)
- RSI, MACD, ADX, Supertrend indicators
- 6 comprehensive charts
- Auto-refresh every 60 seconds

## 🚀 Quick Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## ⚙️ Configuration
Edit `backend/config.json` to customize symbols, intervals, and indicator parameters.

## 📊 Tech Stack
- **Backend:** Flask + yfinance + ta library
- **Frontend:** React + Tailwind CSS + Recharts
- **Indicators:** ta library (stable, easy installation)

## ⚠️ Important Notes
- yfinance 1-minute data limited to last 7 days
- For production, consider paid APIs for real-time data
- Background scheduler updates data every 1 minute

## 📝 License
MIT

For NIFTY : RSI follows 1hr
Strong Reversal to Bullish 
IF RSI_score < 30 
AND Supertrend_score > 3 (
AND price < MA201

1. create new function in sumit_ma.py 
sumit_ma_signals()

SUMIT_MA SIGNAL  LOGIC : 
count MA to price in terms of BUY signal or SELL signal
find where is price in terms of MA
We are using total 18 moving averages here. remove ma3(H) and ma3(L)

count BUY signal = it would be max 0-18
count SELL signal = it would be max 0-18

create a chart for it also and include in this logic in auto_trader.py

2.
new supertrend logic : change whole logic as per below
1. there are 3 timeframes and 2 supertrend settings.. give 1 to 6 points to each if any one is green give 1 point else give 0 point
normalized it to range of 0 to 100
2. remove logic of weights={"1m": 1, "5m": 2, "1h": 4}
3. add supertrend flip logic : flip to bullish or bearish
Example in autotrader.py
'1m': {
        'rsi': ('>', 30),           # Min:0 Max:100 | >30 = not oversold
        'supertrend': ('>', 50), 
        'supertrend_flip': 'bullish'  # as soon as the supertrend flip to bullish from bearish the entry will done


BACKEND ISSUE :
Add Notification to existing system 
1. notification integration : "notifications": {
    "enabled": true,
    "method": "telegram",
    "telegram": {
      "token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    },
    "ntfy": {
      "endpoint": "https://ntfy.sh/your-topic"
    }
  },
2. convert config.json to .env file
3. divide auto_trader.py to 3 modules auto_trader to reduce code 
   give option to turn of logs = true / false
   Logs rotate indefinitely (disk space)

4. Async Processing - Process multiple symbols in parallel
5. Better Caching - Keep only last 200 candles in memory
6. Rate Limiting - Prevent yfinance API throttling
7. Multiple positions modified simultaneously without locks
8. File I/O not thread-safe (temp file pattern insufficient)
9. Auto-trader runs every 30s while data updates every 1m - timing conflicts

Data Quality Issues
       1. Supertrend calculation can fail silently, returns NaN
       2. No validation that indicators are ready before trading
       3. Missing data handling inconsistent
Performance

        1. Recalculates ALL 301-period MAs on every update
        2. No incremental updates
        3. Fetches full history repeatedly
Production Gaps
        No monitoring/alerting

FRONTEND ISSUE:
charts.jsx : 
1. Chart 4: Price Chart (OHLC) : HERE I NEED CANDELSTICK CHART WITH MOVING AVG 9,21,51,101
2. Chart 5: Cross-Timeframe Sumit MA with SMA Crossover : SHOW BLANK NO OUTPUT SEEN
3. Chart 6: Sumit MA Signals (BUY/SELL Count) : ONLY NEED LINE CHART OF RANGE 0-18 VALUES REMOVE CURRENTLY RANGE (-18 -18) , ADD MA3 AND MA9 TO THIS LINE CHART.
Notifications.jsx : 
1. add entry time to the table

"ALL TIMING SHOULD BE IN IST"

IMP NOTES : Read this github project CAREFULLY.. ITS A WORKING LIVE PROJECT..if small change in file give me change only.. if more change then give me completely code.. give all code step step in seperate code windows.. mention filename at top