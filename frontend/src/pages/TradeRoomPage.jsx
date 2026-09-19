import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, MessageSquareText } from 'lucide-react';
import {
  acknowledgeTradePayment,
  addTradeLogisticsUpdate,
  addTradeQualityReport,
  addTradeWeighment,
  createOperationKey,
  getStorageFacilities,
  getTradeRoom,
  addTradeNote,
  reportTradePayment,
  requestTradeStorage,
  uploadTradeEvidence,
} from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { Field, Notice, PageHeading } from '../components/Experience';
import { dateLabel } from '../lib/produce';

function timelineTitle(event, t) {
  if (event.event_type === 'USER_NOTE') return t('tradeNote');
  if (event.to_status) return t(`status_${event.to_status}`, event.title);
  const keyByType = {
    PAYMENT_REPORTED_SENT: 'timelinePaymentReported',
    PAYMENT_RECEIPT_ACKNOWLEDGED: 'timelinePaymentAcknowledged',
    QUALITY_CLAIM: 'timelineQualityClaim',
    QUALITY_OBSERVATION: 'timelineQualityObservation',
    WEIGHMENT_REPORTED: 'timelineWeighment',
    LOGISTICS_PICKUP_REPORTED: 'timelinePickup',
    LOGISTICS_DISPATCH_REPORTED: 'timelineDispatch',
    LOGISTICS_DELIVERY_REPORTED: 'timelineDelivery',
    LOGISTICS_RECEIPT_CONFIRMED: 'timelineReceipt',
    STORAGE_REQUESTED: 'timelineStorageRequest',
    EVIDENCE_SUBMITTED: 'timelineEvidence',
    DISPUTE_OPENED: 'timelineDisputeOpened',
    DISPUTE_STATUS_CHANGED: 'timelineDisputeUpdated',
  };
  const key = keyByType[event.event_type];
  return key ? t(key) : event.title;
}

function timelineDetail(event, t) {
  if (event.event_type === 'USER_NOTE' || event.event_type.startsWith('QUALITY_') || event.event_type.startsWith('LOGISTICS_')) {
    return event.description;
  }
  if (event.event_type === 'WEIGHMENT_REPORTED' && event.metadata) {
    const item = event.metadata;
    return `${t('netQuantity')}: ${item.net_quantity} ${t(item.unit)} · ${t('grossQuantity')}: ${item.gross_quantity} · ${t('tareQuantity')}: ${item.tare_quantity} · ${t('difference')}: ${item.difference_quantity} ${t(item.unit)}`;
  }
  if (event.event_type === 'EVIDENCE_SUBMITTED') return t('participantSubmitted');
  return null;
}

