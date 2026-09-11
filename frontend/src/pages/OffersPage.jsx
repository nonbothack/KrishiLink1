import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { IndianRupee, CheckCircle2, XCircle, Eye, Clock } from 'lucide-react';
import { getOffers, acceptOffer, rejectOffer } from '../services/api';
import { StatusBadge } from '../components/Badges';
import { LoadingState, EmptyState } from '../components/States';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { ToastContainer } from '../components/ui/Toast';

export default function OffersPage() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const isBuyer = user?.role === 'buyer';
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState(null);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'error') => {
    const id = Date.now().toString();
    setToasts(p => [...p, { id, message, type, title: type === 'error' ? 'Error' : 'Notification' }]);
  };
  const removeToast = (id) => setToasts(p => p.filter(t => t.id !== id));

  const loadOffers = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await getOffers();
    if (res && res.success && Array.isArray(res.data)) {
      setOffers(res.data);
    } else if (res && !res.success) {
      setError(res.error || 'Failed to load offers');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadOffers();
  }, [loadOffers]);

  async function handleAccept(id) {
    setUpdatingId(id);
    const res = await acceptOffer(id);
    if (res && res.success) {
      setOffers(prev => prev.map(o => o.id === id ? { ...o, status: 'ACCEPTED' } : o));
      addToast('Offer accepted! Deal order created and SMS confirmation sent.', 'success');
    } else {
      addToast(res?.error || 'Failed to accept offer', 'error');
    }
    setUpdatingId(null);
  }

  async function handleReject(id) {
    setUpdatingId(id);
    const res = await rejectOffer(id);
    if (res && res.success) {
      setOffers(prev => prev.map(o => o.id === id ? { ...o, status: 'REJECTED' } : o));
    } else {
      addToast(res?.error || 'Failed to decline offer', 'error');
    }
    setUpdatingId(null);
  }

  const normStatus = (s) => (s || '').toLowerCase();
  const filtered = filter === 'all' ? offers : offers.filter(o => normStatus(o.status) === filter);

  const getTabLabel = (val) => {
    if (val === 'all') return t('all') || 'All';
    if (val === 'pending') return t('pending') || 'Pending';
    if (val === 'accepted') return t('accepted') || 'Accepted';
    if (val === 'rejected') return t('rejected') || 'Rejected';
    return val;
  };

  const tabs = [
    { label: getTabLabel('all'), value: 'all', count: offers.length },
    { label: getTabLabel('pending'), value: 'pending', count: offers.filter(o => normStatus(o.status) === 'pending').length },
    { label: getTabLabel('accepted'), value: 'accepted', count: offers.filter(o => normStatus(o.status) === 'accepted').length },
    { label: getTabLabel('rejected'), value: 'rejected', count: offers.filter(o => normStatus(o.status) === 'rejected').length },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isBuyer ? (t('myOffers') || 'My Offers & Proposals') : (t('offers') || 'Offers & Negotiations')}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {isBuyer
              ? 'Track proposals and offers you sent to farmers'
              : 'Review incoming buyer offers and manage negotiations'}
          </p>
        </div>
        <button
          onClick={loadOffers}
          disabled={loading}
          className="btn-secondary btn-sm"
        >
          {loading ? 'Refreshing...' : 'Refresh Offers'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {tabs.map(tab => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              filter === tab.value
                ? 'bg-green-800 text-white shadow-sm'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-green-300'
            }`}
          >
            {tab.label}
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
              filter === tab.value ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
            }`}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <EmptyState
          title={isBuyer ? 'No offers placed yet' : 'No offers in this category'}
          description={
            isBuyer
              ? 'Browse produce in the Marketplace and click "Make Offer" to start negotiating with farmers.'
              : 'When buyers make offers on your listings, they will appear here.'
          }
          action={
            isBuyer ? (
              <Link to="/buyer/dashboard" className="btn-primary btn-sm">
                {t('browseMarketplace') || 'Explore Marketplace'}
              </Link>
            ) : (
              <Link to="/sell" className="btn-primary btn-sm">
                {t('createListing') || 'Create a Listing'}
              </Link>
            )
          }
        />
      ) : (
        <div className="space-y-4">
          {filtered.map(offer => {
            const price = offer.price_per_unit || offer.offered_price || 0;
            const total = offer.total_value || (price * (offer.quantity || 0));
            const status = normStatus(offer.status);

            return (
              <div key={offer.id} className="card hover:shadow-md transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Left: Offer details */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h3 className="font-bold text-gray-900">
                        {isBuyer
                          ? `Offer to: ${offer.farmer_name || 'Farmer'}${offer.lot_public_id ? ` · Lot ${offer.lot_public_id}` : ''}`
                          : `Offer from: ${offer.buyer_name || 'Buyer'}${offer.lot_public_id ? ` · Lot ${offer.lot_public_id}` : ''}`}
                      </h3>
                      <StatusBadge status={offer.status} />
                    </div>
                    <p className="text-sm text-gray-600">
                      {cropT(offer.crop_name || offer.crop) || 'Produce'} · {offer.quantity} {t('quintal') || 'quintals'}
                      {offer.location ? ` · ${offer.location}` : ''}
                    </p>

                    {/* Price breakdown */}
                    <div className="flex items-center gap-4 mt-3 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <IndianRupee className="w-4 h-4 text-green-600" />
                        <span className="font-bold text-green-800 text-lg">
                          ₹{Number(price).toLocaleString('en-IN')}
                        </span>
                        <span className="text-gray-400 text-sm">{t('perQuintal') || 'per quintal'}</span>
                      </div>
                      <div className="text-sm text-gray-500">
                        {t('totalAmount') || 'Total'}: <span className="font-semibold text-gray-800">₹{Number(total).toLocaleString('en-IN')}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-2">
                      <Clock className="w-3.5 h-3.5" />
                      {isBuyer ? 'Sent ' : 'Received '}
                      {offer.created_at ? new Date(offer.created_at).toLocaleDateString('en-IN') : 'recently'}
                      {offer.expires_at && ` · Expires ${new Date(offer.expires_at).toLocaleDateString('en-IN')}`}
                    </div>
                  </div>

                  {/* Right: Actions */}
                  {status === 'pending' && !isBuyer && (
                    <div className="flex flex-col gap-2 min-w-fit">
                      <button
                        onClick={() => handleAccept(offer.id)}
                        disabled={updatingId === offer.id}
                        className="btn-primary btn-sm flex items-center gap-2 disabled:opacity-60"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        {t('accept') || 'Accept Offer'}
                      </button>
                      <button
                        onClick={() => handleReject(offer.id)}
                        disabled={updatingId === offer.id}
                        className="btn-secondary btn-sm flex items-center gap-2 text-red-600 border-red-200 hover:bg-red-50 disabled:opacity-60"
                      >
                        <XCircle className="w-4 h-4" />
                        {t('reject') || 'Decline'}
                      </button>
                    </div>
                  )}

                  {status === 'pending' && isBuyer && (
                    <div className="min-w-fit">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold">
                        <Clock className="w-3.5 h-3.5" />
                        Awaiting Farmer Response
                      </span>
                    </div>
                  )}

                  {status === 'accepted' && (
                    <Link to="/transactions" className="btn-secondary btn-sm flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      {t('viewTransaction') || 'View Order'}
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}

