import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('staff operations surface is protected, scoped and accessible', async ({ page }) => {
  await page.route('**/api/v1/admin/**', (route) => route.fulfill({ json: { success: true, data: { status: 'UNKNOWN', items: [] } } }));
  await page.route('**/api/v1/auth/refresh', (route) => route.fulfill({ json: { success: true, data: { access_token: 'test-access-token' } } }));
  await page.route('**/api/v1/auth/me', (route) => route.fulfill({ json: { success: true, data: { id: 'staff-1', full_name: 'Operations reviewer', role: 'support' } } }));
  await page.goto('/');
  await page.evaluate(() => {
    localStorage.setItem('krishilink_user', JSON.stringify({ id: 'staff-1', name: 'Operations reviewer', role: 'support' }));
    localStorage.setItem('krishilink_access_token', 'test-access-token');
  });
  await page.goto('/admin/operations');
  await expect(page.getByRole('heading', { name: 'Operations console' })).toBeVisible();
  await expect(page.getByText('Fraud entries are review signals.')).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag22aa']).analyze();
  expect(results.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
});
