import axios from 'axios';

// Connect to FastAPI backend (support environment variable for production deployment)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatic JWT Bearer token injection
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('optrail_jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // Authentication & RBAC
  getDemoUsers: async () => {
    const response = await client.get('/auth/demo-users');
    return response.data;
  },

  login: async (username, password) => {
    const response = await client.post('/auth/login', { username, password });
    if (response.data?.access_token) {
      localStorage.setItem('optrail_jwt_token', response.data.access_token);
    }
    return response.data;
  },

  getMe: async () => {
    const response = await client.get('/auth/me');
    return response.data;
  },

  switchRole: async (username) => {
    const response = await client.post('/auth/switch-role', { username });
    if (response.data?.access_token) {
      localStorage.setItem('optrail_jwt_token', response.data.access_token);
    }
    return response.data;
  },

  createTask: async (taskData) => {
    const response = await client.post('/tasks', taskData);
    return response.data;
  },

  // Health & Root Status
  getStatus: async () => {
    try {
      const response = await client.get('/');
      return response.data;
    } catch (err) {
      console.warn('API getStatus offline, using local state', err);
      return null;
    }
  },

  // Executive Dashboard KPIs
  getKPI: async () => {
    try {
      const response = await client.get('/kpi');
      return response.data;
    } catch (err) {
      console.warn('API getKPI offline', err);
      return null;
    }
  },

  // Trigger CP-SAT Optimization
  optimizeSchedule: async (horizon = 'weekly', bundlingBonus = 15) => {
    const response = await client.post('/optimize', {
      horizon,
      bundling_bonus: bundlingBonus,
    });
    return response.data;
  },

  // Get Timetable Schedule
  getSchedule: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.day) params.append('day', filters.day);
    if (filters.section_id) params.append('section_id', filters.section_id);
    if (filters.department_id) params.append('department_id', filters.department_id);

    const response = await client.get(`/schedule?${params.toString()}`);
    return response.data;
  },

  // Get Block Windows
  getBlocks: async (sectionId = null) => {
    const url = sectionId ? `/blocks?section_id=${sectionId}` : '/blocks';
    const response = await client.get(url);
    return response.data;
  },

  // Get Asset Registry
  getAssets: async (criticality = null) => {
    const url = criticality ? `/assets?criticality=${criticality}` : '/assets';
    const response = await client.get(url);
    return response.data;
  },

  // Get Task Backlog
  getTasks: async (priority = null) => {
    const url = priority ? `/tasks?priority=${priority}` : '/tasks';
    const response = await client.get(url);
    return response.data;
  },

  // Get Train Conflicts
  getConflicts: async () => {
    const response = await client.get('/conflicts');
    return response.data;
  },

  // Get Scenario List
  getScenarios: async () => {
    const response = await client.get('/scenarios');
    return response.data;
  },

  // Run What-If Scenario
  runScenario: async (scenarioId, horizon = 'weekly') => {
    const response = await client.post('/scenario', {
      scenario_id: scenarioId,
      horizon: horizon,
    });
    return response.data;
  },

  // Get Benchmark Comparison (Before vs After)
  getBenchmark: async (horizon = 'weekly') => {
    const response = await client.get(`/benchmark?horizon=${horizon}`);
    return response.data;
  },

  // Get Resources / Crews
  getResources: async () => {
    const response = await client.get('/resources');
    return response.data;
  },
};
