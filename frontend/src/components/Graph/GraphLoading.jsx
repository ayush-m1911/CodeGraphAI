/**
 * Purpose:
 * Renders the high-quality loading skeleton interface for compiling graphs.
 *
 * Responsibilities:
 * - Render glowing spin animations.
 * - Display progress logs.
 */

import React from 'react';
import { VscLoading } from 'react-icons/vsc';

export default function GraphLoading({ message = 'Resolving symbols and layout positioning...' }) {
  return (
    <div className="h-full flex flex-col justify-center items-center select-none bg-black/50">
      <div className="flex flex-col items-center gap-4 p-6 bg-surface/50 border border-white/5 rounded-xl max-w-xs shadow-2xl backdrop-blur-md">
        <VscLoading className="animate-spin text-primary text-3xl flex-shrink-0" />
        <span className="text-xs text-text-secondary text-center font-bold tracking-wide uppercase">
          {message}
        </span>
      </div>
    </div>
  );
}
