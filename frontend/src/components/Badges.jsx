// =============================================================
// Trend Badge Component
// Shows RISING / FALLING / STABLE with color and icon
// =============================================================

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export function TrendBadge({ trend, change }) {
  const { t: translate } = useLanguage();
  const tr = (trend || '').toUpperCase();
  const hasChange = change != null && !isNaN(Number(change));
  const numChange = hasChange ? Number(change) : null;
  const changeText = numChange != null ? (numChange > 0 ? `+${numChange}%` : `${numChange}%`) : '';

  if (tr === 'RISING') {
    const raw = translate('rising') || 'Rising';
    const label = raw.replace(/^[↑→↓]\s*/, '');
    return (
      <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-green-200">
        <TrendingUp className="w-3.5 h-3.5" />
        {label} {changeText}
      </span>
    );
  }
  if (tr === 'FALLING') {
    const raw = translate('falling') || 'Falling';
    const label = raw.replace(/^[↑→↓]\s*/, '');
    return (
      <span className="inline-flex items-center gap-1 bg-red-100 text-red-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-red-200">
        <TrendingDown className="w-3.5 h-3.5" />
        {label} {changeText}
      </span>
    );
  }
  const raw = translate('stable') || 'Stable';
  const label = raw.replace(/^[↑→↓]\s*/, '');
  return (
    <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-700 font-semibold text-xs px-2.5 py-1 rounded-full border border-amber-200">
      <Minus className="w-3.5 h-3.5" />
      {label} {changeText}
    </span>
  );
}

// =============================================================
// Status Badge Component
// Shows offer/transaction/grievance status with color
// =============================================================
export function StatusBadge({ status }) {
  const { t } = useLanguage();
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
    active:       t('active') || 'Active',
    pending:      t('pending') || 'Pending',
    accepted:     t('accepted') || 'Accepted',
    rejected:     t('rejected') || 'Rejected',
    expired:      t('expired') || 'Expired',
    completed:    t('completed') || 'Completed',
    matched:      t('matched') || 'Matched',
    sold:         t('sold') || 'Sold',
    open:         t('open') || 'Open',
    under_review: t('underReview') || 'Under Review',
    resolved:     t('resolved') || 'Resolved',
    received:     t('paymentReceived') || 'Received',
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
  const { t } = useLanguage();
  return (
    <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded-full border border-blue-200">
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      {t('verified') || 'Verified'}
    </span>
  );
}
