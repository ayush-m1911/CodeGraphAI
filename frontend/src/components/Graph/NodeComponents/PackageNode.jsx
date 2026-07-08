/**
 * Purpose:
 * Renders a directory Package node representing filesystem subfolders.
 *
 * Responsibilities:
 * - Render package name, absolute folder path, and child count metrics.
 * - Display folder styling matching HSL gold accents.
 *
 * Props:
 * - data (object): Object containing node attributes.
 * - selected (boolean): Active selection state flag.
 *
 * Interactions with backend:
 * - Represents package structures generated dynamically in the hierarchy.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { FaFolderOpen } from 'react-icons/fa';

export default function PackageNode({ data, selected }) {
  const symbol = data.symbol_name || 'package';
  const parent = data.parent || 'root';
  
  return (
    <div className={`px-4 py-3 rounded-lg bg-[#0F0F0F] border transition-all duration-300 min-w-[200px] shadow-[0_4px_12px_rgba(0,0,0,0.5)] ${
      selected ? 'border-amber-500 shadow-[0_0_12px_rgba(200,125,40,0.4)] scale-[1.02]' : 'border-amber-500/30 hover:border-amber-500/70 hover:scale-[1.01]'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-amber-500 !w-2 !h-2 !border-none" />
      
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 flex-shrink-0">
          <FaFolderOpen size={14} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-extrabold uppercase tracking-widest text-amber-500/70">Package</div>
          <div className="text-xs font-bold text-text truncate">{symbol}</div>
        </div>
      </div>
      
      {data.children && data.children.length > 0 && (
        <div className="mt-2 pt-1.5 border-t border-white/5 flex justify-between items-center text-[8px] text-text-secondary">
          <span>Subfolders / Modules</span>
          <span className="font-extrabold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1 rounded">
            {data.children.length} items
          </span>
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="!bg-amber-500 !w-2 !h-2 !border-none" />
    </div>
  );
}
