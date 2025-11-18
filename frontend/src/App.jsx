import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const TradingDashboard = () => {
  const [view, setView] = useState('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [dashboardData, setDashboardData] = useState([]);
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard');
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      const data = await response.json();
      setDashboardData(data);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setError('Failed to load dashboard. Make sure backend is running on port 5000.');
      setLoading(false);
    }
  };

  const fetchSymbolData = async (symbol) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5000/api/symbol/${symbol}`);
      if (!response.ok) throw new Error('Failed to fetch symbol data');
      const data = await response.json();
      setSymbolData(data);
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Error fetching symbol data:', error);
      setError(`Failed to load data for ${symbol}`);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (view === 'dashboard') {
      fetchDashboard();
      const interval = setInterval(fetchDashboard, 60000);
      return () => clearInterval(interval);
    } else if (selectedSymbol) {
      fetchSymbolData(selectedSymbol);
      const interval = setInterval(() => fetchSymbolData(selectedSymbol), 60000);
      return () => clearInterval(interval);
    }
  }, [view, selectedSymbol]);

  const handleSymbolClick = (symbol) => {
    setSelectedSymbol(symbol);
    setView('symbol');
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setSelectedSymbol(null);
    setSymbolData(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {view === 'symbol' && (
              <button 
                onClick={handleBackToDashboard} 
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                ← Back
              </button>
            )}
            <h1 className="text-2xl font-bold">
              {view === 'dashboard' ? 'Trading Dashboard' : `${selectedSymbol} Analysis`}
            </h1>
          </div>
          {lastUpdate && (
            <div className="text-sm text-gray-400">
              Last Update: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>
      </header>

      <main className="p-6">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-xl">Loading...</div>
          </div>
        ) : view === 'dashboard' ? (
          <DashboardView data={dashboardData} onSymbolClick={handleSymbolClick} />
        ) : (
          <SymbolView data={symbolData} symbol={selectedSymbol} />
        )}
      </main>
    </div>
  );
};

const DashboardView = ({ data, onSymbolClick }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold mb-4">All Symbols Overview</h2>
    {data.length === 0 ? (
      <div className="text-gray-400">No data available. Backend is starting up...</div>
    ) : (
      data.map((symbolData) => (
        <div key={symbolData.symbol} className="bg-gray-800 rounded-lg overflow-hidden">
          <div 
            className="p-4 bg-gray-750 border-b border-gray-700 cursor-pointer hover:bg-gray-700 transition" 
            onClick={() => onSymbolClick(symbolData.symbol)}
          >
            <h3 className="text-lg font-bold">{symbolData.symbol}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-750 text-left">
                  <th className="px-4 py-3">Interval</th>
                  <th className="px-4 py-3">Price</th>
                  <th className="px-4 py-3">RSI</th>
                  <th className="px-4 py-3">MACD</th>
                  <th className="px-4 py-3">ADX</th>
                  <th className="px-4 py-3">Supertrend</th>
                  <th className="px-4 py-3">Avg Score</th>
                  <th className="px-4 py-3">Weighted Avg</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(symbolData.intervals).map(([interval, scores]) => (
                  <tr key={interval} className="border-t border-gray-700 hover:bg-gray-750">
                    <td className="px-4 py-3 font-semibold">{interval}</td>
                    <td className="px-4 py-3">${scores.price.toFixed(2)}</td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.rsi_score} /></td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.macd_score} /></td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.adx_score} /></td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.supertrend_score} /></td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.avg_score} /></td>
                    <td className="px-4 py-3"><ScoreBadge score={scores.weighted_avg_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))
    )}
  </div>
);

const SymbolView = ({ data, symbol }) => {
  if (!data) return <div>No data available</div>;
  const intervals = ['1m', '5m', '1h'];
  
  return (
    <div className="space-y-8">
      <ChartContainer title="Chart 1: Individual Indicator Scores">
        <MultiIntervalChart 
          data={data} 
          intervals={intervals} 
          lines={[
            { key: 'rsi_score', name: 'RSI', color: '#8884d8' },
            { key: 'macd_score', name: 'MACD', color: '#82ca9d' },
            { key: 'adx_score', name: 'ADX', color: '#ffc658' },
            { key: 'supertrend_score', name: 'Supertrend', color: '#ff7c7c' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 2: Composite Scores">
        <MultiIntervalChart 
          data={data} 
          intervals={intervals} 
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#82ca9d' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 3: Average Score with SMA Crossover">
        <MultiIntervalChart 
          data={data} 
          intervals={intervals} 
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'avg_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'avg_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 4: Weighted Average with SMA Crossover">
        <MultiIntervalChart 
          data={data} 
          intervals={intervals} 
          lines={[
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#8884d8' },
            { key: 'weighted_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'weighted_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 5: Sumit MA Indicator">
        <MultiIntervalChart 
          data={data} 
          intervals={intervals} 
          lines={[
            { key: 'sumit_ma_score', name: 'Sumit MA', color: '#9b59b6' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 6: Price Chart (OHLC)">
        <CandlestickChart data={data} intervals={intervals} />
      </ChartContainer>
    </div>
  );
};

const ChartContainer = ({ title, children }) => (
  <div className="bg-gray-800 rounded-lg p-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    {children}
  </div>
);

const ScoreBadge = ({ score }) => {
  const getColor = (val) => {
    if (val >= 80) return 'bg-red-500';
    if (val >= 60) return 'bg-orange-500';
    if (val >= 40) return 'bg-yellow-500';
    if (val >= 20) return 'bg-green-500';
    return 'bg-blue-500';
  };
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getColor(score)}`}>
      {score.toFixed(1)}
    </span>
  );
};

