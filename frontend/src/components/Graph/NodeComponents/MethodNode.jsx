/**
 * Purpose:
 * Renders a Python Class Method symbol node.
 *
 * Responsibilities:
 * - Render method identifier, arguments signature, and code block scope.
 * - Display code styling with blue/cyan highlights.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaCodeBranch } from 'react-icons/fa';

export default function MethodNode({ data, selected }) {
  const symbol = data.symbol_name || 'method_name';
  const sig = data.signature || `def ${symbol}(self)`;
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0A0C0E] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.4)] scale-[1.02]' : 'border-blue-500/30 hover:border-blue-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-blue-500 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 flex-shrink-0">
          <FaCodeBranch size={13} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-blue-400/70">Method</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex items-center text-[8px] text-text-secondary select-text font-mono truncate">
        <span className="text-blue-300 font-semibold" title={sig}>{sig}</span>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-blue-500 !w-2 !h-2 !border-none" />
    </div>
  );
}
