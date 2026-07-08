/**
 * Purpose:
 * Renders the collapsible metadata panel displaying node details and statistics.
 *
 * Responsibilities:
 * - Render details of the selected node (symbol name, signatures, FQN, docstrings).
 * - Render general statistics placeholder (node totals, edges).
 * - Render search bar and filter controls.
 * - Manage collapse transition animations.
 *
 * Props:
 * - selectedNode (object): Node data representing the active node selection.
 * - stats (object): Metrics count from active repository graph.
 * - searchVal (string): Current search keyword.
 * - onSearch (function): Search text modifier callback.
 * - isOpen (boolean): Sidebar collapse display state.
 * - onToggle (function): Sidebar collapse callback.
 */

import React, { useState } from 'react';
import { 
  FaAngleLeft, 
  FaAngleRight, 
  FaInfoCircle, 
  FaSearch, 
  FaChartPie,
  FaFolder,
  FaFileCode,
  FaCube,
  FaTerminal,
  FaSlidersH
} from 'react-icons/fa';

export default function GraphSidebar({
  selectedNode,
  stats = { nodes: 0, edges: 0 },
  searchVal,
  onSearch,
  isOpen,
  onToggle
}) {
  const [activeTab, setActiveTab] = useState('details');

  const getNodeIcon = (type) => {
    const t = type?.toLowerCase() || '';
    if (t === 'package') return <FaFolder className="text-amber-500" />;
    if (t === 'file' || t === 'module') return <FaFileCode className="text-emerald-400" />;
    if (t === 'class') return <FaCube className="text-violet-400" />;
    if (t === 'method' || t === 'function') return <FaTerminal className="text-pink-400" />;
    return <FaInfoCircle className="text-primary" />;
  };

  return (
    <div className={`relative h-full border-r border-white/5 bg-[#090909] flex flex-col transition-all duration-300 ${
      isOpen ? 'w-80' : 'w-0'
    }`}>
      {/* Collapse Button */}
      <button
        onClick={onToggle}
        title={isOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
        className="absolute -right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black border border-white/10 hover:border-primary/50 text-text-secondary hover:text-primary flex items-center justify-center z-30 transition-all cursor-pointer shadow-[0_0_8px_rgba(0,0,0,0.8)]"
      >
        {isOpen ? <FaAngleLeft size={12} /> : <FaAngleRight size={12} />}
      </button>

      {isOpen && (
        <div className="h-full flex flex-col overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="p-4 border-b border-white/5 bg-black/25 flex items-center justify-between select-none">
            <span className="text-[10px] uppercase font-extrabold tracking-widest text-primary">Graph Workspace</span>
            <div className="flex gap-1.5">
              <button 
                onClick={() => setActiveTab('details')}
                className={`px-2.5 py-1 rounded text-[9px] font-bold uppercase transition-all cursor-pointer ${
                  activeTab === 'details' ? 'bg-primary/10 border border-primary/20 text-primary' : 'text-text-secondary hover:text-text'
                }`}
              >
                Details
              </button>
              <button 
                onClick={() => setActiveTab('stats')}
                className={`px-2.5 py-1 rounded text-[9px] font-bold uppercase transition-all cursor-pointer ${
                  activeTab === 'stats' ? 'bg-primary/10 border border-primary/20 text-primary' : 'text-text-secondary hover:text-text'
                }`}
              >
                Stats
              </button>
            </div>
          </div>

          {/* Search bar */}
          <div className="p-4 border-b border-white/5 select-none bg-black/10">
            <div className="relative">
              <FaSearch size={10} className="absolute left-3 top-3 text-text-secondary/50" />
              <input
                type="text"
                placeholder="Search symbol FQN in graph..."
                value={searchVal || ''}
                onChange={(e) => onSearch(e.target.value)}
                className="w-full pl-8 pr-4 py-2 bg-surface border border-white/5 focus:border-primary/40 rounded-lg text-xs focus:outline-none text-text leading-none placeholder:text-text-secondary/40 select-text"
              />
            </div>
          </div>

          {/* Content Pane */}
          <div className="flex-1 overflow-y-auto p-4 select-text">
            {activeTab === 'details' ? (
              selectedNode ? (
                <div className="space-y-4">
                  {/* Selected Node Header */}
                  <div className="flex items-start gap-3 bg-surface/30 p-3 rounded-lg border border-white/5">
                    <div className="w-8 h-8 rounded bg-white/3 border border-white/10 flex items-center justify-center flex-shrink-0">
                      {getNodeIcon(selectedNode.type)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-[8px] uppercase tracking-wider font-extrabold text-primary/75 mb-0.5">
                        {selectedNode.type} Node
                      </div>
                      <h3 className="text-xs font-bold text-text truncate">{selectedNode.symbol_name}</h3>
                    </div>
                  </div>

                  {/* Attributes metadata */}
                  <div className="space-y-3">
                    <span className="text-[9px] font-bold text-text-secondary uppercase tracking-wider block border-b border-white/5 pb-1">Properties</span>
                    
                    {/* FQN */}
                    <div className="space-y-0.5">
                      <div className="text-[8px] font-bold text-text-secondary/60 uppercase">Qualified FQN</div>
                      <div className="text-[10px] font-mono text-text bg-black/40 border border-white/5 px-2.5 py-1.5 rounded break-all leading-normal select-all">
                        {selectedNode.id}
                      </div>
                    </div>

                    {/* File Path */}
                    {selectedNode.file_path && (
                      <div className="space-y-0.5">
                        <div className="text-[8px] font-bold text-text-secondary/60 uppercase">File Path</div>
                        <div className="text-[10px] font-mono text-text truncate" title={selectedNode.file_path}>
                          {selectedNode.file_path}
                        </div>
                      </div>
                    )}

                    {/* Line Range */}
                    {selectedNode.start_line && (
                      <div className="flex justify-between text-[10px]">
                        <span className="text-text-secondary/60">Defined Line Range:</span>
                        <span className="font-semibold text-text">
                          {selectedNode.start_line} {selectedNode.end_line && `-> ${selectedNode.end_line}`}
                        </span>
                      </div>
                    )}

                    {/* Hierarchy Depth */}
                    {selectedNode.hierarchy_depth !== undefined && (
                      <div className="flex justify-between text-[10px]">
                        <span className="text-text-secondary/60">Nesting Tree Depth:</span>
                        <span className="font-semibold text-primary">Level {selectedNode.hierarchy_depth}</span>
                      </div>
                    )}

                    {/* Signature */}
                    {selectedNode.signature && (
                      <div className="space-y-0.5 pt-1.5">
                        <div className="text-[8px] font-bold text-text-secondary/60 uppercase">Signature</div>
                        <pre className="p-2.5 bg-[#070707] border border-white/5 rounded text-[9px] text-emerald-400 overflow-x-auto font-mono max-h-[120px]">
                          <code>{selectedNode.signature}</code>
                        </pre>
                      </div>
                    )}

                    {/* Docstring */}
                    {selectedNode.docstring && (
                      <div className="space-y-0.5 pt-1.5">
                        <div className="text-[8px] font-bold text-text-secondary/60 uppercase">Docstring</div>
                        <div className="p-2.5 bg-surface/20 border border-white/5 rounded text-[10px] text-text-secondary leading-relaxed max-h-[160px] overflow-y-auto whitespace-pre-wrap select-text">
                          {selectedNode.docstring}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col justify-center items-center text-center text-text-secondary/30 select-none py-12">
                  <FaInfoCircle size={22} className="mb-2 animate-bounce" />
                  <span className="text-[10px] uppercase font-bold tracking-wider">Click a Node to View Details</span>
                </div>
              )
            ) : (
              <div className="space-y-5 animate-fade-in">
                {/* Graph Summary */}
                <div className="space-y-3">
                  <span className="text-[9px] font-bold text-text-secondary uppercase tracking-wider block border-b border-white/5 pb-1">Graph Statistics</span>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-3 bg-surface/40 border border-white/5 rounded-lg text-center">
                      <div className="text-lg font-extrabold text-primary">{stats.nodes}</div>
                      <div className="text-[8px] uppercase tracking-wider text-text-secondary/70">Total Nodes</div>
                    </div>
                    <div className="p-3 bg-surface/40 border border-white/5 rounded-lg text-center">
                      <div className="text-lg font-extrabold text-primary">{stats.edges}</div>
                      <div className="text-[8px] uppercase tracking-wider text-text-secondary/70">Total Edges</div>
                    </div>
                  </div>
                </div>

                {/* Legend Shortcut placeholder */}
                <div className="bg-surface/30 border border-white/5 rounded-lg p-3 text-[10px] text-text-secondary leading-relaxed space-y-2 select-none">
                  <div className="flex items-center gap-1.5 text-primary font-bold">
                    <FaChartPie size={11} />
                    <span className="text-[9px] uppercase tracking-wider">Topological Centrality</span>
                  </div>
                  <p className="text-[9px] text-text-secondary/60 leading-normal">
                    This indexes caller in-degree values to isolate highly decoupled framework modules. Expand the Legend below for visual color-coding parameters.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
