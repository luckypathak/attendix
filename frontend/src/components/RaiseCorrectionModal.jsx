import React, { useState } from 'react';
import { Modal, Box, Typography, Button, TextField, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import api from '../../api';

export default function RaiseCorrectionModal({ open, onClose, onSaved }) {
  const [requestType, setRequestType] = useState('MISSED_OUT');
  const [date, setDate] = useState('');
  const [reason, setReason] = useState('');
  const [checkInTime, setCheckInTime] = useState('');
  const [checkOutTime, setCheckOutTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = {
        request_type: requestType,
        date: date,
        reason: reason,
        requested_check_in: checkInTime || null,
        requested_check_out: checkOutTime || null
      };
      await api.post('/attendance/correction/', data);
      onSaved();
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={{
        position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        width: 400, bgcolor: 'background.paper', boxShadow: 24, p: 4, borderRadius: 2
      }}>
        <Typography variant="h6" mb={2}>Raise Attendance Correction</Typography>
        
        {error && <Typography color="error" mb={2}>{error}</Typography>}
        
        <FormControl fullWidth margin="normal">
          <InputLabel>Correction Type</InputLabel>
          <Select
            value={requestType}
            label="Correction Type"
            onChange={(e) => setRequestType(e.target.value)}
          >
            <MenuItem value="MISSED_IN">Missed Check In</MenuItem>
            <MenuItem value="MISSED_OUT">Missed Check Out</MenuItem>
            <MenuItem value="MISSED_BOTH">Missed Both</MenuItem>
          </Select>
        </FormControl>

        <TextField
          label="Date"
          type="date"
          fullWidth
          margin="normal"
          InputLabelProps={{ shrink: true }}
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />

        {(requestType === 'MISSED_IN' || requestType === 'MISSED_BOTH') && (
          <TextField
            label="Requested Check In Time"
            type="time"
            fullWidth
            margin="normal"
            InputLabelProps={{ shrink: true }}
            value={checkInTime}
            onChange={(e) => setCheckInTime(e.target.value)}
          />
        )}

        {(requestType === 'MISSED_OUT' || requestType === 'MISSED_BOTH') && (
          <TextField
            label="Requested Check Out Time"
            type="time"
            fullWidth
            margin="normal"
            InputLabelProps={{ shrink: true }}
            value={checkOutTime}
            onChange={(e) => setCheckOutTime(e.target.value)}
          />
        )}

        <TextField
          label="Reason"
          multiline
          rows={3}
          fullWidth
          margin="normal"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />

        <Box display="flex" justifyContent="flex-end" gap={2} mt={3}>
          <Button onClick={onClose} color="inherit">Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary" disabled={loading}>
            {loading ? 'Submitting...' : 'Submit Request'}
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}
