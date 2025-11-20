import React, { useState, useEffect } from 'react';

const LiveAnalysis = ({ symbol }) => {
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedInterval, setSelectedInterval] = useState('1m');

  const fetchSymbolData = async () => {
    if (!symbol) return;
    
    try {
      setError(null);
      const response = await fetch(`http://localhost:5000/api/symbol/${symbol}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      if (!data || Object.keys(data).length === 0) {
        throw new Error('No data available');
      }
      
      setSymbolData(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching symbol data:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSymbolData();
    // Auto-refresh every minute
    const interval = setInterval(fetchSymbolData, 60000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (!symbol) {
    return (
      <div className="text-center text-gray-400">
        Please select a symbol from the dashboard
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Loading live data for {symbol}...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
        {error}
        <button 
          onClick={fetchSymbolData} 
          className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  const intervals = ['1m', '5m', '1h'];
  const candles = symbolData[selectedInterval] || [];
  const last10 = candles.slice(-10);
  
  if (last10.length < 2) {
    return <div className="text-gray-400">Not enough data for analysis</div>;
  }

  // Calculate SMA9
  const calculateSMA = (arr, field) => {
    const values = arr.map(c => parseFloat(c[field]) || 0).filter(v => v > 0);
    return values.reduce((a, b) => a + b, 0) / values.length;
  };

  const sma9_H = calculateSMA(last10, 'High');
  const sma9_L = calculateSMA(last10, 'Low');
  const sma9_O = calculateSMA(last10, 'Open');
  const sma9_C = calculateSMA(last10, 'Close');
  const sma9_HLOC = (sma9_H + sma9_L + sma9_O + sma9_C) / 4;

  const current = candles[candles.length - 1];
  const currentPrice = parseFloat(current.Close) || 0;
  const currentOpen = parseFloat(current.Open) || 0;
  const currentClose = parseFloat(current.Close) || 0;

  const diffH = sma9_H - sma9_O;
  const diffL = sma9_L - sma9_O;
  const diffC = sma9_C - sma9_O;
  const diffHLOC = sma9_HLOC - sma9_O;

  const predictedOpen = currentClose + diffHLOC;
  const predictedHigh = currentClose + diffH;
  const predictedLow = currentClose + diffL;
  const predictedClose = currentClose + diffC;

  const isBullish = currentClose > currentOpen;
  const isStrongBullish = currentClose > sma9_HLOC;
  const sentiment = isStrongBullish ? "Strong Bullish 🚀" : isBullish ? "Bullish 📈" : "Bearish 📉";
  const sentimentColor = isStrongBullish ? "text-green-400" : isBullish ? "text-yellow-400" : "text-red-400";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">🔴 Live Market Analysis - {symbol}</h2>
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            {intervals.map(interval => (
              <button
                key={interval}
                onClick={() => setSelectedInterval(interval)}
                className={`px-3 py-1 rounded-lg transition text-sm font-semibold ${
                  selectedInterval === interval
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {interval}
              </button>
            ))}
          </div>
          {lastUpdate && (
            <div className="text-sm text-gray-400 animate-pulse">
              🔴 Live - Updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* Live Analysis Card */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="grid grid-cols-3 gap-6 mb-6">
          {/* Current Price */}
          <div className="bg-gray-750 p-4 rounded-lg">
            <h4 className="text-sm text-gray-400 mb-2">Current Price</h4>
            <p className="text-3xl font-bold text-blue-400">{currentPrice.toFixed(2)}</p>
          </div>

          {/* Market Sentiment */}
          <div className="bg-gray-750 p-4 rounded-lg col-span-2">
            <h4 className="text-sm text-gray-400 mb-2">Market Sentiment</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">Trend:</span>
                <span className={`font-bold text-xl ${sentimentColor}`}>{sentiment}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">Close vs Open:</span>
                <span className={`font-semibold ${isBullish ? "text-green-400" : "text-red-400"}`}>
                  {isBullish ? "Bullish ✓" : "Bearish ✗"}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-sm">Close vs Average:</span>
                <span className={`font-semibold ${isStrongBullish ? "text-green-400" : "text-red-400"}`}>
                  {isStrongBullish ? "Above Average (Strong) ✓" : "Below Average ✗"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Possible Moves Table */}
        <div>
          <h4 className="text-md font-semibold mb-3">Possible Next Moves</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 px-3">Timeframe</th>
                  <th className="text-right py-2 px-3">O →</th>
                  <th className="text-right py-2 px-3">H ↑</th>
                  <th className="text-right py-2 px-3">L ↓</th>
                  <th className="text-right py-2 px-3">C ←</th>
                </tr>
              </thead>
              <tbody>
                <tr className="bg-gray-750">
                  <td className="py-2 px-3 font-semibold">1D</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedOpen.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-green-400">{predictedHigh.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-red-400">{predictedLow.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedClose.toFixed(2)}</td>
                </tr>
                <tr className="border-t border-gray-700">
                  <td className="py-2 px-3 font-semibold">1hr</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedOpen.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-green-400">{predictedHigh.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-red-400">{predictedLow.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedClose.toFixed(2)}</td>
                </tr>
                <tr className="border-t border-gray-700">
                  <td className="py-2 px-3 font-semibold">5min</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedOpen.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-green-400">{predictedHigh.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono text-red-400">{predictedLow.toFixed(2)}</td>
                  <td className="text-right py-2 px-3 font-mono">{predictedClose.toFixed(2)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Latest Scores */}
        <div className="mt-6 pt-6 border-t border-gray-700">
          <h4 className="text-md font-semibold mb-3">Latest Indicator Scores</h4>
          <div className="grid grid-cols-4 gap-4">
            {current.rsi_score && (
              <div className="bg-gray-750 p-3 rounded">
                <div className="text-xs text-gray-400 mb-1">RSI</div>
                <div className="text-lg font-bold">{parseFloat(current.rsi_score).toFixed(1)}</div>
              </div>
            )}
            {current.macd_score && (
              <div className="bg-gray-750 p-3 rounded">
                <div className="text-xs text-gray-400 mb-1">MACD</div>
                <div className="text-lg font-bold">{parseFloat(current.macd_score).toFixed(1)}</div>
              </div>
            )}
            {current.adx_score && (
              <div className="bg-gray-750 p-3 rounded">
                <div className="text-xs text-gray-400 mb-1">ADX</div>
                <div className="text-lg font-bold">{parseFloat(current.adx_score).toFixed(1)}</div>
              </div>
            )}
            {current.supertrend_score && (
              <div className="bg-gray-750 p-3 rounded">
                <div className="text-xs text-gray-400 mb-1">Supertrend</div>
                <div className="text-lg font-bold">{parseFloat(current.supertrend_score).toFixed(1)}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveAnalysis;