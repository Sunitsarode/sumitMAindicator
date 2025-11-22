// API Configuration
// Auto-detect: use same host as frontend, or fallback to localhost for dev

const API_HOST = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000' 
  : `http://${window.location.hostname}:5000`;

export const API_BASE_URL = API_HOST;

// API Endpoints
export const API = {
  dashboard: `${API_BASE_URL}/api/dashboard`,
  symbol: (symbol) => `${API_BASE_URL}/api/symbol/${symbol}`,
  tradesLoad: (symbol) => `${API_BASE_URL}/api/trades/load/${symbol}`,
  tradesSave: `${API_BASE_URL}/api/trades/save`,
  tradesClear: (symbol) => `${API_BASE_URL}/api/trades/clear/${symbol}`,
  tradesReport: (symbol) => `${API_BASE_URL}/api/trades/report/${symbol}`,
};

export default API;
