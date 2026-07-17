import os

content = """import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  CircularProgress, Alert, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Accordion, AccordionSummary, AccordionDetails, Tooltip,
  IconButton, Pagination, Select, MenuItem, InputLabel, FormControl
} from '@mui/material';
import { MapPin, ShieldAlert, CheckCircle, Clock, ChevronDown, ChevronRight, X, Maximize2 } from 'lucide-react';
import api, { getMediaUrl } from '../services/api';
import { formatDate } from '../utils/format';
import EditAttendanceModal from '../components/EditAttendanceModal';

// --- STYLED COMPONENTS & HELPERS ---
const StatusChip = ({ status }) => {
  const colors = {
    PRESENT: 'success',
    LATE: 'warning',
    HALF_DAY: 'primary',
    ABSENT: 'error',
    PENDING: 'default'
  };
  return <Chip label={status || 'UNKNOWN'} color={colors[status] || 'default'} size="small" sx={{ fontWeight: 600 }} />;
};

const PhotoPreview = ({ url, label, onClick }) => {
  if (!url) return <Typography variant="caption" color="text.secondary">No Photo</Typography>;
  return (
    <Box 
      onClick={() => onClick(url)}
      sx={{ 
        width: 40, height: 40, borderRadius: 2, overflow: 'hidden', 
        border: '2px solid rgba(255,255,255,0.1)', cursor: 'pointer',
        transition: 'transform 0.2s', '&:hover': { transform: 'scale(1.1)' }
      }}
    >
      <img src={getMediaUrl(url)} alt={label} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
    </Box>
  );
};

export default function Attendance() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';

  // --- FILTERS & PAGINATION ---
  const [filters, setFilters] = useState({
    date: '',
    startDate: '',
    endDate: '',
    employee: '',
    status: '',
    autoCheckout: '',
    overtimePending: ''
  });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalRecords, setTotalRecords] = useState(0);

  // --- DATA ---
  const [adminRecords, setAdminRecords] = useState([]);
  const [groupedRecords, setGroupedRecords] = useState({});
  const [loading, setLoading] = useState(true);

  // --- MODALS & UI ---
  const [expandedDates, setExpandedDates] = useState({});
  const [expandedEmployees, setExpandedEmployees] = useState({});
  const [photoViewerOpen, setPhotoViewerOpen] = useState(false);
  const [viewPhotoUrl, setViewPhotoUrl] = useState('');
  
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedSessionForEdit, setSelectedSessionForEdit] = useState(null);

  useEffect(() => {
    fetchAdminRecords();
  }, [isAdmin, selectedFirm, page, filters]);

  const fetchAdminRecords = async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      const params = {
        firm: selectedFirm,
        limit: pageSize,
        offset: (page - 1) * pageSize,
        ...filters
      };
      
      // Clean empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) {
          delete params[key];
        }
      });

      const response = await api.get('/attendance/records/', { params });
      
      const results = response.data.results || response.data;
      setAdminRecords(results);
      setTotalRecords(response.data.count || results.length);
      groupRecords(results);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const groupRecords = (records) => {
    const grouped = {};
    records.forEach(rec => {
      const d = rec.date;
      if (!grouped[d]) grouped[d] = [];
      grouped[d].push(rec);
    });
    setGroupedRecords(grouped);
  };

  const toggleDate = (date) => {
    setExpandedDates(prev => ({ ...prev, [date]: !prev[date] }));
  };

  const toggleEmployee = (date, empId) => {
    const key = `${date}_${empId}`;
    setExpandedEmployees(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this session?")) return;
    try {
      await api.delete('/attendance/records/delete-session/', { data: { session_id: sessionId } });
      fetchAdminRecords();
    } catch (err) {
      alert("Failed to delete session.");
    }
  };

  const openPhoto = (url) => {
    setViewPhotoUrl(getMediaUrl(url));
    setPhotoViewerOpen(true);
  };

  const handleFilterChange = (e) => {
    setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setPage(1); // reset to page 1
  };

  return (
    <Box sx={{ py: 2 }}>
      {/* Filters Section */}
      <Card sx={{ mb: 3, p: 2, background: 'rgba(255,255,255,0.02)' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>Filter Attendance</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={2}>
            <TextField 
              fullWidth size="small" type="date" name="date" 
              label="Exact Date" InputLabelProps={{ shrink: true }}
              value={filters.date} onChange={handleFilterChange} 
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField 
              fullWidth size="small" type="date" name="startDate" 
              label="Start Date" InputLabelProps={{ shrink: true }}
              value={filters.startDate} onChange={handleFilterChange} 
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField 
              fullWidth size="small" type="date" name="endDate" 
              label="End Date" InputLabelProps={{ shrink: true }}
              value={filters.endDate} onChange={handleFilterChange} 
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField 
              fullWidth size="small" name="employee" 
              label="Employee (Name/Username)" 
              value={filters.employee} onChange={handleFilterChange} 
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select name="status" value={filters.status} label="Status" onChange={handleFilterChange}>
                <MenuItem value=""><em>All</em></MenuItem>
                <MenuItem value="PRESENT">Present</MenuItem>
                <MenuItem value="HALF_DAY">Half Day</MenuItem>
                <MenuItem value="LATE">Late</MenuItem>
                <MenuItem value="ABSENT">Absent</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button variant="outlined" color="error" fullWidth onClick={() => {
              setFilters({ date: '', startDate: '', endDate: '', employee: '', status: '', autoCheckout: '', overtimePending: '' });
              setPage(1);
            }}>
              Clear Filters
            </Button>
          </Grid>
        </Grid>
      </Card>

      {/* Accordions */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
      ) : Object.keys(groupedRecords).length === 0 ? (
        <Alert severity="info">No attendance records found for the selected filters.</Alert>
      ) : (
        Object.keys(groupedRecords).sort((a,b) => new Date(b) - new Date(a)).map(date => {
          const dateRecords = groupedRecords[date];
          const isDateExpanded = !!expandedDates[date];
          
          const summary = {
            total: dateRecords.length,
            present: dateRecords.filter(r => r.status === 'PRESENT').length,
            halfDay: dateRecords.filter(r => r.status === 'HALF_DAY').length,
            late: dateRecords.filter(r => r.status === 'LATE').length,
          };

          return (
            <Accordion 
              key={date} 
              expanded={isDateExpanded} 
              onChange={() => toggleDate(date)}
              sx={{ mb: 2, bgcolor: 'background.paper', borderRadius: '8px !important', '&:before': { display: 'none' } }}
            >
              <AccordionSummary expandIcon={<ChevronDown />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, width: '100%' }}>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: 'primary.main', minWidth: 120 }}>
                    {formatDate(date)}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 3, opacity: 0.8 }}>
                    <Typography variant="body2">Employees: <b>{summary.total}</b></Typography>
                    <Typography variant="body2">Present: <b>{summary.present}</b></Typography>
                    <Typography variant="body2">Half Day: <b>{summary.halfDay}</b></Typography>
                    <Typography variant="body2">Late: <b>{summary.late}</b></Typography>
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ bgcolor: 'rgba(0,0,0,0.1)', p: 2 }}>
                
                {/* Employee Accordions */}
                {dateRecords.map(rec => {
                  const empKey = `${date}_${rec.id}`;
                  const isEmpExpanded = !!expandedEmployees[empKey];

                  return (
                    <Accordion 
                      key={empKey} 
                      expanded={isEmpExpanded} 
                      onChange={() => toggleEmployee(date, rec.id)}
                      sx={{ mb: 1, bgcolor: 'background.default', borderRadius: '6px !important', '&:before': { display: 'none' } }}
                    >
                      <AccordionSummary expandIcon={<ChevronDown />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', pr: 2 }}>
                          {/* Employee Name Typography */}
                          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 800, color: 'secondary.main', textTransform: 'uppercase' }}>
                              {rec.employee_name}
                            </Typography>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                              @{rec.employee_username || rec.employee_name.toLowerCase().replace(' ', '_')}
                            </Typography>
                          </Box>

                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              Total: {parseFloat(rec.daily_total_hours).toFixed(2)}h
                            </Typography>
                            <StatusChip status={rec.status} />
                          </Box>
                        </Box>
                      </AccordionSummary>
                      
                      <AccordionDetails sx={{ p: 0 }}>
                        <TableContainer sx={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                          <Table size="small">
                            <TableHead sx={{ bgcolor: 'rgba(0,0,0,0.2)' }}>
                              <TableRow>
                                <TableCell sx={{ width: 80, fontWeight: 700 }}>Session</TableCell>
                                <TableCell sx={{ width: 120, fontWeight: 700 }}>Check In</TableCell>
                                <TableCell sx={{ width: 120, fontWeight: 700 }}>Check Out</TableCell>
                                <TableCell sx={{ width: 100, fontWeight: 700 }}>Duration</TableCell>
                                <TableCell sx={{ width: 120, fontWeight: 700 }}>Photos</TableCell>
                                <TableCell sx={{ width: 250, fontWeight: 700 }}>Locations</TableCell>
                                <TableCell sx={{ width: 150, fontWeight: 700, textAlign: 'right' }}>Actions</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {(!rec.sessions || rec.sessions.length === 0) ? (
                                <TableRow>
                                  <TableCell colSpan={7} align="center" sx={{ py: 3, color: 'text.secondary' }}>No sessions recorded.</TableCell>
                                </TableRow>
                              ) : rec.sessions.map((sess, idx) => (
                                <TableRow key={sess.id} hover>
                                  <TableCell sx={{ fontWeight: 600 }}>{idx + 1}</TableCell>
                                  <TableCell>{sess.check_in_time || '--'}</TableCell>
                                  <TableCell>{sess.check_out_time || '--'}</TableCell>
                                  <TableCell>{parseFloat(sess.hours).toFixed(2)}h</TableCell>
                                  
                                  {/* Photos */}
                                  <TableCell>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                      <Tooltip title="Check In Photo">
                                        <Box><PhotoPreview url={sess.captured_image} label="In" onClick={openPhoto} /></Box>
                                      </Tooltip>
                                      <Tooltip title="Check Out Photo">
                                        <Box><PhotoPreview url={sess.check_out_captured_image} label="Out" onClick={openPhoto} /></Box>
                                      </Tooltip>
                                    </Box>
                                  </TableCell>

                                  {/* Locations (Overflow handled) */}
                                  <TableCell sx={{ maxWidth: 250 }}>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                      <Tooltip title={sess.check_in_address || 'Unknown In Location'}>
                                        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                          <MapPin size={12} color="#00f5d4" /> 
                                          {sess.check_in_address || '---'}
                                        </Typography>
                                      </Tooltip>
                                      <Tooltip title={sess.check_out_address || 'Unknown Out Location'}>
                                        <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                          <MapPin size={12} color="#ff9f43" /> 
                                          {sess.check_out_address || '---'}
                                        </Typography>
                                      </Tooltip>
                                    </Box>
                                  </TableCell>

                                  {/* Actions */}
                                  <TableCell align="right">
                                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                                      <Button size="small" variant="outlined" color="primary" onClick={() => { setSelectedSessionForEdit(sess); setEditModalOpen(true); }}>
                                        Edit
                                      </Button>
                                      <Button size="small" variant="outlined" color="error" onClick={() => handleDeleteSession(sess.id)}>
                                        Delete
                                      </Button>
                                    </Box>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>
                  );
                })}

              </AccordionDetails>
            </Accordion>
          );
        })
      )}

      {/* Pagination */}
      {totalRecords > pageSize && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination 
            count={Math.ceil(totalRecords / pageSize)} 
            page={page} 
            onChange={(e, v) => setPage(v)} 
            color="primary" 
          />
        </Box>
      )}

      {/* Photo Viewer Modal */}
      <Dialog open={photoViewerOpen} onClose={() => setPhotoViewerOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Photo Preview
          <IconButton onClick={() => setPhotoViewerOpen(false)}><X /></IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, bgcolor: '#000', display: 'flex', justifyContent: 'center' }}>
          {viewPhotoUrl && <img src={viewPhotoUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain' }} />}
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      {selectedSessionForEdit && (
        <EditAttendanceModal
          open={editModalOpen}
          onClose={() => setEditModalOpen(false)}
          session={selectedSessionForEdit}
          onSaved={() => {
            fetchAdminRecords();
            setEditModalOpen(false);
          }}
        />
      )}

    </Box>
  );
}
"""

with open("../frontend/src/pages/Attendance.jsx", "w") as f:
    f.write(content)
