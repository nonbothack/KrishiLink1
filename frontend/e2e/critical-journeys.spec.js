import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('public home is responsive and has no serious accessibility violations', async ({ page }) => {
  await page.route('**/api/v1/prices**', route => route.fulfill({ json: { success: true, data: { items: [] } } }));
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByRole('link', { name: /list my crop/i })).toBeVisible();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(item => ['critical', 'serious'].includes(item.impact))).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
});

test('protected intent survives login and opens the farmer journey', async ({ page }) => {
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/auth/login')) {
      return route.fulfill({ json: { success: true, data: { access_token: 'test-token', user: { id: 'farmer-1', full_name: 'Ramesh Patil', email: 'ramesh@example.com', role: 'farmer' } } } });
    }
    if (url.pathname.endsWith('/lots/farmer-summary')) {
      return route.fulfill({ json: { success: true, data: { active_lots: 0, pending_offers: 0, total_sales: 0 } } });
    }
    return route.fulfill({ json: { success: true, data: { items: [] } } });
  });
  await page.goto('/sell');
  await expect(page).toHaveURL(/\/login\?next=/);
  await page.getByLabel(/mobile number or email/i).fill('ramesh@example.com');
  await page.getByLabel(/^password$/i).fill('demo123!');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/sell$/);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});
