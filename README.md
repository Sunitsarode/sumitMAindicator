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
