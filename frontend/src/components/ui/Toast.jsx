import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { useLanguage } from '../../hooks/useLanguage';

const ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const STYLES = {
  success: 'bg-emerald-900/90 text-white border-emerald-700',
  error: 'bg-rose-950/90 text-white border-rose-800',
  warning: 'bg-amber-950/90 text-white border-amber-800',
  info: 'bg-slate-900/90 text-white border-slate-700',
};

/**
 * Toast: Ephemeral notification toast supporting standard levels, auto-dismiss,
 * and high-contrast styling for outdoor mobile visibility.
 */
export function Toast({
  id,
  type = 'info',
  title,
  message,
  duration = 4000,
  onDismiss,
}) {
  const { t } = useLanguage();
  const Icon = ICONS[type] || ICONS.info;

  useEffect(() => {
    if (!duration || !onDismiss) return;
    const timer = setTimeout(() => {
      onDismiss(id);
    }, duration);
    return () => clearTimeout(timer);
  }, [id, duration, onDismiss]);

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur-md transition-all animate-in fade-in slide-in-from-top-2 ${
        STYLES[type] || STYLES.info
      }`}
    >
      <Icon className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        {title && <p className="text-sm font-semibold leading-tight">{title}</p>}
        {message && <p className="text-xs text-gray-200 mt-0.5 leading-relaxed">{message}</p>}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={() => onDismiss(id)}
          className="text-gray-400 hover:text-white p-1 rounded-lg transition-colors"
          aria-label={t('closeNotification')}
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export function ToastContainer({ toasts = [], onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast {...toast} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
}

export default Toast;
