import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiMenu, FiX } from 'react-icons/fi';
import { getStoredUser, clearStoredUser } from '../services/authStorage';
import { clearAuthTokens } from '../services/api';
import './Navigation.css';

const Navigation = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const user = getStoredUser();
  const role = user?.role;

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    clearAuthTokens();
    clearStoredUser();
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <span className="logo-icon">📝</span>
          AI Examiner
        </Link>

        <button 
          className="mobile-menu-toggle"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>

        <ul className={`nav-menu ${isMobileMenuOpen ? 'active' : ''}`}>
          <li className="nav-item">
            <Link 
              to="/" 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Home
            </Link>
          </li>
          <li className="nav-item">
            <Link 
              to="/dashboard" 
              className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
          </li>
          <li className="nav-item">
            <Link 
              to="/evaluate" 
              className={`nav-link nav-link-primary ${isActive('/evaluate') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Evaluate Now
            </Link>
          </li>
          <li className="nav-item">
            <Link 
              to="/management" 
              className={`nav-link ${isActive('/management') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Management
            </Link>
          </li>
          <li className="nav-item">
            <Link 
              to="/history" 
              className={`nav-link ${isActive('/history') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              History
            </Link>
          </li>
          {!user && (
            <li className="nav-item">
              <Link
                to="/login"
                className={`nav-link ${isActive('/login') ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Login
              </Link>
            </li>
          )}
          {user && role === 'student' && (
            <li className="nav-item">
              <Link
                to="/student"
                className={`nav-link ${isActive('/student') ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Student
              </Link>
            </li>
          )}
          {user && role === 'teacher' && (
            <li className="nav-item">
              <Link
                to="/teacher"
                className={`nav-link ${isActive('/teacher') ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Teacher
              </Link>
            </li>
          )}
          {user && role === 'admin' && (
            <li className="nav-item">
              <Link
                to="/admin"
                className={`nav-link ${isActive('/admin') ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Admin
              </Link>
            </li>
          )}
          {user && (
            <li className="nav-item">
              <Link
                to="/"
                className="nav-link"
                onClick={() => {
                  handleLogout();
                  setIsMobileMenuOpen(false);
                }}
              >
                Logout
              </Link>
            </li>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navigation;
