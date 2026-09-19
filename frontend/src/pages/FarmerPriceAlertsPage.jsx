import { useRef, useState } from 'react';
import { Bell, BellOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { createOperationKey, createPriceAlert, disablePriceAlert, getCrops, getMarkets, getPriceAlerts } from '../services/api';
import { Button, DataState, Field, Notice, PageHeading, useResource } from '../components/Experience';

export default function FarmerPriceAlertsPage() {
  const { user } = useAuth();
  const { t, cropT, money } = useLanguage();
  const crops = useResource(getCrops);
  const markets = useResource(() => getMarkets({ limit: 100 }));
  const alerts = useResource(getPriceAlerts, [user.id]);
  const [cropId, setCropId] = useState('');
  const [marketId, setMarketId] = useState('');
  const [threshold, setThreshold] = useState('');
  const [direction, setDirection] = useState('AT_OR_ABOVE');
  const [saving, setSaving] = useState(false);
  const [disabling, setDisabling] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const submission = useRef({ signature: '', key: '' });

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    setError('');
    const payload = {
      crop_id: cropId,
      market_id: marketId,
      threshold,
      direction,
      unit: 'INR/quintal',
    };
    const signature = JSON.stringify(payload);
    if (submission.current.signature !== signature) {
      submission.current = { signature, key: createOperationKey() };
    }
    const result = await createPriceAlert(payload, submission.current.key);
    setSaving(false);
    if (!result?.success) {
      setError(result?.message || t('priceAlertSaveError'));
      return;
    }
    setNotice(t('priceAlertSaved'));
    setThreshold('');
    submission.current = { signature: '', key: '' };
    alerts.retry();
  }

  async function disable(id) {
    setDisabling(id);
    setError('');
    const result = await disablePriceAlert(id);
    setDisabling('');
    if (!result?.success) {
      setError(result?.message || t('priceAlertSaveError'));
      return;
    }
    alerts.retry();
  }

  return (
    <div className="site-container page-section farmer-alerts-page">
      <PageHeading title={t('priceAlerts')} description={t('priceAlertsIntro')} />
      <Notice>{t('priceAlertTruth')}</Notice>
      {notice && <Notice role="status">{notice}</Notice>}
      {error && <Notice role="alert" error>{error}</Notice>}

      <section className="panel" aria-labelledby="price-alert-form-title">
        <h2 id="price-alert-form-title"><Bell size={20} aria-hidden="true" /> {t('createPriceAlert')}</h2>
        <p className="muted">{t('priceAlertThresholdHelp')}</p>
        <form className="form-grid" onSubmit={submit}>
          <Field as="select" label={t('crop')} value={cropId} onChange={(event) => setCropId(event.target.value)} disabled={saving} required>
            <option value="">{t('selectCrop')}</option>
            {crops.data.map((crop) => <option key={crop.id} value={crop.id}>{cropT(crop.name)}</option>)}
          </Field>
          <Field as="select" label={t('market')} value={marketId} onChange={(event) => setMarketId(event.target.value)} disabled={saving} required>
            <option value="">{t('selectMarket')}</option>
            {markets.data.map((market) => <option key={market.id} value={market.id}>{market.name}{market.district ? ` · ${market.district}` : ''}</option>)}
          </Field>
          <Field
            type="number"
            label={t('priceAlertThreshold')}
            hint={t('priceAlertUnit')}
            value={threshold}
            onChange={(event) => setThreshold(event.target.value)}
            disabled={saving}
            min="0.01"
            step="0.01"
            inputMode="decimal"
            required
          />
          <Field as="select" label={t('priceAlertWhen')} value={direction} onChange={(event) => setDirection(event.target.value)} disabled={saving}>
            <option value="AT_OR_ABOVE">{t('priceAlertAbove')}</option>
            <option value="AT_OR_BELOW">{t('priceAlertBelow')}</option>
          </Field>
          <div className="form-actions">
            <Button type="submit" size="large" loading={saving} disabled={crops.loading || markets.loading || !cropId || !marketId || !threshold}>
              {t('savePriceAlert')}
            </Button>
          </div>
        </form>
      </section>

      <section className="panel" aria-labelledby="price-alert-list-title">
        <h2 id="price-alert-list-title">{t('yourPriceAlerts')}</h2>
        <DataState loading={alerts.loading} error={alerts.error} empty={!alerts.data.length && !alerts.loading ? t('noPriceAlerts') : false} onRetry={alerts.retry}>
          <div className="list-stack">
            {alerts.data.map((alert) => (
              <article className="panel notification-row" key={alert.id}>
                <Bell size={20} aria-hidden="true" />
                <div className="notification-copy">
                  <strong>{cropT(alert.crop || '')} · {alert.market}</strong>
                  <span>{alert.direction === 'AT_OR_ABOVE' ? t('priceAlertAbove') : t('priceAlertBelow')} {money(alert.threshold)} / {t('quintal')}</span>
                  <small>{alert.is_active ? (alert.is_armed ? t('priceAlertArmed') : t('priceAlertWaitingRearm')) : t('priceAlertDisabled')}</small>
                </div>
                {alert.is_active && <Button variant="secondary" loading={disabling === alert.id} onClick={() => disable(alert.id)} aria-label={`${t('disablePriceAlert')} ${cropT(alert.crop || '')} ${alert.market}`}><BellOff size={16} aria-hidden="true" /> {t('disablePriceAlert')}</Button>}
              </article>
            ))}
          </div>
        </DataState>
      </section>
    </div>
  );
}
