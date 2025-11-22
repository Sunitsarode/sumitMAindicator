import React, { useState, useEffect } from 'react';
import { API } from '../config';

const Dashboard = ({ onSymbolClick, onLiveClick }) => {
  const [dashboardData, setDashboardData] = useState([]);
  const [symbolsFullData, setSymbolsFullData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchDashboard = async () => {
    try {
      const response = await fetch(API.dashboard);
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      const data = await response.json();
      setDashboardData(data);
      
      const fullDataPromises = data.map(async (symbolData) => {
        try {
          const res = await fetch(API.symbol(symbolData.symbol));
          if (res.ok) {
            const fullData = await res.json();
            return { symbol: symbolData.symbol, data: fullData };
          }
        } catch (err) { console.error(`Error fetching ${symbolData.symbol}:`, err); }
        return null;
      });
      
      const results = await Promise.all(fullDataPromises);
      const fullDataMap = {};
      results.filter(r => r).forEach(r => { fullDataMap[r.symbol] = r.data; });
      
      setSymbolsFullData(fullDataMap);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setError('Failed to load dashboard. Make sure backend is running on port 5000.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-xl">Loading dashboard...</div></div>;
  if (error) return (
    <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
      {error}
      <button onClick={fetchDashboard} className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm">Retry</button>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">All Symbols Overview</h2>
        <div className="flex items-center gap-4">
          {lastUpdate && <div className="text-sm text-gray-400 animate-pulse">🔴 Live - Last Update: {lastUpdate.toLocaleTimeString()}</div>}
          <button onClick={fetchDashboard} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-semibold">🔄 Refresh</button>
        </div>
      </div>
      {dashboardData.length === 0 ? (
        <div className="text-gray-400">No data available. Backend is starting up...</div>
      ) : (
        dashboardData.map((symbolData) => (
          <SymbolCard key={symbolData.symbol} symbolData={symbolData} fullData={symbolsFullData[symbolData.symbol]} onSymbolClick={onSymbolClick} onLiveClick={onLiveClick} />
        ))
      )}
    </div>
  );
};

const SymbolCard = ({ symbolData, fullData, onSymbolClick, onLiveClick }) => {
  const intervals = ['1m', '5m', '1h'];
  const predictions = {};
  
  if (fullData) {
    intervals.forEach(interval => {
      const candles = fullData[interval] || [];
      const last10 = candles.slice(-10);
      if (last10.length >= 2) {
        const calculateSMA = (arr, field) => {
          const values = arr.map(c => parseFloat(c[field]) || 0).filter(v => v > 0);
          return values.reduce((a, b) => a + b, 0) / values.length;
        };
        const sma9_H = calculateSMA(last10, 'High'), sma9_L = calculateSMA(last10, 'Low');
        const sma9_O = calculateSMA(last10, 'Open'), sma9_C = calculateSMA(last10, 'Close');
        const sma9_HLOC = (sma9_H + sma9_L + sma9_O + sma9_C) / 4;
        const current = candles[candles.length - 1];
        const currentClose = parseFloat(current.Close) || 0, currentOpen = parseFloat(current.Open) || 0;
        predictions[interval] = {
          current: currentClose, open: currentClose + (sma9_HLOC - sma9_O),
          high: currentClose + (sma9_H - sma9_O), low: currentClose + (sma9_L - sma9_O),
          close: currentClose + (sma9_C - sma9_O), isBullish: currentClose > currentOpen, sma9_HLOC
        };
      }
    });
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-4 bg-gray-750 border-b border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-bold">{symbolData.symbol}</h3>
        <div className="flex gap-2">
          <button onClick={() => onLiveClick(symbolData.symbol)} className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold">🔴 Live</button>
          <button onClick={() => onSymbolClick(symbolData.symbol)} className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm font-semibold">📈 Charts</button>
        </div>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          {intervals.map(interval => {
            const scores = symbolData.intervals[interval];
            const pred = predictions[interval];
            return (
              <div key={interval} className="bg-gray-750 rounded-lg p-3">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-lg">{interval}</h4>
                  <div className="text-right">
                    <div className="text-xs text-gray-400">Price</div>
                    <div className="text-lg font-bold text-blue-400">{scores?.price?.toFixed(2) || 'N/A'}</div>
                  </div>
                </div>
                {pred ? <MiniCandlestick {...pred} /> : <div className="text-center text-gray-500 text-sm py-4">Loading...</div>}
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div><div className="text-xs text-gray-400">RSI</div><ScoreBadge score={scores?.rsi_score} small /></div>
                  <div><div className="text-xs text-gray-400">MACD</div><ScoreBadge score={scores?.macd_score} small /></div>
                  <div><div className="text-xs text-gray-400">ADX</div><ScoreBadge score={scores?.adx_score} small /></div>
                  <div><div className="text-xs text-gray-400">ST</div><ScoreBadge score={scores?.supertrend_score} small /></div>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="text-xs text-gray-400 mb-1">Avg Score</div>
                  <ScoreBadge score={scores?.avg_score} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const MiniCandlestick = ({ open, high, low, close, avgLine, isBullish }) => {
  const svgHeight = 150, svgWidth = 100, padding = 15;
  const priceRange = high - low, scale = (svgHeight - 2 * padding) / priceRange;
  const toY = (price) => svgHeight - padding - (price - low) * scale;
  const openY = toY(open), highY = toY(high), lowY = toY(low), closeY = toY(close), avgY = toY(avgLine);
  const bodyTop = Math.min(openY, closeY), bodyHeight = Math.abs(openY - closeY) || 1;
  const bodyWidth = 20, centerX = svgWidth / 2, color = isBullish ? '#10b981' : '#ef4444';
  
  return (
    <div className="flex justify-center">
      <svg width={svgWidth} height={svgHeight}>
        <line x1={centerX} y1={highY} x2={centerX} y2={lowY} stroke={color} strokeWidth="1.5" />
        <rect x={centerX - bodyWidth / 2} y={bodyTop} width={bodyWidth} height={bodyHeight} fill={color} stroke={color} />
        <line x1={padding} y1={avgY} x2={svgWidth - padding} y2={avgY} stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="3,3" />
        <text x="5" y={highY} fill="#9ca3af" fontSize="9">{high.toFixed(1)}</text>
        <text x="5" y={lowY} fill="#9ca3af" fontSize="9">{low.toFixed(1)}</text>
        <circle cx={centerX} cy={openY} r="2" fill="#10b981" />
        <circle cx={centerX} cy={closeY} r="2" fill="#ef4444" />
      </svg>
    </div>
  );
};

const ScoreBadge = ({ score, small = false }) => {
  if (score === undefined || score === null) return <span className="text-gray-500 text-xs">N/A</span>;
  const getColor = (val) => val >= 80 ? 'bg-red-500' : val >= 60 ? 'bg-orange-500' : val >= 40 ? 'bg-yellow-500' : val >= 20 ? 'bg-green-500' : 'bg-blue-500';
  const sizeClass = small ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';
  return <span className={`${getColor(score)} ${sizeClass} rounded-full font-semibold inline-block`}>{score.toFixed(1)}</span>;
};

export default Dashboard;
