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
