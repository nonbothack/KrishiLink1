import React from 'react';
import { useLanguage } from '../../hooks/useLanguage';

/**
 * Standardized status badge supporting domain, lifecycle, and truthfulness classifications.
 * Truth categories: VERIFIED, DECLARED, CALCULATED, ESTIMATED, SANDBOX, SIMULATION, NOT CONNECTED
 */
export function StatusBadge({ status, label, tone, className = '' }) {
  const { t } = useLanguage();
  const norm = (status || '').toUpperCase().trim();

  // Tone maps
  const toneClasses = {
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  };

  // Truthfulness badges
  const truthMap = {
    VERIFIED: { tone: 'green', text: 'Verified' },
    DECLARED: { tone: 'gray', text: 'Declared' },
    CALCULATED: { tone: 'blue', text: 'Calculated' },
    ESTIMATED: { tone: 'amber', text: 'Estimate Only' },
    SANDBOX: { tone: 'amber', text: 'Sandbox' },
    SIMULATION: { tone: 'purple', text: 'Simulation' },
    NOT_CONNECTED: { tone: 'red', text: 'Not Connected' },
    MISSING: { tone: 'red', text: 'Missing' },

    // FSM & Commercial Statuses
    ACTIVE: { tone: 'green', text: 'Active' },
    COMPLETED: { tone: 'green', text: 'Completed' },
    SETTLED: { tone: 'green', text: 'Settled' },
    ACCEPTED: { tone: 'green', text: 'Accepted' },
    CONFIRMED: { tone: 'green', text: 'Confirmed' },
    PENDING: { tone: 'amber', text: 'Pending' },
    PAYMENT_PENDING: { tone: 'amber', text: 'Payment Pending' },
    PAYMENT_CONFIRMED: { tone: 'blue', text: 'Payment In Custody' },
    IN_TRANSIT: { tone: 'blue', text: 'In Transit' },
    UNDER_REVIEW: { tone: 'blue', text: 'Under Review' },
    DISPUTE_OPEN: { tone: 'red', text: 'Dispute Open' },
    REJECTED: { tone: 'red', text: 'Rejected' },
    EXPIRED: { tone: 'gray', text: 'Expired' },
    CANCELLED: { tone: 'gray', text: 'Cancelled' },
  };

  const config = truthMap[norm] || { tone: tone || 'gray', text: label || status || 'Unknown' };
  const badgeTone = tone || config.tone;
  const translationKey = `status_${norm.toLowerCase()}`;
  const translated = t(translationKey);
  const displayText = label || (translated && translated !== translationKey ? translated : null) || config.text;

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium text-xs px-2.5 py-0.5 rounded-full border ${toneClasses[badgeTone] || toneClasses.gray} ${className}`}
    >
      {displayText}
    </span>
  );
}

export default StatusBadge;
