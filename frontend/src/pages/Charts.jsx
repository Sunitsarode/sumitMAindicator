import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart, Bar, ReferenceArea, Brush } from 'recharts';

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
      setLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:5000/api/symbol/${symbol}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      if (!data || Object.keys(data).length === 0) {
        throw new Error('No data available for this symbol yet.');
      }
      
      setSymbolData(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching symbol data:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSymbolData();
  }, [symbol]);

  // Format datetime like Chart 6
  const formatDateTime = (timestamp, data, idx) => {
    const date = new Date(timestamp);
    const dateStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
    
    const prevDate = idx > 0 ? new Date(data[idx - 1].timestamp) : null;
    const showDate = idx === 0 || (prevDate && date.toDateString() !== prevDate.toDateString());
    return showDate ? `${dateStr} : ${timeStr}` : timeStr;
  };

  if (!symbol) {
    return (
      <div className="text-center text-gray-400">
        Please select a symbol from the dashboard
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Loading {symbol} charts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
        {error}
        <button 
          onClick={fetchSymbolData} 
          className="ml-4 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Control Bar */}
      <div className="flex items-center justify-between bg-gray-800 p-4 rounded-lg">
        <div>
          <h2 className="text-2xl font-bold mb-2">{symbol} - Charts</h2>
          <div className="flex gap-2">
            <span className="text-gray-400 text-sm mr-2">Timeframe:</span>
            {intervals.map(interval => (
              <button 
                key={interval} 
                onClick={() => setSelectedInterval(interval)}
                className={`px-4 py-2 rounded-lg transition font-semibold ${
                  selectedInterval === interval 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {interval}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <div className="text-sm text-gray-400">
              {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button 
            onClick={fetchSymbolData}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-semibold"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Charts */}
      <ChartContainer title="Chart 1: Individual Indicator Scores">
        <ImprovedChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
          lines={[
            { key: 'rsi_score', name: 'RSI', color: '#8884d8' },
            { key: 'macd_score', name: 'MACD', color: '#82ca9d' },
            { key: 'adx_score', name: 'ADX', color: '#ffc658' },
            { key: 'supertrend_score', name: 'Supertrend', color: '#ff7c7c' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 2: Composite Scores">
        <ImprovedChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#82ca9d' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 3: Average Score with SMA Crossover">
        <ImprovedChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'avg_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'avg_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 4: Weighted Average with SMA Crossover">
        <ImprovedChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
          lines={[
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#8884d8' },
            { key: 'weighted_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'weighted_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 5: Sumit MA - Price Position Strength (NEW LOGIC)">
        <div className="mb-4 p-4 bg-gray-750 rounded-lg">
          <h4 className="font-semibold mb-2">📊 How to Read This Chart:</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="font-semibold text-blue-400">Blue Line (Short):</span> Position vs MA 3,9,15,21
            </div>
            <div>
              <span className="font-semibold text-green-400">Green Line (Mid):</span> Position vs MA 27,51,81,101
            </div>
            <div>
              <span className="font-semibold text-orange-400">Orange Line (Long):</span> Position vs MA 151,201
            </div>
            <div>
              <span className="font-semibold text-purple-400">Purple Line (Overall):</span> Average of all 10 MAs
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-700">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-green-400">📈 LONG: Score &gt; 70</div>
              <div className="text-yellow-400">➡️ NEUTRAL: Score 40-60</div>
              <div className="text-red-400">📉 SHORT: Score &lt; 30</div>
            </div>
          </div>
        </div>
        <ImprovedChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
          lines={[
            { key: 'sumit_ratio1_score', name: 'Short-term (MA 3-21)', color: '#3b82f6' },
            { key: 'sumit_ratio2_score', name: 'Mid-term (MA 27-101)', color: '#10b981' },
            { key: 'sumit_ratio3_score', name: 'Long-term (MA 151-201)', color: '#f59e0b' },
            { key: 'sumit_ma_score', name: 'Overall (All 10 MAs)', color: '#9b59b6' }
          ]}
          showTradingZones={true}
        />
      </ChartContainer>

      <ChartContainer title="Chart 6: Price Chart (OHLC)">
        <CandlestickChart 
          data={symbolData} 
          interval={selectedInterval}
          formatDateTime={formatDateTime}
        />
      </ChartContainer>
    </div>
  );
};

const ChartContainer = ({ title, children }) => (
  <div className="bg-gray-800 rounded-lg p-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    {children}
  </div>
);

const ImprovedChart = ({ data, interval, lines, showTradingZones = false, formatDateTime }) => {
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    
    const cleanedData = {
      time: formatDateTime(timestamp, data[interval], idx),
      timestamp: date.getTime(),
      index: idx,
    };
    
    lines.forEach(line => {
      const value = candle[line.key];
      if (value !== null && value !== undefined && !isNaN(value)) {
        cleanedData[line.key] = parseFloat(value);
      }
    });
    
    return cleanedData;
  }).filter(item => lines.some(line => item[line.key] !== undefined)) || [];

  const startIdx = brushRange.startIndex || 0;
  const endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <div>
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
          <YAxis domain={[0, 100]} stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151' 
            }}
            labelFormatter={(value) => `Time: ${value}`}
            formatter={(value) => value.toFixed(2)}
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
            onChange={(range) => {
              if (range && range.startIndex !== undefined && range.endIndex !== undefined) {
                setBrushRange({ 
                  startIndex: range.startIndex, 
                  endIndex: range.endIndex 
                });
              }
            }}
          />
          
          {showTradingZones && (
            <>
              <ReferenceArea y1={0} y2={30} fill="#ef4444" fillOpacity={0.1} label={{ value: "STRONG SHORT", position: "insideTopLeft", fill: "#ef4444" }} />
              <ReferenceArea y1={70} y2={100} fill="#10b981" fillOpacity={0.1} label={{ value: "STRONG LONG", position: "insideTopLeft", fill: "#10b981" }} />
              <ReferenceArea y1={40} y2={60} fill="#fbbf24" fillOpacity={0.05} label={{ value: "NEUTRAL", position: "center", fill: "#fbbf24" }} />
            </>
          )}
          
          <ReferenceLine y={70} stroke="#10b981" strokeDasharray="3 3" label="Long Zone" />
          <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" label="Neutral" />
          <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="3 3" label="Short Zone" />
          
          {lines.map(line => (
            <Line 
              key={line.key} 
              type="monotone" 
              dataKey={line.key} 
              stroke={line.color} 
              name={line.name} 
              dot={false} 
              strokeWidth={2}
              connectNulls={true}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const CandlestickChart = ({ data, interval, formatDateTime }) => {
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    
    const open = parseFloat(candle.Open) || 0;
    const close = parseFloat(candle.Close) || 0;
    const high = parseFloat(candle.High) || 0;
    const low = parseFloat(candle.Low) || 0;
    
    return {
      time: formatDateTime(timestamp, data[interval], idx),
      Open: open,
      Close: close,
      High: high,
      Low: low,
      color: close >= open ? '#10b981' : '#ef4444'
    };
  }) || [];

  const CustomCandlestick = (props) => {
    const { x, y, width, height, payload } = props;
    if (!payload || !payload.High) return null;
    
    const wickX = x + width / 2;
    const bodyWidth = Math.max(width * 0.6, 1);
    const bodyX = x + (width - bodyWidth) / 2;
    
    const scale = height / (Math.max(...chartData.map(d => d.High)) - Math.min(...chartData.map(d => d.Low)));
    const yMin = y + height;
    
    const highY = yMin - (payload.High - Math.min(...chartData.map(d => d.Low))) * scale;
    const lowY = yMin - (payload.Low - Math.min(...chartData.map(d => d.Low))) * scale;
    const openY = yMin - (payload.Open - Math.min(...chartData.map(d => d.Low))) * scale;
    const closeY = yMin - (payload.Close - Math.min(...chartData.map(d => d.Low))) * scale;
    
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.abs(openY - closeY) || 1;
    
    return (
      <g>
        <line x1={wickX} y1={highY} x2={wickX} y2={bodyTop} stroke={payload.color} strokeWidth={1} />
        <line x1={wickX} y1={bodyTop + bodyHeight} x2={wickX} y2={lowY} stroke={payload.color} strokeWidth={1} />
        <rect x={bodyX} y={bodyTop} width={bodyWidth} height={bodyHeight} fill={payload.color} stroke={payload.color} />
      </g>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
        <YAxis stroke="#9ca3af" domain={['auto', 'auto']} />
        <Tooltip 
          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
          content={({ active, payload }) => {
            if (active && payload && payload[0]) {
              const data = payload[0].payload;
              return (
                <div className="bg-gray-800 border border-gray-600 p-3 rounded">
                  <p className="text-gray-300">{data.time}</p>
                  <p className="text-green-400">O: {data.Open?.toFixed(2)}</p>
                  <p className="text-blue-400">H: {data.High?.toFixed(2)}</p>
                  <p className="text-orange-400">L: {data.Low?.toFixed(2)}</p>
                  <p className="text-red-400">C: {data.Close?.toFixed(2)}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Brush dataKey="time" height={30} stroke="#3b82f6" fill="#1f2937" />
        <Bar dataKey="High" shape={<CustomCandlestick />} />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default Charts;