import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 15000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token automatically if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('meddemand_token') || sessionStorage.getItem('meddemand_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle session expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.includes('/api/auth/login')) {
      // Clear token and notify listeners
      localStorage.removeItem('meddemand_token');
      sessionStorage.removeItem('meddemand_token');
      localStorage.removeItem('meddemand_shop');
      sessionStorage.removeItem('meddemand_shop');
      window.dispatchEvent(new Event('meddemand_logout'));
    }
    return Promise.reject(error);
  }
);

/* =========================================================================
   Authentication & Profile Endpoints
   ========================================================================= */

export const registerShop = async (shopData) => {
  try {
    const res = await api.post('/api/auth/register', shopData);
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Registration failed. Please try again.',
    };
  }
};

export const loginShop = async (email, password, rememberMe = false) => {
  try {
    const res = await api.post('/api/auth/login', {
      email,
      password,
      remember_me: rememberMe,
    });
    const { access_token, shop } = res.data;
    if (rememberMe) {
      localStorage.setItem('meddemand_token', access_token);
      localStorage.setItem('meddemand_shop', JSON.stringify(shop));
      sessionStorage.removeItem('meddemand_token');
      sessionStorage.removeItem('meddemand_shop');
    } else {
      sessionStorage.setItem('meddemand_token', access_token);
      sessionStorage.setItem('meddemand_shop', JSON.stringify(shop));
      localStorage.removeItem('meddemand_token');
      localStorage.removeItem('meddemand_shop');
    }
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.',
    };
  }
};

export const logoutShop = async () => {
  try {
    await api.post('/api/auth/logout');
  } catch (err) {
    // Ignore error on logout cleanup
  } finally {
    localStorage.removeItem('meddemand_token');
    sessionStorage.removeItem('meddemand_token');
    localStorage.removeItem('meddemand_shop');
    sessionStorage.removeItem('meddemand_shop');
    window.dispatchEvent(new Event('meddemand_logout'));
  }
  return { ok: true };
};

export const getCurrentShopProfile = async () => {
  try {
    const res = await api.get('/api/auth/me');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Unable to fetch shop profile.',
    };
  }
};

export const updateShopProfile = async (profileData) => {
  try {
    const res = await api.put('/api/auth/profile', profileData);
    // Update cached shop data
    const updated = res.data;
    if (localStorage.getItem('meddemand_token')) {
      localStorage.setItem('meddemand_shop', JSON.stringify(updated));
    } else if (sessionStorage.getItem('meddemand_token')) {
      sessionStorage.setItem('meddemand_shop', JSON.stringify(updated));
    }
    return { ok: true, data: updated };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to update profile.',
    };
  }
};

export const requestPasswordReset = async (email) => {
  try {
    const res = await api.post('/api/auth/forgot-password', { email });
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Password reset request failed.',
    };
  }
};

export const resetPassword = async (token, newPassword, confirmPassword) => {
  try {
    const res = await api.post('/api/auth/reset-password', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Password reset failed.',
    };
  }
};

/* =========================================================================
   Medicine Catalog & Inventory Endpoints (Multi-Shop)
   ========================================================================= */

export const getMedicines = async () => {
  try {
    const res = await api.get('/api/medicines');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to fetch medicines catalog',
    };
  }
};

export const getShopMedicineItems = async () => {
  try {
    const res = await api.get('/api/medicines/items');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to fetch medicine inventory items',
    };
  }
};

export const createMedicine = async (medicineData) => {
  try {
    const res = await api.post('/api/medicines', medicineData);
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to add medicine to inventory',
    };
  }
};

export const seedStarterMedicines = async () => {
  try {
    const res = await api.post('/api/medicines/seed-starter');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to load starter catalog',
    };
  }
};

export const updateMedicineStock = async (medicineIdentifier, stockPayload) => {
  try {
    const res = await api.post(`/api/inventory/${encodeURIComponent(medicineIdentifier)}`, stockPayload);
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to update medicine stock',
    };
  }
};

/* =========================================================================
   Forecasting & Analytics Endpoints (Multi-Shop)
   ========================================================================= */

export const getDemandForecast = async (medicine, days = 7) => {
  try {
    const res = await api.post('/api/forecast', { medicine, days: Number(days) });
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Forecast generation failed',
    };
  }
};

export const getForecastHistory = async (limit = 15) => {
  try {
    const res = await api.get(`/api/forecasts/history?limit=${limit}`);
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to load forecast history',
    };
  }
};

export const analyzeInventory = async (medicine, days = 7, currentStock = null) => {
  try {
    const payload = {
      medicine,
      days: Number(days),
    };
    if (currentStock !== null && currentStock !== '' && !isNaN(currentStock)) {
      payload.current_stock = Number(currentStock);
    }
    const res = await api.post('/api/inventory-analysis', payload);
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Inventory analysis failed',
    };
  }
};

export const getModelMetrics = async () => {
  try {
    const res = await api.get('/api/model-metrics');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to load model metrics',
    };
  }
};

export const getAnalyticsSummary = async () => {
  try {
    const res = await api.get('/api/analytics/summary');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Failed to load dashboard analytics',
    };
  }
};

export const checkBackendHealth = async () => {
  try {
    const res = await api.get('/api/health');
    return { ok: true, data: res.data };
  } catch (err) {
    return {
      ok: false,
      error: err.response?.data?.detail || err.message || 'Unable to connect to backend',
    };
  }
};

export default api;
