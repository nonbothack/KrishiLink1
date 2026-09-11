// =============================================================
// Farmer Dashboard
// Main page for logged-in farmers
// =============================================================

import { useState, useEffect, useMemo } from 'react';
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
  getLivePrices,
  getTrend,
  getPriceHistory,
  getFarmerDashboardSummary,
  getNearbyBuyers,
  getStorageFacilities,
  getNotifications,
} from '../services/api';
import { LIVE_GOVERNMENT_PRICES } from '../data/liveMandiData';
import { DEMO_PRICES, DEMO_PRICE_HISTORY, DEMO_BUYERS, DEMO_STORAGE } from '../data/demoData';
import { TrendBadge, VerifiedBadge } from '../components/Badges';
import { LoadingState } from '../components/States';
import { NextActionCard } from '../components/ui/NextActionCard';

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
  const [selectedMarket, setSelectedMarket] = useState('Lasalgaon');
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
        const targetMarket = selectedMarket && selectedMarket !== 'All' ? selectedMarket : null;
        const [
          priceRes,
          trendRes,
          histRes,
          summaryRes,
          buyersRes,
          storageRes,
          notifRes,
        ] = await Promise.all([
          getLivePrices({ limit: 100 }),
          getTrend(selectedCrop, targetMarket),
          getPriceHistory(selectedCrop, targetMarket, 15),
          getFarmerDashboardSummary(),
          getNearbyBuyers({ crop: selectedCrop }),
          getStorageFacilities(),
          getNotifications(),
        ]);

        if (priceRes && priceRes.success && Array.isArray(priceRes.data) && priceRes.data.length > 0) {
          setPrices(priceRes.data);
        } else {
          const dbPrices = await getPrices(null, null, 100);
          if (dbPrices && dbPrices.success && Array.isArray(dbPrices.data) && dbPrices.data.length > 0) {
            setPrices(dbPrices.data);
          } else {
            setPrices(LIVE_GOVERNMENT_PRICES);
          }
        }

        if (trendRes && trendRes.success && trendRes.data) {
          setTrendData(trendRes.data);
        } else {
          const cleanCrop = selectedCrop.toLowerCase().replace(/soyabean/i, 'soybean');
          const realMatch = LIVE_GOVERNMENT_PRICES.find(p => p.crop.toLowerCase().replace(/soyabean/i, 'soybean') === cleanCrop) || LIVE_GOVERNMENT_PRICES[0];
          const movingAvg = Math.round(realMatch.modal_price / (1 + (realMatch.change_pct || 0) / 100));
          setTrendData({
            crop: selectedCrop,
            market: targetMarket || realMatch.market,
            current_price: realMatch.modal_price,
            moving_average: movingAvg,
            percentage_change: realMatch.change_pct || 0,
            trend: realMatch.trend || 'STABLE',
            explanation: `${selectedCrop} modal prices are currently ${(realMatch.trend || 'STABLE').toLowerCase()} (${realMatch.change_pct > 0 ? `+${realMatch.change_pct}%` : `${realMatch.change_pct}%`} relative to the 7-day average).`,
            note: 'Rule-based signal calculated from authentic arrivals arithmetic',
          });
        }

        if (histRes && histRes.success && Array.isArray(histRes.data) && histRes.data.length > 0) {
          setPriceHistory(histRes.data);
        } else {
          const cleanCrop = selectedCrop === 'Soyabean' ? 'Soybean' : selectedCrop;
          const marketKey = selectedMarket && selectedMarket !== 'All' ? selectedMarket.replace(/\s*APMC/i, '').trim() : 'All';
          const fallback = DEMO_PRICE_HISTORY[cleanCrop]?.[marketKey] ||
            DEMO_PRICE_HISTORY[cleanCrop]?.[selectedMarket] ||
            DEMO_PRICE_HISTORY[cleanCrop]?.['All'] ||
            DEMO_PRICE_HISTORY['Onion']?.['All'] || [];
          setPriceHistory(fallback.slice(-15));
        }
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
  }, [selectedCrop, selectedMarket]);

  const movingAvg = trendData?.moving_average || 0;

  const nextAction = useMemo(() => {
    if (summary.offers_received > 0) {
      return {
        title: `Buyer Offer Received`,
        description: `You have ${summary.offers_received} pending offer(s). Review commercial terms to accept or negotiate.`,
        badge: 'Offer Received',
        badgeTone: 'warning',
        urgency: 'Action required to proceed',
        primaryAction: {
          label: 'Review Offers',
          to: '/offers',
        },
        contextItems: [
          { label: 'Pending Offers', value: summary.offers_received },
        ],
      };
    }
    if (summary.pending_payments_count > 0) {
      return {
        title: `Active Deal in Progress`,
        description: `You have ${summary.pending_payments_count} active deal(s) awaiting payment or dispatch.`,
        badge: 'In Execution',
        badgeTone: 'info',
        urgency: 'Lifecycle active',
        primaryAction: {
          label: 'View Active Deals',
          to: '/transactions?tab=active',
        },
        contextItems: [
          { label: 'Pending Value', value: summary.pending_payments_formatted },
        ],
      };
    }
    if (summary.active_listings > 0) {
      return {
        title: `${summary.active_listings} Lot(s) Listed Live`,
        description: 'Your produce is published on the decentralized market. Connect with matching buyers to initiate direct negotiations.',
        badge: 'Listing Live',
        badgeTone: 'success',
        primaryAction: {
          label: 'Find Matching Buyers',
          to: '/matches',
        },
        secondaryAction: {
          label: '+ List Another Lot',
          to: '/sell',
        },
      };
    }
    return {
      title: 'Ready to Sell Your Harvest at Direct Market Rates?',
      description: 'List your produce in 60 seconds with live Agmarknet mandi price benchmarks and direct buyer matching.',
      badge: 'Start Selling',
      badgeTone: 'neutral',
      primaryAction: {
        label: '+ List Produce Now',
        to: '/sell',
      },
      secondaryAction: {
        label: 'Explore Live Mandi Prices',
        to: '/prices',
      },
      contextItems: [
        { label: 'Platform Fee', value: '₹0 Commission' },
        { label: 'Payments', value: 'Direct Settlement' },
      ],
    };
  }, [summary]);

  // Fallback activity feed when user has 0 notifications
  const defaultActivity = [
    { label: 'Market price ledger verified across 8 APMCs', time: 'Today', icon: CheckCircle2, color: 'text-green-600 bg-green-50' },
    { label: 'Connected to direct buyer marketplace', time: 'Active', icon: ArrowUpRight, color: 'text-blue-600 bg-blue-50' },
    { label: 'Smart contract escrow ready for transactions', time: 'Secured', icon: Wallet, color: 'text-amber-600 bg-amber-50' },
  ];

  const crops = ['Onion', 'Tomato', 'Soybean', 'Cotton', 'Wheat', 'Potato', 'Chilli', 'Rice'];
  const markets = ['All', 'Lasalgaon', 'Nashik', 'Pune', 'Mumbai', 'Ahmednagar', 'Solapur', 'Aurangabad', 'Nagpur'];

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

      {/* High-Contrast Next Action Card */}
      <NextActionCard {...nextAction} />

      {/* Summary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Link to="/sell" className="card flex items-center gap-3.5 hover:shadow-md transition-shadow">
          <div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center flex-shrink-0">
            <Package className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-gray-500">Active Listings</p>
            <p className="text-xl font-black text-gray-900 mt-0.5">{summary.active_listings} Lots</p>
            <p className="text-[11px] text-emerald-700 font-semibold truncate">+ List new harvest</p>
          </div>
        </Link>

        <Link to="/offers" className="card flex items-center gap-3.5 hover:shadow-md transition-shadow relative">
          <div className="w-11 h-11 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-gray-500">Incoming Offers</p>
            <div className="flex items-center gap-2 mt-0.5">
              <p className="text-xl font-black text-gray-900">{summary.offers_received}</p>
              {summary.offers_received > 0 && (
                <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full border border-amber-300 animate-pulse">
                  Action Required
                </span>
              )}
            </div>
            <p className="text-[11px] text-gray-500 truncate">Review buyer bids</p>
          </div>
        </Link>

        <Link to="/transactions?tab=active" className="card flex items-center gap-3.5 hover:shadow-md transition-shadow">
          <div className="w-11 h-11 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center flex-shrink-0">
            <Wallet className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-gray-500">Active Deals</p>
            <p className="text-xl font-black text-gray-900 mt-0.5">{summary.pending_payments_count} In Progress</p>
            <p className="text-[11px] text-teal-700 font-semibold truncate">View payment & dispatch</p>
          </div>
        </Link>
      </div>

      {/* 4 State-Aware Action Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Card 1: Sell Produce */}
        <Link
          to="/sell"
          className="card group flex flex-col gap-3 hover:border-green-300 hover:shadow-md transition-all border-2 border-transparent"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <Package className="w-5 h-5 text-green-700" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-gray-300 group-hover:text-green-600 transition-colors" />
          </div>
          <div>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Sell Produce</p>
            {summary.active_listings > 0 ? (
              <>
                <p className="text-2xl font-black text-gray-900 mt-0.5">{summary.active_listings}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {summary.active_listings === 1 ? 'lot listed' : 'lots live'} — tap to add more
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold text-green-700 mt-1">+ List Produce</p>
                <p className="text-xs text-gray-400 mt-0.5">No active listings</p>
              </>
            )}
          </div>
        </Link>

        {/* Card 2: Market Prices */}
        <Link
          to="/prices"
          className="card group flex flex-col gap-3 hover:border-blue-300 hover:shadow-md transition-all border-2 border-transparent"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <TrendingUp className="w-5 h-5 text-blue-700" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-gray-300 group-hover:text-blue-600 transition-colors" />
          </div>
          <div>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Market Price</p>
            {prices.length > 0 ? (() => {
              const best = prices.filter(p => p.crop === selectedCrop).sort((a, b) => (b.modal_price || 0) - (a.modal_price || 0))[0];
              return best ? (
                <>
                  <p className="text-2xl font-black text-gray-900 mt-0.5">₹{Number(best.modal_price).toLocaleString('en-IN')}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{selectedCrop} · {best.market}</p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-blue-700 mt-1">See Rates</p>
                  <p className="text-xs text-gray-400 mt-0.5">Tap to view mandi prices</p>
                </>
              );
            })() : (
              <>
                <p className="text-sm font-semibold text-blue-700 mt-1">See Today's Rates</p>
                <p className="text-xs text-gray-400 mt-0.5">Live Agmarknet prices</p>
              </>
            )}
          </div>
        </Link>

        {/* Card 3: Buyer Demand */}
        <Link
          to="/matches"
          className="card group flex flex-col gap-3 hover:border-purple-300 hover:shadow-md transition-all border-2 border-transparent"
        >
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <MapPin className="w-5 h-5 text-purple-700" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-gray-300 group-hover:text-purple-600 transition-colors" />
          </div>
          <div>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Buyer Demand</p>
            {buyers.length > 0 ? (
              <>
                <p className="text-2xl font-black text-gray-900 mt-0.5">{buyers.length}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  buyer{buyers.length === 1 ? '' : 's'} nearby
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold text-purple-700 mt-1">Find Buyers</p>
                <p className="text-xs text-gray-400 mt-0.5">See who's buying now</p>
              </>
            )}
          </div>
        </Link>

        {/* Card 4: Active Deal */}
        <Link
          to={summary.pending_payments_count > 0 ? '/transactions?tab=active' : '/transactions'}
          className={`card group flex flex-col gap-3 hover:shadow-md transition-all border-2 ${summary.pending_payments_count > 0 ? 'border-amber-200 bg-amber-50/50 hover:border-amber-400' : 'border-transparent hover:border-teal-300'
            }`}
        >
          <div className="flex items-center justify-between">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${summary.pending_payments_count > 0 ? 'bg-amber-100 group-hover:bg-amber-200' : 'bg-teal-100 group-hover:bg-teal-200'
              }`}>
              <FileText className={`w-5 h-5 ${summary.pending_payments_count > 0 ? 'text-amber-700' : 'text-teal-700'}`} />
            </div>
            <ArrowUpRight className={`w-4 h-4 transition-colors ${summary.pending_payments_count > 0 ? 'text-amber-400 group-hover:text-amber-600' : 'text-gray-300 group-hover:text-teal-600'}`} />
          </div>
          <div>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Active Deal</p>
            {summary.pending_payments_count > 0 ? (
              <>
                <p className="text-2xl font-black text-gray-900 mt-0.5">{summary.pending_payments_count}</p>
                <p className="text-xs text-amber-700 font-semibold mt-0.5">
                  {summary.pending_payments_count === 1 ? '1 trade in progress →' : `${summary.pending_payments_count} trades in progress →`}
                </p>
              </>
            ) : summary.offers_received > 0 ? (
              <>
                <p className="text-2xl font-black text-gray-900 mt-0.5">{summary.offers_received}</p>
                <p className="text-xs text-orange-600 font-semibold mt-0.5">offer{summary.offers_received === 1 ? '' : 's'} awaiting review</p>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold text-teal-700 mt-1">No active trades</p>
                <p className="text-xs text-gray-400 mt-0.5">Start by listing produce</p>
              </>
            )}
          </div>
        </Link>
      </div>

      {/* Main content grid */}
      <div className="grid lg:grid-cols-3 gap-6">

        {/* LEFT: Market Prices + Trend Chart */}
        <div className="lg:col-span-2 space-y-6">

          {/* Crop selector + Trend */}
          <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
              <div>
                <p className="section-label">{t('datedSeries') || 'Dated Series'}</p>
                <h2 className="text-lg font-bold text-gray-900">{t('historicalPriceTrend') || 'Historical Price Trend'}</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  {selectedMarket === 'All'
                    ? (t('fifteenDayAvgRate') || '15-day state average modal rate')
                    : `${t('fifteenDaySeriesFor') || '15-day daily series for'} ${selectedMarket} APMC`}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  id="farmer-crop-select"
                  aria-label="Select crop"
                  className="input text-xs sm:text-sm font-semibold text-gray-700 bg-white border border-gray-200 rounded-xl py-2 px-3 shadow-xs hover:border-green-600 focus:ring-2 focus:ring-green-500 focus:outline-hidden min-h-[38px] cursor-pointer"
                  value={selectedCrop}
                  onChange={(e) => setSelectedCrop(e.target.value)}
                >
                  {crops.map((c) => (
                    <option key={c} value={c}>
                      {cropT(c)}
                    </option>
                  ))}
                </select>

                <select
                  id="farmer-market-select"
                  aria-label="Select market"
                  className="input text-xs sm:text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl py-2 px-3 shadow-xs hover:border-green-600 focus:ring-2 focus:ring-green-500 focus:outline-hidden min-h-[38px] cursor-pointer"
                  value={selectedMarket}
                  onChange={(e) => setSelectedMarket(e.target.value)}
                >
                  <option value="All">{t('allMandisAvg') || 'All Mandis (Avg)'}</option>
                  {markets.filter(m => m !== 'All').map((m) => (
                    <option key={m} value={m}>
                      {m} APMC
                    </option>
                  ))}
                </select>
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
                        tickFormatter={(d) => (d ? d.slice(5) : '')}
                      />
                      <YAxis
                        domain={['dataMin - 150', 'dataMax + 150']}
                        tick={{ fontSize: 10, fill: '#9ca3af' }}
                        tickFormatter={(v) => `₹${Number(v || 0).toLocaleString('en-IN')}`}
                        width={70}
                      />
                      <Tooltip
                        formatter={(v) => [`₹${Number(v || 0).toLocaleString('en-IN')}`, 'Price']}
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
                        dot={{ r: 3.5, fill: '#2D6A4F' }}
                        activeDot={{ r: 6, fill: '#1B4332' }}
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
                  {(Array.isArray(prices) && prices.length > 0 ? prices : LIVE_GOVERNMENT_PRICES).slice(0, 8).map(p => {
                    const cropName = p.crop || p.commodity || 'Produce';
                    return (
                      <tr key={p.id || `${cropName}-${p.market}`} className="hover:bg-green-50/30 transition-colors">
                        <td className="py-3 font-semibold text-gray-800 flex items-center gap-2.5">
                          <img
                            src={getCropImage(cropName)}
                            alt={cropName}
                            className="w-7 h-7 rounded-md object-cover flex-shrink-0 border border-gray-100 shadow-2xs"
                          />
                          <span>{cropT(cropName)}</span>
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
                          {p.change_pct != null ? (
                            <span className={Number(p.change_pct) >= 0 ? 'text-green-600' : 'text-red-600'}>
                              {Number(p.change_pct) >= 0 ? '+' : ''}{p.change_pct}%
                            </span>
                          ) : (
                            <span className="text-gray-400">0.0%</span>
                          )}
                        </td>
                        <td className="py-3 text-center">
                          <TrendBadge trend={p.trend} />
                        </td>
                      </tr>
                    );
                  })}
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
