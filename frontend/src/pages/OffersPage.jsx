import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowRight, Clock3 } from 'lucide-react';
import { getOffers, acceptOffer, rejectOffer, counterOffer, getOfferHistory, withdrawOffer } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Field, Notice, PageHeading, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';

const idempotencyName = (userId, offerId, action) => `offer-${action}-key-${userId}-${offerId}`;
const randomKey = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;

function OfferHistory({ history, t, money }) {
  if (!history) return null;
  if (history.loading) return <p className="offer-history" role="status">{t('loading')}</p>;
  if (history.error) return <p className="offer-history">{t('server')}</p>;
  return (
    <div className="offer-history" aria-live="polite">
      {history.data.map((step) => (
        <p key={step.id}>
          {t(`status_${step.status}`, step.status)} · {step.quantity} {t(step.unit || 'quintal')} · {money(step.price_per_unit)} / {t(step.unit || 'quintal')}
        </p>
      ))}
    </div>
  );
}

export default function OffersPage() {
  const { user } = useAuth();
  const { t, cropT, money, language } = useLanguage();
  const [params] = useSearchParams();
  const offers = useResource(getOffers, [user.id]);
  const [confirm, setConfirm] = useState(null);
  const [countering, setCountering] = useState(null);
  const [counterPrice, setCounterPrice] = useState('');
  const [counterQuantity, setCounterQuantity] = useState('');
  const [declineReason, setDeclineReason] = useState('');
  const [sort, setSort] = useState('expiry');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [acceptedOfferToFocus, setAcceptedOfferToFocus] = useState(null);
  const [histories, setHistories] = useState({});
  const [now, setNow] = useState(Date.now());
  const dialogRef = useRef(null);
  const dialogOpener = useRef(null);
  const actionStatusRef = useRef(null);
  const fallbackKeys = useRef({});
  const highlighted = params.get('offer_id');
  const selectedLot = params.get('lot_id');
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (confirm && dialog && !dialog.open) dialog.showModal();
    if (!confirm && dialog?.open) dialog.close();
  }, [confirm]);
  useEffect(() => {
    if (!acceptedOfferToFocus || !offers.data.some((offer) => offer.id === acceptedOfferToFocus && offer.status === 'ACCEPTED')) return;
    requestAnimationFrame(() => actionStatusRef.current?.focus());
    setAcceptedOfferToFocus(null);
  }, [acceptedOfferToFocus, offers.data]);

  function actionKey(name) {
    try {
      const stored = localStorage.getItem(name);
      if (stored) return stored;
      const created = randomKey();
      localStorage.setItem(name, created);
      return created;
    } catch {
      fallbackKeys.current[name] ||= randomKey();
      return fallbackKeys.current[name];
    }
  }

  function clearActionKey(name) {
    delete fallbackKeys.current[name];
    try { localStorage.removeItem(name); } catch { /* The in-memory key is cleared either way. */ }
  }

  function openConfirmation(offer, action, event) {
    dialogOpener.current = event.currentTarget;
    setConfirm({ offer, action });
    if (action === 'decline') setDeclineReason('');
  }
  const lotGroups = useMemo(() => {
    const groups = new Map();
    offers.data.filter((offer) => !selectedLot || offer.lot_id === selectedLot).forEach((offer) => {
      const key = offer.lot_id || 'unknown';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(offer);
    });
    return [...groups.entries()].map(([lotId, entries]) => {
      const items = [...entries].sort((a, b) => sort === 'newest'
        ? (Date.parse(b.created_at || '') || 0) - (Date.parse(a.created_at || '') || 0)
        : (Date.parse(a.expires_at || '') || Infinity) - (Date.parse(b.expires_at || '') || Infinity));
      return [lotId, items];
    });
  }, [offers.data, selectedLot, sort]);

  async function updateOffer() {
    if (!confirm || busy) return;
    setBusy(true);
    setError('');
    const name = idempotencyName(user.id, confirm.offer.id, 'accept');
    const key = actionKey(name);
    const result = await acceptOffer(confirm.offer.id, key);
    setBusy(false);
    if (result.success) {
      clearActionKey(name);
      setMessage('accepted');
      setAcceptedOfferToFocus(confirm.offer.id);
      setConfirm(null);
      offers.retry();
    } else setError(result.error || 'server');
  }

  async function decline() {
    if (!confirm || busy) return;
    setBusy(true);
    setError('');
    const name = idempotencyName(user.id, confirm.offer.id, 'decline');
    const result = await rejectOffer(confirm.offer.id, declineReason || undefined, actionKey(name));
    setBusy(false);
    if (result.success) {
      setMessage('declined');
      clearActionKey(name);
      setConfirm(null);
      setDeclineReason('');
      offers.retry();
    } else setError(result.error || 'server');
  }

  async function sendCounter(event) {
    event.preventDefault();
    if (!countering || busy) return;
    setBusy(true);
    setError('');
    const name = idempotencyName(user.id, countering.id, 'counter');
    const key = actionKey(name);
    const result = await counterOffer(countering.id, {
      ...(counterQuantity ? { quantity: counterQuantity } : {}),
      ...(counterPrice ? { price_per_unit: counterPrice } : {}),
      unit: 'quintal',
    }, key);
    setBusy(false);
    if (result.success) {
      clearActionKey(name);
      setMessage('counterSent');
      setCountering(null);
      offers.retry();
    } else setError(result.error || 'server');
  }

  async function toggleHistory(offerId) {
    if (histories[offerId]) {
      setHistories((items) => ({ ...items, [offerId]: null }));
      return;
    }
    setHistories((items) => ({ ...items, [offerId]: { loading: true, data: [] } }));
    const result = await getOfferHistory(offerId);
    setHistories((items) => ({ ...items, [offerId]: result.success ? { data: result.data } : { error: result.error, data: [] } }));
  }

  return (
    <>
      <PageHeading title={t('offers')} description={t('farmerOffersIntro')} action={<button className="button secondary" onClick={offers.retry}>{t('refresh')}</button>} />
      {message && <div ref={actionStatusRef} id="offer-action-status" tabIndex={-1}><Notice>{t(message)} <Link className="text-link" to="/transactions">{t('orders')}</Link></Notice></div>}
      {error && <Notice error>{t(error)}</Notice>}
      {countering && <section className="panel form-stack farmer-counter-panel" aria-labelledby="counter-title">
        <h2 id="counter-title">{t('sendCounter')}</h2>
        <p>{cropT(countering.crop_name)} · {countering.quantity} {t('quintal')} × {money(countering.price_per_unit)} / {t('quintal')}</p>
        <form className="form-stack" onSubmit={sendCounter}>
          <Field label={`${t('counterPrice')} / ${t('quintal')}`} type="number" min="0.01" step="0.01" inputMode="decimal" value={counterPrice} onChange={(event) => setCounterPrice(event.target.value)} required />
          <Field label={`${t('counterQuantity')} (${t('optional')})`} type="number" min="0.01" step="0.01" inputMode="decimal" value={counterQuantity} onChange={(event) => setCounterQuantity(event.target.value)} />
          <div className="form-actions"><button type="button" className="button secondary" onClick={() => setCountering(null)} disabled={busy}>{t('cancel')}</button><button className="button" disabled={busy}>{t(busy ? 'loading' : 'sendCounter')}</button></div>
        </form>
      </section>}
      <dialog ref={dialogRef} className="offer-dialog" aria-labelledby="offer-confirm-title" onCancel={() => setConfirm(null)} onClose={() => { setConfirm(null); requestAnimationFrame(() => dialogOpener.current?.focus()); }}>
        {confirm && <>
        <h2 id="offer-confirm-title">{t(confirm.action === 'accept' ? 'confirmAccept' : 'declineOffer')}</h2>
        <dl className="review-list">
          <div><dt>{user.role === 'buyer' ? t('seller') : t('buyer')}</dt><dd>{user.role === 'buyer' ? confirm.offer.seller_label : confirm.offer.buyer_name}</dd></div>
          {user.role !== 'buyer' && <div><dt>{t('verification')}</dt><dd>{t(`verification_${String(confirm.offer.buyer_verification_status || 'UNVERIFIED').toLowerCase()}`)}</dd></div>}
          <div><dt>{t('crop')}</dt><dd>{cropT(confirm.offer.crop_name)}</dd></div>
          <div><dt>{t('quantity')}</dt><dd>{confirm.offer.quantity} {t(confirm.offer.unit || 'quintal')}</dd></div>
          <div><dt>{t('offerPrice')}</dt><dd>{money(confirm.offer.price_per_unit)} / {t(confirm.offer.unit || 'quintal')}</dd></div>
          <div><dt>{t('offerGross')}</dt><dd>{money(confirm.offer.total_value)}</dd></div>
          {confirm.offer.expires_at && <div><dt>{t('expires')}</dt><dd>{dateLabel(confirm.offer.expires_at, language)} {new Date(confirm.offer.expires_at).toLocaleTimeString()}</dd></div>}
          {confirm.offer.message && <div><dt>{t('buyerMessage')}</dt><dd>{confirm.offer.message}</dd></div>}
        </dl>
        <p className="field-hint">{t('acceptTermsHelp')}</p>
        {confirm.action === 'decline' && <label className="field"><span>{t('declineReason')}</span><select value={declineReason} onChange={(event) => setDeclineReason(event.target.value)}><option value="">{t('optional')}</option>{['price', 'quantity', 'timing', 'quality', 'other'].map((reason) => <option key={reason} value={reason}>{t(`reason_${reason}`)}</option>)}</select></label>}
        <div className="form-actions"><button autoFocus className="button secondary" disabled={busy} onClick={() => dialogRef.current?.close()}>{t('cancel')}</button><button className="button" disabled={busy} onClick={confirm.action === 'accept' ? updateOffer : decline}>{t(busy ? 'loading' : confirm.action === 'accept' ? 'accept' : 'decline')}</button></div>
        </>}
      </dialog>
      <div className="offer-sort-row"><label htmlFor="offer-sort">{t('sortOffers')}</label><select id="offer-sort" value={sort} onChange={(event) => setSort(event.target.value)}><option value="expiry">{t('soonestExpiry')}</option><option value="newest">{t('newestFirst')}</option></select></div>
      <DataState loading={offers.loading} error={offers.error} empty={!offers.data.length || !lotGroups.length ? t('noOffers') : false} onRetry={offers.retry}>
        <div className="offer-groups">{lotGroups.map(([lotId, items]) => <section className="offer-group" key={lotId} aria-labelledby={`lot-${lotId}`}>
          <div className="section-heading"><h2 id={`lot-${lotId}`}>{cropT(items[0].crop_name)} · {items[0].location || t('locationNotSet')}</h2><span>{items.length} {t('offers')}</span></div>
          {items.map((offer) => {
            const expired = offer.expires_at && Date.parse(offer.expires_at) <= now;
            const pending = offer.status === 'PENDING' && !expired;
            const statusKey = expired ? 'status_EXPIRED' : `status_${offer.status}`;
            const statusFallback = expired ? 'EXPIRED' : offer.status;
            const verificationKey = `verification_${String(offer.buyer_verification_status || 'UNVERIFIED').toLowerCase()}`;
            return <article className={`panel farmer-offer-card ${highlighted === offer.id ? 'offer-highlight' : ''}`} id={`offer-${offer.id}`} key={offer.id}>
              <div className="farmer-offer-heading"><div><span className="status-pill">{t(statusKey, statusFallback)}</span><h3>{user.role === 'buyer' ? offer.seller_label : offer.buyer_name}</h3>{user.role !== 'buyer' && <p>{t(verificationKey)}</p>}</div><strong className="amount">{money(offer.total_value)}</strong></div>
              <div className="farmer-offer-terms"><p><strong>{offer.quantity} {t(offer.unit || 'quintal')}</strong></p><p>{money(offer.price_per_unit)} / {t(offer.unit || 'quintal')}</p><p>{t('offerGross')}</p></div>
              {offer.expires_at && <p className="offer-expiry"><Clock3 size={16} aria-hidden="true" />{t(expired ? 'offerExpired' : 'expires')}: {dateLabel(offer.expires_at, language)} {new Date(offer.expires_at).toLocaleTimeString()}</p>}
              {offer.message && <p className="farmer-offer-message">{offer.message}</p>}
              <button className="text-link" type="button" onClick={() => toggleHistory(offer.id)}>{t(histories[offer.id] ? 'hideHistory' : 'viewNegotiationHistory')}</button>
              <OfferHistory history={histories[offer.id]} t={t} money={money} />
              {pending && user.role !== 'buyer' && <div className="form-actions farmer-offer-actions"><button className="button secondary" onClick={(event) => openConfirmation(offer, 'decline', event)}>{t('decline')}</button><button className="button secondary" onClick={() => { setCountering(offer); setCounterPrice(String(offer.price_per_unit)); setCounterQuantity(String(offer.quantity)); }}>{t('counter')}</button><button className="button" onClick={(event) => openConfirmation(offer, 'accept', event)}>{t('accept')}</button></div>}
              {pending && user.role === 'buyer' && <div className="form-actions farmer-offer-actions">{offer.parent_offer_id && <><button className="button secondary" onClick={(event) => openConfirmation(offer, 'decline', event)}>{t('decline')}</button><button className="button secondary" onClick={() => { setCountering(offer); setCounterPrice(String(offer.price_per_unit)); setCounterQuantity(String(offer.quantity)); }}>{t('counter')}</button><button className="button" onClick={(event) => openConfirmation(offer, 'accept', event)}>{t('accept')}</button></>}<button className="button secondary" onClick={async () => { await withdrawOffer(offer.id, actionKey('withdraw')); offers.retry(); }}>{t('withdrawOffer')}</button></div>}
              {offer.status === 'ACCEPTED' && <Link className="button secondary" to={offer.transaction_id ? `/trades/${offer.transaction_id}` : '/transactions'}>{t(offer.transaction_id ? 'openTrade' : 'viewTradeRecords')}<ArrowRight size={17} /></Link>}
            </article>;
          })}
        </section>)}</div>
      </DataState>
    </>
  );
}
