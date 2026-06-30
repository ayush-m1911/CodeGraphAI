/**
 * Purpose:
 * Axios-based API client wrappers connecting the React frontend to the FastAPI backend service.
 *
 * Role in CodeGraphAI:
 * Handles HTTP request packaging and response mapping for all backend endpoint interactions.
 *
 * Key Responsibilities:
 * - Configure Axios instances with host routes (defaulting to localhost:8000) and headers.
 * - Expose POST /index endpoint integrations for repository cloning and indexing.
 * - Expose POST /chat endpoint integration for hybrid-retrieval chat.
 * - Expose GET /graph endpoint integration to load constructed knowledge graphs.
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  /**
   * Indexes a GitHub repository.
   * @param {string} repoUrl - The github repository URL
   */
  indexRepository: async (repoUrl) => {
    try {
      const response = await client.post('/index', { repo_url: repoUrl });
      return response.data;
    } catch (error) {
      console.error('API Index Repository Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  /**
   * Sends a user query to chat with the codebase.
   * @param {string} question - The user question
   */
  chat: async (question) => {
    try {
      const response = await client.post('/chat', { question });
      return response.data;
    } catch (error) {
      console.error('API Chat Error:', error);
      throw error.response?.data || error.message || error;
    }
  },

  /**
   * Fetches the complete repository knowledge graph.
   */
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
