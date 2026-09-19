import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export default function PwaLifecycle() {
  const { t } = useLanguage();
  const location = useLocation();
  const [waitingWorker, setWaitingWorker] = useState(null);
  const updateAccepted = useRef(false);

  useEffect(() => {
    if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return undefined;
    let registration;
    let active = true;
    let installingWorker;
    const inspect = () => {
      if (active && registration?.waiting && navigator.serviceWorker.controller) {
        setWaitingWorker(registration.waiting);
      }
    };
    const onControllerChange = () => {
      if (active && updateAccepted.current) window.location.reload();
    };
    navigator.serviceWorker.addEventListener('controllerchange', onControllerChange);
    navigator.serviceWorker.register('/service-worker.js').then((result) => {
      if (!active) return;
      registration = result;
      inspect();
      registration.addEventListener('updatefound', () => {
        installingWorker = registration.installing;
        installingWorker?.addEventListener('statechange', inspect);
      });
    }).catch(() => undefined);
    return () => {
      active = false;
      installingWorker?.removeEventListener('statechange', inspect);
      navigator.serviceWorker.removeEventListener('controllerchange', onControllerChange);
    };
  }, []);

  if (!waitingWorker) return null;
  const onSellFlow = location.pathname === '/sell';
  return (
    <aside className="pwa-update-banner" role="status">
      <span>{onSellFlow ? t('updateAfterForm') : t('appUpdateAvailable')}</span>
      <button
        type="button"
        className="button secondary"
        disabled={onSellFlow}
        onClick={() => {
          updateAccepted.current = true;
          waitingWorker.postMessage({ type: 'ACTIVATE_UPDATE' });
        }}
      >
        <RefreshCw size={17} aria-hidden="true" /> {t('updateApp')}
      </button>
    </aside>
  );
}
