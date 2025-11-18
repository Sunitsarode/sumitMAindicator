import React, { useState, useEffect } from 'react';

const Dashboard = ({ onSymbolClick }) => {
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
        {lastUpdate && (
          <div className="text-sm text-gray-400">
            Last Update: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>

      {dashboardData.length === 0 ? (
        <div className="text-gray-400">No data available. Backend is starting up...</div>
      ) : (
        dashboardData.map((symbolData) => (
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