// =============================================================
// KrishiLink — Accessible Route Loading Fallback (Stage 9 / §42)
// Used with React.Suspense during route chunk fetching.
// =============================================================

import React from 'react';
import { Sprout } from 'lucide-react';

export default function PageLoader({ message = 'Loading module…' }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="min-h-[60vh] w-full flex flex-col items-center justify-center p-6 text-center"
    >
      <div className="relative flex items-center justify-center mb-4">
        <div className="w-14 h-14 rounded-full border-4 border-emerald-100 border-t-emerald-600 animate-spin" />
        <div className="absolute w-8 h-8 bg-emerald-50 rounded-full flex items-center justify-center">
          <Sprout className="w-4 h-4 text-emerald-700 animate-pulse" />
        </div>
      </div>
      <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider">{message}</p>
      <p className="text-[11px] text-gray-400 mt-1">Connecting to KrishiLink trade network</p>
      <span className="sr-only">Loading page content, please wait...</span>
    </div>
  );
}
