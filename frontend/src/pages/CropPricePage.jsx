import { Link, useParams } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { DataState, PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { usePageMetadata } from '../lib/metadata';
import { getCrops, getReportedPrices } from '../services/api';

export default function CropPricePage() {
  const { crop: slug } = useParams();
  const { t, language, money, cropT } = useLanguage();
  const snapshot = getPublicSnapshot();
  const initialCrop = snapshot?.path === `/prices/${slug}` ? snapshot.crop : null;
  const crops = useResource(getCrops, [], initialCrop ? { data: [initialCrop], total: 1, pages: 1 } : null);
  const crop = initialCrop || crops.data.find((item) => item.slug === slug);
  const prices = useResource(
    () => crop ? getReportedPrices({ crop: crop.name, limit: 20 }) : Promise.resolve({ success: true, data: [] }),
    [crop?.id],
    snapshot?.path === `/prices/${slug}` && snapshot.prices ? { data: snapshot.prices.items || [], total: snapshot.prices.total || 0, pages: snapshot.prices.pages || 1, error: snapshot.priceStatus === 'error' ? 'network' : null } : null,
  );
  usePageMetadata({
    title: crop ? `${crop.name}: reported market prices | KrishiLink` : 'Reported crop prices | KrishiLink',
    description: crop ? `See dated official reported market price observations for ${crop.name}, with market, source and unit.` : 'Browse dated official reported agricultural market price observations with their source and unit.',
    path: `/prices/${slug}`,
    noindex: !crop || (!prices.loading && !prices.error && prices.data.length === 0),
  });

  if (!crops.loading && !crops.error && !crop) {
    return <div className="site-container page-section"><PageHeading title={t('publicNoCrop')} /><Link className="button" to="/prices">{t('publicTryPrices')}</Link></div>;
  }
  return (
    <div className="site-container page-section public-crop-page">
      <PageHeading eyebrow={t('prices')} title={crop ? `${cropT(crop.name)} ${t('publicPricesForCrop')}` : t('publicPricesForCrop')} description={t('publicCropPriceIntro')} />
      <DataState loading={crops.loading || prices.loading} error={crops.error || prices.error} empty={!prices.data.length && !prices.loading && !prices.error ? t('publicNoCropPrice') : false} onRetry={crops.error ? crops.retry : prices.retry}>
        <div className="card-grid public-price-grid">
          {prices.data.map((price) => (
            <article className="panel price-result" key={price.id}>
              <p className="eyebrow">{price.market}</p>
              <div className="price-number">{price.modal_price != null ? money(price.modal_price) : '—'}</div>
              <p className="unit-label">{price.unit === 'INR/quintal' ? t('perQuintal') : price.unit === 'INR/number' ? t('perNumber') : t('unitUnavailable')}</p>
              <p className="market-line">{[price.district, price.state].filter(Boolean).join(', ')}</p>
              <p>{t('reportedOn')}: {dateLabel(price.price_date, language) || t('noDate')}</p>
              <p className="price-source">{t('sourceLabel')}: {price.source || t('unitUnavailable')}</p>
              <p className="price-source">{price.freshness_state === 'stale' ? t('staleReportedPrice') : t('publicReportedFreshness')}</p>
              {price.location_verified === false && <p className="price-source">{t('locationUnverified')}</p>}
            </article>
          ))}
        </div>
      </DataState>
      <p className="rate-disclaimer">{t('referenceOnly')}</p>
      <Link className="text-link" to={`/prices?crop=${encodeURIComponent(crop?.name || slug)}`}>{t('publicTryPrices')}<ArrowUpRight size={17} /></Link>
    </div>
  );
}
