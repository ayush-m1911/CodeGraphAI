/**
 * Purpose:
 * Axios-based API client for CodeGraphAI with Authentication and Multi-Tenant routing.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT Bearer token if present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('codegraph_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // ------------------- AUTH APIS -------------------
  signup: async ({ email, password, tier = 'free' }) => {
    try {
      const response = await client.post('/api/auth/signup', { email, password, tier });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  login: async ({ email, password }) => {
    try {
      const response = await client.post('/api/auth/login', { email, password });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  getMe: async () => {
    try {
      const response = await client.get('/api/auth/me');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  // ------------------- REPOSITORIES APIS -------------------
  listRepositories: async () => {
    try {
      const response = await client.get('/api/repositories');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  createRepository: async ({ name, git_url, is_private = false }) => {
    try {
      const response = await client.post('/api/repositories', { name, git_url, is_private });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  deleteRepository: async (repoId) => {
    try {
      const response = await client.delete(`/api/repositories/${repoId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  // ------------------- CONVERSATIONS APIS -------------------
  listConversations: async (repositoryId = null) => {
    try {
      const url = repositoryId ? `/api/conversations?repository_id=${repositoryId}` : '/api/conversations';
      const response = await client.get(url);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  createConversation: async ({ repository_id, title = 'New Chat' }) => {
    try {
      const response = await client.post('/api/conversations', { repository_id, title });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  getConversation: async (conversationId) => {
    try {
      const response = await client.get(`/api/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  getConversationMessages: async (conversationId) => {
    try {
      const response = await client.get(`/api/conversations/${conversationId}/messages`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  updateConversation: async (conversationId, title) => {
    try {
      const response = await client.patch(`/api/conversations/${conversationId}`, { title });
      return response.data;
    } catch (error) {
      console.error('API Update Conversation Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  deleteConversation: async (conversationId) => {
    try {
      const response = await client.delete(`/api/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message || error;
    }
  },

  // ------------------- INDEXING & SEARCH APIS -------------------
  indexRepository: async (repoUrl, repoId = null) => {
    try {
      const payload = { repo_url: repoUrl };
      if (repoId) payload.repo_id = repoId;
      const response = await client.post('/repositories/index', payload);
      return response.data;
    } catch (error) {
      console.error('API Index Repository Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  getJobStatus: async (jobId) => {
    try {
      const response = await client.get(`/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('API Get Job Status Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  chat: async ({ question, repository_id = null, conversation_id = null }) => {
    try {
      const payload = { question };
      if (repository_id) payload.repository_id = repository_id;
      if (conversation_id) payload.conversation_id = conversation_id;
      const response = await client.post('/chat', payload);
      return response.data;
    } catch (error) {
      console.error('API Chat Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  fetchGraph: async () => {
    try {
      const response = await client.get('/graph');
      return response.data;
    } catch (error) {
      console.error('API Fetch Graph Error:', error);
      throw error.response?.data || error.message || error;
    }
  },
};

export default apiService;
