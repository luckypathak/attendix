import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Get API base URL dynamically
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login/`, { username, password });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || error.response?.data || 'Invalid username or password.'
      );
    }
  }
);

const savedUser = JSON.parse(localStorage.getItem('user') || 'null');
const savedAccessToken = localStorage.getItem('accessToken') || null;
const savedRefreshToken = localStorage.getItem('refreshToken') || null;

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: savedUser,
    accessToken: savedAccessToken,
    refreshToken: savedRefreshToken,
    loading: false,
    error: null,
  },
  reducers: {
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      localStorage.removeItem('user');
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.accessToken = action.payload.access;
        state.refreshToken = action.payload.refresh;
        
        localStorage.setItem('user', JSON.stringify(action.payload.user));
        localStorage.setItem('accessToken', action.payload.access);
        localStorage.setItem('refreshToken', action.payload.refresh);
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
