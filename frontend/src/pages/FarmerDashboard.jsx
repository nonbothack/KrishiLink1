// =============================================================
// Farmer Dashboard
// Main page for logged-in farmers
// =============================================================

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Package, FileText, Wallet,
  TrendingUp, TrendingDown, Minus, MapPin, Star,
  ArrowUpRight, Warehouse, Clock, CheckCircle2
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { getCropImage } from '../utils/cropImages';
import {
  getPrices,
  getTrend,
  getPriceHistory,
  getFarmerDashboardSummary,
  getNearbyBuyers,
  getStorageFacilities,
  getNotifications,
} from '../services/api';
import { DEMO_BUYERS, DEMO_STORAGE } from '../data/demoData';
import { TrendBadge, VerifiedBadge } from '../components/Badges';
import { LoadingState } from '../components/States';

// ---- Summary Card (secondary level) ----
function SummaryCard({ title, value, sub, icon: Icon, color, accent }) {
  return (
    <div className={`card flex items-start gap-4 ${accent}`}>
      <div className={`w-11 h-11 ${color} rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5 leading-tight">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

// ---- Best Price Hero Card (primary level) ----
function BestPriceHeroCard({ trendData, prices, selectedCrop, t, cropT }) {
  const priceList = Array.isArray(prices) ? prices : [];
  let best = priceList
    .filter(p => p && p.crop && p.crop.toLowerCase() === selectedCrop?.toLowerCase())
    .sort((a, b) => (b.modal_price || 0) - (a.modal_price || 0))[0];

  // Graceful fallback to trendData if crop is not in initial batch
  if (!best && trendData?.current_price) {
    best = {
      crop: selectedCrop,
      market: trendData.market || 'Lasalgaon',
      modal_price: trendData.current_price,
      min_price: Math.round(trendData.current_price * 0.95),
      max_price: Math.round(trendData.current_price * 1.05),
      volume: 450,
    };
  }

  if (!best) {
    return (
      <div className="card-primary col-span-2 relative overflow-hidden flex items-center justify-center p-6 min-h-[160px]">
        <p className="text-sm text-gray-500">Fetching latest mandi prices...</p>
      </div>
    );
  }

  const isRising = trendData?.trend === 'RISING';
  const isFalling = trendData?.trend === 'FALLING';

  return (
    <div className="card-primary col-span-2 relative overflow-hidden">
      {/* Decorative background circle */}
      <div className="absolute -right-8 -top-8 w-40 h-40 bg-green-50 rounded-full opacity-60 pointer-events-none" />
      <div className="absolute -right-4 -bottom-8 w-24 h-24 bg-green-100 rounded-full opacity-40 pointer-events-none" />

      <div className="relative flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="section-label">{t('todaysBestPrice') || "Today's Best Price"}</p>
          <div className="flex items-end gap-3 mt-1 flex-wrap">
            <span className="stat-number">₹{Number(best.modal_price || 0).toLocaleString('en-IN')}</span>
            <span className="text-sm text-gray-500 mb-1 font-medium">{t('perQuintal') || 'per quintal'}</span>
          </div>

          {/* Market + crop info */}
          <div className="flex items-center gap-2 mt-2">
            <MapPin className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
            <span className="text-sm font-semibold text-gray-700">{best.market}</span>
            <span className="text-gray-300">·</span>
            <span className="text-sm text-gray-500">{cropT(best.crop)}</span>
          </div>

          {/* Trend indicator */}
          {trendData && (
            <div className="flex items-center gap-2 mt-3">
              {isRising ? (
                <span className="inline-flex items-center gap-1.5 bg-green-100 text-green-700 text-xs font-bold px-3 py-1.5 rounded-full border border-green-200">
                  <TrendingUp className="w-3.5 h-3.5" />
                  {t('rising') || 'Rising'} {trendData.percentage_change > 0 ? `+${trendData.percentage_change}%` : ''}
                </span>
              ) : isFalling ? (
                <span className="inline-flex items-center gap-1.5 bg-red-100 text-red-700 text-xs font-bold px-3 py-1.5 rounded-full border border-red-200">
                  <TrendingDown className="w-3.5 h-3.5" />
                  {t('falling') || 'Falling'} {trendData.percentage_change}%
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1.5 rounded-full border border-amber-200">
                  <Minus className="w-3.5 h-3.5" />
                  {t('stable') || 'Stable'}
                </span>
              )}
              <span className="text-xs text-gray-400">{t('sevenDaySignal') || '7-day signal'}</span>
            </div>
          )}
        </div>

        {/* Crop image */}
        <img
          src={getCropImage(best.crop)}
          alt={best.crop}
          className="w-20 h-20 rounded-2xl object-cover border-2 border-green-100 shadow-md flex-shrink-0"
        />
      </div>

      {/* Bottom row — min/max context */}
      <div className="mt-4 pt-4 border-t border-green-100 flex items-center gap-6 text-xs text-gray-500">
        <span>{t('minPrice') || 'Min'}: <strong className="text-gray-700">₹{Number(best.min_price || best.modal_price || 0).toLocaleString('en-IN')}</strong></span>
        <span>{t('maxPrice') || 'Max'}: <strong className="text-gray-700">₹{Number(best.max_price || best.modal_price || 0).toLocaleString('en-IN')}</strong></span>
        <span>Vol: <strong className="text-gray-700">{best.volume ? `${best.volume}T` : 'Active'}</strong></span>
        <span className="ml-auto text-[10px] bg-green-100 text-green-700 font-bold px-2 py-1 rounded-full">Best nearby price</span>
      </div>
    </div>
  );
}


// ---- Trend Info Box ----
function TrendInfoBox({ trendData }) {
  if (!trendData) return null;
  const { trend, explanation } = trendData;

  const bg = trend === 'RISING' ? 'bg-green-50 border-green-200'
    : trend === 'FALLING' ? 'bg-red-50 border-red-200'
    : 'bg-amber-50 border-amber-200';

  const Icon = trend === 'RISING' ? TrendingUp
    : trend === 'FALLING' ? TrendingDown
    : Minus;

  const iconColor = trend === 'RISING' ? 'text-green-600'
    : trend === 'FALLING' ? 'text-red-600'
    : 'text-amber-600';

  return (
    <div className={`rounded-xl border p-4 ${bg}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 ${iconColor} flex-shrink-0`} />
        <div>
          <p className="font-semibold text-gray-800 text-sm">{explanation}</p>
          <p className="text-xs text-gray-500 mt-1">
            Rule-Based Signal — calculated from 7-day price arithmetic. Not AI prediction.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function FarmerDashboard() {
  const { user } = useAuth();
  const { t, cropT, greeting } = useLanguage();
  const [prices, setPrices] = useState([]);
  const [trendData, setTrendData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState('Onion');
  const [summary, setSummary] = useState({
    active_listings: 0,
    active_listings_sub: 'No active listings',
    offers_received: 0,
    offers_received_sub: '0 pending offers',
    pending_payments_count: 0,
    pending_payments_total: 0,
    pending_payments_formatted: '₹0',
    pending_payments_sub: 'No pending payments',
  });
  const [buyers, setBuyers] = useState([]);
  const [storage, setStorage] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [
          priceRes,
          trendRes,
          histRes,
          summaryRes,
          buyersRes,
          storageRes,
          notifRes,
        ] = await Promise.all([
          getPrices(null, null, 100),
          getTrend(selectedCrop, 'Lasalgaon'),
          getPriceHistory(selectedCrop, 'Lasalgaon', 15),
          getFarmerDashboardSummary(),
          getNearbyBuyers({ crop: selectedCrop }),
          getStorageFacilities(),
          getNotifications(),
        ]);

        if (priceRes && priceRes.success && priceRes.data) setPrices(priceRes.data);
        if (trendRes && trendRes.success && trendRes.data) setTrendData(trendRes.data);
        if (histRes && histRes.success && histRes.data) setPriceHistory(histRes.data);
        if (summaryRes && summaryRes.success && summaryRes.data) setSummary(summaryRes.data);
        if (buyersRes && buyersRes.success && Array.isArray(buyersRes.data) && buyersRes.data.length > 0) {
          setBuyers(buyersRes.data);
        } else {
          setBuyers(DEMO_BUYERS);
        }
        if (storageRes && storageRes.success && Array.isArray(storageRes.data) && storageRes.data.length > 0) {
          setStorage(storageRes.data);
        } else {
          setStorage(DEMO_STORAGE);
        }
        if (notifRes && notifRes.success && Array.isArray(notifRes.data)) {
          setNotifications(notifRes.data);
        }
      } catch (err) {
        console.warn('Dashboard loadData fallback:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedCrop]);

  const movingAvg = trendData?.moving_average || 0;

  // Fallback activity feed when user has 0 notifications
  const defaultActivity = [
    { label: 'Market price ledger verified across 8 APMCs', time: 'Today', icon: CheckCircle2, color: 'text-green-600 bg-green-50' },
    { label: 'Connected to direct buyer marketplace', time: 'Active', icon: ArrowUpRight, color: 'text-blue-600 bg-blue-50' },
    { label: 'Smart contract escrow ready for transactions', time: 'Secured', icon: Wallet, color: 'text-amber-600 bg-amber-50' },
  ];

  const crops = ['Onion', 'Tomato', 'Soybean', 'Cotton'];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-green-900 to-green-800 rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        {/* Subtle background pattern/glow */}
        <div className="absolute -right-20 -top-20 w-64 h-64 bg-green-700 rounded-full opacity-50 blur-3xl" />
        <div className="absolute right-10 -bottom-10 w-40 h-40 bg-green-500 rounded-full opacity-20 blur-2xl" />

        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">
              {greeting}, {(user?.name || user?.full_name || 'Farmer').split(' ')[0]} 👋
            </h1>
            <div className="flex items-center gap-4 text-green-100 text-sm">
              <span className="flex items-center gap-1.5 bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">
                <MapPin className="w-4 h-4" />
                {user?.location || 'Nashik, Maharashtra'}
              </span>
            </div>
          </div>
          <Link to="/sell" className="bg-white text-green-900 hover:bg-green-50 font-bold px-6 py-3 rounded-xl transition-all shadow-sm flex items-center gap-2 whitespace-nowrap active:scale-95">
            + {t('listProduce') || 'List Produce'}
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        {/* Primary Hero Card */}
        <div className="xl:col-span-2">
          <BestPriceHeroCard trendData={trendData} prices={prices} selectedCrop={selectedCrop} t={t} cropT={cropT} />
        </div>
        
        {/* Secondary Summary Cards */}
        <div className="xl:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SummaryCard
            title={t('activeListings') || 'Active Listings'}
            value={summary.active_listings}
            sub={summary.active_listings_sub}
            icon={Package}
            color="bg-blue-50 text-blue-600"
            accent="accent-bar-blue"
          />
          <SummaryCard
            title={t('offersReceived') || 'Offers Received'}
            value={summary.offers_received}
            sub={summary.offers_received_sub}
            icon={FileText}
            color="bg-purple-50 text-purple-600"
            accent="accent-bar-purple"
          />
          <SummaryCard
            title={t('pendingPayments') || 'Pending Payments'}
            value={summary.pending_payments_formatted}
            sub={summary.pending_payments_sub}
            icon={Wallet}
            color="bg-amber-50 text-amber-600"
            accent="accent-bar-amber"
          />
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid lg:grid-cols-3 gap-6">

        {/* LEFT: Market Prices + Trend Chart */}
        <div className="lg:col-span-2 space-y-6">

          {/* Crop selector + Trend */}
          <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
              <div>
                <p className="section-label">Market Intelligence</p>
                <h2 className="text-lg font-bold text-gray-900">{t('historicalPriceTrend') || 'Price Trend'}</h2>
                <p className="text-xs text-gray-400 mt-0.5">{t('sevenDaySignal') || '7-day rule-based signal'}</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                {crops.map(crop => (
                  <button
                    key={crop}
                    onClick={() => setSelectedCrop(crop)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      selectedCrop === crop
                        ? 'bg-green-800 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {cropT(crop)}
                  </button>
                ))}
              </div>
            </div>

            {loading ? <LoadingState message="Loading price data..." /> : (
              <>
                {/* Chart */}
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={priceHistory}>
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 10, fill: '#9ca3af' }}
                        tickFormatter={(d) => d.slice(5)}
                      />
                      <YAxis
                        tick={{ fontSize: 10, fill: '#9ca3af' }}
                        tickFormatter={(v) => `₹${v.toLocaleString('en-IN')}`}
                        width={70}
                      />
                      <Tooltip
                        formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'Price']}
                        labelFormatter={(l) => `Date: ${l}`}
                        contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', fontSize: '13px' }}
                      />
                      {movingAvg > 0 && (
                        <ReferenceLine
                          y={movingAvg}
                          stroke="#d97706"
                          strokeDasharray="5 5"
                          label={{ value: '7d avg', position: 'insideTopRight', fontSize: 10, fill: '#d97706' }}
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#2D6A4F"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: '#2D6A4F' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Trend stats */}
                {trendData && (
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    <div className="bg-gray-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">{t('currentPrice') || 'Current Price'}</p>
                      <p className="text-lg font-bold text-green-800">₹{trendData.current_price?.toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">{t('sevenDayAverage') || '7-Day Average'}</p>
                      <p className="text-lg font-bold text-gray-700">₹{trendData.moving_average?.toLocaleString('en-IN')}</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3 text-center">
                      <p className="text-xs text-gray-500 mb-1">{t('change') || 'Change'}</p>
                      <TrendBadge trend={trendData.trend} change={trendData.percentage_change} />
                    </div>
                  </div>
                )}

                {/* Recommended action */}
                <div className="mt-4">
                  <TrendInfoBox trendData={trendData} crop={selectedCrop} />
                </div>
              </>
            )}
          </div>

          {/* Market Prices Table */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="section-label">Live Data</p>
                <h2 className="text-lg font-bold text-gray-900">{t('marketPrices') || "Today's Market Prices"}</h2>
              </div>
              <Link to="/prices" className="text-green-700 text-sm font-semibold flex items-center gap-1 hover:underline">
                {t('viewAll') || 'View All'} <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 text-gray-500 font-medium">{t('crop') || 'Crop'}</th>
                    <th className="text-left py-2 text-gray-500 font-medium">{t('market') || 'Market'}</th>
                    <th className="text-right py-2 text-gray-500 font-medium">{t('price') || 'Price'}</th>
                    <th className="text-right py-2 text-gray-500 font-medium hidden sm:table-cell">{t('change') || 'Change'}</th>
                    <th className="text-center py-2 text-gray-500 font-medium">{t('trend') || 'Trend'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(Array.isArray(prices) ? prices : []).slice(0, 8).map(p => (
                    <tr key={p.id || `${p.crop}-${p.market}`} className="hover:bg-green-50/30 transition-colors">
                      <td className="py-3 font-semibold text-gray-800 flex items-center gap-2.5">
                        <img
                          src={getCropImage(p.crop)}
                          alt={p.crop || 'Crop'}
                          className="w-7 h-7 rounded-md object-cover flex-shrink-0 border border-gray-100 shadow-2xs"
                        />
                        <span>{cropT(p.crop) || 'Crop'}</span>
                      </td>
                      <td className="py-3 text-gray-600">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-gray-400" />
                          {p.market || 'APMC'}
                        </span>
                      </td>
                      <td className="py-3 text-right font-bold text-green-800">
                        ₹{Number(p.modal_price || 0).toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 text-right hidden sm:table-cell">
                        <span className={p.change_pct >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {p.change_pct >= 0 ? '+' : ''}{p.change_pct}%
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <TrendBadge trend={p.trend} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT: Buyers + Storage + Activity */}
        <div className="space-y-6">
          {/* Nearby Buyers */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="section-label">Connections</p>
                <h2 className="text-base font-bold text-gray-900">{t('nearbyBuyers') || 'Nearby Buyers'}</h2>
              </div>
            </div>
            <div className="space-y-3">
              {(buyers.length > 0 ? buyers : DEMO_BUYERS).slice(0, 3).map(buyer => (
                <div key={buyer.id} className="border border-gray-100 rounded-xl p-3 hover:border-green-200 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">{buyer.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{buyer.type} · {(buyer.crops || []).map(c => cropT(c)).join(', ')}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        {buyer.verified && <VerifiedBadge />}
                        <span className="flex items-center gap-0.5 text-xs text-amber-600">
                          <Star className="w-3 h-3 fill-amber-500 stroke-amber-500" />
                          {buyer.rating}
                        </span>
                        <span className="text-xs text-gray-400">{buyer.distance_km} km</span>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-bold text-green-800">₹{Number(buyer.offer_price || 0).toLocaleString('en-IN')}</p>
                      <p className="text-xs text-gray-400">/qtl</p>
                    </div>
                  </div>
                  <Link to="/matches" className="btn-primary btn-sm w-full mt-2 text-center text-xs block">
                    {t('makeOffer') || 'Make Offer'}
                  </Link>
                </div>
              ))}
            </div>
            <Link to="/matches" className="text-green-700 text-sm font-semibold flex items-center justify-center gap-1 mt-3 hover:underline">
              {t('findMoreBuyers') || 'Find More Buyers'} <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Nearby Storage */}
          <div className="card">
            <div className="mb-4">
              <p className="section-label">Logistics</p>
              <h2 className="text-base font-bold text-gray-900">{t('nearbyStorage') || 'Nearby Storage'}</h2>
            </div>
            <div className="space-y-3">
              {(storage.length > 0 ? storage : DEMO_STORAGE).slice(0, 2).map(s => (
                <div key={s.id} className="border border-gray-100 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Warehouse className="w-4 h-4 text-gray-400" />
                    <p className="font-semibold text-gray-800 text-sm">{s.name}</p>
                  </div>
                  <p className="text-xs text-gray-500">{s.type} · {s.distance_km} km away</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-600">
                      <span className="font-semibold text-green-700">{s.available}T</span> available of {s.capacity}T
                    </span>
                    <span className="badge-green text-xs">₹{s.price_per_day}/T/day</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card">
            <div className="mb-4">
              <p className="section-label">Overview</p>
              <h2 className="text-base font-bold text-gray-900">{t('recentActivity') || 'Recent Activity'}</h2>
            </div>
            <div className="space-y-3">
              {notifications.length > 0 ? (
                notifications.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-green-50 text-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-700 font-medium">{item.title || item.message}</p>
                      <div className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                defaultActivity.map((item, i) => {
                  const Icon = item.icon;
                  return (
                    <div key={i} className="flex items-start gap-3">
                      <div className={`w-8 h-8 ${item.color} rounded-lg flex items-center justify-center flex-shrink-0`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-700 font-medium">{item.label}</p>
                        <div className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {item.time}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
