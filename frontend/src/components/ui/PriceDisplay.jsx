import React from 'react';

/**
 * Standardized agricultural price display with unit, benchmark tags, and currency formatting.
 */
export function PriceDisplay({
  amount,
  unit = 'QTL',
  badge,
  badgeTone = 'gray',
  size = 'md', // 'sm' | 'md' | 'lg'
  subtext,
  className = '',
}) {
  const sizeClasses = {
    sm: 'text-sm font-semibold',
    md: 'text-lg font-bold',
    lg: 'text-2xl font-extrabold',
  };

  const toneClasses = {
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
  };

  return (
    <div className={`inline-flex flex-col ${className}`}>
      <div className="flex items-baseline gap-1.5 flex-wrap">
        <span className={`text-gray-900 ${sizeClasses[size] || sizeClasses.md}`}>
          ₹{Number(amount || 0).toLocaleString('en-IN')}
        </span>
        {unit && (
          <span className="text-xs text-gray-500 font-medium">/{unit}</span>
        )}
        {badge && (
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
              toneClasses[badgeTone] || toneClasses.gray
            }`}
          >
            {badge}
          </span>
        )}
      </div>
      {subtext && <span className="text-[10px] text-gray-400 mt-0.5">{subtext}</span>}
    </div>
  );
}

export default PriceDisplay;
