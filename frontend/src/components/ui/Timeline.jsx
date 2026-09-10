import React from 'react';
import { Circle, Clock } from 'lucide-react';

/**
 * Reusable chronological timeline for audit history and logistics milestones.
 * items: [{ id, title, description, timestamp, actor, icon, tone: 'green'|'blue'|'amber'|'gray' }]
 */
export function Timeline({ items = [], className = '' }) {
  if (!items || items.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-gray-400">
        No recorded milestones yet.
      </div>
    );
  }

  const toneColors = {
    green: 'bg-emerald-500 text-white',
    blue: 'bg-blue-500 text-white',
    amber: 'bg-amber-500 text-white',
    gray: 'bg-gray-300 text-gray-700',
    red: 'bg-red-500 text-white',
  };

  return (
    <div className={`flow-root ${className}`}>
      <ul className="-mb-8 space-y-4">
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          const Icon = item.icon || Circle;
          const tone = item.tone || 'green';

          return (
            <li key={item.id || idx} className="relative pb-6">
              {!isLast && (
                <span
                  className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200"
                  aria-hidden="true"
                />
              )}
              <div className="relative flex items-start space-x-3">
                <div
                  className={`relative flex h-8 w-8 items-center justify-center rounded-full shadow-sm ${
                    toneColors[tone] || toneColors.gray
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex justify-between items-baseline gap-2">
                    <p className="text-xs font-bold text-gray-900">{item.title}</p>
                    {item.timestamp && (
                      <span className="text-[10px] text-gray-400 whitespace-nowrap flex items-center gap-1">
                        <Clock className="w-3 h-3 text-gray-400" />
                        {item.timestamp}
                      </span>
                    )}
                  </div>
                  {item.description && (
                    <p className="mt-0.5 text-xs text-gray-600">{item.description}</p>
                  )}
                  {item.actor && (
                    <p className="mt-1 text-[10px] font-medium text-gray-400">
                      By {item.actor}
                    </p>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default Timeline;
