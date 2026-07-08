/**
 * Purpose:
 * Renders the full screen repository knowledge graph explorer page.
 *
 * Responsibilities:
 * - Handle loading states during repository indexing.
 * - Manage states for selected nodes, search filter inputs, and collapsible sidebars.
 * - Provide a demo mode loading standard simulated tree structures when graphs are empty.
 * - Adhere completely to the Black + Gold premium aesthetic.
 *
 * Props:
 * - onNavigate (function): Callback routing handler to switch active pages.
 *
 * Interactions with backend:
 * - Pulls the constructed knowledge graph data from the AppContext and renders the nodes.
 */

import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import GraphCanvas from '../components/Graph/GraphCanvas';
import GraphSidebar from '../components/Graph/GraphSidebar';
import GraphLoading from '../components/Graph/GraphLoading';
import GraphEmptyState from '../components/Graph/GraphEmptyState';
import { mockGraph } from '../components/Graph/services/mockGraphData';
import { FaNetworkWired, FaGitAlt } from 'react-icons/fa';

export default function GraphViewDashboard({ onNavigate }) {
  const { graphData, setGraphData, indexingState, repoName } = useApp();
  
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchVal, setSearchVal] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [localGraph, setLocalGraph] = useState({ nodes: [], edges: [] });
  
  // Track mock state versus active backend graph
  const [isMockLoaded, setIsMockLoaded] = useState(false);

  // Sync with context graphData
  useEffect(() => {
    if (graphData && graphData.nodes && graphData.nodes.length > 0) {
      setLocalGraph(graphData);
      setIsMockLoaded(false);
    }
  }, [graphData]);

  // Load mock data handler
  const handleLoadMock = () => {
    setLocalGraph(mockGraph);
    setIsMockLoaded(true);
  };

  // Determine graph statistics counts
  const stats = {
    nodes: localGraph.nodes?.length || 0,
    edges: localGraph.edges?.length || 0
  };

  if (indexingState === 'indexing') {
    return <GraphLoading message="Repository indexing in progress. Generating structural trees..." />;
  }

  const hasGraph = localGraph.nodes && localGraph.nodes.length > 0;

  return (
    <div className="h-[calc(100vh-120px)] flex bg-[#030303] select-none text-text">
      {/* 1. COLLAPSIBLE GRAPH SIDEBAR */}
      <GraphSidebar
        selectedNode={selectedNode}
        stats={stats}
        searchVal={searchVal}
        onSearch={setSearchVal}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* 2. MAIN GRAPH VIEWPORT CANVAS */}
      <div className="flex-1 h-full flex flex-col relative bg-black">
        {/* Floating Top Header Info panel */}
        {hasGraph && (
          <div className="absolute top-4 right-4 z-20 bg-black/85 border border-white/10 px-4 py-2.5 rounded-lg backdrop-blur-md flex items-center gap-3.5 shadow-[0_4px_16px_rgba(0,0,0,0.8)] select-text">
            <div className="flex flex-col gap-0.5 min-w-0 max-w-[200px]">
              <span className="text-[8px] uppercase tracking-widest font-extrabold text-primary">Active Scope</span>
              <span className="text-xs font-bold text-text truncate">
                {isMockLoaded ? mockGraph.metadata.repository : (repoName || 'Index Repository')}
              </span>
            </div>
            {isMockLoaded && (
              <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded text-[8px] font-extrabold uppercase tracking-widest flex-shrink-0 animate-pulse">
                Mock Demo Mode
              </span>
            )}
          </div>
        )}

        {hasGraph ? (
          <GraphCanvas
            nodes={localGraph.nodes}
            edges={localGraph.edges}
            onNodeSelect={setSelectedNode}
            selectedNode={selectedNode}
            searchVal={searchVal}
          />
        ) : (
          <GraphEmptyState
            onLoadMock={handleLoadMock}
            onNavigate={onNavigate}
          />
        )}
      </div>
    </div>
  );
}
