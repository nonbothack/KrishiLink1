// =============================================================
// KrishiLink — Offline Connection Awareness Banner (Stage 9 / §44)
// Truthfully alerts users when internet connectivity is interrupted.
// =============================================================

import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

export default function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(typeof navigator !== 'undefined' ? !navigator.onLine : false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleCheckConnection = () => {
    setChecking(true);
    setTimeout(() => {
      setIsOffline(!navigator.onLine);
      setChecking(false);
    }, 600);
  };

  if (!isOffline) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="sticky top-0 z-50 bg-rose-600 text-white px-4 py-2.5 shadow-md flex items-center justify-between gap-3 text-xs"
    >
      <div className="flex items-center gap-2 min-w-0">
        <WifiOff className="h-4 w-4 shrink-0 text-rose-200 animate-pulse" />
        <p className="truncate">
          <strong className="font-bold">Offline:</strong> Connection lost. Live updates and trade actions are paused until reconnected.
        </p>
      </div>
      <button
        type="button"
        onClick={handleCheckConnection}
        disabled={checking}
        className="shrink-0 bg-white/20 hover:bg-white/30 px-2.5 py-1 rounded font-bold transition flex items-center gap-1.5"
      >
        <RefreshCw className={`h-3 w-3 ${checking ? 'animate-spin' : ''}`} />
        <span>{checking ? 'Checking…' : 'Retry'}</span>
      </button>
    </div>
  );
}
