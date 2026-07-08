/**
 * Purpose:
 * Renders a Python Variable/Attribute symbol node.
 *
 * Responsibilities:
 * - Render variable name and scope details.
 * - Display box styling with amber/yellow highlights.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaSlidersH } from 'react-icons/fa';

export default function VariableNode({ data, selected }) {
  const symbol = data.symbol_name || 'variable_name';
  const path = data.file_path || 'module.py';
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0F0D0A] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.4)] scale-[1.02]' : 'border-amber-400/30 hover:border-amber-400/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-amber-400 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 flex-shrink-0">
          <FaSlidersH size={13} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-amber-400/70">Variable</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex justify-between items-center text-[8px] text-text-secondary select-text">
        <span className="truncate max-w-[130px] font-mono">{path.split('/').pop()}</span>
        <span className="text-[7px] text-amber-400 font-extrabold uppercase tracking-widest bg-amber-500/10 border border-amber-500/20 px-1 rounded flex-shrink-0">
          Global
        </span>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-amber-400 !w-2 !h-2 !border-none" />
    </div>
  );
}
