import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Brush } from 'recharts';

const toIST = (timestamp) => {
  return new Date(timestamp); // Backend already sends IST
};

const AroonMultiTimeframeChart = ({ data, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  const chartData = data['1m']?.map((candle, idx) => ({
    time: formatDateTime(candle.Datetime || candle.Date, data['1m'], idx),
    timestamp: toIST(candle.Datetime || candle.Date).getTime(),
    aroon_1m: parseFloat(candle.aroon_1m_cross),
    aroon_5m: parseFloat(candle.aroon_5m_cross),
    aroon_1h: parseFloat(candle.aroon_1h_cross),
    aroon_avg: parseFloat(candle.aroon_avg_cross),
    aroon_sma9: parseFloat(candle.aroon_sma9_cross)
  })).filter(i => 
       !isNaN(i.aroon_1m) || 
       !isNaN(i.aroon_5m) || 
       !isNaN(i.aroon_1h) || 
       !isNaN(i.aroon_avg) || 
       !isNaN(i.aroon_sma9)) || [];
       
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
        <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" />
        <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" />
        <Line type="monotone" dataKey="aroon_1m" stroke="#3b82f6" name="1m Aroon" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="aroon_5m" stroke="#10b981" name="5m Aroon" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="aroon_1h" stroke="#f59e0b" name="1h Aroon" dot={false} strokeWidth={2} connectNulls />
        <Line type="monotone" dataKey="aroon_avg" stroke="#9b59b6" name="Avg Aroon" dot={false} strokeWidth={3} connectNulls />
        <Line type="monotone" dataKey="aroon_sma9" stroke="#ef4444" name="SMA9" dot={false} strokeWidth={2} strokeDasharray="5 5" connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default AroonMultiTimeframeChart;
