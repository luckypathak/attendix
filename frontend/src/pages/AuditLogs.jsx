import React, { useState, useEffect } from 'react';
import { 
  Box, Card, CardContent, Typography, Table, TableBody, 
  TableCell, TableContainer, TableHead, TableRow, Paper, Chip 
} from '@mui/material';
import { FileClock, User } from 'lucide-react';
import api from '../services/api';

export default function AuditLogs() {
  const [logs, setLogs] = useState([
    { id: 1, username: 'sarah_hr', action: 'UPDATE', model_name: 'LeaveRequest', object_id: '4', changes: { detail: 'Approved Sick Leave request for john_dev' }, ip_address: '192.168.1.10', timestamp: '2026-07-05 10:15:32' },
    { id: 2, username: 'john_dev', action: 'CREATE', model_name: 'Attendance', object_id: '15', changes: { created: 'Checked in at 09:05 AM' }, ip_address: '192.168.1.42', timestamp: '2026-07-05 09:05:01' },
    { id: 3, username: 'attendix_admin', action: 'CREATE', model_name: 'Shift', object_id: '2', changes: { created: 'Created Night Shift (9 PM - 6 AM)' }, ip_address: '192.168.1.1', timestamp: '2026-07-05 08:30:15' }
  ]);

  useEffect(() => {
    // In a real environment, fetch from API:
    // fetchLogs();
  }, []);

  const getActionColor = (action) => {
    switch (action) {
      case 'CREATE': return 'success';
      case 'UPDATE': return 'info';
      case 'DELETE': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Security Audit Trails
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track database mutations, system updates, and verify credentials security logs.
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
            <FileClock size={20} /> System Audit Trail Logs
          </Typography>

          <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.05)' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Actor</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Model / Record</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Modification Details</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>IP Address</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                      No audit trails logged.
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell sx={{ fontWeight: 600 }}>{log.username || 'System'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={log.action} 
                          size="small" 
                          color={getActionColor(log.action)} 
                          sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                        />
                      </TableCell>
                      <TableCell>{log.model_name} #{log.object_id}</TableCell>
                      <TableCell>{JSON.stringify(log.changes)}</TableCell>
                      <TableCell>{log.ip_address}</TableCell>
                      <TableCell>{log.timestamp}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
