import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/api';

/**
 * AuthContext — global auth state management.
 * Provides: user, isAuthenticated, isLoading, login, googleLogin, register, logout
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]         = useState(null);
  const [isLoading, setIsLoading] = useState(true); // checking existing session

  // On mount: restore session from localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authApi
        .getProfile()
        .then(({ data }) => setUser(data))
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  /** Save tokens + user to state */
  const _saveSession = useCallback((data) => {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    setUser(data.user);
  }, []);

  /** Email / password login → POST /api/auth/login/ */
  const login = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password });
    _saveSession(data);
    return data;
  }, [_saveSession]);

  /** Google OAuth login → POST /api/auth/google/ */
  const googleLogin = useCallback(async (googleIdToken) => {
    const { data } = await authApi.googleAuth(googleIdToken);
    _saveSession(data);
    return data;
  }, [_saveSession]);

  /** Email registration → POST /api/auth/register/ */
  const register = useCallback(async (payload) => {
    const { data } = await authApi.register(payload);
    _saveSession(data);
    return data;
  }, [_saveSession]);

  /** Logout — clear tokens */
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    googleLogin,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** useAuth hook — consume AuthContext anywhere */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
