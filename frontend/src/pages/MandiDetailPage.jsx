import { ExternalLink, MapPin } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { DataState, PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { useResource } from '../components/Experience';
import { getPublicMarket } from '../services/api';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { usePageMetadata } from '../lib/metadata';

function safeSourceUrl(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.toString() : null;
  } catch {
    return null;
  }
}

export default function MandiDetailPage() {
  const { slug } = useParams();
  const { t, language } = useLanguage();
  const snapshot = getPublicSnapshot();
  const initial = snapshot?.path === `/mandis/${slug}` ? snapshot.market : null;
  const market = useResource(
    () => getPublicMarket(slug).then((result) => ({ success: result.success, data: result.data, error: result.error })),
    [slug],
    initial ? { data: initial } : null,
  );
  const sourceUrl = safeSourceUrl(market.data?.source_url);
  usePageMetadata({
    title: market.data?.name ? `${market.data.name}, ${market.data.district || market.data.state || ''} | KrishiLink` : 'Agricultural outlet details | KrishiLink',
    description: market.data ? `${market.data.name} in ${[market.data.district, market.data.state].filter(Boolean).join(', ')}. View the public outlet record and its review information.` : 'Public agricultural outlet details from the reviewed registry.',
    path: `/mandis/${slug}`,
    noindex: !market.data,
  });

  if (!market.data && market.error === 'notFound') {
    return <div className="site-container page-section"><PageHeading title={t('publicNoOutlets')} /></div>;
  }

  return (
    <div className="site-container narrow page-section public-detail-page">
      <DataState loading={market.loading} error={market.error} empty={false} onRetry={market.retry} errorText={t('publicOutletUnavailable')}>
        {market.data && (
          <>
            <PageHeading eyebrow={t('publicMandis')} title={market.data.name} description={[market.data.district, market.data.state].filter(Boolean).join(', ')} />
            <section className="panel public-detail-card" aria-labelledby="outlet-facts-title">
              <h2 id="outlet-facts-title">{t('publicMarketType')}</h2>
              <p>{market.data.market_type || market.data.outlet_type || t('unitUnavailable')}</p>
              <h2>{t('publicOutletStatus')}</h2>
              <p>{t('publicOutletReviewed')}</p>
              <p className="public-location-line"><MapPin size={17} />{[market.data.district, market.data.state].filter(Boolean).join(', ')}</p>
              <dl className="public-facts-list">
                <div><dt>{t('publicLocationSource')}</dt><dd>{market.data.coordinate_source || t('unitUnavailable')}</dd></div>
                <div><dt>{t('publicCoordinateConfidence')}</dt><dd>{market.data.coordinate_confidence != null ? `${Math.round(market.data.coordinate_confidence * 100)}%` : t('unitUnavailable')}</dd></div>
                <div><dt>{t('publicSourceConfidence')}</dt><dd>{market.data.source_confidence != null ? `${Math.round(market.data.source_confidence * 100)}%` : t('unitUnavailable')}</dd></div>
                <div><dt>{t('publicLastReviewed')}</dt><dd>{market.data.last_reviewed_at ? new Intl.DateTimeFormat({ en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' }[language]).format(new Date(market.data.last_reviewed_at)) : t('unitUnavailable')}</dd></div>
              </dl>
              <p>{market.data.source_name || t('publicNoSourceDetails')}</p>
              {sourceUrl && <a className="text-link" href={sourceUrl} target="_blank" rel="noopener noreferrer">{t('publicSourceRecord')}<ExternalLink size={16} /></a>}
            </section>
            <p className="rate-disclaimer">{t('publicCropPriceIntro')}</p>
            <Link className="button" to={`/prices?market=${encodeURIComponent(market.data.name)}&district=${encodeURIComponent(market.data.district || '')}`}>{t('publicCheckPricesAtMarket')}</Link>
          </>
        )}
      </DataState>
    </div>
  );
}
