const API_BASE = '/api';
const API_KEY = 'dev-key';  // Match SMARTMART_API_KEY env var on backend

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function postJSON(url, data, { auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) headers['X-API-Key'] = API_KEY;
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJSON(`${API_BASE}/dashboard/summary`),

  // Inventory
  getInventory: (page = 1, limit = 50, search = '', category = '') => {
    let url = `${API_BASE}/inventory?page=${page}&limit=${limit}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    return fetchJSON(url);
  },
  getAllInventory: () => fetchJSON(`${API_BASE}/inventory/all`),
  getLowStock: () => fetchJSON(`${API_BASE}/inventory/low-stock`),
  getInventoryByCategory: () => fetchJSON(`${API_BASE}/inventory/by-category`),
  getExpiringSoon: () => fetchJSON(`${API_BASE}/inventory/expiring-soon`),
  getCategories: () => fetchJSON(`${API_BASE}/inventory/categories`),
  addProduct: (data) => postJSON(`${API_BASE}/inventory`, data),
  restockProduct: (productId, quantity = 50) => postJSON(`${API_BASE}/inventory/restock/${productId}?quantity=${quantity}`),

  // Sales
  getSales: (limit = 100) => fetchJSON(`${API_BASE}/sales?limit=${limit}`),
  getRevenue: () => fetchJSON(`${API_BASE}/sales/revenue`),
  getBestSellers: () => fetchJSON(`${API_BASE}/sales/best-sellers`),
  getSalesByCategory: () => fetchJSON(`${API_BASE}/sales/by-category`),
  getHourlyHeatmap: () => fetchJSON(`${API_BASE}/sales/hourly-heatmap`),
  getPaymentBreakdown: () => fetchJSON(`${API_BASE}/sales/payment-breakdown`),
  getProfitMargins: () => fetchJSON(`${API_BASE}/sales/profit-margins`),

  // Customers
  getCustomers: (page = 1, limit = 50, search = '', tier = '') => {
    let url = `${API_BASE}/customers?page=${page}&limit=${limit}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (tier) url += `&tier=${encodeURIComponent(tier)}`;
    return fetchJSON(url);
  },
  exportCustomersCSV: () => `${API_BASE}/customers/export`,
  getSegments: () => fetchJSON(`${API_BASE}/customers/segments`),
  getAllSegmented: () => fetchJSON(`${API_BASE}/customers/segments/all`),
  getTopCustomers: () => fetchJSON(`${API_BASE}/customers/top`),
  getDemographics: () => fetchJSON(`${API_BASE}/customers/demographics`),
  getRetention: () => fetchJSON(`${API_BASE}/customers/retention`),
  addCustomer: (data) => postJSON(`${API_BASE}/customers`, data),

  // Suppliers
  getSuppliers: () => fetchJSON(`${API_BASE}/suppliers`),
  getSupplierPerformance: () => fetchJSON(`${API_BASE}/suppliers/performance`),
  getSupplierDetail: (id) => fetchJSON(`${API_BASE}/suppliers/${id}`),

  // ML
  getForecasts: () => fetchJSON(`${API_BASE}/forecast`),
  getCategoryForecast: (cat) => fetchJSON(`${API_BASE}/forecast/${cat}`),
  getRecommendations: () => fetchJSON(`${API_BASE}/recommendations`),
  getAnomalies: () => fetchJSON(`${API_BASE}/anomalies`),
  getPricing: () => fetchJSON(`${API_BASE}/pricing`),
  retrainModels: () => postJSON(`${API_BASE}/ml/retrain`, {}, { auth: true }),

  // Upload / Data Management
  getUploadStatus: () => fetchJSON(`${API_BASE}/upload/status`),
  previewUpload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload/preview`, { method: 'POST', body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  importData: async (uploadId, fileType, mapping) => {
    const formData = new FormData();
    formData.append('upload_id', uploadId);
    formData.append('file_type', fileType);
    formData.append('mapping_json', JSON.stringify(mapping));
    const res = await fetch(`${API_BASE}/upload/import`, { method: 'POST', body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Import failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  resetData: async () => {
    const res = await fetch(`${API_BASE}/upload/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Reset failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  loadDemoData: async () => {
    const res = await fetch(`${API_BASE}/upload/load-demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Load demo failed: HTTP ${res.status}`);
    }
    return res.json();
  },

  // Chatbot
  sendChat: (message, sessionId) => postJSON(`${API_BASE}/chat`, { message, session_id: sessionId }),
};
