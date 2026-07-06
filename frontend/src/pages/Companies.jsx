import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Button, Card, CardContent, Grid, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  Paper, Dialog, DialogTitle, DialogContent, DialogActions, 
  TextField, Alert, CircularProgress, Chip
} from '@mui/material';
import { Plus, Building, UserPlus, Mail, Globe, MapPin } from 'lucide-react';
import api from '../services/api';

export default function Companies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  
  // Modal states
  const [openModal, setOpenModal] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [formMessage, setFormMessage] = useState(null);

  const fetchCompanies = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.get('/company/companies/');
      setCompanies(res.data.results || res.data);
    } catch (e) {
      console.error(e);
      setErrorMsg('Failed to load tenant companies directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const handleOpenModal = () => {
    setOpenModal(true);
    setFormMessage(null);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setCompanyName('');
    setUsername('');
    setEmail('');
    setPassword('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormMessage(null);

    try {
      await api.post('/auth/register-company/', {
        company_name: companyName,
        username,
        email,
        password
      });
      setFormMessage({ type: 'success', text: 'Company & Admin registered successfully!' });
      fetchCompanies();
      setTimeout(() => {
        handleCloseModal();
      }, 1500);
    } catch (err) {
      console.error(err);
      const errDetail = err.response?.data?.detail || 'Registration failed. Check if username or email is already taken.';
      setFormMessage({ type: 'error', text: errDetail });
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            Company Directory
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Super Admin Tenant Registry. Add new enterprise workspaces and initialize admin accounts.
          </Typography>
        </Box>
        <Button 
          variant="contained" 
          startIcon={<Plus size={18} />}
          onClick={handleOpenModal}
        >
          Add Company Workspace
        </Button>
      </Box>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }}>
          {errorMsg}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
          <Table>
            <TableHead sx={{ bgcolor: 'background.neutral' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Company Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Domain / Domain Slug</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Address / Headquarter</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Grace Period (Mins)</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {companies.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                    No companies registered yet. Click the button to add a new company tenant.
                  </TableCell>
                </TableRow>
              ) : (
                companies.map((c) => (
                  <TableRow key={c.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Building size={20} style={{ color: '#9d4edd' }} />
                        <Typography sx={{ fontWeight: 600 }}>{c.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{c.domain || 'N/A'}</TableCell>
                    <TableCell>{c.address || 'N/A'}</TableCell>
                    <TableCell>{c.grace_period_minutes} Mins</TableCell>
                    <TableCell>
                      <Chip label="Active" color="success" size="small" sx={{ fontWeight: 600 }} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Creation Modal */}
      <Dialog 
        open={openModal} 
        onClose={handleCloseModal}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { borderRadius: '16px', p: 1 }
        }}
      >
        <DialogTitle sx={{ fontWeight: 800 }}>Create Enterprise Workspace</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            {formMessage && (
              <Alert severity={formMessage.type} sx={{ mb: 3, borderRadius: '12px' }}>
                {formMessage.text}
              </Alert>
            )}

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Company Name"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Admin Username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. acme_admin"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="email"
                  label="Admin Email Address"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. admin@acme.com"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="password"
                  label="Temporary Password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2.5, gap: 1 }}>
            <Button onClick={handleCloseModal} variant="outlined">
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="contained" 
              disabled={formLoading}
              startIcon={formLoading ? <CircularProgress size={18} /> : null}
            >
              Create Tenant & Admin
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
