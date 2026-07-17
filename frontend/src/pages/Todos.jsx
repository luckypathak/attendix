import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useOutletContext } from 'react-router-dom';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, Checkbox, FormControlLabel, List, ListItem, 
  ListItemButton, ListItemIcon, ListItemText, Alert, 
  CircularProgress, Tabs, Tab, MenuItem, Dialog, DialogTitle,
  DialogContent, DialogActions, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, IconButton, Chip
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import { ClipboardList, Plus, Trash2, Edit2, AlertCircle, Clock } from 'lucide-react';
import api from '../services/api';
import { formatDate, formatDateTime } from '../utils/format';

export default function Todos() {
  const { user } = useSelector((state) => state.auth);
  const { selectedFirm } = useOutletContext();
  const isManagement = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN' || user?.role === 'MANAGER';
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN';

  // Todo states
  const [todos, setTodos] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [tabValue, setTabValue] = useState(0);

  // Form states
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [dueDate, setDueDate] = useState(null);
  const [targetEmployeeId, setTargetEmployeeId] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // Edit Modal states
  const [openEditModal, setOpenEditModal] = useState(false);
  const [editingTodo, setEditingTodo] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editDueDate, setEditDueDate] = useState(null);
  const [editPostponeReason, setEditPostponeReason] = useState('');
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState(null);

  const fetchTodos = async () => {
    try {
      const res = await api.get('/todos/', { params: { firm: selectedFirm } });
      setTodos(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchEmployees = async () => {
    if (!isManagement) return;
    try {
      const res = await api.get('/employees/', { params: { firm: selectedFirm } });
      setEmployees(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchTodos();
    fetchEmployees();
  }, [selectedFirm]);

  const handleCreateTodo = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await api.post('/todos/', {
        title,
        description: desc,
        due_date: dueDate ? dueDate.format('YYYY-MM-DD') : null,
        employee_id: targetEmployeeId || null
      });
      setMessage({ type: 'success', text: 'Task created and assigned successfully!' });
      setTitle('');
      setDesc('');
      setDueDate(null);
      setTargetEmployeeId('');
      fetchTodos();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to create task.' });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTodo = async (id) => {
    try {
      await api.post(`/todos/${id}/toggle-complete/`);
      fetchTodos();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteTodo = async (id) => {
    if (!window.confirm("Are you sure you want to delete this task?")) return;
    try {
      await api.delete(`/todos/${id}/`);
      fetchTodos();
    } catch (e) {
      console.error(e);
      alert(e.response?.data?.detail || 'Failed to delete task.');
    }
  };

  const handleOpenEditModal = (todo) => {
    setEditingTodo(todo);
    setEditTitle(todo.title);
    setEditDesc(todo.description || '');
    setEditDueDate(todo.due_date ? dayjs(todo.due_date) : null);
    setEditPostponeReason(todo.postpone_reason || '');
    setEditError(null);
    setOpenEditModal(true);
  };

  const handleCloseEditModal = () => {
    setOpenEditModal(false);
    setEditingTodo(null);
  };

  const handleUpdateTodo = async (e) => {
    e.preventDefault();
    setEditLoading(true);
    setEditError(null);

    const formattedDate = editDueDate ? editDueDate.format('YYYY-MM-DD') : null;
    const isPostponed = editingTodo.due_date && formattedDate && formattedDate > editingTodo.due_date;

    if (isPostponed && (!editPostponeReason || !editPostponeReason.trim())) {
      setEditError("A reason is required to extend the due date.");
      setEditLoading(false);
      return;
    }

    try {
      await api.patch(`/todos/${editingTodo.id}/`, {
        title: editTitle,
        description: editDesc,
        due_date: formattedDate,
        postpone_reason: isPostponed ? editPostponeReason : editingTodo.postpone_reason
      });
      fetchTodos();
      handleCloseEditModal();
    } catch (err) {
      console.error(err);
      setEditError(err.response?.data?.postpone_reason || err.response?.data?.detail || 'Failed to update task.');
    } finally {
      setEditLoading(false);
    }
  };

  const shouldBlink = (todo) => {
    if (todo.is_completed) return false;
    if (!todo.due_date || !todo.employee_shift_end_time) return false;
    
    // Check if due date is today
    const todayStr = dayjs().format('YYYY-MM-DD');
    if (todo.due_date !== todayStr) return false;
    
    // Check shift end warning (within 15 minutes before or any time after)
    const [endHour, endMin] = todo.employee_shift_end_time.split(':').map(Number);
    const now = new Date();
    const currentHour = now.getHours();
    const currentMin = now.getMinutes();
    
    const shiftEndTotalMinutes = endHour * 60 + endMin;
    const currentTotalMinutes = currentHour * 60 + currentMin;
    
    return currentTotalMinutes >= (shiftEndTotalMinutes - 15);
  };

  const myTasks = todos.filter(todo => todo.employee === user.id);

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
            Task Workspace
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage operational workflows, assign daily checklist tasks, and log completed actions.
          </Typography>
        </Box>

        {isManagement && (
          <Tabs value={tabValue} onChange={(e, val) => setTabValue(val)} sx={{ mb: 4, borderBottom: 1, borderColor: 'divider' }}>
            <Tab label="My Checklist" />
            <Tab label="Workforce Dashboard" />
          </Tabs>
        )}

        {tabValue === 0 ? (
          <Grid container spacing={4}>
            {/* Create Task Form */}
            <Grid item xs={12} md={5}>
              <Card sx={{ borderRadius: '16px' }}>
                <CardContent sx={{ p: 4 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                    Assign New Task
                  </Typography>

                  {message && <Alert severity={message.type} sx={{ mb: 3, borderRadius: 2 }}>{message.text}</Alert>}

                  <Box component="form" onSubmit={handleCreateTodo}>
                    <TextField
                      fullWidth
                      label="Task Title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      sx={{ mb: 2 }}
                      required
                    />

                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      label="Task Description"
                      value={desc}
                      onChange={(e) => setDesc(e.target.value)}
                      sx={{ mb: 2 }}
                    />

                    {isManagement && (
                      <TextField
                        select
                        fullWidth
                        label="Assign To"
                        value={targetEmployeeId}
                        onChange={(e) => setTargetEmployeeId(e.target.value)}
                        sx={{ mb: 2 }}
                      >
                        <MenuItem value=""><em>Assign to Myself</em></MenuItem>
                        {employees.map((emp) => (
                          <MenuItem key={emp.user_id} value={emp.user_id}>
                            {emp.first_name} {emp.last_name} ({emp.username})
                          </MenuItem>
                        ))}
                      </TextField>
                    )}

                    <Box sx={{ mb: 3 }}>
                      <DatePicker
                        label="Due Date"
                        value={dueDate}
                        onChange={(newValue) => setDueDate(newValue)}
                        slotProps={{ textField: { fullWidth: true } }}
                      />
                    </Box>

                    <Button
                      type="submit"
                      variant="contained"
                      fullWidth
                      disabled={loading}
                      startIcon={<Plus size={16} />}
                    >
                      Create Task
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Task Checklist */}
            <Grid item xs={12} md={7}>
              <Card sx={{ borderRadius: '16px' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ClipboardList size={20} /> My Checklist
                  </Typography>

                  {myTasks.length === 0 ? (
                    <Typography variant="body2" color="text.secondary" sx={{ py: 6, textAlign: 'center' }}>
                      No tasks assigned to you. Have a great day!
                    </Typography>
                  ) : (
                    <List sx={{ width: '100%' }}>
                      {myTasks.map((todo) => {
                        const blinking = shouldBlink(todo);
                        const labelId = `checkbox-list-label-${todo.id}`;

                        return (
                          <ListItem
                            key={todo.id}
                            secondaryAction={
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                <IconButton size="small" onClick={() => handleOpenEditModal(todo)}>
                                  <Edit2 size={16} />
                                </IconButton>
                                {isAdmin && (
                                  <IconButton size="small" color="error" onClick={() => handleDeleteTodo(todo.id)}>
                                    <Trash2 size={16} />
                                  </IconButton>
                                )}
                              </Box>
                            }
                            sx={{ 
                              mb: 1.5, 
                              borderRadius: '12px', 
                              bgcolor: 'background.neutral',
                              border: (theme) => `1px solid ${theme.palette.divider}`,
                              ...(blinking && {
                                animation: 'blink-alert 1.5s infinite alternate',
                                '@keyframes blink-alert': {
                                  '0%': { border: '1px solid rgba(239, 83, 80, 0.3)', backgroundColor: 'rgba(239, 83, 80, 0.04)' },
                                  '100%': { border: '1px solid rgba(239, 83, 80, 0.9)', backgroundColor: 'rgba(239, 83, 80, 0.15)' }
                                }
                              })
                            }}
                          >
                            <ListItemButton onClick={() => handleToggleTodo(todo.id)} dense sx={{ mr: 4 }}>
                              <ListItemIcon>
                                <Checkbox
                                  edge="start"
                                  checked={todo.is_completed}
                                  tabIndex={-1}
                                  disableRipple
                                  inputProps={{ 'aria-labelledby': labelId }}
                                />
                              </ListItemIcon>
                              <ListItemText
                                id={labelId}
                                primary={todo.title}
                                secondary={
                                  <Box component="span" sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                    <Typography variant="body2" color="text.secondary">
                                      {todo.description}
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                                      {todo.due_date && (
                                        <Chip 
                                          label={`Due: ${formatDate(todo.due_date)}`} 
                                          size="small" 
                                          color={blinking ? "error" : "default"}
                                          sx={{ fontWeight: 600, fontSize: '0.7rem' }} 
                                        />
                                      )}
                                      {blinking && (
                                        <Chip 
                                          label="Shift Ending Soon" 
                                          size="small" 
                                          color="error" 
                                          icon={<Clock size={12} />}
                                          sx={{ fontWeight: 600, fontSize: '0.7rem', animation: 'pulse 1s infinite' }} 
                                        />
                                      )}
                                      {todo.postpone_reason && (
                                        <Typography variant="caption" sx={{ color: 'warning.main', fontWeight: 500 }}>
                                          Reason for extension: "{todo.postpone_reason}"
                                        </Typography>
                                      )}
                                    </Box>
                                  </Box>
                                }
                                primaryTypographyProps={{ 
                                  fontWeight: 700,
                                  style: { textDecoration: todo.is_completed ? 'line-through' : 'none', opacity: todo.is_completed ? 0.6 : 1 } 
                                }}
                              />
                            </ListItemButton>
                          </ListItem>
                        );
                      })}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          /* Admin / Manager Complete Monitoring Board */
          <Card sx={{ borderRadius: '16px', border: (theme) => `1px solid ${theme.palette.divider}` }}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead sx={{ bgcolor: 'background.neutral' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Employee Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Task Title</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Created Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Due Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Completion Date</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Postpone Reason</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {todos.map((todo) => {
                    const blinking = shouldBlink(todo);
                    return (
                      <TableRow 
                        key={todo.id} 
                        hover
                        sx={{
                          ...(blinking && {
                            animation: 'blink-table-row 1.5s infinite alternate',
                            '@keyframes blink-table-row': {
                              '0%': { backgroundColor: 'rgba(239, 83, 80, 0.02)' },
                              '100%': { backgroundColor: 'rgba(239, 83, 80, 0.1)' }
                            }
                          })
                        }}
                      >
                        <TableCell sx={{ fontWeight: 600 }}>{todo.employee_name || 'N/A'}</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{todo.title}</TableCell>
                        <TableCell>{todo.description || '—'}</TableCell>
                        <TableCell>{formatDate(todo.created_at?.split('T')[0])}</TableCell>
                        <TableCell>
                          <Chip 
                            label={formatDate(todo.due_date)} 
                            size="small" 
                            color={blinking ? "error" : "default"} 
                            sx={{ fontWeight: 600 }}
                          />
                        </TableCell>
                        <TableCell>{todo.completed_at ? formatDateTime(todo.completed_at) : 'Pending'}</TableCell>
                        <TableCell sx={{ color: 'warning.main', fontSize: '0.8rem', fontStyle: 'italic' }}>
                          {todo.postpone_reason || '—'}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={todo.is_completed ? "Completed" : "In Progress"} 
                            color={todo.is_completed ? "success" : (blinking ? "error" : "warning")} 
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <IconButton size="small" onClick={() => handleOpenEditModal(todo)}>
                              <Edit2 size={16} />
                            </IconButton>
                            {isAdmin && (
                              <IconButton size="small" color="error" onClick={() => handleDeleteTodo(todo.id)}>
                                <Trash2 size={16} />
                              </IconButton>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        )}

        {/* Edit Dialog */}
        <Dialog 
          open={openEditModal} 
          onClose={handleCloseEditModal}
          maxWidth="sm"
          fullWidth
          PaperProps={{ sx: { borderRadius: '16px' } }}
        >
          <DialogTitle sx={{ fontWeight: 800 }}>Update Task Details</DialogTitle>
          <form onSubmit={handleUpdateTodo}>
            <DialogContent>
              {editError && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{editError}</Alert>}
              
              <TextField
                fullWidth
                label="Task Title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                sx={{ mb: 2.5 }}
                required
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Task Description"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                sx={{ mb: 2.5 }}
              />

              <Box sx={{ mb: 3 }}>
                <DatePicker
                  label="Due Date"
                  value={editDueDate}
                  onChange={(newValue) => setEditDueDate(newValue)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Box>

              {/* Show Postpone Reason if the new date is later than the original date */}
              {editingTodo?.due_date && editDueDate && editDueDate.format('YYYY-MM-DD') > editingTodo.due_date && (
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Why are you extending this task's timeline?"
                  value={editPostponeReason}
                  onChange={(e) => setEditPostponeReason(e.target.value)}
                  sx={{ mb: 2 }}
                  required
                />
              )}
            </DialogContent>
            <DialogActions sx={{ p: 2.5, gap: 1 }}>
              <Button onClick={handleCloseEditModal} variant="outlined">
                Cancel
              </Button>
              <Button 
                type="submit" 
                variant="contained" 
                disabled={editLoading}
              >
                Save Updates
              </Button>
            </DialogActions>
          </form>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
}
