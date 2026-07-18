import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { 
  Grid, Card, CardContent, Typography, Box, Button, 
  Chip, Avatar, CircularProgress, Dialog, DialogTitle, DialogContent, Accordion, AccordionSummary, AccordionDetails, Table, TableBody, TableCell, TableHead, TableRow, TableContainer, Paper, IconButton 
} from '@mui/material';
import { 
  Users, CheckCircle2, AlertTriangle, FileText, 
  ArrowUpRight, Clock, ClipboardList, Wallet, MonitorOff,
  Banknote, Receipt, Hourglass, ChevronDown, X
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

export default function Dashboard() {
  const { user } = useSelector((state) => state.auth);
  const navigate = useNavigate();
  const { selectedFirm } = useOutletContext();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';
  
  const [stats, setStats] = useState({
    totalEmployees: 0,
    attendance: { present: 0, absent: 0, half_day: 0, late: 0, auto_checkouts_today: 0, auto_checkouts_month: 0, top_auto_checkouts: [] },
    leaves: { pending: 0, approved: 0, rejected: 0 },
    overtime: { pending: 0, approved: 0, rejected: 0 },
    reimbursements: { paid: 0, pending: 0, this_month: 0, graph: [] },
    advance_salary: { given: 0, pending_recovery: 0, recovered_this_month: 0 },
    payroll: { processed: 0, pending: 0 }
  });

  const [employeeDashboard, setEmployeeDashboard] = useState({
    checkedInTime: 'Pending',
    checkedOutTime: 'Pending',
    taskCompleteness: 'No Tasks Assigned',
    remainingLeaves: '0 Days Left',
  });

  const [loading, setLoading] = useState(true);
  const [autoCheckoutModalOpen, setAutoCheckoutModalOpen] = useState(false);
  const [attendanceData, setAttendanceData] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      fetchDashboardData(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [isAdmin, selectedFirm]);

  const fetchDashboardData = async (isPolling = false) => {
    if (!isPolling) setLoading(true);
    try {
      const statsRes = await api.get('/company/dashboard-stats/', { params: { firm: selectedFirm } });
      const statsData = statsRes.data.stats;
      if (isAdmin) {
        setStats(statsData);
        if (statsRes.data.trends) {
          setAttendanceData(statsRes.data.trends);
        }
      } else {
        setEmployeeDashboard({
          status: statsData?.attendance?.status || 'Pending',
          checkedInTime: statsData?.attendance?.checked_in_time || 'Pending',
          checkedOutTime: statsData?.attendance?.checked_out_time || 'Pending',
          taskCompleteness: statsData?.tasks?.completeness || 'No Tasks Assigned',
          remainingLeaves: statsData?.leaves?.remaining || '0 Days Left',
        });
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
  };

  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Welcome back, {user?.first_name || user?.username}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here is your summary for today, {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
      ) : isAdmin ? (
        // ==========================================
        // ADMIN DASHBOARD
        // ==========================================
        <Grid container spacing={3}>
          {/* Attendance Overview */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Attendance</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={2}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', bgcolor: 'rgba(0, 245, 212, 0.05)' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Present</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'success.main' }}>{stats?.attendance?.present ?? 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', bgcolor: 'rgba(255, 159, 67, 0.05)' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Late</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'warning.main' }}>{stats?.attendance?.late ?? 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', bgcolor: 'rgba(231, 76, 60, 0.05)' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Absent</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'error.main' }}>{stats?.attendance?.absent ?? 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', bgcolor: 'rgba(157, 78, 221, 0.05)' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Half Day</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main' }}>{stats?.attendance?.half_day ?? 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Auto Checkouts */}
              <Grid item xs={12} sm={12} md={4}>
                <Card onClick={() => setAutoCheckoutModalOpen(true)} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s', background: 'linear-gradient(135deg, rgba(231, 76, 60, 0.05) 0%, rgba(255, 159, 67, 0.05) 100%)' }}>
                  <CardContent sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <MonitorOff size={18} color="#e74c3c" />
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Auto Checkouts</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="h4" sx={{ fontWeight: 800, color: '#e74c3c' }}>{stats?.attendance?.auto_checkouts_today ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">Today</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats?.attendance?.auto_checkouts_yesterday ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">Yesterday</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats?.attendance?.auto_checkouts_month ?? 0}</Typography>
                        <Typography variant="caption" color="text.secondary">This Month</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Top Auto Checkout Employees */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Top Auto Checkouts</Typography>
                {(stats?.attendance?.top_auto_checkouts || []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No auto checkouts this month.</Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    {(stats?.attendance?.top_auto_checkouts || []).map((item, index) => (
                      <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1.5, bgcolor: 'background.default', borderRadius: 2 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{item.attendance__employee__username}</Typography>
                        <Chip label={`${item.count} times`} size="small" color="error" variant="outlined" />
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>


          {/* Auto Checkout History Table */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Recent Auto Checkouts History</Typography>
                {(stats?.attendance?.history || []).length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No recent auto checkouts found.</Typography>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.1)' }}>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Shift</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Checkout Time</TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>Reason</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(stats?.attendance?.history || []).map((row, idx) => (
                          <TableRow key={idx} hover>
                            <TableCell sx={{ fontWeight: 600 }}>{row.employee}</TableCell>
                            <TableCell>{row.date}</TableCell>
                            <TableCell>{row.shift}</TableCell>
                            <TableCell>{row.checkout_time || '--'}</TableCell>
                            <TableCell>
                              <Chip size="small" color={row.reason === 'AUTO_CHECKOUT_TIMEOUT' ? 'error' : row.reason === 'ADMIN_REJECTED_AUTO_CHECKOUT' ? 'warning' : 'default'} label={row.reason.replace(/_/g, ' ')} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Reimbursements Analytics */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Reimbursement Analytics</Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={4}>
                    <Box onClick={() => navigate('/reimbursements')} sx={{ cursor: 'pointer', p: 2, bgcolor: 'rgba(0, 245, 212, 0.05)', borderRadius: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Total Paid</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 800, color: 'success.main' }}>{formatCurrency(stats?.reimbursements?.paid ?? 0)}</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box onClick={() => navigate('/reimbursements')} sx={{ cursor: 'pointer', p: 2, bgcolor: 'rgba(231, 76, 60, 0.05)', borderRadius: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Pending</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 800, color: 'error.main' }}>{formatCurrency(stats?.reimbursements?.pending ?? 0)}</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box onClick={() => navigate('/reimbursements')} sx={{ cursor: 'pointer', p: 2, bgcolor: 'rgba(157, 78, 221, 0.05)', borderRadius: 2 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>This Month</Typography>
                      <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main' }}>{formatCurrency(stats?.reimbursements?.this_month ?? 0)}</Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box sx={{ width: '100%', height: 200, mt: 3 }}>
                  <ResponsiveContainer>
                    <LineChart data={stats?.reimbursements?.graph || []}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="name" stroke="#6c757d" fontSize={12} />
                      <YAxis stroke="#6c757d" fontSize={12} tickFormatter={(value) => `₹${value}`} width={80} />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Line type="monotone" dataKey="amount" stroke="#00f5d4" strokeWidth={3} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Advance Salary Analytics */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, mt: 2 }}>Advance Salary & Payroll</Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Card onClick={() => navigate('/payroll')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)' }, transition: 'all 0.2s', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Total Advance Given</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800 }}>{formatCurrency(stats?.advance_salary?.given ?? 0)}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card onClick={() => navigate('/payroll')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)' }, transition: 'all 0.2s', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Pending Recovery</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'warning.main' }}>{formatCurrency(stats?.advance_salary?.pending_recovery ?? 0)}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card onClick={() => navigate('/payroll')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)' }, transition: 'all 0.2s', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Recovered This Month</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, color: 'success.main' }}>{formatCurrency(stats?.advance_salary?.recovered_this_month ?? 0)}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card onClick={() => navigate('/payroll')} sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)' }, transition: 'all 0.2s', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Payroll Status</Typography>
                    <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                      <Typography variant="h6" sx={{ fontWeight: 800, color: 'success.main' }}>{stats?.payroll?.processed ?? 0} <Typography component="span" variant="caption">Processed</Typography></Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800, color: 'warning.main' }}>{stats?.payroll?.pending ?? 0} <Typography component="span" variant="caption">Pending</Typography></Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Leave & Overtime Pending Approvals */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, mt: 2 }}>Approvals (Leave & Overtime)</Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Card onClick={() => navigate('/leaves')} sx={{ cursor: 'pointer', border: '1px solid', borderColor: 'divider' }}>
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(255, 159, 67, 0.1)', color: 'warning.main' }}><Hourglass size={20} /></Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Leaves</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2, textAlign: 'center' }}>
                      <Box><Typography variant="h6" sx={{ fontWeight: 800, color: 'warning.main' }}>{stats?.leaves?.pending ?? 0}</Typography><Typography variant="caption" color="text.secondary">Pending</Typography></Box>
                      <Box><Typography variant="h6" sx={{ fontWeight: 800, color: 'success.main' }}>{stats?.leaves?.approved ?? 0}</Typography><Typography variant="caption" color="text.secondary">Approved</Typography></Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Card onClick={() => navigate('/attendance')} sx={{ cursor: 'pointer', border: '1px solid', borderColor: 'divider' }}>
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(157, 78, 221, 0.1)', color: 'primary.main' }}><Clock size={20} /></Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Overtime</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2, textAlign: 'center' }}>
                      <Box><Typography variant="h6" sx={{ fontWeight: 800, color: 'warning.main' }}>{stats?.overtime?.pending ?? 0}</Typography><Typography variant="caption" color="text.secondary">Pending</Typography></Box>
                      <Box><Typography variant="h6" sx={{ fontWeight: 800, color: 'success.main' }}>{stats?.overtime?.approved ?? 0}</Typography><Typography variant="caption" color="text.secondary">Approved</Typography></Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      ) : (
        // ==========================================
        // EMPLOYEE DASHBOARD
        // ==========================================
        <Grid container spacing={3}>
          {/* Punch Card Card */}
          <Grid item xs={12} md={6}>
            <Card sx={{ background: 'linear-gradient(135deg, rgba(157, 78, 221, 0.1) 0%, rgba(0, 245, 212, 0.05) 100%)' }}>
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>Punch Status</Typography>
                  <Chip 
                    label={employeeDashboard.status || "Pending"} 
                    color={employeeDashboard.status === 'Checked In' ? 'success' : employeeDashboard.status === 'Checked Out' ? 'error' : 'default'} 
                    sx={{ fontWeight: 600 }} 
                  />
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Clock size={16} />
                      <Typography variant="body2" color="text.secondary">Check-In</Typography>
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 700, mt: 0.5 }}>{employeeDashboard.checkedInTime}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Clock size={16} />
                      <Typography variant="body2" color="text.secondary">Check-Out</Typography>
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 700, mt: 0.5 }}>{employeeDashboard.checkedOutTime}</Typography>
                  </Grid>
                </Grid>
                <Button 
                  variant="contained" 
                  fullWidth 
                  sx={{ mt: 4 }}
                  onClick={() => navigate('/attendance')}
                >
                  Manage Attendance
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Metrics */}
          <Grid item xs={12} md={6}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 3 }}>
                    <Box sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(0, 245, 212, 0.1)', color: 'secondary.main' }}>
                      <ClipboardList size={24} />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Active Tasks</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>{employeeDashboard.taskCompleteness}</Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Card>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 3 }}>
                    <Box sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(157, 78, 221, 0.1)', color: 'primary.main' }}>
                      <FileText size={24} />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Leave Balance</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>{employeeDashboard.remainingLeaves}</Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card>
                  <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ p: 2, borderRadius: 3, bgcolor: 'rgba(0, 187, 249, 0.1)', color: 'secondary.dark' }}>
                        <Wallet size={24} />
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Recent Payslip</Typography>
                        <Typography variant="h6" sx={{ fontWeight: 800 }}>June 2026 Payslip</Typography>
                      </Box>
                    </Box>
                    <Button variant="outlined" size="small" onClick={() => navigate('/payroll')}>
                      View Payslips
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      )}

      {/* Auto Checkouts Details Modal */}
      <Dialog 
        open={autoCheckoutModalOpen} 
        onClose={() => setAutoCheckoutModalOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ m: 0, p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: 'rgba(231, 76, 60, 0.05)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MonitorOff size={20} color="#e74c3c" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Auto Checkouts Details</Typography>
          </Box>
          <IconButton onClick={() => setAutoCheckoutModalOpen(false)}>
            <X size={20} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ p: 0 }}>
          <Accordion defaultExpanded disableGutters elevation={0} sx={{ borderBottom: '1px solid #eee', '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ChevronDown />} sx={{ bgcolor: '#fafafa' }}>
              <Typography sx={{ fontWeight: 600 }}>Today's Auto Checkouts ({stats?.attendance?.auto_checkouts_today ?? 0})</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>
              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Employee</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Shift</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Check-Out Time</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Reason</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.attendance?.history?.filter(h => h.date === new Date().toISOString().split('T')[0]).map((row, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{row.employee}</TableCell>
                        <TableCell>
                          <Chip label={row.shift} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{row.checkout_time || 'N/A'}</TableCell>
                        <TableCell>
                          <Chip label={row.reason} size="small" color="warning" sx={{ fontWeight: 500 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!stats?.attendance?.history || stats?.attendance?.history?.filter(h => h.date === new Date().toISOString().split('T')[0]).length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 3, color: 'text.secondary' }}>No auto checkouts today</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          <Accordion disableGutters elevation={0} sx={{ '&:before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ChevronDown />} sx={{ bgcolor: '#fafafa' }}>
              <Typography sx={{ fontWeight: 600 }}>Yesterday's Auto Checkouts ({stats?.attendance?.auto_checkouts_yesterday ?? 0})</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>
              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Employee</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Shift</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Check-Out Time</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Reason</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.attendance?.history?.filter(h => {
                      const d = new Date();
                      d.setDate(d.getDate() - 1);
                      return h.date === d.toISOString().split('T')[0];
                    }).map((row, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{row.employee}</TableCell>
                        <TableCell>
                          <Chip label={row.shift} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{row.checkout_time || 'N/A'}</TableCell>
                        <TableCell>
                          <Chip label={row.reason} size="small" color="warning" sx={{ fontWeight: 500 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!stats?.attendance?.history || stats?.attendance?.history?.filter(h => {
                      const d = new Date();
                      d.setDate(d.getDate() - 1);
                      return h.date === d.toISOString().split('T')[0];
                    }).length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ py: 3, color: 'text.secondary' }}>No auto checkouts yesterday</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

