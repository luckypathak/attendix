import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Grid, CircularProgress, Alert, 
  FormControl, InputLabel, Select, MenuItem 
} from '@mui/material';
import api from '../services/api';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useSelector } from 'react-redux';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function LiveTracking() {
  const [employees, setEmployees] = useState([]);
  const [selectedEmpId, setSelectedEmpId] = useState('');
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const user = useSelector(state => state.auth.user);

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmpId) {
      fetchTrackingHistory(selectedEmpId);
      const interval = setInterval(() => {
        fetchTrackingHistory(selectedEmpId);
      }, 30000); // refresh every 30s
      return () => clearInterval(interval);
    }
  }, [selectedEmpId]);

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/employees/');
      setEmployees(res.data.results || res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchTrackingHistory = async (empId) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await api.get(`/attendance/tracking-history/?employee_id=${empId}&date=${today}`);
      setHistory(res.data);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.status === 404) {
        setErrorMsg("No active tracking history found for today.");
        setHistory(null);
      } else {
        setErrorMsg("Failed to load tracking data.");
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedEmp = employees.find(e => e.id === parseInt(selectedEmpId));

  return (
    <Box p={3} maxWidth="1200px" mx="auto">
      <Typography variant="h4" fontWeight="800" sx={{ mb: 4 }}>Live Tracking Dashboard</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #e0e0e0', height: '100%' }}>
            <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>Select Employee</Typography>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Employee</InputLabel>
              <Select
                value={selectedEmpId}
                label="Employee"
                onChange={(e) => setSelectedEmpId(e.target.value)}
              >
                {employees.map(emp => (
                  <MenuItem key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name} ({emp.work_category === 'FIELD' ? 'Field' : 'Office'})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedEmp && (
              <Box>
                <Typography variant="body1"><strong>Name:</strong> {selectedEmp.first_name} {selectedEmp.last_name}</Typography>
                <Typography variant="body1"><strong>Category:</strong> {selectedEmp.work_category}</Typography>
                {history && history.pings && history.pings.length > 0 && (
                  <Typography variant="body1" sx={{ mt: 2 }}>
                    <strong>Latest Update:</strong> {new Date(history.pings[history.pings.length - 1].timestamp).toLocaleTimeString()}
                  </Typography>
                )}
              </Box>
            )}

            {errorMsg && <Alert severity="warning" sx={{ mt: 3 }}>{errorMsg}</Alert>}
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid #e0e0e0', overflow: 'hidden', height: '600px' }}>
            {!selectedEmpId ? (
              <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                <Typography color="text.secondary">Select an employee to view tracking map.</Typography>
              </Box>
            ) : loading && !history ? (
              <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                <CircularProgress />
              </Box>
            ) : history && history.pings && history.pings.length > 0 ? (
              <MapContainer 
                center={[history.pings[0].latitude, history.pings[0].longitude]} 
                zoom={14} 
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {selectedEmp?.work_category === 'OFFICE' && history.pings.length > 0 && (
                  <Circle 
                    center={[history.pings[0].latitude, history.pings[0].longitude]}
                    radius={100} // office radius config
                    pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.1 }}
                  />
                )}

                <Polyline 
                  positions={history.pings.map(p => [p.latitude, p.longitude])} 
                  color="red"
                />

                {history.pings.map((ping, idx) => (
                  <Marker key={idx} position={[ping.latitude, ping.longitude]}>
                    <Popup>
                      Time: {new Date(ping.timestamp).toLocaleTimeString()} <br/>
                      Accuracy: {ping.accuracy}m
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            ) : (
              <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                <Typography color="text.secondary">Map will appear when location data is available.</Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
