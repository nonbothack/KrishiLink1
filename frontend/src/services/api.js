// =============================================================
// KrishiLink API Service
// Connects to FastAPI v2.0 backend with truthful error reporting
// =============================================================

import {
  DEMO_PRICES,
  DEMO_PRICE_HISTORY,
  DEMO_BUYERS,
  DEMO_LOTS,
  DEMO_OFFERS,
  DEMO_TRANSACTIONS,
  DEMO_STORAGE,
  DEMO_GRIEVANCES,
  DEMO_MARKERS,
} from '../data/demoData';

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8000' : '');

// Check if explicit demo mode was requested via query param (?demo=1) or .env
export function isExplicitDemoMode() {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    if (params.get('demo') === '1' || params.get('demo') === 'true') return true;
  }
  return import.meta.env.VITE_DEMO_MODE === 'true';
}

// Retrieve the stored JWT access token for authenticated requests
function getAuthHeaders() {
  const token = localStorage.getItem('krishilink_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Helper for safe fetch with timeout + auth header
export async function apiCall(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  try {
    const controller = new AbortController();
    const timeoutMs = options.timeout || 30000;
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const { timeout: _unused, ...fetchOptions } = options;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...fetchOptions.headers,
      },
      signal: controller.signal,
      ...fetchOptions,
    });
    clearTimeout(timeoutId);

    const json = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = json?.message || json?.detail || `API error: ${response.status} ${response.statusText}`;
      return { success: false, error: errorMsg, status: response.status, data: null };
    }

    return json;
  } catch (error) {
    const isAbort = error.name === 'AbortError';
    const message = isAbort
      ? 'Request timed out. Please check your connection and retry.'
      : (error.message || 'Network error communicating with server.');
    return { success: false, error: message, status: 0, data: null };
  }
}

