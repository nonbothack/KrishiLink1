import { useEffect, useState } from 'react';
import { BellRing } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';
import { disableWebPush, enableWebPush, isPushSupported, reconcileGrantedSubscription } from '../services/webPush';
import { apiCall } from '../lib/http';

export default function WebPushPreferences() {
  const { t, language } = useLanguage();
  const [status, setStatus] = useState('CHECKING');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    async function inspect() {
      if (!isPushSupported()) {
        if (active) setStatus('UNSUPPORTED');
        return;
      }
      if (Notification.permission === 'denied') {
        if (active) setStatus('DENIED');
        return;
      }
      try {
        const capability = await apiCall('/api/v1/notifications/push/capability');
        if (!capability.success || capability.data?.status !== 'AVAILABLE') {
          if (active) setStatus('UNAVAILABLE');
          return;
        }
        const result = await reconcileGrantedSubscription();
        if (!active) return;
        setStatus(result.status === 'ACTIVE' ? 'ACTIVE' : result.status === 'REASSOCIATION_REQUIRED' ? 'REASSOCIATION_REQUIRED' : result.status === 'UNAVAILABLE' ? 'UNAVAILABLE' : 'OFF');
      } catch {
        if (active) setStatus('UNAVAILABLE');
      }
    }
    void inspect();
    return () => { active = false; };
  }, []);

  async function enable() {
    setBusy(true);
    try {
      const result = await enableWebPush(language);
      setStatus(result.status);
    } catch {
      setStatus('UNAVAILABLE');
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);
    try {
      const result = await disableWebPush();
      setStatus(result.status === 'DISABLED' ? 'OFF' : 'UNAVAILABLE');
    } finally {
      setBusy(false);
    }
  }

  const stateCopy = {
    CHECKING: 'pushChecking',
    ACTIVE: 'pushActive',
    OFF: 'pushOff',
    DENIED: 'pushDenied',
    UNSUPPORTED: 'pushUnsupported',
    UNAVAILABLE: 'pushUnavailable',
    NOT_GRANTED: 'pushNotGranted',
    CONFLICT: 'pushReassociate',
    REASSOCIATION_REQUIRED: 'pushReassociate',
    UNSUBSCRIBE_INCOMPLETE: 'pushUnavailable',
  };

  return (
    <section className="panel web-push-preferences" aria-labelledby="push-preferences-title">
      <h3 id="push-preferences-title"><BellRing size={20} aria-hidden="true" /> {t('pushTitle')}</h3>
      <p role="status">{t(stateCopy[status] || 'pushOff')}</p>
      {status === 'ACTIVE' ? (
        <button className="button secondary" type="button" disabled={busy} onClick={disable}>
          {busy ? t('pushWorking') : t('pushTurnOff')}
        </button>
      ) : ['OFF', 'REASSOCIATION_REQUIRED', 'CONFLICT', 'NOT_GRANTED'].includes(status) ? (
        <button className="button primary" type="button" disabled={busy} onClick={enable}>
          {busy ? t('pushWorking') : t(status === 'REASSOCIATION_REQUIRED' || status === 'CONFLICT' ? 'pushTurnOnForAccount' : 'pushTurnOn')}
        </button>
      ) : null}
      <small>{t('pushPrivacyNote')}</small>
    </section>
  );
}
