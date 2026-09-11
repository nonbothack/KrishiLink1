import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, CheckCircle2, ArrowRight, TrendingUp } from 'lucide-react';
import { createLot, getTrend } from '../services/api';
import { LIVE_GOVERNMENT_PRICES } from '../data/liveMandiData';
import { DEMO_PRICES } from '../data/demoData';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';

const CROPS = ['Onion', 'Tomato', 'Soybean', 'Cotton', 'Wheat', 'Rice', 'Potato', 'Chilli'];
const GRADES = [
  { value: 'A', label: 'Grade A — Premium quality, uniform size, no damage' },
  { value: 'B', label: 'Grade B — Good quality, minor variations acceptable' },
  { value: 'C', label: 'Grade C — Standard quality, some imperfections' },
];
const UNITS = ['Quintal', 'Kg', 'Tonne'];

export default function SellPage() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    crop: '',
    quantity: '',
    unit: 'Quintal',
    grade: '',
    location: user?.location || '',
    expected_price: '',
    available_date: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [createdLot, setCreatedLot] = useState(null);
  const [currentPriceInfo, setCurrentPriceInfo] = useState(null);
  const [, setPriceLoading] = useState(false);

  useEffect(() => {
    if (!formData.crop) {
      setCurrentPriceInfo(null);
      return;
    }

    let active = true;
    const cleanCrop = formData.crop.toLowerCase().replace(/soyabean/i, 'soybean');

    // Immediate baseline from verified dataset so price shows instantly with zero delay
    const govMatch = LIVE_GOVERNMENT_PRICES.find(
      p => p.crop.toLowerCase().replace(/soyabean/i, 'soybean') === cleanCrop
    );
    const demoMatch = DEMO_PRICES.find(
      p => p.crop.toLowerCase().replace(/soyabean/i, 'soybean') === cleanCrop
    );
    const initialMatch = govMatch || demoMatch;
    if (initialMatch) {
      setCurrentPriceInfo({
        price: initialMatch.modal_price,
        market: initialMatch.market,
      });
    }

    // Then asynchronously fetch live API price trend from backend /prices/trends/{crop}
    async function fetchLiveTrend() {
      setPriceLoading(true);
      try {
        const res = await getTrend(formData.crop);
        if (active && res && res.success && res.data && res.data.current_price) {
          setCurrentPriceInfo({
            price: res.data.current_price,
            market: res.data.market,
          });
        }
      } catch {
        // Fallback baseline remains active
      } finally {
        if (active) setPriceLoading(false);
      }
    }

    fetchLiveTrend();
    return () => {
      active = false;
    };
  }, [formData.crop]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.crop) { setError('Please select a crop.'); return; }
    if (!formData.grade) { setError('Please select a quality grade.'); return; }
    if (!formData.quantity || parseInt(formData.quantity) <= 0) {
      setError('Please enter a valid quantity.');
      return;
    }

    setLoading(true);
    setError('');

    const res = await createLot(formData);
    setLoading(false);

    if (res.success) {
      setCreatedLot({
        ...formData,
        ...res.data,
        expected_price: res.data?.expected_price ?? res.data?.asking_price ?? formData.expected_price,
        unit: res.data?.unit || formData.unit || 'Quintal',
        location: res.data?.location || res.data?.location_text || formData.location,
      });
      setSuccess(true);
    } else {
      setError(res.message);
    }
  };

  // Success screen
  if (success && createdLot) {
    const displayPrice = createdLot.expected_price || createdLot.asking_price;
    return (
      <div className="max-w-lg mx-auto px-4 py-12">
        <div className="card text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <CheckCircle2 className="w-9 h-9 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('lotCreated') || 'Lot Created!'}</h2>
          <p className="text-gray-500 mb-6">
            Your listing for <strong>{createdLot.quantity} {createdLot.unit || 'Quintal'} of {cropT(createdLot.crop)}</strong> has been created successfully.
          </p>

          <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">{t('crop') || 'Crop'}</span>
              <span className="font-semibold">{cropT(createdLot.crop)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('quantity') || 'Quantity'}</span>
              <span className="font-semibold">{createdLot.quantity} {createdLot.unit || 'Quintal'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('grade') || 'Grade'}</span>
              <span className="font-semibold">Grade {createdLot.grade}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('price') || 'Expected Price'}</span>
              <span className="font-semibold text-green-800">
                {displayPrice
                  ? `₹${Number(displayPrice).toLocaleString('en-IN')}/qtl`
                  : 'Market Rate'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('location') || 'Location'}</span>
              <span className="font-semibold">{createdLot.location || createdLot.location_text || '—'}</span>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={() => navigate('/matches', { state: { lot: createdLot } })}
              className="btn-primary flex items-center gap-2 justify-center"
            >
              {t('findBuyers') || 'Find Matching Buyers'}
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => {
                setSuccess(false);
                setFormData({ crop: '', quantity: '', unit: 'Quintal', grade: '', location: user?.location || '', expected_price: '', available_date: '', notes: '' });
                setCurrentPriceInfo(null);
              }}
              className="btn-secondary"
            >
              {t('createListing') || 'Create Another Listing'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
          <Package className="w-5 h-5 text-green-700" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('sellProduce') || 'Sell Your Produce'}</h1>
          <p className="text-gray-500 text-sm">Create a listing and we'll find matching buyers for you</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Crop */}
          <div>
            <label className="label">{t('crop') || 'Crop'} *</label>
            <select
              className="input"
              value={formData.crop}
              onChange={(e) => handleChange('crop', e.target.value)}
              required
            >
              <option value="">{t('selectCropPlaceholder') || 'Select your crop'}</option>
              {CROPS.map(c => <option key={c} value={c}>{cropT(c)}</option>)}
            </select>
          </div>

          {/* Quantity + Unit */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('quantity') || 'Quantity'} *</label>
              <input
                type="number"
                className="input"
                placeholder="e.g. 500"
                min="1"
                value={formData.quantity}
                onChange={(e) => handleChange('quantity', e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">{t('unit') || 'Unit'} *</label>
              <select
                className="input"
                value={formData.unit}
                onChange={(e) => handleChange('unit', e.target.value)}
              >
                {UNITS.map(u => <option key={u}>{u}</option>)}
              </select>
            </div>
          </div>

          {/* Grade */}
          <div>
            <label className="label">{t('grade') || 'Quality / Grade'} *</label>
            <div className="space-y-2">
              {GRADES.map(g => (
                <label
                  key={g.value}
                  className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                    formData.grade === g.value
                      ? 'border-green-600 bg-green-50'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="grade"
                    value={g.value}
                    checked={formData.grade === g.value}
                    onChange={() => handleChange('grade', g.value)}
                    className="mt-0.5 accent-green-700"
                  />
                  <div>
                    <span className="font-semibold text-gray-800">{g.value}</span>
                    <p className="text-sm text-gray-500 mt-0.5">{g.label.split(' — ')[1]}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="label">{t('location') || 'Location (Village / Town)'} *</label>
            <input
              type="text"
              className="input"
              placeholder="e.g. Lasalgaon, Nashik"
              value={formData.location}
              onChange={(e) => handleChange('location', e.target.value)}
              required
            />
          </div>

          {/* Expected Price + Available Date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">{t('expectedPrice') || 'Your Expected Price (₹/quintal)'}</label>
              <input
                type="number"
                className="input"
                placeholder="e.g. 1800"
                min="1"
                value={formData.expected_price}
                onChange={(e) => handleChange('expected_price', e.target.value)}
              />

              {/* Live Current Price display right below the price input */}
              {formData.crop ? (
                <div className="mt-2 flex flex-wrap items-center justify-between gap-1.5 p-2.5 bg-green-50/80 border border-green-200 rounded-xl">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <TrendingUp className="w-4 h-4 text-green-600 shrink-0" />
                    <span className="text-xs text-gray-600">
                      {t('currentPrice') || 'Current Price'} ({cropT(formData.crop)}):
                    </span>
                    {currentPriceInfo ? (
                      <span className="text-sm font-bold text-green-700">
                        ₹{Number(currentPriceInfo.price).toLocaleString('en-IN')}
                        <span className="text-xs font-normal text-green-600">/qtl</span>
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">Loading...</span>
                    )}
                  </div>
                  {currentPriceInfo && (
                    <button
                      type="button"
                      onClick={() => handleChange('expected_price', currentPriceInfo.price)}
                      className="text-xs font-semibold text-green-700 hover:text-green-800 hover:underline shrink-0"
                      title="Click to use this price"
                    >
                      {t('usePrice') || 'Use this price'}
                    </button>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-400 mt-1">Select a crop above to see current market price</p>
              )}
              <p className="text-xs text-gray-400 mt-1">Buyers can make offers above or below this</p>
            </div>
            <div>
              <label className="label">{t('availableDate') || 'Available From'}</label>
              <input
                type="date"
                className="input"
                value={formData.available_date}
                onChange={(e) => handleChange('available_date', e.target.value)}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="label">{t('notes') || 'Additional Notes'}</label>
            <textarea
              className="input resize-none"
              rows={3}
              placeholder="Any additional details about your produce (storage, transport, packaging, etc.)"
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-60 flex items-center gap-2 justify-center text-base"
          >
            {loading ? (t('submittingListing') || 'Creating listing...') : (
              <>
                <Package className="w-5 h-5" />
                {t('findBuyers') || 'Find Buyers for My Produce'}
              </>
            )}
          </button>
        </form>
      </div>

      <p className="text-xs text-gray-400 text-center mt-4">
        Your listing will be visible to verified buyers. You stay in full control.
      </p>
    </div>
  );
}

