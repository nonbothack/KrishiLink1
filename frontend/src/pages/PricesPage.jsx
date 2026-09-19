import RateLookup from '../components/RateLookup';
import { PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { usePageMetadata } from '../lib/metadata';
export default function PricesPage() {
  const { t } = useLanguage();
  usePageMetadata({ title: 'Reported agricultural market prices | KrishiLink', description: 'Compare official reported market price observations by crop, district and market, with report date, source and unit.', path: '/prices' });
  return (
    <div className="site-container page-section">
      <PageHeading eyebrow="KRISHILINK" title={t('prices')} description={t('priceIntro')} />
      <RateLookup />
    </div>
  );
}
