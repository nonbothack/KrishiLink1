import { lazy, Suspense, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, MapPin } from 'lucide-react';
import { DataState, Field, PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { useResource } from '../components/Experience';
import { getMarkets } from '../services/api';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { usePageMetadata } from '../lib/metadata';

const PublicMarketsMap = lazy(() => import('../components/PublicMarketsMap'));

export default function MapPage() {
  const { t } = useLanguage();
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get('search') || '');
  const [mapReady, setMapReady] = useState(false);
  useEffect(() => setMapReady(true), []);
  const snapshot = getPublicSnapshot();
  const markets = useResource(
    () => getMarkets({ search: params.get('search') || '', limit: 100 }),
    [params.get('search')],
    snapshot?.path === '/map' && snapshot.markets
      ? { data: snapshot.markets.items || [], total: snapshot.markets.total || 0, pages: snapshot.markets.pages || 1, error: snapshot.marketsStatus === 'error' ? 'network' : null }
      : null,
  );
  const located = markets.data.filter((market) => Number.isFinite(market.latitude) && Number.isFinite(market.longitude));
  usePageMetadata({ title: 'Reviewed agricultural markets on the map | KrishiLink', description: 'View public agricultural market records that meet the current outlet and location review checks. Buyer and member locations are not shown.', path: '/map', noindex: !markets.loading && markets.data.length === 0 });
  return (
    <div className="site-container page-section public-directory">
      <PageHeading title={t('map')} description={t('publicDirectoryIntro')} />
      <form className="public-search-form" onSubmit={(event) => { event.preventDefault(); const next = new URLSearchParams(params); if (search.trim()) next.set('search', search.trim()); else next.delete('search'); setParams(next); }}>
        <Field label={t('publicSearchOutlet')} type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
        <button className="button" type="submit">{t('search')}</button>
      </form>
      {mapReady && located.length > 0 && (
        <Suspense fallback={<div className="map-preview map-loading" role="status">{t('loading')}</div>}>
          <PublicMarketsMap markets={located} ariaLabel={t('publicMapLabel')} />
        </Suspense>
      )}
      <DataState loading={markets.loading} error={markets.error} empty={!markets.data.length && !markets.loading && !markets.error ? t('publicNoOutlets') : false} onRetry={markets.retry}>
        <div className="card-grid map-card-list">
          {markets.data.map((market) => (
            <article className="panel public-outlet-card" key={market.id}>
              <h2>{market.name}</h2>
              <p className="public-location-line"><MapPin size={16} />{[market.district, market.state].filter(Boolean).join(', ')}</p>
              <p className="public-status-text">{t('publicOutletReviewed')}</p>
              <div className="public-card-actions">
                <Link className="text-link" to={`/mandis/${market.slug}`}>{t('publicViewOutlet')}<ArrowUpRight size={16} /></Link>
                <Link className="text-link" to={'/prices?' + new URLSearchParams({ market: market.name, ...(params.get('crop') ? { crop: params.get('crop') } : {}) })}>{t('checkPrices')}</Link>
              </div>
            </article>
          ))}
        </div>
      </DataState>
    </div>
  );
}
