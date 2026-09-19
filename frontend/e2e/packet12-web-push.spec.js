import { expect, test } from '@playwright/test';

test('explicit push opt-in stays account-scoped on a shared browser', async ({ page }) => {
  test.setTimeout(60_000);
  const registrations = [];
  const deletedOwners = [];
  await page.addInitScript(() => {
    window.__permissionRequests = Number(sessionStorage.getItem('push-permission-requests') || 0);
    window.__subscribeCalls = Number(sessionStorage.getItem('push-subscribe-calls') || 0);
    const browserSubscription = (endpoint) => ({
      endpoint,
      toJSON: () => ({ endpoint, keys: { p256dh: 'public-key', auth: 'auth-key' } }),
      unsubscribe: async () => {
        sessionStorage.removeItem('push-subscription-endpoint');
        window.__pushSubscription = null;
        return true;
      },
    });
    window.__pushSubscription = sessionStorage.getItem('push-subscription-endpoint')
      ? browserSubscription(sessionStorage.getItem('push-subscription-endpoint'))
      : null;
    Object.defineProperty(window, 'Notification', {
      configurable: true,
      value: {
        permission: sessionStorage.getItem('push-permission') || 'default',
        requestPermission: async () => {
          window.__permissionRequests += 1;
          sessionStorage.setItem('push-permission-requests', String(window.__permissionRequests));
          window.Notification.permission = 'granted';
          sessionStorage.setItem('push-permission', 'granted');
          return 'granted';
        },
      },
    });
    window.PushManager = function PushManager() {};
    const registration = {
      pushManager: {
        getSubscription: async () => {
          const endpoint = sessionStorage.getItem('push-subscription-endpoint');
          window.__pushSubscription = endpoint ? browserSubscription(endpoint) : null;
          return window.__pushSubscription;
        },
        subscribe: async () => {
          window.__subscribeCalls += 1;
          sessionStorage.setItem('push-subscribe-calls', String(window.__subscribeCalls));
          const endpoint = `https://fcm.googleapis.com/fcm/send/device-${window.__subscribeCalls}`;
          sessionStorage.setItem('push-subscription-endpoint', endpoint);
          window.__pushSubscription = browserSubscription(endpoint);
          return window.__pushSubscription;
        },
      },
    };
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: {
        register: async () => registration,
        getRegistration: async () => registration,
        ready: Promise.resolve(registration),
      },
    });
  });
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();
    const body = route.request().postDataJSON?.() || {};
    if (url.pathname.endsWith('/auth/login')) {
      const email = body.email;
      const id = email.startsWith('a-') ? 'shared-farmer-a' : 'shared-farmer-b';
      return route.fulfill({ json: { success: true, data: { access_token: `token-${id}`, user: { id, full_name: id, role: 'farmer' } } } });
    }
    if (url.pathname.endsWith('/auth/logout')) return route.fulfill({ json: { success: true, data: {} } });
    if (url.pathname.endsWith('/auth/refresh')) return route.fulfill({ status: 401, json: { success: false } });
    if (url.pathname.endsWith('/auth/me')) return route.fulfill({ json: { success: true, data: { id: 'shared-farmer-a', full_name: 'Farmer', role: 'farmer' } } });
    if (url.pathname.endsWith('/notifications/push/capability')) return route.fulfill({ json: { success: true, data: { status: 'AVAILABLE', application_server_key: 'AQIDBA', explicit_opt_in: true } } });
    if (url.pathname.endsWith('/notifications/push/subscriptions/current') && method === 'DELETE') {
      deletedOwners.push(route.request().headers().authorization);
      return route.fulfill({ status: 503, json: { success: false } });
    }
    if (url.pathname.endsWith('/notifications/push/subscriptions') && method === 'POST') {
      registrations.push({ authorization: route.request().headers().authorization, body });
      return route.fulfill({ json: { success: true, data: { status: 'ACTIVE' } } });
    }
    return route.fulfill({ json: { success: true, data: { items: [], total: 0, pages: 1 } } });
  });

  async function login(email) {
    await page.goto('/login');
    await page.getByLabel(/mobile number or email/i).fill(email);
    await page.getByLabel(/^password$/i).fill('test-password');
    await page.getByRole('button', { name: /^log in/i }).click();
    await expect(page).toHaveURL(/\/farmer\/dashboard$/);
  }

  await login('a-farmer@example.test');
  await expect(page.getByRole('link', { name: /notification settings/i })).toBeVisible();
  await page.getByRole('link', { name: /notification settings/i }).click();
  await expect(page.getByRole('button', { name: /turn on notifications/i })).toBeVisible();
  expect(await page.evaluate(() => window.__permissionRequests)).toBe(0);
  await page.getByRole('button', { name: /turn on notifications/i }).click();
  await expect(page.getByText(/notifications are on for this browser/i)).toBeVisible();
  expect(await page.evaluate(() => window.__permissionRequests)).toBe(1);
  expect(registrations).toHaveLength(1);
  expect(registrations[0].authorization).toBe('Bearer token-shared-farmer-a');

  await page.getByRole('button', { name: /log out/i }).last().click();
  await login('b-farmer@example.test');
  expect(deletedOwners).toEqual(['Bearer token-shared-farmer-a']);
  await page.getByRole('link', { name: /notification settings/i }).click();
  await expect(page.getByRole('button', { name: /turn on notifications/i })).toBeVisible();
  expect(await page.evaluate(() => window.__pushSubscription)).toBeNull();
  expect(await page.evaluate(() => window.__permissionRequests)).toBe(1);
  expect(registrations).toHaveLength(1);
  await page.getByRole('button', { name: /turn on notifications/i }).click();
  await expect(page.getByText(/notifications are on for this browser/i)).toBeVisible();
  expect(registrations).toHaveLength(2);
  expect(registrations[1].authorization).toBe('Bearer token-shared-farmer-b');
  expect(registrations[1].body.endpoint).toContain('device-2');
  expect(await page.locator('.web-push-preferences button').evaluate((element) => element.getBoundingClientRect().height)).toBeGreaterThanOrEqual(48);

  for (const viewport of [
    { width: 360, height: 640 }, { width: 390, height: 844 },
    { width: 768, height: 1024 }, { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `no horizontal overflow at ${viewport.width}px`).toBe(true);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
    }
  }
});
