import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Brush } from 'recharts';

const toIST = (timestamp) => {
  const date = new Date(timestamp);
  return new Date(date.getTime() + (5.5 * 60 * 60 * 1000));
};

const SumitMASignalsChart = ({ data, interval, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  // Calculate MA3 and MA9 for buy_signal_count
  const calculateMA = (values, period) => {
    const result = [];
    for (let i = 0; i < values.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        const sum = values.slice(i - period + 1, i + 1).reduce((acc, val) => acc + val, 0);
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
      index: idx,
      buySignals: parseInt(candle.buy_signal_count) || 0,
      sellSignals: parseInt(candle.sell_signal_count) || 0,
      price: parseFloat(candle.Close) || 0,
    };
  }).filter(item => item.buySignals !== undefined || item.sellSignals !== undefined) || [];

  // Calculate MA3 and MA9 for buy signals
  const buyValues = chartData.map(d => d.buySignals);
  const ma3Buy = calculateMA(buyValues, 3);
  const ma9Buy = calculateMA(buyValues, 9);

  // Add MAs to chartData
  chartData.forEach((item, idx) => {
    item.MA3_Buy = ma3Buy[idx];
    item.MA9_Buy = ma9Buy[idx];
  });

  const startIdx = brushRange.startIndex || 0;
  const endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <div className="space-y-4">
      <div className="bg-gray-750 rounded-lg p-4">
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-semibold text-green-400">🟢 BUY Signals (0-18):</span>
            <p className="text-xs text-gray-400 mt-1">Count of MAs below price. Higher = stronger uptrend.</p>
            <p className="text-xs text-green-300 mt-1">
              • &gt;15 = Very Strong Buy<br/>
              • 12-15 = Strong Buy<br/>
              • 9-12 = Moderate Buy
            </p>
          </div>
          <div>
            <span className="font-semibold text-red-400">🔴 SELL Signals (0-18):</span>
            <p className="text-xs text-gray-400 mt-1">Count of MAs above price. Higher = stronger downtrend.</p>
            <p className="text-xs text-red-300 mt-1">
              • &gt;15 = Very Strong Sell<br/>
              • 12-15 = Strong Sell<br/>
              • 9-12 = Moderate Sell
            </p>
          </div>
          <div>
            <span className="font-semibold text-blue-400">📊 Moving Averages:</span>
            <p className="text-xs text-gray-400 mt-1">MA3 and MA9 smooth the BUY signal line for trend clarity.</p>
            <p className="text-xs text-blue-300 mt-1">
              Uses 18 OHLC/4 Moving Averages (MA 3 to MA 301)
            </p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={visibleData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9ca3af" 
            angle={-45} 
            textAnchor="end" 
            height={80} 
            tick={{ fontSize: 11 }} 
          />
          <YAxis 
            domain={[0, 18]} 
            stroke="#9ca3af"
            label={{ value: 'Signal Count', angle: -90, position: 'insideLeft' }}
            ticks={[0, 3, 6, 9, 12, 15, 18]}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
            formatter={(value, name) => {
              if (name === 'MA3_Buy' || name === 'MA9_Buy') {
                return [`${value?.toFixed(1) || 'N/A'}/18`, name];
              }
              return [`${value}/18`, name];
            }}
          />
          <Legend />
          <Brush 
            dataKey="time" 
            height={30} 
            stroke="#3b82f6" 
            fill="#1f2937" 
            data={chartData}
            startIndex={startIdx}
            endIndex={endIdx}
            onChange={(r) => { 
              if (r) setBrushRange({ startIndex: r.startIndex, endIndex: r.endIndex }); 
            }}
          />
          
          {/* Reference lines for signal strength zones */}
          <ReferenceLine y={15} stroke="#10b981" strokeDasharray="3 3" label={{ value: "Very Strong", position: "right" }} />
          <ReferenceLine y={12} stroke="#84cc16" strokeDasharray="3 3" label={{ value: "Strong", position: "right" }} />
          <ReferenceLine y={9} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: "Moderate", position: "right" }} />
          
          {/* BUY signals as green line */}
          <Line 
            type="monotone"
            dataKey="buySignals" 
            stroke="#10b981" 
            name="BUY Signals"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          
          {/* MA3 of BUY signals */}
          <Line 
            type="monotone"
            dataKey="MA3_Buy" 
            stroke="#3b82f6" 
            name="MA3 (BUY)"
            strokeWidth={2}
            dot={false}
            strokeDasharray="5 5"
            connectNulls
          />
          
          {/* MA9 of BUY signals */}
          <Line 
            type="monotone"
            dataKey="MA9_Buy" 
            stroke="#a855f7" 
            name="MA9 (BUY)"
            strokeWidth={2}
            dot={false}
            strokeDasharray="5 5"
            connectNulls
          />
          
          {/* SELL signals as red line */}
          <Line 
            type="monotone"
            dataKey="sellSignals" 
            stroke="#ef4444" 
            name="SELL Signals"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Latest Signal Summary */}
      {visibleData.length > 0 && (
        <div className="bg-gray-750 rounded-lg p-4">
          <h4 className="font-semibold mb-3">Latest Signal Status</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-900/30 border border-green-600 rounded-lg p-3">
              <div className="text-xs text-gray-400">BUY Signals</div>
              <div className="text-2xl font-bold text-green-400">
                {visibleData[visibleData.length - 1].buySignals}/18
              </div>
              <div className="text-xs text-green-300 mt-1">
                {visibleData[visibleData.length - 1].buySignals >= 15 ? 'Very Strong Buy' :
                 visibleData[visibleData.length - 1].buySignals >= 12 ? 'Strong Buy' :
                 visibleData[visibleData.length - 1].buySignals >= 9 ? 'Moderate Buy' : 'Weak'}
              </div>
              <div className="text-xs text-blue-300 mt-2">
                MA3: {visibleData[visibleData.length - 1].MA3_Buy?.toFixed(1) || 'N/A'} | 
                MA9: {visibleData[visibleData.length - 1].MA9_Buy?.toFixed(1) || 'N/A'}
              </div>
            </div>
            <div className="bg-red-900/30 border border-red-600 rounded-lg p-3">
              <div className="text-xs text-gray-400">SELL Signals</div>
              <div className="text-2xl font-bold text-red-400">
                {visibleData[visibleData.length - 1].sellSignals}/18
              </div>
              <div className="text-xs text-red-300 mt-1">
                {visibleData[visibleData.length - 1].sellSignals >= 15 ? 'Very Strong Sell' :
                 visibleData[visibleData.length - 1].sellSignals >= 12 ? 'Strong Sell' :
                 visibleData[visibleData.length - 1].sellSignals >= 9 ? 'Moderate Sell' : 'Weak'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SumitMASignalsChart;
