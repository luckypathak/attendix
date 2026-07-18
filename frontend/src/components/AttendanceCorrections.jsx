import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Button, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { CheckCircle, XCircle } from 'lucide-react';
import api from '../services/api';

export default function AttendanceCorrections({ firmId, user }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rejectModal, setRejectModal] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [statusFilter, setStatusFilter] = useState('PENDING');

  useEffect(() => {
    fetchRequests();
  }, [firmId, statusFilter]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const params = { status: statusFilter };
      if (firmId && firmId !== 'ALL') params.firm = firmId;
      const response = await api.get('/attendance/correction/', { params });
      setRequests(response.data.results || response.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.post(`/attendance/correction/${id}/approve/`);
      fetchRequests();
    } catch (e) {
      alert('Error approving correction');
    }
  };

  const handleReject = async () => {
    try {
      await api.post(`/attendance/correction/${selectedId}/reject/`, { rejected_reason: rejectReason });
      setRejectModal(false);
      fetchRequests();
    } catch (e) {
      alert('Error rejecting correction');
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">Attendance Corrections</Typography>
        <FormControl size="small" sx={{ width: 200 }}>
          <InputLabel>Status</InputLabel>
          <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="PENDING">Pending</MenuItem>
            <MenuItem value="APPROVED">Approved</MenuItem>
            <MenuItem value="REJECTED">Rejected</MenuItem>
            <MenuItem value="ALL">All</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {loading ? (
        <CircularProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Employee</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Requested Times</TableCell>
                <TableCell>Reason</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {requests.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{row.employee_name} ({row.employee_username})</TableCell>
                  <TableCell>{row.date}</TableCell>
                  <TableCell>{row.request_type_display}</TableCell>
                  <TableCell>
                    {row.requested_check_in && <div>IN: {row.requested_check_in}</div>}
                    {row.requested_check_out && <div>OUT: {row.requested_check_out}</div>}
                  </TableCell>
                  <TableCell>{row.reason}</TableCell>
                  <TableCell>
                    <Chip
                      label={row.status}
                      color={row.status === 'APPROVED' ? 'success' : row.status === 'REJECTED' ? 'error' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {row.status === 'PENDING' && (
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          onClick={() => handleApprove(row.id)}
                        >
                          <CheckCircle size={16} />
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          color="error"
                          onClick={() => {
                            setSelectedId(row.id);
                            setRejectReason('');
                            setRejectModal(true);
                          }}
                        >
                          <XCircle size={16} />
                        </Button>
                      </Box>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {requests.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">No requests found</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={rejectModal} onClose={() => setRejectModal(false)}>
        <DialogTitle>Reject Correction Request</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Rejection Reason"
            fullWidth
            variant="outlined"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectModal(false)}>Cancel</Button>
          <Button onClick={handleReject} color="error" variant="contained">Reject</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
