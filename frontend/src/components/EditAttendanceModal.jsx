import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, MenuItem, Box, Alert, CircularProgress,
  Typography, FormControlLabel, Switch, Avatar
} from '@mui/material';
import api, { getMediaUrl } from '../services/api';

export default function EditAttendanceModal({ open, onClose, session, onSaved }) {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Form State
  const [checkInTime, setCheckInTime] = useState('');
  const [checkOutTime, setCheckOutTime] = useState('');
  const [status, setStatus] = useState('');
  const [otStatus, setOtStatus] = useState('');
  const [continueShift, setContinueShift] = useState(false);
  const [autoCheckout, setAutoCheckout] = useState(false);
  const [reason, setReason] = useState('');
  
  // Location and Photos
  const [checkInAddress, setCheckInAddress] = useState('');
  const [checkOutAddress, setCheckOutAddress] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);
  const [checkOutCapturedImage, setCheckOutCapturedImage] = useState(null);


  const convertTo24Hour = (timeStr) => {
    if (!timeStr) return '';
    if (timeStr.match(/^\d{2}:\d{2}$/)) return timeStr; // already 24h
    const match = timeStr.match(/(\d+):(\d+)\s?(AM|PM)/i);
    if (!match) return timeStr;
    let [_, h, m, period] = match;
    h = parseInt(h);
    if (period.toUpperCase() === 'PM' && h < 12) h += 12;
    if (period.toUpperCase() === 'AM' && h === 12) h = 0;
    return `${h.toString().padStart(2, '0')}:${m}`;
  };

  useEffect(() => {
    if (session && open) {
      setCheckInTime(convertTo24Hour(session.check_in_time) || '');
      setCheckOutTime(convertTo24Hour(session.check_out_time) || '');
      setStatus(session.parent_status || 'PRESENT'); // Assumes parent_status is passed or we default
      setOtStatus(session.ot_status || '');
      setContinueShift(session.continue_shift || false);
      setAutoCheckout(session.auto_checkout || false);
      setCheckInAddress(session.check_in_address || '');
      setCheckOutAddress(session.check_out_address || '');
      setCapturedImage(null);
      setCheckOutCapturedImage(null);
      setReason('');
      setErrorMsg(null);
    }
  }, [session, open]);

  const handleSave = async () => {
    if (!reason.trim()) {
      setErrorMsg("Reason is required for editing attendance.");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append('session_id', session.id);
      formData.append('reason', reason);
      if (checkInTime) formData.append('check_in_time', checkInTime);
      if (checkOutTime) formData.append('check_out_time', checkOutTime);
      if (status) formData.append('status', status);
      
      formData.append('continue_shift', continueShift);
      formData.append('auto_checkout', autoCheckout);
      
      if (checkInAddress) formData.append('check_in_address', checkInAddress);
      if (checkOutAddress) formData.append('check_out_address', checkOutAddress);
      
      if (otStatus) formData.append('ot_status', otStatus);
      if (capturedImage) formData.append('captured_image', capturedImage);
      if (checkOutCapturedImage) formData.append('check_out_captured_image', checkOutCapturedImage);

      await api.patch('/attendance/records/edit-session/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onSaved();
      onClose();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to edit session.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>Edit Attendance: {session?.employee_name || 'Session'}</DialogTitle>
      <DialogContent dividers>
        {errorMsg && <Alert severity="error" sx={{ mb: 2 }}>{errorMsg}</Alert>}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Check-in Time"
              type="time"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={checkInTime}
              onChange={(e) => setCheckInTime(e.target.value)}
            />
            <TextField
              label="Check-out Time"
              type="time"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={checkOutTime}
              onChange={(e) => setCheckOutTime(e.target.value)}
            />
          </Box>

          <TextField
            select
            label="Parent Attendance Status"
            fullWidth
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            helperText="Forces the overall attendance status for the day."
          >
            <MenuItem value="PRESENT">Present</MenuItem>
            <MenuItem value="LATE">Late</MenuItem>
            <MenuItem value="HALF_DAY">Half Day</MenuItem>
            <MenuItem value="ABSENT">Absent</MenuItem>
            <MenuItem value="LEAVE">On Leave</MenuItem>
            <MenuItem value="HOLIDAY">Holiday</MenuItem>
          </TextField>

          <TextField
            select
            label="Overtime Status"
            fullWidth
            value={otStatus}
            onChange={(e) => setOtStatus(e.target.value)}
          >
            <MenuItem value="">None</MenuItem>
            <MenuItem value="PENDING">Pending Approval</MenuItem>
            <MenuItem value="APPROVED">Approved</MenuItem>
            <MenuItem value="REJECTED">Rejected</MenuItem>
          </TextField>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={continueShift}
                  onChange={(e) => setContinueShift(e.target.checked)}
                />
              }
              label="Continue Shift"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={autoCheckout}
                  onChange={(e) => setAutoCheckout(e.target.checked)}
                />
              }
              label="Auto Checkout"
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Check-in Location"
              fullWidth
              value={checkInAddress}
              onChange={(e) => setCheckInAddress(e.target.value)}
            />
            <TextField
              label="Check-out Location"
              fullWidth
              value={checkOutAddress}
              onChange={(e) => setCheckOutAddress(e.target.value)}
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Replace Check-in Photo
              </Typography>
              {session?.captured_image && (
                <Box sx={{ mb: 1 }}>
                  <img src={getMediaUrl(session.captured_image)} alt="Check In" style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover' }} />
                </Box>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setCapturedImage(e.target.files[0])}
              />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Replace Check-out Photo
              </Typography>
              {session?.check_out_captured_image && (
                <Box sx={{ mb: 1 }}>
                  <img src={getMediaUrl(session.check_out_captured_image)} alt="Check Out" style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover' }} />
                </Box>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setCheckOutCapturedImage(e.target.files[0])}
              />
            </Box>
          </Box>

          <TextField
            label="Reason for Edit (Required)"
            fullWidth
            multiline
            rows={2}
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="E.g., Employee forgot to checkout, correcting time."
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={loading} color="inherit">Cancel</Button>
        <Button onClick={handleSave} variant="contained" disabled={loading} startIcon={loading ? <CircularProgress size={16} /> : null}>
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
}
