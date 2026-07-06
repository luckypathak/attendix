import React, { useState, useContext, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  AppBar, Box, IconButton, Toolbar, Typography, Avatar, 
  Menu, MenuItem, Divider, Tooltip, useTheme, Select, Chip
} from '@mui/material';
import { Menu as MenuIcon, Sun, Moon, LogOut, User as UserIcon } from 'lucide-react';
import { logout } from '../features/authSlice';
import { ColorModeContext } from '../main';
import Sidebar from './Sidebar';
import api from '../services/api';

const drawerWidth = 240;

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { toggleColorMode } = useContext(ColorModeContext);
  
  const { user } = useSelector((state) => state.auth);

  const [firms, setFirms] = useState([]);
  const [selectedFirm, setSelectedFirm] = useState(localStorage.getItem('selectedFirmId') || 'ALL');

  useEffect(() => {
    if (user && (user.role === 'SUPER_ADMIN' || user.role === 'COMPANY_ADMIN')) {
      fetchFirms();
    }
  }, [user]);

  const fetchFirms = async () => {
    try {
      const res = await api.get('/company/firms/');
      setFirms(res.data.results || res.data);
    } catch (e) {
      console.error("Failed to load firms", e);
    }
  };

  const handleFirmChange = (event) => {
    const val = event.target.value;
    setSelectedFirm(val);
    localStorage.setItem('selectedFirmId', val);
    window.location.reload();
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      
      {/* Top Header */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
          bgcolor: 'background.paper',
          color: 'text.primary',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between', px: { xs: 2, md: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700, letterSpacing: '-0.3px' }}>
              Workspace OS
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            {/* Firm Selector for Admins */}
            {(user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN') && (
              <Select
                value={selectedFirm}
                onChange={handleFirmChange}
                size="small"
                variant="outlined"
                sx={{ 
                  minWidth: 140, 
                  height: 36, 
                  borderRadius: '8px', 
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  bgcolor: 'background.paper',
                  border: '1px solid rgba(255,255,255,0.05)',
                  '& .MuiOutlinedInput-notchedOutline': { border: 'none' }
                }}
              >
                <MenuItem value="ALL">All Firms</MenuItem>
                {firms.map((f) => (
                  <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                ))}
              </Select>
            )}

            {/* Read-only Firm badge for Managers */}
            {user?.role === 'MANAGER' && user?.firm_name && (
              <Chip 
                label={`Firm: ${user.firm_name}`} 
                size="small"
                variant="outlined"
                color="primary"
                sx={{ fontWeight: 600, height: 32, borderRadius: '8px' }} 
              />
            )}

            {/* Theme Toggle */}
            <Tooltip title="Toggle Theme">
              <IconButton onClick={toggleColorMode} color="inherit">
                {theme.palette.mode === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </IconButton>
            </Tooltip>

            {/* Profile Menu */}
            <Tooltip title="Account settings">
              <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0 }}>
                <Avatar 
                  sx={{ 
                    bgcolor: 'primary.main', 
                    width: 36, 
                    height: 36, 
                    fontWeight: 700, 
                    fontSize: '0.9rem' 
                  }}
                >
                  {user?.username?.substring(0, 2).toUpperCase() || 'US'}
                </Avatar>
              </IconButton>
            </Tooltip>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              PaperProps={{
                sx: {
                  borderRadius: '12px',
                  mt: 1.5,
                  minWidth: 200,
                  boxShadow: (theme) => theme.palette.mode === 'dark'
                    ? '0 10px 40px 0 rgba(0, 0, 0, 0.4)'
                    : '0 10px 40px 0 rgba(31, 38, 135, 0.08)',
                  border: (theme) => `1px solid ${theme.palette.divider}`
                }
              }}
            >
              <Box sx={{ px: 2, py: 1.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.email || 'No email associated'}
                </Typography>
              </Box>
              <Divider />
              <MenuItem onClick={handleProfileMenuClose} disabled>
                <UserIcon size={16} style={{ marginRight: 10 }} />
                Profile
              </MenuItem>
              <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
                <LogOut size={16} style={{ marginRight: 10 }} />
                Sign Out
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Sidebar 
        mobileOpen={mobileOpen} 
        handleDrawerToggle={handleDrawerToggle} 
      />

      {/* Content wrapper */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: '64px',
          bgcolor: 'background.default',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
