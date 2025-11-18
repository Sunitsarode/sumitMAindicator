import React, { useState } from 'react';
import Dashboard from './Dashboard';
import SymbolCharts from './SymbolCharts';

const App = () => {
  const [view, setView] = useState('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState(null);

  const handleSymbolClick = (symbol) => {
    setSelectedSymbol(symbol);
    setView('symbol');
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setSelectedSymbol(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
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
      </header>

      <main className="p-6">
        {view === 'dashboard' ? (
          <Dashboard onSymbolClick={handleSymbolClick} />
        ) : (
          <SymbolCharts symbol={selectedSymbol} onBack={handleBackToDashboard} />
        )}
      </main>
    </div>
  );
};

export default App;