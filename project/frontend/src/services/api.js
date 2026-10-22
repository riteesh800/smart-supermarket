const rawBase = (import.meta.env.VITE_API_BASE_URL || '/api').trim();
const API_BASE = rawBase.endsWith('/api') ? rawBase : (rawBase === '/api' || !rawBase ? '/api' : `${rawBase.replace(/\/$/, '')}/api`);
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-key';  // Match SMARTMART_API_KEY env var on backend

function getAuthHeaders(customToken) {
  const headers = {};
  const activeToken = customToken || localStorage.getItem('smartmart_token');
  if (activeToken) {
    headers['Authorization'] = `Bearer ${activeToken}`;
  } else {
    let guestId = localStorage.getItem('smartmart_guest_id');
    if (!guestId) {
      guestId = 'guest_' + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
      localStorage.setItem('smartmart_guest_id', guestId);
    }
    headers['Authorization'] = `Bearer ${guestId}`;
    headers['X-Guest-ID'] = guestId;
  }
  return headers;
}

async function fetchJSON(url, { token } = {}) {
  const headers = getAuthHeaders(token);
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function postJSON(url, data, { auth = false, token } = {}) {
  const headers = { 'Content-Type': 'application/json', ...getAuthHeaders(token) };
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
  restockProduct: (productId, quantity = 50) => postJSON(`${API_BASE}/inventory/restock/${productId}?quantity=${quantity}`, {}),

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
    const headers = getAuthHeaders();
    const res = await fetch(`${API_BASE}/upload/preview`, { method: 'POST', headers, body: formData });
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
    const headers = getAuthHeaders();
    const res = await fetch(`${API_BASE}/upload/import`, { method: 'POST', headers, body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Import failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  resetData: async () => {
    const headers = { 'Content-Type': 'application/json', 'X-API-Key': API_KEY, ...getAuthHeaders() };
    const res = await fetch(`${API_BASE}/upload/reset`, {
      method: 'POST',
      headers,
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Reset failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  loadDemoData: async () => {
    const headers = { 'Content-Type': 'application/json', 'X-API-Key': API_KEY, ...getAuthHeaders() };
    const res = await fetch(`${API_BASE}/upload/load-demo`, {
      method: 'POST',
      headers,
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Load demo failed: HTTP ${res.status}`);
    }
    return res.json();
  },
  getSampleDatasets: () => fetchJSON(`${API_BASE}/upload/sample-datasets`),
  getSampleDownloadUrl: (filename) => `${API_BASE}/upload/sample-datasets/${filename}/download`,

  // Chatbot
  sendChat: (message, sessionId) => postJSON(`${API_BASE}/chat`, { message, session_id: sessionId }),

  // Authentication & User State
  checkEmail: (email) => postJSON(`${API_BASE}/auth/check-email`, { email }),
  register: (name, email, password) => postJSON(`${API_BASE}/auth/register`, { name, email, password }),
  login: (email, password) => postJSON(`${API_BASE}/auth/login`, { email, password }),
  loginGoogle: (email, name, avatarUrl, idToken) =>
    postJSON(`${API_BASE}/auth/google`, { email, name, avatar_url: avatarUrl, id_token: idToken }),
  getGoogleConfigStatus: () => fetchJSON(`${API_BASE}/auth/google/config-status`),
  getGoogleAuthUrl: (prompt = 'select_account', dest = '/') =>
    fetchJSON(`${API_BASE}/auth/google/url?prompt=${encodeURIComponent(prompt)}&dest=${encodeURIComponent(dest)}`),
  initiateGoogleOAuth: (prompt = 'select_account', dest = '/') => {
    window.location.href = `${API_BASE}/auth/google?prompt=${encodeURIComponent(prompt)}&dest=${encodeURIComponent(dest)}`;
  },
  linkGoogleAccount: (ticket, password) =>
    postJSON(`${API_BASE}/auth/google/link`, { ticket, password }),
  getMe: (token) => fetchJSON(`${API_BASE}/auth/me`, { token }),
  saveUserState: (stateData, token) => postJSON(`${API_BASE}/auth/save-state`, { state_data: stateData }, { token }),
  logout: (token) => postJSON(`${API_BASE}/auth/logout`, {}, { token }),
};
