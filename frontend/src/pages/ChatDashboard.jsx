/**
 * Purpose:
 * Main workspace dashboard for querying the indexed repository and traversing the knowledge graph.
 *
 * Role in CodeGraphAI:
 * Renders the triple-pane developer interface (Black + Gold aesthetic). It links chat inputs,
 * rendered Markdown responses, code copy elements, referenced source files, and the interactive
 * GraphRAG relation timeline panel into a unified cockpit.
 *
 * Key Responsibilities:
 * - Render ChatGPT-style chat feed wrapping Markdown rendering and custom code blocks.
 * - Display interactive source drawers to view retrieved file snippets and scores.
 * - Render the GraphRAG Context timeline panel displaying calls and containment paths dynamically.
 * - Provide prompt shortcut configurations and quick access controls (clear chat, new repo onboarding).
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useApp } from '../context/AppContext';
import { 
  FaGitAlt, 
  FaTrashAlt, 
  FaArrowLeft, 
  FaPaperPlane, 
  FaCode, 
  FaSearch, 
  FaNetworkWired,
  FaChevronRight,
  FaChevronDown,
  FaCopy,
  FaCheck,
  FaBars
} from 'react-icons/fa';
import { IoTerminalSharp } from 'react-icons/io5';
import { VscLoading } from 'react-icons/vsc';

// Reusable Copy Button for Code Blocks
const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1.5 bg-black/85 hover:bg-black border border-white/10 hover:border-primary/50 text-text-secondary hover:text-primary rounded text-xs transition-colors flex items-center gap-1 z-10 cursor-pointer"
    >
      {copied ? <FaCheck size={10} /> : <FaCopy size={10} />}
      <span>{copied ? 'Copied' : 'Copy'}</span>
    </button>
  );
};

export const ChatDashboard = ({ onNavigate }) => {
  const {
    repoUrl,
    repoName,
    chatMessages,
    isChatLoading,
    previousQuestions,
    sendQuery,
    clearChat,
    resetAll,
    selectedSource,
    setSelectedSource,
    graphData
  } = useApp();

  const [inputVal, setInputVal] = useState('');
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatLoading]);

  // Handle textarea autosize
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputVal]);

  const handleSend = (e) => {
    e?.preventDefault();
    if (!inputVal.trim() || isChatLoading) return;
    sendQuery(inputVal.trim());
    setInputVal('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleSourceExpand = (sourceId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [sourceId]: !prev[sourceId]
    }));
  };

  // Get active graph relationships from the last assistant message
  const getLastMessageRelations = () => {
    const assistantMsgs = chatMessages.filter(m => m.sender === 'assistant');
    if (assistantMsgs.length === 0) return [];
    const lastMsg = assistantMsgs[assistantMsgs.length - 1];
    
    // Filter sources that contain GraphRAG relationship expansion metadata
    return (lastMsg.sources || []).filter(s => s.relation && s.graph_source);
  };

  const activeRelations = getLastMessageRelations();

  return (
    <div className="flex h-[90vh] overflow-hidden border-t border-white/5 relative bg-[#090909]">
      
      {/* 1. DESKTOP LEFT SIDEBAR */}
      <aside className="w-64 bg-background border-r border-white/5 flex flex-col justify-between flex-shrink-0 hidden md:flex select-none">
        {/* Top area */}
        <div className="flex flex-col flex-1 overflow-y-auto p-4 space-y-6">
          {/* Logo Title */}
          <div className="flex items-center gap-2.5">
            <span className="text-primary font-bold text-lg tracking-widest bg-primary/10 px-2.5 py-1 rounded border border-primary/20 shadow-[0_0_10px_rgba(212,175,55,0.1)]">CG</span>
            <div className="flex flex-col">
              <span className="text-sm font-extrabold tracking-wider gold-text-gradient">CodeGraphAI</span>
              <span className="text-[9px] uppercase tracking-widest text-text-secondary">workspace</span>
            </div>
          </div>

          {/* Current Repo Details */}
          <div className="bg-surface border border-white/5 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center justify-between text-[10px] font-bold text-primary uppercase tracking-wider">
              <span>Active Repository</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <FaGitAlt className="text-text-secondary flex-shrink-0" />
              <span className="text-xs text-text font-semibold truncate select-text">{repoName || 'fastapi'}</span>
            </div>
            <div className="text-[10px] text-text-secondary/60 truncate select-text">
              {repoUrl || 'https://github.com/tiangolo/fastapi'}
            </div>
            <button
              onClick={() => {
                resetAll();
                onNavigate('setup');
              }}
              className="w-full text-center py-1.5 mt-2 bg-black/40 border border-white/10 hover:border-primary/45 rounded text-[10px] text-text-secondary hover:text-primary transition-all font-bold uppercase tracking-wider cursor-pointer"
            >
              New Repository
            </button>
          </div>

          {/* Previous Questions */}
          <div className="flex-1 space-y-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-text-secondary block px-1">Previous Questions</span>
            <div className="space-y-1 max-h-[25vh] overflow-y-auto">
              {previousQuestions.length === 0 ? (
                <span className="text-[10px] text-text-secondary/40 italic px-2 block">No previous queries.</span>
              ) : (
                previousQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      if (!isChatLoading) sendQuery(q);
                    }}
                    className="w-full text-left px-2.5 py-2 hover:bg-surface border border-transparent hover:border-white/5 rounded text-xs text-text-secondary/80 hover:text-text truncate transition-all cursor-pointer block"
                  >
                    {q}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Bottom actions */}
        <div className="p-4 border-t border-white/5 bg-black/25 flex flex-col gap-2">
          <button
            onClick={clearChat}
            disabled={chatMessages.length === 0}
            className="w-full flex items-center justify-center gap-2 py-2 border border-white/5 hover:border-rose-500/25 bg-surface text-text-secondary hover:text-rose-400 rounded text-xs transition-colors disabled:opacity-40 cursor-pointer"
          >
            <FaTrashAlt size={11} />
            Clear Chat
          </button>
          
          <button
            onClick={() => onNavigate('landing')}
            className="w-full flex items-center justify-center gap-2 py-2 border border-white/5 hover:border-white/20 bg-surface text-text-secondary hover:text-text rounded text-xs transition-colors cursor-pointer"
          >
            <FaArrowLeft size={10} />
            Back to Landing
          </button>
        </div>
      </aside>

      {/* MOBILE LEFT SIDEBAR DRAWER OVERLAY */}
      <AnimatePresence>
        {isMobileSidebarOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileSidebarOpen(false)}
              className="absolute inset-0 bg-black/80 backdrop-blur-xs"
            />
            {/* Drawer */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.25 }}
              className="relative w-64 bg-background border-r border-white/5 flex flex-col justify-between h-full z-10 p-4 select-none animate-fade-in"
            >
              <div className="flex flex-col flex-1 overflow-y-auto space-y-6">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-primary font-bold text-base bg-primary/10 px-2 py-0.5 rounded border border-primary/20">CG</span>
                    <span className="text-sm font-extrabold gold-text-gradient">CodeGraphAI</span>
                  </div>
                  <button 
                    onClick={() => setIsMobileSidebarOpen(false)}
                    className="text-text-secondary hover:text-primary text-xs font-semibold p-1 cursor-pointer"
                  >
                    Close
                  </button>
                </div>
                
                {/* Active Repo Details */}
                <div className="bg-surface border border-white/5 rounded-lg p-3.5 space-y-2">
                  <span className="text-[10px] font-bold text-primary uppercase tracking-wider block">Active Repository</span>
                  <div className="flex items-center gap-2">
                    <FaGitAlt className="text-text-secondary flex-shrink-0" />
                    <span className="text-xs text-text font-semibold truncate select-text">{repoName || 'fastapi'}</span>
                  </div>
                  <button
                    onClick={() => {
                      setIsMobileSidebarOpen(false);
                      resetAll();
                      onNavigate('setup');
                    }}
                    className="w-full text-center py-1.5 mt-2 bg-black/40 border border-white/10 rounded text-[10px] text-text-secondary hover:text-primary transition-all font-bold uppercase tracking-wider cursor-pointer"
                  >
                    New Repository
                  </button>
                </div>

                {/* Previous Questions */}
                <div className="flex-1 space-y-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-text-secondary block px-1">Previous Questions</span>
                  <div className="space-y-1">
                    {previousQuestions.length === 0 ? (
                      <span className="text-[10px] text-text-secondary/40 italic block px-1">No previous queries.</span>
                    ) : (
                      previousQuestions.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setIsMobileSidebarOpen(false);
                            if (!isChatLoading) sendQuery(q);
                          }}
                          className="w-full text-left px-2.5 py-2 hover:bg-surface border border-transparent hover:border-white/5 rounded text-xs text-text-secondary/85 hover:text-text truncate transition-all cursor-pointer block"
                        >
                          {q}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="pt-4 border-t border-white/5 bg-black/25 flex flex-col gap-2">
                <button
                  onClick={() => {
                    clearChat();
                    setIsMobileSidebarOpen(false);
                  }}
                  disabled={chatMessages.length === 0}
                  className="w-full flex items-center justify-center gap-2 py-2 border border-white/5 bg-surface text-text-secondary hover:text-rose-400 rounded text-xs transition-colors disabled:opacity-40 cursor-pointer"
                >
                  <FaTrashAlt size={11} />
                  Clear Chat
                </button>
              </div>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      {/* 2. MAIN WORKSPACE / CHAT PANEL */}
      <div className="flex-1 flex flex-col justify-between overflow-hidden relative">
        {/* Mobile Toolbar */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-white/5 bg-black/40 select-none">
          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="flex items-center gap-2 text-xs text-primary font-bold uppercase border border-primary/20 bg-primary/10 px-3 py-1.5 rounded cursor-pointer"
          >
            <FaBars size={12} />
            <span>Workspace</span>
          </button>
          <span className="text-xs font-mono text-text truncate max-w-[150px]">{repoName || 'fastapi'}</span>
          <button
            onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
            className="text-xs text-text-secondary hover:text-primary border border-white/10 hover:border-primary/30 px-3 py-1.5 rounded bg-surface cursor-pointer"
          >
            GraphRAG
          </button>
        </div>

        {/* Chat Feed */}
        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 space-y-6">
          {chatMessages.length === 0 ? (
            /* Empty State: Ask anything about your repository. */
            <div className="h-full flex flex-col justify-center items-center text-center max-w-xl mx-auto space-y-6 animate-fade-in">
              <div className="w-16 h-16 rounded-full bg-primary/5 border border-primary/20 flex items-center justify-center text-primary gold-border-pulse">
                <IoTerminalSharp size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-text mb-1.5 select-text">Ask anything about your repository.</h3>
                <p className="text-xs text-text-secondary leading-relaxed max-w-sm select-text">
                  Enter questions about call stacks, class layouts, functions, dependencies, or architectural flows. CodeGraphAI utilizes AST-Graph retrieval.
                </p>
              </div>

              {/* Sample queries */}
              <div className="grid grid-cols-1 gap-2.5 w-full max-w-md">
                {[
                  `How does the APIRouter get initialized?`,
                  `Show me the call flow of adding a route in FastAPI.`,
                  `What are the class properties of APIRoute?`
                ].map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputVal(sample);
                      textareaRef.current?.focus();
                    }}
                    className="text-left px-4 py-2.5 bg-surface border border-white/5 hover:border-primary/20 text-xs text-text-secondary hover:text-text rounded-lg transition-colors flex justify-between items-center cursor-pointer"
                  >
                    <span>{sample}</span>
                    <FaChevronRight size={10} className="text-primary/45" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto select-text">
              {chatMessages.map((msg) => (
                <div key={msg.id} className="flex flex-col gap-2 animate-fade-in">
                  {/* Sender Header */}
                  <div className="flex items-center gap-2.5 select-none">
                    <div className={`w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold ${msg.sender === 'user' ? 'bg-white/10 border border-white/20 text-text' : 'bg-primary/10 border border-primary/20 text-primary shadow-[0_0_8px_rgba(212,175,55,0.15)]'}`}>
                      {msg.sender === 'user' ? 'U' : 'AI'}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-text-secondary">
                      {msg.sender === 'user' ? 'You' : 'CodeGraphAI'}
                    </span>
                    <span className="text-[8px] text-text-secondary/40">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  {/* Message Bubble */}
                  <div className={`px-4 py-3 rounded-lg border text-sm leading-relaxed ${msg.sender === 'user' ? 'bg-white/3 border-white/5' : 'bg-surface border-white/5 shadow-md'}`}>
                    {/* Render Intent & Strategy Metadata */}
                    {msg.sender === 'assistant' && msg.intent && (
                      <div className="flex flex-wrap items-center gap-2 mb-3 bg-black/30 border border-white/5 px-3 py-1.5 rounded-md text-xs select-none">
                        <span className="text-[10px] uppercase font-bold text-text-secondary">Intent:</span>
                        <span className="px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary rounded text-[9px] font-extrabold uppercase tracking-wider">
                          {msg.intent.replace('_', ' ')}
                        </span>
                        
                        {msg.retrieval_strategy && msg.retrieval_strategy.length > 0 && (
                          <>
                            <span className="text-[10px] uppercase font-bold text-text-secondary ml-2">Retrieval:</span>
                            <div className="flex flex-wrap gap-1">
                              {msg.retrieval_strategy.map((strat, sIdx) => (
                                <span key={sIdx} className="px-1.5 py-0.5 bg-white/5 border border-white/10 rounded text-[9px] font-semibold text-text-secondary">
                                  ✓ {strat}
                                </span>
                              ))}
                            </div>
                          </>
                        )}
                        
                        {msg.confidence && (
                          <span className="ml-auto text-[9px] font-bold text-emerald-400">
                            Confidence: {typeof msg.confidence === 'number' ? (msg.confidence * 100).toFixed(0) : msg.confidence}%
                          </span>
                        )}
                      </div>
                    )}

                    <ReactMarkdown 
                      components={{
                        pre: ({ node, ...props }) => (
                          <div className="relative group my-3">
                            <pre className="p-4 rounded-lg overflow-x-auto text-xs" {...props} />
                          </div>
                        ),
                        code: ({ node, inline, ...props }) => {
                          const codeText = props.children ? String(props.children).replace(/\n$/, '') : '';
                          if (!inline && codeText) {
                            return (
                              <div className="relative group my-3">
                                <CopyButton text={codeText} />
                                <code className="block p-4 rounded bg-[#0A0A0A] overflow-x-auto border border-white/5 text-xs text-emerald-400 font-mono" {...props} />
                              </div>
                            );
                          }
                          return <code className="px-1.5 py-0.5 rounded bg-black/40 text-primary border border-white/5 text-xs font-mono" {...props} />;
                        }
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>

                    {/* Render message-specific sources */}
                    {msg.sender === 'assistant' && (
                      <div className="mt-5 pt-4 border-t border-white/5 space-y-3 select-none">
                        <span className="text-[10px] uppercase font-extrabold tracking-wider text-primary block">Retrieved Sources</span>
                        
                        {!msg.sources || msg.sources.length === 0 ? (
                          <p className="text-xs text-text-secondary/40 italic select-text">No supporting sources found.</p>
                        ) : (
                          <div className="grid grid-cols-1 gap-2.5">
                            {msg.sources.map((source, sIdx) => {
                              const sourceId = `${msg.id}-src-${sIdx}`;
                              const isExpanded = expandedSources[sourceId];
                              
                              return (
                                <div 
                                  key={sIdx} 
                                  className="bg-[#0B0B0B] border border-white/5 hover:border-primary/25 rounded-lg overflow-hidden transition-all duration-300"
                                >
                                  {/* Source Card Header */}
                                  <div 
                                    onClick={() => toggleSourceExpand(sourceId)}
                                    className="flex items-center justify-between px-3.5 py-2.5 cursor-pointer hover:bg-white/1"
                                  >
                                    <div className="flex flex-col gap-0.5 truncate pr-4">
                                      <span className="text-[11px] font-bold text-text truncate select-text">{source.file_path.split('\\').pop().split('/').pop()}</span>
                                      <span className="text-[9px] text-text-secondary truncate select-text">{source.file_path}</span>
                                    </div>
                                    
                                    <div className="flex items-center gap-3 flex-shrink-0">
                                      {source.symbol_name && (
                                        <span className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[9px] font-mono text-primary truncate max-w-[120px] select-text">
                                          {source.symbol_name}
                                        </span>
                                      )}
                                      {source.chunk_type && (
                                        <span className="text-[8px] uppercase tracking-wider font-bold text-text-secondary px-1.5 py-0.5 bg-surface border border-white/5 rounded">
                                          {source.chunk_type}
                                        </span>
                                      )}
                                      <span className="text-[9px] font-bold text-emerald-400">
                                        Score: {typeof source.score === 'number' ? source.score.toFixed(2) : source.score}
                                      </span>
                                      {isExpanded ? <FaChevronDown size={10} className="text-text-secondary" /> : <FaChevronRight size={10} className="text-text-secondary" />}
                                    </div>
                                  </div>

                                  {/* Source Card Expanded Code */}
                                  <AnimatePresence>
                                    {isExpanded && (
                                      <motion.div
                                        initial={{ height: 0 }}
                                        animate={{ height: 'auto' }}
                                        exit={{ height: 0 }}
                                        className="overflow-hidden border-t border-white/5 bg-black/60 relative"
                                      >
                                        <CopyButton text={source.text} />
                                        <pre className="p-4 text-xs text-emerald-400 overflow-x-auto max-h-[300px] select-text font-mono leading-normal bg-black">
                                          <code>{source.text}</code>
                                        </pre>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Typing Indicator & Premium Skeleton Loader */}
          {isChatLoading && (
            <div className="space-y-4 max-w-3xl mx-auto select-none mt-4">
              {/* Typing Indicator */}
              <div className="flex items-center gap-3 px-4 py-2 bg-surface border border-white/5 rounded-lg max-w-xs mx-auto animate-pulse">
                <VscLoading className="animate-spin text-primary text-base flex-shrink-0" />
                <span className="text-xs text-text-secondary font-medium">Analyzing database and files...</span>
              </div>
              
              {/* Skeleton response box */}
              <div className="flex flex-col gap-2 animate-pulse">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-white/5 border border-white/10" />
                  <div className="h-3 w-24 bg-white/10 rounded" />
                </div>
                <div className="p-4 bg-surface border border-white/5 rounded-lg space-y-3">
                  <div className="h-3.5 bg-white/10 rounded w-3/4" />
                  <div className="h-3.5 bg-white/10 rounded w-5/6" />
                  <div className="h-3.5 bg-white/10 rounded w-2/3" />
                  
                  {/* Sources Skeletons */}
                  <div className="pt-4 border-t border-white/5 space-y-2 mt-4">
                    <div className="h-3 bg-white/10 rounded w-28" />
                    <div className="grid grid-cols-1 gap-2">
                      <div className="h-10 bg-black/40 border border-white/5 rounded-lg" />
                      <div className="h-10 bg-black/40 border border-white/5 rounded-lg" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-white/5 bg-black/25 select-none">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto relative flex gap-2">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the repository structures, symbol usages, or functions..."
              disabled={isChatLoading}
              className="w-full py-3 pl-4 pr-12 bg-surface border border-white/10 focus:border-primary/50 text-sm text-text rounded-xl focus:outline-none resize-none overflow-y-auto leading-relaxed select-text placeholder:text-text-secondary/55"
            />
            <button
              type="submit"
              disabled={!inputVal.trim() || isChatLoading}
              className="absolute right-3.5 top-[11px] p-2 bg-primary text-black rounded-lg hover:bg-primary-hover hover:scale-[1.03] transition-all disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center cursor-pointer"
            >
              <FaPaperPlane size={11} />
            </button>
          </form>
          <div className="text-[10px] text-text-secondary/35 text-center mt-2">
            Press Enter to Send • Shift+Enter for New Line • Dynamic AST retrieval active
          </div>
        </div>
      </div>

      {/* Mobile GraphRAG backdrop overlay */}
      {isRightPanelOpen && (
        <div 
          onClick={() => setIsRightPanelOpen(false)} 
          className="lg:hidden fixed inset-0 bg-black/70 z-30 backdrop-blur-xs transition-opacity"
        />
      )}

      {/* 3. RIGHT COLLAPSIBLE PANEL (GraphRAG Context) */}
      <AnimatePresence>
        {isRightPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 220, damping: 24 }}
            className="h-full bg-background border-l border-white/5 flex flex-col flex-shrink-0 overflow-hidden lg:relative fixed inset-y-0 right-0 z-40 shadow-2xl lg:shadow-none bg-[#090909]"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/5 flex justify-between items-center bg-black/35 select-none">
              <div className="flex items-center gap-2">
                <FaNetworkWired size={13} className="text-primary" />
                <span className="text-[10px] uppercase font-extrabold tracking-widest text-primary">GraphRAG Relations</span>
              </div>
              <span className="text-[9px] bg-primary/10 border border-primary/20 text-primary font-bold px-1.5 py-0.5 rounded select-text">
                {activeRelations.length} active
              </span>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {activeRelations.length === 0 ? (
                /* Empty state: No GraphRAG relationships available. */
                <div className="h-full flex flex-col justify-center items-center text-center p-6 space-y-3 select-none">
                  <FaNetworkWired size={24} className="text-text-secondary/20 animate-pulse" />
                  <div>
                    <span className="text-[10px] uppercase font-bold text-text-secondary/70 block">No GraphRAG relationships available.</span>
                    <p className="text-[9px] text-text-secondary/40 leading-normal mt-1">
                      Reasoning links appear when queries touch referenced classes or methods.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <span className="text-[9px] font-bold text-text-secondary uppercase tracking-wider block">Graph Expansion Flow</span>
                  
                  {/* Timeline Flow */}
                  <div className="relative pl-4 border-l-2 border-primary/15 ml-2.5 space-y-6 select-text">
                    {activeRelations.map((rel, rIdx) => (
                      <div key={rIdx} className="relative flex flex-col items-start gap-1">
                        {/* Dot indicator */}
                        <div className="absolute -left-[22px] top-1.5 w-3 h-3 rounded-full bg-surface border-2 border-primary flex items-center justify-center shadow-[0_0_6px_rgba(212,175,55,0.4)]" />
                        
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-xs font-bold text-text font-mono truncate max-w-[180px]" title={rel.graph_source}>
                            {rel.graph_source}
                          </span>
                          <span className="px-1.5 py-0.5 bg-primary/10 border border-primary/20 text-primary rounded text-[8px] font-bold uppercase tracking-wider">
                            {rel.relation}
                          </span>
                        </div>
                        
                        <div className="text-[11px] font-bold text-emerald-400 font-mono pl-1" title={rel.symbol_name}>
                          ➔ {rel.symbol_name}
                        </div>

                        <div className="text-[9px] text-text-secondary/60 font-mono truncate max-w-[210px] pl-1">
                          in {rel.file_path.split('\\').pop().split('/').pop()}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Nodes & Edges Count Metadata info */}
                  <div className="pt-4 border-t border-white/5 bg-surface/20 rounded p-3 text-[10px] text-text-secondary/80 space-y-1 select-text">
                    <span className="text-[9px] uppercase font-bold text-primary block mb-1">Knowledge Graph Stats</span>
                    <div className="flex justify-between">
                      <span>Total graph nodes:</span>
                      <span className="font-semibold text-text">{graphData.nodes?.length || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total graph edges:</span>
                      <span className="font-semibold text-text">{graphData.edges?.length || 0}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Trigger button to open/close right panel */}
      <button
        onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
        className="absolute top-1/2 -translate-y-1/2 right-0 z-30 p-2 bg-surface hover:bg-black border-y border-l border-white/10 hover:border-primary/50 text-text hover:text-primary rounded-l-md transition-colors cursor-pointer select-none"
      >
        <FaChevronRight className={`transition-transform duration-300 ${isRightPanelOpen ? 'rotate-0' : 'rotate-180'}`} size={11} />
      </button>

    </div>
  );
};
export default ChatDashboard;
