/**
 * Purpose:
 * Renders a Configuration/External boundary symbol node.
 *
 * Responsibilities:
 * - Render boundary name and dependency details.
 * - Display box styling with neutral/grey highlights.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaWrench } from 'react-icons/fa';

export default function ConfigurationNode({ data, selected }) {
  const symbol = data.symbol_name || 'external_dependency';
  const doc = data.docstring || 'Boundary configuration element.';
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0E0E0E] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-gray-400 shadow-[0_0_12px_rgba(156,163,175,0.4)] scale-[1.02]' : 'border-gray-500/30 hover:border-gray-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-gray-400 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-gray-500/10 border border-gray-500/20 flex items-center justify-center text-gray-400 flex-shrink-0">
          <FaWrench size={12} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-gray-400/70">Boundary / Config</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      <div className="mt-2 pt-1.5 border-t border-white/5 flex items-center text-[8px] text-text-secondary select-text truncate">
        <span className="text-gray-300 font-semibold" title={doc}>{doc}</span>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400 !w-2 !h-2 !border-none" />
    </div>
  );
}
