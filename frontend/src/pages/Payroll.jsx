import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, CardHeader,
  IconButton, MenuItem
} from '@mui/material';
import { IndianRupee, Send, ShieldAlert, Sparkles, Download } from 'lucide-react';
import api from '../services/api';

export default function Payroll() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN';

  // State
  const [payrolls, setPayrolls] = useState([]);
  const [advances, setAdvances] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Generator states
  const [selectedEmp, setSelectedEmp] = useState('');
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  
  // Advance request states
  const [advAmount, setAdvAmount] = useState('');
  const [advDeduction, setAdvDeduction] = useState('');
  const [bonusAmount, setBonusAmount] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    fetchPayrolls();
    fetchAdvances();
    if (isAdmin) {
      fetchEmployees();
    }
  }, [isAdmin, selectedFirm]);

  const fetchPayrolls = async () => {
    try {
      const res = await api.get('/payroll/records/', { params: { firm: selectedFirm } });
      setPayrolls(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAdvances = async () => {
    try {
      const res = await api.get('/payroll/advances/', { params: { firm: selectedFirm } });
      setAdvances(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/employees/', { params: { firm: selectedFirm } });
      setEmployees(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGeneratePayroll = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await api.post('/payroll/records/generate/', {
        employee_id: selectedEmp,
        month: month,
        year: year,
        bonus: bonusAmount ? parseFloat(bonusAmount) : 0.0
      });
      setSuccessMsg("Payroll calculated successfully as DRAFT.");
      setBonusAmount('');
      fetchPayrolls();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to generate payroll.");
    } finally {
      setLoading(false);
    }
  };

  const handlePayout = async (id) => {
    try {
      await api.post(`/payroll/records/${id}/payout/`);
      fetchPayrolls();
      fetchAdvances();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemoveBonus = async (id) => {
    try {
      await api.post(`/payroll/records/${id}/remove-bonus/`);
      fetchPayrolls();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to remove bonus.");
    }
  };

  const handleRequestAdvance = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await api.post('/payroll/advances/', {
        amount: advAmount,
        monthly_deduction: advDeduction
      });
      setSuccessMsg("Advance salary request filed successfully.");
      setAdvAmount('');
      setAdvDeduction('');
      fetchAdvances();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Failed to file advance request.");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAdvance = async (id) => {
    try {
      await api.post(`/payroll/advances/${id}/approve/`);
      fetchAdvances();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to approve advance request.");
    }
  };

  const handleRejectAdvance = async (id) => {
    try {
      await api.post(`/payroll/advances/${id}/reject/`);
      fetchAdvances();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to reject advance request.");
    }
  };

  const handleDisburseAdvance = async (id) => {
    try {
      await api.post(`/payroll/advances/${id}/disburse/`);
      fetchAdvances();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to disburse advance request.");
    }
  };

  const handleMarkPendingAdvance = async (id) => {
    try {
      await api.post(`/payroll/advances/${id}/mark-pending/`);
      fetchAdvances();
    } catch (e) {
      console.error(e);
      setErrorMsg(e.response?.data?.detail || "Failed to revert advance request.");
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Payroll & Financials
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track salary ledger history, file salary advance requests, and verify disbursements.
        </Typography>
      </Box>

      {errorMsg && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{errorMsg}</Alert>}
      {successMsg && <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>{successMsg}</Alert>}

      <Grid container spacing={4}>
        {/* Admin Section: Payroll Generator */}
        {isAdmin && (
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Generate Monthly Payroll" titleTypographyProps={{ fontWeight: 700 }} />
              <CardContent sx={{ pt: 0 }}>
                <Box component="form" onSubmit={handleGeneratePayroll}>
                  <TextField
                    select
                    fullWidth
                    label="Select Employee"
                    value={selectedEmp}
                    onChange={(e) => setSelectedEmp(e.target.value)}
                    sx={{ mb: 2 }}
                    required
                  >
                    {employees.map((emp) => (
                      <MenuItem key={emp.id} value={emp.user_id || emp.id}>{emp.username}</MenuItem>
                    ))}
                  </TextField>

                  <TextField
                    type="number"
                    fullWidth
                    label="Month (1-12)"
                    value={month}
                    onChange={(e) => setMonth(e.target.value)}
                    sx={{ mb: 2 }}
                    inputProps={{ min: 1, max: 12 }}
                    required
                  />

                  <TextField
                    type="number"
                    fullWidth
                    label="Year"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    sx={{ mb: 2 }}
                    required
                  />

                  <TextField
                    type="number"
                    fullWidth
                    label="Bonus Amount (₹) - Optional"
                    value={bonusAmount}
                    onChange={(e) => setBonusAmount(e.target.value)}
                    sx={{ mb: 3 }}
                    inputProps={{ min: 0 }}
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    startIcon={<Sparkles size={16} />}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Calculate Payslip'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Employee Section: Request Salary Advance */}
        {!isAdmin && (
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Request Salary Advance" titleTypographyProps={{ fontWeight: 700 }} />
              <CardContent sx={{ pt: 0 }}>
                <Box component="form" onSubmit={handleRequestAdvance}>
                  <TextField
                    type="number"
                    fullWidth
                    label="Advance Amount (₹)"
                    value={advAmount}
                    onChange={(e) => setAdvAmount(e.target.value)}
                    sx={{ mb: 2 }}
                    required
                  />

                  <TextField
                    type="number"
                    fullWidth
                    label="Monthly Repayment Deduction (₹)"
                    value={advDeduction}
                    onChange={(e) => setAdvDeduction(e.target.value)}
                    sx={{ mb: 3 }}
                    required
                  />

                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    startIcon={<Send size={16} />}
                  >
                    Submit Request
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Payslips Table */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Payslip Disbursements
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Period</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Base Salary</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>OT Pay</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Deductions</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>PF Deducted</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Net Pay</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {payrolls.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 9 : 8} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No payslips recorded.
                        </TableCell>
                      </TableRow>
                    ) : (
                      payrolls.map((p) => (
                        <TableRow key={p.id}>
                          {isAdmin && <TableCell sx={{ fontWeight: 600 }}>{p.employee_name}</TableCell>}
                          <TableCell>{p.month}/{p.year}</TableCell>
                          <TableCell>
                            ₹{parseFloat(p.base_salary).toLocaleString('en-IN')}
                            {parseFloat(p.bonus) > 0 && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                <Typography sx={{ fontSize: '0.75rem', color: 'success.main', fontWeight: 500 }}>
                                  +₹{parseFloat(p.bonus).toLocaleString('en-IN')} Bonus
                                </Typography>
                                {p.status === 'DRAFT' && (
                                  <Typography 
                                    component="span"
                                    onClick={() => handleRemoveBonus(p.id)}
                                    sx={{ 
                                      fontSize: '0.7rem', 
                                      color: 'error.main', 
                                      cursor: 'pointer',
                                      textDecoration: 'underline',
                                      ml: 0.5,
                                      '&:hover': { color: 'error.dark' }
                                    }}
                                  >
                                    (Remove)
                                  </Typography>
                                )}
                              </Box>
                            )}
                          </TableCell>
                          <TableCell>₹{parseFloat(p.overtime_pay).toLocaleString('en-IN')}</TableCell>
                          <TableCell>
                            ₹{parseFloat(parseFloat(p.advance_deduction) + parseFloat(p.unpaid_leave_deduction) + parseFloat(p.absent_deduction)).toLocaleString('en-IN')}
                            {parseFloat(p.already_paid) > 0 && (
                              <Box sx={{ fontSize: '0.75rem', color: 'error.main', mt: 0.5 }}>
                                -₹{parseFloat(p.already_paid).toLocaleString('en-IN')} Prev Paid
                              </Box>
                            )}
                          </TableCell>
                          <TableCell>
                            {parseFloat(p.pf_deduction) > 0 ? (
                              <Typography color="error.main" variant="body2" sx={{ fontWeight: 600 }}>
                                -₹{parseFloat(p.pf_deduction).toLocaleString('en-IN')}
                              </Typography>
                            ) : (
                              '--'
                            )}
                          </TableCell>
                          <TableCell sx={{ fontWeight: 700 }}>₹{parseFloat(p.net_salary).toLocaleString('en-IN')}</TableCell>
                          <TableCell>
                            <Chip 
                              label={p.status} 
                              size="small" 
                              color={p.status === 'PAID' ? 'success' : p.status === 'APPROVED' ? 'primary' : 'default'} 
                              sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            {isAdmin && p.status === 'DRAFT' ? (
                              <Button variant="outlined" size="small" onClick={() => handlePayout(p.id)}>
                                Payout
                              </Button>
                            ) : (
                              <IconButton color="primary">
                                <Download size={16} />
                              </IconButton>
                            )}
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

        {/* Advances History Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Salary Advance Requests
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Requested Amount</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Monthly Repayment</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Repaid</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {advances.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 6 : 5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No advance request records.
                        </TableCell>
                      </TableRow>
                    ) : (
                      advances.map((a) => (
                        <TableRow key={a.id}>
                          {isAdmin && <TableCell>{a.employee_name}</TableCell>}
                          <TableCell>₹{a.amount}</TableCell>
                          <TableCell>₹{a.monthly_deduction}/mo</TableCell>
                          <TableCell>₹{a.repaid_amount}</TableCell>
                          <TableCell>
                            <Chip 
                              label={a.status} 
                              size="small" 
                              color={
                                a.status === 'DISBURSED' ? 'info' :
                                a.status === 'APPROVED' ? 'success' : 
                                a.status === 'PENDING' ? 'warning' : 
                                a.status === 'REJECTED' ? 'error' :
                                'default'
                              } 
                              sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          {isAdmin && (
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                {a.status === 'PENDING' && (
                                  <>
                                    <Button 
                                      variant="outlined" 
                                      color="success"
                                      size="small"
                                      onClick={() => handleApproveAdvance(a.id)}
                                    >
                                      Approve
                                    </Button>
                                    <Button 
                                      variant="outlined" 
                                      color="error"
                                      size="small"
                                      onClick={() => handleRejectAdvance(a.id)}
                                    >
                                      Reject
                                    </Button>
                                  </>
                                )}
                                {a.status === 'APPROVED' && (
                                  <>
                                    <Button 
                                      variant="contained" 
                                      color="primary"
                                      size="small"
                                      onClick={() => handleDisburseAdvance(a.id)}
                                    >
                                      Disburse
                                    </Button>
                                    <Button 
                                      variant="outlined" 
                                      color="error"
                                      size="small"
                                      onClick={() => handleRejectAdvance(a.id)}
                                    >
                                      Reject
                                    </Button>
                                    <Button 
                                      variant="outlined" 
                                      color="warning"
                                      size="small"
                                      onClick={() => handleMarkPendingAdvance(a.id)}
                                    >
                                      Revert
                                    </Button>
                                  </>
                                )}
                                {a.status === 'DISBURSED' && (
                                  <Button 
                                    variant="outlined" 
                                    color="warning"
                                    size="small"
                                    onClick={() => handleMarkPendingAdvance(a.id)}
                                  >
                                    Revert
                                  </Button>
                                )}
                                {a.status === 'REJECTED' && (
                                  <Button 
                                    variant="outlined" 
                                    color="warning"
                                    size="small"
                                    onClick={() => handleMarkPendingAdvance(a.id)}
                                  >
                                    Revert
                                  </Button>
                                )}
                                {a.status !== 'PENDING' && a.status !== 'APPROVED' && a.status !== 'DISBURSED' && a.status !== 'REJECTED' && (
                                  '--'
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
        </Grid>

      </Grid>
    </Box>
  );
}
