import { apiCall } from '../lib/http';
import { cachePublicSnapshot, readPublicSnapshot } from '../lib/offlineStore';
export { apiCall };
export const isExplicitDemoMode = () => false;
const query = (params = {}) =>
  new URLSearchParams(
    Object.entries(params).filter(
      ([, v]) => v !== null && v !== undefined && v !== '' && v !== 'All',
    ),
  ).toString();
async function list(path, params) {
  const queryString = query(params);
  const res = await apiCall(`/api/v1/${path}?${queryString}`);
  const normalized = res.success ? {
    success: true,
    data: Array.isArray(res.data) ? res.data : res.data?.items || [],
    total: res.data?.total,
    pages: res.data?.pages,
    provenance: 'api',
  } : null;
  if (normalized) {
    if (path === 'prices' || path === 'crops') {
      const key = `${path}:${queryString}`;
      void Promise.resolve(cachePublicSnapshot(key, normalized)).catch(() => undefined);
    }
    return normalized;
  }
  if ((path === 'prices' || path === 'crops') && (!res.status || !globalThis.navigator?.onLine)) {
    const cached = await readPublicSnapshot(`${path}:${queryString}`).catch(() => null);
    if (cached?.value?.success && Array.isArray(cached.value.data)) {
      return {
        ...cached.value,
        provenance: 'offline-cache',
        offline_cache: true,
        cached_at: cached.cachedAt,
      };
    }
  }
  if (!res.success) return { ...res, data: [] };
  return {
    ...res,
    ...normalized,
  };
}
const post = (path, data, key) =>
  apiCall(`/api/v1/${path}`, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
    ...(key ? { headers: { 'Idempotency-Key': key } } : {}),
  });
export const getPrices = (crop, market, limit = 100) => list('prices', { crop, market, limit });
export const getReportedPrices = (options = {}) =>
  list('prices', {
    limit: 30,
    ...(typeof options === 'number' ? { limit: Math.min(options, 100) } : options),
  });
// Compatibility alias for authenticated screens; the API contains daily reports, not live quotes.
export const getLivePrices = getReportedPrices;
export const getPriceHistory = (crop, market, days = 15) =>
  list(`prices/${encodeURIComponent(crop)}/history`, { market, days });
