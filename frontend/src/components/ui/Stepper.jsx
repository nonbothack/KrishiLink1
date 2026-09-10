import React from 'react';
import { Check } from 'lucide-react';

/**
 * Reusable Stepper for visual lifecycle workflows (trade, fulfillment, tutorial).
 * Steps: [{ id, label, description, state: 'completed' | 'current' | 'upcoming' | 'exception' }]
 */
export function Stepper({ steps = [], currentStepIndex, className = '' }) {
  return (
    <div className={`w-full ${className}`}>
      <nav aria-label="Progress">
        <ol className="flex items-center justify-between gap-2 overflow-x-auto py-2">
          {steps.map((step, idx) => {
            const isCompleted = step.state === 'completed' || (currentStepIndex != null && idx < currentStepIndex);
            const isCurrent = step.state === 'current' || (currentStepIndex != null && idx === currentStepIndex);
            const isException = step.state === 'exception';

            return (
              <li key={step.id || idx} className="relative flex-1 min-w-[80px]">
                <div className="flex flex-col items-center text-center group">
                  {/* Step Circle */}
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                      isException
                        ? 'bg-red-600 text-white ring-4 ring-red-100'
                        : isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-emerald-50 text-emerald-700 border-2 border-emerald-600 ring-4 ring-emerald-50'
                        : 'bg-gray-100 text-gray-500 border border-gray-200'
                    }`}
                  >
                    {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : idx + 1}
                  </div>

                  {/* Label */}
                  <span
                    className={`text-[11px] font-semibold mt-1.5 line-clamp-1 ${
                      isException
                        ? 'text-red-700'
                        : isCurrent
                        ? 'text-emerald-800'
                        : isCompleted
                        ? 'text-gray-800'
                        : 'text-gray-400'
                    }`}
                  >
                    {step.label}
                  </span>

                  {step.description && (
                    <span className="text-[10px] text-gray-400 hidden sm:block line-clamp-1">
                      {step.description}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}

export default Stepper;
