// =============================================================
// Buyer Dashboard
// =============================================================

import { useState, useEffect } from 'react';
import { Search, ShoppingBag, FileText, CheckCircle2, TrendingUp, MapPin } from 'lucide-react';
import { getLots, createOffer } from '../services/api';
import { StatusBadge } from '../components/Badges';
import { LoadingState } from '../components/States';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { ToastContainer } from '../components/ui/Toast';
import Tilt3DCard from '../components/visual/Tilt3DCard';

function SummaryCard({ title, value, sub, icon: Icon, color }) {
  return (
    <Tilt3DCard className="h-full">
      <div className="card flex items-start gap-4 h-full">
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
        </div>
      </div>
    </Tilt3DCard>
  );
}

export default function BuyerDashboard() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const [lots, setLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [cropFilter, setCropFilter] = useState('All');
  const [offeringSent, setOfferingSent] = useState({});
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'error') => {
    const id = Date.now().toString();
    setToasts(p => [...p, { id, message, type, title: type === 'error' ? 'Error' : 'Notification' }]);
  };
  const removeToast = (id) => setToasts(p => p.filter(t => t.id !== id));

  const loadLots = async () => {
    setLoading(true);
    const res = await getLots(null, { limit: 100 });
    if (res && res.success && Array.isArray(res.data)) {
      setLots(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadLots();
  }, []);

  const lotList = Array.isArray(lots) ? lots : [];
  const filtered = lotList.filter(l => {
    if (!l) return false;
    const cropName = l.crop_name || l.crop || '';
    const loc = l.district || l.location_text || l.location || '';
    if (cropFilter !== 'All' && cropName.toLowerCase() !== cropFilter.toLowerCase()) return false;
    if (searchTerm && !cropName.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !loc.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    const s = (l.status || '').toLowerCase();
    return s === 'published' || s === 'active' || s === 'matched';
  });

  const knownCrops = ['All', 'Onion', 'Tomato', 'Soybean', 'Cotton', 'Wheat', 'Rice', 'Potato', 'Chilli'];
  const dynamicCrops = Array.from(new Set(lotList.map(l => l.crop_name || l.crop).filter(Boolean)));
  const filterOptions = Array.from(new Set([...knownCrops, ...dynamicCrops]));

  async function handleOffer(lot) {
    setOfferingSent(p => ({ ...p, [lot.id]: 'sending' }));
    const price = Number(lot.asking_price || lot.expected_price || 2000);
    const res = await createOffer({
      lot_id: lot.id,
      quantity: Number(lot.quantity) || 10,
      price_per_unit: Math.round(price * 0.98),
      message: `Offer from ${user?.name || 'Verified Buyer'}`
    });
    if (res && res.success) {
      setOfferingSent(p => ({ ...p, [lot.id]: 'sent' }));
      addToast('Offer sent! Track updates in the My Offers tab.', 'success');
    } else {
      addToast(res?.error || 'Could not send offer. Please try again.', 'error');
      setOfferingSent(p => ({ ...p, [lot.id]: null }));
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t('buyerMarketplace')}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {t('welcome')} {user?.name ? `${user.name.split(' ')[0]} — ` : ''}{t('buyerSubtitle')}
          </p>
        </div>
        <button
          onClick={loadLots}
          disabled={loading}
          className="btn-secondary btn-sm flex items-center gap-2"
        >
          {loading ? 'Refreshing...' : 'Refresh Listings'}
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title={t('availableLots')}
          value={lotList.filter(l => ['published', 'active'].includes((l?.status || '').toLowerCase())).length}
          sub={t('readyForSourcing')}
          icon={ShoppingBag}
          color="bg-blue-100 text-blue-700"
        />
        <SummaryCard title={t('verifiedMandis')} value="8" sub={t('directFarmGates')} icon={FileText} color="bg-amber-100 text-amber-700" />
        <SummaryCard title={t('avgQuality')} value="Grade A" sub={t('qualityVerified')} icon={CheckCircle2} color="bg-green-100 text-green-700" />
        <SummaryCard title={t('escrowSecurity')} value="100%" sub={t('disputeProtection')} icon={TrendingUp} color="bg-purple-100 text-purple-700" />
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              className="input pl-10"
              placeholder={t('searchCropOrLocation')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select className="input sm:w-44" value={cropFilter} onChange={(e) => setCropFilter(e.target.value)}>
            {filterOptions.map(c => (
              <option key={c} value={c}>{c === 'All' ? t('allCrops') : cropT(c)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Lot cards */}
      {loading ? <LoadingState message={t('loadingProduceLots')} /> : (
        <>
          <p className="text-sm text-gray-500">{filtered.length} {t('produceLotsAvailable')}</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map(lot => {
              const rawCropName = lot.crop_name || lot.crop || 'Produce';
              const price = Number(lot.asking_price || lot.expected_price || 0);
              const loc = lot.district || lot.location_text || lot.location || 'Maharashtra';
              const status = lot.status || 'PUBLISHED';

              return (
                <div key={lot.id} className="card-hover">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-gray-900 text-lg">{cropT(rawCropName)}</h3>
                      <p className="text-gray-500 text-xs mt-0.5 font-mono">{lot.public_id || `#${String(lot.id).slice(0, 8)}`}</p>
                    </div>
                    <StatusBadge status={status} />
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-gray-50 rounded-xl p-3">
                      <p className="text-xs text-gray-500">{t('quantity')}</p>
                      <p className="font-bold text-gray-900 mt-0.5">{lot.quantity} {lot.unit || 'qtl'}</p>
                    </div>
                    <div className="bg-green-50 rounded-xl p-3">
                      <p className="text-xs text-gray-500">{t('askingPrice')}</p>
                      <p className="font-bold text-green-800 mt-0.5">₹{price.toLocaleString('en-IN')}<span className="text-xs font-normal text-gray-400">/{t('quintal')}</span></p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 mb-4 text-sm">
                    <span className="badge-blue">{t('grade')} {lot.grade || 'A'}</span>
                    <span className="flex items-center gap-1 text-gray-500 truncate">
                      <MapPin className="w-3.5 h-3.5 flex-shrink-0" />{loc}
                    </span>
                  </div>

                  {offeringSent[lot.id] === 'sent' ? (
                    <div className="py-2.5 bg-green-50 text-green-700 font-semibold text-sm text-center rounded-xl flex items-center justify-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      {t('offerSent')}
                    </div>
                  ) : (
                    <button
                      onClick={() => handleOffer(lot)}
                      disabled={offeringSent[lot.id] === 'sending'}
                      className="btn-primary w-full disabled:opacity-60"
                    >
                      {offeringSent[lot.id] === 'sending' ? t('submittingOffer') : t('makeOffer')}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {filtered.length === 0 && (
            <div className="card text-center py-12">
              <p className="text-gray-500">{t('noLotsMatch')}</p>
            </div>
          )}
        </>
      )}

      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
