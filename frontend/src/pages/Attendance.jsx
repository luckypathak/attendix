import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  CircularProgress, Alert, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Accordion, AccordionSummary, AccordionDetails, Tooltip,
  IconButton, Pagination, Select, MenuItem, InputLabel, FormControl, Tabs, Tab
} from '@mui/material';
import { MapPin, ShieldAlert, CheckCircle, Clock, ChevronDown, ChevronRight, X, Maximize2 } from 'lucide-react';
import api, { getMediaUrl } from '../services/api';


import { Trash2, Calendar } from 'lucide-react';
import RaiseCorrectionModal from '../components/RaiseCorrectionModal';
import AttendanceCorrections from '../components/AttendanceCorrections';
import { formatDate } from '../utils/format';
import EditAttendanceModal from '../components/EditAttendanceModal';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import useBackgroundLocation from '../hooks/useBackgroundLocation';


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
  
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsError, setGpsError] = useState(null);
  const [gpsData, setGpsData] = useState(null);
  const [address, setAddress] = useState('');
  
  const [isClockedIn, setIsClockedIn] = useState(false);
  const [attendanceToday, setAttendanceToday] = useState(null);
  const [history, setHistory] = useState([]);
  const [adminRecords, setAdminRecords] = useState([]);
  // --- FILTERS & PAGINATION ---
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = {
    date: searchParams.get('date') ?? '',
    startDate: searchParams.get('startDate') ?? '',
    endDate: searchParams.get('endDate') ?? '',
    employee: searchParams.get('employee') ?? '',
    status: searchParams.get('status') ?? '',
    autoCheckout: searchParams.get('autoCheckout') ?? '',
    overtimePending: searchParams.get('overtimePending') ?? ''
  };

  const setFilters = (newFilters) => {
    const nextParams = new URLSearchParams(searchParams);
    const updatedFilters = typeof newFilters === 'function' ? newFilters(filters) : { ...filters, ...newFilters };
    Object.entries(updatedFilters).forEach(([key, value]) => {
      if (value === '' || value === null || value === undefined) {
        nextParams.delete(key);
      } else {
        nextParams.set(key, value);
      }
    });
    setSearchParams(nextParams, { replace: true });
  };

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalRecords, setTotalRecords] = useState(0);
  const [overtimeRequests, setOvertimeRequests] = useState([]);
  const [adminTab, setAdminTab] = useState(0);
  const [expandedDates, setExpandedDates] = useState({});
  const [expandedEmployees, setExpandedEmployees] = useState({});
  const [photoViewerOpen, setPhotoViewerOpen] = useState(false);
  const [viewPhotoUrl, setViewPhotoUrl] = useState('');
  const [adminLoading, setAdminLoading] = useState(false);

  useEffect(() => {
    // Default state: if no date is in URL and no other filters exist, set to today
    if (!searchParams.get('date') && !searchParams.get('employee')) {
      const now = new Date();
      const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
      const params = new URLSearchParams(searchParams);
      params.set('date', today);
      setSearchParams(params, { replace: true });
    }
  }, []);

  const groupedRecords = React.useMemo(() => {
    if (filters.employee) {
      // Group by Employee Name -> Date
      const grouped = {};
      adminRecords.forEach(rec => {
        const emp = rec.employee_name;
        if (!grouped[emp]) grouped[emp] = {};
        const d = rec.date;
        if (!grouped[emp][d]) grouped[emp][d] = [];
        grouped[emp][d].push(rec);
      });
      return grouped;
    } else {
      // Group by Date -> Employee
      const grouped = {};
      adminRecords.forEach(rec => {
        const d = rec.date;
        if (!grouped[d]) grouped[d] = [];
        grouped[d].push(rec);
      });
      return grouped;
    }
  }, [adminRecords, filters.employee]);

  const toggleDate = (date) => setExpandedDates(prev => ({ ...prev, [date]: !prev[date] }));
  const toggleEmployee = (date, empId) => {
    const key = `${date}_${empId}`;
    setExpandedEmployees(prev => ({ ...prev, [key]: !prev[key] }));
  };
  const openPhoto = (url) => { setViewPhotoUrl(getMediaUrl(url)); setPhotoViewerOpen(true); };
  const handleFilterChange = (e) => { setFilters(prev => ({ ...prev, [e.target.name]: e.target.value })); setPage(1); };

  
  const [otModalOpen, setOtModalOpen] = useState(false);
  const [selectedRecordForOt, setSelectedRecordForOt] = useState(null);
  const [otHours, setOtHours] = useState('2.0');

  // Camera states
  const [openCameraModal, setOpenCameraModal] = useState(false);
  const [cameraMode, setCameraMode] = useState('IN'); // 'IN' or 'OUT'
  const [otPromptModal, setOtPromptModal] = useState(false);
  const [otPromptMessage, setOtPromptMessage] = useState('');
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const [stream, setStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [activeSession, setActiveSession] = useState(null);

  // Edit Modal State
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedSessionForEdit, setSelectedSessionForEdit] = useState(null);
  
  const [companySettings, setCompanySettings] = useState(null);
  
  useBackgroundLocation(isClockedIn, user?.work_category, companySettings);

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this session?")) return;
    try {
      await api.delete('/attendance/records/delete-session/', { data: { session_id: sessionId } });
      fetchHistory();
      fetchCurrentState();
      if (isAdmin) fetchAdminRecords();
    } catch (err) {
      alert("Failed to delete session.");
    }
  };

  useEffect(() => {
    const fetchCompanySettings = async () => {
      try {
        const res = await api.get('/company/companies/');
        let company = null;
        if (Array.isArray(res.data.results) && res.data.results.length > 0) {
          company = res.data.results.find(c => c.name === user?.firm_name) || res.data.results[0];
        } else if (Array.isArray(res.data) && res.data.length > 0) {
          company = res.data.find(c => c.name === user?.firm_name) || res.data[0];
        }
        setCompanySettings(company);
      } catch (err) {}
    };
    fetchCompanySettings();
    
    fetchHistory();
    fetchCurrentState();
    fetchOvertimeRequests();
    if (isAdmin) fetchAdminRecords();
    // Polling removed to prevent continuous API spam
  }, [isAdmin, selectedFirm, page, searchParams]);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/attendance/records/history/');
      setHistory(response.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCurrentState = async () => {
    try {
      const response = await api.get('/attendance/records/current/');
      setIsClockedIn(response.data.is_clocked_in);
      setAttendanceToday(response.data.attendance_record);
      setActiveSession(response.data.active_session);
    } catch (e) {
      console.error(e);
      // Fallback
      setIsClockedIn(false);
      setAttendanceToday(null);
      setActiveSession(null);
    }
  };

  const fetchAdminRecords = async () => {
    if (!isAdmin) return;
    setAdminLoading(true);
    try {
      const params = { firm: selectedFirm, limit: pageSize, offset: (page - 1) * pageSize, ...filters };
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) delete params[key];
      });
      const response = await api.get('/attendance/records/', { params });
      const results = response.data.results || response.data;
      setAdminRecords(results);
      setTotalRecords(response.data.count || results.length);
    } catch (e) {
      console.error(e);
    } finally {
      setAdminLoading(false);
    }
  };

  const fetchOvertimeRequests = async () => {
    try {
      const response = await api.get('/attendance/overtime/', { params: { firm: selectedFirm } });
      setOvertimeRequests(response.data.results || response.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handlePreContinue = async (empRec) => {
    try {
      const res = await api.post(`/attendance/records/${empRec.id}/pre-continue/`);
      alert(res.data.detail);
      fetchAdminRecords();
    } catch (e) {
      alert("Failed to pre-continue shift: " + (e.response?.data?.detail || e.message));
    }
  };


  const renderSessions = (empRec) => {
    if (!empRec.sessions || empRec.sessions.length === 0) {
      return <Typography variant="caption" color="text.secondary">No sessions recorded.</Typography>;
    }
    return empRec.sessions.map((sess, idx) => (
      <Box key={sess.id} sx={{ p: 1.5, mb: 1, borderRadius: 2, bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          {/* Session Core Info */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 120 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700 }}>Session {idx + 1}</Typography>
            <Typography variant="body2"><strong>In:</strong> {sess.check_in_time || '--'}</Typography>
            <Typography variant="body2"><strong>Out:</strong> {sess.check_out_time || 'Active'}</Typography>
            <Typography variant="caption" color="primary.main">Duration: {sess.working_hours || '--'}</Typography>
          </Box>
          {/* Photos */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">Check In</Typography>
              <Box sx={{ mt: 0.5 }}>
                {sess.captured_image ? (
                  <img src={getMediaUrl(sess.captured_image)} alt="Check In" onClick={() => setPreviewImage(getMediaUrl(sess.captured_image))} style={{ width: 40, height: 40, borderRadius: 4, cursor: 'pointer', objectFit: 'cover' }} />
                ) : '--'}
              </Box>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">Check Out</Typography>
              <Box sx={{ mt: 0.5 }}>
                {sess.check_out_captured_image ? (
                  <img src={getMediaUrl(sess.check_out_captured_image)} alt="Check Out" onClick={() => setPreviewImage(getMediaUrl(sess.check_out_captured_image))} style={{ width: 40, height: 40, borderRadius: 4, cursor: 'pointer', objectFit: 'cover' }} />
                ) : '--'}
              </Box>
            </Box>
          </Box>
          {/* Location */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: 200 }}>
            {sess.check_in_address && (
              <Tooltip title={sess.check_in_address} placement="top">
                <Typography variant="caption" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>📍 <strong>In:</strong> {sess.check_in_address}</Typography>
              </Tooltip>
            )}
            {sess.check_out_address && (
              <Tooltip title={sess.check_out_address} placement="bottom">
                <Typography variant="caption" sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>📍 <strong>Out:</strong> {sess.check_out_address}</Typography>
              </Tooltip>
            )}
            {sess.checkout_reason === 'AUTO_CHECKOUT' && (
              <Chip size="small" color="error" label="Auto Checkout" sx={{ mt: 0.5 }} />
            )}
          </Box>
          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
            <Button size="small" variant="outlined" onClick={() => {
              const sessWithParentStatus = { ...sess, parent_status: empRec.status, employee_name: empRec.employee_name };
              setSelectedSessionForEdit(sessWithParentStatus);
              setEditModalOpen(true);
            }}>Edit</Button>
            <Button size="small" color="error" variant="outlined" onClick={() => handleDeleteSession(sess.id)}>Delete</Button>
          </Box>
        </Box>
      </Box>
    ));
  };

  const handleOpenOtModal = (rec) => {
    setSelectedRecordForOt(rec);
    setOtHours('2.0');
    setOtModalOpen(true);
  };

  const handleSubmitPreApprovedOt = async () => {
    try {
      await api.post(`/attendance/records/${selectedRecordForOt.id}/grant-ot/`, {
        hours: parseFloat(otHours)
      });
      setOtModalOpen(false);
      fetchAdminRecords();
      fetchOvertimeRequests();
      alert('Overtime pre-approved successfully!');
    } catch (e) {
      console.error(e);
      alert('Failed to grant overtime. Make sure attendance record is active.');
    }
  };

  const handleApproveOvertime = async (id) => {
    try {
      await api.post(`/attendance/overtime/${id}/approve/`);
      fetchOvertimeRequests();
    } catch (e) {
      console.error(e);
      alert('Failed to approve overtime.');
    }
  };

  const handleRejectOvertime = async (id) => {
    try {
      await api.post(`/attendance/overtime/${id}/reject/`);
      fetchOvertimeRequests();
    } catch (e) {
      console.error(e);
      alert('Failed to reject overtime.');
    }
  };

  const captureLocation = () => {
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser.");
      return;
    }

    setGpsLoading(true);
    setGpsError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const accuracy = position.coords.accuracy;

        if (accuracy > 50) {
          setGpsError(`GPS accuracy is poor (${accuracy.toFixed(1)}m). Please step outside to get a stronger signal.`);
          setGpsLoading(false);
          return;
        }

        try {
          const geocodeRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
          const data = await geocodeRes.json();
          setAddress(data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        } catch {
          setAddress(`Coordinates: Lat ${lat.toFixed(5)}, Lng ${lng.toFixed(5)}`);
        }

        setGpsData({ latitude: lat, longitude: lng, accuracy });
        setGpsLoading(false);
      },
      (error) => {
        let msg = "Failed to retrieve location. Make sure Location Services is ON and permission is granted.";
        if (error.code === error.PERMISSION_DENIED) {
          msg = "Location permission was denied. Attendix Workforce OS requires GPS permissions to clock in.";
        }
        setGpsError(msg);
        setGpsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000 }
    );
  };

  const getError = (err, defaultMsg) => {
    if (err.response?.data) {
      const data = err.response.data;
      if (typeof data === 'string') return data;
      if (data.detail) return data.detail;
      if (typeof data === 'object') {
        const values = Object.values(data);
        if (values.length > 0) {
          const val = values[0];
          return Array.isArray(val) ? val[0] : val;
        }
      }
    }
    return err.message || defaultMsg;
  };

  const startCamera = async () => {
    setCameraError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' }
      });
      setStream(mediaStream);
      setTimeout(() => {
        const videoElement = document.getElementById('webcam-preview');
        if (videoElement) {
          videoElement.srcObject = mediaStream;
        }
      }, 300);
    } catch (err) {
      console.error("Camera access failed", err);
      setCameraError("Camera access was denied or is unavailable. Photo capture is mandatory to clock in.");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const handleOpenClockInCamera = () => {
    setCameraMode('IN');
    setOpenCameraModal(true);
    startCamera();
  };

  const handleOpenClockOutCamera = () => {
    setCameraMode('OUT');
    setOpenCameraModal(true);
    startCamera();
  };

  const handleCaptureAndProcess = () => {
    const videoElement = document.getElementById('webcam-preview');
    if (!videoElement) {
      alert("Camera preview is not active.");
      return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth || 640;
    canvas.height = videoElement.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) {
        alert("Failed to capture image from camera.");
        return;
      }
      stopCamera();
      setOpenCameraModal(false);
      if (cameraMode === 'IN') {
        await performClockIn(blob);
      } else {
        await performClockOut(blob);
      }
    }, 'image/jpeg', 0.85);
  };

  const performClockIn = async (photoBlob) => {
    if (!gpsData) return;
    setGpsLoading(true);
    setGpsError(null);
    try {
      const formData = new FormData();
      formData.append('latitude', gpsData.latitude);
      formData.append('longitude', gpsData.longitude);
      if (gpsData.accuracy) {
        formData.append('accuracy', gpsData.accuracy);
      }
      formData.append('address', address);
      formData.append('device_info', `Web Browser (${navigator.userAgent.substring(0, 50)})`);
      formData.append('captured_image', photoBlob, `attendance_${Date.now()}.jpg`);

      const response = await api.post('/attendance/records/check-in/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setIsClockedIn(true);
      setAttendanceToday(response.data);
      setGpsData(null);
      setAddress('');
      fetchHistory();
      fetchCurrentState();
    } catch (e) {
      if (e.response && e.response.status === 409 && e.response.data?.requires_ot_approval) {
        setOtPromptMessage(e.response.data.message);
        setOtPromptModal(true);
      } else if (e.response && e.response.status === 409 && (e.response.data?.code === 'correction_request_submitted' || e.response.data?.detail?.includes('correction request'))) {
        alert(e.response.data?.detail || "You attempted to check in again after your shift ended. A correction request has been sent to the Admin.");
        setGpsData(null);
        setCameraOpen(false);
      } else {
        setGpsError(getError(e, "Failed to check in."));
      }
    } finally {
      setGpsLoading(false);
    }
  };

  const performClockOut = async (photoBlob) => {
    if (!gpsData) return;
    setGpsLoading(true);
    setGpsError(null);
    try {
      const formData = new FormData();
      formData.append('latitude', gpsData.latitude);
      formData.append('longitude', gpsData.longitude);
      if (gpsData.accuracy) {
        formData.append('accuracy', gpsData.accuracy);
      }
      formData.append('address', address);
      formData.append('device_info', `Web Browser (${navigator.userAgent.substring(0, 50)})`);
      formData.append('captured_image', photoBlob, `attendance_checkout_${Date.now()}.jpg`);

      const response = await api.post('/attendance/records/check-out/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setIsClockedIn(false);
      setAttendanceToday(response.data);
      setGpsData(null);
      setAddress('');
      fetchHistory();
      fetchCurrentState();
      fetchOvertimeRequests();
    } catch (e) {
      setGpsError(getError(e, "Failed to check out."));
    } finally {
      setGpsLoading(false);
    }
  };

  const handleClockIn = () => {
    handleOpenClockInCamera();
  };

  const handleClockOut = () => {
    handleOpenClockOutCamera();
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

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <div className="flex justify-between items-center mb-1">
          <Typography variant="h4" sx={{ fontWeight: 800, letterSpacing: '-0.5px' }}>
            Attendance Console
          </Typography>
          <Button
            variant="outlined"
            color="warning"
            onClick={() => setCorrectionModalOpen(true)}
            size="small"
          >
            Request Correction
          </Button>
        </div>
        <Typography variant="body1" color="text.secondary">
          Track clock-ins, verify check-out details, and audit location metrics.
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Punch In Card */}
        {!isAdmin && (
          <Grid item xs={12} md={5}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'space-between' }}>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 4, width: '100%' }}>
                  Digital Timecard
                </Typography>

                {gpsError && (
                  <Alert severity="error" sx={{ width: '100%', mb: 3, borderRadius: 2 }}>
                    {gpsError}
                  </Alert>
                )}

                {/* Status Display */}
                <Box sx={{ textAlign: 'center', mb: 4 }}>
                  <Clock size={48} color={isClockedIn ? (activeSession?.ot_status === 'PENDING' ? '#ff9f1c' : '#00f5d4') : '#6c757d'} style={{ margin: '0 auto 16px' }} />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {isClockedIn ? (
                      activeSession?.ot_status === 'PENDING' ? 'Waiting for OT Approval' : 'Currently Clocked In'
                    ) : 'Currently Clocked Out'}
                  </Typography>
                  {isClockedIn && activeSession ? (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Active Session Check-in: <strong>{activeSession.check_in_time}</strong>
                      </Typography>
                      {activeSession.ot_status === 'PENDING' && (
                        <Chip label="OT Approval Pending" color="warning" size="small" sx={{ mt: 1, fontWeight: 700 }} />
                      )}
                      {activeSession.ot_status === 'APPROVED' && (
                        <Chip label="OT Approved" color="success" size="small" sx={{ mt: 1, fontWeight: 700 }} />
                      )}
                    </Box>
                  ) : null}
                  {!isClockedIn && attendanceToday && attendanceToday.sessions && attendanceToday.sessions.length > 0 ? (() => {
                    const lastSess = attendanceToday.sessions[attendanceToday.sessions.length - 1];
                    return (
                      <Box sx={{ mt: 1 }}>
                        {lastSess.check_out_time && (
                          <Typography variant="body2" color="text.secondary">
                            Last Clock-out: <strong>{lastSess.check_out_time}</strong> {lastSess.checkout_reason === 'AUTO_CHECKOUT' && "(Auto Checked Out)"}
                          </Typography>
                        )}
                        {lastSess.checkout_reason === 'AUTO_CHECKOUT' && (
                          <Chip label="Auto Checked Out" color="error" size="small" sx={{ mt: 1, fontWeight: 700 }} />
                        )}
                        <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 600, color: 'primary.main' }}>
                          Today's Total: {attendanceToday.formatted_worked_hours || '0h 0m'}
                        </Typography>
                      </Box>
                    );
                  })() : null}
                </Box>

                {/* Capture Location Section */}
                {!gpsData ? (
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    size="large"
                    onClick={captureLocation}
                    disabled={gpsLoading}
                    startIcon={<MapPin />}
                    sx={{ py: 1.5, mb: 2 }}
                  >
                    {gpsLoading ? <CircularProgress size={24} /> : 'Fetch Live GPS Location'}
                  </Button>
                ) : (
                  <Box sx={{ width: '100%', p: 2, bgcolor: 'background.default', borderRadius: 3, mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <CheckCircle size={16} color="#00f5d4" /> GPS Locked ({gpsData.accuracy.toFixed(1)}m Accuracy)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {address}
                    </Typography>
                  </Box>
                )}

                {/* Action Buttons */}
                <Box sx={{ width: '100%', display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  {isClockedIn ? (
                    <>
                      {/* Check if in shift window and user hasn't made a choice yet */}
                      {attendanceToday?.in_shift_window && !activeSession?.continue_shift && !activeSession?.ot_requested ? (
                        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
                          <Alert severity="info" sx={{ width: '100%' }}>
                            Your shift is ending soon. Are you continuing to complete your shift, or requesting overtime?
                          </Alert>
                          <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                            <Button
                              variant="contained"
                              color="primary"
                              fullWidth
                              size="large"
                              onClick={async () => {
                                try {
                                  await api.post(`/attendance/records/${attendanceToday.id}/continue-shift/`);
                                  fetchHistory();
                                  fetchCurrentState();
                                } catch (e) {
                                  alert(getError(e, 'Failed to continue shift'));
                                }
                              }}
                            >
                              Continue Shift
                            </Button>
                            <Button
                              variant="outlined"
                              color="warning"
                              fullWidth
                              size="large"
                              onClick={async () => {
                                try {
                                  await api.post(`/attendance/records/${attendanceToday.id}/request-overtime/`);
                                  fetchHistory();
                                  fetchCurrentState();
                                  fetchOvertimeRequests();
                                } catch (e) {
                                  alert(getError(e, 'Failed to request overtime'));
                                }
                              }}
                            >
                              Request Overtime
                            </Button>
                          </Box>
                          <Button
                            variant="outlined"
                            color="secondary"
                            fullWidth
                            size="large"
                            disabled={!gpsData}
                            onClick={handleClockOut}
                          >
                            Clock Out Now
                          </Button>
                        </Box>
                      ) : (
                        <Button
                          variant="contained"
                          color={activeSession?.ot_status === 'PENDING' ? 'warning' : 'secondary'}
                          fullWidth
                          size="large"
                          disabled={!gpsData || activeSession?.ot_status === 'PENDING'}
                          onClick={handleClockOut}
                          sx={{ py: 1.5 }}
                        >
                          {activeSession?.ot_status === 'PENDING' ? 'Waiting for OT Approval' : 'Clock Out'}
                        </Button>
                      )}
                    </>
                  ) : (
                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      disabled={!gpsData}
                      onClick={handleClockIn}
                      sx={{ py: 1.5 }}
                    >
                      Clock In
                    </Button>
                  )}
                </Box>

              </CardContent>
            </Card>
          </Grid>
        )}

        {/* History Table */}
        <Grid item xs={12} md={isAdmin ? 12 : 7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                {isAdmin ? 'Team Attendance Records' : 'My Attendance History'}
              </Typography>

              {isAdmin && (
                <Tabs value={adminTab} onChange={(e, v) => setAdminTab(v)} sx={{ mb: 3 }}>
                  <Tab label="Attendance Records" />
                  <Tab label={`Overtime Requests (${overtimeRequests.filter(r => r.status === 'PENDING').length})`} />
                  <Tab label="Correction Requests" />
                </Tabs>
              )}

        {isAdmin && adminTab === 0 && (
          <>
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
                  <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <DatePicker
                      label="Date"
                      format="DD/MM/YYYY"
                      value={filters.date ? dayjs(filters.date, 'YYYY-MM-DD') : null}
                      onChange={(newValue) => {
                        setFilters(prev => ({ ...prev, date: newValue ? newValue.format('YYYY-MM-DD') : '' }));
                        setPage(1);
                      }}
                      slotProps={{ 
                        textField: { 
                          size: 'small', 
                          variant: 'outlined',
                          sx: { minWidth: 180 }
                        } 
                      }}
                    />
                  </LocalizationProvider>
                  <TextField 
                    size="small" 
                    name="employee" 
                    label="Employee Name" 
                    value={filters.employee} 
                    onChange={handleFilterChange} 
                    sx={{ minWidth: 180 }}
                  />
                  <FormControl size="small" sx={{ minWidth: 180 }}>
                    <InputLabel id="status-label">Status</InputLabel>
                    <Select labelId="status-label" name="status" value={filters.status} label="Status" onChange={handleFilterChange}>
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="PRESENT">Present</MenuItem>
                      <MenuItem value="LATE">Late</MenuItem>
                      <MenuItem value="HALF_DAY">Half Day</MenuItem>
                      <MenuItem value="ABSENT">Absent</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small" sx={{ minWidth: 180 }}>
                    <InputLabel id="autocheckout-label">Auto Checkout</InputLabel>
                    <Select labelId="autocheckout-label" name="autoCheckout" value={filters.autoCheckout} label="Auto Checkout" onChange={handleFilterChange}>
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="true">Yes</MenuItem>
                      <MenuItem value="false">No</MenuItem>
                    </Select>
                  </FormControl>
                  <Button 
                    variant="outlined" 
                    color="secondary" 
                    size="small"
                    onClick={() => {
                      const now = new Date();
                      const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                      setSearchParams({ date: today });
                      setPage(1);
                    }}
                  >
                    Clear Filters
                  </Button>
                </Box>
              </>
              )}

              {/* ACCORDION IMPLEMENTATION */}
              {isAdmin ? (
                <Box>
                  {Object.keys(groupedRecords).length === 0 ? (
                    <Typography color="text.secondary">No attendance logs available.</Typography>
                  ) : (
                    filters.employee ? (
                      // EMPLOYEE SEARCH MODE (Employee -> Date -> Sessions)
                      Object.keys(groupedRecords).sort().map(empName => {
                        const empDates = groupedRecords[empName];
                        const isEmpExpanded = expandedEmployees[empName];
                        const allDates = Object.keys(empDates);
                        
                        return (
                          <Accordion 
                            key={empName} 
                            expanded={isEmpExpanded !== false} // default expanded if searching
                            onChange={() => toggleEmployee('ALL', empName)}
                            sx={{ mb: 1, bgcolor: 'background.neutral', '&:before': { display: 'none' }, borderRadius: '8px !important' }}
                          >
                            <AccordionSummary expandIcon={<ChevronDown />}>
                              <Typography sx={{ fontWeight: 700, color: 'primary.main' }}>
                                {empName} ({allDates.length} Days)
                              </Typography>
                            </AccordionSummary>
                            <AccordionDetails sx={{ p: 0, bgcolor: 'background.default' }}>
                              {(isEmpExpanded !== false) && allDates.sort((a, b) => new Date(b) - new Date(a)).map(dateStr => {
                                const empRecs = empDates[dateStr];
                                const empRec = empRecs[0];
                                const empKey = `${dateStr}_${empRec.id}`;
                                const isDateExpanded = expandedDates[empKey];
                                
                                return (
                                  <Accordion 
                                    key={dateStr} 
                                    expanded={!!isDateExpanded}
                                    onChange={() => toggleDate(empKey)}
                                    sx={{ m: 1, boxShadow: 'none', border: '1px solid rgba(255,255,255,0.05)', '&:before': { display: 'none' } }}
                                  >
                                    <AccordionSummary expandIcon={<ChevronDown />}>
                                      <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', width: '100%' }}>
                                        <Typography sx={{ fontWeight: 600, minWidth: 120 }}>{formatDate(dateStr)}</Typography>
                                        <Chip label={empRec.status} size="small" color={getStatusChipColor(empRec.status)} sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                                        <Typography variant="body2" color="text.secondary">Total: {empRec.formatted_worked_hours || '0h 0m'}</Typography>
                                        <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                                          <Button size="small" variant="outlined" color="secondary" onClick={(e) => { e.stopPropagation(); handlePreContinue(empRec); }} sx={{ fontSize: '0.7rem' }}>
                                            Pre-Continue
                                          </Button>
                                          <Button size="small" variant="outlined" onClick={(e) => { e.stopPropagation(); handleOpenOtModal(empRec); }} sx={{ fontSize: '0.7rem' }}>
                                            Pre-Approve OT
                                          </Button>
                                        </Box>
                                      </Box>
                                    </AccordionSummary>
                                    <AccordionDetails sx={{ p: 2, pt: 0 }}>
                                      {renderSessions(empRec)}
                                    </AccordionDetails>
                                  </Accordion>
                                );
                              })}
                            </AccordionDetails>
                          </Accordion>
                        );
                      })
                    ) : (
                      // NORMAL MODE (Date -> Employee -> Sessions)
                      Object.keys(groupedRecords).sort((a, b) => new Date(b) - new Date(a)).map(dateStr => {
                        const dayRecords = groupedRecords[dateStr];
                        const presentCount = dayRecords.filter(r => r.status === 'PRESENT').length;
                        const lateCount = dayRecords.filter(r => r.status === 'LATE').length;
                        const halfDayCount = dayRecords.filter(r => r.status === 'HALF_DAY').length;
                        const absentCount = dayRecords.filter(r => r.status === 'ABSENT').length;
                        const isDateExpanded = expandedDates[dateStr];

                        return (
                          <Accordion 
                            key={dateStr} 
                            expanded={!!isDateExpanded} 
                            onChange={() => toggleDate(dateStr)}
                            sx={{ mb: 1, bgcolor: 'background.neutral', '&:before': { display: 'none' }, borderRadius: '8px !important' }}
                          >
                            <AccordionSummary expandIcon={<ChevronDown />}>
                              <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                                <Typography sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                                  {formatDate(dateStr)} ({dayRecords.length} Employees)
                                </Typography>
                                {!isDateExpanded && (
                                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                    <Typography variant="caption">Present: {presentCount}</Typography>
                                    <Typography variant="caption">Late: {lateCount}</Typography>
                                    <Typography variant="caption">Half Day: {halfDayCount}</Typography>
                                    <Typography variant="caption">Absent: {absentCount}</Typography>
                                  </Box>
                                )}
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails sx={{ p: 0, bgcolor: 'background.default' }}>
                              {isDateExpanded && dayRecords.map(empRec => {
                                const empKey = `${dateStr}_${empRec.id}`;
                                const isEmpExpanded = expandedEmployees[empKey];
                                
                                return (
                                  <Accordion 
                                    key={empRec.id} 
                                    expanded={!!isEmpExpanded}
                                    onChange={() => toggleEmployee(dateStr, empRec.id)}
                                    sx={{ m: 1, boxShadow: 'none', border: '1px solid rgba(255,255,255,0.05)', '&:before': { display: 'none' } }}
                                  >
                                    <AccordionSummary expandIcon={<ChevronDown />}>
                                      <Box sx={{ display: 'flex', gap: 3, alignItems: 'center', width: '100%' }}>
                                        <Typography sx={{ fontWeight: 600, minWidth: 150 }}>{empRec.employee_name}</Typography>
                                        <Chip label={empRec.status} size="small" color={getStatusChipColor(empRec.status)} sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                                        <Typography variant="body2" color="text.secondary">Total: {empRec.formatted_worked_hours || '0h 0m'}</Typography>
                                        <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                                          <Button size="small" variant="outlined" color="secondary" onClick={(e) => { e.stopPropagation(); handlePreContinue(empRec); }} sx={{ fontSize: '0.7rem' }}>
                                            Pre-Continue
                                          </Button>
                                          <Button size="small" variant="outlined" onClick={(e) => { e.stopPropagation(); handleOpenOtModal(empRec); }} sx={{ fontSize: '0.7rem' }}>
                                            Pre-Approve OT
                                          </Button>
                                        </Box>
                                      </Box>
                                    </AccordionSummary>
                                    <AccordionDetails sx={{ p: 2, pt: 0 }}>
                                      {isEmpExpanded && renderSessions(empRec)}
                                    </AccordionDetails>
                                  </Accordion>
                                );
                              })}
                            </AccordionDetails>
                          </Accordion>
                        );
                      })
                    )
                  )}
                  
                  {totalRecords > pageSize && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                      <Pagination count={Math.ceil(totalRecords / pageSize)} page={page} onChange={(e, v) => setPage(v)} color="primary" />
                    </Box>
                  )}
                </Box>
              ) : (
                /* Non-Admin Employee View */
                <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                  <Table>
                    <TableBody>
                      {history.length === 0 ? (
                        <TableRow>
                          <TableCell align="center" sx={{ py: 4, color: 'text.secondary' }}>No attendance logs available.</TableCell>
                        </TableRow>
                      ) : (
                        history.map((rec) => (
                          <TableRow key={rec.id}>
                            <TableCell colSpan={1} sx={{ p: 0 }}>
                              <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2, pb: 1.5, borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main' }}>
                                    {formatDate(rec.date)}
                                  </Typography>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                                    <Typography variant="body2"><strong>Daily Total:</strong> {rec.formatted_worked_hours || '0h 0m'}</Typography>
                                    <Chip label={rec.status} size="small" color={getStatusChipColor(rec.status)} sx={{ fontWeight: 600, fontSize: '0.75rem' }} />
                                  </Box>
                                </Box>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                  {rec.sessions && rec.sessions.length > 0 ? (
                                    rec.sessions.map((sess, idx) => (
                                      <Box key={sess.id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 1.5, borderRadius: '8px', bgcolor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', flexWrap: 'wrap', gap: 2 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, minWidth: '250px' }}>
                                          <Typography variant="body2" sx={{ fontWeight: 700, minWidth: '80px', color: 'text.secondary' }}>Session {idx + 1}</Typography>
                                          <Box>
                                            <Typography variant="body2" sx={{ fontWeight: 600 }}>🌅 {sess.check_in_time || '--'} &rarr; 🌇 {sess.check_out_time || 'Active'}</Typography>
                                            <Typography variant="caption" color="text.secondary">Duration: {sess.working_hours || '--'}</Typography>
                                          </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 0.5 }}>Check In</Typography>
                                            {sess.captured_image ? (
                                              <img src={getMediaUrl(sess.captured_image)} alt="Checkin" onClick={() => setPreviewImage(getMediaUrl(sess.captured_image))} style={{ width: 48, height: 48, borderRadius: '6px', objectFit: 'cover', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)' }} />
                                            ) : '--'}
                                          </Box>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mb: 0.5 }}>Check Out</Typography>
                                            {sess.check_out_captured_image ? (
                                              <img src={getMediaUrl(sess.check_out_captured_image)} alt="Checkout" onClick={() => setPreviewImage(getMediaUrl(sess.check_out_captured_image))} style={{ width: 48, height: 48, borderRadius: '6px', objectFit: 'cover', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)' }} />
                                            ) : '--'}
                                          </Box>
                                        </Box>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: '300px' }}>
                                          {sess.check_in_address && <Typography variant="caption" sx={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={sess.check_in_address}>📍 <strong>In:</strong> {sess.check_in_address}</Typography>}
                                          {sess.check_out_address && <Typography variant="caption" sx={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={sess.check_out_address}>📍 <strong>Out:</strong> {sess.check_out_address}</Typography>}
                                        </Box>
                                      </Box>
                                    ))
                                  ) : (
                                    <Typography variant="caption" color="text.secondary">No sessions recorded.</Typography>
                                  )}
                                </Box>
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

            </CardContent>
          </Card>
        </Grid>
        {/* Overtime Approval Registry for Admin/Managers */}
        {isAdmin && (
          <Grid item xs={12}>
            <Card sx={{ border: (theme) => `1px solid ${theme.palette.divider}` }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                  Overtime Approvals Registry
                </Typography>
                <TableContainer component={Paper} elevation={0}>
                  <Table>
                    <TableHead sx={{ bgcolor: 'background.neutral' }}>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Shift</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Worked Hours</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Current OT</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {overtimeRequests.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                            No overtime requests found.
                          </TableCell>
                        </TableRow>
                      ) : (
                        overtimeRequests.map((ot) => (
                          <TableRow key={ot.id} hover>
                            <TableCell sx={{ fontWeight: 600 }}>{ot.employee_name}</TableCell>
                            <TableCell>{formatDate(ot.date)}</TableCell>
                            <TableCell>
                              {ot.shift_start && ot.shift_end ? (
                                `${ot.shift_start} - ${ot.shift_end} (${ot.shift_duration})`
                              ) : (
                                'N/A'
                              )}
                            </TableCell>
                            <TableCell>
                              {ot.shift_duration && ot.shift_duration !== 'N/A' ? (
                                `${(parseFloat(ot.shift_duration) + parseFloat(ot.hours || 0)).toFixed(2)} hrs`
                              ) : (
                                `${parseFloat(ot.hours || 0).toFixed(2)} hrs`
                              )}
                            </TableCell>
                            <TableCell>{ot.hours} hrs</TableCell>
                            <TableCell>
                              <Chip 
                                label={ot.status} 
                                color={ot.status === 'APPROVED' ? 'success' : ot.status === 'REJECTED' ? 'error' : 'warning'} 
                                size="small" 
                                sx={{ fontWeight: 600 }}
                              />
                            </TableCell>
                            <TableCell>
                              {ot.status === 'PENDING' ? (
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                  <Button 
                                    variant="contained" 
                                    color="success" 
                                    size="small"
                                    onClick={() => handleApproveOvertime(ot.id)}
                                  >
                                    Approve
                                  </Button>
                                  <Button 
                                    variant="outlined" 
                                    color="error" 
                                    size="small"
                                    onClick={() => handleRejectOvertime(ot.id)}
                                  >
                                    Reject
                                  </Button>
                                </Box>
                              ) : (
                                <Typography variant="body2" color="text.secondary">
                                  Processed by {ot.approved_by_name || 'System'}
                                </Typography>
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
        )}

        {isAdmin && adminTab === 2 && (
          <Grid item xs={12}>
            <AttendanceCorrections firmId={selectedFirm} user={user} />
          </Grid>
        )}

        {/* Overtime Status for Employees */}
        {!isAdmin && (
          <Grid item xs={12}>
            <Card sx={{ border: (theme) => `1px solid ${theme.palette.divider}` }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                  My Overtime Records
                </Typography>
                <TableContainer component={Paper} elevation={0}>
                  <Table>
                    <TableHead sx={{ bgcolor: 'background.neutral' }}>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Hours Pre-Approved</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Approved By</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {overtimeRequests.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                            No overtime logs recorded.
                          </TableCell>
                        </TableRow>
                      ) : (
                        overtimeRequests.map((ot) => (
                          <TableRow key={ot.id} hover>
                            <TableCell>{formatDate(ot.date)}</TableCell>
                            <TableCell>{ot.hours} hours</TableCell>
                            <TableCell>
                              <Chip 
                                label={ot.status} 
                                color={ot.status === 'APPROVED' ? 'success' : ot.status === 'REJECTED' ? 'error' : 'warning'} 
                                size="small" 
                                sx={{ fontWeight: 600 }}
                              />
                            </TableCell>
                            <TableCell>
                              {ot.approved_by_name || (ot.status === 'PENDING' ? 'Awaiting Approval' : 'System Auto')}
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

      {/* Dialog for Admin to pre-approve overtime */}
      <Dialog open={otModalOpen} onClose={() => setOtModalOpen(false)}>
        <DialogTitle sx={{ fontWeight: 700 }}>Pre-Approve Overtime</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Pre-approve hours of overtime for <strong>{selectedRecordForOt?.employee_name}</strong> on date <strong>{selectedRecordForOt && formatDate(selectedRecordForOt.date)}</strong>.
          </Typography>
          <TextField
            fullWidth
            label="Overtime Hours"
            type="number"
            value={otHours}
            onChange={(e) => setOtHours(e.target.value)}
            inputProps={{ step: 0.5, min: 0.5 }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOtModalOpen(false)} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleSubmitPreApprovedOt} variant="contained" color="primary">
            Pre-Approve
          </Button>
        </DialogActions>
      </Dialog>

      {/* Camera Capture Dialog */}
      <Dialog open={openCameraModal} onClose={() => { stopCamera(); setOpenCameraModal(false); }} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          Verify {cameraMode === 'IN' ? 'Check-In' : 'Check-Out'} Identity
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Workforce OS requires real-time photo capture to complete your {cameraMode === 'IN' ? 'check-in' : 'check-out'}.
          </Typography>
          {cameraError ? (
            <Alert severity="error" sx={{ width: '100%' }}>{cameraError}</Alert>
          ) : (
            <Box sx={{ width: '100%', aspectRatio: '4/3', bgcolor: 'black', borderRadius: '8px', overflow: 'hidden', position: 'relative' }}>
              <video
                id="webcam-preview"
                autoPlay
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={() => { stopCamera(); setOpenCameraModal(false); }} variant="outlined">
            Cancel
          </Button>
          {!cameraError && (
            <Button onClick={handleCaptureAndProcess} variant="contained" color="success">
              Capture & {cameraMode === 'IN' ? 'Clock In' : 'Clock Out'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Photo Preview Dialog */}
      <Dialog open={!!previewImage} onClose={() => setPreviewImage(null)} maxWidth="sm">
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>Verification Photo</Typography>
          <Button onClick={() => setPreviewImage(null)} size="small" variant="text" sx={{ minWidth: 0, p: 0.5 }}>Close</Button>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <img src={previewImage} alt="Preview" style={{ width: '100%', height: 'auto', display: 'block' }} />
        </DialogContent>
      </Dialog>
      
      {editModalOpen && (
        <EditAttendanceModal
          open={editModalOpen}
          onClose={() => setEditModalOpen(false)}
          session={selectedSessionForEdit}
          onSaved={() => {
            fetchHistory();
            fetchCurrentState();
            if (isAdmin) fetchAdminRecords();
          }}
        />
      )}

      <Dialog open={photoViewerOpen} onClose={() => setPhotoViewerOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Photo Preview
          <IconButton onClick={() => setPhotoViewerOpen(false)}><X /></IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, bgcolor: '#000', display: 'flex', justifyContent: 'center' }}>
          {viewPhotoUrl && <img src={viewPhotoUrl} alt="Preview" style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain' }} />}
        </DialogContent>
      </Dialog>

      {/* OT Prompt Modal */}
      <Dialog open={otPromptModal} onClose={() => setOtPromptModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Shift Completed</DialogTitle>
        <DialogContent>
          <Box sx={{ p: 2 }}>
            <Typography variant="body1">
              {otPromptMessage || "Your shift has already ended. Would you like to continue working as Overtime?"}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, justifyContent: 'space-between' }}>
          <Button onClick={() => setOtPromptModal(false)} color="inherit">
            Cancel
          </Button>
          <Box>
            <Button
              variant="outlined"
              color="primary"
              sx={{ mr: 1 }}
              onClick={async () => {
                try {
                  await api.post('/attendance/correction/', {
                    request_type: 'CONTINUE_SHIFT',
                    reason: 'Requested to continue shift after shift end'
                  });
                  setOtPromptModal(false);
                  alert('Continue Shift request sent to Admin.');
                  fetchCurrentState();
                } catch (e) {
                  alert(getError(e, "Failed to request Continue Shift"));
                }
              }}
            >
              Continue Shift
            </Button>
            <Button
              variant="contained"
              color="secondary"
              onClick={async () => {
                try {
                  await api.post('/attendance/overtime/request-ot/', { reason: 'Requested OT after shift end' });
                  setOtPromptModal(false);
                  alert('Overtime request sent to Admin.');
                  fetchOvertimeRequests();
                  fetchCurrentState();
                } catch (e) {
                  alert(getError(e, "Failed to request OT"));
                }
              }}
            >
              Request OT
            </Button>
          </Box>
        </DialogActions>
      </Dialog>
      
      <RaiseCorrectionModal
        open={correctionModalOpen}
        onClose={() => setCorrectionModalOpen(false)}
        onSaved={() => {
          fetchHistory();
          fetchCurrentState();
        }}
      />
    </Box>
  );
}
