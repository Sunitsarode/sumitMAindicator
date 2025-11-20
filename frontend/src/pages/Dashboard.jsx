import React, { useState, useEffect } from 'react';

const Dashboard = ({ onSymbolClick, onLiveClick }) => {
  const [dashboardData, setDashboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

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

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
        {error}
        <button 
          onClick={fetchDashboard} 
          className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">All Symbols Overview</h2>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <div className="text-sm text-gray-400">
              Last Update: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button 
            onClick={fetchDashboard}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-semibold"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {dashboardData.length === 0 ? (
        <div className="text-gray-400">No data available. Backend is starting up...</div>
      ) : (
        dashboardData.map((symbolData) => (
          <div key={symbolData.symbol} className="bg-gray-800 rounded-lg overflow-hidden">
            <div className="p-4 bg-gray-750 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-bold">{symbolData.symbol}</h3>
              <div className="flex gap-2">
                <button
                  onClick={() => onLiveClick(symbolData.symbol)}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold"
                >
                  🔴 Live
                </button>
                <button
                  onClick={() => onSymbolClick(symbolData.symbol)}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm font-semibold"
                >
                  📈 Charts
                </button>
              </div>
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
                    <th className="px-4 py-3">O →</th>
                    <th className="px-4 py-3">H ↑</th>
                    <th className="px-4 py-3">L ↓</th>
                    <th className="px-4 py-3">C ←</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(symbolData.intervals).map(([interval, scores]) => {
                    const predictions = calculatePredictions(scores);
                    return (
                      <tr key={interval} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3 font-semibold">{interval}</td>
                        <td className="px-4 py-3">{scores.price.toFixed(2)}</td>
                        <td className="px-4 py-3"><ScoreBadge score={scores.rsi_score} /></td>
                        <td className="px-4 py-3"><ScoreBadge score={scores.macd_score} /></td>
                        <td className="px-4 py-3"><ScoreBadge score={scores.adx_score} /></td>
                        <td className="px-4 py-3"><ScoreBadge score={scores.supertrend_score} /></td>
                        <td className="px-4 py-3"><ScoreBadge score={scores.avg_score} /></td>
                        <td className="px-4 py-3 text-sm text-gray-300">{predictions.open}</td>
                        <td className="px-4 py-3 text-sm text-green-400">{predictions.high}</td>
                        <td className="px-4 py-3 text-sm text-red-400">{predictions.low}</td>
                        <td className="px-4 py-3 text-sm text-blue-400">{predictions.close}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

const calculatePredictions = (scores) => {
  // Simple prediction based on current price and avg score
  const price = scores.price;
  const avgScore = scores.avg_score;
  
  // Estimate movement based on score (simplified)
  const movement = ((avgScore - 50) / 50) * (price * 0.02); // 2% max movement
  
  return {
    open: (price + movement * 0.5).toFixed(2),
    high: (price + Math.abs(movement)).toFixed(2),
    low: (price - Math.abs(movement)).toFixed(2),
    close: (price + movement).toFixed(2)
  };
};

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

export default Dashboard;