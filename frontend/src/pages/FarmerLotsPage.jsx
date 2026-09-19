import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { getCrops, getLot, getMyLots, getOffers, getTransactions, updateLot, withdrawLot } from '../services/api';
import { DataState, Field, PageHeading, useResource } from '../components/Experience';

export default function FarmerLotsPage() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const location = useLocation();
  const lots = useResource(getMyLots, [user.id]);
  let hasDraft = false;
  try {
    hasDraft = Boolean(JSON.parse(localStorage.getItem(`listing-draft-${user.id}`) || 'null'));
  } catch {
    hasDraft = false;
  }

  return (
    <div className="farmer-lots-page">
      <PageHeading title={t('myLots')} description={t('myLotsIntro')} action={<Link className="button" to="/sell">{t('sellProduce')}</Link>} />
      {location.state?.notice && <p className="notice" role="status">{t(location.state.notice)}</p>}
      {hasDraft && <article className="panel saved-draft-row"><div><strong>{t('savedListingDraft')}</strong><p>{t('draftSaved')}</p></div><Link className="button secondary" to="/sell">{t('continueDraft')}<ArrowRight size={17} /></Link></article>}
      <DataState loading={lots.loading} error={lots.error} empty={!lots.data.length && !lots.loading ? t('noLots') : false} onRetry={lots.retry}>
        <div className="list-stack">
          {lots.data.map((lot) => (
            <article className="panel listing-row farmer-lot-row" key={lot.id}>
              <div>
                <span className={`status-pill status-pill-${String(lot.status).toLowerCase()}`}>{t(`status_${lot.status}`, lot.status)}</span>
                <h2>{cropT(lot.crop)}</h2>
                <p>{lot.original_quantity || lot.quantity} {t(lot.original_unit || lot.unit || 'quintal')} · {lot.location || t('locationNotSet')}</p>
                {lot.asking_price && <p>{t('askingPricePerQtl')}: {t('rupee')}{lot.asking_price} / {t('quintal')}</p>}
                <small>{lot.public_id}</small>
              </div>
              <Link className="button secondary" to={`/farmer/lots/${lot.id}`}>{t('manageLot')}<ArrowRight size={17} /></Link>
            </article>
          ))}
        </div>
      </DataState>
    </div>
  );
}

