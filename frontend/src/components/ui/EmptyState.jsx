import React from 'react';
import { PackageOpen, ArrowRight } from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';

/**
 * EmptyState: Standardized visual placeholder when a collection, query or queue is empty.
 * Provides clear headline, explanation, and an actionable next step.
 */
export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon: Icon = PackageOpen,
  className = '',
}) {
  const { t } = useLanguage();
  const displayTitle = title || t('emptyStateDefaultTitle');
  const displayDescription = description !== undefined ? description : t('emptyStateDefaultDesc');

  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center bg-white border border-dashed border-gray-300 rounded-xl my-4 ${className}`}>
      <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center text-green-600 mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-gray-900">{displayTitle}</h3>
      {displayDescription && (
        <p className="mt-1 text-sm text-gray-500 max-w-sm">{displayDescription}</p>
      )}
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-green-700 hover:bg-green-800 rounded-lg shadow-sm transition-colors"
        >
          <span>{actionLabel}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
export default EmptyState;
