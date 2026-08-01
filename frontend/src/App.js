import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/ui/header-1';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Evaluate from './pages/Evaluate';
import Results from './pages/Results';
import Management from './pages/Management';
import EvaluationHistory from './pages/EvaluationHistory';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import AdminDashboard from './pages/AdminDashboard';
import './App.css';
import { getStoredUser } from './services/authStorage';

function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const setAppLoading = (isLoading, message = '') => {
    setLoading(isLoading);
    setLoadingMessage(message);
  };

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="App">
        <Header />
        {loading && (
          <div className="app-loading-overlay">
            <div className="app-loading-container">
              <div className="loading-spinner"></div>
              <p className="loading-message">{loadingMessage || 'Processing...'}</p>
            </div>
          </div>
        )}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="/student"
            element={
              <ProtectedRoute roles={['student']}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/teacher"
            element={
              <ProtectedRoute roles={['teacher']}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard setLoading={setAppLoading} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/evaluate"
            element={
              <ProtectedRoute roles={['teacher', 'admin']}>
                <Evaluate setLoading={setAppLoading} />
              </ProtectedRoute>
            }
          />
          <Route path="/results/:evaluationId" element={<Results />} />
          <Route
            path="/management"
            element={
              <ProtectedRoute roles={['admin']}>
                <Management setLoading={setAppLoading} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <EvaluationHistory setLoading={setAppLoading} />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

function ProtectedRoute({ children, roles }) {
  const user = getStoredUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default App;
