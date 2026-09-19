import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const cropId = '8a1b1c10-3b21-4eaa-a867-bb224b6ff901';
const crop = { id: cropId, name: 'Onion', name_en: 'Onion', name_hindi: 'प्याज', name_marathi: 'कांदा', default_unit: 'quintal', valid_units: ['quintal', 'kg'] };

async function login(page, email) {
  await page.goto('/login');
  await page.getByLabel(/mobile number or email/i).fill(email);
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/farmer\/dashboard$/);
}

test('farmer listing queue stays account-scoped and requires explicit foreground sync', async ({ page, context }) => {
  test.setTimeout(120_000);
  const lotPosts = [];
  const accountForEmail = (email) => email.startsWith('a-') ? 'farmer-account-a' : 'farmer-account-b';
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const { pathname } = url;
    const method = route.request().method();
    if (pathname.endsWith('/auth/login')) {
      const email = route.request().postDataJSON().email;
      const id = accountForEmail(email);
      return route.fulfill({ json: { success: true, data: { access_token: `token-${id}`, user: { id, full_name: id === 'farmer-account-a' ? 'Asha Farmer' : 'Bharat Farmer', role: 'farmer' } } } });
    }
    if (pathname.endsWith('/auth/logout')) return route.fulfill({ json: { success: true, data: {} } });
    if (pathname.endsWith('/users/me')) return route.fulfill({ json: { success: true, data: { district: 'Nashik', location: 'Nashik' } } });
    if (pathname.endsWith('/crops')) return route.fulfill({ json: { success: true, data: { items: [crop], total: 1 } } });
    if (pathname.endsWith('/prices')) return route.fulfill({ json: { success: true, data: { items: [], total: 0, pages: 1 } } });
    if (pathname.endsWith('/lots') && method === 'POST') {
      lotPosts.push({ payload: route.request().postDataJSON(), key: route.request().headers()['idempotency-key'] });
      return route.fulfill({ status: 201, json: { success: true, data: { id: 'lot-created-on-sync', public_id: 'KL-OFFLINE-1', original_quantity: '50', original_unit: 'quintal' } } });
    }
    return route.fulfill({ json: { success: true, data: { items: [], total: 0, pages: 1 } } });
  });

  await login(page, 'a-farmer@example.test');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('.app-mobile-nav a[href="/sell"]').click();
  await expect(page.getByLabel(/^Crop$/i)).toBeVisible();
  // Load the More route's lazy chunk while connected so the test reflects an
  // already-open app transitioning offline, rather than a cold browser cache.
  await page.locator('.app-mobile-nav a[href="/farmer/more"]').click();
  await expect(page.getByRole('heading', { name: /access and language help/i })).toBeVisible();
  await page.locator('.app-mobile-nav a[href="/sell"]').click();
  await expect(page.getByLabel(/^Crop$/i)).toBeVisible();
  await page.context().setOffline(true);
  await page.getByLabel(/^Crop$/i).selectOption(cropId);
  await page.locator('input.quantity-number').fill('50');
  await page.getByLabel(/asking price per quintal/i).fill('2500');
  await page.getByLabel(/village \/ collection location/i).fill('Nashik district');
  await page.getByRole('button', { name: /review( your)? listing/i }).click();
  await expect(page.getByText(/offline review only/i)).toBeVisible();
  await page.getByRole('button', { name: /save for sending later/i }).click();
  await expect(page.getByRole('heading', { name: /listing saved on this device/i })).toBeVisible();
  const queuedKey = await page.evaluate(() => new Promise((resolve, reject) => {
    const opening = indexedDB.open('krishilink-offline-v1');
    opening.onerror = () => reject(opening.error);
    opening.onsuccess = () => {
      const db = opening.result;
      const request = db.transaction('lot-create-queue', 'readonly').objectStore('lot-create-queue').getAll();
      request.onsuccess = () => {
        resolve(request.result.find((entry) => entry.ownerId === 'farmer-account-a')?.idempotencyKey || null);
        db.close();
      };
      request.onerror = () => reject(request.error);
    };
  }));
  expect(queuedKey).toBeTruthy();
  await page.getByRole('link', { name: /listings waiting for a connection/i }).click();
  await expect(page.getByText(/waiting to send/i)).toBeVisible();
  const simpleMode = page.getByRole('checkbox', { name: /use simple mode/i });
  await simpleMode.check();
  await expect(page.locator('.app-shell')).toHaveClass(/simple-mode/);
  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `${language} at ${viewport.width}px`).toBe(true);
    }
    if (viewport.width === 360) {
      const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
      expect(accessibility.violations).toEqual([]);
    }
  }
  await page.getByLabel(/language|भाषा/i).selectOption('en');

  await context.setOffline(false);
  await page.waitForTimeout(250);
  expect(lotPosts).toHaveLength(0);
  await page.locator('.app-header button').filter({ hasText: 'Log out' }).click();
  await login(page, 'b-farmer@example.test');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('.app-mobile-nav a[href="/farmer/more"]').click();
  await expect(page.getByText(/no saved listings are waiting/i)).toBeVisible();
  await expect(page.getByRole('checkbox', { name: /use simple mode/i })).not.toBeChecked();
  expect(lotPosts).toHaveLength(0);

  await page.locator('.app-header button').filter({ hasText: 'Log out' }).click();
  await login(page, 'a-farmer@example.test');
  await page.locator('.app-mobile-nav a[href="/farmer/more"]').click();
  await expect(page.getByText(/waiting to send/i)).toBeVisible();
  expect(lotPosts).toHaveLength(0);
  await page.getByRole('button', { name: /send saved listings now/i }).click();
  await expect(page.getByText(/server accepted 1 listing/i)).toBeVisible();
  expect(lotPosts).toHaveLength(1);
  expect(lotPosts[0].key).toBe(queuedKey);
  expect(lotPosts[0].payload).toMatchObject({ crop: cropId, quantity: '50', unit: 'quintal', location_text: 'Nashik district' });
  await expect(page.getByText(/no saved listings are waiting/i)).toBeVisible();
});

test('public reported prices use a dated saved snapshot on a network failure', async ({ page, context }) => {
  test.setTimeout(60_000);
  let failPriceRequest = false;
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/crops')) return route.fulfill({ json: { success: true, data: { items: [crop], total: 1 } } });
    if (url.pathname.endsWith('/prices')) {
      if (failPriceRequest) return route.abort('failed');
      return route.fulfill({ json: { success: true, data: { items: [{ id: 'reported-onion-1', crop: 'Onion', market: 'Lasalgaon APMC', district: 'Nashik', modal_price: '2450.00', unit: 'INR/quintal', price_date: '2026-09-17', source: 'AGMARKNET' }], total: 1, pages: 1 } } });
    }
    return route.fulfill({ json: { success: true, data: { items: [], total: 0, pages: 1 } } });
  });
  await page.goto('/prices?crop=Onion');
  await expect(page.getByText('AGMARKNET')).toBeVisible();
  await expect(page.getByText(/17 Sep 2026|17 Sept 2026/)).toBeVisible();
  failPriceRequest = true;
  await context.setOffline(true);
  await page.getByRole('button', { name: /refresh/i }).click();
  await expect(page.getByText(/saved prices/i)).toBeVisible();
  await expect(page.getByText('AGMARKNET')).toBeVisible();
  await expect(page.getByText(/17 Sep 2026|17 Sept 2026/)).toBeVisible();
});
