import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

/**
 * Accessible Tooltip for explaining agricultural, regulatory, and financial concepts.
 */
export function Tooltip({ text, children, className = '' }) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children || (
        <button
          type="button"
          aria-label="More information"
          className="text-gray-400 hover:text-gray-600 focus:outline-none cursor-help p-0.5"
        >
          <HelpCircle className="w-3.5 h-3.5" />
        </button>
      )}

      {visible && (
        <div
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2.5 bg-slate-900 text-white text-[11px] leading-relaxed rounded-lg shadow-xl border border-slate-700 pointer-events-none"
        >
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900" />
        </div>
      )}
    </div>
  );
}

export default Tooltip;
