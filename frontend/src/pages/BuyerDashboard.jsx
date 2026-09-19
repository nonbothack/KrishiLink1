import { Link } from 'react-router-dom';
import { getNotifications, getOffers, getRequirements, getTransactions } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, PageHeading, useResource } from '../components/Experience';
export default function BuyerDashboard() {
  const { t, cropT } = useLanguage();
  const requirements = useResource(getRequirements); const offers = useResource(getOffers); const trades = useResource(getTransactions); const notifications = useResource(getNotifications);
  const active = requirements.data.filter((item) => ['ACTIVE', 'PARTIALLY_FILLED'].includes(item.status));
  const actions = [...offers.data.filter((item) => item.status === 'COUNTERED'), ...trades.data.filter((item) => item.status !== 'COMPLETED')].slice(0, 3);
  return (
    <>
      <PageHeading
        title={t('buyerDashboard')}
        description={t('buyerDashboardIntro')}
        action={
          <Link className="button" to="/buyer/requirements">{t('createRequirement')}</Link>
        }
      />
      <div className="card-grid buyer-summary"><article className="panel"><h2>{t('openRequirements')}</h2><strong className="amount">{active.length}</strong><Link to="/buyer/requirements">{t('viewRequirements')}</Link></article><article className="panel"><h2>{t('offersRequiringAction')}</h2><strong className="amount">{offers.data.filter((item) => item.status === 'COUNTERED').length}</strong><Link to="/offers">{t('viewOffers')}</Link></article><article className="panel"><h2>{t('activeTrades')}</h2><strong className="amount">{trades.data.filter((item) => item.status !== 'COMPLETED').length}</strong><Link to="/transactions">{t('orders')}</Link></article></div>
      <section className="panel"><h2>{t('procurementActions')}</h2><DataState loading={offers.loading || trades.loading} error={offers.error || trades.error} empty={!actions.length ? t('noBuyerActions') : false}>{actions.map((item) => <p key={item.id}>{item.crop_name ? cropT(item.crop_name) : cropT(item.crop)} · <Link to={item.transaction_id ? `/trades/${item.transaction_id}` : '/offers'}>{t('open')}</Link></p>)}</DataState></section>
      <section className="panel"><h2>{t('notifications')}</h2><DataState loading={notifications.loading} error={notifications.error} empty={!notifications.data.length ? t('empty') : false}>{notifications.data.slice(0, 3).map((item) => <p key={item.id}>{item.title}</p>)}</DataState></section>
    </>
  );
}
