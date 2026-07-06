import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { 
  Box, Card, CardContent, Grid, Button, Typography, 
  TextField, Checkbox, FormControlLabel, List, ListItem, 
  ListItemButton, ListItemIcon, ListItemText, Alert, 
  CircularProgress 
} from '@mui/material';
import { ClipboardList, Plus } from 'lucide-react';
import api from '../services/api';

export default function Todos() {
  const { user } = useSelector((state) => state.auth);

  // Todo states
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [dueDate, setDueDate] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    try {
      const res = await api.get('/todos/');
      setTodos(res.data.results || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateTodo = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await api.post('/todos/', {
        title,
        description: desc,
        due_date: dueDate || null
      });
      setMessage({ type: 'success', text: 'Task created successfully!' });
      setTitle('');
      setDesc('');
      setDueDate('');
      fetchTodos();
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to create task.' });
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

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, letterSpacing: '-0.5px' }}>
          Task Workspace
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track employee todo items, assign operational responsibilities, and monitor task status.
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {/* Create Task Form */}
        <Grid item xs={12} md={5}>
          <Card>
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

                <TextField
                  type="date"
                  fullWidth
                  label="Due Date"
                  InputLabelProps={{ shrink: true }}
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  sx={{ mb: 3 }}
                />

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
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ClipboardList size={20} /> My Task Checklist
              </Typography>

              {todos.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 6, textAlign: 'center' }}>
                  No tasks assigned. Have a great day!
                </Typography>
              ) : (
                <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                  {todos.map((todo) => {
                    const labelId = `checkbox-list-label-${todo.id}`;

                    return (
                      <ListItem
                        key={todo.id}
                        disablePadding
                        sx={{ 
                          mb: 1.5, 
                          borderRadius: 3, 
                          bgcolor: 'background.default',
                          border: '1px solid rgba(255,255,255,0.03)'
                        }}
                      >
                        <ListItemButton role={undefined} onClick={() => handleToggleTodo(todo.id)} dense>
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
                              <>
                                <Typography component="span" variant="body2" color="text.secondary">
                                  {todo.description}
                                </Typography>
                                {todo.due_date && (
                                  <Typography component="span" variant="caption" display="block" color="error.main" sx={{ mt: 0.5, fontWeight: 600 }}>
                                    Due: {todo.due_date}
                                  </Typography>
                                )}
                              </>
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
    </Box>
  );
}
