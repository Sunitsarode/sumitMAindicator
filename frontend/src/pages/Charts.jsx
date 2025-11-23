import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart, Bar, ReferenceArea, Brush } from 'recharts';
import { API } from '../config';

const Charts = ({ symbol }) => {
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedInterval, setSelectedInterval] = useState('1m');
  const intervals = ['1m', '5m', '1h'];

  const fetchSymbolData = async () => {
    if (!symbol) return;
    try {
      setLoading(true); setError(null);
      const response = await fetch(API.symbol(symbol));
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data || Object.keys(data).length === 0) throw new Error('No data available');
      setSymbolData(data); setLastUpdate(new Date()); setLoading(false);
    } catch (error) { setError(error.message); setLoading(false); }
  };

  useEffect(() => { fetchSymbolData(); }, [symbol]);

  const formatDateTime = (timestamp, data, idx) => {
    const date = new Date(timestamp);
    const dateStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
    const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    const prevDate = idx > 0 ? new Date(data[idx - 1].timestamp) : null;
    return idx === 0 || (prevDate && date.toDateString() !== prevDate.toDateString()) ? `${dateStr} : ${timeStr}` : timeStr;
  };

  if (!symbol) return <div className="text-center text-gray-400">Please select a symbol from the dashboard</div>;
  if (loading) return <div className="flex items-center justify-center h-64"><div className="text-xl">Loading {symbol} charts...</div></div>;
  if (error) return (
    <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
      {error}<button onClick={fetchSymbolData} className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm">Retry</button>
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between bg-gray-800 p-4 rounded-lg">
        <div>
          <h2 className="text-2xl font-bold mb-2">{symbol} - Charts</h2>
          <div className="flex gap-2">
            <span className="text-gray-400 text-sm mr-2">Timeframe:</span>
            {intervals.map(interval => (
              <button key={interval} onClick={() => setSelectedInterval(interval)}
                className={`px-4 py-2 rounded-lg transition font-semibold ${selectedInterval === interval ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>{interval}</button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && <div className="text-sm text-gray-400">{lastUpdate.toLocaleTimeString()}</div>}
          <button onClick={fetchSymbolData} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-semibold">🔄 Refresh</button>
        </div>
      </div>

      <ChartContainer title="Chart 1: Individual Indicator Scores">
        <ImprovedChart data={symbolData} interval={selectedInterval} formatDateTime={formatDateTime}
          lines={[{ key: 'rsi_score', name: 'RSI', color: '#8884d8' }, { key: 'macd_score', name: 'MACD', color: '#82ca9d' }, { key: 'adx_score', name: 'ADX', color: '#ffc658' }, { key: 'supertrend_score', name: 'Supertrend', color: '#ff7c7c' }]} />
      </ChartContainer>

      <ChartContainer title="Chart 2: Weighted Average with SMA Crossover">
        <ImprovedChart data={symbolData} interval={selectedInterval} formatDateTime={formatDateTime}
          lines={[{ key: 'weighted_avg_score', name: 'Weighted Avg', color: '#8884d8' }, { key: 'weighted_sma9', name: 'SMA9', color: '#82ca9d' }, { key: 'weighted_sma21', name: 'SMA21', color: '#ffc658' }]} />
      </ChartContainer>

      <ChartContainer title="Chart 3: Sumit MA - Multi-Timeframe Scores">
        <div className="mb-4 p-4 bg-gray-750 rounded-lg">
          <div className="grid grid-cols-4 gap-3 text-sm">
            <div><span className="font-semibold text-blue-400">Blue (1m):</span> 1-minute Sumit MA score</div>
            <div><span className="font-semibold text-green-400">Green (5m):</span> 5-minute Sumit MA score</div>
            <div><span className="font-semibold text-orange-400">Orange (1h):</span> 1-hour Sumit MA score</div>
            <div><span className="font-semibold text-purple-400">Purple (Cross):</span> Average of all 3 timeframes</div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-700">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-green-400">📈 LONG: Score &gt; 70</div>
              <div className="text-yellow-400">➡️ NEUTRAL: Score 40-60</div>
              <div className="text-red-400">📉 SHORT: Score &lt; 30</div>
            </div>
          </div>
        </div>
        <MultiTimeframeSumitChart data={symbolData} formatDateTime={formatDateTime} showTradingZones={true} />
      </ChartContainer>

      <ChartContainer title="Chart 4: Price Chart (OHLC)">
        <CandlestickChart data={symbolData} interval={selectedInterval} formatDateTime={formatDateTime} />
      </ChartContainer>

      <ChartContainer title="Chart 5: Cross-Timeframe Sumit MA with SMA Crossover">
        <CrossTimeframeChart data={symbolData} formatDateTime={formatDateTime} />
      </ChartContainer>
    </div>
  );
};

const ChartContainer = ({ title, children }) => (<div className="bg-gray-800 rounded-lg p-6"><h3 className="text-lg font-semibold mb-4">{title}</h3>{children}</div>);

const ImprovedChart = ({ data, interval, lines, showTradingZones = false, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const cleanedData = { time: formatDateTime(timestamp, data[interval], idx), timestamp: new Date(timestamp).getTime(), index: idx };
    lines.forEach(line => { const v = candle[line.key]; if (v != null && !isNaN(v)) cleanedData[line.key] = parseFloat(v); });
    return cleanedData;
  }).filter(item => lines.some(line => item[line.key] !== undefined)) || [];
  const startIdx = brushRange.startIndex || 0, endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={visibleData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} stroke="#9ca3af" />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} formatter={(v) => v.toFixed(2)} />
        <Legend />
        <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" data={chartData} startIndex={startIdx} endIndex={endIdx} onChange={(r) => { if (r) setBrushRange({ startIndex: r.startIndex, endIndex: r.endIndex }); }} />
        {showTradingZones && <><ReferenceArea y1={0} y2={30} fill="#ef4444" fillOpacity={0.1} /><ReferenceArea y1={70} y2={100} fill="#10b981" fillOpacity={0.1} /></>}
        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" />
        {lines.map(line => <Line key={line.key} type="monotone" dataKey={line.key} stroke={line.color} name={line.name} dot={false} strokeWidth={2} connectNulls={true} />)}
      </LineChart>
    </ResponsiveContainer>
  );
};

const MultiTimeframeSumitChart = ({ data, formatDateTime, showTradingZones = false }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  // Get 1m data as base (has most frequent updates)
  const chartData = data['1m']?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    const cleanedData = {
      time: formatDateTime(timestamp, data['1m'], idx),
      timestamp: date.getTime(),
      index: idx,
    };
    
    // 1m sumit_ma_score
    if (candle.sumit_ma_score != null && !isNaN(candle.sumit_ma_score)) {
      cleanedData.sumit_1m = parseFloat(candle.sumit_ma_score);
    }
    
    // cross_avg_score (average of 1m+5m+1h)
    if (candle.cross_avg_score != null && !isNaN(candle.cross_avg_score)) {
      cleanedData.cross_avg = parseFloat(candle.cross_avg_score);
    }
    
    return cleanedData;
  }).filter(item => item.sumit_1m !== undefined || item.cross_avg !== undefined) || [];
  
  // Merge 5m and 1h data by finding closest timestamps
  if (data['5m'] && data['5m'].length > 0) {
    data['5m'].forEach(candle5m => {
      const ts5m = new Date(candle5m.Datetime || candle5m.Date).getTime();
      // Find closest 1m candle
      const closest = chartData.reduce((prev, curr) => 
        Math.abs(curr.timestamp - ts5m) < Math.abs(prev.timestamp - ts5m) ? curr : prev
      );
      if (candle5m.sumit_ma_score != null && !isNaN(candle5m.sumit_ma_score)) {
        closest.sumit_5m = parseFloat(candle5m.sumit_ma_score);
      }
    });
  }
  
  if (data['1h'] && data['1h'].length > 0) {
    data['1h'].forEach(candle1h => {
      const ts1h = new Date(candle1h.Datetime || candle1h.Date).getTime();
      const closest = chartData.reduce((prev, curr) => 
        Math.abs(curr.timestamp - ts1h) < Math.abs(prev.timestamp - ts1h) ? curr : prev
      );
      if (candle1h.sumit_ma_score != null && !isNaN(candle1h.sumit_ma_score)) {
        closest.sumit_1h = parseFloat(candle1h.sumit_ma_score);
      }
    });
  }
  
  // Forward fill missing values
  let last5m = null, last1h = null;
  chartData.forEach(item => {
    if (item.sumit_5m !== undefined) last5m = item.sumit_5m;
    else if (last5m !== null) item.sumit_5m = last5m;
    
    if (item.sumit_1h !== undefined) last1h = item.sumit_1h;
    else if (last1h !== null) item.sumit_1h = last1h;
  });

  const startIdx = brushRange.startIndex || 0;
  const endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={visibleData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} stroke="#9ca3af" />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} formatter={(v) => v?.toFixed(2) || 'N/A'} />
        <Legend />
        <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" data={chartData} startIndex={startIdx} endIndex={endIdx}
          onChange={(r) => { if (r) setBrushRange({ startIndex: r.startIndex, endIndex: r.endIndex }); }} />
        {showTradingZones && (
          <>
            <ReferenceArea y1={0} y2={30} fill="#ef4444" fillOpacity={0.1} />
            <ReferenceArea y1={70} y2={100} fill="#10b981" fillOpacity={0.1} />
          </>
        )}
        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" />
        
        <Line type="monotone" dataKey="sumit_1m" stroke="#3b82f6" name="1m Sumit MA" dot={false} strokeWidth={2} connectNulls={true} />
        <Line type="monotone" dataKey="sumit_5m" stroke="#10b981" name="5m Sumit MA" dot={false} strokeWidth={2} connectNulls={true} />
        <Line type="monotone" dataKey="sumit_1h" stroke="#f59e0b" name="1h Sumit MA" dot={false} strokeWidth={2} connectNulls={true} />
        <Line type="monotone" dataKey="cross_avg" stroke="#9b59b6" name="Cross Avg (1m+5m+1h)" dot={false} strokeWidth={3} connectNulls={true} />
      </LineChart>
    </ResponsiveContainer>
  );
};

const CandlestickChart = ({ data, interval, formatDateTime }) => {
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    return {
      time: formatDateTime(timestamp, data[interval], idx),
      Open: parseFloat(candle.Open) || 0, Close: parseFloat(candle.Close) || 0,
      High: parseFloat(candle.High) || 0, Low: parseFloat(candle.Low) || 0,
      color: parseFloat(candle.Close) >= parseFloat(candle.Open) ? '#10b981' : '#ef4444'
    };
  }) || [];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis stroke="#9ca3af" domain={['auto', 'auto']} />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
          content={({ active, payload }) => active && payload?.[0] ? (
            <div className="bg-gray-800 border border-gray-600 p-3 rounded">
              <p className="text-gray-300">{payload[0].payload.time}</p>
              <p className="text-green-400">O: {payload[0].payload.Open?.toFixed(2)}</p>
              <p className="text-blue-400">H: {payload[0].payload.High?.toFixed(2)}</p>
              <p className="text-orange-400">L: {payload[0].payload.Low?.toFixed(2)}</p>
              <p className="text-red-400">C: {payload[0].payload.Close?.toFixed(2)}</p>
            </div>
          ) : null} />
        <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" />
        <Bar dataKey="High" fill="#10b981" />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

const CrossTimeframeChart = ({ data, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  const chartData = data['1m']?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date;
    const d = { time: formatDateTime(timestamp, data['1m'], idx), index: idx };
    if (candle.cross_avg_score != null) d.cross_avg = parseFloat(candle.cross_avg_score);
    if (candle.cross_sma9 != null) d.cross_sma9 = parseFloat(candle.cross_sma9);
    if (candle.cross_sma21 != null) d.cross_sma21 = parseFloat(candle.cross_sma21);
    return d;
  }).filter(item => item.cross_avg !== undefined) || [];
  const startIdx = brushRange.startIndex || 0, endIdx = brushRange.endIndex || chartData.length;

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData.slice(startIdx, endIdx)}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} stroke="#9ca3af" />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} formatter={(v) => v.toFixed(2)} />
        <Legend />
        <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" data={chartData} startIndex={startIdx} endIndex={endIdx} onChange={(r) => { if (r) setBrushRange({ startIndex: r.startIndex, endIndex: r.endIndex }); }} />
        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" />
        <Line type="monotone" dataKey="cross_avg" stroke="#9b59b6" name="Cross Avg" dot={false} strokeWidth={2} connectNulls={true} />
        <Line type="monotone" dataKey="cross_sma9" stroke="#10b981" name="SMA9" dot={false} strokeWidth={2} connectNulls={true} />
        <Line type="monotone" dataKey="cross_sma21" stroke="#f59e0b" name="SMA21" dot={false} strokeWidth={2} connectNulls={true} />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default Charts;
