import { getTransactions } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Notice, PageHeading, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
import { Link } from 'react-router-dom';
export default function TransactionsPage() {
  const { t, cropT, money, language } = useLanguage();
  const orders = useResource(getTransactions);
  return (
    <>
      <PageHeading
        title={t('orders')}
        action={
          <button className="button secondary" onClick={orders.retry}>
            {t('refresh')}
          </button>
        }
      />
      <Notice>{t('paymentNote')}</Notice>
      <DataState
        loading={orders.loading}
        error={orders.error}
        empty={!orders.data.length ? t('noOrders') : false}
        onRetry={orders.retry}
      >
        <div className="list-stack">
          {orders.data.map((o) => (
            <article className="panel listing-row" key={o.id}>
              <div>
                <span className="status-pill">{t('status_' + o.status, o.status)}</span>
                <h3>{cropT(o.crop_name || o.crop) || t('orders')}</h3>
                <p>{o.seller_label || o.buyer_name || t('buyer')}</p>
                {o.quantity && <p>{o.quantity} {t(o.unit || 'quintal')} · {o.price_per_unit ? `${money(o.price_per_unit)} / ${t(o.unit || 'quintal')}` : t('priceUnavailable')}</p>}
                <p>{dateLabel(o.created_at, language)}</p>
                <p>{t('tradeReference')}: {o.public_id || o.id}</p>
              </div>
              <div>
                {o.gross_value != null ? <><strong className="amount">{money(o.gross_value)}</strong><p>{t('agreedGross')}</p></> : <p>{t('amountUnavailable')}</p>}
                <Link className="text-link" to={`/trades/${o.id}`}>
                  {t('openTrade')} →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </DataState>
    </>
  );
}
