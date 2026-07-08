/**
 * Purpose:
 * Renders the empty state indicator panel for the graph canvas.
 *
 * Responsibilities:
 * - Render description text and git network icons in black/gold palette.
 * - Provide interactive shortcut buttons to trigger mock repository layout load or redirect.
 *
 * Props:
 * - onLoadMock (function): callback to trigger mock data rendering.
 * - onNavigate (function): page redirection router callback.
 */

import React from 'react';
import { FaNetworkWired, FaGitAlt } from 'react-icons/fa';

export default function GraphEmptyState({ onLoadMock, onNavigate }) {
  return (
    <div className="h-full flex flex-col justify-center items-center text-center p-8 select-none bg-black/40">
      <div className="w-16 h-16 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-6 shadow-[0_0_24px_rgba(212,175,55,0.15)] animate-pulse">
        <FaNetworkWired size={28} />
      </div>
      
      <h2 className="text-lg font-bold text-text mb-2">No Active Repository Indexed</h2>
      <p className="text-xs text-text-secondary max-w-sm leading-relaxed mb-6">
        Graph visualizations are computed automatically during repository ingestion. Connect and parse a repository first, or load a mock demonstration database.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onLoadMock}
          className="px-4 py-2 border border-primary text-primary hover:bg-primary/10 rounded-md font-bold text-xs transition-all uppercase tracking-wider cursor-pointer"
        >
          Load Mock Graph Demo
        </button>
        
        <button
          onClick={() => onNavigate('setup')}
          className="px-4 py-2 bg-primary text-black hover:bg-primary-hover font-bold text-xs transition-all uppercase tracking-wider rounded-md cursor-pointer flex items-center gap-1.5"
        >
          <FaGitAlt size={12} />
          <span>Connect Repository</span>
        </button>
      </div>
    </div>
  );
}
