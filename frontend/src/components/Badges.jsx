// =============================================================
// Trend Badge Component
// Shows RISING / FALLING / STABLE with color and icon
// =============================================================

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function TrendBadge({ trend, change }) {
  const t = (trend || '').toUpperCase();
  const hasChange = change != null && !isNaN(Number(change));
  const numChange = hasChange ? Number(change) : null;
  const changeText = numChange != null ? (numChange > 0 ? `+${numChange}%` : `${numChange}%`) : '';

  if (t === 'RISING') {
    return (
      <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-green-200">
        <TrendingUp className="w-3.5 h-3.5" />
        Rising {changeText}
      </span>
    );
  }
  if (t === 'FALLING') {
    return (
      <span className="inline-flex items-center gap-1 bg-red-100 text-red-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-red-200">
        <TrendingDown className="w-3.5 h-3.5" />
        Falling {changeText}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-amber-200">
      <Minus className="w-3.5 h-3.5" />
      Stable {changeText}
    </span>
  );
}

// =============================================================
// Status Badge Component
// Shows offer/transaction/grievance status with color
// =============================================================
export function StatusBadge({ status }) {
  const map = {
    active:       'badge-green',
    pending:      'badge-yellow',
    accepted:     'badge-green',
    rejected:     'badge-red',
    expired:      'badge-gray',
    completed:    'badge-blue',
    matched:      'badge-blue',
    sold:         'badge-gray',
    open:         'badge-yellow',
    under_review: 'badge-blue',
    resolved:     'badge-green',
    received:     'badge-green',
    processing:   'badge-blue',
    failed:       'badge-red',
  };

  const labels = {
    active:       'Active',
    pending:      'Pending',
    accepted:     'Accepted',
    rejected:     'Rejected',
    expired:      'Expired',
    completed:    'Completed',
    matched:      'Matched',
    sold:         'Sold',
    open:         'Open',
    under_review: 'Under Review',
    resolved:     'Resolved',
    received:     'Received',
    processing:   'Processing',
    failed:       'Failed',
  };

  const className = map[status] || 'badge-gray';
  const label = labels[status] || status;

  return <span className={className}>{label}</span>;
}

// =============================================================
// Verified Badge
// =============================================================
export function VerifiedBadge() {
  return (
    <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded-full border border-blue-200">
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      Verified
    </span>
  );
}