export default function TradeRoomPage() {
  const { id } = useParams();
  const { t, cropT, money, language } = useLanguage();
  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const [facilities, setFacilities] = useState([]);
  const [facilitiesError, setFacilitiesError] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentReference, setPaymentReference] = useState('');
  const [note, setNote] = useState('');
  const [qualityDetails, setQualityDetails] = useState('');
  const [gross, setGross] = useState('');
  const [tare, setTare] = useState('');
  const [logisticsKind, setLogisticsKind] = useState('');
  const [logisticsDetails, setLogisticsDetails] = useState('');
  const [storageFacility, setStorageFacility] = useState('');
  const [storageQuantity, setStorageQuantity] = useState('');
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidenceType, setEvidenceType] = useState('QUALITY_PHOTO');
  const operationKeys = useRef({});
  const fileInput = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const result = await getTradeRoom(id);
    setLoading(false);
    if (!result.success || !result.data) {
      setError(result.error || 'server');
      setRoom(null);
      return;
    }
    setRoom(result.data);
  }, [id]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    let active = true;
    getStorageFacilities().then((result) => {
      if (!active) return;
      setFacilities(result.data || []);
      setFacilitiesError(!result.success);
    });
    return () => { active = false; };
  }, []);

  function keyFor(name) {
    operationKeys.current[name] ||= createOperationKey();
    return operationKeys.current[name];
  }

  async function perform(name, action, onSuccess) {
    if (busy) return;
    setBusy(name);
    setActionError('');
    setNotice('');
    const result = await action(keyFor(name));
    setBusy('');
    if (!result.success) {
      setActionError(result.error || 'server');
      return;
    }
    delete operationKeys.current[name];
    setNotice('operationSaved');
    onSuccess?.();
    await load();
  }

  async function submitNote(event) {
    event.preventDefault();
    if (!note.trim() || busy) return;
    setBusy('note');
    setActionError('');
    const result = await addTradeNote(id, note.trim());
    setBusy('');
    if (!result.success) {
      setActionError(result.error || 'server');
      return;
    }
    setNote('');
    setNotice('tradeNoteSaved');
    await load();
  }

  if (loading) return <div className="data-state" role="status"><p>{t('loading')}</p></div>;
  if (!room) return <div className="farmer-trade-room"><Notice error>{t(error || 'tradeUnavailable')}</Notice><Link className="button secondary" to="/transactions"><ArrowLeft size={18} />{t('orders')}</Link></div>;

  const terms = room.terms;
  const buyerLabel = room.buyer?.business_name || (room.buyer?.full_name && room.buyer?.full_name !== 'Unavailable' ? room.buyer.full_name : t('buyerAccount'));
  const sellerLabel = room.seller?.full_name && room.seller.full_name !== 'Unavailable' ? room.seller.full_name : t('seller');
  const counterpartyLabel = room.viewer_party === 'seller' ? buyerLabel : sellerLabel;
  const locale = language === 'mr' ? 'mr-IN' : language === 'hi' ? 'hi-IN' : 'en-IN';

  return (
    <div className="farmer-trade-room">
      <Link className="text-link trade-back-link" to="/transactions"><ArrowLeft size={18} />{t('orders')}</Link>
      <PageHeading eyebrow={room.public_id || room.id} title={t('tradeRoom')} description={t('tradeRoomIntro')} />
      {actionError && <Notice error>{t(actionError)}</Notice>}
      {notice && <Notice>{t(notice)}</Notice>}
      <div className="trade-state-panel panel">
        <span className="status-pill">{t(`status_${room.status}`, room.status)}</span>
        <h2>{terms ? cropT(terms.crop_name) : t('termsUnavailable')}</h2>
        <p>{t('counterparty')}: <strong>{counterpartyLabel}</strong></p>
        <p>{t('tradeReference')}: {room.public_id || room.id}</p>
      </div>

      <section className="panel trade-terms-panel" aria-labelledby="trade-terms-title">
        <h2 id="trade-terms-title">{t('agreedTerms')}</h2>
        {terms ? <dl className="review-list">
          <div><dt>{t('crop')}</dt><dd>{cropT(terms.crop_name)}</dd></div>
          <div><dt>{t('quantity')}</dt><dd>{terms.quantity} {t(terms.unit || 'quintal')}</dd></div>
          <div><dt>{t('agreedPrice')}</dt><dd>{money(terms.price_per_unit)} / {t(terms.unit || 'quintal')}</dd></div>
          <div><dt>{t('agreedGross')}</dt><dd>{money(terms.gross_value)}</dd></div>
          <div><dt>{t('grade')}</dt><dd>{t(`grade_${terms.grade || 'UNSPECIFIED'}`)}</dd></div>
          {terms.pickup_location && <div><dt>{t('location')}</dt><dd>{terms.pickup_location}</dd></div>}
          {terms.delivery_window && <div><dt>{t('deliveryTerms')}</dt><dd>{terms.delivery_window}</dd></div>}
        </dl> : <Notice error>{t('termsUnavailable')}</Notice>}
      </section>

      <section className="panel trade-operations-panel" aria-labelledby="payment-report-title">
        <h2 id="payment-report-title">{t('paymentReport')}</h2>
        <p>{t('paymentReportIntro')}</p>
        <Notice>{t('paymentNoMovement')}</Notice>
        <p className="field-hint">{t('providerNotConnected')}</p>
        {room.payment?.reports?.map((report) => (
          <article className="trade-operation-record" key={report.id}>
            <strong>{money(report.amount)} · {t(report.source_kind === 'PARTICIPANT_REPORTED' ? 'participantReported' : 'legacyPaymentRecord')}</strong>
            <p>{t('paymentReference')}: {report.reference}</p>
            <p>{report.seller_acknowledged ? t('sellerAcknowledged') : t('notAcknowledged')}</p>
            <p className="field-hint">{t('participantSubmitted')}</p>
            {room.viewer_party === 'seller' && !report.seller_acknowledged && (
              <button className="button secondary" disabled={Boolean(busy)} onClick={() => perform(`payment-ack-${report.id}`, (key) => acknowledgeTradePayment(id, report.id, key))}>{t(busy === `payment-ack-${report.id}` ? 'loading' : 'acknowledgeReport')}</button>
            )}
          </article>
        ))}
        {room.viewer_party === 'buyer' && terms && !room.payment?.reports?.length && (
          <form className="form-stack trade-operation-form" onSubmit={(event) => {
            event.preventDefault();
            perform('payment-report', (key) => reportTradePayment(id, { amount: paymentAmount || String(terms.gross_value), reference: paymentReference }, key), () => { setPaymentReference(''); setPaymentAmount(''); });
          }}>
            <Field label={t('reportedAmount')} type="number" min="0.01" max={terms.gross_value} step="0.01" value={paymentAmount || String(terms.gross_value)} onChange={(event) => setPaymentAmount(event.target.value)} required />
            <Field label={t('paymentReference')} maxLength={120} value={paymentReference} onChange={(event) => setPaymentReference(event.target.value)} required />
            <button className="button" disabled={Boolean(busy)}>{t(busy === 'payment-report' ? 'loading' : 'reportPaymentSent')}</button>
          </form>
        )}
        {room.payment?.legacy_unverified_count > 0 && <p className="field-hint">{t('legacyPaymentWarning')} ({room.payment.legacy_unverified_count})</p>}
      </section>

      <details className="panel trade-operations-panel">
        <summary><strong>{t('qualitySection')}</strong></summary>
        <p>{t('qualityIntro')}</p>
        <p className="field-hint">{t(room.quality?.verification_status === 'PARTICIPANT_REPORTED' ? 'participantReported' : 'noAssay')}</p>
        <form className="form-stack trade-operation-form" onSubmit={(event) => {
          event.preventDefault();
          perform('quality-report', (key) => addTradeQualityReport(id, { kind: 'PARTICIPANT_CLAIM', details: qualityDetails, attributes: {} }, key), () => setQualityDetails(''));
        }}>
          <Field as="textarea" label={t('qualityClaim')} maxLength={1000} value={qualityDetails} onChange={(event) => setQualityDetails(event.target.value)} required />
          <button className="button secondary" disabled={Boolean(busy)}>{t(busy === 'quality-report' ? 'loading' : 'recordStatement')}</button>
        </form>
      </details>

      <details className="panel trade-operations-panel">
        <summary><strong>{t('weighmentSection')}</strong></summary>
        <p>{t('weighmentIntro')}</p>
        {terms && <form className="form-stack trade-operation-form" onSubmit={(event) => {
          event.preventDefault();
          perform('weighment', (key) => addTradeWeighment(id, { gross_quantity: gross, tare_quantity: tare || '0', unit: terms.unit }, key), () => { setGross(''); setTare(''); });
        }}>
          <Field label={`${t('grossQuantity')} (${t(terms.unit)})`} type="number" min="0.001" step="0.001" value={gross} onChange={(event) => setGross(event.target.value)} required />
          <Field label={`${t('tareQuantity')} (${t(terms.unit)})`} type="number" min="0" step="0.001" value={tare} onChange={(event) => setTare(event.target.value)} />
          <button className="button secondary" disabled={Boolean(busy)}>{t(busy === 'weighment' ? 'loading' : 'recordWeighment')}</button>
        </form>}
      </details>

      <details className="panel trade-operations-panel">
        <summary><strong>{t('logisticsSection')}</strong></summary>
        <p>{t('logisticsIntro')}</p>
        <form className="form-stack trade-operation-form" onSubmit={(event) => {
          event.preventDefault();
          perform('logistics', (key) => addTradeLogisticsUpdate(id, { kind: logisticsKind, details: logisticsDetails || null }, key), () => { setLogisticsKind(''); setLogisticsDetails(''); });
        }}>
          <label className="field"><span>{t('logisticsSection')}</span><select value={logisticsKind} onChange={(event) => setLogisticsKind(event.target.value)} required>
            <option value="">{t('chooseAction')}</option>
            {room.viewer_party === 'seller' ? <>
              <option value="PICKUP_REPORTED">{t('pickupReported')}</option>
              <option value="DISPATCH_REPORTED">{t('dispatchReported')}</option>
              <option value="DELIVERY_REPORTED">{t('deliveryReported')}</option>
            </> : <option value="RECEIPT_CONFIRMED">{t('receiptConfirmed')}</option>}
          </select></label>
          <Field label={t('optionalDetails')} maxLength={500} value={logisticsDetails} onChange={(event) => setLogisticsDetails(event.target.value)} />
          <button className="button secondary" disabled={Boolean(busy)}>{t(busy === 'logistics' ? 'loading' : 'recordLogistics')}</button>
        </form>
      </details>

      <details className="panel trade-operations-panel">
        <summary><strong>{t('storageSection')}</strong></summary>
        <p>{t('storageRequestIntro')}</p>
        {facilitiesError ? <Notice error>{t('server')}</Notice> : facilities.length ? <>
          {facilities.some((facility) => facility.is_demo) && <Notice>{t('storageDemo')}</Notice>}
          {terms && <form className="form-stack trade-operation-form" onSubmit={(event) => {
            event.preventDefault();
            perform('storage-request', (key) => requestTradeStorage(id, { facility_id: storageFacility, quantity: storageQuantity || String(terms.quantity), unit: terms.unit }, key), () => { setStorageFacility(''); setStorageQuantity(''); });
          }}>
            <label className="field"><span>{t('chooseFacility')}</span><select value={storageFacility} onChange={(event) => setStorageFacility(event.target.value)} required>
              <option value="">{t('chooseFacility')}</option>
              {facilities.map((facility) => <option key={facility.id} value={facility.id}>{facility.name}{facility.is_demo ? ` · ${t('storageDemo')}` : ''}</option>)}
            </select></label>
            <Field label={`${t('quantity')} (${t(terms.unit)})`} type="number" min="0.001" max={terms.quantity} step="0.001" value={storageQuantity || String(terms.quantity)} onChange={(event) => setStorageQuantity(event.target.value)} required />
            <button className="button secondary" disabled={Boolean(busy)}>{t(busy === 'storage-request' ? 'loading' : 'requestStorage')}</button>
          </form>}
        </> : <p>{t('noFacilities')}</p>}
        {room.storage_requests?.map((request) => <p className="trade-operation-record" key={request.id}>{request.facility_name} · {request.quantity} {t(request.unit)} · {t('pendingFacility')}</p>)}
      </details>

      <details className="panel trade-operations-panel">
        <summary><strong>{t('evidenceSection')}</strong></summary>
        <p>{t('evidenceIntro')}</p>
        <form className="form-stack trade-operation-form" onSubmit={(event) => {
          event.preventDefault();
          if (!evidenceFile) return;
          perform('evidence', (key) => uploadTradeEvidence(id, evidenceFile, evidenceType, key), () => { setEvidenceFile(null); if (fileInput.current) fileInput.current.value = ''; });
        }}>
          <label className="field"><span>{t('evidenceType')}</span><select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)}>
            <option value="QUALITY_PHOTO">{t('qualityPhoto')}</option>
            <option value="WEIGHMENT_DOCUMENT">{t('weighmentDocument')}</option>
            <option value="DELIVERY_DOCUMENT">{t('deliveryDocument')}</option>
            <option value="OTHER_TRADE_EVIDENCE">{t('otherEvidence')}</option>
          </select></label>
          <label className="field"><span>{t('uploadEvidence')}</span><input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => setEvidenceFile(event.target.files?.[0] || null)} required /></label>
          <button className="button secondary" disabled={Boolean(busy) || !evidenceFile}>{t(busy === 'evidence' ? 'loading' : 'uploadEvidence')}</button>
        </form>
        <div className="list-stack">
          {room.evidence?.map((item) => <article className="trade-operation-record" key={item.id}>
            <strong>{t(item.classification === 'QUALITY_PHOTO' ? 'qualityPhoto' : item.classification === 'WEIGHMENT_DOCUMENT' ? 'weighmentDocument' : item.classification === 'DELIVERY_DOCUMENT' ? 'deliveryDocument' : 'otherEvidence')}</strong>
            <p>{item.original_filename}</p>
            <p>{t('participantSubmitted')} · {item.file_size_bytes || '—'} {t('bytes')}</p>
            {item.url && <a className="text-link" href={item.url} target="_blank" rel="noreferrer">{t('viewEvidence')}</a>}
          </article>)}
        </div>
      </details>

      <section className="panel trade-timeline-panel" aria-labelledby="trade-timeline-title">
        <h2 id="trade-timeline-title">{t('tradeTimeline')}</h2>
        {room.timeline?.length ? <ol className="trade-timeline">{room.timeline.map((event) => {
          const detail = timelineDetail(event, t);
          const sourceKey = event.source_kind === 'PARTICIPANT_REPORTED' ? 'participantReported' : event.source_kind === 'OPERATOR_RECORDED' ? 'operatorRecorded' : event.source_kind === 'PLATFORM_RECORDED' ? 'platformRecorded' : '';
          return <li key={event.id}>
            <span className="trade-timeline-marker" aria-hidden="true" />
            <div>
              <strong>{timelineTitle(event, t)}</strong>
              {sourceKey && <span className="trade-source-label">{t(sourceKey)}</span>}
              {detail && <p>{detail}</p>}
              <time dateTime={event.created_at}>{dateLabel(event.created_at, language)} · {new Intl.DateTimeFormat(locale, { hour: '2-digit', minute: '2-digit' }).format(new Date(event.created_at))}</time>
            </div>
          </li>;
        })}</ol> : <p>{t('noTradeEvents')}</p>}
      </section>

      <section className="panel trade-support-panel">
        <h2>{t('needHelp')}</h2>
        <p>{t('tradeSupportHelp')}</p>
        <Link className="button secondary" to={`/grievances?trade=${encodeURIComponent(room.id)}`}><MessageSquareText size={18} />{t('raiseIssue')}</Link>
      </section>

      <form className="panel form-stack trade-note-form" onSubmit={submitNote}>
        <h2>{t('addTradeNote')}</h2>
        <Field as="textarea" label={t('noteDetails')} maxLength={1000} value={note} onChange={(event) => setNote(event.target.value)} required />
        <button className="button" disabled={Boolean(busy) || !note.trim()}>{t(busy === 'note' ? 'loading' : 'saveNote')}</button>
      </form>
    </div>
  );
}