export const getPriceAlerts = () => list('intelligence/price-alerts', {});
export const createPriceAlert = (data, key) => post('intelligence/price-alerts', data, key);
export const disablePriceAlert = (id) => apiCall(`/api/v1/intelligence/price-alerts/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const getTrend = (crop, market) =>
  apiCall(`/api/v1/prices/trends/${encodeURIComponent(crop)}?${query({ market })}`);
export const syncPrices = (force = false) => post(`prices/sync?force=${force}`);
export const getCrops = () => list('crops', { limit: 100 });
export const getLots = (farmerId, options = {}) =>
  list('lots', { farmer_id: farmerId, limit: 100, ...options });
export const getMyLots = (options = {}) => list('lots/mine', { limit: 100, ...options });
export const getLot = (id) => apiCall(`/api/v1/lots/${encodeURIComponent(id)}`);
export const quoteLot = (data) => post('lots/quote', data);
export const createLot = (data, key) => post('lots', data, key);
export const updateLot = (id, data) => apiCall(`/api/v1/lots/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const withdrawLot = (id) => post(`lots/${id}/withdraw`);
export const getMyProfile = () => apiCall('/api/v1/users/me');
export const saveMyLocation = (coords) => apiCall('/api/v1/users/me/location', { method: 'PUT', body: JSON.stringify({ ...coords, consent: true }) });
export const getFarmerDashboardSummary = () => apiCall('/api/v1/lots/farmer-summary');
export const getMatches = (lot) => post('matches/refresh', { lot_id: lot.id || lot.lot_id });
export const getOffers = (params = {}) => list('offers', { limit: 100, ...params });
export const createOffer = (data, key) => post('offers', data, key);
export const acceptOffer = (id, key) => post(`offers/${id}/accept`, null, key);
export const rejectOffer = (id, reason, key) => post(`offers/${id}/reject`, reason ? { reason } : undefined, key);
export const counterOffer = (id, data, key) => post(`offers/${id}/counter`, data, key);
export const withdrawOffer = (id, key) => post(`offers/${id}/withdraw`, undefined, key);
export const getOfferHistory = (id) => list(`offers/${id}/history`, {});
export const updateOffer = (id, status) => post(`offers/${id}/${status.toLowerCase()}`);
export const getTransactions = (params = {}) => list('transactions', { limit: 100, ...params });
export const getTransaction = (id) => apiCall(`/api/v1/transactions/${id}`);
export const getTradeRoom = (id) => apiCall(`/api/v1/trades/${id}/room`);
export const listTrades = (params = {}) => list('trades', params);
export const transitionTrade = (id, toStatus, reason = null) =>
  post(`trades/${id}/transition`, { to_status: toStatus, reason });
export const addTradeNote = (id, note) => post(`trades/${id}/notes`, { note });
export const createOperationKey = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
export const reportTradePayment = (id, data, key) => post(`trades/${id}/payment-reports`, data, key);
export const acknowledgeTradePayment = (id, paymentId, key) =>
  post(`trades/${id}/payment-reports/${paymentId}/acknowledge`, undefined, key);
export const addTradeQualityReport = (id, data, key) => post(`trades/${id}/quality-reports`, data, key);
export const addTradeWeighment = (id, data, key) => post(`trades/${id}/weighments`, data, key);
export const addTradeLogisticsUpdate = (id, data, key) => post(`trades/${id}/logistics-updates`, data, key);
export const requestTradeStorage = (id, data, key) => post(`trades/${id}/storage-requests`, data, key);
export const uploadTradeEvidence = (id, file, classification, key) => {
  const form = new FormData();
  form.set('file', file);
  form.set('classification', classification);
  return apiCall(`/api/v1/trades/${encodeURIComponent(id)}/evidence`, {
    method: 'POST',
    body: form,
    headers: { 'Idempotency-Key': key },
  });
};
export const getMarkets = (params = {}) => list('markets', { limit: 100, ...params });
export const getPublicMarket = (slug) => apiCall(`/api/v1/markets/slug/${encodeURIComponent(slug)}`, { auth: false });
export const getPublicBuyers = (params = {}) => list('users/buyers', { limit: 20, ...params });
export const getMapMarkers = () => getMarkets();
export const getStorageFacilities = () => list('storage', {});
export const getNearbyBuyers = (params = {}) => list('users/buyers', params);
export const getGrievances = () => list('disputes', { limit: 100 });
export const createGrievance = (data) => post('disputes', data);
export const getNotifications = (unreadOnly = false) =>
  list('notifications', { unread_only: unreadOnly });
export const getRequirements = (params = {}) => list('requirements', params);
export const createRequirement = (data) => post('requirements', data);
export const closeRequirement = (id) => post(`requirements/${id}/close`);
export const discoverSupply = (params = {}) => list('requirements/discover/lots', params);
export const markNotificationRead = (id) => post(`notifications/${id}/read`);
export const markAllNotificationsRead = () => post('notifications/read-all');
export const checkHealth = () => apiCall('/api/v1/health');
export const getMarketLocations = (params = {}) =>
  apiCall(`/api/v1/markets/locations?${query(params)}`);
export const getFPOSummary = () => apiCall('/api/v1/fpo/summary');
export const getFPOMembers = () => list('fpo/members', {});
export const addFPOMember = (data) => post('fpo/members', data);
export const getFPOLots = () => list('fpo/lots', {});
export const createFPOAggregatedLot = (data) => post('fpo/aggregate-lot', data);
export const getFPOIntakes = () => list('fpo/intakes', {});
export const createFPOIntake = (data, key) => post('fpo/intakes', data, key);
export const getFPOPools = () => list('fpo/pools', {});
export const createFPOPool = (data, key) => post('fpo/pools', data, key);
export const publishFPOPool = (id, data, key) => post(`fpo/pools/${id}/publish`, data, key);
export const addFPOPoolContribution = (id, data, key) => post(`fpo/pools/${id}/contributions`, data, key);
export const removeFPOPoolContribution = (poolId, contributionId, key) => apiCall(`/api/v1/fpo/pools/${poolId}/contributions/${contributionId}`, { method: 'DELETE', ...(key ? { headers: { 'Idempotency-Key': key } } : {}) });
export const correctFPOIntake = (id, data, key) => post(`fpo/intakes/${id}/corrections`, data, key);
export const getFPOTrades = () => list('fpo/trades', {});
export const getFPOTradeTrace = (id) => apiCall(`/api/v1/fpo/trades/${encodeURIComponent(id)}/trace`);
export const previewFPOMemberImport = (csv) => apiCall('/api/v1/fpo/members/import/preview', { method: 'POST', headers: { 'Content-Type': 'text/csv; charset=utf-8' }, body: csv });
export const importFPOMembers = (csv, key) => apiCall('/api/v1/fpo/members/import', { method: 'POST', headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Idempotency-Key': key }, body: csv });
export const getOperationsOverview = () => apiCall('/api/v1/admin/system-health');
export const getVerificationQueue = (dimension) => apiCall(`/api/v1/admin/verification/queue?${query({ dimension })}`);
export const getFraudCases = (status) => apiCall(`/api/v1/admin/fraud/cases?${query({ status })}`);
export const getSupportContext = (id) => apiCall(`/api/v1/admin/support/users/${encodeURIComponent(id)}/context`);
export const getOutboxQueue = (status) => apiCall(`/api/v1/admin/outbox?${query({ status })}`);
export const getProviderHealth = () => apiCall('/api/v1/admin/provider-health');
export const getFeatureFlags = () => apiCall('/api/v1/admin/feature-flags');
