/**
 * Purpose:
 * Renders a Python Class symbol node.
 *
 * Responsibilities:
 * - Render class identifier, FQN prefix, and class signatures.
 * - Display code box formatting with violet highlights.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaCube } from 'react-icons/fa';

export default function ClassNode({ data, selected }) {
  const symbol = data.symbol_name || 'MyClass';
  const sig = data.signature || `class ${symbol}`;
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0C0B0E] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-violet-500 shadow-[0_0_12px_rgba(139,92,246,0.4)] scale-[1.02]' : 'border-violet-500/30 hover:border-violet-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-violet-500 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 flex-shrink-0">
          <FaCube size={14} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-violet-400/70">Class</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex items-center text-[8px] text-text-secondary select-text font-mono truncate">
        <span className="text-violet-300 font-semibold" title={sig}>{sig}</span>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-violet-500 !w-2 !h-2 !border-none" />
    </div>
  );
}
