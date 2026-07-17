import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Paper, Chip, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { UploadCloud, Paperclip, FileImage, Send, ShieldCheck } from 'lucide-react';
import api from '../services/api';

export default function Reimbursements() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';

  // Forms states
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [fileUrl, setFileUrl] = useState('');
  const [filePreview, setFilePreview] = useState(null);
  
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // Detail preview state
  const [openPreview, setOpenPreview] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState(null);

  useEffect(() => {
    fetchClaims();
  }, [selectedFirm]);

  const fetchClaims = async () => {
    try {
      const res = await api.get('/reimbursements/', { params: { firm: selectedFirm } });
      setClaims(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Create local preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setFilePreview(reader.result);
        setFileUrl(reader.result); // Store the actual base64 file data URL!
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await api.post('/reimbursements/', {
        title,
        amount,
        description,
        receipt_url: fileUrl || 'https://res.cloudinary.com/demo/image/upload/v1620000000/sample.jpg'
      });
      setMessage({ type: 'success', text: 'Expense claim submitted successfully!' });
      setTitle('');
      setAmount('');
      setDescription('');
      setFilePreview(null);
      setFileUrl('');
      fetchClaims();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to submit expense claim.' });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.post(`/reimbursements/${id}/approve/`, { manager_comments: 'Approved' });
      fetchClaims();
      setOpenPreview(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (id) => {
    try {
      await api.post(`/reimbursements/${id}/reject/`, { manager_comments: 'Rejected' });
      fetchClaims();
      setOpenPreview(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteClaim = async (claim) => {
    if (window.confirm(`Are you sure you want to delete this expense claim for ${claim.employee_name || 'this employee'}?`)) {
      try {
        await api.delete(`/reimbursements/${claim.id}/`);
        fetchClaims();
      } catch (err) {
        console.error("Delete claim error:", err);
      }
    }
  };

  const openClaimDetails = (claim) => {
    setSelectedClaim(claim);
    setOpenPreview(true);
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Reimbursements & Expenses
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload receipt bills, submit travel/office claims, and reconcile expenses.
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Submit Form */}
        {!isAdmin && (
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                  Submit Expense Claim
                </Typography>

                {message && <Alert severity={message.type} sx={{ mb: 3, borderRadius: 2 }}>{message.text}</Alert>}

                <Box component="form" onSubmit={handleSubmit}>
                  <TextField
                    fullWidth
                    label="Expense Title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    sx={{ mb: 2 }}
                    required
                  />

                  <TextField
                    type="number"
                    fullWidth
                    label="Amount (₹)"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    sx={{ mb: 2 }}
                    required
                  />

                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    sx={{ mb: 3 }}
                  />

                  {/* Upload box */}
                  <Box 
                    sx={{ 
                      border: '2px dashed rgba(255,255,255,0.1)', 
                      borderRadius: 3, 
                      p: 3, 
                      textAlign: 'center',
                      mb: 3,
                      cursor: 'pointer',
                      bgcolor: 'background.default',
                      position: 'relative'
                    }}
                  >
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleFileChange}
                      style={{ 
                        position: 'absolute', 
                        top: 0, 
                        left: 0, 
                        width: '100%', 
                        height: '100%', 
                        opacity: 0, 
                        cursor: 'pointer' 
                      }} 
                    />
                    {filePreview ? (
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                        <FileImage size={32} color="#00f5d4" />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>Receipt Attached</Typography>
                        <Box component="img" src={filePreview} sx={{ maxHeight: 80, borderRadius: 1, mt: 1 }} />
                      </Box>
                    ) : (
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                        <UploadCloud size={32} color="#6c757d" />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>Click to attach receipt bill</Typography>
                        <Typography variant="caption" color="text.secondary">Supports JPEG, PNG up to 5MB</Typography>
                      </Box>
                    )}
                  </Box>

                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={loading}
                    startIcon={<Send size={16} />}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Submit Claim'}
                  </Button>

                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Ledger Table */}
        <Grid item xs={12} md={isAdmin ? 12 : 7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                Expense Claims Ledger
              </Typography>

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Expense</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Amount</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {claims.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 5 : 4} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No expense claims filed.
                        </TableCell>
                      </TableRow>
                    ) : (
                      claims.map((c) => (
                        <TableRow key={c.id}>
                          {isAdmin && <TableCell>{c.employee_name}</TableCell>}
                          <TableCell>{c.title}</TableCell>
                          <TableCell>₹{c.amount}</TableCell>
                          <TableCell>
                            <Chip 
                              label={c.status} 
                              size="small" 
                              color={c.status === 'APPROVED' ? 'success' : c.status === 'REJECTED' ? 'error' : 'warning'} 
                              sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button variant="outlined" size="small" onClick={() => openClaimDetails(c)}>
                                {isAdmin && c.status === 'PENDING' ? 'Process' : 'View'}
                              </Button>
                              {isAdmin && (
                                <Button 
                                  variant="outlined" 
                                  color="error" 
                                  size="small" 
                                  onClick={() => handleDeleteClaim(c)}
                                >
                                  Delete
                                </Button>
                              )}
                            </Box>
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
      </Grid>

      {/* Claim Preview Dialog */}
      <Dialog open={openPreview} onClose={() => setOpenPreview(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Expense Claim Detail</DialogTitle>
        <DialogContent sx={{ minWidth: 350, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">Claimant</Typography>
            <Typography variant="body1" sx={{ fontWeight: 700 }}>{selectedClaim?.employee_name}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Details</Typography>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>{selectedClaim?.title} - ₹{selectedClaim?.amount}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{selectedClaim?.description || 'No description provided.'}</Typography>
          </Box>
          
          <Box sx={{ border: '1px solid rgba(255,255,255,0.05)', borderRadius: 2, p: 2, textAlign: 'center', bgcolor: 'background.default' }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, justifyContent: 'center' }}>
              <Paperclip size={12} /> Receipt Attachment
            </Typography>
            <Box 
              component="img" 
              src={selectedClaim?.receipt_url} 
              sx={{ maxWidth: '100%', maxHeight: 200, borderRadius: 1 }} 
              onError={(e) => { e.target.src = 'https://res.cloudinary.com/demo/image/upload/v1620000000/sample.jpg' }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          {isAdmin && selectedClaim?.status === 'PENDING' ? (
            <>
              <Button onClick={() => handleReject(selectedClaim.id)} color="error" variant="outlined">
                Reject
              </Button>
              <Button onClick={() => handleApprove(selectedClaim.id)} color="success" variant="contained">
                Approve
              </Button>
            </>
          ) : (
            <Button onClick={() => setOpenPreview(false)} variant="outlined">
              Close
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
