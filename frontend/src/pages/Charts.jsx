import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart, Bar, ReferenceArea, Brush } from 'recharts';
import { API } from '../config';
import SumitMASignalsChart from './SumitMASignalsChart';
import AroonMultiTimeframeChart from './Aroon_Chart';

// Helper to convert UTC to IST
const toIST = (timestamp) => {
  return new Date(timestamp); // Backend already sends IST
};

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
    const date = toIST(timestamp);
    const dateStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
    const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    const prevDate = idx > 0 ? toIST(data[idx - 1].timestamp) : null;
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
          <h2 className="text-2xl font-bold mb-2">{symbol} - Charts (IST)</h2>
          <div className="flex gap-2">
            <span className="text-gray-400 text-sm mr-2">Timeframe:</span>
            {intervals.map(interval => (
              <button key={interval} onClick={() => setSelectedInterval(interval)}
                className={`px-4 py-2 rounded-lg transition font-semibold ${selectedInterval === interval ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>{interval}</button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && <div className="text-sm text-gray-400">{toIST(lastUpdate).toLocaleTimeString('en-IN')}</div>}
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

      <ChartContainer title="Chart 4: Price Chart with Moving Averages">
        <CandlestickWithMAsChart data={symbolData} interval={selectedInterval} formatDateTime={formatDateTime} />
      </ChartContainer>

      <ChartContainer title="Chart 5: Cross-Timeframe Sumit MA with SMA Crossover">
        <CrossTimeframeChart data={symbolData} formatDateTime={formatDateTime} />
      </ChartContainer>

      <ChartContainer title="Chart 6: Sumit MA Signals (BUY/SELL Count) with Moving Averages">
        <SumitMASignalsChart data={symbolData} interval={selectedInterval} formatDateTime={formatDateTime} />
      </ChartContainer>

      <ChartContainer title="Chart 7: Aroon Indicator - Multi-Timeframe Analysis">
        <AroonMultiTimeframeChart data={symbolData} formatDateTime={formatDateTime} />
      </ChartContainer>
    </div>
  );
};

const ChartContainer = ({ title, children }) => (<div className="bg-gray-800 rounded-lg p-6"><h3 className="text-lg font-semibold mb-4">{title}</h3>{children}</div>);

const ImprovedChart = ({ data, interval, lines, showTradingZones = false, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  const chartData = data[interval]
    ?.filter(candle => candle.Datetime || candle.Date || candle.index)
    .map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const cleanedData = { time: formatDateTime(timestamp, data[interval], idx), timestamp: toIST(timestamp).getTime(), index: idx };
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
  
  const chartData = data['1m']?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = toIST(timestamp);
    const cleanedData = {
      time: formatDateTime(timestamp, data['1m'], idx),
      timestamp: date.getTime(),
      index: idx,
    };
    
    if (candle.sumit_ma_score != null && !isNaN(candle.sumit_ma_score)) {
      cleanedData.sumit_1m = parseFloat(candle.sumit_ma_score);
    }
    
    if (candle.cross_avg_score != null && !isNaN(candle.cross_avg_score)) {
      cleanedData.cross_avg = parseFloat(candle.cross_avg_score);
    }
    
    return cleanedData;
  }).filter(item => item.sumit_1m !== undefined || item.cross_avg !== undefined) || [];
  
  if (data['5m'] && data['5m'].length > 0) {
    data['5m'].forEach(candle5m => {
      const ts5m = toIST(candle5m.Datetime || candle5m.Date).getTime();
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
      const ts1h = toIST(candle1h.Datetime || candle1h.Date).getTime();
      const closest = chartData.reduce((prev, curr) => 
        Math.abs(curr.timestamp - ts1h) < Math.abs(prev.timestamp - ts1h) ? curr : prev
      );
      if (candle1h.sumit_ma_score != null && !isNaN(candle1h.sumit_ma_score)) {
        closest.sumit_1h = parseFloat(candle1h.sumit_ma_score);
      }
    });
  }
  
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
        <Line type="monotone" dataKey="cross_avg" stroke="#9b59b6" name="Cross Avg" dot={false} strokeWidth={3} connectNulls={true} />
      </LineChart>
    </ResponsiveContainer>
  );
};

const CandlestickWithMAsChart = ({ data, interval, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  // Calculate moving averages
  const calculateMA = (data, period) => {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((acc, val) => acc + val, 0);
        result.push(sum / period);
      }
    }
    return result;
  };

  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    return {
      time: formatDateTime(timestamp, data[interval], idx),
      timestamp: toIST(timestamp).getTime(),
      Open: parseFloat(candle.Open) || 0,
      High: parseFloat(candle.High) || 0,
      Low: parseFloat(candle.Low) || 0,
      Close: parseFloat(candle.Close) || 0,
    };
  }) || [];

  // Calculate MAs
  const closes = chartData.map(d => d.Close);
  const ma9 = calculateMA(closes, 9);
  const ma21 = calculateMA(closes, 21);
  const ma51 = calculateMA(closes, 51);
  const ma101 = calculateMA(closes, 101);

  // Add MAs to chart data
  chartData.forEach((item, idx) => {
    item.MA9 = ma9[idx];
    item.MA21 = ma21[idx];
    item.MA51 = ma51[idx];
    item.MA101 = ma101[idx];
  });

  const startIdx = brushRange.startIndex || 0;
  const endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <div className="space-y-2">
      <div className="bg-gray-750 rounded p-2 text-xs flex gap-4">
        <span className="flex items-center gap-1"><div className="w-3 h-3 bg-blue-500 rounded"></div>MA9</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 bg-green-500 rounded"></div>MA21</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 bg-yellow-500 rounded"></div>MA51</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 bg-purple-500 rounded"></div>MA101</span>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={visibleData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
          <YAxis stroke="#9ca3af" domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const data = payload[0].payload;
              return (
                <div className="bg-gray-800 border border-gray-600 p-3 rounded">
                  <p className="text-gray-300">{data.time}</p>
                  <p className="text-green-400">O: {data.Open?.toFixed(2)}</p>
                  <p className="text-blue-400">H: {data.High?.toFixed(2)}</p>
                  <p className="text-orange-400">L: {data.Low?.toFixed(2)}</p>
                  <p className="text-red-400">C: {data.Close?.toFixed(2)}</p>
                  {data.MA9 && <p className="text-blue-300">MA9: {data.MA9.toFixed(2)}</p>}
                  {data.MA21 && <p className="text-green-300">MA21: {data.MA21.toFixed(2)}</p>}
                </div>
              );
            }} />
          <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" data={chartData} 
            startIndex={startIdx} endIndex={endIdx}
            onChange={(r) => { if (r) setBrushRange({ startIndex: r.startIndex, endIndex: r.endIndex }); }} />
          <Legend />
          <Line type="monotone" dataKey="MA9" stroke="#3b82f6" strokeWidth={1.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="MA21" stroke="#10b981" strokeWidth={1.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="MA51" stroke="#fbbf24" strokeWidth={1.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="MA101" stroke="#a855f7" strokeWidth={1.5} dot={false} connectNulls />
          <Bar dataKey="High" fill="transparent" shape={<CustomCandlestick />} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

const CustomCandlestick = (props) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;
  
  const { Open, Close, High, Low } = payload;
  const isBullish = Close >= Open;
  const color = isBullish ? '#10b981' : '#ef4444';
  const bodyHeight = Math.abs(Close - Open);
  const bodyY = Math.min(Open, Close);
  
  return (
    <g>
      <line x1={x + width / 2} y1={y} x2={x + width / 2} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={x} y={bodyY} width={width} height={bodyHeight || 1} fill={color} stroke={color} />
    </g>
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
  }).filter(item => item.cross_avg !== undefined || item.cross_sma9 !== undefined || item.cross_sma21 !== undefined) || [];
  const startIdx = brushRange.startIndex || 0, endIdx = brushRange.endIndex || chartData.length;

  if (chartData.length === 0) {
    return <div className="text-center py-8 text-gray-500">No cross-timeframe data available. Data will appear after all timeframes have collected sufficient candles.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData.slice(startIdx, endIdx)}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} stroke="#9ca3af" />
        <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} formatter={(v) => v?.toFixed(2) || 'N/A'} />
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

// Export all components
export { MultiTimeframeSumitChart, CandlestickWithMAsChart, CustomCandlestick, CrossTimeframeChart, toIST };
export default Charts;
