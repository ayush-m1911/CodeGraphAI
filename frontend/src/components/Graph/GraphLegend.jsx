/**
 * Purpose:
 * Renders the map legend explaining node type colors and relation line types.
 *
 * Responsibilities:
 * - Render list of color-coded symbols (Repository, Class, Method, etc.).
 * - Render relationship line styles and arrow descriptions.
 * - Provide a toggle/collapse control to stay compact.
 *
 * Props:
 * - isOpen (boolean): active panel display state.
 * - onClose (function): toggle callback.
 */

import React, { useState } from 'react';
import { FaInfoCircle, FaAngleRight, FaAngleDown } from 'react-icons/fa';

export default function GraphLegend() {
  const [collapsed, setCollapsed] = useState(false);

  const nodeItems = [
    { label: 'Repository', color: 'bg-primary border-primary/45' },
    { label: 'Package', color: 'bg-amber-500 border-amber-500/30' },
    { label: 'Module', color: 'bg-emerald-500 border-emerald-500/30' },
    { label: 'Class', color: 'bg-violet-500 border-violet-500/30' },
    { label: 'Method', color: 'bg-blue-500 border-blue-500/30' },
    { label: 'Function', color: 'bg-pink-500 border-pink-500/30' },
    { label: 'Variable', color: 'bg-amber-400 border-amber-400/30' },
    { label: 'Config / External', color: 'bg-gray-500 border-gray-500/30' },
  ];

  const relationItems = [
    { label: 'CALLS / RETURNS', style: 'border-blue-500 border-t-2' },
    { label: 'INHERITS', style: 'border-violet-500 border-t-2' },
    { label: 'IMPORTS', style: 'border-amber-500 border-t-2' },
    { label: 'CONTAINS / DEFINES', style: 'border-gray-500 border-t-2 border-dashed' },
    { label: 'DECORATES', style: 'border-pink-500 border-t-2' },
    { label: 'RAISES', style: 'border-red-500 border-t-2' },
  ];

  return (
    <div className="absolute bottom-4 left-4 z-20 bg-black/85 border border-white/10 rounded-lg backdrop-blur-md max-w-xs shadow-[0_4px_24px_rgba(0,0,0,0.8)] overflow-hidden transition-all duration-300">
      {/* Header */}
      <div 
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between px-3.5 py-2.5 cursor-pointer select-none bg-white/3 hover:bg-white/5"
      >
        <div className="flex items-center gap-2">
          <FaInfoCircle size={12} className="text-primary" />
          <span className="text-[10px] uppercase font-extrabold tracking-widest text-primary">Graph Legend</span>
        </div>
        {collapsed ? <FaAngleRight size={10} className="text-text-secondary" /> : <FaAngleDown size={10} className="text-text-secondary" />}
      </div>

      {/* Lists */}
      {!collapsed && (
        <div className="p-3.5 space-y-4 max-h-[300px] overflow-y-auto select-none border-t border-white/5">
          {/* Nodes list */}
          <div className="space-y-2">
            <span className="text-[8px] font-bold text-text-secondary uppercase tracking-widest block">Node Entities</span>
            <div className="grid grid-cols-2 gap-2">
              {nodeItems.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-sm flex-shrink-0 ${item.color} border`} />
                  <span className="text-[9px] font-bold text-text-secondary">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Relations list */}
          <div className="space-y-2 pt-3 border-t border-white/5">
            <span className="text-[8px] font-bold text-text-secondary uppercase tracking-widest block">Relation Connects</span>
            <div className="grid grid-cols-2 gap-2">
              {relationItems.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className={`w-6 flex-shrink-0 ${item.style}`} />
                  <span className="text-[9px] font-bold text-text-secondary">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
