import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Star, MapPin, CheckCircle2, Info } from 'lucide-react';
import { getMatches, createOffer } from '../services/api';
import { VerifiedBadge } from '../components/Badges';
import { LoadingState, EmptyState } from '../components/States';
import { getCropImage } from '../utils/cropImages';
import { useLanguage } from '../hooks/useLanguage';

// Individual match card
function MatchCard({ buyer, onMakeOffer, t, cropT }) {
  const [offering, setOffering] = useState(false);
  const [offered, setOffered] = useState(false);

  const labelColor = buyer.label === 'Excellent' ? 'badge-green'
    : buyer.label === 'Good' ? 'badge-blue'
    : 'badge-yellow';

  const handleOffer = async () => {
    setOffering(true);
    await createOffer({
      buyer_id: buyer.id,
      crop: buyer.crops[0],
      offered_price: buyer.offer_price,
      quantity: 100,
    });
    setOffering(false);
    setOffered(true);
    if (onMakeOffer) onMakeOffer(buyer);
  };

  return (
    <div className="card border-2 border-transparent hover:border-green-200 transition-all">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-bold text-gray-900">{buyer.name}</h3>
            {buyer.verified && <VerifiedBadge />}
          </div>
          <p className="text-sm text-gray-500">{buyer.type}</p>
          <div className="flex items-center gap-3 mt-1.5 flex-wrap">
            <span className="flex items-center gap-1 text-xs text-amber-600">
              <Star className="w-3.5 h-3.5 fill-amber-500 stroke-amber-500" />
              {buyer.rating} ({buyer.reviews} reviews)
            </span>
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <MapPin className="w-3.5 h-3.5" />
              {buyer.location} · {buyer.distance_km} km
            </span>
          </div>
        </div>

        {/* Score */}
        <div className="text-center flex-shrink-0">
          <div className="w-14 h-14 rounded-full border-4 border-green-200 flex items-center justify-center bg-green-50">
            <span className="text-lg font-bold text-green-800">{buyer.score}</span>
          </div>
          <span className={`${labelColor} mt-1 block`}>{buyer.label}</span>
        </div>
      </div>

      {/* Match details */}
      <div className="bg-gray-50 rounded-xl p-3 mb-4">
        <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
          <Info className="w-3.5 h-3.5" /> Why this match?
        </p>
        <div className="space-y-1">
          {buyer.reasons?.map((r, i) => (
            <p key={i} className="text-xs text-gray-700 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
              {r}
            </p>
          ))}
        </div>
      </div>

      {/* Price + quantity */}
      <div className="grid grid-cols-3 gap-3 mb-4 text-center">
        <div className="bg-green-50 rounded-xl p-2">
          <p className="text-xs text-gray-500">{t('offerPrice') || 'Offer Price'}</p>
          <p className="font-bold text-green-800 text-sm">₹{buyer.offer_price.toLocaleString('en-IN')}</p>
          <p className="text-xs text-gray-400">/qtl</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-2">
          <p className="text-xs text-gray-500">Min Qty</p>
          <p className="font-bold text-gray-800 text-sm">{buyer.min_qty}</p>
          <p className="text-xs text-gray-400">{t('quintal') || 'quintals'}</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-2">
          <p className="text-xs text-gray-500">Max Qty</p>
          <p className="font-bold text-gray-800 text-sm">{buyer.max_qty}</p>
          <p className="text-xs text-gray-400">{t('quintal') || 'quintals'}</p>
        </div>
      </div>

      {/* Crops */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {buyer.crops.map(c => (
          <span key={c} className="badge-green text-xs">{cropT(c)}</span>
        ))}
      </div>

      {/* Action button */}
      {offered ? (
        <div className="flex items-center gap-2 justify-center py-3 text-green-700 font-semibold text-sm bg-green-50 rounded-xl">
          <CheckCircle2 className="w-5 h-5" />
          Offer Sent! Buyer will respond shortly.
        </div>
      ) : (
        <button
          onClick={handleOffer}
          disabled={offering}
          className="btn-primary w-full disabled:opacity-60"
        >
          {offering ? 'Sending Offer...' : (t('makeOffer') || 'Make an Offer')}
        </button>
      )}
    </div>
  );
}

export default function MatchesPage() {
  const { t, cropT } = useLanguage();
  const location = useLocation();
  const lotFromState = location.state?.lot;

  const [lot, setLot] = useState(lotFromState || {
    crop: 'Onion',
    quantity: 500,
    grade: 'A',
    location: 'Lasalgaon',
  });
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  // Quick form to customize search if no lot was passed
  const [editMode, setEditMode] = useState(!lotFromState);

  const loadMatches = useCallback(async () => {
    setLoading(true);
    const res = await getMatches(lot);
    if (res.success) setMatches(res.data);
    setLoading(false);
  }, [lot]);

  useEffect(() => {
    if (!editMode) loadMatches();
  }, [editMode, loadMatches]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('buyerMatches') || 'Buyer Matches'}</h1>
        <p className="text-gray-500 text-sm mt-1">
          Rule-based matching — buyers are ranked by crop, grade, quantity, and distance. Not AI.
        </p>
      </div>

      {/* Current lot summary */}
      <div className="card bg-green-50 border border-green-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <img
              src={getCropImage(lot.crop)}
              alt={lot.crop}
              className="w-11 h-11 rounded-xl object-cover border border-green-300 shadow-2xs flex-shrink-0"
            />
            <div>
              <p className="font-bold text-gray-900">
                {lot.quantity} {lot.unit || t('quintal') || 'Quintal'} · {cropT(lot.crop)} · Grade {lot.grade}
              </p>
              <p className="text-sm text-gray-600 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {lot.location}
                {lot.expected_price && ` · Expected: ₹${parseInt(lot.expected_price).toLocaleString('en-IN')}/qtl`}
              </p>
            </div>
          </div>
          <button
            onClick={() => setEditMode(!editMode)}
            className="btn-secondary btn-sm text-sm"
          >
            {editMode ? (t('search') || 'Search') : 'Change Details'}
          </button>
        </div>

        {/* Quick edit form */}
        {editMode && (
          <div className="mt-4 pt-4 border-t border-green-200 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="label text-xs">{t('crop') || 'Crop'}</label>
              <select className="input text-sm" value={lot.crop} onChange={(e) => setLot(p => ({ ...p, crop: e.target.value }))}>
                {['Onion', 'Tomato', 'Soybean', 'Cotton', 'Wheat'].map(c => <option key={c} value={c}>{cropT(c)}</option>)}
              </select>
            </div>
            <div>
              <label className="label text-xs">{t('quantity') || 'Quantity'} (qtl)</label>
              <input type="number" className="input text-sm" value={lot.quantity} onChange={(e) => setLot(p => ({ ...p, quantity: e.target.value }))} />
            </div>
            <div>
              <label className="label text-xs">{t('grade') || 'Grade'}</label>
              <select className="input text-sm" value={lot.grade} onChange={(e) => setLot(p => ({ ...p, grade: e.target.value }))}>
                {['A', 'B', 'C'].map(g => <option key={g} value={g}>Grade {g}</option>)}
              </select>
            </div>
            <div>
              <label className="label text-xs">{t('location') || 'Location'}</label>
              <input type="text" className="input text-sm" value={lot.location} onChange={(e) => setLot(p => ({ ...p, location: e.target.value }))} />
            </div>
          </div>
        )}
      </div>

      {/* Match info */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800 flex items-start gap-2">
        <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <span>
          Matches are calculated using a 100-point scoring system: <strong>Crop (40)</strong> + <strong>Grade (25)</strong> + <strong>Quantity (20)</strong> + <strong>Distance (15)</strong>. This is rule-based logic — not machine learning.
        </span>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingState message="Finding matching buyers..." />
      ) : matches.length === 0 ? (
        <EmptyState
          title="No buyers found"
          description="Try changing your crop or grade. More buyers join regularly."
        />
      ) : (
        <>
          <p className="text-sm text-gray-500">{matches.length} buyers found</p>
          <div className="grid sm:grid-cols-2 gap-5">
            {matches.map(buyer => (
              <MatchCard
                key={buyer.id}
                buyer={buyer}
                t={t}
                cropT={cropT}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

