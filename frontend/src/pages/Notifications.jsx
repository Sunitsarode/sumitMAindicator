import React, { useState, useEffect } from 'react';
import { API } from '../config';

const Notifications = ({ symbol }) => {
  const [trades, setTrades] = useState([]);
  const [openPositions, setOpenPositions] = useState([]);
  const [symbolData, setSymbolData] = useState(null);
  const [totalPL, setTotalPL] = useState(0);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [config, setConfig] = useState({ MAX_OPEN_POSITIONS: 3 });

  const loadData = async () => {
    if (!symbol) return;
    try {
      const res = await fetch(API.tradesLoad(symbol));
      if (res.ok) {
        const data = await res.json();
        if (data) {
          setTrades(data.trades || []);
          setOpenPositions(data.openPositions || []);
          setTotalPL(data.totalPL || 0);
        }
      }
    } catch (err) { console.error('Load error:', err); }
  };

  const fetchPrice = async () => {
    if (!symbol) return;
    try {
      const res = await fetch(API.symbol(symbol));
      if (res.ok) {
        const data = await res.json();
        setSymbolData(data);
        if (data['1m']?.length > 0) {
          setCurrentPrice(parseFloat(data['1m'][data['1m'].length - 1].Close));
        }
      }
    } catch (err) { console.error('Price fetch error:', err); }
  };

  useEffect(() => {
    loadData(); fetchPrice();
    const interval = setInterval(() => { loadData(); fetchPrice(); }, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  const exportReport = () => {
    const report = { symbol, totalPL, totalTrades: trades.length, winRate: trades.length > 0 ? (trades.filter(t => t.pl > 0).length / trades.length * 100).toFixed(1) : 0, openPositions, trades, generatedAt: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `trade_report_${symbol}_${Date.now()}.json`; a.click();
  };

  const clearData = async () => {
    if (!symbol || !confirm('Clear all trade data?')) return;
    try { await fetch(API.tradesClear(symbol), { method: 'DELETE' }); setTrades([]); setOpenPositions([]); setTotalPL(0); } catch (err) { console.error('Clear error:', err); }
  };

  const formatTime = (ts) => new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  
  const getReasonBadge = (reason) => {
    const colors = { SL: 'bg-red-600', PROFIT: 'bg-green-600', REVERSAL: 'bg-yellow-600', CROSS_REVERSAL: 'bg-orange-600', MANUAL: 'bg-blue-600' };
    return <span className={`${colors[reason] || 'bg-gray-500'} px-2 py-1 rounded text-xs font-semibold`}>{reason}</span>;
  };

  const calcUnrealizedPL = (pos) => !currentPrice ? 0 : pos.direction === 'LONG' ? currentPrice - pos.entryPrice : pos.entryPrice - currentPrice;

  // Format indicator criteria for display
  const formatEntryCriteria = (trade) => {
    const ec = trade.entryCriteria;
    if (!ec) return <span className="text-gray-500 text-xs">N/A</span>;
    
    return (
      <div className="text-xs space-y-1">
        <div className="flex gap-1 flex-wrap">
          <span className="bg-purple-700 px-1 rounded">RSI:{ec.rsi?.toFixed(0) || '-'}</span>
          <span className="bg-blue-700 px-1 rounded">MACD:{ec.macd?.toFixed(0) || '-'}</span>
        </div>
        <div className="flex gap-1 flex-wrap">
          <span className="bg-yellow-700 px-1 rounded">ADX:{ec.adx?.toFixed(0) || '-'}</span>
          <span className="bg-pink-700 px-1 rounded">ST:{ec.supertrend?.toFixed(0) || '-'}</span>
        </div>
        <div className="flex gap-1 flex-wrap">
          <span className="bg-green-700 px-1 rounded">SMA:{ec.sumit_ma?.toFixed(0) || '-'}</span>
          {ec.cross_sma9 && <span className="bg-cyan-700 px-1 rounded">C9:{ec.cross_sma9?.toFixed(0)}</span>}
          {ec.cross_sma21 && <span className="bg-orange-700 px-1 rounded">C21:{ec.cross_sma21?.toFixed(0)}</span>}
        </div>
        {ec.cross_avg && <div><span className="bg-indigo-700 px-1 rounded">CrossAvg:{ec.cross_avg?.toFixed(1)}</span></div>}
      </div>
    );
  };

  const formatExitCriteria = (trade) => {
    const ec = trade.exitCriteria;
    if (!ec) return <span className="text-gray-500 text-xs">N/A</span>;
    
    return (
      <div className="text-xs space-y-1">
        <div className="flex gap-1 flex-wrap">
          <span className="bg-purple-700 px-1 rounded">RSI:{ec.rsi?.toFixed(0) || '-'}</span>
          <span className="bg-blue-700 px-1 rounded">MACD:{ec.macd?.toFixed(0) || '-'}</span>
        </div>
        <div className="flex gap-1 flex-wrap">
          <span className="bg-yellow-700 px-1 rounded">ADX:{ec.adx?.toFixed(0) || '-'}</span>
          <span className="bg-pink-700 px-1 rounded">ST:{ec.supertrend?.toFixed(0) || '-'}</span>
        </div>
        <div className="flex gap-1 flex-wrap">
          <span className="bg-green-700 px-1 rounded">SMA:{ec.sumit_ma?.toFixed(0) || '-'}</span>
          {ec.cross_sma9 && <span className="bg-cyan-700 px-1 rounded">C9:{ec.cross_sma9?.toFixed(0)}</span>}
          {ec.cross_sma21 && <span className="bg-orange-700 px-1 rounded">C21:{ec.cross_sma21?.toFixed(0)}</span>}
        </div>
        {ec.cross_avg && <div><span className="bg-indigo-700 px-1 rounded">CrossAvg:{ec.cross_avg?.toFixed(1)}</span></div>}
        {trade.reason === 'SL' && <div className="text-red-400">SL Hit @ {trade.exitPrice?.toFixed(2)}</div>}
        {trade.reason === 'PROFIT' && <div className="text-green-400">Target Hit</div>}
      </div>
    );
  };

  const totalUnrealizedPL = openPositions.reduce((sum, pos) => sum + calcUnrealizedPL(pos), 0);
  const winCount = trades.filter(t => t.pl > 0).length;
  const lossCount = trades.filter(t => t.pl <= 0).length;
  const winRate = trades.length > 0 ? (winCount / trades.length * 100).toFixed(1) : 0;

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">📊 Auto Trader - {symbol || 'Select Symbol'}</h2>
            <p className="text-sm text-green-400 mt-1">🤖 Backend auto-trading active</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={loadData} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold">🔄 Refresh</button>
            <button onClick={exportReport} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold">📥 Export</button>
            <button onClick={clearData} className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg font-semibold">🗑️ Clear</button>
          </div>
        </div>
        <div className="grid grid-cols-5 gap-4">
          <div className={`p-4 rounded-lg ${totalPL >= 0 ? 'bg-green-900/50' : 'bg-red-900/50'}`}>
            <div className="text-xs text-gray-400">Realized P/L</div>
            <div className={`text-2xl font-bold ${totalPL >= 0 ? 'text-green-400' : 'text-red-400'}`}>{totalPL >= 0 ? '+' : ''}{totalPL.toFixed(2)}</div>
          </div>
          <div className={`p-4 rounded-lg ${totalUnrealizedPL >= 0 ? 'bg-blue-900/50' : 'bg-orange-900/50'}`}>
            <div className="text-xs text-gray-400">Unrealized P/L</div>
            <div className={`text-2xl font-bold ${totalUnrealizedPL >= 0 ? 'text-blue-400' : 'text-orange-400'}`}>{totalUnrealizedPL >= 0 ? '+' : ''}{totalUnrealizedPL.toFixed(2)}</div>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="text-xs text-gray-400">Win Rate</div>
            <div className="text-2xl font-bold text-blue-400">{winRate}%</div>
            <div className="text-xs text-gray-500">{winCount}W / {lossCount}L</div>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="text-xs text-gray-400">Open Positions</div>
            <div className="text-2xl font-bold text-yellow-400">{openPositions.length} / {config.MAX_OPEN_POSITIONS}</div>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="text-xs text-gray-400">Current Price</div>
            <div className="text-2xl font-bold text-white">{currentPrice.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-bold mb-4">🔵 Open Positions ({openPositions.length}/{config.MAX_OPEN_POSITIONS})</h3>
        {openPositions.length === 0 ? (
          <div className="text-center py-6 text-gray-500 border-2 border-dashed border-gray-600 rounded-lg">No open positions.</div>
        ) : (
          <div className="grid gap-3">
            {openPositions.map((pos, idx) => {
              const upl = calcUnrealizedPL(pos);
              return (
                <div key={pos.id} className={`p-4 rounded-lg border-2 ${pos.direction === 'LONG' ? 'bg-green-900/20 border-green-600' : 'bg-red-900/20 border-red-600'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-xl">{pos.direction === 'LONG' ? '🟢' : '🔴'}</span>
                      <span className={`px-3 py-1 rounded font-bold ${pos.direction === 'LONG' ? 'bg-green-600' : 'bg-red-600'}`}>{pos.direction}</span>
                      <span className="text-xs text-gray-400">[{pos.signalType || 'INDICATOR'}]</span>
                    </div>
                    <div className={`text-xl font-bold ${upl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{upl >= 0 ? '+' : ''}{upl.toFixed(2)} pts</div>
                  </div>
                  <div className="grid grid-cols-6 gap-4 mt-3 text-sm">
                    <div><span className="text-gray-400">Entry:</span> <span className="font-mono">{pos.entryPrice?.toFixed(2)}</span></div>
                    <div><span className="text-gray-400">Current:</span> <span className="font-mono text-yellow-400">{currentPrice.toFixed(2)}</span></div>
                    <div><span className="text-gray-400">SL:</span> <span className="font-mono text-red-400">{pos.stopLoss?.toFixed(2)}</span></div>
                    <div><span className="text-gray-400">Signal:</span> {pos.strength}</div>
                    <div><span className="text-gray-400">Time:</span> {formatTime(pos.entryTime)}</div>
                    <div>
                      {pos.entryCriteria && (
                        <div className="text-xs">
                          <span className="text-gray-400">Entry: </span>
                          <span className="bg-purple-700 px-1 rounded mr-1">R:{pos.entryCriteria.rsi?.toFixed(0)}</span>
                          <span className="bg-green-700 px-1 rounded">S:{pos.entryCriteria.sumit_ma?.toFixed(0)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Trade History Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-bold">📋 Trade History ({trades.length})</h3>
          <p className="text-xs text-gray-400 mt-1">RSI | MACD | ADX | ST (Supertrend) | SMA (Sumit MA) | C9/C21 (Cross SMA9/21) | CrossAvg</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-3 py-3 text-left text-sm">Exit Time</th>
                <th className="px-3 py-3 text-left text-sm">Signal</th>
                <th className="px-3 py-3 text-right text-sm">Entry</th>
                <th className="px-3 py-3 text-right text-sm">Exit</th>
                <th className="px-3 py-3 text-right text-sm">P/L</th>
                <th className="px-3 py-3 text-center text-sm">Entry Criteria</th>
                <th className="px-3 py-3 text-center text-sm">Exit Criteria</th>
                <th className="px-3 py-3 text-center text-sm">Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr><td colSpan="8" className="px-4 py-8 text-center text-gray-500">No trades yet.</td></tr>
              ) : trades.slice(0, 100).map((t, i) => (
                <tr key={t.id} className={`border-t border-gray-700 ${i % 2 === 0 ? 'bg-gray-800' : 'bg-gray-750'}`}>
                  <td className="px-3 py-3 text-sm whitespace-nowrap">{formatTime(t.timestamp)}</td>
                  <td className="px-3 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${t.direction === 'LONG' ? 'bg-green-600' : 'bg-red-600'}`}>{t.direction}</span>
                    <div className="text-xs text-gray-400 mt-1">[{t.signalType || 'IND'}]</div>
                  </td>
                  <td className="px-3 py-3 text-right font-mono text-sm">{t.entryPrice?.toFixed(2)}</td>
                  <td className="px-3 py-3 text-right font-mono text-sm">{t.exitPrice?.toFixed(2)}</td>
                  <td className={`px-3 py-3 text-right font-bold ${t.pl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {t.pl >= 0 ? '+' : ''}{t.pl?.toFixed(2)}
                  </td>
                  <td className="px-3 py-3">{formatEntryCriteria(t)}</td>
                  <td className="px-3 py-3">{formatExitCriteria(t)}</td>
                  <td className="px-3 py-3 text-center">{getReasonBadge(t.reason)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Notifications;
