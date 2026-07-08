/**
 * Purpose:
 * Main canvas component that hosts the React Flow graph renderer.
 *
 * Responsibilities:
 * - Render React Flow container wrapping Background grid, Controls, and panel widgets.
 * - Map custom NodeComponents (`nodeTypes`) and EdgeComponents (`edgeTypes`).
 * - Call layout algorithms (`layoutGraphNodes`) to position raw symbol nodes.
 * - Trigger callbacks when elements are selected or search queries update.
 *
 * Props:
 * - nodes (array): Unified list of GraphNode items.
 * - edges (array): List of GraphEdge relations.
 * - onNodeSelect (function): Callback when a node is clicked.
 * - selectedNode (object): Node data representing the active node selection.
 * - searchVal (string): Current search query.
 *
 * Interactions with backend:
 * - Takes inputs parsed during repository indexing and formats them into React Flow models.
 */

import React, { useEffect, useState, useRef } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow
} from '@xyflow/react';

// Import CSS styles directly for React Flow canvas
import '@xyflow/react/dist/style.css';

// Import customized widgets and mappings
import { nodeTypes } from './NodeComponents';
import { edgeTypes } from './EdgeComponents';
import GraphToolbar from './GraphToolbar';
import GraphLegend from './GraphLegend';
import GraphMiniMap from './GraphMiniMap';
import { layoutGraphNodes } from './utils/layout';

function CanvasContent({
  nodes: rawNodes,
  edges: rawEdges,
  onNodeSelect,
  selectedNode,
  searchVal
}) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  const [miniMapVisible, setMiniMapVisible] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  // Apply layout algorithm when inputs change
  useEffect(() => {
    const positionedNodes = layoutGraphNodes(rawNodes, rawEdges);
    
    // Map edges to React Flow layout
    const formattedEdges = (rawEdges || []).map((edge, idx) => ({
      id: `edge-${idx}`,
      source: edge.source,
      target: edge.target,
      type: 'customEdge',
      data: { ...edge },
      // Custom edge style parameters
      style: { strokeWidth: 1.5 }
    }));
    
    setNodes(positionedNodes);
    setEdges(formattedEdges);
    
    // Fit view after small delay to let render complete
    setTimeout(() => {
      fitView({ padding: 0.15, duration: 800 });
    }, 100);
  }, [rawNodes, rawEdges, setNodes, setEdges, fitView]);

  // Handle graph search highlights
  useEffect(() => {
    if (!searchVal) {
      // Remove search highlights
      setNodes((nds) => nds.map((node) => ({
        ...node,
        style: { ...node.style, opacity: 1, filter: 'none' }
      })));
      return;
    }

    const keyword = searchVal.toLowerCase();
    setNodes((nds) => nds.map((node) => {
      const match = node.data?.symbol_name?.toLowerCase().includes(keyword) || 
                    node.id.toLowerCase().includes(keyword);
      return {
        ...node,
        style: {
          ...node.style,
          opacity: match ? 1 : 0.25,
          filter: match ? 'drop-shadow(0 0 10px rgba(212,175,55,0.45))' : 'none',
        }
      };
    }));
  }, [searchVal, setNodes]);

  // Viewport Control Handlers
  const handleReset = () => {
    fitView({ padding: 0.2, duration: 600 });
  };

  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(err => {
        console.error('Fullscreen request failed:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  };

  // Node Selection Handlers
  const handleNodeClick = (event, node) => {
    if (onNodeSelect) {
      onNodeSelect(node.data);
    }
  };

  const handlePaneClick = () => {
    if (onNodeSelect) {
      onNodeSelect(null);
    }
  };

  return (
    <div ref={containerRef} className="w-full h-full relative select-none bg-[#050505] flex-1">
      {/* Interactive Controls Overlay */}
      <GraphToolbar
        onZoomIn={() => zoomIn({ duration: 300 })}
        onZoomOut={() => zoomOut({ duration: 300 })}
        onFitView={() => fitView({ padding: 0.15, duration: 500 })}
        onReset={handleReset}
        miniMapVisible={miniMapVisible}
        onToggleMiniMap={() => setMiniMapVisible(!miniMapVisible)}
        isFullscreen={isFullscreen}
        onToggleFullscreen={handleToggleFullscreen}
      />

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        fitView
        className="w-full h-full"
        minZoom={0.1}
        maxZoom={2.5}
      >
        {/* Background grid */}
        <Background color="#ffffff" gap={20} size={1} opacity={0.03} />
        
        {/* Custom MiniMap */}
        {miniMapVisible && <GraphMiniMap />}
      </ReactFlow>

      {/* Legend widget */}
      <GraphLegend />
    </div>
  );
}

export default function GraphCanvas(props) {
  return (
    <ReactFlowProvider>
      <CanvasContent {...props} />
    </ReactFlowProvider>
  );
}
