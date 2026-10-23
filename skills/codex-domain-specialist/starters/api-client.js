// ============================================
// API CLIENT STARTER — Cookie Session + Idempotency-Key + SILC-001 Error Mapping
// In-Memory Access Token + HttpOnly Refresh Cookie (XSS-Safe)
// ============================================
import axios from 'axios';

const API_BASE = import.meta.env?.VITE_API_URL || '/api/v1';

let inMemoryAccessToken = null;

export const setAccessToken = (token) => {
  inMemoryAccessToken = token || null;
};

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  withCredentials: true, // Send HttpOnly refresh cookie automatically
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  if (inMemoryAccessToken) {
    config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
  }
  const method = String(config.method || 'get').toLowerCase();
  if (['post', 'put', 'patch', 'delete'].includes(method) && !config.headers['Idempotency-Key']) {
    config.headers['Idempotency-Key'] = crypto.randomUUID();
  }
  return config;
});

let refreshPromise = null;

client.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE}/auth/refresh`, {}, { withCredentials: true })
            .then((res) => {
              const nextToken = res.data?.data?.accessToken || null;
              setAccessToken(nextToken);
              return nextToken;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const nextToken = await refreshPromise;
        if (nextToken) {
          originalRequest.headers.Authorization = `Bearer ${nextToken}`;
          return client(originalRequest);
        }
      } catch (refreshError) {
        setAccessToken(null);
        return Promise.reject(normalizeApiError(refreshError));
      }
    }

    return Promise.reject(normalizeApiError(error));
  }
);

export function normalizeApiError(error) {
  const envelope = error?.response?.data?.error;
  if (envelope && typeof envelope === 'object') {
    const fieldMap = {};
    for (const item of envelope.fieldErrors || []) {
      if (item?.field && item?.message) {
        fieldMap[item.field] = item.message;
      }
    }
    return {
      code: envelope.code || 'API_ERROR',
      message: envelope.title || envelope.detail || 'Request failed',
      status: envelope.status || error?.response?.status || 500,
      requestId: envelope.requestId || 'unknown',
      fieldErrors: envelope.fieldErrors || [],
      fieldMap,
    };
  }
  return {
    code: 'NETWORK_ERROR',
    message: error?.message || 'Network request failed',
    status: error?.response?.status || 0,
    requestId: 'unknown',
    fieldErrors: [],
    fieldMap: {},
  };
}

export const api = {
  get: (url, params) => client.get(url, { params }),
  post: (url, data, headers = {}) => client.post(url, data, { headers }),
  put: (url, data, headers = {}) => client.put(url, data, { headers }),
  patch: (url, data, headers = {}) => client.patch(url, data, { headers }),
  delete: (url, headers = {}) => client.delete(url, { headers }),
};

export default client;
