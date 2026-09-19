import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  addFPOMember, correctFPOIntake, createFPOIntake, createFPOPool, getCrops, getFPOIntakes,
  getFPOLots, getFPOMembers, getFPOPools, getFPOTrades, getFPOTradeTrace,
  importFPOMembers, previewFPOMemberImport, publishFPOPool,
} from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Field, Notice, PageHeading, useResource } from '../components/Experience';

const newKey = () => crypto.randomUUID();

export default function FPODashboard() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const members = useResource(getFPOMembers);
  const intakes = useResource(getFPOIntakes);
  const pools = useResource(getFPOPools);
  const lots = useResource(getFPOLots);
  const trades = useResource(getFPOTrades);
  const crops = useResource(getCrops);
  const [member, setMember] = useState({ farmer_name: '', primary_crop: '', grade: 'UNSPECIFIED' });
  const [intake, setIntake] = useState({ member_id: '', crop: '', grade: 'UNSPECIFIED', gross_quantity: '', tare_quantity: '0', unit: 'kg' });
  const [selected, setSelected] = useState({});
  const [publish, setPublish] = useState({});
  const [corrections, setCorrections] = useState({});
  const [csv, setCsv] = useState('');
  const [importPreview, setImportPreview] = useState(null);
  const [trace, setTrace] = useState({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const intakeKey = useRef(newKey());
  const poolKey = useRef(newKey());
  const importKey = useRef(newKey());
  const refresh = () => { members.retry(); intakes.retry(); pools.retry(); lots.retry(); trades.retry(); };
  async function run(action) {
    if (busy) return false;
    setBusy(true); setError(''); setMessage('');
    const response = await action();
    setBusy(false);
    if (response.success) { setMessage(response.message); refresh(); return true; }
    setError(t('fpoErrorSave')); return false;
  }
  async function submitMember(event) {
    event.preventDefault();
    if (await run(() => addFPOMember(member))) setMember({ farmer_name: '', primary_crop: '', grade: 'UNSPECIFIED' });
  }
  async function submitIntake(event) {
    event.preventDefault();
    if (await run(() => createFPOIntake(intake, intakeKey.current))) {
      intakeKey.current = newKey();
      setIntake({ member_id: '', crop: '', grade: 'UNSPECIFIED', gross_quantity: '', tare_quantity: '0', unit: 'kg' });
    }
  }
  async function makePool() {
    const contributions = Object.entries(selected).filter(([, amount]) => Number(amount) > 0).map(([intake_id, quantity]) => ({ intake_id, quantity }));
    if (!contributions.length) { setError(t('fpoPoolIntro')); return; }
    if (await run(() => createFPOPool({ contributions }, poolKey.current))) { poolKey.current = newKey(); setSelected({}); }
  }
  async function previewImport() {
    setBusy(true); setError(''); setMessage('');
    const response = await previewFPOMemberImport(csv);
    setBusy(false);
    if (response.success) setImportPreview(response.data);
    else setError(t('fpoErrorSave'));
  }
  async function loadCsvFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(''); setImportPreview(null);
    if (file.size > 1_048_576) { setCsv(''); setError(t('fpoCsvTooLarge')); return; }
    try {
      const contents = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
      setCsv(contents.replace(/^\uFEFF/, ''));
    } catch {
      setCsv(''); setError(t('fpoCsvUtf8Error'));
    }
  }
  async function confirmImport() {
    if (await run(() => importFPOMembers(csv, importKey.current))) {
      importKey.current = newKey(); setCsv(''); setImportPreview(null);
    }
  }
  return (
    <>
      <PageHeading title={user.name || t('fpoDashboardTitle')} description={t('fpoDashboardIntro')} />
      {error && <Notice error>{error}</Notice>}
      {message && <Notice>{message}</Notice>}

      <section className="panel form-stack" aria-labelledby="fpo-members-heading">
        <h2 id="fpo-members-heading">1. {t('fpoMembers')}</h2>
        <form className="form-grid" onSubmit={submitMember}>
          <Field label={t('fpoMemberName')} required minLength={2} value={member.farmer_name} onChange={(event) => setMember({ ...member, farmer_name: event.target.value })} />
          <Field label={t('fpoPrimaryCrop')} as="select" required value={member.primary_crop} onChange={(event) => setMember({ ...member, primary_crop: event.target.value })}>
            <option value="">{t('selectCrop')}</option>{crops.data.map((crop) => <option key={crop.id} value={crop.name}>{cropT(crop.name)}</option>)}
          </Field>
          <Field label={t('grade')} as="select" value={member.grade} onChange={(event) => setMember({ ...member, grade: event.target.value })}>
            {['A', 'B', 'C', 'UNSPECIFIED'].map((grade) => <option key={grade} value={grade}>{t(`grade_${grade}`)}</option>)}
          </Field>
          <button className="button" disabled={busy}>{busy ? t('loading') : t('fpoAddMember')}</button>
        </form>
        <DataState loading={members.loading} error={members.error} empty={members.data.length ? false : t('empty')} onRetry={members.retry}>
          <ul className="list-stack">{members.data.map((item) => <li className="listing-row" key={item.id}><span><strong>{item.farmer_name}</strong> · {cropT(item.primary_crop)} · {item.grade}</span><span>{item.available_quantity_qtl} {t('quintal')}</span></li>)}</ul>
        </DataState>
        <details>
          <summary>{t('fpoImport')}</summary>
          <p>{t('fpoCsvHelp')}</p>
          <Field label={t('fpoChooseCsv')} type="file" accept=".csv,text/csv" onChange={loadCsvFile} />
          <Field label={t('fpoImport')} as="textarea" rows={5} value={csv} onChange={(event) => { setCsv(event.target.value); setImportPreview(null); }} />
          <button className="button secondary" type="button" disabled={busy || !csv} onClick={previewImport}>{t('fpoPreviewImport')}</button>
          {importPreview && <div role="status"><p>{t('fpoImportAccepted')}: {importPreview.accepted_count} · {t('fpoImportRejected')}: {importPreview.rejected_count}</p>
            {importPreview.rejected.map((row) => <p key={`${row.row}-${row.member_code}`}>{t('fpoImportRejected')} {row.row}: {t('fpoImportRowInvalid')}</p>)}
            {importPreview.accepted_count > 0 && <button className="button" type="button" disabled={busy} onClick={confirmImport}>{t('fpoConfirmImport')}</button>}
          </div>}
        </details>
      </section>

      <section className="panel form-stack" aria-labelledby="fpo-intake-heading">
        <h2 id="fpo-intake-heading">2. {t('fpoIntake')}</h2><p>{t('fpoIntakeIntro')}</p>
        <form className="form-grid" onSubmit={submitIntake}>
          <Field label={t('fpoMembers')} as="select" required value={intake.member_id} onChange={(event) => setIntake({ ...intake, member_id: event.target.value })}>
            <option value="">{t('fpoMembers')}</option>{members.data.map((item) => <option key={item.id} value={item.id}>{item.farmer_name}</option>)}
          </Field>
          <Field label={t('crop')} as="select" required value={intake.crop} onChange={(event) => setIntake({ ...intake, crop: event.target.value })}>
            <option value="">{t('selectCrop')}</option>{crops.data.map((crop) => <option key={crop.id} value={crop.id}>{cropT(crop.name)}</option>)}
          </Field>
          <Field label={t('grade')} as="select" value={intake.grade} onChange={(event) => setIntake({ ...intake, grade: event.target.value })}>
            {['A', 'B', 'C', 'UNSPECIFIED'].map((grade) => <option key={grade} value={grade}>{t(`grade_${grade}`)}</option>)}
          </Field>
          <Field label={t('fpoGross')} type="number" inputMode="decimal" min=".001" step=".001" required value={intake.gross_quantity} onChange={(event) => setIntake({ ...intake, gross_quantity: event.target.value })} />
          <Field label={t('fpoTare')} type="number" inputMode="decimal" min="0" step=".001" value={intake.tare_quantity} onChange={(event) => setIntake({ ...intake, tare_quantity: event.target.value })} />
          <Field label={t('unit')} as="select" value={intake.unit} onChange={(event) => setIntake({ ...intake, unit: event.target.value })}><option value="kg">kg</option><option value="quintal">{t('quintal')}</option></Field>
          <button className="button" disabled={busy}>{busy ? t('loading') : t('fpoReceipt')}</button>
        </form>
        <DataState loading={intakes.loading} error={intakes.error} empty={intakes.data.length ? false : t('fpoNoReceipts')} onRetry={intakes.retry}>
          <div className="list-stack">{intakes.data.map((item) => <article className="panel" key={item.id}>
            <strong>{t('fpoReceiptId')}: {item.receipt_id}</strong>
            <p>{cropT(item.crop)} · {t('fpoGross')}: {item.gross_quantity} {item.unit} · {t('fpoTare')}: {item.tare_quantity} {item.unit}</p>
            <p>{t('fpoNet')}: {item.net_quantity} {item.unit} · {item.canonical_quantity_qtl} {t('quintal')} · {t('fpoAvailable')}: {item.available_quantity_qtl}</p>
            {item.correction_of_receipt_id && <p>{t('fpoCorrected')} {item.correction_of_receipt_id}</p>}
            {item.is_voided ? <p>{t('fpoCorrected')} {item.corrected_by_receipt_id}</p> : item.available_quantity_qtl === item.canonical_quantity_qtl && <details><summary>{t('fpoCorrectReceipt')}</summary>
              <Field label={t('fpoGross')} type="number" min=".001" step=".001" value={corrections[item.id]?.gross_quantity || ''} onChange={(event) => setCorrections({ ...corrections, [item.id]: { ...corrections[item.id], gross_quantity: event.target.value } })} />
              <Field label={t('fpoCorrectionReason')} value={corrections[item.id]?.reason || ''} onChange={(event) => setCorrections({ ...corrections, [item.id]: { ...corrections[item.id], reason: event.target.value } })} />
              <button className="button secondary" type="button" disabled={busy} onClick={() => run(() => correctFPOIntake(item.id, { gross_quantity: corrections[item.id]?.gross_quantity, tare_quantity: item.tare_quantity, reason: corrections[item.id]?.reason }, newKey()))}>{t('fpoCorrectReceipt')}</button>
            </details>}
          </article>)}</div>
        </DataState>
      </section>

      <section className="panel form-stack" aria-labelledby="fpo-pool-heading">
        <h2 id="fpo-pool-heading">3. {t('fpoPool')}</h2><p>{t('fpoPoolIntro')}</p>
        <DataState loading={intakes.loading} error={intakes.error} empty={intakes.data.length ? false : t('fpoNoReceipts')} onRetry={intakes.retry}>
          <div className="list-stack">{intakes.data.filter((item) => Number(item.available_quantity_qtl) > 0).map((item) => <div className="listing-row" key={item.id}>
            <span><strong>{item.receipt_id}</strong> · {cropT(item.crop)} · {item.grade}<br />{t('fpoAvailable')}: {item.available_quantity_qtl} {t('quintal')}</span>
            <Field label={`${t('fpoContribution')} · ${item.receipt_id}`} type="number" min="0" max={item.available_quantity_qtl} step=".001" value={selected[item.id] || ''} onChange={(event) => setSelected({ ...selected, [item.id]: event.target.value })} />
          </div>)}</div>
          <button className="button" type="button" disabled={busy} onClick={makePool}>{t('fpoCreatePool')}</button>
        </DataState>
        <DataState loading={pools.loading} error={pools.error} empty={pools.data.length ? false : t('fpoNoPools')} onRetry={pools.retry}>
          <div className="list-stack">{pools.data.map((pool) => <article className="listing-row" key={pool.id}>
            <span><strong>{pool.pool_id}</strong> · {cropT(pool.crop)} · {pool.grade} · {pool.quantity_qtl} {t('quintal')} · {t(`pool_${pool.status}`)}</span>
            {pool.status === 'READY' && <div className="form-stack">
              <Field label={`${t('fpoAskingPrice')} · ${pool.pool_id}`} type="number" min=".01" step=".01" value={publish[pool.id]?.asking_price || ''} onChange={(event) => setPublish({ ...publish, [pool.id]: { ...publish[pool.id], asking_price: event.target.value } })} />
              <Field label={`${t('fpoLocation')} · ${pool.pool_id}`} value={publish[pool.id]?.location_text || ''} onChange={(event) => setPublish({ ...publish, [pool.id]: { ...publish[pool.id], location_text: event.target.value } })} />
              <button className="button" type="button" disabled={busy} onClick={() => run(() => publishFPOPool(pool.id, publish[pool.id], newKey()))}>{t('fpoPublish')}</button>
            </div>}
          </article>)}</div>
        </DataState>
      </section>

      <section className="panel form-stack"><h2>{t('groupLots')}</h2>
        <DataState loading={lots.loading} error={lots.error} empty={lots.data.length ? false : t('empty')} onRetry={lots.retry}>
          <div className="list-stack">{lots.data.map((lot) => <Link className="listing-row" to="/offers" key={lot.id}><span><strong>{lot.public_id}</strong> · {cropT(lot.crop)} · {lot.quantity} {t('quintal')}</span><strong>{t(`status_${lot.status}`) || lot.status}</strong></Link>)}</div>
        </DataState>
        <Link className="text-link" to="/offers">{t('fpoOffers')}</Link>
      </section>

      <section className="panel form-stack"><h2>{t('fpoTrades')}</h2>
        <DataState loading={trades.loading} error={trades.error} empty={trades.data.length ? false : t('fpoNoTrades')} onRetry={trades.retry}>
          <div className="list-stack">{trades.data.map((trade) => <article className="panel" key={trade.id}>
            <h3>{cropT(trade.crop)} · {trade.trade_reference}</h3><p>{t(`status_${trade.status}`) || trade.status} · {trade.gross}</p>
            <Link className="button secondary" to={`/trades/${trade.id}`}>{t('fpoTradeRoom')}</Link>
            <button className="text-link" type="button" onClick={async () => { const result = await getFPOTradeTrace(trade.id); if (result.success) setTrace({ ...trace, [trade.id]: result.data }); else setError(t('fpoErrorLoad')); }}>{t('fpoTradeTrace')}</button>
            {trace[trade.id] && <div aria-label={t('fpoProjectedAllocation')}><h4>{t('fpoProjectedAllocation')} · {trace[trade.id].quantity_qtl} {t('quintal')} · {trace[trade.id].gross}</h4>
              <ul>{trace[trade.id].allocations.map((allocation) => <li key={allocation.contribution_id}>{allocation.member_name} · {allocation.intake_receipt_id} · {allocation.sold_quantity_qtl} {t('quintal')} · {allocation.gross_allocation}</li>)}</ul>
            </div>}
          </article>)}</div>
        </DataState>
      </section>
    </>
  );
}
