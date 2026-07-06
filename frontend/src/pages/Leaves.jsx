import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, MenuItem, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip, 
  CircularProgress, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions
} from '@mui/material';
import { Send, FileText, CalendarRange } from 'lucide-react';
import api from '../services/api';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import { formatDate } from '../utils/format';

export default function Leaves() {
  const { user } = useSelector((state) => state.auth);
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';

  // Forms states
  const [leaveType, setLeaveType] = useState('CASUAL');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [reason, setReason] = useState('');
  
  const [balances, setBalances] = useState([]);
  const [requests, setRequests] = useState([]);
  const [adminRequests, setAdminRequests] = useState([]);
  const [formLoading, setFormLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  // Comments state for approval dialog
  const [openComments, setOpenComments] = useState(false);
  const [selectedReq, setSelectedReq] = useState(null);
  const [comments, setComments] = useState('');

  // Allocation editing states
  const [selectedBalance, setSelectedBalance] = useState(null);
  const [newAllocation, setNewAllocation] = useState('');
  const [openAllocationModal, setOpenAllocationModal] = useState(false);
  const [allocationLoading, setAllocationLoading] = useState(false);

  useEffect(() => {
    fetchBalances();
    fetchRequests();
    if (isAdmin) {
      fetchAdminRequests();
    }
  }, [isAdmin]);

  const fetchBalances = async () => {
    try {
      const res = await api.get('/leaves/balances/');
      setBalances(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRequests = async () => {
    try {
      const res = await api.get('/leaves/requests/');
      setRequests(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAdminRequests = async () => {
    try {
      const res = await api.get('/leaves/requests/');
      setAdminRequests(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setMessage(null);
    try {
      await api.post('/leaves/requests/', {
        leave_type: leaveType,
        start_date: startDate ? startDate.format('YYYY-MM-DD') : '',
        end_date: endDate ? endDate.format('YYYY-MM-DD') : '',
        reason: reason
      });
      setMessage({ type: 'success', text: 'Leave request submitted successfully!' });
      setStartDate(null);
      setEndDate(null);
      setReason('');
      fetchRequests();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to submit leave request.' });
    } finally {
      setFormLoading(false);
    }
  };

  const openApprovalDialog = (req) => {
    setSelectedReq(req);
    setOpenComments(true);
  };

  const handleApprove = async () => {
    try {
      await api.post(`/leaves/requests/${selectedReq.id}/approve/`, { manager_comments: comments });
      setOpenComments(false);
      setComments('');
      fetchAdminRequests();
      fetchBalances();
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async () => {
    try {
      await api.post(`/leaves/requests/${selectedReq.id}/reject/`, { manager_comments: comments });
      setOpenComments(false);
      setComments('');
      fetchAdminRequests();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveAllocation = async (e) => {
    e.preventDefault();
    setAllocationLoading(true);
    try {
      await api.patch(`/leaves/balances/${selectedBalance.id}/`, {
        allocated: parseInt(newAllocation)
      });
      setOpenAllocationModal(false);
      fetchBalances();
    } catch (err) {
      console.error("Allocation edit error:", err);
    } finally {
      setAllocationLoading(false);
    }
  };

  const handleDeleteRequest = async (req) => {
    if (window.confirm(`Are you sure you want to delete this leave request for ${req.employee_name || 'this employee'}?`)) {
      try {
        await api.delete(`/leaves/requests/${req.id}/`);
        fetchAdminRequests();
        fetchRequests();
        fetchBalances();
      } catch (err) {
        console.error("Delete request error:", err);
      }
    }
  };

  const handleUnapproveRequest = async (req) => {
    const actionText = req.status === 'APPROVED' ? 'unapprove' : 'revert';
    if (window.confirm(`Are you sure you want to ${actionText} this leave request for ${req.employee_name}?`)) {
      try {
        await api.post(`/leaves/requests/${req.id}/unapprove/`);
        fetchAdminRequests();
        fetchRequests();
        fetchBalances();
      } catch (err) {
        console.error("Revert request error:", err);
      }
    }
  };

  const getStatusChipColor = (status) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'REJECTED': return 'error';
      default: return 'warning';
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Leave Planner
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Request absences, view available balances, and audit approval logs.
        </Typography>
      </Box>

      {/* Balances Section (Only for Employees) */}
      {!isAdmin && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {balances.map((b) => (
            <Grid item xs={12} sm={6} md={3} key={b.id}>
              <Card>
                <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }} color="text.secondary">
                      {b.leave_type.replace('_', ' ')}
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 800, mt: 1 }}>
                      {b.remaining} <Typography variant="caption" color="text.secondary">left</Typography>
                    </Typography>
                  </Box>
                  <Chip label={`Allocated: ${b.allocated}`} size="small" variant="outlined" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Grid container spacing={4}>
        {/* Leave Request Form */}
        {!isAdmin && (
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarRange size={20} /> Request Leave
                </Typography>

                {message && (
                  <Alert severity={message.type} sx={{ mb: 3, borderRadius: 2 }}>
                    {message.text}
                  </Alert>
                )}

                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Box component="form" onSubmit={handleSubmit}>
                    <TextField
                      select
                      fullWidth
                      label="Leave Type"
                      value={leaveType}
                      onChange={(e) => setLeaveType(e.target.value)}
                      sx={{ mb: 2 }}
                    >
                      <MenuItem value="CASUAL">Casual Leave</MenuItem>
                      <MenuItem value="SICK">Sick Leave</MenuItem>
                      <MenuItem value="PAID">Paid Leave</MenuItem>
                      <MenuItem value="UNPAID">Unpaid Leave</MenuItem>
                    </TextField>

                    <Box sx={{ mb: 2 }}>
                      <DatePicker
                        label="Start Date"
                        value={startDate}
                        onChange={(newValue) => setStartDate(newValue)}
                        slotProps={{ textField: { fullWidth: true } }}
                      />
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <DatePicker
                        label="End Date"
                        value={endDate}
                        onChange={(newValue) => setEndDate(newValue)}
                        slotProps={{ textField: { fullWidth: true } }}
                      />
                    </Box>

                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Reason for Leave"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    sx={{ mb: 3 }}
                    required
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    size="large"
                    disabled={formLoading}
                    startIcon={<Send size={16} />}
                  >
                    {formLoading ? <CircularProgress size={24} /> : 'Submit Request'}
                  </Button>
                </Box>
              </LocalizationProvider>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Requests Logs */}
        <Grid item xs={12} md={isAdmin ? 12 : 7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                {isAdmin ? 'Leave Approval Timeline' : 'My Leave Requests'}
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Duration</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(isAdmin ? adminRequests : requests).length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 5 : 4} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No leave requests filed.
                        </TableCell>
                      </TableRow>
                    ) : (
                      (isAdmin ? adminRequests : requests).map((req) => (
                        <TableRow key={req.id}>
                          {isAdmin && <TableCell>{req.employee_name}</TableCell>}
                          <TableCell>{req.leave_type}</TableCell>
                          <TableCell>{formatDate(req.start_date)} to {formatDate(req.end_date)}</TableCell>
                          <TableCell>
                            <Chip 
                              label={req.status} 
                              size="small" 
                              color={getStatusChipColor(req.status)} 
                              sx={{ fontWeight: 600, fontSize: '0.75rem' }}
                            />
                          </TableCell>
                          {isAdmin && (
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                {req.status === 'PENDING' && (
                                  <Button 
                                    variant="outlined" 
                                    size="small"
                                    onClick={() => openApprovalDialog(req)}
                                  >
                                    Process
                                  </Button>
                                )}
                                {req.status === 'APPROVED' && (
                                  <Button 
                                    variant="outlined" 
                                    color="warning"
                                    size="small"
                                    onClick={() => handleUnapproveRequest(req)}
                                  >
                                    Unapprove
                                  </Button>
                                )}
                                {req.status === 'REJECTED' && (
                                  <Button 
                                    variant="outlined" 
                                    color="warning"
                                    size="small"
                                    onClick={() => handleUnapproveRequest(req)}
                                  >
                                    Revert
                                  </Button>
                                )}
                                {req.status !== 'PENDING' && req.status !== 'APPROVED' && req.status !== 'REJECTED' && (
                                  '--'
                                )}
                                <Button 
                                  variant="outlined" 
                                  color="error"
                                  size="small"
                                  onClick={() => handleDeleteRequest(req)}
                                >
                                  Delete
                                </Button>
                              </Box>
                            </TableCell>
                          )}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Admin Section: Workforce Leave Balances */}
        {isAdmin && (
          <Grid item xs={12} sx={{ mt: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                  Workforce Leave Allocations
                </Typography>
                <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Leave Type</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Allocated Days</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Used Days</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Remaining</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {balances.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                            No leave balances registered.
                          </TableCell>
                        </TableRow>
                      ) : (
                        balances.map((b) => (
                          <TableRow key={b.id} hover>
                            <TableCell sx={{ fontWeight: 600 }}>{b.employee_name}</TableCell>
                            <TableCell>{b.leave_type}</TableCell>
                            <TableCell>{b.allocated} days</TableCell>
                            <TableCell>{b.used} days</TableCell>
                            <TableCell>{b.allocated - b.used} days</TableCell>
                            <TableCell>
                              <Button 
                                variant="outlined" 
                                size="small" 
                                onClick={() => {
                                  setSelectedBalance(b);
                                  setNewAllocation(b.allocated);
                                  setOpenAllocationModal(true);
                                }}
                              >
                                Edit Allocation
                              </Button>
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
        )}
      </Grid>

      {/* Approval Dialog with comments */}
      <Dialog open={openComments} onClose={() => setOpenComments(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Review Leave Request</DialogTitle>
        <DialogContent sx={{ minWidth: 350 }}>
          <Typography variant="body2" sx={{ mb: 2 }} color="text.secondary">
            Employee: {selectedReq?.employee_name}
            <br />
            Dates: {selectedReq?.start_date} to {selectedReq?.end_date}
            <br />
            Reason: {selectedReq?.reason}
          </Typography>
          <TextField
            fullWidth
            label="Manager Comments"
            multiline
            rows={3}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleReject} color="error" variant="outlined">
            Reject
          </Button>
          <Button onClick={handleApprove} color="success" variant="contained">
            Approve
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Allocation Dialog */}
      <Dialog open={openAllocationModal} onClose={() => setOpenAllocationModal(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Edit Leave Allocation</DialogTitle>
        <Box component="form" onSubmit={handleSaveAllocation}>
          <DialogContent sx={{ minWidth: 350, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Employee: <strong>{selectedBalance?.employee_name}</strong>
              <br />
              Leave Type: <strong>{selectedBalance?.leave_type}</strong>
            </Typography>
            <TextField
              type="number"
              fullWidth
              label="Allocated Days"
              value={newAllocation}
              onChange={(e) => setNewAllocation(e.target.value)}
              required
            />
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setOpenAllocationModal(false)} variant="outlined">
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={allocationLoading}>
              {allocationLoading ? <CircularProgress size={24} /> : 'Save Allocation'}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  );
}
