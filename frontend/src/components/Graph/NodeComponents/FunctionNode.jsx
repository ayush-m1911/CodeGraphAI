/**
 * Purpose:
 * Renders a Python top-level Function symbol node.
 *
 * Responsibilities:
 * - Render function identifier, parameters signature, and docstrings.
 * - Display box styling with rose/pink highlights.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaTerminal } from 'react-icons/fa';

export default function FunctionNode({ data, selected }) {
  const symbol = data.symbol_name || 'func_name';
  const sig = data.signature || `def ${symbol}()`;
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0E0A0C] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-pink-500 shadow-[0_0_12px_rgba(236,72,153,0.4)] scale-[1.02]' : 'border-pink-500/30 hover:border-pink-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-pink-500 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 flex-shrink-0">
          <FaTerminal size={12} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-pink-400/70">Function</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex items-center text-[8px] text-text-secondary select-text font-mono truncate">
        <span className="text-pink-300 font-semibold" title={sig}>{sig}</span>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-pink-500 !w-2 !h-2 !border-none" />
    </div>
  );
}
