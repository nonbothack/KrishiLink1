import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, CircleHelp, FileText, MessageSquareText, TrendingUp } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { getNotifications, markNotificationRead } from '../services/api';
import { DataState, PageHeading, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
import OfflineLotQueue from '../components/OfflineLotQueue';
import { ReadAloudButton } from '../components/VoiceControls';
import { getSimpleMode, setSimpleMode } from '../lib/experiencePreferences';

function notificationPath(item) {
  const type = String(item.type || '').toLowerCase();
  if (type === 'price_alert') return '/prices';
  if (type.includes('offer') && item.related_id) return `/offers?offer_id=${encodeURIComponent(item.related_id)}`;
  if ((type.includes('order') || type.includes('trade') || type.includes('deal')) && item.related_id) return `/trades/${encodeURIComponent(item.related_id)}`;
  return '/grievances';
}

function notificationTitle(item, t) {
  const type = String(item.type || '').toLowerCase();
  const keyByType = {
    offer_received: 'notificationTitle_offer_received',
    counter_offer: 'notificationTitle_counter_offer',
    offer_accepted: 'notificationTitle_offer_accepted',
    offer_rejected: 'notificationTitle_offer_rejected',
    lot_withdrawn: 'notificationTitle_lot_withdrawn',
    trade_created: 'notificationTitle_trade_created',
    order_status: 'notificationTitle_order_status',
    support_ticket: 'notificationTitle_support_ticket',
    grievance_updated: 'notificationTitle_support_update',
    price_alert: 'notificationTitle_price_alert',
  };
  return keyByType[type] ? t(keyByType[type]) : t('notificationTitle_update');
}

function notificationCopy(item, t, cropT, money, language) {
  const type = String(item.type || '').toLowerCase();
  if (type === 'price_alert' && item.metadata) {
    const facts = item.metadata;
    const reportDate = facts.reported_date
      ? new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${facts.reported_date}T12:00:00Z`))
      : t('dateUnavailable');
    return `${t('priceAlertNotificationLead')} ${cropT(facts.crop || '')} · ${facts.market || ''} · ${money(facts.modal_price || 0)} / ${t('perQuintal')} · ${t('priceAlertLimitLabel')}: ${money(facts.threshold || 0)} · ${t('reportedOn')} ${reportDate} · ${t('sourceLabel')}: ${facts.source || t('sourceUnavailable')}`;
  }
  if (type.includes('offer_received')) return t('notificationOfferReceived');
  if (type.includes('counter_offer')) return t('notificationCounterOffer');
  if (type.includes('offer_accepted')) return t('notificationOfferAccepted');
  if (type.includes('offer_rejected')) return t('notificationOfferDeclined');
  if (type.includes('trade_created')) return t('notificationTradeCreated');
  if (type.includes('lot_withdrawn')) return t('notificationLotWithdrawn');
  if (type.includes('order_status')) return t('notificationTradeUpdate');
  if (type.includes('grievance') || type.includes('dispute')) return t('notificationSupportUpdate');
  return item.message;
}

export default function FarmerMorePage() {
  const { user } = useAuth();
  const { t, language, cropT, money } = useLanguage();
  const navigate = useNavigate();
  const notifications = useResource(getNotifications, [user.id]);
  const [simple, setSimple] = useState(() => getSimpleMode(user.id));

  async function openNotification(item) {
    if (!item.is_read) await markNotificationRead(item.id);
    navigate(notificationPath(item));
  }

  return (
    <div className="farmer-more-page">
      <PageHeading title={t('more')} description={t('farmerMoreIntro')} />
      <div className="farmer-more-grid">
        <Link className="panel farmer-more-tile" to="/transactions"><FileText size={24} /><strong>{t('orders')}</strong><span>{t('transactionRecords')}</span></Link>
        <Link className="panel farmer-more-tile" to="/farmer/price-alerts"><TrendingUp size={24} /><strong>{t('priceAlerts')}</strong><span>{t('priceAlertsIntro')}</span></Link>
        <Link className="panel farmer-more-tile" to="/grievances"><MessageSquareText size={24} /><strong>{t('support')}</strong><span>{t('raiseIssue')}</span></Link>
        <Link className="panel farmer-more-tile" to="/help"><CircleHelp size={24} /><strong>{t('help')}</strong><span>{t('helpIntro')}</span></Link>
      </div>

      <section className="panel reach-preferences">
        <h2>{t('farmerAccessTitle')}</h2>
        <label className="checkbox-row">
          <input type="checkbox" checked={simple} onChange={(event) => { setSimple(event.target.checked); setSimpleMode(user.id, event.target.checked); }} />
          <span><strong>{t('simpleMode')}</strong><br /><small>{t('simpleModeHelp')}</small></span>
        </label>
        <p>{t('voiceHelpCopy')}</p>
        <ReadAloudButton text={t('voiceHelpCopy')} />
      </section>


      <OfflineLotQueue />

      <section id="notifications" className="farmer-notifications">
        <div className="section-heading"><h2><Bell size={20} aria-hidden="true" />{t('notifications')}</h2><button className="text-link" onClick={notifications.retry}>{t('refresh')}</button></div>
        <DataState loading={notifications.loading} error={notifications.error} empty={!notifications.data.length && !notifications.loading ? t('noNotifications') : false} onRetry={notifications.retry}>
          <div className="list-stack">{notifications.data.map((item) => (
            <button className={`panel notification-row ${item.is_read ? '' : 'unread'}`} key={item.id} type="button" onClick={() => openNotification(item)}>
              <span className="notification-dot" aria-hidden="true" />
              <span className="notification-copy"><strong>{notificationTitle(item, t)}</strong><span>{notificationCopy(item, t, cropT, money, language)}</span><small>{dateLabel(item.created_at, language)}</small></span>
            </button>
          ))}</div>
        </DataState>
      </section>
    </div>
  );
}
