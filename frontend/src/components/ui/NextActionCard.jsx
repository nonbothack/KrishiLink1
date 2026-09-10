import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, AlertCircle, Clock, ShieldAlert } from 'lucide-react';

const TONE_STYLES = {
  critical: {
    border: 'border-red-300 dark:border-red-800/60',
    bg: 'bg-gradient-to-r from-red-50/80 to-white dark:from-red-950/20 dark:to-slate-900',
    badge: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400',
    btn: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
  },
  warning: {
    border: 'border-amber-300 dark:border-amber-800/60',
    bg: 'bg-gradient-to-r from-amber-50/80 to-white dark:from-amber-950/20 dark:to-slate-900',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-800',
    iconBg: 'bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400',
    btn: 'bg-amber-600 hover:bg-amber-700 text-white focus:ring-amber-500',
  },
  success: {
    border: 'border-emerald-300 dark:border-emerald-800/60',
    bg: 'bg-gradient-to-r from-emerald-50/80 to-white dark:from-emerald-950/20 dark:to-slate-900',
    badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
    iconBg: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400',
    btn: 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500',
  },
  info: {
    border: 'border-blue-300 dark:border-blue-800/60',
    bg: 'bg-gradient-to-r from-blue-50/80 to-white dark:from-blue-950/20 dark:to-slate-900',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-800',
    iconBg: 'bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400',
    btn: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
  },
  neutral: {
    border: 'border-slate-200 dark:border-slate-800',
    bg: 'bg-white dark:bg-slate-900',
    badge: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
    iconBg: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
    btn: 'bg-slate-800 hover:bg-slate-900 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 focus:ring-slate-400',
  },
};

export function NextActionCard({
  title,
  description,
  badge = 'Action Required',
  badgeTone = 'warning',
  primaryAction,
  secondaryAction,
  contextItems = [],
  urgency,
  isDemo = false,
  meta,
  className = '',
}) {
  const tone = TONE_STYLES[badgeTone] || TONE_STYLES.warning;

  const renderButton = (action, isPrimary = false) => {
    if (!action) return null;
    const { label, onClick, to, href, icon: ActionIcon = ArrowRight, disabled = false, variant } = action;

    const baseClass = `inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ${
      disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : 'shadow-sm active:scale-[0.98]'
    }`;

    const styleClass = isPrimary
      ? (variant === 'success'
          ? 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500'
          : variant === 'danger'
          ? 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
          : tone.btn)
      : 'bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 focus:ring-slate-400';

    const content = (
      <>
        <span>{label}</span>
        {ActionIcon && <ActionIcon className="w-4 h-4 flex-shrink-0" />}
      </>
    );

    if (to) {
      return (
        <Link to={to} className={`${baseClass} ${styleClass}`}>
          {content}
        </Link>
      );
    }
    if (href) {
      return (
        <a href={href} className={`${baseClass} ${styleClass}`}>
          {content}
        </a>
      );
    }
    return (
      <button type="button" onClick={onClick} disabled={disabled} className={`${baseClass} ${styleClass}`}>
        {content}
      </button>
    );
  };

  return (
    <div
      className={`relative rounded-2xl border-2 p-5 transition-all shadow-sm ${tone.border} ${tone.bg} ${className}`}
      role="region"
      aria-label={typeof title === 'string' ? title : 'Next Recommended Action'}
    >
      {/* Header: Badges & Urgency */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {badge && (
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${tone.badge}`}>
              <AlertCircle className="w-3 h-3" />
              {badge}
            </span>
          )}
          {isDemo && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
              <ShieldAlert className="w-2.5 h-2.5" />
              DEMO / SANDBOX
            </span>
          )}
          {meta && <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">{meta}</span>}
        </div>

        {urgency && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium">
            <Clock className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            <span>{urgency}</span>
          </div>
        )}
      </div>

      {/* Main Content: Title & Description */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white leading-snug">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{description}</p>
        )}
      </div>

      {/* Context Metrics Grid */}
      {contextItems && contextItems.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 p-3 rounded-xl bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 mb-4">
          {contextItems.map((item, idx) => (
            <div key={idx} className="min-w-0">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate">
                {item.label}
              </p>
              <div className="flex items-center gap-1.5 mt-0.5">
                {item.icon && <item.icon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />}
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">
                  {item.value}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      {(primaryAction || secondaryAction) && (
        <div className="flex flex-wrap items-center gap-3 pt-1">
          {renderButton(primaryAction, true)}
          {renderButton(secondaryAction, false)}
        </div>
      )}
    </div>
  );
}

export default NextActionCard;
