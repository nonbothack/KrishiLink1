import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { MapPin, ArrowUpRight, RefreshCw } from 'lucide-react';
import { getCrops, getReportedPrices } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { Field, DataState, useResource } from './Experience';
import { dateLabel } from '../lib/produce';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { savedSnapshotLabel } from '../lib/offlinePresentation';
export default function RateLookup({ compact = false }) {
  const { t, cropT, money, language } = useLanguage();
  const snapshot = getPublicSnapshot();
  const [params, setParams] = useSearchParams();
  const [choice, setChoice] = useState(() => {
    if (compact && snapshot?.path === '/' && snapshot?.selectedCrop) {
      return { crop: snapshot.selectedCrop, district: '' };
    }
    try {
      return (
        JSON.parse(localStorage.getItem('krishilink_price_choice')) || {
          crop: '',
          district: '',
        }
      );
    } catch {
      return { crop: '', district: '' };
    }
  });
  useEffect(() => {
    if (!compact || snapshot?.path !== '/') return;
    try {
      const saved = JSON.parse(localStorage.getItem('krishilink_price_choice'));
      if (saved && typeof saved === 'object') {
        setChoice((current) => ({
          crop: cropRegistry.data.some((item) => item.name === saved.crop) ? saved.crop : current.crop,
          district: typeof saved.district === 'string' ? saved.district : current.district,
        }));
      }
    } catch {
      // The public page keeps its server-selected crop when storage is unavailable.
    }
  }, [compact, snapshot?.path]);
  const cropRegistry = useResource(
    getCrops,
    [],
    snapshot?.crops
      ? { data: snapshot.crops, total: snapshot.crops.length, pages: 1, provenance: 'build-snapshot', error: snapshot.cropStatus === 'error' ? 'network' : null }
      : null,
  );
  const requestedCrop = compact ? choice.crop : params.get('crop') || '';
  const selectedCrop = requestedCrop
    ? cropRegistry.data.find((item) =>
        [item.name, item.slug, ...(item.aliases || [])].some(
          (name) => String(name).toLocaleLowerCase() === requestedCrop.toLocaleLowerCase(),
        ),
      )
    : cropRegistry.data[0];
  const resolvedCrop = selectedCrop?.name || '';
  const unavailableCrop = Boolean(requestedCrop && cropRegistry.data.length && !selectedCrop);
  const district = compact ? choice.district : params.get('district') || '';
  const market = compact ? '' : params.get('market') || '';
  const state = compact ? '' : params.get('state') || '';
  const page = compact ? 1 : Math.max(1, Number(params.get('page')) || 1);
  const [draftDistrict, setDraftDistrict] = useState(district);
  useEffect(() => {
    setDraftDistrict(district);
  }, [district]);
  const resource = useResource(
    () =>
      resolvedCrop && !unavailableCrop
        ? getReportedPrices({ crop: resolvedCrop, district, market, state, page, limit: compact ? 3 : 12 })
        : Promise.resolve({ success: true, data: [] }),
    [resolvedCrop, unavailableCrop, district, market, state, page, compact],
    snapshot?.priceCrop === resolvedCrop && snapshot?.prices
      ? {
          data: snapshot.prices.items || [],
          total: snapshot.prices.total || snapshot.prices.items?.length || 0,
          pages: snapshot.prices.pages || 1,
          provenance: 'build-snapshot',
          error: snapshot.priceStatus === 'error' ? 'network' : null,
        }
      : null,
  );
  function update(values) {
    if (compact) {
      const next = { ...choice, ...values };
      setChoice(next);
      localStorage.setItem('krishilink_price_choice', JSON.stringify(next));
    } else {
      const next = new URLSearchParams(params);
      Object.entries(values).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
      next.delete('page');
      setParams(next);
    }
  }
  return (
    <div className="rate-lookup">
      <form
        className="rate-filters"
        onSubmit={(e) => {
          e.preventDefault();
          update({ district: draftDistrict.trim() });
        }}
      >
        <Field
          label={t('crop')}
          as="select"
          value={resolvedCrop}
          disabled={cropRegistry.loading || Boolean(cropRegistry.error) || !cropRegistry.data.length}
          onChange={(e) => update({ crop: e.target.value })}
        >
          <option value="">{t('crop')}</option>
          {cropRegistry.data.map((item) => (
            <option key={item.id} value={item.name}>
              {language === 'hi' ? item.name_hindi || cropT(item.name) : language === 'mr' ? item.name_marathi || cropT(item.name) : item.name_en || item.name}
            </option>
          ))}
        </Field>
        <Field
          label={t('district')}
          value={draftDistrict}
          onChange={(e) => setDraftDistrict(e.target.value)}
          placeholder={t('all')}
          autoComplete="address-level2"
        />
        <button className="button" type="submit">
          {t('search')}
          <ArrowUpRight size={18} />
        </button>
        <button
          className="icon-button"
          type="button"
          aria-label={t('refresh')}
          onClick={resource.retry}
        >
          <RefreshCw size={20} />
        </button>
      </form>
      {(cropRegistry.offline_cache || resource.offline_cache) && (
        <p className="offline-cache-note" role="status">
          {savedSnapshotLabel(t, resource.cached_at || cropRegistry.cached_at, language)}
        </p>
      )}
      <DataState
        loading={cropRegistry.loading || resource.loading}
        error={cropRegistry.error || resource.error}
        empty={
          unavailableCrop
            ? t('cropUnavailable')
            : !cropRegistry.loading && !cropRegistry.error && !cropRegistry.data.length
              ? t('cropRegistryEmpty')
              : resource.data.length === 0
                ? t('rateEmpty')
                : false
        }
        onRetry={cropRegistry.error ? cropRegistry.retry : resource.retry}
      >
        <div className="price-grid">
          {resource.data.map((p, i) => (
            <article className={`price-result ${p.freshness_state === 'stale' ? 'price-result-stale' : ''}`} key={p.id || i}>
              <div className="price-top">
                <span className="crop-dot" />
                <strong>{cropT(p.crop || p.commodity)}</strong>
              </div>
              <div className="price-number">
                {p.modal_price != null ? money(p.modal_price) : '—'}
              </div>
              <p className="unit-label">
                {p.unit === 'INR/quintal' ? t('perQuintal') : p.unit === 'INR/number' ? t('perNumber') : t('unitUnavailable')}
              </p>
              <p className="market-line">
                <MapPin size={16} />
                {p.market}
                {p.district ? ' · ' + p.district : ''}
              </p>
              <p className="date-line">
                {t('reportedOn')}:{' '}
                {dateLabel(p.price_date || p.arrival_date, language) || t('noDate')}
              </p>
              {p.freshness_state && p.freshness_state !== 'reported_today' && (
                <p className={`price-freshness ${p.freshness_state === 'stale' ? 'text-warning' : ''}`}>
                  {t(p.freshness_state === 'stale' ? 'staleReportedPrice' : p.freshness_state)}
                </p>
              )}
              <p className="price-source">{t('sourceLabel')}: {p.source || 'AGMARKNET'}</p>
              {p.location_verified === false && <p className="price-source">{t('locationUnverified')}</p>}
              {p.unit === 'INR/quintal' && (
                <Link
                  className="text-link"
                  to={
                    '/sell?' +
                    new URLSearchParams({
                      crop: p.crop || p.commodity,
                      price: p.modal_price || '',
                      market: p.market || '',
                      district: p.district || '',
                      unit: 'quintal',
                    })
                  }
                >
                  {t('listCrop')}
                  <ArrowUpRight size={18} />
                </Link>
              )}
            </article>
          ))}
        </div>
      </DataState>
      <p className="rate-disclaimer">{t('referenceOnly')}</p>
      {!compact && resource.pages > 1 && (
        <div className="pagination">
          <button
            className="button secondary"
            disabled={page <= 1}
            onClick={() => {
              const n = new URLSearchParams(params);
              n.set('page', page - 1);
              setParams(n);
            }}
          >
            {t('previous')}
          </button>
          <span>
            {page} / {resource.pages}
          </span>
          <button
            className="button secondary"
            disabled={page >= resource.pages}
            onClick={() => {
              const n = new URLSearchParams(params);
              n.set('page', page + 1);
              setParams(n);
            }}
          >
            {t('next')}
          </button>
        </div>
      )}
    </div>
  );
}
