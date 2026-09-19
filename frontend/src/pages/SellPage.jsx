import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Minus, Plus } from 'lucide-react';
import { getCrops, getLivePrices, getMyProfile, quoteLot, createLot } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { Field, Notice, DataState, PageHeading, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
import { savedSnapshotLabel } from '../lib/offlinePresentation';
import { enqueueLotCreate } from '../lib/offlineStore';
import { DictationButton } from '../components/VoiceControls';

const randomKey = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const safeRead = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch { return fallback; }
};

export default function SellPage() {
  const { user } = useAuth();
  const { t, money, language } = useLanguage();
  const [params] = useSearchParams();
  const draftKey = `listing-draft-${user.id}`;
  const idempotencyKey = `listing-key-${user.id}`;
  const historyKey = `farmer-last-lot-${user.id}`;
  const initialDraft = useMemo(() => safeRead(draftKey, {}), [draftKey]);
  const previous = useMemo(() => safeRead(historyKey, {}), [historyKey]);
  const [form, setForm] = useState(() => ({
    crop: previous.crop || '',
    variety_id: previous.variety_id || '',
    quantity: previous.quantity || '',
    unit: previous.unit || 'quintal',
    price: previous.price || '',
    grade: previous.grade || '',
    location: '',
    district: '',
    ...initialDraft,
    ...Object.fromEntries(['crop', 'district', 'unit'].filter((key) => params.has(key)).map((key) => [key, params.get(key)])),
  }));
  const [submissionKey] = useState(() => {
    try { return localStorage.getItem(idempotencyKey) || randomKey(); } catch { return randomKey(); }
  });
  const [review, setReview] = useState(false);
  const [offlineReview, setOfflineReview] = useState(false);
  const [quote, setQuote] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState(null);
  const [queued, setQueued] = useState(false);
  const [online, setOnline] = useState(globalThis.navigator?.onLine !== false);
  const crops = useResource(getCrops);
  const profile = useResource(getMyProfile, [user.id]);
  const selectedCrop = crops.data.find((crop) => crop.id === form.crop || crop.name === form.crop);
  const selectedVariety = selectedCrop?.varieties?.find((variety) => variety.id === form.variety_id);
  const district = form.district || profile.data?.district || '';
  const linkedMarket = params.get('market') || '';
  const currentPrice = useResource(
    () => selectedCrop ? getLivePrices({ crop: selectedCrop.name, district, market: linkedMarket, limit: 100 }) : Promise.resolve({ success: true, data: [] }),
    [selectedCrop?.id, district, linkedMarket],
  );
  const officialPrice = currentPrice.data.find((item) => item.unit === 'INR/quintal');
  const validUnits = (selectedCrop?.valid_units || (selectedCrop?.default_unit ? [selectedCrop.default_unit] : ['quintal']))
    .filter((unit) => ['quintal', 'kg', 'tonne'].includes(unit));

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  useEffect(() => {
    try { localStorage.setItem(draftKey, JSON.stringify(form)); } catch { /* Keep the draft in memory if storage is unavailable. */ }
  }, [draftKey, form]);
  useEffect(() => {
    try { localStorage.setItem(idempotencyKey, submissionKey); } catch { /* The API remains authoritative. */ }
  }, [idempotencyKey, submissionKey]);
  useEffect(() => {
    if (!form.location && profile.data?.location) setForm((value) => ({ ...value, location: profile.data.location }));
    else if (!form.location && profile.data?.district) setForm((value) => ({ ...value, location: profile.data.district }));
    if (!form.district && profile.data?.district) setForm((value) => ({ ...value, district: profile.data.district }));
  }, [form.location, form.district, profile.data?.location, profile.data?.district]);
  useEffect(() => {
    if (form.crop || Object.keys(initialDraft).length || previous.crop || !crops.data.length) return;
    const favorites = safeRead(`farmer-crops-${user.id}`, []);
    const favorite = crops.data.find((crop) => favorites.includes(crop.id));
    if (favorite) setForm((value) => ({ ...value, crop: favorite.id, unit: favorite.default_unit || 'quintal' }));
  }, [crops.data, form.crop, initialDraft, previous.crop, user.id]);
  useEffect(() => {
    if (selectedCrop && !validUnits.includes(form.unit)) {
      setForm((value) => ({ ...value, unit: selectedCrop.default_unit || validUnits[0] || 'quintal' }));
    }
  }, [selectedCrop?.id, form.unit, validUnits]);

  const cropName = (crop) => !crop ? '' : language === 'hi' ? crop.name_hindi || crop.name : language === 'mr' ? crop.name_marathi || crop.name : crop.name_en || crop.name;
  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
    setError('');
    setQuote(null);
    setOfflineReview(false);
  }
  function chooseCrop(id) {
    const crop = crops.data.find((item) => item.id === id);
    const last = safeRead(historyKey, {});
    const matches = last.crop === id;
    const defaultUnit = crop?.default_unit || crop?.valid_units?.[0] || 'quintal';
    setForm((current) => ({
      ...current,
      crop: id,
      variety_id: matches && crop?.varieties?.some((variety) => variety.id === last.variety_id) ? last.variety_id : '',
      quantity: matches ? last.quantity : '',
      unit: matches && crop?.valid_units?.includes(last.unit) ? last.unit : defaultUnit,
      price: matches ? last.price : '',
      grade: matches ? last.grade : '',
    }));
    setReview(false);
    setQuote(null);
  }
  function adjustQuantity(delta) {
    const current = Number(form.quantity || 0);
    const increments = form.unit === 'kg' ? 100 : form.unit === 'tonne' ? 1 : 10;
    update('quantity', String(Math.max(0, current + delta * increments)));
  }

  async function openReview(event) {
    event.preventDefault();
    setError('');
    if (!selectedCrop || !form.quantity || !form.location.trim()) {
      setError('validation');
      return;
    }
    if (globalThis.navigator?.onLine === false || !online) {
      if (user.role !== 'farmer') {
        setError('connectionRequired');
        return;
      }
      setQuote({ offline_draft: true, entered_quantity: form.quantity, entered_unit: form.unit });
      setOfflineReview(true);
      setReview(true);
      return;
    }
    setBusy(true);
    const result = await quoteLot({
      crop: selectedCrop.id,
      variety_id: form.variety_id || null,
      quantity: form.quantity,
      unit: form.unit,
      asking_price: form.price || null,
      district: district || null,
    });
    setBusy(false);
    if (!result.success) {
      if (!result.status || result.error === 'network' || result.error === 'timeout') {
        setQuote({ offline_draft: true, entered_quantity: form.quantity, entered_unit: form.unit });
        setOfflineReview(true);
        setReview(true);
        return;
      }
      setError(result.error || 'validation');
      return;
    }
    setQuote(result.data);
    setOfflineReview(false);
    setReview(true);
  }

  async function queueForLater() {
    if (!quote || busy || user.role !== 'farmer') return;
    setBusy(true);
    setError('');
    try {
      await enqueueLotCreate({
        ownerId: user.id,
        idempotencyKey: submissionKey,
        payload: {
          crop: selectedCrop.id,
          variety_id: form.variety_id || null,
          quantity: form.quantity,
          unit: form.unit,
          asking_price: form.price || null,
          grade: form.grade || 'UNSPECIFIED',
          location_text: form.location.trim(),
          district: district || null,
        },
      });
      try {
        localStorage.removeItem(draftKey);
        localStorage.removeItem(idempotencyKey);
      } catch { /* The account-scoped IndexedDB entry is authoritative for this saved operation. */ }
      setQueued(true);
    } catch (queueError) {
      setError(queueError.code || 'offlineQueueStorageUnavailable');
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    if (!quote || busy) return;
    if (offlineReview || globalThis.navigator?.onLine === false || !online) {
      await queueForLater();
      return;
    }
    setBusy(true);
    setError('');
    const result = await createLot({
      crop: selectedCrop.id,
      variety_id: form.variety_id || null,
      quantity: form.quantity,
      unit: form.unit,
      asking_price: form.price || null,
      grade: form.grade || 'UNSPECIFIED',
      location_text: form.location.trim(),
      district: district || null,
    }, submissionKey);
    setBusy(false);
    if (!result.success) {
      setError(result.error || 'server');
      return;
    }
    const lot = result.data;
    setCreated(lot);
    try {
      localStorage.removeItem(draftKey);
      localStorage.removeItem(idempotencyKey);
      localStorage.setItem(historyKey, JSON.stringify({
        crop: selectedCrop.id,
        variety_id: form.variety_id,
        quantity: form.quantity,
        unit: form.unit,
        price: form.price,
        grade: form.grade,
      }));
    } catch { /* Submission is already saved on the server. */ }
  }

  if (queued) return (
    <div className="narrow success-page panel">
      <CheckCircle2 size={52} aria-hidden="true" />
      <h1>{t('offlineListingQueued')}</h1>
      <p>{t('offlineListingQueuedDetail')}</p>
      <p>{cropName(selectedCrop)} · {form.quantity} {t(form.unit)}</p>
      <p className="field-hint">{t('offlineQueueTruth')}</p>
      <Link className="button" to="/farmer/more">{t('offlineQueueTitle')}<ArrowRight size={19} /></Link>
      <Link className="text-link" to="/farmer/dashboard">{t('dashboard')}</Link>
    </div>
  );

  if (created) return (
    <div className="narrow success-page panel">
      <CheckCircle2 size={52} aria-hidden="true" />
      <h1>{t('published')}</h1>
      <p>{cropName(selectedCrop)} · {created.original_quantity || created.quantity} {t(created.original_unit || created.unit || 'quintal')}</p>
      <p className="muted">{created.public_id}</p>
      <Link className="button" to={`/offers?lot_id=${created.id}`}>{t('viewOffers')}<ArrowRight size={19} /></Link>
      <Link className="text-link" to="/farmer/dashboard">{t('dashboard')}</Link>
    </div>
  );

  return (
    <div className="narrow farmer-sell-page">
      <PageHeading title={t('sellProduce')} description={t('sellIntro')} />
      {params.has('price') && <Notice>{t('marketPriceContextOnly')}</Notice>}
      <DataState loading={crops.loading} error={crops.error} empty={!crops.loading && !crops.error && !crops.data.length ? t('cropRegistryEmpty') : false} onRetry={crops.retry}>
        <form className="panel form-stack" onSubmit={review ? (event) => { event.preventDefault(); publish(); } : openReview}>
          {review && quote ? (
            <>
              <h2>{t('reviewListing')}</h2>
              {(offlineReview || !online) && <Notice>{t('offlineReviewPending')}</Notice>}
              <dl className="review-list">
                <div><dt>{t('crop')}</dt><dd>{cropName(selectedCrop)}</dd></div>
                {selectedVariety && <div><dt>{t('variety')}</dt><dd>{language === 'hi' ? selectedVariety.name_hindi || selectedVariety.name : language === 'mr' ? selectedVariety.name_marathi || selectedVariety.name : selectedVariety.name}</dd></div>}
                <div><dt>{t('quantity')}</dt><dd>{quote.entered_quantity} {t(quote.entered_unit)}</dd></div>
                <div><dt>{t('askingPricePerQtl')}</dt><dd>{form.price ? `${money(form.price)} / ${t('quintal')}` : t('buyerOfferMayVary')}</dd></div>
                <div><dt>{t('grade')}</dt><dd>{t(form.grade ? `grade_${form.grade}` : 'grade_UNSPECIFIED')}</dd></div>
                {!(offlineReview || !online) && quote.indicative_gross && <div><dt>{t('indicativeGross')}</dt><dd>{money(quote.indicative_gross)}</dd></div>}
                <div><dt>{t('location')}</dt><dd>{form.location}{district ? ` · ${district}` : ''}</dd></div>
                <div><dt>{t('available')}</dt><dd>{t('availableToday')}</dd></div>
              </dl>
              {!(offlineReview || !online) && quote.price_warning && <Notice error>{t('priceSanityWarning').replace('{price}', money(quote.reference_price.modal_price)).replace('{market}', quote.reference_price.market)} ({t('priceWarningThreshold').replace('{pct}', quote.warning_threshold_pct)}).</Notice>}
              {!(offlineReview || !online) && quote.reference_price && <p className="field-hint">{t('latestReportedRate')}: {money(quote.reference_price.modal_price)} / {t('quintal')} · {quote.reference_price.market} · {dateLabel(quote.reference_price.price_date, language)} · {quote.reference_price.source}</p>}
              <p className="field-hint">{t('indicativeGrossNote')}</p>
            </>
          ) : (
            <>
              <Field as="select" label={t('crop')} required value={form.crop} onChange={(event) => chooseCrop(event.target.value)}>
                <option value="">{t('chooseCrop')}</option>
                {crops.data.map((crop) => <option key={crop.id} value={crop.id}>{cropName(crop)}</option>)}
              </Field>
              {selectedCrop?.varieties?.length > 0 && <Field as="select" label={`${t('variety')} (${t('optional')})`} value={form.variety_id} onChange={(event) => update('variety_id', event.target.value)}>
                <option value="">{t('grade_UNSPECIFIED')}</option>
                {selectedCrop.varieties.map((variety) => <option key={variety.id} value={variety.id}>{language === 'hi' ? variety.name_hindi || variety.name : language === 'mr' ? variety.name_marathi || variety.name : variety.name}</option>)}
              </Field>}
              {selectedCrop && (
                <>
                  <div className="quantity-control">
                    <span className="quantity-label">{t('quantity')}</span>
                    <div className="quantity-input-row">
                      <button className="icon-button quantity-step" type="button" aria-label={t('reduceQuantity')} onClick={() => adjustQuantity(-1)}><Minus size={20} /></button>
                      <Field label={t('quantity')} className="quantity-number" type="number" inputMode="decimal" min="0.01" max="100000000" step={form.unit === 'kg' ? '1' : form.unit === 'tonne' ? '0.001' : '0.01'} value={form.quantity} onChange={(event) => update('quantity', event.target.value)} />
                      <button className="icon-button quantity-step" type="button" aria-label={t('increaseQuantity')} onClick={() => adjustQuantity(1)}><Plus size={20} /></button>
                      <Field as="select" label={t('unit')} value={form.unit} onChange={(event) => update('unit', event.target.value)}>
                        {validUnits.map((unit) => <option key={unit} value={unit}>{t(unit)}</option>)}
                      </Field>
                    </div>
                  </div>
                  <Field label={`${t('askingPricePerQtl')} (${t('optional')})`} type="number" inputMode="decimal" min="0.01" max="10000000" step="0.01" value={form.price} onChange={(event) => update('price', event.target.value)} hint={t('askingPriceHelp')} />
                  {currentPrice.loading ? <p role="status" className="field-hint">{t('loading')}</p> : currentPrice.error ? <p className="field-hint">{t('priceLoadFailed')}</p> : officialPrice ? (
                    <div className="reported-rate-context"><strong>{t('latestReportedRate')}: {money(officialPrice.modal_price)} / {t('quintal')}</strong><span>{officialPrice.market} · {dateLabel(officialPrice.price_date, language)} · {officialPrice.source} · {t(officialPrice.freshness_state || 'priceFreshnessUnknown')}</span><button className="text-link" type="button" onClick={() => update('price', officialPrice.modal_price)}>{t('useThisPrice')}</button></div>
                  ) : <p className="field-hint">{t('noComparablePrice')}</p>}
                  {currentPrice.offline_cache && <p className="offline-cache-note" role="status">{savedSnapshotLabel(t, currentPrice.cached_at, language)}</p>}
                  <Field as="select" label={t('grade')} value={form.grade} onChange={(event) => update('grade', event.target.value)}>
                    <option value="">{t('grade_UNSPECIFIED')}</option>
                    {['A', 'B', 'C'].map((grade) => <option key={grade} value={grade}>{t(`grade_${grade}`)}</option>)}
                  </Field>
                  <Field label={t('location')} required minLength={2} maxLength={300} autoComplete="address-line1" value={form.location} onChange={(event) => update('location', event.target.value)} hint={t('locationListingHelp')} />
                  <DictationButton onTranscript={(text) => update('location', text)} />
                  {error && <Notice error>{t(error)}</Notice>}
                  <button className="button wide button-large" type="submit" disabled={busy}>{t(busy ? 'loading' : 'reviewListing')}<ArrowRight size={19} /></button>
                  <p className="field-hint">{t('draftSaved')}</p>
                </>
              )}
            </>
          )}
          {review && <>
            {error && <Notice error>{t(error)}</Notice>}
            <div className="form-actions"><button type="button" className="button secondary" disabled={busy} onClick={() => { setReview(false); setOfflineReview(false); }}>{t('edit')}</button><button className="button" type="submit" disabled={busy || (!online && user.role !== 'farmer')}>{t(busy ? 'loading' : offlineReview || !online ? 'offlineQueueSave' : 'publish')}</button></div>
            {review && quote && !offlineReview && (error === 'network' || error === 'timeout') && <button type="button" className="text-link" disabled={busy} onClick={queueForLater}>{t('offlineQueueSave')}</button>}
          </>}
        </form>
      </DataState>
    </div>
  );
}
