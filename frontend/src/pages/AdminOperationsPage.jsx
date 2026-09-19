import { useEffect, useState } from 'react';
import { AlertTriangle, ClipboardCheck, Radio, ShieldCheck } from 'lucide-react';
import { DataState } from '../components/Experience';
import { getFraudCases, getOperationsOverview, getOutboxQueue, getProviderHealth, getVerificationQueue } from '../services/api';

export default function AdminOperationsPage() {
  const [state, setState] = useState({ loading: true, data: {}, error: false });
  useEffect(() => {
    let active = true;
    Promise.allSettled([getOperationsOverview(), getVerificationQueue(), getFraudCases(), getOutboxQueue('FAILED'), getProviderHealth()]).then((results) => {
      if (!active) return;
      const [overview, verification, fraud, outbox, providers] = results.map((item) => item.status === 'fulfilled' ? item.value : { success: false });
      setState({ loading: false, error: results.every((item) => item.status === 'rejected'), data: { overview, verification, fraud, outbox, providers } });
    });
    return () => { active = false; };
  }, []);
  if (state.loading) return <DataState loading />;
  if (state.error) return <DataState error onRetry={() => window.location.reload()} />;
  const { overview, verification, fraud, outbox, providers } = state.data;
  const cards = [
    ['System status', overview?.data?.status || 'Unknown', Radio],
    ['Verification reviews', verification?.data?.items?.length ?? 'Unavailable', ClipboardCheck],
    ['Cases requiring review', fraud?.data?.items?.length ?? 'Unavailable', ShieldCheck],
    ['Failed delivery events', outbox?.data?.items?.length ?? 'Unavailable', AlertTriangle],
  ];
  return <section className="page-stack" aria-labelledby="operations-title">
    <div><p className="eyebrow">Internal operations</p><h1 id="operations-title">Operations console</h1><p className="muted">Review evidence, delivery state and support work with least-privilege access.</p></div>
    <div className="card-grid">{cards.map(([label, value, Icon]) => <article className="card" key={label}><Icon size={22} aria-hidden="true" /><p className="muted">{label}</p><strong>{String(value)}</strong></article>)}</div>
    <article className="card"><h2>Provider configuration</h2><p className="muted">Configuration status is shown as evidence; it is not a delivery guarantee.</p><ul>{Object.entries(providers?.data || {}).map(([name, item]) => <li key={name}><strong>{name}</strong>: {item.status}</li>)}</ul></article>
    <article className="card"><h2>Safe operating rule</h2><p>Fraud entries are review signals. Notification retry is available only through the typed, audited delivery path; trade, payment and domain mutations are never replayed from this console.</p></article>
  </section>;
}