// 1. Market Prices
export async function getPrices(crop = null, market = null) {
  if (isExplicitDemoMode()) {
    let prices = [...DEMO_PRICES];
    if (crop && crop !== 'All') prices = prices.filter(p => p.crop === crop);
    if (market && market !== 'All') prices = prices.filter(p => p.market === market);
    return { success: true, data: prices, provenance: 'demo' };
  }

  const params = new URLSearchParams();
  if (crop && crop !== 'All') params.append('crop', crop);
  if (market && market !== 'All') params.append('market', market);

  const res = await apiCall(`/api/v1/prices?${params}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load market prices', data: [] };
}

// 2. Price History
export async function getPriceHistory(crop, market = null, days = 15) {
  if (isExplicitDemoMode()) {
    const marketKey = market || Object.keys(DEMO_PRICE_HISTORY[crop] || {})[0] || 'Lasalgaon';
    const history = DEMO_PRICE_HISTORY[crop]?.[marketKey] ||
                    DEMO_PRICE_HISTORY[crop]?.[Object.keys(DEMO_PRICE_HISTORY[crop] || {})[0]] ||
                    DEMO_PRICE_HISTORY['Onion']['Lasalgaon'] || [];
    return { success: true, data: history.slice(-days), provenance: 'demo' };
  }

  const res = await apiCall(`/api/v1/prices/${crop}/history?market=${market || ''}&days=${days}`);
  if (res && res.success && res.data) {
    const raw = Array.isArray(res.data) ? res.data : (res.data.history || res.data.items || []);
    const history = raw.map(item => ({
      date: item.date || item.price_date,
      price: Number(item.price ?? item.modal_price ?? 0),
      modal_price: Number(item.modal_price ?? item.price ?? 0),
      min_price: Number(item.min_price ?? 0),
      max_price: Number(item.max_price ?? 0),
    }));
    return { success: true, data: history, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load price history', data: [] };
}

// 3. Trend Analysis
export async function getTrend(crop, market = null) {
  if (isExplicitDemoMode()) {
    const priceData = DEMO_PRICES.find(p => p.crop === crop && (!market || p.market === market)) || DEMO_PRICES.find(p => p.crop === crop);
    if (!priceData) return { success: false, message: 'Crop not found' };
    const movingAvg = Math.round(priceData.modal_price / (1 + (priceData.change_pct || 0) / 100));
    return {
      success: true,
      data: {
        crop,
        market: priceData.market,
        current_price: priceData.modal_price,
        moving_average: movingAvg,
        percentage_change: priceData.change_pct || 0,
        trend: priceData.trend || 'STABLE',
        explanation: `${crop} prices in ${priceData.market} are ${priceData.trend.toLowerCase()} relative to the 7-day average.`,
        note: 'Calculated from 7-day arithmetic',
      },
      provenance: 'demo'
    };
  }

  const res = await apiCall(`/api/v1/prices/trends/${crop}${market ? `?market=${market}` : ''}`);
  if (res && res.success && res.data) {
    return { ...res, provenance: 'live' };
  }

  // If trends endpoint is unavailable, compute trend from history arithmetic
  const hist = await getPriceHistory(crop, market, 7);
  if (hist.success && hist.data.length >= 2) {
    const prices = hist.data.map(h => h.modal_price || h.price);
    const current = prices[prices.length - 1];
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const diffPct = Math.round(((current - avg) / avg) * 100 * 10) / 10;
    const trend = diffPct > 2 ? 'RISING' : diffPct < -2 ? 'FALLING' : 'STABLE';
    return {
      success: true,
      data: {
        crop,
        market: market || 'Primary Mandi',
        current_price: current,
        moving_average: Math.round(avg),
        percentage_change: diffPct,
        trend,
        explanation: `${crop} is ${trend.toLowerCase()} (${diffPct > 0 ? '+' : ''}${diffPct}%) vs 7-day moving average.`,
        note: 'Computed from verified price arithmetic',
      },
      provenance: 'live'
    };
  }

  return { success: false, error: res?.error || 'Trend data unavailable', data: null };
}

// 4. Produce Listings (Lots)
export async function getLots(farmerId = null) {
  if (isExplicitDemoMode()) {
    return { success: true, data: DEMO_LOTS, provenance: 'demo' };
  }

  const params = farmerId ? `?farmer_id=${farmerId}` : '';
  const res = await apiCall(`/api/v1/lots${params}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to fetch produce listings', data: [] };
}

export async function createLot(lotData) {
  if (isExplicitDemoMode()) {
    const newLot = {
      id: `lot-${Date.now()}`,
      ...lotData,
      farmer: 'Demo Farmer',
      status: 'ACTIVE',
      created_at: new Date().toISOString()
    };
    return { success: true, data: newLot, message: 'Listing created (Demo Mode)', provenance: 'demo' };
  }

  const payload = {
    crop:            lotData.crop,
    grade:           lotData.grade,
    quantity:        Number(lotData.quantity),
    unit:            lotData.unit || 'quintal',
    location_text:   lotData.location_text || lotData.location || '',
    asking_price:    Number(lotData.asking_price ?? lotData.expected_price ?? 0) || null,
    harvest_date:    lotData.harvest_date || null,
    available_from:  lotData.available_from || null,
    available_until: lotData.available_until || null,
    district:        lotData.district || null,
  };

  const res = await apiCall('/api/v1/lots', { method: 'POST', body: JSON.stringify(payload) });
  if (res && res.success) {
    return { ...res, provenance: 'live' };
  }
  return { success: false, error: res?.error || 'Failed to create listing', message: res?.error };
}

// 5. Buyer Matches (7-factor explainable matchmaking)
export async function getMatches(lotData) {
  if (isExplicitDemoMode()) {
    const buyers = DEMO_BUYERS.filter(b => b.crops.includes(lotData?.crop || 'Onion'));
    const pool = buyers.length > 0 ? buyers : DEMO_BUYERS;
    const scored = pool.map(buyer => {
      let score = 0;
      const reasons = [];
      if (buyer.crops.includes(lotData?.crop || 'Onion')) { score += 40; reasons.push('✓ Crop matches buyer requirement'); }
      if (lotData?.grade === 'A') { score += 25; reasons.push('✓ Grade A preferred by buyer'); } else { score += 15; reasons.push('✓ Standard grade accepted'); }
      const qty = parseInt(lotData?.quantity) || 100;
      if (qty >= buyer.min_qty && qty <= buyer.max_qty) { score += 20; reasons.push('✓ Quantity within buyer range'); } else { score += 10; reasons.push('~ Partial volume fit'); }
      if (buyer.distance_km <= 20) { score += 15; reasons.push('✓ Buyer is nearby (< 20 km)'); } else { score += 8; reasons.push('~ Buyer within 100 km'); }
      const label = score >= 80 ? 'Excellent' : score >= 55 ? 'Good' : 'Fair';
      return { ...buyer, score, reasons, label };
    });
    return { success: true, data: scored.sort((a, b) => b.score - a.score), provenance: 'demo' };
  }

  const res = await apiCall('/api/v1/matches/refresh', {
    method: 'POST',
    body: JSON.stringify({ lot_id: lotData?.id || lotData?.lot_id })
  });

  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'No matching buyers found for this lot', data: [] };
}

