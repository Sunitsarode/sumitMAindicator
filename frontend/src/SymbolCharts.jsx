import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart, Bar } from 'recharts';

const SymbolCharts = ({ symbol, onBack }) => {
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSymbolData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:5000/api/symbol/${symbol}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      
      // Check if data is empty or has error
      if (!data || Object.keys(data).length === 0) {
        throw new Error('No data available for this symbol yet. Please wait for data to load.');
      }
      
      // Check if intervals have data
      const hasData = Object.values(data).some(interval => interval && interval.length > 0);
      if (!hasData) {
        throw new Error('Symbol data is still loading. Please wait a moment and try again.');
      }
      
      setSymbolData(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching symbol data:', error);
      setError(error.message || `Failed to load data for ${symbol}`);
      setLoading(false);
      setSymbolData(null);
    }
  };

  useEffect(() => {
    fetchSymbolData();
    const interval = setInterval(fetchSymbolData, 60000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Loading {symbol} data...</div>
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

  if (!symbolData) {
    return <div>No data available</div>;
  }

  const intervals = ['1m', '5m', '1h'];
  
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">{symbol} Analysis</h2>
        {lastUpdate && (
          <div className="text-sm text-gray-400">
            Last Update: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>

      <ChartContainer title="Chart 1: Individual Indicator Scores">
        <MultiIntervalChart 
          data={symbolData} 
          intervals={intervals} 
          lines={[
            { key: 'rsi_score', name: 'RSI', color: '#8884d8' },
            { key: 'macd_score', name: 'MACD', color: '#82ca9d' },
            { key: 'adx_score', name: 'ADX', color: '#ffc658' },
            { key: 'supertrend_score', name: 'Supertrend', color: '#ff7c7c' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 2: Composite Scores">
        <MultiIntervalChart 
          data={symbolData} 
          intervals={intervals} 
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#82ca9d' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 3: Average Score with SMA Crossover">
        <MultiIntervalChart 
          data={symbolData} 
          intervals={intervals} 
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'avg_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'avg_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 4: Weighted Average with SMA Crossover">
        <MultiIntervalChart 
          data={symbolData} 
          intervals={intervals} 
          lines={[
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#8884d8' },
            { key: 'weighted_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'weighted_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 5: Sumit MA Indicator">
        <MultiIntervalChart 
          data={symbolData} 
          intervals={intervals} 
          lines={[
            { key: 'sumit_ma_score', name: 'Sumit MA', color: '#9b59b6' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 6: Price Chart (OHLC)">
        <CandlestickChart data={symbolData} intervals={intervals} />
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

const MultiIntervalChart = ({ data, intervals, lines }) => {
  const [selectedInterval, setSelectedInterval] = useState(intervals[0]);
  
  const chartData = data[selectedInterval]?.slice(-100).map((candle) => {
    // Parse timestamp from candle data
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
    
    // Create cleaned data object with parsed numbers
    const cleanedData = {
      time: timeStr,
      timestamp: date.getTime(),
    };
    
    // Parse all line data values
    lines.forEach(line => {
      const value = candle[line.key];
      // Only include if value exists and is not null
      if (value !== null && value !== undefined && !isNaN(value)) {
        cleanedData[line.key] = parseFloat(value);
      }
    });
    
    return cleanedData;
  }).filter(item => {
    // Filter out items where ALL line values are missing
    return lines.some(line => item[line.key] !== undefined);
  }) || [];
  
  // Debug log for Sumit MA
  if (lines.some(line => line.key === 'sumit_ma_score')) {
    console.log('Sumit MA Chart Data Sample:', chartData.slice(0, 5));
    console.log('Total data points:', chartData.length);
    console.log('Valid Sumit MA points:', chartData.filter(d => d.sumit_ma_score !== undefined).length);
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {intervals.map(interval => (
          <button 
            key={interval} 
            onClick={() => setSelectedInterval(interval)}
            className={`px-4 py-2 rounded-lg transition ${
              selectedInterval === interval 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {interval}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9ca3af"
            angle={-45}
            textAnchor="end"
            height={80}
            interval="preserveStartEnd"
          />
          <YAxis domain={[0, 100]} stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151' 
            }}
            labelFormatter={(value) => `Time: ${value}`}
          />
          <Legend />
          
          <ReferenceLine 
            y={80} 
            stroke="#ef4444" 
            strokeDasharray="3 3" 
            label="Overbought" 
          />
          <ReferenceLine 
            y={50} 
            stroke="#6b7280" 
            strokeDasharray="3 3" 
            label="Neutral" 
          />
          <ReferenceLine 
            y={20} 
            stroke="#10b981" 
            strokeDasharray="3 3" 
            label="Oversold" 
          />
          
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

const CandlestickChart = ({ data, intervals }) => {
  const [selectedInterval, setSelectedInterval] = useState(intervals[0]);
  
  const chartData = data[selectedInterval]?.slice(-50).map((candle) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
    
    const open = parseFloat(candle.Open) || 0;
    const close = parseFloat(candle.Close) || 0;
    const high = parseFloat(candle.High) || 0;
    const low = parseFloat(candle.Low) || 0;
    
    const isGreen = close >= open;
    
    return {
      time: timeStr,
      timestamp: date.getTime(),
      Open: open,
      Close: close,
      High: high,
      Low: low,
      // For candlestick body
      bodyLow: Math.min(open, close),
      bodyHigh: Math.max(open, close),
      // Wick ranges
      upperWick: [Math.max(open, close), high],
      lowerWick: [low, Math.min(open, close)],
      color: isGreen ? '#10b981' : '#ef4444',
      isGreen: isGreen
    };
  }) || [];

  const CustomCandlestick = (props) => {
    const { x, y, width, height, payload } = props;
    if (!payload || !payload.High) return null;
    
    const wickX = x + width / 2;
    const bodyWidth = Math.max(width * 0.6, 1);
    const bodyX = x + (width - bodyWidth) / 2;
    
    // Calculate positions
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
        {/* Upper wick */}
        <line 
          x1={wickX} 
          y1={highY} 
          x2={wickX} 
          y2={bodyTop} 
          stroke={payload.color} 
          strokeWidth={1}
        />
        {/* Lower wick */}
        <line 
          x1={wickX} 
          y1={bodyTop + bodyHeight} 
          x2={wickX} 
          y2={lowY} 
          stroke={payload.color} 
          strokeWidth={1}
        />
        {/* Body */}
        <rect 
          x={bodyX} 
          y={bodyTop} 
          width={bodyWidth} 
          height={bodyHeight}
          fill={payload.color}
          stroke={payload.color}
        />
      </g>
    );
  };

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {intervals.map(interval => (
          <button 
            key={interval} 
            onClick={() => setSelectedInterval(interval)}
            className={`px-4 py-2 rounded-lg transition ${
              selectedInterval === interval 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {interval}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9ca3af"
            angle={-45}
            textAnchor="end"
            height={80}
            interval="preserveStartEnd"
          />
          <YAxis 
            stroke="#9ca3af" 
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151' 
            }}
            formatter={(value, name) => {
              if (typeof value === 'number') {
                return [`${value.toFixed(2)}`, name];
              }
              return [value, name];
            }}
            labelFormatter={(value) => `Time: ${value}`}
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload;
                return (
                  <div className="bg-gray-800 border border-gray-600 p-3 rounded">
                    <p className="text-gray-300">{data.time}</p>
                    <p className="text-green-400">O: ${data.Open?.toFixed(2)}</p>
                    <p className="text-blue-400">H: ${data.High?.toFixed(2)}</p>
                    <p className="text-orange-400">L: ${data.Low?.toFixed(2)}</p>
                    <p className="text-red-400">C: ${data.Close?.toFixed(2)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar 
            dataKey="High" 
            shape={<CustomCandlestick />}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SymbolCharts;