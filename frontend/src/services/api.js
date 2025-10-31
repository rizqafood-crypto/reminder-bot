import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ================== AUTH ==================

export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (userData) =>
    api.post('/auth/register', userData),

  getCurrentUser: () =>
    api.get('/auth/me')
};

// ================== CLIENTS ==================

export const clientsAPI = {
  getAll: (params) =>
    api.get('/clients', { params }),

  getById: (id) =>
    api.get(`/clients/${id}`),

  create: (data) =>
    api.post('/clients', data),

  update: (id, data) =>
    api.put(`/clients/${id}`, data),

  delete: (id) =>
    api.delete(`/clients/${id}`),

  addContact: (id, data) =>
    api.post(`/clients/${id}/contacts`, data),

  getInteractions: (id) =>
    api.get(`/clients/${id}/interactions`),

  addInteraction: (id, data) =>
    api.post(`/clients/${id}/interactions`, data)
};

// ================== CAMPAIGNS ==================

export const campaignsAPI = {
  getAll: (params) =>
    api.get('/campaigns', { params }),

  getById: (id) =>
    api.get(`/campaigns/${id}`),

  create: (data) =>
    api.post('/campaigns', data),

  update: (id, data) =>
    api.put(`/campaigns/${id}`, data),

  delete: (id) =>
    api.delete(`/campaigns/${id}`),

  addTeamMember: (id, userId) =>
    api.post(`/campaigns/${id}/team`, { user_id: userId }),

  getAnalytics: (id) =>
    api.get(`/campaigns/${id}/analytics`),

  addAnalytics: (id, data) =>
    api.post(`/campaigns/${id}/analytics`, data)
};

// ================== CONTENT ==================

export const contentAPI = {
  getAll: (params) =>
    api.get('/content', { params }),

  getById: (id) =>
    api.get(`/content/${id}`),

  create: (data) =>
    api.post('/content', data),

  update: (id, data) =>
    api.put(`/content/${id}`, data),

  delete: (id) =>
    api.delete(`/content/${id}`),

  approve: (id, data) =>
    api.post(`/content/${id}/approve`, data),

  getComments: (id) =>
    api.get(`/content/${id}/comments`),

  addComment: (id, data) =>
    api.post(`/content/${id}/comments`, data),

  getCalendar: (params) =>
    api.get('/content/calendar', { params }),

  getTags: () =>
    api.get('/tags'),

  createTag: (data) =>
    api.post('/tags', data)
};

// ================== TASKS ==================

export const tasksAPI = {
  getAll: (params) =>
    api.get('/tasks', { params }),

  getById: (id) =>
    api.get(`/tasks/${id}`),

  create: (data) =>
    api.post('/tasks', data),

  update: (id, data) =>
    api.put(`/tasks/${id}`, data),

  delete: (id) =>
    api.delete(`/tasks/${id}`),

  getComments: (id) =>
    api.get(`/tasks/${id}/comments`),

  addComment: (id, data) =>
    api.post(`/tasks/${id}/comments`, data),

  getBoard: (params) =>
    api.get('/tasks/board', { params }),

  getMyTasks: () =>
    api.get('/tasks/my-tasks')
};

// ================== FINANCE ==================

export const financeAPI = {
  // Invoices
  getInvoices: (params) =>
    api.get('/invoices', { params }),

  getInvoice: (id) =>
    api.get(`/invoices/${id}`),

  createInvoice: (data) =>
    api.post('/invoices', data),

  updateInvoice: (id, data) =>
    api.put(`/invoices/${id}`, data),

  // Payments
  createPayment: (data) =>
    api.post('/payments', data),

  // Expenses
  getExpenses: (params) =>
    api.get('/expenses', { params }),

  createExpense: (data) =>
    api.post('/expenses', data),

  // Time Tracking
  getTimeEntries: (params) =>
    api.get('/time-entries', { params }),

  createTimeEntry: (data) =>
    api.post('/time-entries', data),

  // Reports
  getFinancialSummary: (params) =>
    api.get('/reports/financial-summary', { params })
};

// ================== DASHBOARD ==================

export const dashboardAPI = {
  getOverview: () =>
    api.get('/dashboard/overview'),

  getActivity: (params) =>
    api.get('/dashboard/activity', { params }),

  getTeamPerformance: () =>
    api.get('/dashboard/team-performance')
};

// ================== NOTIFICATIONS ==================

export const notificationsAPI = {
  getAll: (params) =>
    api.get('/notifications', { params }),

  markAsRead: (id) =>
    api.put(`/notifications/${id}/read`)
};

// ================== USERS ==================

export const usersAPI = {
  getAll: (params) =>
    api.get('/users', { params }),

  getById: (id) =>
    api.get(`/users/${id}`),

  update: (id, data) =>
    api.put(`/users/${id}`, data)
};

// ================== WORKFLOWS ==================

export const workflowsAPI = {
  getAll: () =>
    api.get('/workflows'),

  create: (data) =>
    api.post('/workflows', data)
};

// ================== INTEGRATIONS ==================

export const integrationsAPI = {
  getAll: () =>
    api.get('/integrations'),

  create: (data) =>
    api.post('/integrations', data)
};

// ================== SEARCH ==================

export const searchAPI = {
  search: (query) =>
    api.get('/search', { params: { q: query } })
};

export default api;
