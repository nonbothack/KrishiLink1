import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getGrievances, createGrievance } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Field, Notice, PageHeading, useResource } from '../components/Experience';
export default function GrievancesPage() {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const transactionId = searchParams.get('trade');
  const tickets = useResource(getGrievances);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const res = await createGrievance({
      reason,
      description,
      category: 'General Inquiry',
      priority: 'MEDIUM',
      ...(transactionId ? { transaction_id: transactionId } : {}),
    });
    setBusy(false);
    if (res.success && res.data) {
      setOpen(false);
      setSent(true);
      setReason('');
      setDescription('');
      tickets.retry();
    } else setError(res.error || 'server');
  }
  return (
    <>
      <PageHeading
        title={t('support')}
        action={
          <button className="button" onClick={() => setOpen(!open)}>
            {t(open ? 'cancel' : 'raiseIssue')}
          </button>
        }
      />
      {sent && <Notice>{t('submitted')}</Notice>}
      {open && (
        <form className="panel form-stack grievance-form" onSubmit={submit}>
          {transactionId && <p className="field-hint">{t('tradeLinkedIssue')}</p>}
          <Field
            label={t('subject')}
            required
            minLength={3}
            maxLength={200}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <Field
            label={t('description')}
            as="textarea"
            minLength={5}
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          {error && <Notice error>{t(error)}</Notice>}
          <button className="button" disabled={busy}>
            {t(busy ? 'loading' : 'submit')}
          </button>
        </form>
      )}
      <DataState
        loading={tickets.loading}
        error={tickets.error}
        empty={!tickets.data.length}
        onRetry={tickets.retry}
      >
        <div className="list-stack">
          {tickets.data.map((item) => (
            <article className="panel" key={item.id}>
              <span className="status-pill">{t('status_' + item.status, item.status)}</span>
              <h2 className="grievance-title">{item.reason}</h2>
              <p className="muted">{item.description}</p>
              <p className="field-hint">{item.ticket_number || item.id}</p>
              {item.resolution && <p>{item.resolution}</p>}
            </article>
          ))}
        </div>
      </DataState>
    </>
  );
}
