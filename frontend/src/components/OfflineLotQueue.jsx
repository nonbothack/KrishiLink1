import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CloudUpload, FilePenLine, Trash2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { createLot, createOperationKey } from '../services/api';
import { canProcessLotQueueEntry, listLotQueue, lotQueueReviewReason, recordLotQueueAttempt, removeLotQueueEntry, storedSessionMatches, updateLotQueueState } from '../lib/offlineStore';

export default function OfflineLotQueue() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loadedOwnerId, setLoadedOwnerId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [online, setOnline] = useState(globalThis.navigator?.onLine !== false);
  const [message, setMessage] = useState('');

  const refresh = useCallback(async () => {
    setMessage('');
    try {
      const result = await listLotQueue(user.id);
      setItems(result);
      setLoadedOwnerId(user.id);
    } catch {
      setItems([]);
      setLoadedOwnerId(user.id);
    } finally {
      setLoading(false);
    }
  }, [user.id]);

  useEffect(() => {
    void refresh();
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, [refresh]);

  async function syncQueue() {
    if (busy || !online || user.role !== 'farmer') return;
    setBusy(true);
    setMessage('');
    let published = 0;
    for (const item of items) {
      if (user.role !== 'farmer' || item.ownerId !== user.id || !storedSessionMatches(item.ownerId)) break;
      if (!canProcessLotQueueEntry(item, user)) {
        await updateLotQueueState(user.id, item.idempotencyKey, 'NEEDS_REVIEW', lotQueueReviewReason(item));
        continue;
      }
      if (globalThis.navigator?.onLine === false) break;
      await recordLotQueueAttempt(user.id, item.idempotencyKey);
      const result = await createLot(item.payload, item.idempotencyKey);
      if (result.success) {
        await removeLotQueueEntry(user.id, item.idempotencyKey);
        published += 1;
        continue;
      }
      if ([401, 403, 409, 422].includes(result.status)) {
        const reason = ({ 401: 'auth', 403: 'forbidden', 409: 'conflict', 422: 'validation' })[result.status];
        await updateLotQueueState(user.id, item.idempotencyKey, 'NEEDS_REVIEW', reason);
      } else if ((item.attempts || 0) + 1 >= 5) {
        await updateLotQueueState(user.id, item.idempotencyKey, 'NEEDS_REVIEW', 'offlineQueueRetryLimit');
      }
      // Network and server failures preserve the same operation/key for a later
      // user-initiated retry. No worker or online event replays it.
      break;
    }
    await refresh();
    if (published) setMessage(t('offlinePublishedCount').replace('{count}', String(published)));
    else if (!online) setMessage(t('offlineQueueNetworkRequired'));
    else setMessage(t('offlineQueueSyncFinished'));
    setBusy(false);
  }

  async function editAsNew(item) {
    const confirmed = window.confirm(t('offlineQueueEditConfirm'));
    if (!confirmed) return;
    const form = {
      crop: item.payload.crop,
      variety_id: item.payload.variety_id || '',
      quantity: item.payload.quantity,
      unit: item.payload.unit,
      price: item.payload.asking_price || '',
      grade: item.payload.grade === 'UNSPECIFIED' ? '' : item.payload.grade || '',
      location: item.payload.location_text,
      district: item.payload.district || '',
    };
    try {
      localStorage.setItem(`listing-draft-${user.id}`, JSON.stringify(form));
      localStorage.setItem(`listing-key-${user.id}`, createOperationKey());
      await removeLotQueueEntry(user.id, item.idempotencyKey);
      await refresh();
      navigate('/sell');
    } catch {
      setMessage(t('offlineQueueStorageUnavailable'));
    }
  }

  async function discard(item) {
    if (!window.confirm(t('offlineQueueDiscardConfirm'))) return;
    await removeLotQueueEntry(user.id, item.idempotencyKey);
    await refresh();
  }

  if (loading || loadedOwnerId !== user.id) return <p role="status">{t('loading')}</p>;
  return (
    <section className="panel offline-queue-panel" aria-labelledby="offline-queue-title">
      <div className="section-heading">
        <div><h2 id="offline-queue-title">{t('offlineQueueTitle')}</h2><p className="muted">{t('offlineQueueTruth')}</p></div>
        <CloudUpload aria-hidden="true" size={22} />
      </div>
      {items.length ? (
        <>
          <ul className="offline-queue-list">
            {items.map((item) => (
              <li className="offline-queue-item" key={item.idempotencyKey}>
                <div>
                  <strong>{t(item.state === 'NEEDS_REVIEW' ? 'offlineQueueNeedsReview' : 'offlineQueueWaiting')}</strong>
                  <p>{item.payload.quantity} {t(item.payload.unit)} · {item.payload.location_text}</p>
                  {item.state === 'NEEDS_REVIEW' && <small>{t(item.reasonCode || 'offlineQueueReviewReason')}</small>}
                  <small>{new Date(item.createdAt).toLocaleString()}</small>
                </div>
                <div className="offline-queue-actions">
                  {item.state === 'NEEDS_REVIEW' && <button className="button secondary" type="button" onClick={() => editAsNew(item)}><FilePenLine size={17} />{t('offlineQueueEditNew')}</button>}
                  <button className="text-link" type="button" onClick={() => discard(item)}><Trash2 size={16} />{t('offlineQueueDiscard')}</button>
                </div>
              </li>
            ))}
          </ul>
          <button className="button" type="button" disabled={busy || !online || !items.some((item) => item.state === 'QUEUED')} onClick={syncQueue}>
            <CloudUpload size={18} aria-hidden="true" />{t(busy ? 'offlineQueueSyncing' : 'offlineQueueSync')}
          </button>
          {!online && <p className="field-hint" role="status">{t('offlineQueueNetworkRequired')}</p>}
        </>
      ) : (
        <p>{t('offlineQueueEmpty')}</p>
      )}
      {message && <p role="status" className="field-hint">{message}</p>}
      <p className="field-hint"><Link to="/sell">{t('sellProduce')}</Link> · {t('offlineQueueNoOtherActions')}</p>
    </section>
  );
}
