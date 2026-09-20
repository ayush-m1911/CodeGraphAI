/**
 * Purpose:
 * Central React Context Provider managing Authentication, Multi-Tenant Repositories,
 * Conversational Memory Threads, and Indexing/Chat pipelines.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  // Authentication State
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('codegraph_token') || null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Multi-Tenant Repositories & History
  const [userRepos, setUserRepos] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [repoUrl, setRepoUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  
  // Conversational Memory Threads
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [previousQuestions, setPreviousQuestions] = useState([]);

  // Indexing State
  const [indexingState, setIndexingState] = useState('idle'); // idle | indexing | success | error
  const [indexingStep, setIndexingStep] = useState(0); // 0 to 5
  const [indexingPercent, setIndexingPercent] = useState(0);
  const [indexingLog, setIndexingLog] = useState('');

  // Graph and Source States
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedSource, setSelectedSource] = useState(null);

  // UI Modals & Notifications
  const [isArchModalOpen, setIsArchModalOpen] = useState(false);
  const [toast, setToast] = useState({ message: '', type: 'info' });

  const triggerToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  const closeToast = () => {
    setToast({ message: '', type: 'info' });
  };

  const indexingSteps = [
    { label: 'GitHub URL Validation', desc: 'Analyzing URL and verifying Python constraints...' },
    { label: 'Repository Ingestion', desc: 'Cloning Python source code files from GitHub...' },
    { label: 'AST-Aware Parsing', desc: 'Traversing AST structures and extracting classes & methods...' },
    { label: 'Vector Generation', desc: 'Computing local embeddings for parsed chunks...' },
    { label: 'Qdrant Store Upload', desc: 'Upserting vectors into vector database with tenant payload tags...' },
    { label: 'GraphRAG Construction', desc: 'Partitioning Neo4j & knowledge graph relationships...' }
  ];

  // ---------------- AUTHENTICATION HANDLERS ----------------

  const loadUserProfile = useCallback(async () => {
    try {
      const user = await apiService.getMe();
      setCurrentUser(user);
    } catch (err) {
      console.warn('Session expired or invalid token:', err);
      logout();
    }
  }, []);

  const loadUserRepositories = useCallback(async () => {
    if (!token) return;
    try {
      const repos = await apiService.listRepositories();
      setUserRepos(repos);
      if (repos.length > 0 && !activeRepo) {
        selectRepository(repos[0]);
      }
    } catch (err) {
      console.error('Failed to load user repositories:', err);
    }
  }, [token, activeRepo]);

  useEffect(() => {
    if (token) {
      loadUserProfile();
      loadUserRepositories();
    }
  }, [token, loadUserProfile, loadUserRepositories]);

  const login = async ({ email, password }) => {
    const data = await apiService.login({ email, password });
    localStorage.setItem('codegraph_token', data.access_token);
    setToken(data.access_token);
    setCurrentUser(data.user);
    triggerToast(`Welcome back, ${data.user.email}!`, 'success');
    await loadUserRepositories();
    return data;
  };

  const signup = async ({ email, password, tier }) => {
    const data = await apiService.signup({ email, password, tier });
    localStorage.setItem('codegraph_token', data.access_token);
    setToken(data.access_token);
    setCurrentUser(data.user);
    triggerToast(`Account created successfully (${data.user.tier} tier)!`, 'success');
    return data;
  };

  const logout = () => {
    localStorage.removeItem('codegraph_token');
    setToken(null);
    setCurrentUser(null);
    setUserRepos([]);
    setActiveRepo(null);
    setConversations([]);
    setActiveConversation(null);
    setChatMessages([]);
    triggerToast('Logged out successfully.', 'info');
  };

  // ---------------- REPOSITORY & CONVERSATIONS HANDLERS ----------------

  const selectRepository = async (repo) => {
    setActiveRepo(repo);
    setRepoName(repo.name);
    setRepoUrl(repo.git_url);
    setIndexingState('success');
    setSelectedSource(null);

    // Load conversations for this repository
    try {
      const convs = await apiService.listConversations(repo.id);
      setConversations(convs);
      if (convs.length > 0) {
        selectConversation(convs[0]);
      } else {
        createNewConversation(repo.id, 'Initial Analysis');
      }
    } catch (err) {
      console.error('Failed to load conversations for repo:', err);
    }

    // Load graph
    try {
      const graphRes = await apiService.fetchGraph();
      if (graphRes && !graphRes.error) {
        setGraphData(graphRes);
      }
    } catch (err) {
      console.error('Failed to load active graph data:', err);
    }
  };

  const selectConversation = async (conv) => {
    if (!conv) return;
    setActiveConversation(conv);
    try {
      const messages = await apiService.getConversationMessages(conv.id);
      const formatted = messages.map((m) => {
        let strategies = [];
        if (Array.isArray(m.retrieval_strategy)) {
          strategies = m.retrieval_strategy;
        } else if (typeof m.retrieval_strategy === 'string') {
          strategies = m.retrieval_strategy.split(', ').map((s) => s.trim()).filter(Boolean);
        }
        return {
          id: m.id,
          sender: m.role,
          text: m.content,
          sources: m.sources || [],
          intent: strategies[0] || m.retrieval_strategy || null,
          retrieval_strategy: strategies,
          timestamp: new Date(m.created_at)
        };
      });
      setChatMessages(formatted);
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
      setChatMessages([]);
    }
  };

  const createNewConversation = async (repoId = null, title = 'New Conversation') => {
    const targetRepoId = repoId || activeRepo?.id;
    if (!targetRepoId) return null;

    try {
      const newConv = await apiService.createConversation({
        repository_id: targetRepoId,
        title: title || 'New Conversation'
      });
      setConversations((prev) => [newConv, ...prev.filter((c) => c.id !== newConv.id)]);
      setActiveConversation(newConv);
      setChatMessages([]);
      setSelectedSource(null);
      return newConv;
    } catch (err) {
      console.error('Failed to create new conversation:', err);
      triggerToast('Could not start new chat session.', 'error');
      return null;
    }
  };

  const deleteConversation = async (convId) => {
    try {
      await apiService.deleteConversation(convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (activeConversation?.id === convId) {
        if (remaining.length > 0) {
          selectConversation(remaining[0]);
        } else {
          setActiveConversation(null);
          setChatMessages([]);
        }
      }
      triggerToast('Conversation deleted.', 'info');
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // ---------------- INDEXING HANDLER ----------------

  const indexRepository = async (url) => {
    setRepoUrl(url);
    setIndexingState('indexing');
    setIndexingStep(0);
    setIndexingPercent(0);
    setIndexingLog('Queuing indexing job...');
    setSelectedSource(null);
    setChatMessages([]);

    try {
      // 1. Register repository in multi-tenant PostgreSQL if user is logged in
      let repoRecord = null;
      if (currentUser) {
        const urlParts = url.rstrip ? url.rstrip('/').split('/') : url.replace(/\/$/, '').split('/');
        const defaultName = urlParts.slice(-2).join('/');
        try {
          repoRecord = await apiService.createRepository({
            name: defaultName,
            git_url: url,
            is_private: false
          });
          setActiveRepo(repoRecord);
          setRepoName(repoRecord.name);
          setUserRepos((prev) => [repoRecord, ...prev.filter((r) => r.id !== repoRecord.id)]);
        } catch (rErr) {
          console.warn('Repository registration notice:', rErr);
        }
      }

      // 2. Trigger backend Celery index request
      const startRes = await apiService.indexRepository(url, repoRecord?.id);
      const jobId = startRes.job_id;

      let jobFinished = false;
      let summary = null;

      while (!jobFinished) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const jobRes = await apiService.getJobStatus(jobId);

        if (jobRes.status === 'PENDING') {
          setIndexingStep(0);
          setIndexingPercent(5);
          setIndexingLog('Job is queued, waiting for Celery worker...');
        } else if (jobRes.status === 'STARTED') {
          setIndexingStep(1);
          setIndexingPercent(10);
          setIndexingLog('Celery worker started execution...');
        } else if (jobRes.status === 'PROGRESS') {
          const pct = jobRes.progress?.percent || 0;
          const desc = jobRes.progress?.description || 'Indexing repository...';
          setIndexingPercent(pct);
          setIndexingLog(desc);

          let step = 0;
          if (pct >= 100) step = 5;
          else if (pct >= 95) step = 5;
          else if (pct >= 80) step = 4;
          else if (pct >= 60) step = 5;
          else if (pct >= 40) step = 3;
          else if (pct >= 25) step = 2;
          else if (pct >= 10) step = 1;
          setIndexingStep(step);
        } else if (jobRes.status === 'SUCCESS') {
          jobFinished = true;
          summary = jobRes.result;
          setIndexingPercent(100);
          setIndexingStep(5);
        } else if (jobRes.status === 'FAILURE') {
          jobFinished = true;
          throw new Error(jobRes.error || 'Celery background task execution failed.');
        }
      }

      setRepoName(summary.repository || 'repository');
      setIndexingState('success');
      setIndexingLog('Repository successfully indexed and ready for chat reasoning.');
      triggerToast('Repository indexed successfully.', 'success');

      // Refresh conversations
      if (repoRecord) {
        const convs = await apiService.listConversations(repoRecord.id);
        setConversations(convs);
        if (convs.length > 0) {
          selectConversation(convs[0]);
        } else {
          createNewConversation(repoRecord.id, 'Initial Workspace Analysis');
        }
      }

      // Load graph representation
      try {
        const graphRes = await apiService.fetchGraph();
        if (graphRes && !graphRes.error) {
          setGraphData(graphRes);
        }
      } catch (err) {
        console.error('Failed to load active graph data:', err);
      }

    } catch (error) {
      console.error(error);
      let errMsg = 'Unable to index repository.';
      if (error.response?.data?.detail) errMsg = error.response.data.detail;
      else if (error.message) errMsg = error.message;
      setIndexingState('error');
      setIndexingLog(errMsg);
      triggerToast(errMsg, 'error');
    }
  };

  // ---------------- CHAT QUERY HANDLER ----------------

  const sendQuery = async (questionText) => {
    if (!questionText.trim()) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: questionText,
      timestamp: new Date()
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setIsChatLoading(true);

    try {
      const chatRes = await apiService.chat({
        question: questionText,
        repository_id: activeRepo?.id || null,
        conversation_id: activeConversation?.id || null
      });

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: chatRes.answer,
        sources: chatRes.sources || [],
        intent: chatRes.intent,
        retrieval_strategy: chatRes.retrieval_strategy,
        confidence: chatRes.confidence,
        contextualized_query: chatRes.contextualized_query,
        timestamp: new Date()
      };

      setChatMessages((prev) => [...prev, assistantMsg]);
      setIsChatLoading(false);

      // If active conversation had default title, update title locally and sync to backend
      const defaultTitles = [
        'New Chat', 
        'New Conversation', 
        'Initial Analysis', 
        'Initial Workspace Analysis', 
        'Untitled Thread'
      ];
      if (activeConversation && (defaultTitles.includes(activeConversation.title) || !activeConversation.title)) {
        const newTitle = questionText.slice(0, 35) + (questionText.length > 35 ? '...' : '');
        setActiveConversation((prev) => (prev ? { ...prev, title: newTitle } : prev));
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConversation.id ? { ...c, title: newTitle } : c))
        );
        apiService.updateConversation(activeConversation.id, newTitle).catch((err) => {
          console.warn('Background title update notice:', err);
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      triggerToast('Failed to fetch AI response.', 'error');
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Error communicating with CodeGraphAI backend: \n\`\`\`\n${error.detail || error.message || error}\n\`\`\`\nPlease check if your server is running and try again.`,
        sources: [],
        timestamp: new Date()
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const clearChat = () => {
    setChatMessages([]);
    setSelectedSource(null);
    triggerToast('Chat messages cleared.', 'info');
  };

  const resetAll = () => {
    setRepoUrl('');
    setRepoName('');
    setActiveRepo(null);
    setActiveConversation(null);
    setIndexingState('idle');
    setIndexingStep(0);
    setIndexingPercent(0);
    setIndexingLog('');
    setChatMessages([]);
    setGraphData({ nodes: [], edges: [] });
    setSelectedSource(null);
    triggerToast('Context reset.', 'info');
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        token,
        isAuthModalOpen,
        setIsAuthModalOpen,
        userRepos,
        activeRepo,
        selectRepository,
        conversations,
        activeConversation,
        selectConversation,
        createNewConversation,
        deleteConversation,
        login,
        signup,
        logout,
        repoUrl,
        repoName,
        indexingState,
        indexingStep,
        indexingPercent,
        indexingLog,
        indexingSteps,
        chatMessages,
        isChatLoading,
        previousQuestions,
        graphData,
        selectedSource,
        setSelectedSource,
        isArchModalOpen,
        setIsArchModalOpen,
        toast,
        triggerToast,
        closeToast,
        indexRepository,
        sendQuery,
        clearChat,
        resetAll
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
