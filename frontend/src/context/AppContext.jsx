import React, { createContext, useContext, useState, useEffect } from 'react';
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
  // Repository Setup State
  const [repoUrl, setRepoUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  const [indexingState, setIndexingState] = useState('idle'); // idle | indexing | success | error
  const [indexingStep, setIndexingStep] = useState(0); // 0 to 5
  const [indexingLog, setIndexingLog] = useState('');
  
  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [previousQuestions, setPreviousQuestions] = useState([]);

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

  // Stepper descriptions for indexing
  const indexingSteps = [
    { label: 'GitHub URL Validation', desc: 'Analyzing URL and verifying Python constraints...' },
    { label: 'Repository Ingestion', desc: 'Cloning Python source code files from GitHub...' },
    { label: 'AST-Aware Parsing', desc: 'Traversing AST structures and extracting classes & methods...' },
    { label: 'Vector Generation', desc: 'Computing local embeddings for parsed chunks...' },
    { label: 'Qdrant Store Upload', desc: 'Upserting vectors into vector database...' },
    { label: 'GraphRAG Construction', desc: 'Mapping function calls, containment & relationships...' }
  ];

  // Load state from local storage on mount (optional mock history)
  useEffect(() => {
    const savedQuestions = localStorage.getItem('codegen_questions');
    if (savedQuestions) {
      setPreviousQuestions(JSON.parse(savedQuestions));
    }
  }, []);

  // Indexing Handler
  const indexRepository = async (url) => {
    setRepoUrl(url);
    setIndexingState('indexing');
    setIndexingStep(0);
    setIndexingLog('Validating GitHub URL...');
    setSelectedSource(null);
    setChatMessages([]);

    try {
      // Step 1: Validation
      await new Promise((resolve) => setTimeout(resolve, 800));
      setIndexingStep(1);
      setIndexingLog('Cloning repository files into backend filesystem...');

      // Step 2: Ingestion / Clone
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIndexingStep(2);
      setIndexingLog('Parsing files using Tree-sitter and mapping symbol signatures...');

      // Step 3: AST Parsing
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIndexingStep(3);
      setIndexingLog('Generating vector embeddings using HuggingFace BAAI/bge-small-en-v1.5 model...');

      // Step 4: Vector Generation
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIndexingStep(4);
      setIndexingLog('Configuring Qdrant vector database store...');

      // Trigger backend index request
      const res = await apiService.indexRepository(url);
      
      setIndexingStep(5);
      setIndexingLog('Constructing repository knowledge graph & call relationships...');
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setRepoName(res.repository || res.repo_name || 'repository');
      setIndexingState('success');
      setIndexingLog('Repository successfully indexed and ready for chat reasoning.');
      triggerToast('Repository indexed successfully.', 'success');

      // Load full graph representation from backend
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
      if (error.response?.data) {
        const data = error.response.data;
        if (data.error && data.details) {
          errMsg = `${data.error}: ${data.details}`;
        } else if (data.error) {
          errMsg = data.error;
        } else if (data.details) {
          errMsg = data.details;
        } else if (data.detail) {
          errMsg = data.detail;
        }
      } else if (error.message) {
        errMsg = error.message;
      }
      setIndexingState('error');
      setIndexingLog(errMsg);
      triggerToast(errMsg, 'error');
    }
  };

  // Chat Query Handler
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

    // Save questions history
    if (!previousQuestions.includes(questionText)) {
      const updatedQs = [questionText, ...previousQuestions].slice(0, 15);
      setPreviousQuestions(updatedQs);
      localStorage.setItem('codegen_questions', JSON.stringify(updatedQs));
    }

    try {
      const chatRes = await apiService.chat(questionText);
      
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: chatRes.answer,
        sources: chatRes.sources || [],
        timestamp: new Date()
      };

      setChatMessages((prev) => [...prev, assistantMsg]);
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
    setIndexingState('idle');
    setIndexingStep(0);
    setIndexingLog('');
    setChatMessages([]);
    setGraphData({ nodes: [], edges: [] });
    setSelectedSource(null);
    triggerToast('Context reset.', 'info');
  };

  return (
    <AppContext.Provider
      value={{
        repoUrl,
        repoName,
        indexingState,
        indexingStep,
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
