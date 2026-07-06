import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Box, Card, CardContent, TextField, Button, Typography, 
  CircularProgress, Alert, Container 
} from '@mui/material';
import { Shield } from 'lucide-react';
import { login, clearError } from '../features/authSlice';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const { user, loading, error } = useSelector((state) => state.auth);

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (user) {
      navigate('/dashboard');
    }
    // Clean errors on mount
    dispatch(clearError());
  }, [user, navigate, dispatch]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username && password) {
      dispatch(login({ username, password }));
    }
  };

  return (
    <Box 
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        background: (theme) => theme.palette.mode === 'dark'
          ? 'radial-gradient(circle at top right, #1a163a 0%, #0a0915 100%)'
          : 'radial-gradient(circle at top right, #e8eaff 0%, #f8f9fa 100%)',
        py: 4
      }}
    >
      <Container maxWidth="xs">
        <Card 
          sx={{ 
            backgroundColor: (theme) => theme.palette.background.glass,
            backdropFilter: 'blur(20px)',
            border: (theme) => theme.palette.mode === 'dark' 
              ? '1px solid rgba(255, 255, 255, 0.08)' 
              : '1px solid rgba(0, 0, 0, 0.08)',
          }}
        >
          <CardContent sx={{ p: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            
            {/* Logo */}
            <Box 
              sx={{ 
                p: 2, 
                borderRadius: '50%', 
                background: (theme) => theme.palette.mode === 'dark'
                  ? 'rgba(157, 78, 221, 0.1)'
                  : 'rgba(98, 0, 238, 0.05)',
                color: 'primary.main',
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Shield size={36} />
            </Box>

            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 800, letterSpacing: '-0.5px' }}>
              Attendix OS
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4, textAlign: 'center' }}>
              Workforce & HR Management System
            </Typography>

            {error && (
              <Alert severity="error" sx={{ width: '100%', mb: 3, borderRadius: 2 }}>
                {typeof error === 'string' ? error : JSON.stringify(error)}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{ mb: 3 }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{ py: 1.5, position: 'relative' }}
              >
                {loading ? (
                  <CircularProgress size={24} sx={{ color: 'primary.main' }} />
                ) : (
                  'Sign In'
                )}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
