/**
 * Purpose:
 * Renders custom relation edges with hover-states and label capsules in React Flow.
 *
 * Responsibilities:
 * - Calculate bezier path between nodes.
 * - Render relationship label (e.g. CALLS, IMPORTS) on top of the edge path.
 * - Color-code paths based on relation type (CALLS = cyan, INHERITS = violet, etc.).
 * - Implement hover tooltips explaining the relation.
 *
 * Props:
 * - id (string): React Flow edge ID.
 * - sourceX, sourceY, targetX, targetY: Coordinates of the nodes.
 * - sourcePosition, targetPosition: Handle orientations.
 * - data (object): Attributes (relation, confidence, resolved, source_file).
 */

import React, { useState } from 'react';
import { getBezierPath, EdgeLabelRenderer } from '@xyflow/react';

export default function CustomGraphEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data = {}
}) {
  const [isHovered, setIsHovered] = useState(false);
  const relation = data.relation || 'CALLS';
  const confidence = data.confidence || 'high';

  // Compute bezier path coordinates
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Relation color-coding helper
  const getRelationColor = (rel) => {
    const r = rel.toLowerCase();
    if (r === 'calls' || r === 'instantiates' || r === 'returns') return '#3b82f6'; // Blue
    if (r === 'inherits') return '#8b5cf6'; // Violet
    if (r === 'imports') return '#f59e0b'; // Amber
    if (r === 'contains' || r === 'defines') return '#6b7280'; // Gray
    if (r === 'decorates') return '#ec4899'; // Pink
    if (r === 'raises') return '#ef4444'; // Red
    return '#10b981'; // Green
  };

  const color = getRelationColor(relation);

  const edgeStyle = {
    ...style,
    stroke: color,
    strokeWidth: isHovered ? 2.5 : 1.5,
    strokeDasharray: (relation.toLowerCase() === 'contains' || relation.toLowerCase() === 'defines') ? '4 4' : undefined,
    filter: isHovered ? `drop-shadow(0 0 6px ${color})` : undefined,
    transition: 'stroke-width 0.2s, filter 0.2s',
  };

  return (
    <>
      {/* Visual Bezier Path */}
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        style={edgeStyle}
        markerEnd={markerEnd}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />

      {/* Edge Interaction wrapper for better mouse hover sensitivity */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={15}
        className="cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />

      {/* Label Capsule Render */}
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="select-none z-10"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <div
            style={{ borderColor: color }}
            className={`px-1.5 py-0.5 rounded bg-black/90 border text-[7px] font-extrabold uppercase tracking-widest text-text transition-all duration-300 ${
              isHovered ? 'scale-110 shadow-md' : 'opacity-80'
            }`}
          >
            {relation}
          </div>

          {/* Hover Tooltip Overlay */}
          {isHovered && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 w-48 bg-[#0F0F0F] border border-white/10 rounded-md p-2 shadow-2xl z-50 text-[9px] pointer-events-none select-text leading-normal animate-fade-in text-text">
              <div className="font-extrabold text-primary uppercase tracking-wider mb-0.5">{relation} relationship</div>
              <div>Confidence: <span className="font-bold text-emerald-400 capitalize">{confidence}</span></div>
              {data.source_file && (
                <div className="text-text-secondary truncate mt-0.5">
                  Source: <span className="font-mono">{data.source_file.split('/').pop()}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
