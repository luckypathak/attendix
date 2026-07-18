import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Grid, TextField, Button, CircularProgress, Alert
} from '@mui/material';
import { Save } from 'lucide-react';
import api from '../services/api';
import { useSelector } from 'react-redux';

export default function CompanySettings() {
  const user = useSelector(state => state.auth.user);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [companyId, setCompanyId] = useState(null);
  
  const [settings, setSettings] = useState({
    office_radius_meters: 100,
    location_update_frequency_minutes: 5,
    geofence_grace_period_minutes: 5,
    auto_checkout_hours: 10.0,
    grace_period_minutes: 15,
    late_limit_for_half_day: 3
  });

  useEffect(() => {
    fetchCompanySettings();
  }, []);

  const fetchCompanySettings = async () => {
    setLoading(true);
    try {
      const res = await api.get('/company/companies/');
      let company = null;
      if (Array.isArray(res.data.results) && res.data.results.length > 0) {
        company = res.data.results[0];
      } else if (Array.isArray(res.data) && res.data.length > 0) {
        company = res.data[0];
      }
      
      if (company) {
        setCompanyId(company.id);
        setSettings({
          office_radius_meters: company.office_radius_meters,
          location_update_frequency_minutes: company.location_update_frequency_minutes,
          geofence_grace_period_minutes: company.geofence_grace_period_minutes,
          auto_checkout_hours: parseFloat(company.auto_checkout_hours),
          grace_period_minutes: company.grace_period_minutes,
          late_limit_for_half_day: company.late_limit_for_half_day
        });
      }
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to load company settings.");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!companyId) return;
    
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    
    try {
      await api.patch(`/company/companies/${companyId}/`, settings);
      setSuccessMsg("Settings updated successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to update settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: parseFloat(value) || value
    }));
  };

  if (loading) {
    return (
      <Box p={3} display="flex" justifyContent="center">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3} maxWidth="800px" mx="auto">
      <Typography variant="h4" fontWeight="800" sx={{ mb: 4 }}>Company Configuration</Typography>
      
      {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}
      {successMsg && <Alert severity="success" sx={{ mb: 3 }}>{successMsg}</Alert>}
      
      <Paper elevation={0} sx={{ p: 4, borderRadius: 3, border: '1px solid #e0e0e0' }}>
        <form onSubmit={handleSave}>
          <Typography variant="h6" fontWeight="600" sx={{ mb: 3 }}>Location Tracking</Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Office Radius (meters)"
                name="office_radius_meters"
                type="number"
                value={settings.office_radius_meters}
                onChange={handleChange}
                helperText="Geofence size for Office Staff"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Update Frequency (mins)"
                name="location_update_frequency_minutes"
                type="number"
                value={settings.location_update_frequency_minutes}
                onChange={handleChange}
                helperText="How often GPS pings are sent"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Grace Period (mins)"
                name="geofence_grace_period_minutes"
                type="number"
                value={settings.geofence_grace_period_minutes}
                onChange={handleChange}
                helperText="Time outside before auto-checkout"
              />
            </Grid>
          </Grid>
          
          <Typography variant="h6" fontWeight="600" sx={{ mb: 3, mt: 5 }}>General Attendance Settings</Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Standard Grace Period (mins)"
                name="grace_period_minutes"
                type="number"
                value={settings.grace_period_minutes}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Late Limit for Half Day"
                name="late_limit_for_half_day"
                type="number"
                value={settings.late_limit_for_half_day}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Auto Checkout Limit (hours)"
                name="auto_checkout_hours"
                type="number"
                inputProps={{ step: "0.1" }}
                value={settings.auto_checkout_hours}
                onChange={handleChange}
              />
            </Grid>
          </Grid>
          
          <Box display="flex" justifyContent="flex-end" mt={5}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={saving}
            >
              {saving ? <CircularProgress size={20} color="inherit" /> : 'Save Configuration'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}
