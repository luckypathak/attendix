import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, MenuItem, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip, 
  CircularProgress, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, Checkbox, FormControlLabel, IconButton
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import { Send, CalendarRange, Settings, Trash2, Plus } from 'lucide-react';
import api from '../services/api';
import { formatDate } from '../utils/format';

export default function Leaves() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';

  // State collections
  const [categories, setCategories] = useState([]);
  const [requests, setRequests] = useState([]);
  const [adminRequests, setAdminRequests] = useState([]);
  const [employees, setEmployees] = useState([]);

  // Form states
  const [leaveType, setLeaveType] = useState('');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [reason, setReason] = useState('');
  const [durationType, setDurationType] = useState('full_day');
  const [customHours, setCustomHours] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // Category Manager Modal
  const [openCatModal, setOpenCatModal] = useState(false);
  const [newCatName, setNewCatName] = useState('');
  
  // Approval Modal states
  const [openComments, setOpenComments] = useState(false);
  const [selectedReq, setSelectedReq] = useState(null);
  const [comments, setComments] = useState('');
  const [isPaidApproved, setIsPaidApproved] = useState(true);

  // Edit Allocation Modal states
  const [openAllocationModal, setOpenAllocationModal] = useState(false);
  const [selectedEmpProfile, setSelectedEmpProfile] = useState(null);
  const [newAllocation, setNewAllocation] = useState('12');

  const fetchCategories = async () => {
    try {
      const res = await api.get('/leaves/categories/');
      const data = res.data.results || res.data;
      setCategories(data);
      if (data.length > 0 && !leaveType) {
        setLeaveType(data[0].name);
      }
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
    if (!isAdmin) return;
    try {
      const res = await api.get('/leaves/requests/', { params: { firm: selectedFirm } });
      setAdminRequests(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchEmployees = async () => {
    if (!isAdmin) return;
    try {
      const res = await api.get('/employees/', { params: { firm: selectedFirm } });
      setEmployees(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchCategories();
    fetchRequests();
    fetchAdminRequests();
    fetchEmployees();
  }, [selectedFirm]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setMessage(null);
    try {
      await api.post('/leaves/requests/', {
        leave_type: leaveType || 'General Leave',
        start_date: startDate ? startDate.format('YYYY-MM-DD') : '',
        end_date: endDate ? endDate.format('YYYY-MM-DD') : '',
        reason: reason,
        duration_type: durationType,
        custom_hours: durationType === 'custom_hours' ? parseFloat(customHours) : null
      });
      setMessage({ type: 'success', text: 'Leave request submitted successfully!' });
      setStartDate(null);
      setEndDate(null);
      setReason('');
      setDurationType('full_day');
      setCustomHours('');
      fetchRequests();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to submit leave request.' });
    } finally {
      setFormLoading(false);
    }
  };

  // Categories Handlers
  const handleAddCategory = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    try {
      await api.post('/leaves/categories/', { name: newCatName.trim() });
      setNewCatName('');
      fetchCategories();
    } catch (err) {
      console.error(err);
      alert('Failed to add leave category.');
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Delete this category?')) return;
    try {
      await api.delete(`/leaves/categories/${id}/`);
      fetchCategories();
    } catch (err) {
      console.error(err);
    }
  };

  // Approval Handlers
  const openApprovalDialog = (req) => {
    setSelectedReq(req);
    setComments('');
    setIsPaidApproved(true);
    setOpenComments(true);
  };

  const handleApprove = async () => {
    try {
      await api.post(`/leaves/requests/${selectedReq.id}/approve/`, { 
        manager_comments: comments,
        is_paid: isPaidApproved
      });
      setOpenComments(false);
      fetchAdminRequests();
      fetchRequests();
      fetchEmployees();
    } catch (e) {
      console.error(e);
      alert(e.response?.data?.detail || 'Failed to approve leave request.');
    }
  };

  const handleReject = async () => {
    try {
      await api.post(`/leaves/requests/${selectedReq.id}/reject/`, { manager_comments: comments });
      setOpenComments(false);
      fetchAdminRequests();
      fetchRequests();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUnapproveRequest = async (req) => {
    if (window.confirm(`Are you sure you want to revert this leave request decision?`)) {
      try {
        await api.post(`/leaves/requests/${req.id}/unapprove/`);
        fetchAdminRequests();
        fetchRequests();
        fetchEmployees();
      } catch (err) {
        console.error(err);
      }
    }
  };

  // Allocation Handlers
  const handleOpenAllocation = (emp) => {
    setSelectedEmpProfile(emp);
    setNewAllocation(emp.allowed_leaves);
    setOpenAllocationModal(true);
  };

  const handleSaveAllocation = async (e) => {
    e.preventDefault();
    try {
      await api.patch(`/employees/${selectedEmpProfile.id}/`, {
        allowed_leaves: parseInt(newAllocation, 10)
      });
      setOpenAllocationModal(false);
      fetchEmployees();
    } catch (err) {
      console.error(err);
      alert('Failed to update leave allocation.');
    }
  };

  const getStatusChip = (req) => {
    const isPaidStr = req.status === 'APPROVED' ? ` (${req.is_paid ? 'Paid' : 'Unpaid'})` : '';
    switch (req.status) {
      case 'APPROVED': return <Chip label={`Approved${isPaidStr}`} color="success" size="small" sx={{ fontWeight: 600 }} />;
      case 'REJECTED': return <Chip label="Rejected" color="error" size="small" sx={{ fontWeight: 600 }} />;
      default: return <Chip label="Pending" color="warning" size="small" sx={{ fontWeight: 600 }} />;
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            Leave Planner
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Request absences, manage dynamic category rosters, and audit logs.
          </Typography>
        </Box>
        {isAdmin && (
          <Button 
            variant="outlined" 
            startIcon={<Settings size={18} />}
            onClick={() => setOpenCatModal(true)}
          >
            Manage Leave Categories
          </Button>
        )}
      </Box>

      {/* Simplified Employee Balance Cards */}
      {!isAdmin && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: '16px' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 700 }}>
                  Allowed Leaves (Yearly)
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 800, mt: 1 }}>
                  {user?.allowed_leaves !== null && user?.allowed_leaves !== undefined ? user.allowed_leaves : 12} <Typography component="span" variant="caption" color="text.secondary">days</Typography>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: '16px' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 700 }}>
                  Leaves Taken (Used)
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 800, mt: 1 }}>
                  {user?.used_leaves || 0} <Typography component="span" variant="caption" color="text.secondary">days</Typography>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card sx={{ borderRadius: '16px' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 700 }}>
                  Remaining Balance
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 800, mt: 1, color: '#9d4edd' }}>
                  {Math.max(0, (user?.allowed_leaves !== null && user?.allowed_leaves !== undefined ? user.allowed_leaves : 12) - (user?.used_leaves || 0))} <Typography component="span" variant="caption" color="text.secondary">days</Typography>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Grid container spacing={4}>
        {/* Request Form */}
        {!isAdmin && (
          <Grid item xs={12} md={5}>
            <Card sx={{ borderRadius: '16px' }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarRange size={20} /> Request Leave
                </Typography>

                {message && <Alert severity={message.type} sx={{ mb: 3, borderRadius: 2 }}>{message.text}</Alert>}

                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <Box component="form" onSubmit={handleSubmit}>
                    <TextField
                      select
                      fullWidth
                      label="Leave Category"
                      value={leaveType}
                      onChange={(e) => setLeaveType(e.target.value)}
                      sx={{ mb: 2.5 }}
                      required
                    >
                      {categories.length === 0 ? (
                        <MenuItem value="General Leave">General Leave</MenuItem>
                      ) : (
                        categories.map((cat) => (
                          <MenuItem key={cat.id} value={cat.name}>{cat.name}</MenuItem>
                        ))
                      )}
                    </TextField>

                    <Box sx={{ mb: 2.5 }}>
                      <DatePicker
                        label="Start Date"
                        format="DD/MM/YYYY"
                        value={startDate}
                        onChange={(newValue) => setStartDate(newValue)}
                        slotProps={{ textField: { fullWidth: true, size: 'medium', variant: 'outlined' } }}
                      />
                    </Box>

                    <Box sx={{ mb: 2.5 }}>
                      <DatePicker
                        label="End Date"
                        format="DD/MM/YYYY"
                        value={endDate}
                        onChange={(newValue) => setEndDate(newValue)}
                        slotProps={{ textField: { fullWidth: true, size: 'medium', variant: 'outlined' } }}
                      />
                    </Box>

                    <TextField
                      select
                      fullWidth
                      label="Duration Type"
                      value={durationType}
                      onChange={(e) => setDurationType(e.target.value)}
                      sx={{ mb: 2.5 }}
                    >
                      <MenuItem value="full_day">Full Day</MenuItem>
                      <MenuItem value="half_day">Half Day</MenuItem>
                      <MenuItem value="custom_hours">Custom Hours</MenuItem>
                    </TextField>

                    {durationType === 'custom_hours' && (
                      <TextField
                        fullWidth
                        type="number"
                        label="Custom Hours"
                        value={customHours}
                        onChange={(e) => setCustomHours(e.target.value)}
                        sx={{ mb: 2.5 }}
                        required
                        inputProps={{ step: 0.5, min: 0.5 }}
                      />
                    )}

                    <TextField

                      fullWidth
                      multiline
                      rows={3}
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
                    >
                      Submit Request
                    </Button>
                  </Box>
                </LocalizationProvider>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Requests Table Log */}
        <Grid item xs={12} md={!isAdmin ? 7 : 12}>
          <Card sx={{ borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Leave Requests Registry
              </Typography>
              
              <TableContainer component={Paper} elevation={0}>
                <Table>
                  <TableHead sx={{ bgcolor: 'background.neutral' }}>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Duration</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(isAdmin ? adminRequests : requests).length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 5 : 4} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No leave logs recorded.
                        </TableCell>
                      </TableRow>
                    ) : (
                      (isAdmin ? adminRequests : requests).map((req) => (
                        <TableRow key={req.id} hover>
                          {isAdmin && <TableCell sx={{ fontWeight: 600 }}>{req.employee_name}</TableCell>}
                          <TableCell>{req.leave_type}</TableCell>
                          <TableCell>
                            <div>{formatDate(req.start_date)} to {formatDate(req.end_date)}</div>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                              {req.duration_type === 'full_day' && 'Full Day'}
                              {req.duration_type === 'half_day' && 'Half Day'}
                              {req.duration_type === 'custom_hours' && `Custom Hours (${req.custom_hours} hrs)`}
                            </Typography>
                          </TableCell>
                          <TableCell>{getStatusChip(req)}</TableCell>
                          {isAdmin && (
                            <TableCell>
                              {req.status === 'PENDING' ? (
                                <Button 
                                  variant="contained" 
                                  size="small"
                                  onClick={() => openApprovalDialog(req)}
                                >
                                  Process
                                </Button>
                              ) : (
                                <Button 
                                  variant="outlined" 
                                  color="secondary"
                                  size="small"
                                  onClick={() => handleUnapproveRequest(req)}
                                >
                                  Revert Decision
                                </Button>
                              )}
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

        {/* Allowed Leaves Directory for Admin */}
        {isAdmin && (
          <Grid item xs={12}>
            <Card sx={{ borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                  Workforce Leave Allocations
                </Typography>

                <TableContainer component={Paper} elevation={0}>
                  <Table>
                    <TableHead sx={{ bgcolor: 'background.neutral' }}>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Allowed Leaves (Yearly)</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Leaves Taken (Used)</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Remaining Balance</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {employees.map((emp) => (
                        <TableRow key={emp.id} hover>
                          <TableCell sx={{ fontWeight: 600 }}>{emp.first_name} {emp.last_name} ({emp.username})</TableCell>
                          <TableCell>{emp.allowed_leaves} days</TableCell>
                          <TableCell>{emp.used_leaves} days</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>
                            {Math.max(0, emp.allowed_leaves - emp.used_leaves)} days
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="outlined" 
                              size="small" 
                              onClick={() => handleOpenAllocation(emp)}
                            >
                              Edit Allocation
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Category Manager Dialog */}
      <Dialog open={openCatModal} onClose={() => setOpenCatModal(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>Manage Leave Categories</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleAddCategory} sx={{ display: 'flex', gap: 1, mb: 3, mt: 1 }}>
            <TextField
              fullWidth
              size="small"
              label="New Category"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              placeholder="e.g. Maternity Leave"
            />
            <Button type="submit" variant="contained" startIcon={<Plus size={16} />}>
              Add
            </Button>
          </Box>
          <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 250 }}>
            <Table size="small">
              <TableBody>
                {categories.map((cat) => (
                  <TableRow key={cat.id}>
                    <TableCell sx={{ fontWeight: 600 }}>{cat.name}</TableCell>
                    <TableCell align="right">
                      <IconButton color="error" size="small" onClick={() => handleDeleteCategory(cat.id)}>
                        <Trash2 size={16} />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCatModal(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Review Dialog */}
      <Dialog open={openComments} onClose={() => setOpenComments(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Review Leave Request</DialogTitle>
        <DialogContent sx={{ minWidth: 350 }}>
          <Typography variant="body2" sx={{ mb: 2 }} color="text.secondary">
            Employee: <strong>{selectedReq?.employee_name}</strong>
            <br />
            Dates: <strong>{formatDate(selectedReq?.start_date)} to {formatDate(selectedReq?.end_date)}</strong>
            <br />
            Reason: "{selectedReq?.reason}"
          </Typography>
          
          <TextField
            fullWidth
            label="Manager Comments"
            multiline
            rows={3}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Checkbox 
                checked={isPaidApproved} 
                onChange={(e) => setIsPaidApproved(e.target.checked)} 
              />
            }
            label="Mark as Paid Leave (Deducts from employee leave balance)"
          />
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button onClick={handleReject} color="error" variant="outlined">
            Reject
          </Button>
          <Button onClick={handleApprove} color="success" variant="contained">
            Approve Request
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Allocation Dialog */}
      <Dialog open={openAllocationModal} onClose={() => setOpenAllocationModal(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Edit Leave Allocation</DialogTitle>
        <form onSubmit={handleSaveAllocation}>
          <DialogContent sx={{ minWidth: 350 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
              Employee: <strong>{selectedEmpProfile?.first_name} {selectedEmpProfile?.last_name} ({selectedEmpProfile?.username})</strong>
            </Typography>
            <TextField
              type="number"
              fullWidth
              label="Yearly Allowed Leaves"
              value={newAllocation}
              onChange={(e) => setNewAllocation(e.target.value)}
              required
            />
          </DialogContent>
          <DialogActions sx={{ p: 2, gap: 1 }}>
            <Button onClick={() => setOpenAllocationModal(false)} variant="outlined">Cancel</Button>
            <Button type="submit" variant="contained">Save</Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
