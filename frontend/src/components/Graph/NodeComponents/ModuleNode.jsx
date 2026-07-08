/**
 * Purpose:
 * Renders a Python Module (file) node in the graph layout.
 *
 * Responsibilities:
 * - Render module file name, full file path location, and line counts.
 * - Display file code styling with emerald/cyan highlights.
 *
 * Props:
 * - data (object): Node context properties (symbol_name, file_path, line, etc.).
 * - selected (boolean): Selection indicator.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaFileCode } from 'react-icons/fa';

export default function ModuleNode({ data, selected }) {
  const symbol = data.symbol_name || 'module.py';
  const path = data.file_path || 'path/to/module.py';
  const lineCount = data.end_line || 0;
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0A0E0C] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.4)] scale-[1.02]' : 'border-emerald-500/30 hover:border-emerald-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-emerald-400 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 flex-shrink-0">
          <FaFileCode size={14} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-400/70">Module</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex justify-between items-center text-[8px] text-text-secondary">
        <span className="truncate max-w-[130px]" title={path}>{path}</span>
        {lineCount > 0 && (
          <span className="font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1 rounded flex-shrink-0">
            {lineCount} lines
          </span>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-emerald-400 !w-2 !h-2 !border-none" />
    </div>
  );
}
