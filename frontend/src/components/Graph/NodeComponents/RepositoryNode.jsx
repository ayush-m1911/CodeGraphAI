/**
 * Purpose:
 * Renders the top-level Repository root node inside the React Flow visual canvas.
 *
 * Responsibilities:
 * - Render repository title, simple symbol name, and containing folder path.
 * - Display a glowing gold border and git branch branding icon.
 * - Provide top/bottom connection handles styled with theme colors.
 *
 * Props:
 * - data (object): Object containing node attributes (symbol_name, docstring, children, etc.).
 * - selected (boolean): Active selection state flag.
 *
 * Interactions with backend:
 * - Visualizes the base node created during repository indexing.
 *
 * Future extensions:
 * - Click to show full repository-wide indexing metrics or run git diagnostics.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaGitAlt } from 'react-icons/fa';

export default function RepositoryNode({ data, selected }) {
  const symbol = data.symbol_name || 'Repository';
  const doc = data.docstring || 'Repository root node.';
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-black/90 border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-primary shadow-[0_0_15px_rgba(212,175,55,0.4)] scale-[1.02]' : 'border-primary/40 hover:border-primary/75 hover:scale-[1.01]'
    }`}>
      {/* Top Handle */}
      <Handle type="target" position={Position.Top} className="!bg-primary !w-2 !h-2 !border-none !shadow-[0_0_4px_rgba(212,175,55,0.8)]" />
      
      {/* Node Content */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-primary/10 border border-primary/20 flex items-center justify-center text-primary flex-shrink-0">
          <FaGitAlt size={16} className="animate-pulse" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-primary/70">Repository</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      {data.children && data.children.length > 0 && (
        <div className="mt-2 pt-1.5 border-t border-white/5 flex justify-between items-center text-[8px] text-text-secondary">
          <span>Hierarchy Nesting</span>
          <span className="font-extrabold text-primary bg-primary/10 border border-primary/20 px-1 rounded">
            {data.children.length} members
          </span>
        </div>
      )}
      
      {/* Bottom Handle */}
      <Handle type="source" position={Position.Bottom} className="!bg-primary !w-2 !h-2 !border-none !shadow-[0_0_4px_rgba(212,175,55,0.8)]" />
    </div>
  );
}
