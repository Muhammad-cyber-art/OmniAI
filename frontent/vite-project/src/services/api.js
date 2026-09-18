/**
 * ChronosAI — Centralized API Client
 * Base: http://localhost:8000/api/v1/
 *
 * Auth endpoints (apps/users/urls.py):
 *   POST  auth/login/           → { access, refresh }         (SimpleJWT)
 *   POST  auth/register/        → { success, data: {id, email, role} }
 *   POST  auth/google/          → { success, tokens: {access, refresh}, user: {...} }
 *   POST  auth/token/refresh/   → { access, refresh }
 *   POST  auth/logout/          → 205 (blacklists refresh token)
 *   GET   auth/me/              → UserDetailSerializer
 *   PATCH auth/me/              → UserUpdateSerializer
 *   POST  auth/change-password/ → { success, message }
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/* ─── Axios instance ─────────────────────────────────────── */
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,   // send cookies (invite_token cookie support)
  timeout: 12000,
});

/* ─── Request interceptor: attach JWT ───────────────────── */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (err) => Promise.reject(err)
);

/* ─── Response interceptor: silent token refresh on 401 ─── */
let _refreshing = false;
let _refreshQueue = [];  // queued requests waiting for new token

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;

    // Avoid refresh loop on the refresh endpoint itself
    if (
      err.response?.status === 401 &&
      !original._retried &&
      !original.url?.includes('token/refresh')
    ) {
      original._retried = true;

      if (_refreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve, reject) => {
          _refreshQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      _refreshing = true;
      const refresh = localStorage.getItem('refresh_token');

      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
            refresh,
          });
          const newAccess = data.access;
          localStorage.setItem('access_token', newAccess);
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh);

          _refreshQueue.forEach(({ resolve }) => resolve(newAccess));
          _refreshQueue = [];
          _refreshing = false;

          original.headers.Authorization = `Bearer ${newAccess}`;
          return api(original);
        } catch {
          _refreshQueue.forEach(({ reject }) => reject());
          _refreshQueue = [];
          _refreshing = false;
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }

    return Promise.reject(err);
  }
);

export default api;

/* ══════════════════════════════════════════════════════════
   AUTH API
   ══════════════════════════════════════════════════════════ */
export const authApi = {
  /**
   * Login with email + password.
   * POST /auth/login/
   * Body:    { email, password }
   * Returns: { access, refresh, ...custom claims }
   */
  login: (email, password) =>
    api.post('/auth/login/', { email, password }),

  /**
   * Register new user.
   * POST /auth/register/
   * Body:    { email, username, password, password_confirm, first_name, last_name, role }
   * Returns: { success, data: { id, email, role, joined_group? } }
   */
  register: (payload) =>
    api.post('/auth/register/', payload),

  /**
   * Google OAuth login / auto-register.
   * POST /auth/google/
   * Body:    { id_token: "<GSI credential>", invite_token?: "..." }
   * Returns: { success, tokens: { access, refresh }, user: { id, email, username, full_name, role } }
   */
  googleAuth: (idToken, inviteToken = null) =>
    api.post('/auth/google/', {
      id_token: idToken,
      ...(inviteToken ? { invite_token: inviteToken } : {}),
    }),

  /**
   * Refresh access token (called automatically by interceptor).
   * POST /auth/token/refresh/
   * Body:    { refresh }
   * Returns: { access, refresh }
   */
  refreshToken: (refresh) =>
    api.post('/auth/token/refresh/', { refresh }),

  /**
   * Logout — blacklists refresh token.
   * POST /auth/logout/
   * Body:    { refresh }
   */
  logout: (refresh) =>
    api.post('/auth/logout/', { refresh }),

  /**
   * Get current user profile.
   * GET /auth/me/
   * Returns: UserDetailSerializer (id, email, username, first_name, last_name, full_name, role, profile)
   */
  getMe: () =>
    api.get('/auth/me/'),

  /**
   * Update current user safe fields.
   * PATCH /auth/me/
   */
  updateMe: (data) =>
    api.patch('/auth/me/', data),

  /**
   * Change password.
   * POST /auth/change-password/
   * Body: { old_password, new_password, new_password_confirm }
   */
  changePassword: (data) =>
    api.post('/auth/change-password/', data),
};

/* ══════════════════════════════════════════════════════════
   BILLING API
   ══════════════════════════════════════════════════════════ */
export const billingApi = {
  getPlans:        ()     => api.get('/billing/plans/'),
  getWallet:       ()     => api.get('/billing/wallet/'),
  getTransactions: ()     => api.get('/billing/transactions/'),
  getQuota:        ()     => api.get('/billing/quota/'),
};

/* ══════════════════════════════════════════════════════════
   GROUPS API
   ══════════════════════════════════════════════════════════ */
export const groupsApi = {
  list:           ()        => api.get('/groups/'),
  create:         (data)    => api.post('/groups/', data),
  detail:         (id)      => api.get(`/groups/${id}/`),
  generateInvite: (id)      => api.post(`/groups/${id}/generate-invite/`),
  joinByToken:    (token)   => api.post(`/groups/join/${token}/`),
};

/* ══════════════════════════════════════════════════════════
   CURRICULUM API
   ══════════════════════════════════════════════════════════ */
export const curriculumApi = {
  getCourses:  ()                 => api.get('/curriculum/courses/'),
  getCourse:   (id)               => api.get(`/curriculum/courses/${id}/`),
  getLessons:  (courseId)         => api.get(`/curriculum/courses/${courseId}/lessons/`),
  getLesson:   (courseId, lesId)  => api.get(`/curriculum/courses/${courseId}/lessons/${lesId}/`),
};

/* ══════════════════════════════════════════════════════════
   SIMULATION API
   ══════════════════════════════════════════════════════════ */
export const simulationApi = {
  getScenarios:  ()           => api.get('/simulations/cases/'),
  createSession: (caseId)     => api.post('/simulations/sessions/', { case: caseId }),
  getMySessions: ()           => api.get('/simulations/sessions/my/'),
  getSession:    (id)         => api.get(`/simulations/sessions/${id}/`),
};
