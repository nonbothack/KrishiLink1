import React from 'react';

/**
 * Standardized progress bar component with percent display and status tone.
 */
export function ProgressBar({
  value = 0,
  max = 100,
  label,
  tone = 'green', // 'green' | 'amber' | 'blue' | 'red'
  showPercentage = true,
  className = '',
}) {
  const pct = Math.min(Math.max(Math.round((value / max) * 100), 0), 100);

  const barColors = {
    green: 'bg-emerald-500',
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
    red: 'bg-red-500',
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-xs text-gray-600 mb-1">
          {label && <span className="font-medium">{label}</span>}
          {showPercentage && <span className="font-semibold">{pct}%</span>}
        </div>
      )}
      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColors[tone] || barColors.green} transition-all duration-500 rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default ProgressBar;
