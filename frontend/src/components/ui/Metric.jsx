import React from 'react';
import { HelpCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * Reusable Metric component for KPI displays with label, value, subtext, delta, and tooltip.
 */
export function Metric({
  label,
  value,
  subtext,
  delta,
  trend, // 'up' | 'down' | 'neutral'
  tooltip,
  icon: Icon,
  className = '',
}) {
  return (
    <div className={`card p-4 flex flex-col justify-between ${className}`}>
      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span className="font-medium flex items-center gap-1">
          {label}
          {tooltip && (
            <span title={tooltip} className="cursor-help text-gray-400 hover:text-gray-600">
              <HelpCircle className="w-3.5 h-3.5" />
            </span>
          )}
        </span>
        {Icon && <Icon className="w-4 h-4 text-gray-400" />}
      </div>

      <div className="flex items-baseline justify-between gap-2 my-1">
        <span className="text-xl sm:text-2xl font-bold text-gray-900 tracking-tight">
          {value}
        </span>
        {delta && (
          <span
            className={`inline-flex items-center text-xs font-semibold ${
              trend === 'up'
                ? 'text-emerald-700'
                : trend === 'down'
                ? 'text-red-600'
                : 'text-gray-500'
            }`}
          >
            {trend === 'up' && <TrendingUp className="w-3 h-3 mr-0.5" />}
            {trend === 'down' && <TrendingDown className="w-3 h-3 mr-0.5" />}
            {trend === 'neutral' && <Minus className="w-3 h-3 mr-0.5" />}
            {delta}
          </span>
        )}
      </div>

      {subtext && <p className="text-[11px] text-gray-400 mt-0.5">{subtext}</p>}
    </div>
  );
}

export default Metric;