const MultiIntervalChart = ({ data, intervals, lines }) => {
  const [selectedInterval, setSelectedInterval] = useState(intervals[0]);
  
  const chartData = data[selectedInterval]?.slice(-100).map((candle, idx) => ({
    index: idx,
    ...candle
  })) || [];

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {intervals.map(interval => (
          <button 
            key={interval} 
            onClick={() => setSelectedInterval(interval)}
            className={`px-4 py-2 rounded-lg transition ${
              selectedInterval === interval 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {interval}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="index" stroke="#9ca3af" />
          <YAxis domain={[0, 100]} stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151' 
            }} 
          />
          <Legend />
          
          <ReferenceLine 
            y={80} 
            stroke="#ef4444" 
            strokeDasharray="3 3" 
            label="Overbought" 
          />
          <ReferenceLine 
            y={50} 
            stroke="#6b7280" 
            strokeDasharray="3 3" 
            label="Neutral" 
          />
          <ReferenceLine 
            y={20} 
            stroke="#10b981" 
            strokeDasharray="3 3" 
            label="Oversold" 
          />
          
          {lines.map(line => (
            <Line 
              key={line.key} 
              type="monotone" 
              dataKey={line.key} 
              stroke={line.color} 
              name={line.name} 
              dot={false} 
              strokeWidth={2} 
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const CandlestickChart = ({ data, intervals }) => {
  const [selectedInterval, setSelectedInterval] = useState(intervals[0]);
  
  const chartData = data[selectedInterval]?.slice(-50).map((candle, idx) => ({
    index: idx,
    ...candle
  })) || [];

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {intervals.map(interval => (
          <button 
            key={interval} 
            onClick={() => setSelectedInterval(interval)}
            className={`px-4 py-2 rounded-lg transition ${
              selectedInterval === interval 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {interval}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="index" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" domain={['auto', 'auto']} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151' 
            }} 
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="Close" 
            stroke="#3b82f6" 
            name="Close Price" 
            strokeWidth={2} 
          />
          <Line 
            type="monotone" 
            dataKey="High" 
            stroke="#10b981" 
            name="High" 
            strokeWidth={1} 
            strokeDasharray="3 3" 
          />
          <Line 
            type="monotone" 
            dataKey="Low" 
            stroke="#ef4444" 
            name="Low" 
            strokeWidth={1} 
            strokeDasharray="3 3" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TradingDashboard;