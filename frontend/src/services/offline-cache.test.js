import { beforeEach, describe, expect, it, vi } from 'vitest';

const { apiCall, cachePublicSnapshot, readPublicSnapshot } = vi.hoisted(() => ({
  apiCall: vi.fn(),
  cachePublicSnapshot: vi.fn(),
  readPublicSnapshot: vi.fn(),
}));
vi.mock('../lib/http', () => ({ apiCall }));
vi.mock('../lib/offlineStore', () => ({ cachePublicSnapshot, readPublicSnapshot }));

import { getOffers, getReportedPrices } from './api';

describe('offline public snapshots', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
  });

  it('returns an explicitly marked saved public price snapshot after a network failure', async () => {
    apiCall.mockResolvedValue({ success: false, status: 0, error: 'network' });
    readPublicSnapshot.mockResolvedValue({
      key: 'prices:crop=Onion&limit=30',
      cachedAt: '2026-09-18T06:00:00.000Z',
      value: { success: true, data: [{ crop: 'Onion', modal_price: '2450.00', unit: 'INR/quintal', source: 'AGMARKNET', price_date: '2026-09-17' }], total: 1, pages: 1 },
    });

    const result = await getReportedPrices({ crop: 'Onion' });
    expect(result.provenance).toBe('offline-cache');
    expect(result.offline_cache).toBe(true);
    expect(result.cached_at).toBe('2026-09-18T06:00:00.000Z');
    expect(result.data[0]).toMatchObject({ source: 'AGMARKNET', price_date: '2026-09-17', unit: 'INR/quintal' });
  });

  it('caches successful public reports but never falls back to account-specific offers', async () => {
    apiCall.mockResolvedValue({ success: true, data: { items: [{ id: 'r1' }], total: 1, pages: 1 } });
    const prices = await getReportedPrices({ crop: 'Onion' });
    expect(prices.provenance).toBe('api');
    expect(cachePublicSnapshot).toHaveBeenCalledOnce();

    apiCall.mockResolvedValue({ success: false, status: 0, error: 'network' });
    const offers = await getOffers();
    expect(offers.success).toBe(false);
    expect(offers.data).toEqual([]);
    expect(readPublicSnapshot).not.toHaveBeenCalled();
  });
});
