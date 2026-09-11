// =============================================================
// Authentication Context
// Manages the logged-in user state throughout the app
//
// DEMO MODE: clicking "Continue as Farmer/Buyer/FPO" sets a fake user
// LIVE MODE: calls FastAPI /api/v1/auth/login and /api/v1/auth/register
//            and stores JWT access + refresh tokens in localStorage
// =============================================================

import { createContext, useContext, useState, useEffect } from 'react';
import { DEMO_USERS } from '../data/demoData';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On app start, restore user from localStorage so they stay logged in
  useEffect(() => {
    const savedUser = localStorage.getItem('krishilink_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('krishilink_user');
      }
    }
    setLoading(false);
  }, []);

  // Demo login: instantly logs in with a pre-defined demo user (no API call)
  const demoLogin = (role) => {
    const demoUser = DEMO_USERS[role];
    if (demoUser) {
      setUser(demoUser);
      localStorage.setItem('krishilink_user', JSON.stringify(demoUser));
    }
  };

  // Real login: calls FastAPI /api/v1/auth/login, stores JWT tokens
  const login = async (email, password) => {
    const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const json = await res.json();

      if (!res.ok) {
        let msg = json?.message;
        if (!msg || msg === 'Validation failed') {
          if (typeof json?.detail === 'string') {
            msg = json.detail;
          } else if (Array.isArray(json?.details) && json.details.length > 0) {
            msg = json.details.map(d => d.msg || `${d.loc?.slice(-1)[0] || 'Field'}: invalid`).join('. ');
          } else if (Array.isArray(json?.detail) && json.detail.length > 0) {
            msg = json.detail.map(d => d.msg || 'Invalid field').join('. ');
          } else {
            msg = 'Invalid email/phone or password.';
          }
        }
        return { success: false, message: msg };
      }

      // API shape: { success, data: { user, access_token, refresh_token, ... } }
      const { user: apiUser, access_token, refresh_token } = json.data;
      const normalised = { ...apiUser, name: apiUser.full_name, id: String(apiUser.id) };

      setUser(normalised);
      localStorage.setItem('krishilink_user', JSON.stringify(normalised));
      localStorage.setItem('krishilink_access_token', access_token);
      localStorage.setItem('krishilink_refresh_token', refresh_token);

      return { success: true, user: normalised };
    } catch (err) {
      if (err.name === 'AbortError') {
        return { success: false, message: 'Server timed out. Is the backend running?' };
      }
      console.warn('[useAuth] Login API unreachable:', err.message);
      return {
        success: false,
        message: 'Could not connect to authentication server. Please check your connection and try again.',
      };
    }
  };

  // Real register: calls FastAPI /api/v1/auth/register, stores JWT tokens
  const register = async (userData) => {
    const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: userData.name,
          email: userData.email,
          phone: userData.phone || null,
          password: userData.password,
          role: userData.role || 'farmer',
          location: userData.location || null,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const json = await res.json();

      if (!res.ok) {
        let msg = json?.message;
        if (!msg || msg === 'Validation failed') {
          if (typeof json?.detail === 'string') {
            msg = json.detail;
          } else if (Array.isArray(json?.details) && json.details.length > 0) {
            msg = json.details.map(d => d.msg || `${d.loc?.slice(-1)[0] || 'Field'}: invalid`).join('. ');
          } else if (Array.isArray(json?.detail) && json.detail.length > 0) {
            msg = json.detail.map(d => d.msg || 'Invalid field').join('. ');
          } else {
            msg = 'Registration failed. Please check your details.';
          }
        }
        return { success: false, message: msg };
      }

      const { user: apiUser, access_token, refresh_token } = json.data;
      const normalised = { ...apiUser, name: apiUser.full_name, id: String(apiUser.id) };

      setUser(normalised);
      localStorage.setItem('krishilink_user', JSON.stringify(normalised));
      localStorage.setItem('krishilink_access_token', access_token);
      localStorage.setItem('krishilink_refresh_token', refresh_token);

      return { success: true, user: normalised };
    } catch (err) {
      if (err.name === 'AbortError') {
        return { success: false, message: 'Server timed out. Is the backend running?' };
      }
      console.warn('[useAuth] Register API unreachable:', err.message);
      return {
        success: false,
        message: 'Could not connect to registration server. Please check your connection and try again.',
      };
    }
  };

  // Logout: clear tokens + user state
  const logout = () => {
    setUser(null);
    localStorage.removeItem('krishilink_user');
    localStorage.removeItem('krishilink_access_token');
    localStorage.removeItem('krishilink_refresh_token');
  };

  const value = {
    user,
    loading,
    isLoggedIn: !!user,
    isFarmer: user?.role === 'farmer',
    isBuyer: user?.role === 'buyer',
    isFPO: user?.role === 'fpo',
    login,
    register,
    demoLogin,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook — usage: const { user, logout } = useAuth();
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
