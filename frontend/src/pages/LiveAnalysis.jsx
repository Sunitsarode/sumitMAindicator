import React, { useState, useEffect } from 'react';
import { API } from '../config';

const LiveAnalysis = ({ symbol }) => {
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSymbolData = async () => {
    if (!symbol) return;
    try {
      setError(null);
      const response = await fetch(API.symbol(symbol));
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data || Object.keys(data).length === 0) throw new Error('No data available');
      setSymbolData(data); setLastUpdate(new Date()); setLoading(false);
    } catch (error) { setError(error.message); setLoading(false); }
  };

  useEffect(() => {
    fetchSymbolData();
    const interval = setInterval(fetchSymbolData, 60000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (!symbol) return <div className="text-center text-gray-400">Please select a symbol from the dashboard</div>;
  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-xl">Loading live data for {symbol}...</div></div>;
  if (error) return (
    <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
      {error}<button onClick={fetchSymbolData} className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm">Retry</button>
    </div>
  );

  const intervals = ['1m', '5m', '1h'];
  const predictions = {};
  
  intervals.forEach(interval => {
    const candles = symbolData[interval] || [];
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
        close: currentClose + (sma9_C - sma9_O), isBullish: currentClose > currentOpen,
        isStrongBullish: currentClose > sma9_HLOC, sma9_HLOC
      };
    }
  });

  const currentPrice = predictions['1m']?.current || 0;
  const sentiment = predictions['1m']?.isStrongBullish ? "Strong Bullish 🚀" : predictions['1m']?.isBullish ? "Bullish 📈" : "Bearish 📉";
  const sentimentColor = predictions['1m']?.isStrongBullish ? "text-green-400" : predictions['1m']?.isBullish ? "text-yellow-400" : "text-red-400";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">🔴 Live Market Analysis - {symbol}</h2>
        {lastUpdate && <div className="text-sm text-gray-400 animate-pulse">🔴 Live - Updated: {lastUpdate.toLocaleTimeString()}</div>}
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="grid grid-cols-3 gap-6 mb-6">
          <div className="bg-gray-750 p-4 rounded-lg">
            <h4 className="text-sm text-gray-400 mb-2">Current Price</h4>
            <p className="text-3xl font-bold text-blue-400">{currentPrice.toFixed(2)}</p>
          </div>
          <div className="bg-gray-750 p-4 rounded-lg col-span-2">
            <h4 className="text-sm text-gray-400 mb-2">Market Sentiment</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">Trend:</span>
                <span className={`font-bold text-xl ${sentimentColor}`}>{sentiment}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">Close vs Open:</span>
                <span className={`font-semibold ${predictions['1m']?.isBullish ? "text-green-400" : "text-red-400"}`}>
                  {predictions['1m']?.isBullish ? "Bullish ✓" : "Bearish ✗"}
                </span>
              </div>
            </div>
          </div>
        </div>

        <h4 className="text-md font-semibold mb-4">Possible Next Moves</h4>
        <div className="grid grid-cols-3 gap-6">
          {intervals.map(interval => {
            const pred = predictions[interval];
            return pred ? <CandlestickVisual key={interval} interval={interval} {...pred} /> : null;
          })}
        </div>

        <div className="mt-6 pt-6 border-t border-gray-700">
          <h4 className="text-md font-semibold mb-3">Latest Indicator Scores</h4>
          <div className="grid grid-cols-4 gap-4">
            {symbolData['1m']?.length > 0 && (() => {
              const c = symbolData['1m'][symbolData['1m'].length - 1];
              return ['rsi_score', 'macd_score', 'adx_score', 'supertrend_score'].map(key => (
                c[key] && <div key={key} className="bg-gray-750 p-3 rounded">
                  <div className="text-xs text-gray-400 mb-1">{key.replace('_score', '').toUpperCase()}</div>
                  <div className="text-lg font-bold">{parseFloat(c[key]).toFixed(1)}</div>
                </div>
              ));
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};

const CandlestickVisual = ({ interval, open, high, low, close, avgLine, isBullish }) => {
  const svgHeight = 300, svgWidth = 200, padding = 40;
  const priceRange = high - low, scale = (svgHeight - 2 * padding) / priceRange;
  const toY = (price) => svgHeight - padding - (price - low) * scale;
  const openY = toY(open), highY = toY(high), lowY = toY(low), closeY = toY(close), avgY = toY(avgLine);
  const bodyTop = Math.min(openY, closeY), bodyHeight = Math.abs(openY - closeY) || 2;
  const bodyWidth = 40, centerX = svgWidth / 2, color = isBullish ? '#10b981' : '#ef4444';

  return (
    <div className="bg-gray-750 p-4 rounded-lg">
      <h5 className="text-center font-semibold mb-2 text-lg">{interval}</h5>
      <svg width={svgWidth} height={svgHeight} className="mx-auto">
        <text x="5" y={highY + 5} fill="#9ca3af" fontSize="11">H: {high.toFixed(2)}</text>
        <text x="5" y={lowY - 5} fill="#9ca3af" fontSize="11">L: {low.toFixed(2)}</text>
        <text x={svgWidth - 70} y={openY + 5} fill="#10b981" fontSize="11">O: {open.toFixed(2)}</text>
        <text x={svgWidth - 70} y={closeY - 5} fill="#ef4444" fontSize="11">C: {close.toFixed(2)}</text>
        <line x1={centerX} y1={highY} x2={centerX} y2={lowY} stroke={color} strokeWidth="2" />
        <rect x={centerX - bodyWidth / 2} y={bodyTop} width={bodyWidth} height={bodyHeight} fill={color} stroke={color} />
        <line x1={padding} y1={avgY} x2={svgWidth - padding} y2={avgY} stroke="#3b82f6" strokeWidth="2" strokeDasharray="5,5" />
        <text x={svgWidth - 90} y={avgY - 5} fill="#3b82f6" fontSize="11">Avg: {avgLine.toFixed(2)}</text>
        <circle cx={centerX} cy={openY} r="3" fill="#10b981" />
        <circle cx={centerX} cy={highY} r="3" fill="#60a5fa" />
        <circle cx={centerX} cy={lowY} r="3" fill="#fb923c" />
        <circle cx={centerX} cy={closeY} r="3" fill="#ef4444" />
      </svg>
      <div className="text-center mt-3">
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${isBullish ? 'bg-green-600' : 'bg-red-600'}`}>
          {isBullish ? '📈 Bullish' : '📉 Bearish'}
        </span>
      </div>
    </div>
  );
};

export default LiveAnalysis;
