import React from 'react';

/**
 * Reusable MoneyBreakdown for transparent agricultural trade finances.
 * items: [{ label, amount, type: 'add' | 'deduct' | 'neutral', isEstimate, subtitle }]
 * total: { label, amount, subtitle }
 */
export function MoneyBreakdown({ items = [], total, className = '' }) {
  return (
    <div className={`bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs ${className}`}>
      <div className="space-y-2.5">
        {items.map((item, idx) => {
          const isDeduct = item.type === 'deduct';
          const isAdd = item.type === 'add';

          return (
            <div key={idx} className="flex justify-between items-start gap-2">
              <div>
                <span className="font-medium text-gray-700 flex items-center gap-1.5">
                  {item.label}
                  {item.isEstimate && (
                    <span className="bg-amber-100 text-amber-800 text-[10px] font-semibold px-1.5 py-0.2 rounded border border-amber-200">
                      Estimate
                    </span>
                  )}
                </span>
                {item.subtitle && (
                  <p className="text-[10px] text-gray-400 mt-0.5">{item.subtitle}</p>
                )}
              </div>
              <span
                className={`font-semibold whitespace-nowrap ${
                  isDeduct
                    ? 'text-red-600'
                    : isAdd
                    ? 'text-emerald-700'
                    : 'text-gray-800'
                }`}
              >
                {isDeduct ? '-' : isAdd ? '+' : ''}₹
                {Math.abs(Number(item.amount) || 0).toLocaleString('en-IN', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          );
        })}
      </div>

      {total && (
        <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between items-baseline">
          <div>
            <span className="text-sm font-bold text-gray-900">{total.label}</span>
            {total.subtitle && (
              <p className="text-[10px] text-gray-500">{total.subtitle}</p>
            )}
          </div>
          <span className="text-base font-bold text-emerald-800">
            ₹
            {Number(total.amount || 0).toLocaleString('en-IN', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
      )}
    </div>
  );
}

export default MoneyBreakdown;
