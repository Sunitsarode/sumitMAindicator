import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart, Bar, ReferenceArea, Brush } from 'recharts';

const Charts = ({ symbol }) => {
  const [symbolData, setSymbolData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedInterval, setSelectedInterval] = useState('1m');
  const [zoomLevel, setZoomLevel] = useState(1);
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

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
  const handleZoomReset = () => setZoomLevel(1);

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
          {/* Zoom Controls */}
          <div className="flex items-center gap-2 bg-gray-750 px-3 py-2 rounded-lg">
            <span className="text-sm text-gray-400">Zoom:</span>
            <button 
              onClick={handleZoomOut}
              className="px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-sm font-bold"
              title="Zoom Out"
            >
              −
            </button>
            <span className="text-sm font-mono w-12 text-center">{(zoomLevel * 100).toFixed(0)}%</span>
            <button 
              onClick={handleZoomIn}
              className="px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-sm font-bold"
              title="Zoom In"
            >
              +
            </button>
            <button 
              onClick={handleZoomReset}
              className="px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-sm"
              title="Reset Zoom"
            >
              ⟲
            </button>
          </div>

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
        <SyncedChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
          lines={[
            { key: 'rsi_score', name: 'RSI', color: '#8884d8' },
            { key: 'macd_score', name: 'MACD', color: '#82ca9d' },
            { key: 'adx_score', name: 'ADX', color: '#ffc658' },
            { key: 'supertrend_score', name: 'Supertrend', color: '#ff7c7c' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 2: Composite Scores">
        <SyncedChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#82ca9d' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 3: Average Score with SMA Crossover">
        <SyncedChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
          lines={[
            { key: 'avg_score', name: 'Average', color: '#8884d8' },
            { key: 'avg_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'avg_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 4: Weighted Average with SMA Crossover">
        <SyncedChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
          lines={[
            { key: 'weighted_avg_score', name: 'Weighted Avg', color: '#8884d8' },
            { key: 'weighted_sma9', name: 'SMA9', color: '#82ca9d' },
            { key: 'weighted_sma21', name: 'SMA21', color: '#ffc658' }
          ]} 
        />
      </ChartContainer>

      <ChartContainer title="Chart 5: Sumit MA Indicator (Trend Reversal Detection)">
        <SyncedChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
          lines={[
            { key: 'sumit_ratio1_score', name: 'Ratio1 (MA-1/MA-2)', color: '#3b82f6' },
            { key: 'sumit_ratio2_score', name: 'Ratio2 (MA-2/MA-3)', color: '#10b981' },
            { key: 'sumit_ratio3_score', name: 'Ratio3 (MA-3/MA-4)', color: '#f59e0b' },
            { key: 'sumit_ma_score', name: 'Average', color: '#9b59b6' }
          ]}
          showReversalZones={true}
        />
      </ChartContainer>

      <ChartContainer title="Chart 6: Price Chart (OHLC)">
        <SyncedCandlestickChart 
          data={symbolData} 
          interval={selectedInterval}
          zoomLevel={zoomLevel}
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

const SyncedChart = ({ data, interval, lines, showReversalZones = false, zoomLevel }) => {
  const [localZoom, setLocalZoom] = useState(1);
  const [brushRange, setBrushRange] = useState({ startIndex: 0, endIndex: undefined });
  
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    
    // Format: "11Oct-9:15am"
    const dateStr = date.toLocaleDateString('en-GB', { 
      day: '2-digit', 
      month: 'short' 
    }).replace(/ /g, '');
    
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    }).toLowerCase();
    
    const displayTime = `${dateStr}-${timeStr}`;
    
    const cleanedData = {
      time: displayTime,
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

  const handleLocalZoomIn = () => setLocalZoom(prev => Math.min(prev + 0.2, 3));
  const handleLocalZoomOut = () => setLocalZoom(prev => Math.max(prev - 0.2, 0.5));
  const handleLocalZoomReset = () => {
    setLocalZoom(1);
    setBrushRange({ startIndex: 0, endIndex: undefined });
  };

  const visibleDataCount = Math.max(20, Math.ceil(chartData.length / localZoom));
  const startIdx = brushRange.startIndex || Math.max(0, chartData.length - visibleDataCount);
  const endIdx = brushRange.endIndex || chartData.length;
  const visibleData = chartData.slice(startIdx, endIdx);

  return (
    <div>
      <div className="flex justify-end gap-2 mb-2">
        <button 
          onClick={handleLocalZoomOut}
          className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm font-bold"
          title="Zoom Out"
        >
          −
        </button>
        <span className="px-3 py-1 bg-gray-750 rounded text-sm font-mono">
          {(localZoom * 100).toFixed(0)}%
        </span>
        <button 
          onClick={handleLocalZoomIn}
          className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm font-bold"
          title="Zoom In"
        >
          +
        </button>
        <button 
          onClick={handleLocalZoomReset}
          className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
          title="Reset Zoom"
        >
          ⟲
        </button>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={visibleData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9ca3af"
            angle={-45}
            textAnchor="end"
            height={90}
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
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
          
          {showReversalZones && (
            <>
              <ReferenceArea y1={30} y2={50} fill="#ef4444" fillOpacity={0.1} label="Bearish Reversal" />
              <ReferenceArea y1={50} y2={70} fill="#10b981" fillOpacity={0.1} label="Bullish Reversal" />
            </>
          )}
          
          <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="3 3" label="Overbought" />
          <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="3 3" label="Neutral" />
          <ReferenceLine y={20} stroke="#10b981" strokeDasharray="3 3" label="Oversold" />
          
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

const SyncedCandlestickChart = ({ data, interval, zoomLevel }) => {
  const chartData = data[interval]?.map((candle, idx) => {
    const timestamp = candle.Datetime || candle.Date || candle.index;
    const date = new Date(timestamp);
    
    const dateStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
    const timeStr = date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
    
    const prevDate = idx > 0 ? new Date(data[interval][idx - 1].Datetime || data[interval][idx - 1].Date) : null;
    const showDate = idx === 0 || (prevDate && date.toDateString() !== prevDate.toDateString());
    const displayTime = showDate ? `${dateStr} : ${timeStr}` : timeStr;
    
    const open = parseFloat(candle.Open) || 0;
    const close = parseFloat(candle.Close) || 0;
    const high = parseFloat(candle.High) || 0;
    const low = parseFloat(candle.Low) || 0;
    
    return {
      time: displayTime,
      Open: open,
      Close: close,
      High: high,
      Low: low,
      color: close >= open ? '#10b981' : '#ef4444'
    };
  }) || [];

  const visibleDataCount = Math.ceil(chartData.length / zoomLevel);
  const startIndex = Math.max(0, chartData.length - visibleDataCount);
  const visibleData = chartData.slice(startIndex);

  const CustomCandlestick = (props) => {
    const { x, y, width, height, payload } = props;
    if (!payload || !payload.High) return null;
    
    const wickX = x + width / 2;
    const bodyWidth = Math.max(width * 0.6, 1);
    const bodyX = x + (width - bodyWidth) / 2;
    
    const scale = height / (Math.max(...visibleData.map(d => d.High)) - Math.min(...visibleData.map(d => d.Low)));
    const yMin = y + height;
    
    const highY = yMin - (payload.High - Math.min(...visibleData.map(d => d.Low))) * scale;
    const lowY = yMin - (payload.Low - Math.min(...visibleData.map(d => d.Low))) * scale;
    const openY = yMin - (payload.Open - Math.min(...visibleData.map(d => d.Low))) * scale;
    const closeY = yMin - (payload.Close - Math.min(...visibleData.map(d => d.Low))) * scale;
    
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
      <ComposedChart data={visibleData}>
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