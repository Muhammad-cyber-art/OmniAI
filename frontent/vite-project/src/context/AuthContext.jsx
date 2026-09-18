/**
 * AuthContext — Global authentication state
 *
 * Backend response formats (from backend/apps/users/):
 *
 * LOGIN   POST /auth/login/
 *   → SimpleJWT: { access, refresh }   (user info is in JWT claims)
 *   After login → call GET /auth/me/ to get full user object
 *
 * REGISTER POST /auth/register/
 *   → { success: true, data: { id, email, role, joined_group } }
 *   NOTE: register does NOT return tokens → must login after register
 *
 * GOOGLE  POST /auth/google/
 *   → { success: true, tokens: { access, refresh }, user: { id, email, username, full_name, role } }
 *
 * ME      GET /auth/me/
 *   → UserDetailSerializer: { id, email, username, first_name, last_name,
 *       full_name, role, is_portfolio_public, is_email_verified, date_joined, profile }
 *
 * LOGOUT  POST /auth/logout/
 *   → 205 No Content (refresh token blacklisted)
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

/* ═══════════════════════════════════════════════════════════
   PROVIDER
   ═══════════════════════════════════════════════════════════ */
export function AuthProvider({ children }) {
  const [user,      setUser]      = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const initialized = useRef(false);

  /* ── Restore session on mount ─────────────────────────── */
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    authApi
      .getMe()
      .then(({ data }) => setUser(data))
      .catch(() => {
        // Token invalid or expired and refresh failed → clear
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      })
      .finally(() => setIsLoading(false));
  }, []);

  /* ── Helpers ──────────────────────────────────────────── */
  function _saveTokens(access, refresh) {
    localStorage.setItem('access_token',  access);
    localStorage.setItem('refresh_token', refresh);
  }

  function _clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  /* ─── Extract user-friendly error message from DRF ─── */
  function _extractError(err) {
    const d = err?.response?.data;
    if (!d) return err?.message || 'Tarmoq xatosi yuz berdi';

    // Custom exception handler format: { success: false, error: { message, code, details } }
    if (d.error?.message) return d.error.message;

    // SimpleJWT format: { detail: "..." }
    if (d.detail) return d.detail;

    // DRF field errors: { email: ["..."], password: ["..."] }
    if (typeof d === 'object') {
      const firstKey = Object.keys(d)[0];
      if (firstKey && Array.isArray(d[firstKey])) return d[firstKey][0];
    }

    return 'Noma\'lum xatolik yuz berdi';
  }

  /* ═══════════════════════════════════════════════════════
     LOGIN  — POST /auth/login/
     Body:   { email, password }
     Resp:   { access, refresh }
     Then:   GET /auth/me/ for full user data
     ═══════════════════════════════════════════════════════ */
  const login = useCallback(async (email, password) => {
    setAuthError(null);
    try {
      const { data: tokens } = await authApi.login(email, password);
      _saveTokens(tokens.access, tokens.refresh);

      // Fetch full profile (role, name, etc.)
      const { data: userData } = await authApi.getMe();
      setUser(userData);
      return userData;
    } catch (err) {
      const msg = _extractError(err);
      setAuthError(msg);
      throw err;
    }
  }, []);

  /* ═══════════════════════════════════════════════════════
     REGISTER — POST /auth/register/
     Body:   { email, username, password, password_confirm,
               first_name, last_name, role }
     Resp:   { success: true, data: { id, email, role } }
     NOTE:   Registration does NOT return tokens.
             Auto-login after successful registration.
     ═══════════════════════════════════════════════════════ */
  const register = useCallback(async (formData) => {
    setAuthError(null);
    try {
      // Build payload matching backend serializer fields
      const payload = {
        email:            formData.email,
        username:         formData.email.split('@')[0] + '_' + Math.random().toString(36).slice(2, 7),
        password:         formData.password,
        password_confirm: formData.password2 || formData.password_confirm,
        first_name:       formData.first_name || '',
        last_name:        formData.last_name  || '',
        role:             (formData.role || 'student').toUpperCase(),
      };

      await authApi.register(payload);

      // Auto-login after successful registration
      const { data: tokens } = await authApi.login(payload.email, payload.password);
      _saveTokens(tokens.access, tokens.refresh);

      const { data: userData } = await authApi.getMe();
      setUser(userData);
      return userData;
    } catch (err) {
      const msg = _extractError(err);
      setAuthError(msg);
      throw err;
    }
  }, []);

  /* ═══════════════════════════════════════════════════════
     GOOGLE LOGIN — POST /auth/google/
     Body:   { id_token: "<GSI credential>" }
     Resp:   { success, tokens: { access, refresh }, user: {...} }
     ═══════════════════════════════════════════════════════ */
  const googleLogin = useCallback(async (idToken, inviteToken = null) => {
    setAuthError(null);
    try {
      const { data } = await authApi.googleAuth(idToken, inviteToken);

      if (!data.success) {
        throw new Error(data.error?.message || 'Google autentifikatsiyasi muvaffaqiyatsiz');
      }

      _saveTokens(data.tokens.access, data.tokens.refresh);

      // Use user object from response directly (already complete)
      const profile = data.user;

      // Optionally enrich with full /me/ data
      let fullUser = profile;
      try {
        const { data: meData } = await authApi.getMe();
        fullUser = meData;
      } catch {
        // If /me/ fails, use embedded user data — still functional
      }

      setUser(fullUser);
      return fullUser;
    } catch (err) {
      const msg = _extractError(err);
      setAuthError(msg);
      throw err;
    }
  }, []);

  /* ═══════════════════════════════════════════════════════
     LOGOUT — POST /auth/logout/
     Body:   { refresh }
     ═══════════════════════════════════════════════════════ */
  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('refresh_token');
    try {
      if (refresh) await authApi.logout(refresh);
    } catch {
      // Ignore — still clear local state
    } finally {
      _clearTokens();
      setUser(null);
      setAuthError(null);
    }
  }, []);

  /* ═══════════════════════════════════════════════════════
     UPDATE PROFILE — PATCH /auth/me/
     ═══════════════════════════════════════════════════════ */
  const updateProfile = useCallback(async (data) => {
    const { data: updated } = await authApi.updateMe(data);
    setUser(updated);
    return updated;
  }, []);

  /* ── Context value ────────────────────────────────────── */
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    authError,
    login,
    register,
    googleLogin,
    logout,
    updateProfile,
    clearAuthError: () => setAuthError(null),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/* ─── useAuth hook ────────────────────────────────────────── */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
