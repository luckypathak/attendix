import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, MenuItem,
  Checkbox, FormControlLabel, Switch, IconButton, Divider
} from '@mui/material';
import { UserPlus, Shield, Landmark, Calendar, Mail, User, Clock, Settings, Trash2, ArrowRightLeft } from 'lucide-react';
import api from '../services/api';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';

export default function Employees() {
  const { user } = useSelector((state) => state.auth);
  // Manager is only allowed to edit/process within their firm
  const isManager = user?.role === 'MANAGER';
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN';
  const hasEditRights = isAdmin || isManager;

  // List states
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Form Modal states
  const [openModal, setOpenModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('EMPLOYEE');
  const [baseSalary, setBaseSalary] = useState('45000');
  const [joiningDate, setJoiningDate] = useState(new Date().toISOString().split('T')[0]);
  
  // New Fields: Shift, Firm, PF
  const [shiftId, setShiftId] = useState('');
  const [firmId, setFirmId] = useState('');
  const [pfDeduction, setPfDeduction] = useState(false);
  const [shiftStartTime, setShiftStartTime] = useState('');
  const [shiftEndTime, setShiftEndTime] = useState('');
  const [allowedLeaves, setAllowedLeaves] = useState('12');
  const [pfType, setPfType] = useState('disabled');
  const [pfValue, setPfValue] = useState('');
  const [allocations, setAllocations] = useState([]);


  // Related dropdown collections
  const [shifts, setShifts] = useState([]);
  const [firms, setFirms] = useState([]);

  // Bulk Actions
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [openBulkTransferModal, setOpenBulkTransferModal] = useState(false);
  const [bulkTargetFirmId, setBulkTargetFirmId] = useState('');

  // Firm Manager Modal
  const [openFirmManagerModal, setOpenFirmManagerModal] = useState(false);
  const [newFirmName, setNewFirmName] = useState('');
  const [firmManagerLoading, setFirmManagerLoading] = useState(false);

  // Delete states
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [formLoading, setFormLoading] = useState(false);
  const [formMessage, setFormMessage] = useState(null);

  useEffect(() => {
    fetchEmployees();
    fetchFirms();
    fetchShifts();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.get('/employees/');
      setEmployees(res.data.results || res.data);
    } catch (e) {
      setErrorMsg('Failed to load employee list. Please ensure backend is active.');
    } finally {
      setLoading(false);
    }
  };

  const fetchFirms = async () => {
    try {
      const res = await api.get('/company/firms/');
      setFirms(res.data.results || res.data);
    } catch (e) {
      console.error('Failed to load firms', e);
    }
  };

  const fetchShifts = async () => {
    try {
      const res = await api.get('/attendance/shifts/');
      setShifts(res.data.results || res.data);
    } catch (e) {
      console.error('Failed to load shifts', e);
    }
  };

  const handleOpenModal = () => {
    if (isManager) {
      setFirmId(user?.firm_id || user?.firm || '');
    }
    setOpenModal(true);
    setFormMessage(null);
  };

  const handleEditClick = (emp) => {
    setEditingEmployee(emp);
    setUsername(emp.username);
    setEmail(emp.email);
    setFirstName(emp.first_name || '');
    setLastName(emp.last_name || '');
    setPassword('');
    setRole(emp.role);
    setBaseSalary(emp.base_salary);
    setJoiningDate(emp.joining_date);
    setFirmId(emp.firm_id || '');
    setAllowedLeaves(emp.allowed_leaves !== null && emp.allowed_leaves !== undefined ? String(emp.allowed_leaves) : '12');
    setPfDeduction(emp.pf_deduction || false);
    setPfType(emp.pf_type || 'disabled');
    setPfValue(emp.pf_value || '');
    setAllocations(emp.firm_allocations || []);
    if (emp.shift_start_time && emp.shift_end_time) {
      setShiftStartTime(emp.shift_start_time);
      setShiftEndTime(emp.shift_end_time);
      setShiftId('CUSTOM');
    } else {
      setShiftStartTime('');
      setShiftEndTime('');
      setShiftId(emp.shift_id || '');
    }
    setOpenModal(true);
    setFormMessage(null);
  };

  const handleDeleteClick = (emp) => {
    setEmployeeToDelete(emp);
    setOpenDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    setDeleteLoading(true);
    try {
      await api.delete(`/employees/${employeeToDelete.id}/`);
      setOpenDeleteDialog(false);
      fetchEmployees();
    } catch (err) {
      console.error("Delete employee error:", err);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setEditingEmployee(null);
    setUsername('');
    setEmail('');
    setFirstName('');
    setLastName('');
    setPassword('');
    setRole('EMPLOYEE');
    setBaseSalary('45000');
    setShiftId('');
    setFirmId(isManager ? (user?.firm_id || user?.firm || '') : '');
    setAllowedLeaves('12');
    setPfDeduction(false);
    setPfType('disabled');
    setPfValue('');
    setAllocations([]);
    setShiftStartTime('');
    setShiftEndTime('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormMessage(null);

    const payload = {
      username,
      email,
      first_name: firstName,
      last_name: lastName,
      role,
      base_salary: parseFloat(baseSalary),
      joining_date: joiningDate,
      shift_id: (shiftId && shiftId !== 'CUSTOM') ? parseInt(shiftId) : null,
      shift_start_time: shiftId === 'CUSTOM' ? shiftStartTime : null,
      shift_end_time: shiftId === 'CUSTOM' ? shiftEndTime : null,
      firm_id: firmId ? parseInt(firmId) : null,
      pf_deduction: pfType !== 'disabled',
      pf_type: pfType,
      pf_value: pfType !== 'disabled' && pfValue !== '' ? parseFloat(pfValue) : 0.0,
      firm_allocations: allocations.map(a => ({
        firm: a.firm,
        base_salary: parseFloat(a.base_salary) || 0.0,
        pf_type: a.pf_type,
        pf_value: parseFloat(a.pf_value) || 0.0
      })),
      allowed_leaves: (allowedLeaves !== '' && !isNaN(parseInt(allowedLeaves, 10))) ? parseInt(allowedLeaves, 10) : 12
    };

    if (password) {
      payload.password = password;
    }

    try {
      if (editingEmployee) {
        await api.patch(`/employees/${editingEmployee.id}/`, payload);
        setFormMessage({ type: 'success', text: 'Workforce member updated successfully!' });
      } else {
        await api.post('/employees/', payload);
        setFormMessage({ type: 'success', text: 'Workforce member registered successfully!' });
      }
      fetchEmployees();
      setTimeout(() => {
        handleCloseModal();
      }, 1200);
    } catch (err) {
      const errMsg = err.response?.data ? JSON.stringify(err.response.data) : 'Failed to save workforce member.';
      setFormMessage({ type: 'error', text: errMsg });
    } finally {
      setFormLoading(false);
    }
  };

  // Bulk Actions Handlers
  const handleToggleSelect = (id) => {
    if (selectedEmployees.includes(id)) {
      setSelectedEmployees(selectedEmployees.filter(item => item !== id));
    } else {
      setSelectedEmployees([...selectedEmployees, id]);
    }
  };

  const handleSelectAll = () => {
    if (selectedEmployees.length === employees.length) {
      setSelectedEmployees([]);
    } else {
      setSelectedEmployees(employees.map(emp => emp.id));
    }
  };

  const handleBulkTransferSubmit = async () => {
    try {
      await api.post('/employees/bulk-transfer/', {
        employee_ids: selectedEmployees,
        firm_id: bulkTargetFirmId ? parseInt(bulkTargetFirmId) : null
      });
      setOpenBulkTransferModal(false);
      setSelectedEmployees([]);
      setBulkTargetFirmId('');
      fetchEmployees();
    } catch (err) {
      console.error(err);
    }
  };

  // Firms directory handlers
  const handleCreateFirm = async (e) => {
    e.preventDefault();
    if (!newFirmName) return;
    setFirmManagerLoading(true);
    try {
      await api.post('/company/firms/', { name: newFirmName });
      setNewFirmName('');
      fetchFirms();
    } catch (err) {
      console.error(err);
    } finally {
      setFirmManagerLoading(false);
    }
  };

  const handleDeleteFirm = async (id) => {
    if (window.confirm("Are you sure you want to delete this firm branch?")) {
      try {
        await api.delete(`/company/firms/${id}/`);
        fetchFirms();
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            Workforce Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View profiles, shifts, allocate branches, toggle PF deductions, and manage credentials.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          {isAdmin && (
            <Button 
              variant="outlined" 
              startIcon={<Settings size={18} />}
              onClick={() => setOpenFirmManagerModal(true)}
            >
              Firms Directory
            </Button>
          )}
          {hasEditRights && (
            <Button 
              variant="contained" 
              startIcon={<UserPlus size={18} />}
              onClick={handleOpenModal}
            >
              Add Member
            </Button>
          )}
        </Box>
      </Box>

      {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}

      {/* Bulk action bar */}
      {selectedEmployees.length > 0 && isAdmin && (
        <Alert 
          severity="info" 
          sx={{ mb: 3, borderRadius: 2, display: 'flex', alignItems: 'center' }}
          action={
            <Button 
              variant="contained" 
              color="primary" 
              size="small" 
              startIcon={<ArrowRightLeft size={16} />}
              onClick={() => setOpenBulkTransferModal(true)}
            >
              Transfer Selected ({selectedEmployees.length})
            </Button>
          }
        >
          Workforce Selection: {selectedEmployees.length} members checked.
        </Alert>
      )}

      <Card>
        <CardContent sx={{ p: 0 }}>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  {isAdmin && (
                    <TableCell padding="checkbox">
                      <Checkbox 
                        checked={selectedEmployees.length === employees.length && employees.length > 0} 
                        onChange={handleSelectAll} 
                      />
                    </TableCell>
                  )}
                  <TableCell sx={{ fontWeight: 700 }}>Username</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Full Name</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Firm / Branch</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Shift timing</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>PF Deduction</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Role</TableCell>
                  {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Base Salary (₹)</TableCell>}
                  {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Hourly Rate (₹)</TableCell>}
                  {hasEditRights && <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={isAdmin ? 10 : 9} align="center" sx={{ py: 6 }}>
                      <CircularProgress size={32} />
                    </TableCell>
                  </TableRow>
                ) : employees.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={isAdmin ? 10 : 9} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                      No workforce members recorded. Click 'Add Member' to register.
                    </TableCell>
                  </TableRow>
                ) : (
                  employees.map((emp) => (
                    <TableRow key={emp.id} hover>
                      {isAdmin && (
                        <TableCell padding="checkbox">
                          <Checkbox 
                            checked={selectedEmployees.includes(emp.id)} 
                            onChange={() => handleToggleSelect(emp.id)} 
                          />
                        </TableCell>
                      )}
                      <TableCell sx={{ fontWeight: 600 }}>{emp.username}</TableCell>
                      <TableCell>{emp.first_name || '--'} {emp.last_name || ''}</TableCell>
                      <TableCell>
                        <Chip 
                          label={emp.firm_name || 'No Branch'} 
                          size="small" 
                          variant="outlined"
                          color={emp.firm_name ? "primary" : "default"}
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={emp.shift_name ? `${emp.shift_name} (${emp.shift_start_time} - ${emp.shift_end_time})` : 'Standard (8h)'} 
                          size="small"
                          icon={<Clock size={12} />}
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }} 
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={emp.pf_deduction ? "12% PF Enabled" : "No PF"} 
                          size="small" 
                          color={emp.pf_deduction ? "success" : "default"}
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={emp.role} 
                          size="small" 
                          color={emp.role === 'SUPER_ADMIN' || emp.role === 'COMPANY_ADMIN' ? 'secondary' : 'default'} 
                          sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                        />
                      </TableCell>
                      {isAdmin && <TableCell sx={{ fontWeight: 600 }}>₹{parseFloat(emp.base_salary).toLocaleString('en-IN')}</TableCell>}
                      {isAdmin && <TableCell>₹{parseFloat(emp.hourly_rate).toFixed(2)}/hr</TableCell>}
                      {hasEditRights && (
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button 
                              variant="outlined" 
                              size="small"
                              onClick={() => handleEditClick(emp)}
                            >
                              Edit
                            </Button>
                            {isAdmin && (
                              <Button 
                                variant="outlined" 
                                color="error"
                                size="small"
                                onClick={() => handleDeleteClick(emp)}
                              >
                                Delete
                              </Button>
                            )}
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

      {/* Add/Edit Employee Modal */}
      <Dialog open={openModal} onClose={handleCloseModal} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {editingEmployee ? 'Edit Workforce Member' : 'Register New Workforce Member'}
        </DialogTitle>
        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {formMessage && <Alert severity={formMessage.type} sx={{ borderRadius: 2 }}>{formMessage.text}</Alert>}
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={editingEmployee ? "New Password (Optional)" : "Password"}
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required={!editingEmployee}
                />
              </Grid>
              {!isManager && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="Role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    required
                  >
                    <MenuItem value="EMPLOYEE">Employee</MenuItem>
                    <MenuItem value="MANAGER">Manager</MenuItem>
                    <MenuItem value="COMPANY_ADMIN">Company Admin</MenuItem>
                  </TextField>
                </Grid>
              )}

              {!isManager && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="Firm / Branch"
                    value={firmId}
                    onChange={(e) => setFirmId(e.target.value)}
                  >
                    <MenuItem value=""><em>None (No Branch)</em></MenuItem>
                    {firms.map((f) => (
                      <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
              )}

              {/* Shift Timing Selection */}
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  fullWidth
                  label="Shift timing"
                  value={shiftId}
                  onChange={(e) => setShiftId(e.target.value)}
                >
                  <MenuItem value=""><em>None (Standard 8h)</em></MenuItem>
                  <MenuItem value="CUSTOM"><em>Custom Shift (Enter manually)</em></MenuItem>
                  {shifts.map((s) => (
                    <MenuItem key={s.id} value={s.id}>{s.name} ({s.start_time.substring(0, 5)} - {s.end_time.substring(0, 5)})</MenuItem>
                  ))}
                </TextField>
              </Grid>

              {shiftId === 'CUSTOM' && (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Shift Start Time"
                      type="time"
                      InputLabelProps={{ shrink: true }}
                      value={shiftStartTime}
                      onChange={(e) => setShiftStartTime(e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Shift End Time"
                      type="time"
                      InputLabelProps={{ shrink: true }}
                      value={shiftEndTime}
                      onChange={(e) => setShiftEndTime(e.target.value)}
                      required
                    />
                  </Grid>
                </>
              )}

              {isAdmin && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Base Monthly Salary (₹)"
                    type="number"
                    value={baseSalary}
                    onChange={(e) => setBaseSalary(e.target.value)}
                    required
                  />
                </Grid>
              )}
              
              <Grid item xs={12} sm={6}>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                  <DatePicker
                    label="Joining Date"
                    value={joiningDate ? dayjs(joiningDate) : null}
                    onChange={(newValue) => setJoiningDate(newValue ? newValue.format('YYYY-MM-DD') : '')}
                    slotProps={{ textField: { fullWidth: true } }}
                  />
                </LocalizationProvider>
              </Grid>

              {!isManager && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    type="number"
                    fullWidth
                    label="Allowed Leaves (Yearly)"
                    value={allowedLeaves}
                    onChange={(e) => setAllowedLeaves(e.target.value)}
                  />
                </Grid>
              )}

              {/* PF Configuration */}
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  fullWidth
                  label="PF Calculation Type"
                  value={pfType}
                  onChange={(e) => setPfType(e.target.value)}
                >
                  <MenuItem value="disabled">Disabled</MenuItem>
                  <MenuItem value="flat">Flat Amount</MenuItem>
                  <MenuItem value="percentage">Percentage</MenuItem>
                </TextField>
              </Grid>

              {pfType !== 'disabled' && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    type="number"
                    fullWidth
                    label={pfType === 'flat' ? "PF Flat Amount (₹)" : "PF Percentage (%)"}
                    value={pfValue}
                    onChange={(e) => setPfValue(e.target.value)}
                  />
                </Grid>
              )}

              {/* Branch Allocations Section */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 700, mb: 1 }}>
                  Branch-wise Salary Allocation / Splits
                </Typography>
                
                {allocations.map((alloc, idx) => {
                  const firmName = firms.find(f => f.id === alloc.firm)?.name || 'Default';
                  return (
                    <Box key={idx} sx={{ p: 2, mb: 2, border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
                      <Typography sx={{ minWidth: 120, fontWeight: 600, fontSize: '0.85rem' }}>{firmName}</Typography>
                      
                      <TextField
                        type="number"
                        label="Base Salary"
                        size="small"
                        value={alloc.base_salary}
                        onChange={(e) => {
                          const updated = [...allocations];
                          updated[idx].base_salary = parseFloat(e.target.value) || 0;
                          setAllocations(updated);
                        }}
                        sx={{ width: 130 }}
                      />

                      <TextField
                        select
                        label="PF Type"
                        size="small"
                        value={alloc.pf_type}
                        onChange={(e) => {
                          const updated = [...allocations];
                          updated[idx].pf_type = e.target.value;
                          setAllocations(updated);
                        }}
                        sx={{ width: 120 }}
                      >
                        <MenuItem value="disabled">Disabled</MenuItem>
                        <MenuItem value="flat">Flat Amount</MenuItem>
                        <MenuItem value="percentage">Percentage</MenuItem>
                      </TextField>

                      {alloc.pf_type !== 'disabled' && (
                        <TextField
                          type="number"
                          label="PF Value"
                          size="small"
                          value={alloc.pf_value}
                          onChange={(e) => {
                            const updated = [...allocations];
                            updated[idx].pf_value = parseFloat(e.target.value) || 0;
                            setAllocations(updated);
                          }}
                          sx={{ width: 100 }}
                        />
                      )}

                      <Button
                        color="error"
                        size="small"
                        onClick={() => {
                          setAllocations(allocations.filter((_, i) => i !== idx));
                        }}
                      >
                        Remove
                      </Button>
                    </Box>
                  );
                })}

                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mt: 2 }}>
                  <TextField
                    select
                    label="Add to Branch"
                    size="small"
                    value=""
                    onChange={(e) => {
                      const fId = parseInt(e.target.value);
                      if (!allocations.find(a => a.firm === fId)) {
                        setAllocations([...allocations, { firm: fId, base_salary: 0, pf_type: 'disabled', pf_value: 0 }]);
                      }
                    }}
                    sx={{ minWidth: 200 }}
                  >
                    <MenuItem value="" disabled>Select Branch...</MenuItem>
                    {firms.map(f => (
                      <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                    ))}
                  </TextField>
                  <Typography variant="caption" color="text.secondary">
                    Add branch splits if employee splits shifts or duties.
                  </Typography>
                </Box>
              </Grid>
            </Grid>

          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={handleCloseModal} variant="outlined" disabled={formLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={formLoading}>
              {formLoading ? <CircularProgress size={24} /> : (editingEmployee ? 'Save Changes' : 'Register Member')}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Delete Employee Prompt */}
      <Dialog open={openDeleteDialog} onClose={() => setOpenDeleteDialog(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Remove Workforce Member</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove <strong>{employeeToDelete?.username}</strong>? This action softly deletes the account and stops check-ins.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOpenDeleteDialog(false)} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained" disabled={deleteLoading}>
            {deleteLoading ? <CircularProgress size={24} /> : 'Delete Profile'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Transfer Dialog */}
      <Dialog open={openBulkTransferModal} onClose={() => setOpenBulkTransferModal(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Transfer Selected Members</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography variant="body2" sx={{ mb: 3, color: 'text.secondary' }}>
            Choose a target firm/branch to transfer the selected {selectedEmployees.length} workforce members to:
          </Typography>
          <TextField
            select
            fullWidth
            label="Target Firm / Branch"
            value={bulkTargetFirmId}
            onChange={(e) => setBulkTargetFirmId(e.target.value)}
          >
            <MenuItem value=""><em>Remove from Firm (Clear)</em></MenuItem>
            {firms.map((f) => (
              <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setOpenBulkTransferModal(false)} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleBulkTransferSubmit} variant="contained" color="primary">
            Confirm Transfer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Firm Manager Modal */}
      <Dialog open={openFirmManagerModal} onClose={() => setOpenFirmManagerModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Firms Directory Management</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
          {/* Create form */}
          <Box component="form" onSubmit={handleCreateFirm} sx={{ display: 'flex', gap: 1.5, mt: 1 }}>
            <TextField
              fullWidth
              size="small"
              label="New Firm Name"
              placeholder="e.g. Attendix Branch A"
              value={newFirmName}
              onChange={(e) => setNewFirmName(e.target.value)}
              required
            />
            <Button type="submit" variant="contained" disabled={firmManagerLoading}>
              Add Branch
            </Button>
          </Box>

          <Typography variant="subtitle2" sx={{ fontWeight: 700, mt: 1 }}>
            Existing Firms & Branches
          </Typography>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Firm Name</TableCell>
                  <TableCell sx={{ fontWeight: 700 }} align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {firms.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={2} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                      No firm branches configured.
                    </TableCell>
                  </TableRow>
                ) : (
                  firms.map((f) => (
                    <TableRow key={f.id}>
                      <TableCell sx={{ fontWeight: 600 }}>{f.name}</TableCell>
                      <TableCell align="right">
                        <IconButton size="small" color="error" onClick={() => handleDeleteFirm(f.id)}>
                          <Trash2 size={16} />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setOpenFirmManagerModal(false)} variant="contained">
            Close Directory
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
