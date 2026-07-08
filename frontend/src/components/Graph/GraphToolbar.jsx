/**
 * Purpose:
 * Renders the floating control toolbar for canvas zoom/pan interactions.
 *
 * Responsibilities:
 * - Render Zoom In, Zoom Out, Fit View, Toggle Minimap, Fullscreen, and Expand All actions.
 * - Call standard React Flow viewport hook handlers.
 *
 * Props:
 * - onZoomIn (function): React Flow zoom-in handler.
 * - onZoomOut (function): React Flow zoom-out handler.
 * - onFitView (function): React Flow fit-view handler.
 * - onReset (function): Reset zoom/coordinates handler.
 * - miniMapVisible (boolean): MiniMap visibility toggle state.
 * - onToggleMiniMap (function): MiniMap visibility toggle callback.
 * - isFullscreen (boolean): Fullscreen state flag.
 * - onToggleFullscreen (function): Fullscreen toggle callback.
 */

import React from 'react';
import { 
  FaSearchPlus, 
  FaSearchMinus, 
  FaExpandArrowsAlt, 
  FaUndo, 
  FaMap, 
  FaExpand, 
  FaCompress,
  FaSitemap
} from 'react-icons/fa';

export default function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onFitView,
  onReset,
  miniMapVisible,
  onToggleMiniMap,
  isFullscreen,
  onToggleFullscreen
}) {
  return (
    <div className="absolute top-4 left-4 z-20 flex items-center gap-1.5 p-1.5 bg-black/85 border border-white/10 rounded-lg backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.8)] select-none">
      {/* Zoom In */}
      <button
        onClick={onZoomIn}
        title="Zoom In"
        className="p-2 text-text-secondary hover:text-primary hover:bg-white/5 rounded transition-all cursor-pointer"
      >
        <FaSearchPlus size={12} />
      </button>

      {/* Zoom Out */}
      <button
        onClick={onZoomOut}
        title="Zoom Out"
        className="p-2 text-text-secondary hover:text-primary hover:bg-white/5 rounded transition-all cursor-pointer"
      >
        <FaSearchMinus size={12} />
      </button>

      {/* Fit View */}
      <button
        onClick={onFitView}
        title="Fit View to Screen"
        className="p-2 text-text-secondary hover:text-primary hover:bg-white/5 rounded transition-all cursor-pointer"
      >
        <FaExpandArrowsAlt size={12} />
      </button>

      {/* Reset view */}
      <button
        onClick={onReset}
        title="Reset Position"
        className="p-2 text-text-secondary hover:text-primary hover:bg-white/5 rounded transition-all cursor-pointer"
      >
        <FaUndo size={11} />
      </button>

      {/* Divider */}
      <div className="w-[1px] h-4 bg-white/10 mx-1" />

      {/* Toggle MiniMap */}
      <button
        onClick={onToggleMiniMap}
        title="Toggle MiniMap Overview"
        className={`p-2 rounded transition-all cursor-pointer ${
          miniMapVisible ? 'text-primary bg-primary/10' : 'text-text-secondary hover:text-primary hover:bg-white/5'
        }`}
      >
        <FaMap size={11} />
      </button>

      {/* Fullscreen */}
      <button
        onClick={onToggleFullscreen}
        title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
        className="p-2 text-text-secondary hover:text-primary hover:bg-white/5 rounded transition-all cursor-pointer"
      >
        {isFullscreen ? <FaCompress size={12} /> : <FaExpand size={11} />}
      </button>

      {/* Future Expand All placeholder */}
      <button
        disabled
        title="Expand All Nodes (Future Integration)"
        className="p-2 text-text-secondary/30 rounded cursor-not-allowed"
      >
        <FaSitemap size={12} />
      </button>
    </div>
  );
}