export function FarmerLotDetailPage() {
  const { id } = useParams();
  const { t, cropT } = useLanguage();
  const lotResource = useResource(() => getLot(id), [id]);
  const lot = Array.isArray(lotResource.data) ? null : lotResource.data;
  const [editing, setEditing] = useState(false);
  const [confirmWithdraw, setConfirmWithdraw] = useState(false);
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const offers = useResource(() => getOffers({ lot_id: id }), [id]);
  const trades = useResource(getTransactions, [id]);
  const crops = useResource(getCrops);
  const navigate = useNavigate();
  const dialogRef = useRef(null);
  const crop = crops.data.find((item) => item.id === lot?.crop_id);
  const validUnits = (crop?.valid_units || ['quintal']).filter((unit) => ['quintal', 'kg', 'tonne'].includes(unit));
  const relatedTrade = trades.data.find((item) => item.lot_id === id);
  const activeOffer = offers.data.some((offer) => ['PENDING', 'COUNTERED', 'ACCEPTED'].includes(String(offer.status).toUpperCase()));
  const canEdit = lot?.status?.toUpperCase() === 'PUBLISHED'
    && !offers.loading && !offers.error
    && !trades.loading && !trades.error
    && !activeOffer && !relatedTrade;
  const canWithdraw = lot?.status?.toUpperCase() === 'PUBLISHED' && !relatedTrade;

  useEffect(() => {
    if (!confirmWithdraw) return;
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, [confirmWithdraw]);

  useEffect(() => {
    if (!lot || form) return;
    setForm({
      quantity: lot.original_quantity || lot.quantity || '',
      unit: lot.original_unit || lot.unit || 'quintal',
      asking_price: lot.asking_price || '',
      grade: lot.grade || 'UNSPECIFIED',
      location_text: lot.location || '',
    });
  }, [form, lot]);

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
    setError('');
  }

  async function saveChanges(event) {
    event.preventDefault();
    if (!form || busy) return;
    setBusy(true);
    setError('');
    const result = await updateLot(id, {
      quantity: form.quantity,
      unit: form.unit,
      asking_price: form.asking_price || null,
      grade: form.grade,
      location_text: form.location_text,
    });
    setBusy(false);
    if (!result.success) {
      setError(result.error || 'server');
      return;
    }
    setEditing(false);
    setNotice('lotSaved');
    setForm(null);
    lotResource.retry();
  }

  async function withdraw() {
    if (busy) return;
    setBusy(true);
    setError('');
    const result = await withdrawLot(id);
    setBusy(false);
    setConfirmWithdraw(false);
    if (!result.success) {
      setError(result.error || 'server');
      return;
    }
    navigate('/farmer/lots', { replace: true, state: { notice: 'lotWithdrawn' } });
  }

  return (
    <div className="farmer-lot-detail">
      <Link className="text-link" to="/farmer/lots">← {t('myLots')}</Link>
      <DataState loading={lotResource.loading} error={lotResource.error} empty={!lot && !lotResource.loading ? t('lotUnavailable') : false} onRetry={lotResource.retry}>
        {lot && <>
          <PageHeading title={cropT(lot.crop)} eyebrow={lot.public_id} description={`${lot.original_quantity || lot.quantity} ${t(lot.original_unit || lot.unit || 'quintal')} · ${lot.location || t('locationNotSet')}`} action={<span className="status-pill">{t(`status_${lot.status}`, lot.status)}</span>} />
          {notice && <p className="notice" role="status">{t(notice)}</p>}
          {error && <p className="notice notice-error" role="alert">{t(error)}</p>}
          {relatedTrade && <section className="panel lot-related-trade"><h2>{t('activeTrades')}</h2><p>{relatedTrade.public_id || relatedTrade.id} · {t(`status_${relatedTrade.status}`, relatedTrade.status)}</p><Link className="button" to={`/trades/${relatedTrade.id}`}>{t('openTrade')}<ArrowRight size={18} /></Link></section>}
          {offers.data.length > 0 && <section className="panel lot-offers-link"><h2>{t('offers')}</h2><p>{offers.data.length} · {t('farmerOffersIntro')}</p><Link className="button secondary" to={`/offers?lot_id=${id}`}>{t('viewOffers')}<ArrowRight size={18} /></Link></section>}
          {offers.error && <p className="notice notice-error" role="alert">{t('offersLoadFailed')}</p>}
          {canEdit && <section className="panel form-stack">
            <div className="section-heading"><h2>{t('manageLot')}</h2><button type="button" className="text-link" onClick={() => setEditing((value) => !value)}>{t(editing ? 'cancel' : 'editLot')}</button></div>
            {editing && form && <form className="form-stack" onSubmit={saveChanges}>
              <div className="quantity-input-row">
                <Field label={t('quantity')} type="number" min="0.01" step="0.01" value={form.quantity} onChange={(event) => update('quantity', event.target.value)} required />
                <Field as="select" label={t('unit')} value={form.unit} onChange={(event) => update('unit', event.target.value)}>{validUnits.map((unit) => <option key={unit} value={unit}>{t(unit)}</option>)}</Field>
              </div>
              <Field label={t('askingPricePerQtl')} type="number" min="0.01" step="0.01" value={form.asking_price} onChange={(event) => update('asking_price', event.target.value)} hint={t('askingPriceHelp')} />
              <Field as="select" label={t('grade')} value={form.grade} onChange={(event) => update('grade', event.target.value)}>{['UNSPECIFIED', 'A', 'B', 'C'].map((grade) => <option key={grade} value={grade}>{t(`grade_${grade}`)}</option>)}</Field>
              <Field label={t('location')} value={form.location_text} maxLength={300} minLength={2} onChange={(event) => update('location_text', event.target.value)} required />
              <button className="button" disabled={busy}>{t(busy ? 'loading' : 'save')}</button>
            </form>}
            {!editing && <p className="field-hint">{t('lotEditHelp')}</p>}
          </section>}
          {lot.status?.toUpperCase() === 'PUBLISHED' && activeOffer && <p className="notice" role="status">{t('lotEditBlocked')}</p>}
          {canWithdraw && <section className="panel lot-withdraw-panel"><h2>{t('withdrawLot')}</h2><p>{t('withdrawLotHelp')}</p><button className="button button-danger" onClick={() => setConfirmWithdraw(true)}>{t('withdrawLot')}</button></section>}
          <dialog ref={dialogRef} className="confirm-dialog" aria-labelledby="withdraw-title" onCancel={() => setConfirmWithdraw(false)} onClose={() => setConfirmWithdraw(false)}>
            <h2 id="withdraw-title">{t('confirmWithdrawTitle')}</h2><p>{t('confirmWithdrawBody').replace('{count}', String(offers.data.filter((offer) => ['PENDING', 'COUNTERED'].includes(String(offer.status).toUpperCase())).length))}</p>
            <div className="form-actions"><button className="button secondary" type="button" onClick={() => dialogRef.current?.close()} disabled={busy}>{t('cancel')}</button><button className="button button-danger" type="button" onClick={withdraw} disabled={busy}>{t(busy ? 'loading' : 'withdrawLot')}</button></div>
          </dialog>
        </>}
      </DataState>
    </div>
  );
}
