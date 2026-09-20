import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import LandingPage from './pages/LandingPage';
import RepoSetupPage from './pages/RepoSetupPage';
import ChatDashboard from './pages/ChatDashboard';
import GraphViewDashboard from './pages/GraphViewDashboard';
import ArchitectureModal from './components/ArchitectureModal';
import AuthModal from './components/AuthModal';
import Toast from './components/Toast';
import { FaUser, FaSignOutAlt, FaCrown, FaDatabase } from 'react-icons/fa';

function AppContent() {
  const [currentPage, setCurrentPage] = useState('landing');
  const { 
    isArchModalOpen, 
    setIsArchModalOpen, 
    isAuthModalOpen,
    setIsAuthModalOpen,
    currentUser,
    login,
    signup,
    logout,
    toast, 
    closeToast,
    repoName,
    indexingState
  } = useApp();

  return (
    <div className="min-h-screen bg-background text-text flex flex-col justify-between">
      {/* Premium Header Bar */}
      <header className="px-6 py-3.5 bg-black/60 border-b border-white/5 backdrop-blur-md flex justify-between items-center select-none sticky top-0 z-40">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setCurrentPage('landing')}>
          <span className="text-primary font-bold text-base bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded shadow-[0_0_8px_rgba(212,175,55,0.1)]">CG</span>
          <span className="text-sm font-extrabold tracking-wider text-text hover:text-primary transition-colors">CodeGraphAI</span>
        </div>
        
        <nav className="flex items-center gap-5 text-xs font-bold uppercase tracking-wider text-text-secondary">
          <button 
            onClick={() => setCurrentPage('landing')} 
            className={`hover:text-primary transition-colors cursor-pointer ${currentPage === 'landing' ? 'text-primary font-bold' : ''}`}
          >
            Home
          </button>
          
          <button 
            onClick={() => setCurrentPage('setup')} 
            className={`hover:text-primary transition-colors cursor-pointer ${currentPage === 'setup' ? 'text-primary font-bold' : ''}`}
          >
            Index Repo
          </button>
          
          <button 
            onClick={() => {
              if (indexingState === 'success') {
                setCurrentPage('chat');
              } else {
                setCurrentPage('setup');
              }
            }} 
            className={`hover:text-primary transition-colors cursor-pointer ${currentPage === 'chat' ? 'text-primary font-bold' : ''}`}
          >
            Workspace {repoName && `(${repoName})`}
          </button>

          <button 
            onClick={() => {
              if (indexingState === 'success') {
                setCurrentPage('graph');
              } else {
                setCurrentPage('setup');
              }
            }} 
            className={`hover:text-primary transition-colors cursor-pointer ${currentPage === 'graph' ? 'text-primary font-bold' : ''}`}
          >
            Graph View
          </button>
          
          <button 
            onClick={() => setIsArchModalOpen(true)}
            className="text-text-secondary hover:text-primary transition-all border border-white/10 hover:border-primary/50 px-3 py-1 rounded-md bg-white/5 cursor-pointer"
          >
            Architecture
          </button>

          {/* User Auth Section */}
          <div className="pl-2 border-l border-white/10 flex items-center gap-3">
            {currentUser ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 px-2.5 py-1 rounded-md text-[11px] normal-case text-text">
                  <FaUser className="text-primary" size={10} />
                  <span className="max-w-[120px] truncate">{currentUser.email}</span>
                  <span className="ml-1 uppercase text-[9px] font-extrabold px-1.5 py-0.2 rounded bg-primary/20 text-primary border border-primary/30">
                    {currentUser.tier || 'free'}
                  </span>
                </div>
                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-1.5 text-text-secondary hover:text-red-400 hover:bg-white/5 rounded transition-colors cursor-pointer"
                >
                  <FaSignOutAlt size={12} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="bg-primary/10 hover:bg-primary text-primary hover:text-black border border-primary/30 hover:border-primary px-3 py-1 rounded-md font-bold transition-all shadow-[0_0_10px_rgba(212,175,55,0.1)] cursor-pointer"
              >
                Sign In
              </button>
            )}
          </div>
        </nav>
      </header>

      {/* Main Screen Layout */}
      <main className="flex-1">
        {currentPage === 'landing' && <LandingPage onNavigate={setCurrentPage} />}
        {currentPage === 'setup' && <RepoSetupPage onNavigate={setCurrentPage} />}
        {currentPage === 'chat' && <ChatDashboard onNavigate={setCurrentPage} />}
        {currentPage === 'graph' && <GraphViewDashboard onNavigate={setCurrentPage} />}
      </main>

      {/* Footer Branding */}
      <footer className="py-4 border-t border-white/5 bg-black/40 text-center text-[10px] text-text-secondary/30 select-none">
        &copy; {new Date().getFullYear()} CodeGraphAI. Designed with HSL Gold & Multi-Tenant Partitioning. All Rights Reserved.
      </footer>

      {/* Shared Overlay Elements */}
      <ArchitectureModal isOpen={isArchModalOpen} onClose={() => setIsArchModalOpen(false)} />
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onLogin={login}
        onSignup={signup}
      />
      <Toast message={toast.message} type={toast.type} onClose={closeToast} />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
