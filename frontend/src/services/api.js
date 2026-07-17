import axios from 'axios';
import { store } from '../features/store';
import { logout } from '../features/authSlice';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const getMediaUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const base = API_URL.split('/api/v1')[0];
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`;
};

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inject Access Token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Scoping query param for multi-firm selector
    const selectedFirm = localStorage.getItem('selectedFirmId');
    if (selectedFirm && selectedFirm !== 'ALL') {
      if (config.method === 'get') {
        config.params = config.params || {};
        config.params['firm'] = selectedFirm;
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 responses for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and request hasn't been retried yet
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/login/') {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh/`, { refresh: refreshToken });
          const newAccessToken = res.data.access;
          
          localStorage.setItem('accessToken', newAccessToken);
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh token expired or invalid, logout user
          store.dispatch(logout());
          return Promise.reject(refreshError);
        }
      } else {
        store.dispatch(logout());
      }
    }
    return Promise.reject(error);
  }
);

export default api;
