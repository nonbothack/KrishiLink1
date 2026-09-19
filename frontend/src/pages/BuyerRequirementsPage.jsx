import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { closeRequirement, createRequirement, getCrops, getRequirements } from '../services/api';
import { DataState, Field, Notice, PageHeading, useResource } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';

export default function BuyerRequirementsPage() {
  const { t, cropT, money } = useLanguage();
  const requirements = useResource(getRequirements);
  const crops = useResource(() => getCrops({ limit: 100 }));
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ crop_id: '', quantity: '', unit: 'quintal', target_price: '', location_text: '', required_until: '', allow_partial: true });
  const selectedCrop = useMemo(() => crops.data.find((crop) => crop.id === form.crop_id), [crops.data, form.crop_id]);
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  async function save(event) {
    event.preventDefault(); setSaving(true); setError('');
    const result = await createRequirement({ ...form, quantity: String(form.quantity), target_price: form.target_price || null, location_text: form.location_text || null, required_until: form.required_until || null, status: 'ACTIVE' });
    setSaving(false);
    if (!result.success) return setError(result.error || 'server');
    setEditing(false); setForm({ crop_id: '', quantity: '', unit: 'quintal', target_price: '', location_text: '', required_until: '', allow_partial: true }); requirements.retry();
  }
  async function close(id) { await closeRequirement(id); requirements.retry(); }
  return <>
    <PageHeading title={t('buyerRequirements')} description={t('buyerRequirementsIntro')} action={<button className="button" onClick={() => setEditing(true)}>{t('createRequirement')}</button>} />
    {editing && <form className="panel form-stack" onSubmit={save}>
      <h2>{t('createRequirement')}</h2>
      <Field label={t('crop')} as="select" value={form.crop_id} onChange={(event) => { set('crop_id', event.target.value); set('unit', 'quintal'); }} required>
        <option value="">{t('selectCrop')}</option>{crops.data.map((crop) => <option key={crop.id} value={crop.id}>{cropT(crop.name)}</option>)}
      </Field>
      <div className="form-grid"><Field label={t('requestedQuantity')} type="number" inputMode="decimal" min="0.01" step="0.01" value={form.quantity} onChange={(event) => set('quantity', event.target.value)} required /><Field label={t('unit')} as="select" value={form.unit} onChange={(event) => set('unit', event.target.value)}>{(selectedCrop?.valid_units || ['quintal']).map((unit) => <option key={unit}>{unit}</option>)}</Field></div>
      <Field label={t('priceCeilingOptional')} type="number" inputMode="decimal" min="0.01" step="0.01" value={form.target_price} onChange={(event) => set('target_price', event.target.value)} />
      <div className="form-grid"><Field label={t('procurementLocation')} value={form.location_text} onChange={(event) => set('location_text', event.target.value)} /><Field label={t('requiredBy')} type="date" value={form.required_until} onChange={(event) => set('required_until', event.target.value)} /></div>
      <label className="check-row"><input type="checkbox" checked={form.allow_partial} onChange={(event) => set('allow_partial', event.target.checked)} /> {t('allowPartial')}</label>
      {error && <Notice error>{t(error)}</Notice>}<div className="form-actions"><button type="button" className="button secondary" onClick={() => setEditing(false)}>{t('cancel')}</button><button className="button" disabled={saving}>{t(saving ? 'loading' : 'publishRequirement')}</button></div>
    </form>}
    <DataState loading={requirements.loading} error={requirements.error} empty={!requirements.data.length ? t('noRequirements') : false} onRetry={requirements.retry}><div className="list-stack">{requirements.data.map((requirement) => <article className="panel listing-row" key={requirement.id}><div><span className="status-pill">{t('status_' + requirement.status, requirement.status)}</span><h3>{cropT(requirement.crop)}</h3><p>{t('requested')}: {requirement.requested_quantity} {t(requirement.requested_unit)}</p><p>{t('committed')}: {requirement.committed_quantity} · {t('remaining')}: {requirement.remaining_quantity} {t('quintal')}</p>{requirement.target_price && <p>{t('priceCeiling')}: {money(requirement.target_price)} / {t('quintal')}</p>}</div><div><Link className="button secondary" to={`/buyer/discover?requirement=${requirement.id}`}>{t('discoverSupply')}</Link>{['ACTIVE', 'PARTIALLY_FILLED'].includes(requirement.status) && <button className="text-link" onClick={() => close(requirement.id)}>{t('closeRequirement')}</button>}</div></article>)}</div></DataState>
  </>;
}
