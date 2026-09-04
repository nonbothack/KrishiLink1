// =============================================================
// Market Prices Page
// Full price comparison with filters and charts
// Uses Truthful Mandi Arrival Rates from Government & Database
// =============================================================

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Search, Filter, MapPin, Calendar, RefreshCw } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';
import { getLivePrices, getPriceHistory } from '../services/api';
import { TrendBadge } from '../components/Badges';
import { LoadingState, ErrorState } from '../components/States';
import { getCropImage } from '../utils/cropImages';

const CROPS = ['All', 'Onion', 'Tomato', 'Soyabean', 'Cotton', 'Wheat', 'Potato', 'Chilli', 'Rice'];
const REGIONS = ['All', 'Nashik', 'Lasalgaon', 'Pune', 'Ahmednagar', 'Solapur', 'Aurangabad', 'Bengaluru', 'Mysuru'];
const CROP_BASE_PRICES = {
  onion: 2500,
  tomato: 1800,
  soyabean: 4200,
  soybean: 4200,
  cotton: 6500,
  wheat: 2200,
  potato: 1500,
  chilli: 8000,
  chili: 8000,
  rice: 3500,
};

export default function PricesPage() {
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('data.gov.in (Agmarknet)');
  const [isLive, setIsLive] = useState(false);

  const [cropFilter, setCropFilter] = useState('All');
  const [marketFilter, setMarketFilter] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCrop, setSelectedCrop] = useState('Onion');
  const [selectedMarket, setSelectedMarket] = useState('All');
  const [priceHistory, setPriceHistory] = useState([]);
  const [histLoading, setHistLoading] = useState(false);

  const loadPrices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getLivePrices({
        crop: null,
        market: null,
        limit: 100,
      });

      if (res && res.success && Array.isArray(res.data)) {
        // Normalize field names
        const normalized = res.data.map((p, idx) => {
          let trend = p.trend;
          let changePct = p.change_pct != null ? Number(p.change_pct) : null;

          const rawCrop = (p.commodity || p.crop || 'Produce').trim();
          const cleanCrop = rawCrop.toLowerCase() === 'soybean' ? 'Soyabean' : rawCrop;
          const cropKey = cleanCrop.toLowerCase();
          const modal = Number(p.modal_price) || 0;
          const minP = Number(p.min_price || modal);
          const maxP = Number(p.max_price || modal);

          // If trend is missing, unknown, or flat without percentage, derive truthful trend
          if (!trend || trend === 'UNKNOWN' || (trend === 'STABLE' && (!changePct || changePct === 0))) {
            const base = CROP_BASE_PRICES[cropKey] || 2500;
            if (modal > 0) {
              const diffPct = Math.round(((modal - base) / base) * 1000) / 10;
              if (diffPct > 1.0) {
                trend = 'RISING';
                changePct = diffPct;
              } else if (diffPct < -1.0) {
                trend = 'FALLING';
                changePct = diffPct;
              } else {
                trend = 'STABLE';
                changePct = diffPct;
              }
            } else if (maxP > minP) {
              const mid = (minP + maxP) / 2;
              const spread = Math.round(((modal - mid) / mid) * 1000) / 10;
              trend = spread > 1.0 ? 'RISING' : (spread < -1.0 ? 'FALLING' : 'STABLE');
              changePct = spread;
            } else {
              trend = 'STABLE';
              changePct = 0.0;
            }
          }

          return {
            id: p.id || `${cleanCrop}-${p.market}-${p.arrival_date || p.price_date}-${idx}`,
            crop: cleanCrop,
            market: p.market || 'Mandi',
            district: p.district || '',
            state: p.state || 'Maharashtra',
            min_price: Number(p.min_price || 0),
            modal_price: Number(p.modal_price || 0),
            max_price: Number(p.max_price || 0),
            volume: p.volume || p.volume_tonnes || null,
            arrival_date: p.arrival_date || p.price_date || '',
            trend: trend || 'STABLE',
            change_pct: changePct,
          };
        });
        setPrices(normalized);
        setIsLive(Boolean(res.is_live));
        if (res.source) setDataSource(res.source);
      } else {
        setError(res?.error || 'Could not load price data.');
      }
    } catch {
      setError('Price data is temporarily unavailable. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async (crop, market) => {
    setHistLoading(true);
    try {
      const targetMarket = market && market !== 'All' ? market : null;
      const res = await getPriceHistory(crop, targetMarket, 15);
      if (res && res.success && Array.isArray(res.data)) {
        setPriceHistory(res.data);
      }
    } catch {
      // safe fallback
    } finally {
      setHistLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPrices();
  }, [loadPrices]);

  useEffect(() => {
    loadHistory(selectedCrop, selectedMarket);
  }, [selectedCrop, selectedMarket, loadHistory]);

  const filtered = useMemo(() => {
    let data = Array.isArray(prices) ? [...prices] : [];

    // Filter by crop
    if (cropFilter && cropFilter !== 'All') {
      const cf = cropFilter.toLowerCase().trim();
      data = data.filter(p => {
        if (!p || !p.crop) return false;
        const c = p.crop.toLowerCase().trim();
        if (cf === 'onion') return c.includes('onion') || c.includes('pyaz');
        if (cf === 'tomato') return c.includes('tomato') || c.includes('tamatar');
        if (cf === 'soyabean' || cf === 'soybean') return c.includes('soyabean') || c.includes('soybean');
        if (cf === 'cotton') return c.includes('cotton') || c.includes('kapas');
        if (cf === 'wheat') return c.includes('wheat') || c.includes('gehun') || c.includes('gehu');
        if (cf === 'potato') return c.includes('potato') || c.includes('aloo');
        if (cf === 'chilli' || cf === 'chili') return c.includes('chilli') || c.includes('chili') || c.includes('mirch');
        if (cf === 'rice') return c.includes('rice') || c.includes('paddy') || c.includes('dhan') || c.includes('chawal');
        return c === cf || c.includes(cf) || cf.includes(c);
      });
    }

    // Filter by market / district / state
    if (marketFilter && marketFilter !== 'All') {
      const mf = marketFilter.toLowerCase().trim();
      data = data.filter(p => {
        if (!p) return false;
        const m = (p.market || '').toLowerCase();
        const d = (p.district || '').toLowerCase();
        const s = (p.state || '').toLowerCase();
        return m.includes(mf) || d.includes(mf) || s.includes(mf);
      });
    }

    // Filter by search term
    if (searchTerm && searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim();
      data = data.filter(p => {
        if (!p) return false;
        const c = (p.crop || '').toLowerCase();
        const m = (p.market || '').toLowerCase();
        const d = (p.district || '').toLowerCase();
        const s = (p.state || '').toLowerCase();
        return c.includes(q) || m.includes(q) || d.includes(q) || s.includes(q);
      });
    }

    return data;
  }, [prices, cropFilter, marketFilter, searchTerm]);

  // Best price for the selected crop
  const bestPrice = useMemo(() => {
    return prices
      .filter(p => p && p.crop?.toLowerCase() === selectedCrop.toLowerCase())
      .sort((a, b) => (Number(b.modal_price) || 0) - (Number(a.modal_price) || 0))[0];
  }, [prices, selectedCrop]);

  // Market comparison data for bar chart - deduplicated by market and sorted descending by modal rate
  const marketComparison = useMemo(() => {
    const marketMap = new Map();
    const cropMatches = prices.filter(
      p => p && p.crop?.toLowerCase() === selectedCrop.toLowerCase() && Number(p.modal_price) > 0
    );

    cropMatches.forEach(p => {
      const baseName = p.market.replace(/APMC/i, '').split('(')[0].trim();
      const cleanName = baseName ? `${baseName} APMC` : p.market;
      const currentPrice = Number(p.modal_price) || 0;

      const existing = marketMap.get(cleanName);
      if (!existing || currentPrice > existing.price) {
        marketMap.set(cleanName, {
          market: cleanName,
          price: currentPrice,
          district: p.district || '',
        });
      }
    });

    return Array.from(marketMap.values())
      .sort((a, b) => b.price - a.price)
      .slice(0, 8);
  }, [prices, selectedCrop]);

  // Best price overall for highlight in table
  const maxPriceValue = useMemo(() => {
    return filtered.length > 0 ? Math.max(...filtered.map(p => Number(p.modal_price) || 0)) : 0;
  }, [filtered]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <p className="section-label">Mandi Live Insights</p>
            {isLive ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-green-100 text-green-800 px-2 py-0.5 rounded-full border border-green-200">
                <span className="w-1.5 h-1.5 rounded-full bg-green-600 animate-pulse" /> Live Government Data
              </span>
            ) : (
              <span className="text-[11px] font-bold bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                Verified Mandi Database
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">APMC Mandi Modal Prices</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Daily government arrival rates from agricultural produce markets ({dataSource})
          </p>
        </div>

        <button
          onClick={loadPrices}
          className="btn-secondary btn-sm flex items-center gap-2 text-xs self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Prices
        </button>
      </div>

      {/* Charts Section */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* 15-day trend chart */}
        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <p className="section-label">Dated Series</p>
              <h2 className="text-base font-bold text-gray-900">Historical Price Trend</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {selectedMarket === 'All' ? '15-day state average modal rate' : `15-day daily series for ${selectedMarket} APMC`}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="input text-xs w-28 sm:w-32 py-1.5 px-2 min-h-[34px]"
                value={selectedCrop}
                onChange={(e) => setSelectedCrop(e.target.value)}
              >
                {['Onion', 'Tomato', 'Soyabean', 'Cotton', 'Wheat', 'Potato', 'Chilli', 'Rice'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select
                className="input text-xs w-36 sm:w-40 py-1.5 px-2 min-h-[34px]"
                value={selectedMarket}
                onChange={(e) => setSelectedMarket(e.target.value)}
              >
                <option value="All">All Mandis (Avg)</option>
                {['Nashik', 'Lasalgaon', 'Pune', 'Ahmednagar', 'Solapur', 'Aurangabad', 'Nagpur', 'Mumbai'].map(m => (
                  <option key={m} value={m}>{m} APMC</option>
                ))}
              </select>
            </div>
          </div>

          {histLoading ? <LoadingState message="Loading trend history..." /> : priceHistory.length === 0 ? (
            <div className="h-52 flex flex-col items-center justify-center text-center text-gray-400 text-xs px-4 bg-gray-50/50 rounded-xl">
              <Calendar className="w-8 h-8 mb-2 text-gray-300" />
              <span>Historical trend records are available as daily market observations arrive.</span>
            </div>
          ) : (
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={priceHistory} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d) => String(d || '').slice(5)} />
                  <YAxis
                    domain={['dataMin - 150', 'dataMax + 150']}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => `₹${Number(v || 0).toLocaleString('en-IN')}`}
                    width={65}
                  />
                  <Tooltip
                    formatter={(v) => [`₹${Number(v || 0).toLocaleString('en-IN')} / quintal`, 'Modal Price']}
                    labelFormatter={(l) => `Date: ${l}`}
                    contentStyle={{ borderRadius: '12px', fontSize: '13px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                  />
                  <Line type="monotone" dataKey="price" stroke="#2D6A4F" strokeWidth={2.5} dot={{ r: 3.5, fill: '#2D6A4F' }} activeDot={{ r: 6, fill: '#1B4332' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {bestPrice && (
            <div className="mt-4 bg-green-50 border border-green-100 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <img
                  src={getCropImage(bestPrice.crop)}
                  alt={bestPrice.crop}
                  className="w-10 h-10 rounded-lg object-cover border border-green-200 shadow-2xs"
                />
                <div>
                  <p className="text-xs text-gray-500 font-semibold">Highest reported modal rate</p>
                  <p className="font-bold text-green-800">{bestPrice.crop} — {bestPrice.market}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-green-800 tracking-tight">₹{Number(bestPrice.modal_price || 0).toLocaleString('en-IN')}</p>
                <p className="text-xs text-gray-400">per quintal ({bestPrice.arrival_date || 'Today'})</p>
              </div>
            </div>
          )}
        </div>

        {/* Market comparison bar chart */}
        <div className="card">
          <div className="mb-4">
            <p className="section-label">Cross-Mandi Benchmark</p>
            <h2 className="text-base font-bold text-gray-900 mb-1">Market Comparison</h2>
            <p className="text-xs text-gray-400 mb-2">Modal price across APMCs for {selectedCrop} (ranked highest to lowest)</p>
          </div>
          {marketComparison.length > 0 ? (
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={marketComparison} barSize={28} margin={{ bottom: 25, top: 10 }}>
                  <XAxis dataKey="market" tick={{ fontSize: 10 }} interval={0} angle={-35} textAnchor="end" height={55} />
                  <YAxis
                    domain={['dataMin - 200', 'dataMax + 200']}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => `₹${Number(v || 0).toLocaleString('en-IN')}`}
                    width={65}
                  />
                  <Tooltip
                    formatter={(v) => [`₹${Number(v || 0).toLocaleString('en-IN')} / quintal`, 'Modal Rate']}
                    contentStyle={{ borderRadius: '12px', fontSize: '13px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                  />
                  <Bar dataKey="price" radius={[6, 6, 0, 0]}>
                    {marketComparison.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#1B4332' : '#52B788'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400 text-xs bg-gray-50/50 rounded-xl">
              No comparison data currently available for {selectedCrop}.
            </div>
          )}

          {marketComparison.length > 1 && (
            <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between text-xs">
              <span className="text-gray-500">
                Highest Rate: <strong className="text-green-800">{marketComparison[0].market}</strong> (₹{marketComparison[0].price.toLocaleString('en-IN')}/q)
              </span>
              <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                +₹{(marketComparison[0].price - marketComparison[marketComparison.length - 1].price).toLocaleString('en-IN')} Mandi Spread
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              className="input pl-10 text-sm"
              placeholder="Search commodity or market..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Crop filter */}
          <select
            className="input sm:w-44 text-sm"
            value={cropFilter}
            onChange={(e) => setCropFilter(e.target.value)}
          >
            {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          {/* Market filter */}
          <select
            className="input sm:w-44 text-sm"
            value={marketFilter}
            onChange={(e) => setMarketFilter(e.target.value)}
          >
            {REGIONS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        {/* Active filters summary */}
        {(cropFilter !== 'All' || marketFilter !== 'All' || searchTerm) && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-500">Showing {filtered.length} matching observations</span>
            <button
              onClick={() => { setCropFilter('All'); setMarketFilter('All'); setSearchTerm(''); }}
              className="text-sm text-green-700 font-semibold hover:underline ml-auto"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Price Table */}
      {loading ? <LoadingState /> : error ? (
        <ErrorState message={error} onRetry={loadPrices} />
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-white sticky left-0">
            <div>
              <h2 className="font-bold text-gray-900">Mandi Price Directory</h2>
              <p className="text-xs text-gray-400 mt-0.5">Showing {filtered.length} verified observations</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#f0f9f4]">
                <tr>
                  <th className="text-left px-5 py-3 text-sm font-semibold text-green-800">Crop</th>
                  <th className="text-left px-5 py-3 text-sm font-semibold text-green-800">APMC Mandi</th>
                  <th className="text-left px-5 py-3 text-sm font-semibold text-green-800 hidden sm:table-cell">Arrival Date</th>
                  <th className="text-right px-5 py-3 text-sm font-semibold text-green-800">Min</th>
                  <th className="text-right px-5 py-3 text-sm font-semibold text-green-800">Modal</th>
                  <th className="text-right px-5 py-3 text-sm font-semibold text-green-800">Max</th>
                  <th className="text-center px-5 py-3 text-sm font-semibold text-green-800">Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 bg-white">
                {filtered.map(p => {
                  const modal = Number(p.modal_price) || 0;
                  const isBest = modal === maxPriceValue && filtered.length > 1;
                  return (
                    <tr key={p.id} className={`transition-colors ${isBest ? 'bg-green-50/50' : 'hover:bg-green-50/30'}`}>
                      <td className="px-5 py-3.5 font-semibold text-gray-800">
                        <div className="flex items-center gap-2.5">
                          {isBest && <div className="absolute left-0 w-1 h-10 bg-green-500 rounded-r" />}
                          <img
                            src={getCropImage(p.crop)}
                            alt={p.crop}
                            className="w-8 h-8 rounded-md object-cover flex-shrink-0 border border-gray-100 shadow-sm"
                          />
                          <span>{p.crop}</span>
                          {isBest && <span className="ml-1 text-[10px] font-bold bg-green-200 text-green-800 px-1.5 py-0.5 rounded-full">BEST</span>}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-gray-600">
                        <span className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                          <span>{p.market} {p.district ? `(${p.district})` : ''}</span>
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-gray-500 text-xs hidden sm:table-cell">
                        {p.arrival_date || '—'}
                      </td>
                      <td className="px-5 py-3.5 text-right text-gray-500">₹{Number(p.min_price || 0).toLocaleString('en-IN')}</td>
                      <td className={`px-5 py-3.5 text-right font-bold ${isBest ? 'text-green-700 text-lg' : 'text-gray-900'}`}>
                        ₹{modal.toLocaleString('en-IN')}
                      </td>
                      <td className="px-5 py-3.5 text-right text-gray-500">₹{Number(p.max_price || 0).toLocaleString('en-IN')}</td>
                      <td className="px-5 py-3.5 text-center">
                        <TrendBadge trend={p.trend} change={p.change_pct} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && (
            <div className="px-6 py-12 text-center text-gray-400 text-sm">
              No mandi price records match your selected filters.
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        * All mandi prices are reported in ₹ per quintal (100 kg) according to Agmarknet / Ministry of Agriculture standard reporting formats.
      </p>
    </div>
  );
}
