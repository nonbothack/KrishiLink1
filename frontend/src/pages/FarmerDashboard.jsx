import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Bell, MapPin, Sprout } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import {
  getCrops,
  getLivePrices,
  getMarkets,
  getMyLots,
  getMyProfile,
  getNotifications,
  getOffers,
  getTransactions,
  saveMyLocation,
} from '../services/api';
import { DataState, Notice, useResource } from '../components/Experience';
import { dateLabel } from '../lib/produce';
import { savedSnapshotLabel } from '../lib/offlinePresentation';

const safeRead = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
};

export default function FarmerDashboard() {
  const { user } = useAuth();
  const { t, cropT, money, greeting, language } = useLanguage();
  const [selectedCropIds, setSelectedCropIds] = useState(() => safeRead(`farmer-crops-${user.id}`, []));
  const [locationBusy, setLocationBusy] = useState(false);
  const [locationError, setLocationError] = useState('');
  const [coordinates, setCoordinates] = useState(null);
  const [now, setNow] = useState(Date.now());
  const crops = useResource(getCrops);
  const profile = useResource(getMyProfile, [user.id]);
  const lots = useResource(getMyLots, [user.id]);
  const offers = useResource(getOffers, [user.id]);
  const trades = useResource(getTransactions, [user.id]);
  const notifications = useResource(getNotifications, [user.id]);
  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const preferenceCrop = useMemo(
    () => [...selectedCropIds].reverse().map((id) => crops.data.find((crop) => crop.id === id)).find(Boolean),
    [crops.data, selectedCropIds],
  );
  const activeCrop = preferenceCrop || crops.data.find((crop) =>
    lots.data.some((lot) => lot.crop_id === crop.id),
  );
  const contextDistrict = profile.data?.district || profile.data?.data?.district || '';
  const price = useResource(
    () => activeCrop
      ? getLivePrices({ crop: activeCrop.name, district: contextDistrict, limit: 100 })
      : Promise.resolve({ success: true, data: [] }),
    [activeCrop?.id, contextDistrict],
  );
  const latestPrice = price.data.find((item) => item.unit === 'INR/quintal');
  const nearby = useResource(
    () => coordinates && coordinates.accuracy_m <= 1000
      ? getMarkets({ near_lat: coordinates.latitude, near_lng: coordinates.longitude, radius_km: 50, limit: 10 })
      : Promise.resolve({ success: true, data: [] }),
    [coordinates?.latitude, coordinates?.longitude],
  );
  const nearbyPrices = useResource(
    () => activeCrop && coordinates && coordinates.accuracy_m <= 1000
      ? getLivePrices({ crop: activeCrop.name, limit: 100 })
      : Promise.resolve({ success: true, data: [] }),
    [activeCrop?.id, coordinates?.latitude, coordinates?.longitude],
  );
  const verifiedMarkets = new Map(nearby.data
    .filter((market) => market.distance_km <= 50 && market.verification_status === 'verified' && Number(market.coordinate_confidence) >= 0.85)
    .map((market) => [market.name.toLocaleLowerCase(), market]));
  const comparableNearby = latestPrice && latestPrice.freshness_state !== 'stale'
    ? nearbyPrices.data
      .filter((item) => {
        const market = verifiedMarkets.get(String(item.market || '').toLocaleLowerCase());
        return Boolean(market && item.unit === 'INR/quintal' && item.location_verified === true
          && item.freshness_state !== 'stale' && item.price_date === latestPrice.price_date
          && Number(item.modal_price) >= Number(latestPrice.modal_price) * 1.05);
      })
      .map((item) => ({ ...item, distance_km: verifiedMarkets.get(String(item.market).toLocaleLowerCase()).distance_km }))
      .sort((a, b) => Number(b.modal_price) - Number(a.modal_price) || Number(a.distance_km) - Number(b.distance_km))[0]
    : null;

  const pendingOffers = offers.data
    .filter((offer) => String(offer.status).toUpperCase() === 'PENDING' && (!offer.expires_at || Date.parse(offer.expires_at) > now))
    .sort((a, b) => (Date.parse(a.expires_at || '') || Infinity) - (Date.parse(b.expires_at || '') || Infinity));
  const openTrades = trades.data.filter((trade) => !['COMPLETED', 'CANCELLED', 'REFUNDED'].includes(String(trade.status).toUpperCase()));
  const urgentOffer = pendingOffers[0];
  const offerExpiring = Boolean(urgentOffer?.expires_at && Date.parse(urgentOffer.expires_at) - now <= 3 * 60 * 60 * 1000);
  const unreadCount = notifications.data.filter((item) => !item.is_read).length;
  const supportUpdate = notifications.data.find((item) => !item.is_read && /grievance|dispute_update/i.test(item.type || ''));
  const newTrade = openTrades.find((trade) => String(trade.status).toUpperCase() === 'CREATED');
  const locationName = [contextDistrict, profile.data?.state || profile.data?.data?.state]
    .filter(Boolean)
    .join(', ');

  function toggleCrop(id) {
    setSelectedCropIds((current) => {
      const next = current.includes(id) ? current.filter((value) => value !== id) : [...current, id].slice(-3);
      localStorage.setItem(`farmer-crops-${user.id}`, JSON.stringify(next));
      return next;
    });
  }

  function useLocation() {
    setLocationError('');
    if (!navigator.geolocation) {
      setLocationError('locationUnavailable');
      return;
    }
    setLocationBusy(true);
    navigator.geolocation.getCurrentPosition(async (position) => {
      const point = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy_m: position.coords.accuracy,
      };
      const saved = await saveMyLocation(point);
      setLocationBusy(false);
      if (!saved.success) {
        setLocationError(saved.error || 'server');
        return;
      }
      setCoordinates(point);
      profile.retry();
      nearby.retry();
    }, () => {
      setLocationBusy(false);
      setLocationError('locationPermission');
    }, { enableHighAccuracy: false, timeout: 12000, maximumAge: 60000 });
  }

  const urgentText = urgentOffer
    ? (offerExpiring ? t('offerExpiresSoon').replace('{quantity}', String(urgentOffer.quantity)).replace('{crop}', cropT(urgentOffer.crop_name)) : t('actionNewOffer').replace('{quantity}', String(urgentOffer.quantity)).replace('{crop}', cropT(urgentOffer.crop_name)))
    : '';
  const nextAction = urgentOffer
    ? { text: urgentText, href: `/offers?offer_id=${urgentOffer.id}`, label: 'viewOffers' }
      : supportUpdate
        ? { text: t('supportUpdateAction'), href: '/grievances', label: 'support' }
        : newTrade
          ? { text: t('tradeCreatedAction').replace('{crop}', cropT(newTrade.crop_name)), href: `/trades/${newTrade.id}`, label: 'openTrade' }
          : null;

  return (
    <div className="farmer-dashboard">
      <section className="farmer-first-view" aria-labelledby="farmer-greeting">
        <div className="farmer-greeting-row">
          <div>
            <p className="eyebrow">{greeting}</p>
            <h1 id="farmer-greeting">{user.name}</h1>
            <p className="farmer-location"><MapPin size={17} aria-hidden="true" />{locationName || t('locationNotSet')}</p>
          </div>
          {!coordinates && <button className="button secondary" onClick={useLocation} disabled={locationBusy}>{t(locationBusy ? 'loading' : 'useMyLocation')}</button>}
        </div>
        {locationError && <Notice error>{t(locationError)}</Notice>}

        <div className="farmer-first-grid">
          <section className="panel farmer-price-card" aria-labelledby="farmer-price-heading">
            <div className="farmer-card-label"><span>{t('reportedPrice')}</span><Link to="/prices">{t('allPrices')}</Link></div>
            {price.loading ? <p role="status">{t('loading')}</p> : price.error ? (
              <div><p>{t('priceLoadFailed')}</p><button className="text-link" onClick={price.retry}>{t('retry')}</button></div>
            ) : latestPrice ? (
              <>
                <h2 id="farmer-price-heading">{cropT(activeCrop?.name)}</h2>
                <strong className="farmer-price-number">{money(latestPrice.modal_price)} <small>/ {t('quintal')}</small></strong>
                <p>{latestPrice.market}{latestPrice.district ? ` · ${latestPrice.district}` : ''}</p>
                <p className="field-hint">{t('reportedOn')}: {dateLabel(latestPrice.price_date, language)} · {latestPrice.source} · {t(latestPrice.freshness_state || 'priceFreshnessUnknown')}</p>
                {latestPrice.location_verified === false && <p className="field-hint">{t('priceOutletUnverified')}</p>}
              </>
            ) : (
              <div><h2 id="farmer-price-heading">{activeCrop ? cropT(activeCrop.name) : t('reportedPrice')}</h2><p>{activeCrop ? t('noRecentCropPrice') : t('chooseCropForPrice')}</p></div>
            )}
            {price.offline_cache && <p className="offline-cache-note" role="status">{savedSnapshotLabel(t, price.cached_at, language)}</p>}
          </section>

          <section className="panel farmer-action-card" aria-labelledby="farmer-action-heading">
            <div className="farmer-card-label"><span>{t('todayAction')}</span>{unreadCount > 0 && <Bell size={17} aria-label={t('unreadNotifications').replace('{count}', String(unreadCount))} />}</div>
            {nextAction ? (
              <h2 id="farmer-action-heading"><Link className="farmer-action-link" to={nextAction.href} aria-label={`${nextAction.text} ${t(nextAction.label)}`}>{nextAction.text}<ArrowRight size={18} aria-hidden="true" /></Link></h2>
            ) : <h2 id="farmer-action-heading">{offers.error ? t('offersLoadFailed') : t('nothingUrgent')}</h2>}
            {!nextAction && offers.error && <button className="text-link" onClick={offers.retry}>{t('retry')}</button>}
          </section>
        </div>

        <div className="farmer-primary-actions">
          <Link className="button farmer-sell-button" to="/sell">{t('sellProduce')}<ArrowRight size={20} /></Link>
          <Link className="text-link" to="/offers">{t('viewOffers')}</Link>
        </div>
      </section>

      {!activeCrop && lots.data.length === 0 && (
        <section className="farmer-onboarding panel" aria-labelledby="crop-preferences-title">
          <h2 id="crop-preferences-title">{t('whichCrops')}</h2>
          <p>{t('cropPreferenceNote')}</p>
          <DataState loading={crops.loading} error={crops.error} empty={!crops.loading && !crops.error && !crops.data.length ? t('cropRegistryEmpty') : false} onRetry={crops.retry}>
            <div className="crop-choice-grid">
              {crops.data.slice(0, 8).map((crop) => (
                <button className={`crop-choice ${selectedCropIds.includes(crop.id) ? 'selected' : ''}`} key={crop.id} type="button" aria-pressed={selectedCropIds.includes(crop.id)} onClick={() => toggleCrop(crop.id)}>
                  <Sprout size={22} aria-hidden="true" />
                  <span>{language === 'hi' ? crop.name_hindi || crop.name : language === 'mr' ? crop.name_marathi || crop.name : crop.name_en || crop.name}</span>
                </button>
              ))}
            </div>
          </DataState>
          <Link className="text-link" to="/prices">{t('checkPrices')}</Link>
        </section>
      )}

      {coordinates && activeCrop && (
        <section className="panel farmer-nearby" aria-labelledby="nearby-title">
          <h2 id="nearby-title">{t('nearbyComparison')}</h2>
          {coordinates.accuracy_m > 1000 ? <p>{t('locationAccuracyLow')}</p> : nearby.loading || nearbyPrices.loading ? <p role="status">{t('loading')}</p> : nearby.error || nearbyPrices.error ? <p>{t('nearbyUnavailable')}</p> : comparableNearby ? (
            <p>{comparableNearby.market} · {money(comparableNearby.modal_price)} / {t('quintal')} · {t('reportedOn')} {dateLabel(comparableNearby.price_date, language)} · {t('approxDistance')} {comparableNearby.distance_km} km. {t('travelNotIncluded')}</p>
          ) : <p>{latestPrice && latestPrice.freshness_state !== 'stale' ? t('nearbyNoBetterPrice') : t('nearbyUnavailable')}</p>}
        </section>
      )}

      <section className="farmer-below-fold">
        <div className="section-heading"><h2>{t('myLots')}</h2><Link className="text-link" to="/farmer/lots">{t('viewAllLots')}</Link></div>
        <DataState loading={lots.loading} error={lots.error} empty={!lots.data.length && !lots.loading ? t('noListings') : false} onRetry={lots.retry}>
          <div className="list-stack">{lots.data.slice(0, 4).map((lot) => {
            const trade = trades.data.find((item) => item.lot_id === lot.id);
            return <article className="panel listing-row" key={lot.id}>
              <div><span className="status-pill">{t(`status_${lot.status}`, lot.status)}</span><h3>{cropT(lot.crop)}</h3><p>{lot.original_quantity || lot.quantity} {t(lot.original_unit || lot.unit || 'quintal')} · {lot.location}</p></div>
              <Link className="button secondary" to={trade ? `/trades/${trade.id}` : `/farmer/lots/${lot.id}`}>{t(trade ? 'openTrade' : 'manageLot')}</Link>
            </article>;
          })}</div>
        </DataState>
        {openTrades.length > 0 && <><div className="section-heading"><h2>{t('activeTrades')}</h2></div><div className="list-stack">{openTrades.slice(0, 4).map((trade) => <article className="panel listing-row" key={trade.id}><div><span className="status-pill">{t(`status_${trade.status}`, trade.status)}</span><h3>{cropT(trade.crop_name)}</h3><p>{trade.quantity} {t(trade.unit || 'quintal')} · {money(trade.gross_value)} · {trade.public_id || trade.id}</p></div><Link className="button secondary" to={`/trades/${trade.id}`}>{t('openTrade')}</Link></article>)}</div></>}
        <div className="farmer-more-links">
          <Link to="/transactions">{t('orders')}</Link>
          <Link to="/farmer/more#notifications">{t('notifications')}</Link>
          <Link to="/grievances">{t('support')}</Link>
        </div>
      </section>
    </div>
  );
}
