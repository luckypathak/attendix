import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Box, Card, CardContent, TextField, Button, Typography, 
  CircularProgress, Alert, Container 
} from '@mui/material';
import { Shield } from 'lucide-react';
import api from '../services/api';

export default function Register() {
  const [companyName, setCompanyName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!companyName || !username || !email || !password) return;
    
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    
    try {
      await api.post('/auth/register-company/', {
        company_name: companyName,
        username,
        email,
        password
      });
      setSuccessMsg("Company registered successfully! Redirecting to login...");
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      console.error(err);
      if (err.response?.data) {
        const data = err.response.data;
        const firstErr = Object.values(data)[0];
        setErrorMsg(Array.isArray(firstErr) ? firstErr[0] : (typeof firstErr === 'string' ? firstErr : "Registration failed."));
      } else {
        setErrorMsg("Failed to register company. Please try again.");
      }
    } finally {
      setLoading(false);
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
              Register OS
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
              Create a new company account
            </Typography>

            {errorMsg && (
              <Alert severity="error" sx={{ width: '100%', mb: 2, borderRadius: 2 }}>
                {errorMsg}
              </Alert>
            )}

            {successMsg && (
              <Alert severity="success" sx={{ width: '100%', mb: 2, borderRadius: 2 }}>
                {successMsg}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
              <TextField
                margin="dense"
                required
                fullWidth
                id="companyName"
                label="Company Name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                sx={{ mb: 1.5 }}
                autoFocus
              />
              <TextField
                margin="dense"
                required
                fullWidth
                id="username"
                label="Admin Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                sx={{ mb: 1.5 }}
              />
              <TextField
                margin="dense"
                required
                fullWidth
                type="email"
                id="email"
                label="Admin Email Address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{ mb: 1.5 }}
              />
              <TextField
                margin="dense"
                required
                fullWidth
                type="password"
                id="password"
                label="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{ mb: 2.5 }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{ py: 1.5, position: 'relative', mb: 2 }}
              >
                {loading ? (
                  <CircularProgress size={24} sx={{ color: 'primary.main' }} />
                ) : (
                  'Sign Up'
                )}
              </Button>
            </Box>

            <Box sx={{ mt: 1, textAlign: 'center' }}>
              <Link to="/login" style={{ fontSize: '0.85rem', color: '#9d4ede', textDecoration: 'none', fontWeight: 500 }}>
                Already have an account? Sign In
              </Link>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
