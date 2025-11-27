// CHART COMPONENTS - Part 2 of Charts.jsx

const toIST = (timestamp) => {
  const date = new Date(timestamp);
  return new Date(date.getTime() + (5.5 * 60 * 60 * 1000));
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
