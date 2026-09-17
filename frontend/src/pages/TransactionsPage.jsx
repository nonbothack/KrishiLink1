import { getTransactions } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Notice, PageHeading, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
export default function TransactionsPage(){
 const {t,cropT,money,language}=useLanguage();const orders=useResource(getTransactions);
 return <><PageHeading title={t('orders')} action={<button className="button secondary" onClick={orders.retry}>{t('refresh')}</button>}/><Notice>{t('paymentNote')}</Notice><DataState loading={orders.loading} error={orders.error} empty={!orders.data.length?t('noOrders'):false} onRetry={orders.retry}><div className="list-stack">{orders.data.map(o=><article className="panel listing-row" key={o.id}><div><span className="status-pill">{t('status_'+o.status,o.status)}</span><h3>{cropT(o.crop_name||o.crop)||t('orders')}</h3><p>{dateLabel(o.created_at,language)}</p><p>{o.id}</p></div><div><strong className="amount">{money(o.gross_value??o.total_amount??0)}</strong><p>{t('grossTotal')}</p></div></article>)}</div></DataState></>;
}
