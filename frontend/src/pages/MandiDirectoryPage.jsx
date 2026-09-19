import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, MapPin, Search } from 'lucide-react';
import { DataState, Field, PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { getMarkets } from '../services/api';
import { useResource } from '../components/Experience';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { usePageMetadata } from '../lib/metadata';

export default function MandiDirectoryPage() {
  const { t } = useLanguage();
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get('search') || '');
  const page = Math.max(1, Number(params.get('page')) || 1);
  const snapshot = getPublicSnapshot();
  const markets = useResource(
    () => getMarkets({ search: params.get('search') || '', page, limit: 12 }),
    [params.get('search'), page],
    snapshot?.path === '/mandis' && snapshot.markets
      ? { data: snapshot.markets.items || [], total: snapshot.markets.total || 0, pages: snapshot.markets.pages || 1, error: snapshot.marketsStatus === 'error' ? 'network' : null }
      : null,
  );
  usePageMetadata({ title: 'Agricultural market directory | KrishiLink', description: 'Browse public agricultural outlet records with their district and review status. Price observations are shown separately with their report date and source.', path: '/mandis', noindex: !markets.loading && markets.data.length === 0 });

  function searchMarkets(event) {
    event.preventDefault();
    const next = new URLSearchParams(params);
    if (search.trim()) next.set('search', search.trim());
    else next.delete('search');
    next.delete('page');
    setParams(next);
  }

  return (
    <div className="site-container page-section public-directory">
      <PageHeading eyebrow={t('publicMandis')} title={t('publicDirectoryTitle')} description={t('publicDirectoryIntro')} />
      <form className="public-search-form" onSubmit={searchMarkets}>
        <Field label={t('publicSearchOutlet')} type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
        <button className="button" type="submit"><Search size={18} />{t('search')}</button>
      </form>
      <DataState loading={markets.loading} error={markets.error} empty={!markets.data.length && !markets.loading && !markets.error ? t('publicNoOutlets') : false} onRetry={markets.retry}>
        <div className="card-grid public-outlet-grid">
          {markets.data.map((market) => (
            <article className="panel public-outlet-card" key={market.id}>
              <p className="eyebrow">{market.market_type || t('publicMarketType')}</p>
              <h2>{market.name}</h2>
              <p className="public-location-line"><MapPin size={16} />{[market.district, market.state].filter(Boolean).join(', ') || t('locationNotSet')}</p>
              <p className="public-status-text">{t('publicOutletReviewed')}</p>
              <Link className="text-link" to={`/mandis/${market.slug}`}>{t('publicViewOutlet')}<ArrowUpRight size={17} /></Link>
            </article>
          ))}
        </div>
      </DataState>
      {markets.pages > 1 && (
        <div className="pagination" aria-label={t('pagination')}>
          <button className="button secondary" disabled={page <= 1} onClick={() => { const next = new URLSearchParams(params); next.set('page', String(page - 1)); setParams(next); }}>{t('previous')}</button>
          <span>{page} / {markets.pages}</span>
          <button className="button secondary" disabled={page >= markets.pages} onClick={() => { const next = new URLSearchParams(params); next.set('page', String(page + 1)); setParams(next); }}>{t('next')}</button>
        </div>
      )}
    </div>
  );
}