// 6. Offers
export async function getOffers(params = {}) {
  if (isExplicitDemoMode()) {
    return { success: true, data: DEMO_OFFERS, provenance: 'demo' };
  }

  const query = new URLSearchParams(params).toString();
  const res = await apiCall(`/api/v1/offers${query ? `?${query}` : ''}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load offers', data: [] };
}

export async function createOffer(offerData) {
  if (isExplicitDemoMode()) {
    const newOffer = { id: `demo-offer-${Date.now()}`, ...offerData, status: 'PENDING', created_at: new Date().toISOString() };
    return { success: true, data: newOffer, message: 'Offer submitted (Demo Mode)', provenance: 'demo' };
  }

  const res = await apiCall('/api/v1/offers', { method: 'POST', body: JSON.stringify(offerData) });
  if (res && res.success) {
    return { ...res, provenance: 'live' };
  }
  return { success: false, error: res?.error || 'Failed to submit offer', message: res?.error };
}

export async function acceptOffer(offerId) {
  if (isExplicitDemoMode()) {
    return { success: true, data: { id: offerId, status: 'ACCEPTED' }, message: 'Offer accepted (Demo Mode)', provenance: 'demo' };
  }
  const res = await apiCall(`/api/v1/offers/${offerId}/accept`, { method: 'POST' });
  if (res && res.success) return { ...res, provenance: 'live' };
  return { success: false, error: res?.error || 'Failed to accept offer', message: res?.error };
}

export async function rejectOffer(offerId) {
  if (isExplicitDemoMode()) {
    return { success: true, data: { id: offerId, status: 'REJECTED' }, message: 'Offer declined (Demo Mode)', provenance: 'demo' };
  }
  const res = await apiCall(`/api/v1/offers/${offerId}/reject`, { method: 'POST' });
  if (res && res.success) return { ...res, provenance: 'live' };
  return { success: false, error: res?.error || 'Failed to decline offer', message: res?.error };
}

export async function counterOffer(offerId, counterData) {
  if (isExplicitDemoMode()) {
    return { success: true, data: { id: `counter-${Date.now()}`, status: 'PENDING' }, message: 'Counter offer created', provenance: 'demo' };
  }
  const res = await apiCall(`/api/v1/offers/${offerId}/counter`, { method: 'POST', body: JSON.stringify(counterData) });
  if (res && res.success) return { ...res, provenance: 'live' };
  return { success: false, error: res?.error || 'Failed to create counter offer', message: res?.error };
}

export async function updateOffer(offerId, status) {
  if (status.toLowerCase() === 'accepted') return acceptOffer(offerId);
  if (status.toLowerCase() === 'rejected') return rejectOffer(offerId);
  if (isExplicitDemoMode()) {
    return { success: true, data: { id: offerId, status }, message: `Offer ${status} (Demo Mode)`, provenance: 'demo' };
  }

  const res = await apiCall(`/api/v1/offers/${offerId}/${status.toLowerCase()}`, { method: 'POST' });
  if (res && res.success) {
    return { ...res, provenance: 'live' };
  }
  return { success: false, error: res?.error || `Failed to update offer to ${status}`, message: res?.error };
}

// 7. Transactions
export async function getTransactions(params = {}) {
  if (isExplicitDemoMode()) {
    return { success: true, data: DEMO_TRANSACTIONS, provenance: 'demo' };
  }

  const query = new URLSearchParams(params).toString();
  const res = await apiCall(`/api/v1/transactions${query ? `?${query}` : ''}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load transactions', data: [] };
}

export async function getTransaction(id) {
  if (isExplicitDemoMode()) {
    const txn = DEMO_TRANSACTIONS.find(t => t.id === id);
    return txn ? { success: true, data: txn, provenance: 'demo' } : { success: false, error: 'Transaction not found', data: null };
  }

  const res = await apiCall(`/api/v1/transactions/${id}`);
  if (res && res.success && res.data) {
    return { ...res, provenance: 'live' };
  }
  return { success: false, error: res?.error || 'Transaction not found', data: null };
}

// 8. Map Data / Markets
export async function getMapMarkers(type = 'all') {
  if (isExplicitDemoMode()) {
    const markers = type === 'all' ? DEMO_MARKERS : DEMO_MARKERS.filter(m => m.type === type);
    return { success: true, data: markers, provenance: 'demo' };
  }

  const res = await apiCall('/api/v1/markets');
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load map data', data: [] };
}

// 9. Storage Facilities
export async function getStorageFacilities() {
  if (isExplicitDemoMode()) {
    return { success: true, data: DEMO_STORAGE, provenance: 'demo' };
  }

  const res = await apiCall('/api/v1/storage/facilities');
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load storage facilities', data: [] };
}

// 10. Grievances & Support Tickets
export async function getGrievances(farmerId = null) {
  if (isExplicitDemoMode()) {
    return { success: true, data: DEMO_GRIEVANCES, provenance: 'demo' };
  }

  const res = await apiCall(`/api/v1/disputes${farmerId ? `?farmer_id=${farmerId}` : ''}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load support tickets', data: [] };
}

export async function createGrievance(data) {
  if (isExplicitDemoMode()) {
    return {
      success: true,
      data: { id: `g-${Date.now()}`, ...data, status: 'OPEN', created_at: new Date().toISOString() },
      message: 'Support ticket submitted (Demo Mode)',
      provenance: 'demo'
    };
  }

  const res = await apiCall('/api/v1/disputes', { method: 'POST', body: JSON.stringify(data) });
  if (res && res.success) {
    return { ...res, provenance: 'live' };
  }
  return { success: false, error: res?.error || 'Failed to submit support ticket', message: res?.error };
}

// 11. Notifications
export async function getNotifications(unreadOnly = false) {
  if (isExplicitDemoMode()) {
    return { success: true, data: [], provenance: 'demo' };
  }

  const res = await apiCall(`/api/v1/notifications${unreadOnly ? '?unread_only=true' : ''}`);
  if (res && res.success && res.data) {
    const items = Array.isArray(res.data) ? res.data : (res.data.items || []);
    return { success: true, data: items, total: res.data.total || items.length, provenance: 'live' };
  }

  return { success: false, error: res?.error || 'Failed to load notifications', data: [] };
}

export async function markNotificationRead(notifId) {
  if (isExplicitDemoMode()) return { success: true };
  return apiCall(`/api/v1/notifications/${notifId}/read`, { method: 'POST' });
}

export async function markAllNotificationsRead() {
  if (isExplicitDemoMode()) return { success: true };
  return apiCall('/api/v1/notifications/read-all', { method: 'POST' });
}

// 12. Health & Readiness
export async function checkHealth() {
  const res = await apiCall('/api/v1/health');
  if (res && res.success) return res;
  return { success: false, mode: isExplicitDemoMode() ? 'demo' : 'offline', status: 'unreachable' };
}

// 13. Map Locations (Mandis, Buyers, Storage, FPOs)
export async function getMarketLocations({ category = 'all', state = null, district = null, near_lat = null, near_lng = null, radius_km = 150, search = null } = {}) {
  if (isExplicitDemoMode()) {
    const list = category === 'all' ? DEMO_MARKERS : DEMO_MARKERS.filter(m => m.type === category);
    return {
      success: true,
      data: {
        locations: list,
        counts: {
          all: DEMO_MARKERS.length,
          mandi: DEMO_MARKERS.filter(m => m.type === 'mandi').length,
          buyer: DEMO_MARKERS.filter(m => m.type === 'buyer').length,
          storage: DEMO_MARKERS.filter(m => m.type === 'storage').length,
          fpo: 0,
        },
        total: list.length,
      },
      provenance: 'demo'
    };
  }

  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (state && state !== 'All') params.append('state', state);
  if (district && district !== 'All') params.append('district', district);
  if (near_lat !== null && near_lat !== undefined) params.append('near_lat', near_lat);
  if (near_lng !== null && near_lng !== undefined) params.append('near_lng', near_lng);
  if (radius_km) params.append('radius_km', radius_km);
  if (search && search.trim()) params.append('search', search.trim());

  const res = await apiCall(`/api/v1/markets/locations?${params}`);
  if (res && res.success && res.data) {
    return { success: true, data: res.data, provenance: 'live' };
  }
  return { success: false, error: res?.error || 'Failed to load map locations', data: { locations: [], counts: {} } };
}

// 14. Live Government Mandi Prices
export async function getLivePrices({ crop = null, market = null, district = null, state = null, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (crop && crop !== 'All') params.append('crop', crop);
  if (market && market !== 'All') params.append('market', market);
  if (district && district !== 'All') params.append('district', district);
  if (state && state !== 'All') params.append('state', state);
  params.append('limit', limit);
  params.append('offset', offset);

  const res = await apiCall(`/api/v1/prices/live?${params}`);
  if (res && res.success && res.data) {
    return { success: true, data: res.data.items || [], is_live: res.data.is_live, source: res.source, total: res.data.total };
  }
  return { success: false, error: res?.error || 'Failed to load government mandi prices', data: [] };
}

