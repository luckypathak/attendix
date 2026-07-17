import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

// Layout & Pages
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Companies from './pages/Companies';
import Dashboard from './pages/Dashboard';
import Employees from './pages/Employees';
import Attendance from './pages/Attendance';
import AttendanceAnalytics from './pages/AttendanceAnalytics';
import Leaves from './pages/Leaves';
import Payroll from './pages/Payroll';
import Reimbursements from './pages/Reimbursements';
import Todos from './pages/Todos';
import SMSGateway from './pages/SMSGateway';
import AuditLogs from './pages/AuditLogs';

// Higher order component for route shielding
function PrivateRoute({ children }) {
  const { user } = useSelector((state) => state.auth);
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user } = useSelector((state) => state.auth);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth login gate */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Private workspaces portal */}
        <Route 
          path="/" 
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="employees" element={<Employees />} />
          <Route path="attendance" element={<Attendance />} />
          <Route path="attendance-analytics" element={<AttendanceAnalytics />} />
          <Route path="leaves" element={<Leaves />} />
          <Route path="payroll" element={<Payroll />} />
          <Route path="reimbursements" element={<Reimbursements />} />
          <Route path="todos" element={<Todos />} />
          <Route path="sms" element={<SMSGateway />} />
          <Route path="audit" element={<AuditLogs />} />
          <Route path="companies" element={<Companies />} />
        </Route>


        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
