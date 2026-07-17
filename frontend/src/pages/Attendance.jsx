import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  CircularProgress, Alert, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Paper, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField
} from '@mui/material';
import { MapPin, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import api, { getMediaUrl } from '../services/api';
import { formatDate } from '../utils/format';

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
  const [overtimeRequests, setOvertimeRequests] = useState([]);
  const [otModalOpen, setOtModalOpen] = useState(false);
  const [selectedRecordForOt, setSelectedRecordForOt] = useState(null);
  const [otHours, setOtHours] = useState('2.0');

  // Camera states
  const [openCameraModal, setOpenCameraModal] = useState(false);
  const [stream, setStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);


  useEffect(() => {
    fetchHistory();
    fetchOvertimeRequests();
    if (isAdmin) {
      fetchAdminRecords();
    }
  }, [isAdmin, selectedFirm]);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/attendance/records/history/');
      setHistory(response.data);
      
      const getCheckInDateTime = (dateStr, timeStr) => {
        const [year, month, day] = dateStr.split('-').map(Number);
        const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
        let hours = 9, minutes = 0;
        if (match) {
          hours = parseInt(match[1]);
          minutes = parseInt(match[2]);
          const ampm = match[3].toUpperCase();
          if (ampm === 'PM' && hours < 12) hours += 12;
          if (ampm === 'AM' && hours === 12) hours = 0;
        } else {
          const parts = timeStr.split(':');
          if (parts.length >= 2) {
            hours = parseInt(parts[0]);
            minutes = parseInt(parts[1]);
          }
        }
        return new Date(year, month - 1, day, hours, minutes);
      };

      const openRecord = response.data.find(rec => rec.check_in_time && !rec.check_out_time);
      if (openRecord) {
        const checkInDt = getCheckInDateTime(openRecord.date, openRecord.check_in_time);
        const nowDt = new Date();
        const elapsedHours = (nowDt - checkInDt) / (1000 * 60 * 60);
        
        if (elapsedHours < 20) {
          setAttendanceToday(openRecord);
          setIsClockedIn(true);
        } else {
          setAttendanceToday(null);
          setIsClockedIn(false);
        }
      } else {
        setAttendanceToday(null);
        setIsClockedIn(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAdminRecords = async () => {
    try {
      const response = await api.get('/attendance/records/', { params: { firm: selectedFirm } });
      setAdminRecords(response.data.results || response.data);
    } catch (e) {
      console.error(e);
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
    setOpenCameraModal(true);
    startCamera();
  };

  const handleCaptureAndClockIn = () => {
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
      await performClockIn(blob);
    }, 'image/jpeg', 0.85);
  };

  const performClockIn = async (photoBlob) => {
    if (!gpsData) return;
    setGpsLoading(true);
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
    } catch (e) {
      setGpsError(getError(e, "Failed to check in."));
    } finally {
      setGpsLoading(false);
    }
  };

  const handleClockIn = () => {
    handleOpenClockInCamera();
  };


  const handleClockOut = async () => {
    if (!gpsData) return;
    try {
      const response = await api.post('/attendance/records/check-out/', {
        latitude: gpsData.latitude,
        longitude: gpsData.longitude,
        accuracy: gpsData.accuracy,
        address: address,
        device_info: `Web Browser (${navigator.userAgent.substring(0, 50)})`
      });
      setIsClockedIn(false);
      setAttendanceToday(response.data);
      setGpsData(null);
      setAddress('');
      fetchHistory();
      fetchOvertimeRequests();
    } catch (e) {
      setGpsError(getError(e, "Failed to check out."));
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

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Attendance Console
        </Typography>
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
                  <Clock size={48} color={isClockedIn ? '#00f5d4' : '#6c757d'} style={{ margin: '0 auto 16px' }} />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {isClockedIn ? 'Currently Clocked In' : 'Currently Clocked Out'}
                  </Typography>
                  {attendanceToday && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Check-in time: {attendanceToday.check_in_time} {attendanceToday.check_out_time ? `| Check-out time: ${attendanceToday.check_out_time}` : ''}
                    </Typography>
                  )}
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
                <Box sx={{ width: '100%', display: 'flex', gap: 2 }}>
                  {attendanceToday && attendanceToday.check_in_time && attendanceToday.check_out_time ? (
                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      disabled
                      sx={{ py: 1.5, '&.Mui-disabled': { color: 'text.secondary', bgcolor: 'rgba(255,255,255,0.05)' } }}
                    >
                      Shift Completed Today
                    </Button>
                  ) : isClockedIn ? (
                    <Button
                      variant="contained"
                      color="secondary"
                      fullWidth
                      size="large"
                      disabled={!gpsData}
                      onClick={handleClockOut}
                      sx={{ py: 1.5 }}
                    >
                      Clock Out
                    </Button>
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

              <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                <Table>
                  <TableHead sx={{ bgcolor: 'background.neutral' }}>
                    <TableRow>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Employee</TableCell>}
                      <TableCell sx={{ fontWeight: 700 }}>Photo</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>In</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Out</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Locations (In / Out)</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      {isAdmin && <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>}
                    </TableRow>

                  </TableHead>
                  <TableBody>
                    {(isAdmin ? adminRecords : history).length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={isAdmin ? 7 : 5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                          No attendance logs available.
                        </TableCell>
                      </TableRow>
                    ) : (
                      (isAdmin ? adminRecords : history).map((rec) => (
                        <TableRow key={rec.id}>
                          {isAdmin && <TableCell sx={{ fontWeight: 600 }}>{rec.employee_name}</TableCell>}
                          <TableCell>
                            {rec.captured_image ? (
                               <img 
                                 src={getMediaUrl(rec.captured_image)} 
                                 alt="Checkin" 
                                 style={{ width: 40, height: 40, borderRadius: '6px', objectFit: 'cover', border: '1px solid rgba(255,255,255,0.08)' }} 
                               />
                            ) : '--'}
                          </TableCell>
                          <TableCell>{formatDate(rec.date)}</TableCell>
                          <TableCell>{rec.check_in_time || '--'}</TableCell>

                          <TableCell>{rec.check_out_time || '--'}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {rec.check_in_address && (
                                <Typography variant="caption" sx={{ display: 'block', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={rec.check_in_address}>
                                  📍 <strong>In:</strong> {rec.check_in_address}
                                </Typography>
                              )}
                              {rec.check_out_address && (
                                <Typography variant="caption" sx={{ display: 'block', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={rec.check_out_address}>
                                  📍 <strong>Out:</strong> {rec.check_out_address}
                                </Typography>
                              )}
                              {!rec.check_in_address && !rec.check_out_address && (
                                <Typography variant="caption" color="text.secondary">--</Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={rec.status} 
                              size="small" 
                              color={getStatusChipColor(rec.status)} 
                              sx={{ fontWeight: 600, fontSize: '0.75rem' }}
                            />
                          </TableCell>
                          {isAdmin && (
                            <TableCell>
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => handleOpenOtModal(rec)}
                                sx={{ fontSize: '0.7rem', py: 0.5 }}
                              >
                                Pre-Approve OT
                              </Button>
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
                        <TableCell sx={{ fontWeight: 700 }}>Hours Calculated</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {overtimeRequests.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                            No overtime requests found.
                          </TableCell>
                        </TableRow>
                      ) : (
                        overtimeRequests.map((ot) => (
                          <TableRow key={ot.id} hover>
                            <TableCell sx={{ fontWeight: 600 }}>{ot.employee_name}</TableCell>
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
                                <Typography variant="body2" color="text.secondary">Processed</Typography>
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
        <DialogTitle sx={{ fontWeight: 700 }}>Verify Check-In Identity</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Workforce OS requires real-time photo capture to complete your check-in.
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
            <Button onClick={handleCaptureAndClockIn} variant="contained" color="success">
              Capture & Clock In
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>

  );
}
