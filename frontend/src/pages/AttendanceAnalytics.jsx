import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import {
  Box, Card, CardContent, Grid, Button, Typography,
  TextField, MenuItem, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip,
  CircularProgress, Alert, IconButton, Tooltip, Collapse,
  Divider, InputAdornment
} from '@mui/material';
import {
  Calendar, MapPin, User, Building, Clock, ChevronDown,
  ChevronUp, Search, RefreshCw, BarChart2, Eye
} from 'lucide-react';
import api, { getMediaUrl } from '../services/api';
import { formatDate } from '../utils/format';
import EditAttendanceModal from '../components/EditAttendanceModal';
import { Edit2 } from 'lucide-react';

export default function AttendanceAnalytics() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [analyticsData, setAnalyticsData] = useState([]);

  // Filter dropdown lists
  const [employees, setEmployees] = useState([]);
  const [branches, setBranches] = useState([]);

  // Filters State
  const [selectedEmployee, setSelectedEmployee] = useState('ALL');
  const [selectedBranch, setSelectedBranch] = useState('ALL');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Row expansion state
  const [expandedEmployeeId, setExpandedEmployeeId] = useState(null);

  // Edit Modal State
  const [editSession, setEditSession] = useState(null);

  useEffect(() => {
    if (selectedFirm && selectedFirm !== 'ALL') {
      setSelectedBranch(parseInt(selectedFirm));
    } else {
      setSelectedBranch('ALL');
    }
    fetchFilterOptions();
  }, [selectedFirm]);

  useEffect(() => {
    fetchAnalytics();
  }, [selectedBranch]);

  const fetchFilterOptions = async () => {
    try {
      const [empRes, branchRes] = await Promise.all([
        api.get('/employees/', { params: { firm: selectedFirm } }),
        api.get('/company/firms/')
      ]);
      setEmployees(empRes.data.results || empRes.data);
      setBranches(branchRes.data.results || branchRes.data);
    } catch (e) {
      console.error("Failed to load filters data", e);
    }
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const params = {};
      if (selectedEmployee !== 'ALL') params.employee = selectedEmployee;
      if (selectedBranch !== 'ALL') params.branch = selectedBranch;
      if (selectedMonth) params.month = selectedMonth;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const res = await api.get('/attendance/records/analytics/', { params });
      setAnalyticsData(res.data);
    } catch (e) {
      console.error(e);
      setErrorMsg("Failed to load attendance analytics.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setSelectedEmployee('ALL');
    setSelectedBranch('ALL');
    setSelectedMonth('');
    setStartDate('');
    setEndDate('');
    setExpandedEmployeeId(null);
  };

  const toggleRowExpand = (empId) => {
    if (expandedEmployeeId === empId) {
      setExpandedEmployeeId(null);
    } else {
      setExpandedEmployeeId(empId);
    }
  };

  const getStatusChipColor = (status) => {
    switch (status) {
      case 'PRESENT': return 'success';
      case 'LATE': return 'warning';
      case 'HALF_DAY': return 'error';
      case 'LEAVE': return 'primary';
      case 'HOLIDAY': return 'secondary';
      default: return 'default';
    }
  };

  // Calculate high-level summary cards totals across all returned employees
  const totalPresent = analyticsData.reduce((sum, row) => sum + row.present_days, 0);
  const totalAbsent = analyticsData.reduce((sum, row) => sum + row.absent_days, 0);
  const totalLeave = analyticsData.reduce((sum, row) => sum + row.leave_days, 0);
  const totalHoursWorked = analyticsData.reduce((sum, row) => sum + row.total_working_hours, 0);
  const totalBreakHours = analyticsData.reduce((sum, row) => sum + row.total_break_hours, 0);
  const totalOvertimeHours = analyticsData.reduce((sum, row) => sum + row.total_overtime_hours, 0);

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            Attendance Analytics & Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive audit dashboard for working hours, session details, overtime, and leave logs.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshCw size={16} />}
          onClick={fetchAnalytics}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Filters Card */}
      <Card sx={{ mb: 4, borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Search size={18} /> Filter Records
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2.4}>
              <TextField
                select
                fullWidth
                label="Employee"
                size="small"
                value={selectedEmployee}
                onChange={(e) => setSelectedEmployee(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <User size={16} color="#94a3b8" />
                    </InputAdornment>
                  )
                }}
              >
                <MenuItem value="ALL">All Employees</MenuItem>
                {employees.map((emp) => (
                  <MenuItem key={emp.id} value={emp.user_id}>{emp.username}</MenuItem>
                ))}
              </TextField>
            </Grid>

            {user?.role !== 'MANAGER' && (
              <Grid item xs={12} sm={6} md={2.4}>
                <TextField
                  select
                  fullWidth
                  label="Branch (Firm)"
                  size="small"
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Building size={16} color="#94a3b8" />
                      </InputAdornment>
                    )
                  }}
                >
                  <MenuItem value="ALL">All Branches</MenuItem>
                  {branches.map((b) => (
                    <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>
            )}

            <Grid item xs={12} sm={6} md={2.4}>
              <TextField
                type="month"
                fullWidth
                label="Month"
                size="small"
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setStartDate('');
                  setEndDate('');
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={2.4}>
              <TextField
                type="date"
                fullWidth
                label="Start Date"
                size="small"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setSelectedMonth('');
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={2.4}>
              <TextField
                type="date"
                fullWidth
                label="End Date"
                size="small"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setSelectedMonth('');
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12} md={user?.role !== 'MANAGER' ? 12 : 2.4} sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: { md: 0 } }}>
              <Button variant="contained" size="medium" onClick={fetchAnalytics} disabled={loading}>
                Apply
              </Button>
              <Button variant="outlined" size="medium" color="secondary" onClick={handleResetFilters}>
                Reset
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(76, 175, 80, 0.05)', border: '1px solid rgba(76, 175, 80, 0.15)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="success.main" sx={{ fontWeight: 700 }}>Total Present</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalPresent} days</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(244, 67, 54, 0.05)', border: '1px solid rgba(244, 67, 54, 0.15)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="error.main" sx={{ fontWeight: 700 }}>Total Absent</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalAbsent} days</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(33, 150, 243, 0.05)', border: '1px solid rgba(33, 150, 243, 0.15)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="primary.main" sx={{ fontWeight: 700 }}>On Leave</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalLeave} days</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>Working Hours</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalHoursWorked.toFixed(1)} hrs</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>Total Breaks</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalBreakHours.toFixed(1)} hrs</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4} md={2}>
          <Card sx={{ borderRadius: '12px', bgcolor: 'rgba(157, 78, 221, 0.05)', border: '1px solid rgba(157, 78, 221, 0.15)' }}>
            <CardContent sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="#9d4edd" sx={{ fontWeight: 700 }}>Total Overtime</Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, mt: 0.5 }}>{totalOvertimeHours.toFixed(1)} hrs</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Aggregated Table */}
      {errorMsg && <Alert severity="error" sx={{ mb: 3 }}>{errorMsg}</Alert>}

      <Card sx={{ borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            <Box sx={{ py: 8, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>
          ) : analyticsData.length === 0 ? (
            <Box sx={{ py: 6, textAlign: 'center', color: 'text.secondary' }}>No analytics records found for chosen filters.</Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead sx={{ bgcolor: 'background.neutral' }}>
                  <TableRow>
                    <TableCell width="50" />
                    <TableCell sx={{ fontWeight: 700, py: 1.5 }}>Employee</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Branch</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Present</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Absent</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>On Leave</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Work Hours</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Break Hours</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Overtime</TableCell>
                    <TableCell sx={{ fontWeight: 700 }} align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analyticsData.map((row) => {
                    const isExpanded = expandedEmployeeId === row.employee_id;
                    return (
                      <React.Fragment key={row.employee_id}>
                        <TableRow hover sx={{ '& > *': { borderBottom: 'unset' } }}>
                          <TableCell>
                            <IconButton size="small" onClick={() => toggleRowExpand(row.employee_id)}>
                              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </IconButton>
                          </TableCell>
                          <TableCell sx={{ fontWeight: 700, py: 1.5 }}>
                            {row.employee_first_name ? `${row.employee_first_name} ${row.employee_last_name}` : row.employee_username}
                          </TableCell>
                          <TableCell>{row.branch_name}</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: 'success.main' }}>{row.present_days} days</TableCell>
                          <TableCell sx={{ fontWeight: 600, color: 'error.main' }}>{row.absent_days} days</TableCell>
                          <TableCell>{row.leave_days} days</TableCell>
                          <TableCell>{row.total_working_hours} hrs</TableCell>
                          <TableCell>{row.total_break_hours} hrs</TableCell>
                          <TableCell sx={{ color: '#9d4edd', fontWeight: 600 }}>{row.total_overtime_hours} hrs</TableCell>
                          <TableCell align="right">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<Eye size={14} />}
                              onClick={() => toggleRowExpand(row.employee_id)}
                              sx={{ fontSize: '0.75rem' }}
                            >
                              {isExpanded ? 'Hide Logs' : 'View Logs'}
                            </Button>
                          </TableCell>
                        </TableRow>

                        {/* Collapsible logs list */}
                        <TableRow>
                          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                              <Box sx={{ margin: 2, p: 2, bgcolor: 'background.default', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <Typography variant="subtitle2" gutterBottom component="div" sx={{ fontWeight: 700, mb: 2, color: 'primary.main' }}>
                                  Daily Attendance & Punch Logs for {row.employee_username}
                                </Typography>
                                {row.records.length === 0 ? (
                                  <Typography variant="body2" color="text.secondary">No daily attendance logs matching the dates.</Typography>
                                ) : (
                                  <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                    <Table size="small">
                                      <TableHead sx={{ bgcolor: 'background.neutral' }}>
                                        <TableRow>
                                          <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>Photo</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>Clock In / Out</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>Multiple Sessions</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>Hours (Work / Break / OT)</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>GPS Address info</TableCell>
                                          <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {row.records.map((rec) => (
                                          <TableRow key={rec.id} hover>
                                            <TableCell sx={{ fontWeight: 600 }}>{formatDate(rec.date)}</TableCell>
                                            <TableCell>
                                              {rec.captured_image ? (
                                                <Tooltip title="Click to open image in new tab">
                                                  <img
                                                    src={getMediaUrl(rec.captured_image)}
                                                    alt="identity"
                                                    style={{ width: 44, height: 44, borderRadius: '6px', objectFit: 'cover', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)' }}
                                                    onClick={() => window.open(getMediaUrl(rec.captured_image), '_blank')}
                                                  />
                                                </Tooltip>
                                              ) : '--'}
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="body2">📥 <strong>In:</strong> {rec.check_in_time || '--'}</Typography>
                                              <Typography variant="body2">📤 <strong>Out:</strong> {rec.check_out_time || '--'}</Typography>
                                            </TableCell>
                                            <TableCell>
                                              {rec.sessions && rec.sessions.length > 0 ? (
                                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                  {rec.sessions.map((s, idx) => (
                                                    <Box key={s.id} sx={{ display: 'flex', alignItems: 'center', gap: 2, bgcolor: 'rgba(255,255,255,0.02)', p: 1, borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                                      <Box>
                                                        <Typography variant="caption" sx={{ display: 'block', fontWeight: 700 }}>
                                                          S{idx + 1}: {s.check_in_time} - {s.check_out_time || 'Active'}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                          Work: {s.working_hours || '--'}
                                                        </Typography>
                                                      </Box>
                                                      <Box sx={{ display: 'flex', gap: 1, flexGrow: 1, justifyContent: 'flex-end' }}>
                                                        <IconButton size="small" onClick={() => setEditSession({ ...s, parent_status: rec.status })}>
                                                          <Edit2 size={14} color="#94a3b8" />
                                                        </IconButton>
                                                        {s.captured_image && (
                                                          <Tooltip title="Check In Photo">
                                                            <img
                                                              src={getMediaUrl(s.captured_image)}
                                                              alt="In"
                                                              style={{ width: 28, height: 28, borderRadius: '4px', objectFit: 'cover', cursor: 'pointer' }}
                                                              onClick={() => window.open(getMediaUrl(s.captured_image), '_blank')}
                                                            />
                                                          </Tooltip>
                                                        )}
                                                        {s.check_out_captured_image && (
                                                          <Tooltip title="Check Out Photo">
                                                            <img
                                                              src={getMediaUrl(s.check_out_captured_image)}
                                                              alt="Out"
                                                              style={{ width: 28, height: 28, borderRadius: '4px', objectFit: 'cover', cursor: 'pointer' }}
                                                              onClick={() => window.open(getMediaUrl(s.check_out_captured_image), '_blank')}
                                                            />
                                                          </Tooltip>
                                                        )}
                                                      </Box>
                                                    </Box>
                                                  ))}
                                                </Box>
                                              ) : (
                                                <Typography variant="caption" color="text.secondary">Single session / legacy</Typography>
                                              )}
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="body2">💼 <strong>Work:</strong> {rec.total_worked_hours} hrs</Typography>
                                              <Typography variant="body2">☕ <strong>Break:</strong> {rec.break_hours} hrs</Typography>
                                              <Typography variant="body2" sx={{ color: '#9d4edd' }}>⚡ <strong>OT:</strong> {rec.overtime_hours} hrs</Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="caption" sx={{ display: 'block', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }} title={rec.check_in_address}>
                                                <strong>In:</strong> {rec.check_in_address || '--'}
                                              </Typography>
                                              <Typography variant="caption" sx={{ display: 'block', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }} title={rec.check_out_address}>
                                                <strong>Out:</strong> {rec.check_out_address || '--'}
                                              </Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Chip
                                                label={rec.status}
                                                size="small"
                                                color={getStatusChipColor(rec.status)}
                                                sx={{ fontWeight: 700, fontSize: '0.7rem' }}
                                              />
                                            </TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                )}
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      <EditAttendanceModal
        open={Boolean(editSession)}
        onClose={() => setEditSession(null)}
        session={editSession}
        onSaved={fetchAnalytics}
      />
    </Box>
  );
}
