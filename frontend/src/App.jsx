import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import LiveAnalysis from './pages/LiveAnalysis';
import Charts from './pages/Charts';

const App = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState(null);

  const handleSymbolSelect = (symbol) => {
    setSelectedSymbol(symbol);
    setCurrentPage('charts');
  };

  const handleLiveAnalysisSelect = (symbol) => {
    setSelectedSymbol(symbol);
    setCurrentPage('live');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation Bar */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Trading Dashboard</h1>
            
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`px-4 py-2 rounded-lg transition font-semibold ${
                  currentPage === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => setCurrentPage('live')}
                className={`px-4 py-2 rounded-lg transition font-semibold ${
                  currentPage === 'live'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                🔴 Live Analysis
              </button>
              <button
                onClick={() => setCurrentPage('charts')}
                className={`px-4 py-2 rounded-lg transition font-semibold ${
                  currentPage === 'charts'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                disabled={!selectedSymbol}
              >
                📈 Charts {selectedSymbol && `(${selectedSymbol})`}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="p-6">
        {currentPage === 'dashboard' && (
          <Dashboard 
            onSymbolClick={handleSymbolSelect}
            onLiveClick={handleLiveAnalysisSelect}
          />
        )}
        {currentPage === 'live' && (
          <LiveAnalysis symbol={selectedSymbol} />
        )}
        {currentPage === 'charts' && (
          <Charts symbol={selectedSymbol} />
        )}
      </main>
    </div>
  );
};

export default App;