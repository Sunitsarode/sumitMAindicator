import React from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import LiveAnalysis from './pages/LiveAnalysis';
import Charts from './pages/Charts';
import Notifications from './pages/Notifications';

// Debugging imports
console.log('Dashboard import:', Dashboard);
console.log('LiveAnalysis import:', LiveAnalysis);
console.log('Charts import:', Charts);
console.log('Notifications import:', Notifications);
const App = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation Bar */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Trading Dashboard</h1>
            
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 rounded-lg transition font-semibold bg-gray-700 text-gray-300 hover:bg-gray-600"
              >
                📊 Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Routes */}
      <main className="p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/:symbol/live" element={<LiveAnalysisWrapper />} />
          <Route path="/:symbol/charts" element={<ChartsWrapper />} />
          <Route path="/:symbol/trades" element={<NotificationsWrapper />} />
        </Routes>
      </main>
    </div>
  );
};
const LiveAnalysisWrapper = () => {
  const { symbol } = useParams();
  return <LiveAnalysis symbol={symbol} />;
};

const ChartsWrapper = () => {
  const { symbol } = useParams();
  return <Charts symbol={symbol} />;
};

const NotificationsWrapper = () => {
  const { symbol } = useParams();
  return <Notifications symbol={symbol} />;
};

export default App;
