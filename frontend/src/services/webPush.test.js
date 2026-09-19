import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({ apiCall: vi.fn() }));
vi.mock('../lib/http', () => api);

import { cleanupPushOnLogout, decodeApplicationServerKey, isPushSupported } from './webPush';

describe('Web Push browser helpers', () => {
  beforeEach(() => { api.apiCall.mockReset(); });

  it('decodes the VAPID application server key into bytes', () => {
    expect(Array.from(decodeApplicationServerKey('AQIDBA'))).toEqual([1, 2, 3, 4]);
  });

  it('reports unsupported when browser push primitives are absent', () => {
    expect(isPushSupported()).toBe(false);
  });

  it('removes the local subscription during logout even when server revocation is unavailable', async () => {
    const subscription = { endpoint: 'https://fcm.googleapis.com/fcm/send/shared', unsubscribe: vi.fn().mockResolvedValue(true) };
    const getRegistration = vi.fn().mockResolvedValue({ pushManager: { getSubscription: vi.fn().mockResolvedValue(subscription) } });
    Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: { getRegistration } });
    api.apiCall.mockResolvedValue({ success: false, status: 0 });
    await cleanupPushOnLogout();
    expect(subscription.unsubscribe).toHaveBeenCalledOnce();
    expect(api.apiCall).toHaveBeenCalledWith('/api/v1/notifications/push/subscriptions/current', expect.objectContaining({ method: 'DELETE' }));
  });
});
