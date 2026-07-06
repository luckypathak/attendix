import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  Grid, Card, CardContent, Typography, Box, Button, 
  Table, TableBody, TableCell, TableContainer, TableHead, 
  TableRow, Paper, Chip, Avatar 
} from '@mui/material';
import { 
  Users, CheckCircle2, AlertTriangle, FileText, 
  ArrowUpRight, Clock, ClipboardList, Wallet 
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';

const mockAttendanceData = [
  { name: 'Mon', Present: 24, Late: 2 },
  { name: 'Tue', Present: 26, Late: 1 },
  { name: 'Wed', Present: 25, Late: 3 },
  { name: 'Thu', Present: 28, Late: 0 },
  { name: 'Fri', Present: 27, Late: 2 },
];

export default function Dashboard() {
  const { user } = useSelector((state) => state.auth);
  const navigate = useNavigate();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';
  
  // Dashboard states
  const [stats, setStats] = useState({
    totalEmployees: 0,
    checkedIn: 0,
    late: 0,
    pendingLeaves: 0,
  });

  const [pendingApprovals, setPendingApprovals] = useState([]);

  const [employeeDashboard, setEmployeeDashboard] = useState({
    checkedInTime: 'Pending',
    checkedOutTime: 'Pending',
    taskCompleteness: 'No Tasks Assigned',
    remainingLeaves: '0 Days Left',
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [isAdmin]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const statsRes = await api.get('/company/dashboard-stats/');
      const statsData = statsRes.data.stats;
      if (isAdmin) {
        setStats(statsData);
        
        // Fetch real pending leaves & reimbursements
        const [leavesRes, reimbursementsRes] = await Promise.all([
          api.get('/leaves/requests/?status=PENDING'),
          api.get('/reimbursements/?status=PENDING')
        ]);
        
        const pendingLeaves = (leavesRes.data.results || leavesRes.data).map(item => ({
          id: item.id,
          employee: item.employee_name,
          type: 'Leave Request',
          detail: `${item.leave_type} (${item.start_date} to ${item.end_date})`,
        }));

        const pendingReimbursements = (reimbursementsRes.data.results || reimbursementsRes.data).map(item => ({
          id: item.id,
          employee: item.employee_name,
          type: 'Reimbursement',
          detail: `₹${item.amount} for ${item.title}`,
        }));

        setPendingApprovals([...pendingLeaves, ...pendingReimbursements]);
      } else {
        setEmployeeDashboard(statsData);
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (item) => {
    try {
      if (item.type === 'Leave Request') {
        await api.post(`/leaves/requests/${item.id}/approve/`, { manager_comments: 'Approved via Dashboard Quick Action' });
      } else if (item.type === 'Reimbursement') {
        await api.post(`/reimbursements/${item.id}/approve/`, { manager_comments: 'Approved via Dashboard Quick Action' });
      }
      fetchDashboardData();
    } catch (e) {
      console.error("Approval error:", e);
    }
  };

  const handleReject = async (item) => {
    try {
      if (item.type === 'Leave Request') {
        await api.post(`/leaves/requests/${item.id}/reject/`, { manager_comments: 'Rejected via Dashboard Quick Action' });
      } else if (item.type === 'Reimbursement') {
        await api.post(`/reimbursements/${item.id}/reject/`, { manager_comments: 'Rejected via Dashboard Quick Action' });
      }
      fetchDashboardData();
    } catch (e) {
      console.error("Rejection error:", e);
    }
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

      {isAdmin ? (
        // ==========================================
        // ADMIN DASHBOARD
        // ==========================================
        <Grid container spacing={3}>
          {/* Stats Cards */}
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              onClick={() => navigate('/employees')}
              sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s' }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(157, 78, 221, 0.1)', color: 'primary.main' }}>
                  <Users size={24} />
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Total Employees</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats.totalEmployees}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              onClick={() => navigate('/attendance')}
              sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s' }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(0, 245, 212, 0.1)', color: 'secondary.main' }}>
                  <CheckCircle2 size={24} />
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Checked In Today</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats.checkedIn}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card 
              onClick={() => navigate('/attendance')}
              sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s' }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(255, 159, 67, 0.1)', color: '#ff9f43' }}>
                  <AlertTriangle size={24} />
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Late Arrivals</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats.late}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card 
              onClick={() => navigate('/leaves')}
              sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }, transition: 'all 0.2s' }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: 'rgba(231, 76, 60, 0.1)', color: '#e74c3c' }}>
                  <FileText size={24} />
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Pending Leaves</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 800 }}>{stats.pendingLeaves}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Attendance Chart */}
          <Grid item xs={12} md={8}>
            <Card sx={{ height: '100%', minHeight: 350 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Attendance Trends</Typography>
                <Box sx={{ width: '100%', height: 260 }}>
                  <ResponsiveContainer>
                    <LineChart data={mockAttendanceData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="name" stroke="#6c757d" />
                      <YAxis stroke="#6c757d" />
                      <Tooltip />
                      <Line type="monotone" dataKey="Present" stroke="#9d4edd" strokeWidth={3} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="Late" stroke="#ff9f43" strokeWidth={3} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Pending Approvals Queue */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>Approvals Queue</Typography>
                
                {pendingApprovals.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                    All requests have been approved!
                  </Typography>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {pendingApprovals.map((req) => (
                      <Box 
                        key={req.id} 
                        sx={{ 
                          p: 2, 
                          borderRadius: 3, 
                          bgcolor: 'background.default',
                          border: '1px solid rgba(255, 255, 255, 0.03)'
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                            {req.employee}
                          </Typography>
                          <Chip label={req.type} size="small" color="primary" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {req.detail}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button variant="contained" size="small" onClick={() => handleApprove(req)}>
                            Approve
                          </Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => handleReject(req)}>
                            Reject
                          </Button>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
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
                  <Chip label="Checked In" color="success" sx={{ fontWeight: 600 }} />
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
                  href="/attendance"
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
                    <Button variant="outlined" size="small" href="/payroll">
                      View Payslips
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
