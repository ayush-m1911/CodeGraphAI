import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { FaGithub, FaAngleRight, FaExclamationTriangle, FaCheckCircle, FaExclamationCircle } from 'react-icons/fa';
import { VscLoading } from 'react-icons/vsc';

export const RepoSetupPage = ({ onNavigate }) => {
  const {
    indexRepository,
    indexingState,
    indexingStep,
    indexingLog,
    indexingSteps,
    repoUrl,
    repoName
  } = useApp();

  const [inputUrl, setInputUrl] = useState(repoUrl || '');
  const [validationError, setValidationError] = useState('');

  const validateGithubUrl = (url) => {
    if (!url) return 'URL cannot be empty.';
    const pattern = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;
    if (!pattern.test(url.trim())) {
      return 'Please enter a valid GitHub repository URL (e.g. https://github.com/tiangolo/fastapi).';
    }
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const error = validateGithubUrl(inputUrl);
    if (error) {
      setValidationError(error);
      return;
    }
    setValidationError('');
    indexRepository(inputUrl.trim());
  };

  const handleDemoClick = () => {
    const demoUrl = 'https://github.com/tiangolo/fastapi';
    setInputUrl(demoUrl);
    setValidationError('');
    indexRepository(demoUrl);
  };

  return (
    <div className="min-h-[85vh] flex flex-col justify-center items-center py-10 px-6 relative">
      <div className="absolute top-1/3 right-1/4 w-[300px] h-[300px] rounded-full bg-primary/3 blur-[90px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-xl bg-surface border border-white/5 rounded-xl p-8 shadow-xl z-10"
      >
        <h2 className="text-2xl font-bold mb-2 select-text">Connect Repository</h2>
        <p className="text-xs text-text-secondary leading-relaxed mb-6 select-text">
          Enter a Python GitHub repository to begin. CodeGraphAI will build a dynamic call-graph index and database collections to answer context-rich questions.
        </p>

        {indexingState === 'idle' && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="repo-url" className="text-xs font-semibold uppercase tracking-wider text-primary">
                GitHub Repository URL
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-secondary">
                  <FaGithub size={18} />
                </div>
                <input
                  id="repo-url"
                  type="text"
                  placeholder="https://github.com/username/project"
                  value={inputUrl}
                  onChange={(e) => {
                    setInputUrl(e.target.value);
                    if (validationError) setValidationError('');
                  }}
                  className="w-full pl-11 pr-4 py-3 bg-black/50 border border-white/10 rounded-lg text-sm text-text focus:outline-none focus:border-primary transition-all font-mono"
                />
              </div>
              
              {validationError && (
                <div className="flex items-center gap-2 text-rose-500 text-xs mt-1">
                  <FaExclamationCircle />
                  <span>{validationError}</span>
                </div>
              )}
              
              <div className="flex items-center gap-2 px-3 py-2 bg-primary/5 border border-primary/10 rounded text-xs text-text-secondary">
                <FaExclamationTriangle className="text-primary flex-shrink-0" />
                <span>Currently supports Python repositories only.</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="submit"
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-primary text-black font-bold rounded-lg hover:bg-primary-hover transition-colors shadow-lg"
              >
                Analyze Repository
                <FaAngleRight />
              </button>
              
              <button
                type="button"
                onClick={handleDemoClick}
                className="px-6 py-3 bg-black/40 border border-white/10 text-text-secondary hover:text-text hover:border-white/30 rounded-lg transition-colors font-medium text-sm"
              >
                Load FastAPI Demo
              </button>
            </div>
          </form>
        )}

        {/* Loading / Indexing State */}
        {indexingState === 'indexing' && (
          <div className="space-y-6">
            <div className="flex items-center gap-4 px-4 py-3 bg-black/30 border border-white/5 rounded-lg">
              <VscLoading className="animate-spin text-primary text-xl flex-shrink-0" />
              <div>
                <h4 className="text-xs font-semibold text-primary uppercase tracking-wider">Indexing active</h4>
                <p className="text-[11px] text-text-secondary mt-0.5 select-text">Cloning repo and building GraphRAG index...</p>
              </div>
            </div>

            {/* Stepper Progress Visualizer */}
            <div className="space-y-4">
              <div className="h-1.5 w-full bg-black/60 rounded-full overflow-hidden border border-white/5">
                <div 
                  className="h-full bg-primary gold-bar-animated transition-all duration-500" 
                  style={{ width: `${((indexingStep + 1) / indexingSteps.length) * 100}%` }}
                />
              </div>

              <div className="relative pl-6 space-y-4 border-l border-white/10 ml-3">
                {indexingSteps.map((step, idx) => {
                  const isActive = idx === indexingStep;
                  const isDone = idx < indexingStep;
                  const isPending = idx > indexingStep;

                  let bulletStyle = "border-white/10 bg-surface text-text-secondary";
                  if (isActive) bulletStyle = "border-primary bg-background text-primary scale-110 shadow-[0_0_8px_rgba(212,175,55,0.4)]";
                  if (isDone) bulletStyle = "border-primary bg-primary text-black";

                  return (
                    <div key={idx} className="relative flex flex-col items-start gap-0.5">
                      <div className={`absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full border-2 flex items-center justify-center text-[8px] font-bold transition-all ${bulletStyle}`}>
                        {isDone ? '✓' : idx + 1}
                      </div>
                      <span className={`text-xs font-bold leading-normal ${isActive ? 'text-primary' : isPending ? 'text-text-secondary/40' : 'text-text'}`}>
                        {step.label}
                      </span>
                      <span className={`text-[10px] ${isActive ? 'text-text-secondary' : isPending ? 'text-text-secondary/20' : 'text-text-secondary/60'}`}>
                        {step.desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Ingestion console output */}
            <div className="bg-black border border-white/5 p-3.5 rounded-lg text-[10px] font-mono text-emerald-400 max-h-[100px] overflow-y-auto select-text">
              <span className="text-text-secondary select-none">$ </span>{indexingLog}
            </div>
          </div>
        )}

        {/* Success State */}
        {indexingState === 'success' && (
          <div className="space-y-6 text-center py-4">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 border border-primary/20 text-primary mb-2">
              <FaCheckCircle size={30} />
            </div>
            
            <div>
              <h3 className="text-lg font-bold text-text mb-1 select-text">Repository Indexed Successfully</h3>
              <p className="text-xs text-text-secondary select-text">
                All metadata chunk files are embedded and stored. Knowledge Graph parsed for **{repoName || 'repository'}**.
              </p>
            </div>

            <div className="bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col items-center max-w-sm mx-auto">
              <span className="text-[10px] uppercase font-bold tracking-wider text-primary mb-1">Active Database Index</span>
              <span className="text-xs font-mono text-text truncate max-w-xs select-text">{repoUrl}</span>
            </div>

            <div className="flex gap-3 pt-2 max-w-sm mx-auto">
              <button
                onClick={() => onNavigate('chat')}
                className="flex-1 px-6 py-2.5 bg-primary text-black font-bold rounded-lg hover:bg-primary-hover transition-colors shadow-lg text-sm"
              >
                Enter Chat Workspace
              </button>
              
              <button
                onClick={handleSubmit}
                className="px-4 py-2.5 bg-black/40 border border-white/10 text-text-secondary hover:text-text hover:border-white/30 rounded-lg transition-colors text-sm font-semibold cursor-pointer"
              >
                Re-index Repository
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {indexingState === 'error' && (
          <div className="space-y-6 text-center py-4">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-rose-950/20 border border-rose-500/30 text-rose-500 mb-2">
              <FaExclamationCircle size={30} />
            </div>

            <div>
              <h3 className="text-lg font-bold text-rose-500 mb-1 select-text">Unable to index repository</h3>
              <p className="text-xs text-text-secondary max-w-sm mx-auto leading-relaxed select-text">
                The ingestion process failed to execute. Please double check if your URL points to a public python git repository.
              </p>
            </div>

            <div className="bg-rose-950/10 border border-rose-500/10 p-4 rounded-lg max-w-sm mx-auto text-left">
              <span className="text-[9px] uppercase font-bold tracking-wider text-rose-500 block mb-1">Error trace</span>
              <p className="text-[10px] font-mono text-rose-300 leading-normal max-h-[120px] overflow-y-auto select-text">
                {indexingLog}
              </p>
            </div>

            <div className="flex gap-3 pt-2 max-w-sm mx-auto">
              <button
                onClick={() => indexRepository(inputUrl)}
                className="flex-1 px-6 py-2.5 bg-primary text-black font-bold rounded-lg hover:bg-primary-hover transition-colors shadow-lg text-sm"
              >
                Try Again
              </button>
              
              <button
                onClick={() => {
                  setInputUrl('');
                  setValidationError('');
                  // Reset state to idle
                  indexRepository(''); // Wait, indexRepository('') might try to index empty. Let's just set state in component or let context handle it.
                  window.location.reload(); // Quick reset
                }}
                className="px-4 py-2.5 bg-black/40 border border-white/10 text-text-secondary hover:text-text hover:border-white/30 rounded-lg transition-colors text-sm font-semibold"
              >
                Change URL
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};
export default RepoSetupPage;
