/**
 * Purpose:
 * Wraps and styles the React Flow MiniMap element to align with the Golden + Black palette.
 *
 * Responsibilities:
 * - Render compact navigation overlay.
 * - Set background mask colors.
 */

import React from 'react';
import { MiniMap } from '@xyflow/react';

export default function GraphMiniMap() {
  const getNodeColor = (node) => {
    const t = node.type || '';
    if (t === 'repository') return '#d4af37';
    if (t === 'package') return '#c87d28';
    if (t === 'file' || t === 'module') return '#10b981';
    if (t === 'class') return '#8b5cf6';
    if (t === 'method' || t === 'function') return '#ec4899';
    return '#4b5563';
  };

  return (
    <MiniMap
      nodeColor={getNodeColor}
      nodeStrokeWidth={2}
      maskColor="rgba(0, 0, 0, 0.75)"
      className="!bg-black/90 !border !border-white/10 !rounded-lg !shadow-[0_4px_16px_rgba(0,0,0,0.8)] !right-4 !bottom-4"
    />
  );
}
