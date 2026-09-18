import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor - attach auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', data.access);
          error.config.headers.Authorization = `Bearer ${data.access}`;
          return apiClient.request(error.config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ===== Billing / Plans API =====
export const billingApi = {
  getPlans: () => apiClient.get('/billing/plans/'),
  getWallet: () => apiClient.get('/billing/wallet/'),
  getTransactions: () => apiClient.get('/billing/transactions/'),
};

// ===== Auth API =====
export const authApi = {
  login: (data) => apiClient.post('/auth/login/', data),
  register: (data) => apiClient.post('/auth/register/', data),
  googleAuth: (token) => apiClient.post('/auth/google/', { token }),
  refreshToken: (refresh) => apiClient.post('/auth/token/refresh/', { refresh }),
  getProfile: () => apiClient.get('/users/me/'),
};

// ===== Groups API =====
export const groupsApi = {
  list: () => apiClient.get('/groups/'),
  create: (data) => apiClient.post('/groups/', data),
  detail: (id) => apiClient.get(`/groups/${id}/`),
  generateInvite: (id) => apiClient.post(`/groups/${id}/generate-invite/`),
  join: (token) => apiClient.post(`/groups/join/${token}/`),
};

// ===== Curriculum API =====
export const curriculumApi = {
  getCourses: () => apiClient.get('/curriculum/courses/'),
  getCourse: (id) => apiClient.get(`/curriculum/courses/${id}/`),
  getLessons: (courseId) => apiClient.get(`/curriculum/courses/${courseId}/lessons/`),
  getLesson: (courseId, lessonId) =>
    apiClient.get(`/curriculum/courses/${courseId}/lessons/${lessonId}/`),
};

// ===== Simulation API =====
export const simulationApi = {
  getScenarios: () => apiClient.get('/simulation/scenarios/'),
  createSession: (scenarioId) =>
    apiClient.post('/simulation/sessions/', { scenario: scenarioId }),
  getSession: (id) => apiClient.get(`/simulation/sessions/${id}/`),
};
