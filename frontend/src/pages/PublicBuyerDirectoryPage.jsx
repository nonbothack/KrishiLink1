import { Building2 } from 'lucide-react';
import { PageHeading, DataState } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
import { useResource } from '../components/Experience';
import { getPublicBuyers } from '../services/api';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { usePageMetadata } from '../lib/metadata';

export default function PublicBuyerDirectoryPage() {
  const { t } = useLanguage();
  const snapshot = getPublicSnapshot();
  const buyers = useResource(
    getPublicBuyers,
    [],
    snapshot?.path === '/buyers' && snapshot.buyers ? { data: snapshot.buyers, total: snapshot.buyers.length, pages: 1, error: snapshot.buyersStatus === 'error' ? 'network' : null } : null,
  );
  usePageMetadata({ title: 'Buyer businesses | KrishiLink', description: 'Browse public business profiles with business review completed. Personal contact details are not published in this directory.', path: '/buyers', noindex: !buyers.loading && buyers.data.length === 0 });
  return (
    <div className="site-container page-section public-directory">
      <PageHeading eyebrow={t('publicBuyers')} title={t('publicBuyerTitle')} description={t('publicBuyerIntro')} />
      <DataState loading={buyers.loading} error={buyers.error} empty={!buyers.data.length && !buyers.loading && !buyers.error ? t('publicNoBuyer') : false} onRetry={buyers.retry}>
        <div className="card-grid public-buyer-grid">
          {buyers.data.map((buyer, index) => (
            <article className="panel public-buyer-card" key={buyer.business_name + index}>
              <Building2 size={24} aria-hidden="true" />
              <h2>{buyer.business_name}</h2>
              {buyer.type && <p>{buyer.type}</p>}
              <p className="muted">{[buyer.district, buyer.state].filter(Boolean).join(', ')}</p>
              <p className="public-status-text">{t('publicBuyerVerifiedDimension')}: {t('publicBusinessChecked')}</p>
              {buyer.crops?.length > 0 && <p><strong>{t('publicCropsInterested')}:</strong> {buyer.crops.join(', ')}</p>}
            </article>
          ))}
        </div>
      </DataState>
    </div>
  );
}
