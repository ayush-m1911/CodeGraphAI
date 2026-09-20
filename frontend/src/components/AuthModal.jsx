import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaTimes, FaLock, FaEnvelope, FaCrown, FaCheck } from 'react-icons/fa';
import { VscLoading } from 'react-icons/vsc';

export const AuthModal = ({ isOpen, onClose, onLogin, onSignup }) => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tier, setTier] = useState('free');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    if (!email || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }
    setLoading(true);
    try {
      if (isLoginMode) {
        await onLogin({ email, password });
      } else {
        await onSignup({ email, password, tier });
      }
      onClose();
    } catch (err) {
      setErrorMsg(err.detail || err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="w-full max-w-md bg-[#0F0F12] border border-primary/30 rounded-xl shadow-[0_0_30px_rgba(212,175,55,0.15)] overflow-hidden"
        >
          {/* Modal Header */}
          <div className="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-black/40">
            <div className="flex items-center gap-2">
              <span className="text-primary font-bold text-sm bg-primary/10 border border-primary/20 px-2 py-0.5 rounded">CG</span>
              <h2 className="text-sm font-bold tracking-wider text-text uppercase">
                {isLoginMode ? 'Sign In to CodeGraphAI' : 'Create Account'}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-primary transition-colors p-1 rounded hover:bg-white/5 cursor-pointer"
            >
              <FaTimes size={14} />
            </button>
          </div>

          {/* Form Content */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {errorMsg && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded-lg">
                {errorMsg}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <div className="relative">
                <FaEnvelope className="absolute left-3 top-3 text-text-secondary/50" size={12} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="developer@example.com"
                  className="w-full pl-9 pr-3 py-2 bg-black/60 border border-white/10 rounded-lg text-xs text-text placeholder-text-secondary/40 focus:outline-none focus:border-primary transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <FaLock className="absolute left-3 top-3 text-text-secondary/50" size={12} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 bg-black/60 border border-white/10 rounded-lg text-xs text-text placeholder-text-secondary/40 focus:outline-none focus:border-primary transition-colors"
                  required
                />
              </div>
            </div>

            {!isLoginMode && (
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                  Subscription Tier
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['free', 'pro', 'enterprise'].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTier(t)}
                      className={`py-2 px-3 rounded-lg border text-xs font-bold capitalize transition-all cursor-pointer flex flex-col items-center gap-1 ${
                        tier === t
                          ? 'border-primary bg-primary/10 text-primary shadow-[0_0_10px_rgba(212,175,55,0.1)]'
                          : 'border-white/10 bg-black/40 text-text-secondary hover:border-white/20'
                      }`}
                    >
                      <span>{t}</span>
                      {tier === t && <FaCheck size={10} />}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 bg-primary hover:bg-primary/90 text-black font-extrabold text-xs uppercase tracking-wider rounded-lg shadow-[0_0_15px_rgba(212,175,55,0.3)] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading && <VscLoading className="animate-spin" size={14} />}
              <span>{isLoginMode ? 'Sign In' : 'Create Tenant Account'}</span>
            </button>

            {/* Toggle Mode */}
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsLoginMode(!isLoginMode);
                  setErrorMsg('');
                }}
                className="text-xs text-text-secondary hover:text-primary transition-colors cursor-pointer"
              >
                {isLoginMode
                  ? "Don't have an account? Sign up"
                  : 'Already registered? Sign in'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default AuthModal;
