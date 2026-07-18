import React from 'react';
import { NavLink } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { 
  Drawer, List, ListItem, ListItemButton, ListItemIcon, 
  ListItemText, Toolbar, Typography, Divider, Box 
} from '@mui/material';
import { 
  LayoutDashboard, CalendarRange, FileSpreadsheet, 
  WalletCards, CheckSquare, MessageSquareShare, FileClock, Shield,
  Users, Landmark, BarChart2, MapPin, Settings
} from 'lucide-react';

const drawerWidth = 240;

export default function Sidebar({ open, mobileOpen, handleDrawerToggle }) {
  const { user } = useSelector((state) => state.auth);
  const role = user?.role || 'EMPLOYEE';

  const menuItems = [
    { text: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'Employees', path: '/employees', icon: <Users size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'] },
    { text: 'Attendance', path: '/attendance', icon: <CalendarRange size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'Attendance Analytics', path: '/attendance-analytics', icon: <BarChart2 size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER'] },
    { text: 'Leaves', path: '/leaves', icon: <FileSpreadsheet size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'Payroll', path: '/payroll', icon: <WalletCards size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'Reimbursement', path: '/reimbursements', icon: <WalletCards size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'Tasks', path: '/todos', icon: <CheckSquare size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN', 'EMPLOYEE'] },
    { text: 'SMS Gateway', path: '/sms', icon: <MessageSquareShare size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN'] },
    { text: 'Audit Logs', path: '/audit', icon: <FileClock size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN'] },
    { text: 'Live Tracking', path: '/live-tracking', icon: <MapPin size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN'] },
    { text: 'Companies', path: '/companies', icon: <Landmark size={20} />, roles: ['SUPER_ADMIN'] },
    { text: 'Settings', path: '/settings', icon: <Settings size={20} />, roles: ['SUPER_ADMIN', 'COMPANY_ADMIN'] },
  ];


  const filteredMenu = menuItems.filter(item => item.roles.includes(role));

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Toolbar sx={{ px: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Shield size={24} className="text-primary-main" style={{ color: '#9d4edd' }} />
        <Typography variant="h6" noWrap sx={{ fontWeight: 800, background: 'linear-gradient(45deg, #9d4edd, #00f5d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Attendix OS
        </Typography>
      </Toolbar>
      <Divider />
      
      <List sx={{ px: 2, py: 3, flexGrow: 1 }}>
        {filteredMenu.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
            <ListItemButton
              component={NavLink}
              to={item.path}
              onClick={handleDrawerToggle}
              style={({ isActive }) => ({
                backgroundColor: isActive ? 'rgba(157, 78, 221, 0.08)' : 'transparent',
                borderRadius: '12px',
                color: isActive ? '#9d4edd' : 'inherit',
              })}
              sx={{
                '&:hover': {
                  borderRadius: '12px',
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{ fontSize: '0.9rem', fontWeight: 600 }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Divider />
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
          v1.0.0 Stable
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
    >
      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, borderRight: 'none' },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, borderRight: (theme) => `1px solid ${theme.palette.divider}` },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </Box>
  );
}
