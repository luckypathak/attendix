import React, { useState, useEffect } from 'react';
import { 
  Box, Card, CardContent, Grid, Button, Typography, TextField, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  Paper, Chip, CircularProgress, Alert, Dialog, DialogTitle, 
  DialogContent, DialogActions, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import { Smartphone, Phone, Plus, Edit, Trash2, Key, HelpCircle, ChevronDown, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function SMSGateway() {
  // Lists states
  const [devices, setDevices] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [queueLoading, setQueueLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Device Form Modal states
  const [openModal, setOpenModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [deviceName, setDeviceName] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [apiKey, setApiKey] = useState('attendix_gateway_secret_api_key_123');
  const [sim1Limit, setSim1Limit] = useState('100');
  const [sim2Limit, setSim2Limit] = useState('100');
  const [formLoading, setFormLoading] = useState(false);
  const [formMessage, setFormMessage] = useState(null);

  // Delete states
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [deviceToDelete, setDeviceToDelete] = useState(null);

  useEffect(() => {
    fetchDevices();
    fetchQueue();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.get('/notifications/gateway/');
      setDevices(res.data.results || res.data);
    } catch (e) {
      setErrorMsg('Failed to load SMS gateway devices.');
    } finally {
      setLoading(false);
    }
  };

  const fetchQueue = async () => {
    setQueueLoading(true);
    try {
      const res = await api.get('/notifications/queue/');
      setQueue(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setQueueLoading(false);
    }
  };

  const handleOpenModal = () => {
    setOpenModal(true);
    setFormMessage(null);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setEditingDevice(null);
    setDeviceName('');
    setDeviceId('');
    setApiKey('attendix_gateway_secret_api_key_123');
    setSim1Limit('100');
    setSim2Limit('100');
  };

  const handleEditClick = (dev) => {
    setEditingDevice(dev);
    setDeviceName(dev.device_name);
    setDeviceId(dev.device_id);
    setApiKey(dev.api_key);
    setSim1Limit(dev.sim1_daily_limit.toString());
    setSim2Limit(dev.sim2_daily_limit.toString());
    setOpenModal(true);
    setFormMessage(null);
  };

  const handleDeleteClick = (dev) => {
    setDeviceToDelete(dev);
    setOpenDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    try {
      await api.delete(`/notifications/gateway/${deviceToDelete.id}/`);
      setOpenDeleteDialog(false);
      fetchDevices();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormMessage(null);

    const payload = {
      device_name: deviceName,
      device_id: deviceId,
      api_key: apiKey,
      sim1_daily_limit: parseInt(sim1Limit),
      sim2_daily_limit: parseInt(sim2Limit)
    };

    try {
      if (editingDevice) {
        await api.patch(`/notifications/gateway/${editingDevice.id}/`, payload);
        setFormMessage({ type: 'success', text: 'Gateway device updated successfully!' });
      } else {
        await api.post('/notifications/gateway/', payload);
        setFormMessage({ type: 'success', text: 'Gateway device registered successfully!' });
      }
      fetchDevices();
      setTimeout(() => {
        handleCloseModal();
      }, 1200);
    } catch (err) {
      const errMsg = err.response?.data ? JSON.stringify(err.response.data) : 'Failed to save gateway device.';
      setFormMessage({ type: 'error', text: errMsg });
    } finally {
      setFormLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'SENT_SUCCESSFULLY':
      case 'SENT': 
        return 'success';
      case 'FAILED_TO_SEND':
      case 'FAILED': 
        return 'error';
      default: 
        return 'warning';
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            SMS Gateway Hub
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage Android device integrations, failover limits, and message queues.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button 
            variant="outlined" 
            startIcon={<RefreshCw size={16} />}
            onClick={() => { fetchDevices(); fetchQueue(); }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Plus size={18} />}
            onClick={handleOpenModal}
          >
            Register Device
          </Button>
        </Box>
      </Box>

      {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

      {/* Setup Accordion */}
      <Accordion sx={{ mb: 4, borderRadius: 2, '&:before': { display: 'none' } }} elevation={1}>
        <AccordionSummary expandIcon={<ChevronDown />}>
          <Typography sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1, color: 'primary.main' }}>
            <HelpCircle size={18} /> How to Set Up SMS Gateway on your Android Phone
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ bgcolor: 'rgba(255,255,255,0.01)', px: 3, pb: 3 }}>
          <Typography variant="body2" sx={{ lineHeight: 1.7, color: 'text.secondary' }}>
            To use your own Android phone to send automated SMS notifications from Attendix Workforce OS:
            <ol style={{ marginTop: '8px', paddingLeft: '20px' }}>
              <li>Install a standard **Android SMS Gateway App** on your phone (such as *SMS Gateway API* or any generic webhook gateway tool).</li>
              <li>Open the app on your phone and configure the **polling service** settings:
                <ul style={{ marginTop: '4px', listStyleType: 'circle', paddingLeft: '20px' }}>
                  <li><strong>Endpoint URL</strong>: <code>{window.location.origin}/api/v1/notifications/gateway/poll/</code></li>
                  <li><strong>Query Parameter</strong>: <code>?device_id=&lt;YOUR_REGISTERED_DEVICE_ID&gt;</code></li>
                  <li><strong>Polling Interval</strong>: 15 to 30 seconds</li>
                  <li><strong>Authentication Header</strong>: Add <code>X-Attendix-Gateway-Key</code> with value: <code>attendix_gateway_secret_api_key_123</code> (or the secret configured in your device list)</li>
                </ul>
              </li>
              <li>Configure the **status reporting webhook** settings inside the app:
                <ul style={{ marginTop: '4px', listStyleType: 'circle', paddingLeft: '20px' }}>
                  <li><strong>Status URL</strong>: <code>{window.location.origin}/api/v1/notifications/gateway/status/</code></li>
                  <li><strong>Method</strong>: POST</li>
                  <li><strong>Payload Format</strong>: JSON containing: <code>device_id</code>, <code>sms_id</code>, <code>status</code> (SUCCESS or FAILED), and <code>sim_used</code> (1 or 2).</li>
                </ul>
              </li>
              <li>Start the service inside the app. The phone will poll pending SMS notifications, send them via SIM cards, and switch cards if daily SIM limits are reached.</li>
            </ol>
          </Typography>
        </AccordionDetails>
      </Accordion>

      <Grid container spacing={4}>
        {/* Gateway Devices Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Smartphone size={20} /> Registered Gateway Devices
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Device Name</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Device ID</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>SIM 1 Limit</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>SIM 2 Limit</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Last Ping / Active</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                          <CircularProgress size={28} />
                        </TableCell>
                      </TableRow>
                    ) : devices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No gateway devices registered. Click 'Register Device' to get started.
                        </TableCell>
                      </TableRow>
                    ) : (
                      devices.map((dev) => (
                        <TableRow key={dev.id} hover>
                          <TableCell sx={{ fontWeight: 600 }}>{dev.device_name}</TableCell>
                          <TableCell><code>{dev.device_id}</code></TableCell>
                          <TableCell>{dev.sim1_sent_today} / {dev.sim1_daily_limit} messages</TableCell>
                          <TableCell>{dev.sim2_sent_today} / {dev.sim2_daily_limit} messages</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip 
                                label={dev.is_active ? "ACTIVE" : "INACTIVE"} 
                                size="small" 
                                color={dev.is_active ? "success" : "default"} 
                                sx={{ fontWeight: 700, fontSize: '0.65rem' }} 
                              />
                              <Typography variant="caption" color="text.secondary">
                                {new Date(dev.last_ping).toLocaleTimeString()}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button variant="outlined" size="small" onClick={() => handleEditClick(dev)}>
                                Edit
                              </Button>
                              <Button variant="outlined" color="error" size="small" onClick={() => handleDeleteClick(dev)}>
                                Delete
                              </Button>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Message Queue Logs */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Phone size={20} /> Real-Time SMS Queue
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Phone Number</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Message</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>SIM Slot</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {queueLoading ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                          <CircularProgress size={24} />
                        </TableCell>
                      </TableRow>
                    ) : queue.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          SMS transmission queue is empty.
                        </TableCell>
                      </TableRow>
                    ) : (
                      queue.map((sms) => (
                        <TableRow key={sms.id} hover>
                          <TableCell sx={{ fontWeight: 600 }}>{sms.phone}</TableCell>
                          <TableCell>{sms.message}</TableCell>
                          <TableCell>{sms.sim_slot_used ? `Slot ${sms.sim_slot_used}` : '--'}</TableCell>
                          <TableCell>{new Date(sms.created_at).toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip 
                              label={sms.status} 
                              size="small" 
                              color={getStatusColor(sms.status)} 
                              sx={{ fontWeight: 600, fontSize: '0.65rem' }}
                            />
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Add/Edit Device Modal */}
      <Dialog open={openModal} onClose={handleCloseModal} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {editingDevice ? 'Edit Gateway Device' : 'Register New Gateway Device'}
        </DialogTitle>
        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {formMessage && <Alert severity={formMessage.type} sx={{ borderRadius: 2 }}>{formMessage.text}</Alert>}

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Device Name"
                  placeholder="e.g. Galaxy A54 Admin Phone"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Device ID"
                  placeholder="e.g. dev_galaxy_a54_1"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  disabled={!!editingDevice}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Authentication Security Token (Key)"
                  placeholder="Key for app request matching"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  InputProps={{ startAdornment: <Key size={16} style={{ marginRight: '8px', opacity: 0.5 }} /> }}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="SIM 1 Daily Limit"
                  type="number"
                  value={sim1Limit}
                  onChange={(e) => setSim1Limit(e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="SIM 2 Daily Limit"
                  type="number"
                  value={sim2Limit}
                  onChange={(e) => setSim2Limit(e.target.value)}
                  required
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={handleCloseModal} variant="outlined" disabled={formLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={formLoading}>
              {formLoading ? <CircularProgress size={24} /> : (editingDevice ? 'Save Changes' : 'Register Device')}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Delete Device Prompt */}
      <Dialog open={openDeleteDialog} onClose={() => setOpenDeleteDialog(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>De-register Device</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to de-register <strong>{deviceToDelete?.device_name}</strong>? This phone will stop polling the SMS failover logs.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOpenDeleteDialog(false)} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            De-register
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
