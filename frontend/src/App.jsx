import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import LandingPage from './pages/LandingPage';
import RepoSetupPage from './pages/RepoSetupPage';
import ChatDashboard from './pages/ChatDashboard';
import ArchitectureModal from './components/ArchitectureModal';
import Toast from './components/Toast';

function AppContent() {
  const [currentPage, setCurrentPage] = useState('landing');
  const { 
    isArchModalOpen, 
    setIsArchModalOpen, 
    toast, 
    closeToast,
    repoName,
    indexingState
  } = useApp();

  return (
    <div className="min-h-screen bg-background text-text flex flex-col justify-between">
      {/* Premium Header Bar */}
      <header className="px-6 py-4 bg-black/60 border-b border-white/5 backdrop-blur-md flex justify-between items-center select-none sticky top-0 z-40">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentPage('landing')}>
          <span className="text-primary font-bold text-base bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded shadow-[0_0_8px_rgba(212,175,55,0.1)]">CG</span>
          <span className="text-sm font-extrabold tracking-wider text-text hover:text-primary transition-colors">CodeGraphAI</span>
        </div>
        
        <nav className="flex items-center gap-5 text-xs font-bold uppercase tracking-wider text-text-secondary">
          <button 
            onClick={() => setCurrentPage('landing')} 
            className={`hover:text-primary transition-colors ${currentPage === 'landing' ? 'text-primary font-bold' : ''}`}
          >
            Home
          </button>
          
          <button 
            onClick={() => setCurrentPage('setup')} 
            className={`hover:text-primary transition-colors ${currentPage === 'setup' ? 'text-primary font-bold' : ''}`}
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
            className={`hover:text-primary transition-colors ${currentPage === 'chat' ? 'text-primary font-bold' : ''}`}
          >
            Workspace {repoName && `(${repoName})`}
          </button>
          
          <button 
            onClick={() => setIsArchModalOpen(true)}
            className="text-text-secondary hover:text-primary transition-all border border-white/10 hover:border-primary/50 px-3 py-1 rounded-md bg-white/5"
          >
            Architecture
          </button>
        </nav>
      </header>

      {/* Main Screen Layout */}
      <main className="flex-1">
        {currentPage === 'landing' && <LandingPage onNavigate={setCurrentPage} />}
        {currentPage === 'setup' && <RepoSetupPage onNavigate={setCurrentPage} />}
        {currentPage === 'chat' && <ChatDashboard onNavigate={setCurrentPage} />}
      </main>

      {/* Footer Branding */}
      <footer className="py-4 border-t border-white/5 bg-black/40 text-center text-[10px] text-text-secondary/30 select-none">
        &copy; {new Date().getFullYear()} CodeGraphAI. Designed with HSL Gold styling. All Rights Reserved.
      </footer>

      {/* Shared Overlay Elements */}
      <ArchitectureModal isOpen={isArchModalOpen} onClose={() => setIsArchModalOpen(false)} />
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
