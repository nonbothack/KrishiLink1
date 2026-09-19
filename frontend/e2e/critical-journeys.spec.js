import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('home adapts to mobile/tablet/desktop viewports and all supported languages', async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.route('**/api/v1/**', (route) =>
    route.fulfill({ json: { success: true, data: { items: [] } } }),
  );

  const viewports = [
    { width: 360, height: 640 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ];
  const languages = [
    { code: 'en', action: 'List my crop' },
    { code: 'hi', action: 'अपनी फसल दर्ज करें' },
    { code: 'mr', action: 'शेतमाल विक्रीसाठी नोंदवा' },
  ];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    for (const language of languages) {
      await page.goto('/');
      await page.evaluate((code) => localStorage.setItem('krishilink_lang', code), language.code);
      await page.reload();
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await expect(page.locator('html')).toHaveAttribute('lang', language.code);
      const primaryAction = page.getByRole('link', { name: language.action });
      await expect(primaryAction).toBeVisible();
      expect(
        await primaryAction.evaluate((element) => element.getBoundingClientRect().height),
      ).toBeGreaterThanOrEqual(48);

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      expect(results.violations, `${language.code} at ${viewport.width}px`).toEqual([]);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
        ),
      ).toBe(false);
    }
  }
});

test('public and sign-in routes retain accessible page structure', async ({ page }) => {
  test.setTimeout(120_000);
  await page.route('**/api/v1/**', (route) =>
    route.fulfill({ json: { success: true, data: { items: [] } } }),
  );

  for (const path of [
    '/',
    '/login',
    '/register',
    '/prices',
    '/map',
    '/help',
    '/terms',
    '/privacy',
    '/about',
  ]) {
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations, path).toEqual([]);
  }
});

test('public discovery uses dated reports, reviewed outlets and business-only buyer data', async ({ page }) => {
  const outletSlug = 'lasalgaon-apmc-nashik-maharashtra-111111111111';
  const crop = { id: 'crop-onion', name: 'Onion', name_en: 'Onion', name_hindi: 'प्याज', name_marathi: 'कांदा', slug: 'onion', default_unit: 'quintal', valid_units: ['quintal', 'kg'], aliases: [] };
  const price = { id: 'price-onion', crop: 'Onion', market: 'Lasalgaon APMC', district: 'Nashik', state: 'Maharashtra', modal_price: '2450.00', unit: 'INR/quintal', price_date: '2026-09-17', source: 'AGMARKNET', freshness_state: 'fresh', location_verified: true };
  const outlet = { id: '11111111-1111-4111-8111-111111111111', slug: outletSlug, name: 'Lasalgaon APMC', district: 'Nashik', state: 'Maharashtra', latitude: 20.14, longitude: 74.23, market_type: 'apmc_principal', outlet_type: 'apmc_principal', verification_status: 'verified', coordinate_source: 'reviewed_official_source', coordinate_confidence: 0.96, source_confidence: 0.97, source_name: 'AGMARKNET', source_url: 'javascript:alert(1)', last_reviewed_at: '2026-09-10T10:00:00Z' };
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data = { items: [], total: 0, pages: 1 };
    if (path.endsWith('/crops')) data = { items: [crop], total: 1, pages: 1 };
    else if (path.endsWith('/prices')) data = { items: [price], total: 1, pages: 1 };
    else if (path.endsWith('/markets/slug/' + outletSlug)) data = outlet;
    else if (path.endsWith('/markets')) data = { items: [outlet], total: 1, pages: 1 };
    else if (path.endsWith('/users/buyers')) data = [{ business_name: 'Nashik Produce Cooperative', type: 'cooperative', crops: ['Onion'], district: 'Nashik', state: 'Maharashtra', business_verification: 'verified', full_name: 'Private Person', phone: '+919876543210', email: 'private@example.test', location: 'Private Street' }];
    return route.fulfill({ json: { success: true, data } });
  });

  await page.goto('/prices/onion');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Onion');
  await expect(page.getByText('AGMARKNET')).toBeVisible();
  await expect(page.getByText(/17 Sept 2026|17 Sep 2026/)).toBeVisible();
  await expect(page).toHaveTitle(/Onion.*reported market prices/i);

  await page.goto('/mandis');
  await page.getByRole('link', { name: /View outlet/i }).click();
  await expect(page).toHaveURL(new RegExp(`/mandis/${outletSlug}$`));
  await expect(page.getByRole('heading', { level: 1, name: 'Lasalgaon APMC' })).toBeVisible();
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);

  await page.goto('/buyers');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByText('Nashik Produce Cooperative')).toBeVisible();
  for (const privateValue of ['Private Person', '+919876543210', 'private@example.test', 'Private Street']) {
    await expect(page.getByText(privateValue)).toHaveCount(0);
  }

  await page.goto('/contact');
  await expect(page.getByText(/public support phone number or email has not been configured/i)).toBeVisible();
  await expect(page.locator('#main').getByRole('link', { name: /sign in to raise or track a support request/i })).toBeVisible();
  await page.goto('/terms');
  await expect(page.locator('.policy-draft-notice')).toContainText(/draft.*legal review/i);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', /noindex/);

  for (const viewport of [
    { width: 360, height: 640 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    for (const path of ['/prices/onion', '/mandis', '/buyers', '/contact']) {
      await page.goto(path);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
      if (viewport.width === 360) {
        const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
        expect(results.violations, `${path} at 360px`).toEqual([]);
      }
    }
  }
});

test('public shell supports keyboard skip navigation and Escape to close its mobile menu', async ({
  page,
}) => {
  await page.route('**/api/v1/prices**', (route) =>
    route.fulfill({ json: { success: true, data: { items: [] } } }),
  );
  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('/');

  const skipLink = page.locator('.site-header .skip-link');
  await page.keyboard.press('Tab');
  await expect(skipLink).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();

  const menuToggle = page.getByRole('button', { name: /menu/i });
  await menuToggle.click();
  await expect(menuToggle).toHaveAttribute('aria-expanded', 'true');
  await page.keyboard.press('Escape');
  await expect(menuToggle).toHaveAttribute('aria-expanded', 'false');
  await expect(menuToggle).toBeFocused();
});

test('protected intent survives login and opens the farmer journey', async ({ page }) => {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/auth/login')) {
      return route.fulfill({
        json: {
          success: true,
          data: {
            access_token: 'test-token',
            user: {
              id: 'farmer-1',
              full_name: 'Ramesh Patil',
              email: 'ramesh@example.com',
              role: 'farmer',
            },
          },
        },
      });
    }
    if (url.pathname.endsWith('/lots/farmer-summary')) {
      return route.fulfill({
        json: { success: true, data: { active_lots: 0, pending_offers: 0, total_sales: 0 } },
      });
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
  const skipLink = page.locator('.app-shell > .skip-link');
  await skipLink.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('main#main')).toBeFocused();
});

test('farmer can create, receive, and disable a reported-price alert accessibly on all target viewports', async ({ page }) => {
  test.setTimeout(120_000);
  const cropId = '11111111-1111-4111-8111-111111111111';
  const marketId = '22222222-2222-4222-8222-222222222222';
  let rule = null;
  let payloadSeen = null;
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const { pathname } = url;
    const method = route.request().method();
    if (pathname.endsWith('/auth/login')) {
      return route.fulfill({ json: { success: true, data: { access_token: 'farmer-alert-token', user: { id: 'farmer-alert', full_name: 'Ramesh Patil', role: 'farmer' } } } });
    }
    if (pathname.endsWith('/crops')) {
      return route.fulfill({ json: { success: true, data: { items: [{ id: cropId, name: 'Onion' }], total: 1 } } });
    }
    if (pathname.endsWith('/markets')) {
      return route.fulfill({ json: { success: true, data: { items: [{ id: marketId, name: 'Lasalgaon APMC', district: 'Nashik' }], total: 1 } } });
    }
    if (pathname.endsWith('/intelligence/price-alerts') && method === 'GET') {
      return route.fulfill({ json: { success: true, data: { items: rule ? [rule] : [], total: rule ? 1 : 0 } } });
    }
    if (pathname.endsWith('/intelligence/price-alerts') && method === 'POST') {
      payloadSeen = route.request().postDataJSON();
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      rule = { id: '33333333-3333-4333-8333-333333333333', crop_id: cropId, crop: 'Onion', market_id: marketId,
        market: 'Lasalgaon APMC', threshold: payloadSeen.threshold, direction: payloadSeen.direction, unit: payloadSeen.unit,
        is_active: true, is_armed: true };
      return route.fulfill({ status: 201, json: { success: true, data: rule } });
    }
    if (pathname.endsWith(`/intelligence/price-alerts/${rule?.id}`) && method === 'DELETE') {
      rule = { ...rule, is_active: false };
      return route.fulfill({ json: { success: true, data: { id: rule.id, is_active: false } } });
    }
    return route.fulfill({ json: { success: true, data: { items: [], total: 0 } } });
  });

  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('/farmer/price-alerts');
  await expect(page).toHaveURL(/\/login\?next=/);
  await page.getByLabel(/mobile number or email/i).fill('ramesh@example.com');
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/farmer\/price-alerts$/);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await page.getByLabel('Crop').selectOption(cropId);
  await page.getByLabel('Market').selectOption(marketId);
  await page.getByLabel('Price limit').fill('2450');
  await page.getByRole('button', { name: 'Save alert' }).click();
  await expect(page.getByText(/ready for future reports/i)).toBeVisible();
  await expect(page.getByText('Onion · Lasalgaon APMC', { exact: true })).toBeVisible();
  expect(payloadSeen).toMatchObject({ crop_id: cropId, market_id: marketId, threshold: '2450', direction: 'AT_OR_ABOVE', unit: 'INR/quintal' });
  await page.getByRole('button', { name: /Disable.*Onion.*Lasalgaon/i }).click();
  await expect(page.getByText(/disabled/i)).toBeVisible();

  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `price alerts overflow at ${viewport.width}px in ${language}`).toBe(true);
      if (viewport.width === 360) {
        const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
        expect(results.violations, `price alerts ${language}`).toEqual([]);
      }
    }
  }
});

test('OTP login supports a six-digit code and exposes accessible verification controls', async ({
  page,
}) => {
  let verifiedCode = '';
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/auth/otp/request')) {
      return route.fulfill({
        json: {
          success: true,
          data: { message: 'If this number can receive a code, one will arrive.', resend_after_seconds: 30 },
        },
      });
    }
    if (url.pathname.endsWith('/auth/otp/verify')) {
      verifiedCode = route.request().postDataJSON().code;
      return route.fulfill({
        json: {
          success: true,
          data: {
            access_token: 'otp-test-token',
            user: { id: 'farmer-otp', full_name: 'Ramesh Patil', role: 'farmer' },
          },
        },
      });
    }
    if (url.pathname.endsWith('/lots/farmer-summary')) {
      return route.fulfill({
        json: { success: true, data: { active_lots: 0, pending_offers: 0, total_sales: 0 } },
      });
    }
    return route.fulfill({ json: { success: true, data: { items: [] } } });
  });

  await page.goto('/login');
  await page.getByLabel(/mobile number or email/i).fill('9876543210');
  await page.getByRole('button', { name: /get otp/i }).click();
  const digits = page.locator('.otp-inputs input');
  await expect(digits).toHaveCount(6);
  const code = '012345';
  for (let index = 0; index < code.length; index += 1) await digits.nth(index).fill(code[index]);

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(results.violations).toEqual([]);

  await page.getByRole('button', { name: /verify/i }).click();
  await expect(page).toHaveURL(/\/farmer\/dashboard$/);
  expect(verifiedCode).toBe(code);
});

test('farmer can review the dashboard, publish, accept an offer and open its trade record', async ({
  page,
}) => {
  test.setTimeout(120_000);
  const farmerId = 'farmer-pilot-06';
  const cropId = '2ee2ec6a-744e-40d0-93dc-b5a4b9a4c462';
  const lotId = '1a98ba1b-686a-452a-a39c-536a53b42e54';
  const offerId = 'b21f5a55-9310-4f60-a1ca-f66c66149cd2';
  const tradeId = '8bad2b53-04f5-4710-9b16-3fbfd4c34fb2';
  const crop = {
    id: cropId,
    name: 'Onion',
    name_en: 'Onion',
    name_hindi: 'प्याज',
    name_marathi: 'कांदा',
    default_unit: 'quintal',
    valid_units: ['quintal', 'kg'],
    varieties: [],
  };
  let lot = null;
  let accepted = false;
  const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString();
  await page.addInitScript(({ id, selectedCrop }) => {
    localStorage.setItem(`farmer-crops-${id}`, JSON.stringify([selectedCrop]));
    localStorage.setItem(`farmer-last-lot-${id}`, JSON.stringify({ crop: selectedCrop, quantity: '200', unit: 'quintal', price: '2450.00', grade: '' }));
  }, { id: farmerId, selectedCrop: cropId });

  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();
    const respond = (data, status = 200) => route.fulfill({ status, json: { success: true, data } });

    if (path.endsWith('/auth/login')) {
      return respond({ access_token: 'farmer-pilot-token', user: { id: farmerId, full_name: 'Ramesh Patil', role: 'farmer' } });
    }
    if (path.endsWith('/users/me')) {
      return respond({ id: farmerId, full_name: 'Ramesh Patil', district: 'Nashik', state: 'Maharashtra', location: 'Nashik' });
    }
    if (path.endsWith('/crops')) return respond({ items: [crop], total: 1 });
    if (path.endsWith('/lots/mine')) return respond({ items: lot ? [lot] : [], total: lot ? 1 : 0 });
    if (path.endsWith('/prices')) return respond({ items: [{
      crop: 'Onion',
      modal_price: '2400.00',
      unit: 'INR/quintal',
      market: 'Lasalgaon APMC',
      district: 'Nashik',
      price_date: new Date().toISOString().slice(0, 10),
      source: 'AGMARKNET',
      freshness_state: 'fresh',
      location_verified: true,
    }], total: 1 });
    if (path.endsWith('/markets')) return respond({ items: [], total: 0 });
    if (path.endsWith('/offers') && method === 'GET') {
      const items = lot ? [{
        id: offerId,
        lot_id: lotId,
        quantity: '200',
        unit: 'quintal',
        price_per_unit: '2520.00',
        total_value: '504000.00',
        status: accepted ? 'ACCEPTED' : 'PENDING',
        created_at: new Date().toISOString(),
        expires_at: expiresAt,
        crop_name: 'Onion',
        location: 'Nashik',
        buyer_name: 'Nashik Buyers Cooperative',
        buyer_verification_status: 'UNVERIFIED',
        transaction_id: accepted ? tradeId : null,
        trade_public_id: accepted ? 'KL-TRD-PILOT06' : null,
      }] : [];
      return respond({ items, total: items.length });
    }
    if (path.endsWith('/transactions')) {
      const items = accepted ? [{
        id: tradeId,
        public_id: 'KL-TRD-PILOT06',
        lot_id: lotId,
        status: 'CREATED',
        crop_name: 'Onion',
        quantity: 200,
        unit: 'quintal',
        gross_value: 504000,
      }] : [];
      return respond({ items, total: items.length });
    }
    if (path.endsWith('/notifications')) return respond({ items: [], total: 0 });
    if (path.endsWith('/lots/quote') && method === 'POST') {
      return respond({
        crop_id: cropId,
        crop: 'Onion',
        entered_quantity: '200',
        entered_unit: 'quintal',
        canonical_quantity: '200.00',
        canonical_unit: 'quintal',
        asking_price_per_quintal: '2450.00',
        indicative_gross: '490000.00',
        reference_price: null,
        price_warning: false,
        warning_threshold_pct: '50',
      });
    }
    if (path.endsWith('/lots') && method === 'POST') {
      const request = route.request().postDataJSON();
      lot = {
        id: lotId,
        public_id: 'KL-LOT-PILOT06',
        crop: 'Onion',
        crop_id: cropId,
        quantity: '200.00',
        unit: 'quintal',
        original_quantity: request.quantity,
        original_unit: request.unit,
        asking_price: request.asking_price,
        grade: request.grade,
        status: 'PUBLISHED',
        location: request.location_text,
        district: request.district,
      };
      return respond(lot, 201);
    }
    if (path.endsWith(`/offers/${offerId}/accept`) && method === 'POST') {
      accepted = true;
      return respond({ id: offerId, status: 'ACCEPTED', reservation_id: 'reservation-pilot-06', transaction_id: tradeId });
    }
    if (path.endsWith(`/trades/${tradeId}/room`)) {
      return respond({
        id: tradeId,
        public_id: 'KL-TRD-PILOT06',
        status: 'CREATED',
        created_at: new Date().toISOString(),
        buyer: { role: 'buyer', business_name: 'Nashik Buyers Cooperative' },
        seller: { role: 'farmer', full_name: 'Ramesh Patil' },
        terms: { crop_name: 'Onion', grade: 'UNSPECIFIED', quantity: 200, unit: 'quintal', price_per_unit: 2520, gross_value: 504000, created_at: new Date().toISOString() },
        payment: { status: 'NO_PROVIDER_DATA', gross_value: '504000.00', provider_connected: false, provider_verified: false, reports: [], legacy_unverified_count: 0 },
        logistics: { status: 'NOT_PROVIDER_CONNECTED', provider_connected: false },
        quality: { agreed_grade: 'UNSPECIFIED', verification_status: 'NOT_VERIFIED' },
        viewer_party: 'seller',
        next_action: { action_required: false, responsible_role: 'none', action_title: '', action_description: '', action_type: 'NONE', is_current_user_action: false },
        timeline: [],
      });
    }
    if (path.endsWith(`/trades/${tradeId}/quality-reports`) && method === 'POST') {
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      return respond({ id: 'quality-event-packet10', event_type: 'QUALITY_CLAIM', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (path.endsWith('/disputes')) return respond({ items: [], total: 0 });
    return respond({ items: [], total: 0 });
  });

  await page.goto('/login?next=%2Ffarmer%2Fdashboard');
  await page.getByLabel(/mobile number or email/i).fill('ramesh@example.test');
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/farmer\/dashboard$/);
  await expect(page.getByText(/Onion/)).toBeVisible();

  const auditFarmerScreen = async (label) => {
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(results.violations, label).toEqual([]);
  };
  const inspectSupportedLanguages = async () => {
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `${language} horizontal overflow`).toBe(true);
    }
    await page.getByLabel(/language|भाषा/i).selectOption('en');
  };

  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
      if (viewport.width === 360) {
        await expect(page.getByText(/Lasalgaon APMC/)).toBeVisible();
        const positions = await page.locator('.farmer-greeting-row, .farmer-price-card, .farmer-action-card, .farmer-sell-button').evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().bottom));
        expect(positions.every((bottom) => bottom <= 550), `${language} dashboard first viewport`).toBe(true);
      }
    }
  }

  await page.getByLabel(/language|भाषा/i).selectOption('en');
  await page.setViewportSize({ width: 360, height: 640 });
  await expect(page.getByText(/Nashik, Maharashtra/)).toBeVisible();
  await expect(page.getByText(/Lasalgaon APMC/)).toBeVisible();
  await expect(page.getByText(/AGMARKNET/)).toBeVisible();
  await expect(page.locator('.farmer-primary-actions a').first()).toBeVisible();
  const firstViewportPositions = await page.locator('.farmer-greeting-row, .farmer-price-card, .farmer-action-card, .farmer-primary-actions a').evaluateAll((elements) => elements.map((element) => ({ top: element.getBoundingClientRect().top, bottom: element.getBoundingClientRect().bottom })));
  expect(firstViewportPositions.every((item) => item.top >= 0 && item.bottom <= 550)).toBe(true);
  await page.screenshot({ path: 'test-results/packet06-dashboard-360-en.png' });
  await auditFarmerScreen('farmer dashboard, English, 360x640');

  let meaningfulActions = 0;
  await page.locator('.farmer-primary-actions').getByRole('link').first().click();
  meaningfulActions += 1;
  await inspectSupportedLanguages();
  await page.getByRole('button', { name: /review your listing/i }).click();
  meaningfulActions += 1;
  await expect(page.getByText('200 Quintal', { exact: false })).toBeVisible();
  await inspectSupportedLanguages();
  await page.getByRole('button', { name: /publish listing/i }).click();
  meaningfulActions += 1;
  expect(meaningfulActions).toBe(3);
  await expect(page.getByRole('heading', { name: /your crop is listed/i })).toBeVisible();
  await page.locator('.app-mobile-nav a[href="/farmer/dashboard"]').click();
  await expect(page.getByRole('heading', { level: 1, name: 'Ramesh Patil' })).toBeVisible();
  for (const language of ['en', 'hi', 'mr']) {
    await page.getByLabel(/language|भाषा/i).selectOption(language);
    await expect(page.locator('.farmer-action-link')).toBeVisible();
    const urgentFirstViewport = await page.locator('.farmer-greeting-row, .farmer-price-card, .farmer-action-card, .farmer-sell-button').evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().bottom));
    expect(urgentFirstViewport.every((bottom) => bottom <= 560), `${language} urgent dashboard stays above mobile navigation`).toBe(true);
  }
  await page.getByLabel(/language|भाषा/i).selectOption('en');
  await expect(page.getByText(/Offer for 200 qtl Onion expires soon/)).toBeVisible();
  await page.locator('.farmer-action-card').getByRole('link', { name: /view offers/i }).click();
  await expect(page.getByText('Nashik Buyers Cooperative')).toBeVisible();
  await inspectSupportedLanguages();
  const acceptOpener = page.getByRole('button', { name: /^accept offer$/i });
  await acceptOpener.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('dialog').getByRole('button', { name: /cancel/i })).toBeFocused();
  await expect(page.getByRole('dialog').getByText('₹5,04,000')).toBeVisible();
  await auditFarmerScreen('offer acceptance confirmation, English, 360x640');
  await page.keyboard.press('Tab');
  const dialogAccept = page.getByRole('dialog').getByRole('button', { name: /^accept offer$/i });
  await expect(dialogAccept).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#offer-action-status')).toBeFocused();
  await expect(page.getByText(/offer accepted/i)).toBeVisible();
  await page.getByRole('link', { name: /open trade/i }).click();
  await expect(page.getByRole('heading', { name: /trade room/i })).toBeVisible();
  await expect(page.getByText('Nashik Buyers Cooperative')).toBeVisible();
  await expect(page.getByRole('heading', { name: /agreed terms/i })).toBeVisible();
  await expect(page.getByText(/provider not connected/i)).toBeVisible();
  await expect(page.getByText(/not bank verification/i)).toBeVisible();
  const qualityPanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Quality statements' });
  await qualityPanel.locator('summary').click();
  await qualityPanel.getByLabel(/My quality statement/i).fill('Produce was sorted before pickup.');
  await qualityPanel.getByRole('button', { name: /Record statement/i }).click();
  await expect(page.getByText(/Update recorded in the trade timeline/i)).toBeVisible();
  await auditFarmerScreen('trade room, English, 360x640');
  for (const viewport of [
    { width: 360, height: 640 },
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      await expect(page.getByRole('heading', { name: /trade room|व्यवहार कक्ष|व्यापार कक्ष/i })).toBeVisible();
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth),
        `trade room ${language} horizontal overflow at ${viewport.width}px`,
      ).toBe(true);
      if (viewport.width === 360) await auditFarmerScreen(`trade room ${language}, 360x640`);
    }
  }
  await page.setViewportSize({ width: 360, height: 640 });
  await page.getByLabel(/language|भाषा/i).selectOption('en');
  await expect(page.getByRole('link', { name: /report a problem/i })).toHaveAttribute('href', new RegExp(`/grievances\\?trade=${tradeId}`));

  await page.locator('.app-mobile-nav a[href="/farmer/dashboard"]').click();
  await page.getByRole('link', { name: /view all lots/i }).click();
  await expect(page.getByRole('heading', { name: /my lots/i })).toBeVisible();
  await expect(page.getByText('KL-LOT-PILOT06')).toBeVisible();
  await expect(page.getByRole('link', { name: /manage listing/i })).toBeVisible();
  await auditFarmerScreen('my lots, English, 360x640');
  await page.getByRole('link', { name: /more/i }).click();
  await expect(page.getByRole('heading', { name: /more/i })).toBeVisible();
  await page.getByRole('link', { name: /report a problem/i }).click();
  await expect(page.getByRole('heading', { name: /support/i })).toBeVisible();
});

test('first-time farmer chooses a canonical crop and reviews before publishing', async ({ page }) => {
  const farmerId = 'farmer-first-time-06';
  const cropId = 'c117ac78-d231-4c2a-89a2-34b9d3c4a7c0';
  let lot = null;
  let actions = 0;
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();
    const respond = (data, status = 200) => route.fulfill({ status, json: { success: true, data } });
    if (path.endsWith('/auth/login')) return respond({ access_token: 'first-time-token', user: { id: farmerId, full_name: 'Asha More', role: 'farmer' } });
    if (path.endsWith('/users/me')) return respond({ id: farmerId, full_name: 'Asha More', district: 'Pune', state: 'Maharashtra', location: 'Pune District' });
    if (path.endsWith('/crops')) return respond({ items: [{ id: cropId, name: 'Tomato', name_en: 'Tomato', name_hindi: 'टमाटर', name_marathi: 'टोमॅटो', default_unit: 'quintal', valid_units: ['quintal'], varieties: [] }], total: 1 });
    if (path.endsWith('/lots/mine')) return respond({ items: lot ? [lot] : [], total: lot ? 1 : 0 });
    if (path.endsWith('/prices')) return respond({ items: [], total: 0 });
    if (path.endsWith('/offers') || path.endsWith('/transactions') || path.endsWith('/notifications')) return respond({ items: [], total: 0 });
    if (path.endsWith('/lots/quote') && method === 'POST') {
      const request = route.request().postDataJSON();
      return respond({ crop_id: cropId, crop: 'Tomato', entered_quantity: request.quantity, entered_unit: request.unit, canonical_quantity: request.quantity, canonical_unit: 'quintal', asking_price_per_quintal: null, indicative_gross: null, reference_price: null, price_warning: false, warning_threshold_pct: '50' });
    }
    if (path.endsWith('/lots') && method === 'POST') {
      const request = route.request().postDataJSON();
      lot = { id: '5f0b6d1a-5392-4bdd-b3cd-55332712a3a8', public_id: 'KL-LOT-FIRST06', crop: 'Tomato', crop_id: cropId, quantity: request.quantity, unit: 'quintal', original_quantity: request.quantity, original_unit: request.unit, status: 'PUBLISHED', location: request.location_text };
      return respond(lot, 201);
    }
    return respond({ items: [], total: 0 });
  });

  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('/login?next=%2Ffarmer%2Fdashboard');
  await page.getByLabel(/mobile number or email/i).fill('asha@example.test');
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page.getByRole('heading', { name: /which crops do you sell/i })).toBeVisible();
  await page.locator('.farmer-primary-actions').getByRole('link').first().click();
  actions += 1;
  await page.getByLabel(/^crop$/i).selectOption(cropId);
  actions += 1;
  await page.getByLabel(/^quantity$/i).fill('100');
  actions += 1;
  await expect(page.getByLabel(/collection location/i)).toHaveValue('Pune District');
  await page.getByRole('button', { name: /review your listing/i }).click();
  actions += 1;
  await expect(page.getByText(/No asking price/i)).toBeVisible();
  await expect(page.locator('.review-list').getByText(/indicative gross/i)).toHaveCount(0);
  await page.getByRole('button', { name: /publish listing/i }).click();
  actions += 1;
  expect(actions).toBe(5);
  await expect(page.getByText('KL-LOT-FIRST06')).toBeVisible();
});

test('FPO records intake, pools and publishes it, then follows offer to trade trace', async ({ page }) => {
  test.setTimeout(90_000);
  page.setDefaultTimeout(10_000);
  const fpoId = 'fpo-packet08a';
  const cropId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a0';
  const memberId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a1';
  const importedMemberId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928b1';
  const intakeId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a2';
  const poolId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a3';
  const lotId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a4';
  const offerId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a5';
  const counterId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a6';
  const tradeId = 'e44edff0-7eb1-4a15-a14c-0bc8f4b928a7';
  const crop = { id: cropId, name: 'Onion', name_hindi: 'प्याज', name_marathi: 'कांदा', default_unit: 'quintal', valid_units: ['quintal', 'kg'] };
  let members = [];
  let intakes = [];
  let pools = [];
  let lots = [];
  let trades = [];
  let counterCreated = false;
  let offerRows = [];
  const respond = (route, data, status = 200) => route.fulfill({ status, json: { success: true, data, message: 'Saved' } });

  await page.route('**/api/v1/**', async (route) => {
    const { pathname } = new URL(route.request().url());
    const method = route.request().method();
    const payload = () => route.request().postDataJSON();
    if (pathname.endsWith('/auth/login')) return respond(route, { access_token: 'fpo-packet08a-token', user: { id: fpoId, full_name: 'Nashik Farmers Collective', role: 'fpo' } });
    if (pathname.endsWith('/crops')) return respond(route, { items: [crop], total: 1 });
    if (pathname.endsWith('/fpo/members') && method === 'GET') return respond(route, { items: members, total: members.length });
    if (pathname.endsWith('/fpo/members') && method === 'POST') {
      const body = payload();
      const member = { id: memberId, farmer_name: body.farmer_name, primary_crop: 'Onion', grade: body.grade, available_quantity_qtl: '0' };
      members = [member]; return respond(route, member, 201);
    }
    if (pathname.endsWith('/fpo/members/import/preview')) return respond(route, {
      preview: true, accepted_count: 1, rejected_count: 0,
      accepted: [{ member_code: 'F-02', farmer_name: 'Imported Member', phone: '+919876543218', primary_crop: 'Onion', grade: 'A', land_acres: '1' }], rejected: [],
    });
    if (pathname.endsWith('/fpo/members/import')) {
      const importedMember = { id: importedMemberId, member_code: 'F-02', farmer_name: 'Imported Member', primary_crop: 'Onion', grade: 'A', available_quantity_qtl: '0' };
      members = [importedMember, ...members];
      return respond(route, { preview: false, accepted_count: 1, rejected_count: 0, accepted: [{ member_code: 'F-02', farmer_name: 'Imported Member' }], rejected: [] }, 201);
    }
    if (pathname.endsWith('/fpo/intakes') && method === 'GET') return respond(route, { items: intakes, total: intakes.length });
    if (pathname.endsWith('/fpo/intakes') && method === 'POST') {
      const body = payload();
      const receipt = { id: intakeId, receipt_id: 'KL-INT-08A', member_id: memberId, crop: 'Onion', grade: body.grade, gross_quantity: body.gross_quantity, tare_quantity: body.tare_quantity, net_quantity: '1000', unit: 'kg', canonical_quantity_qtl: '10.000', available_quantity_qtl: '10.000', is_voided: false };
      intakes = [receipt]; return respond(route, receipt, 201);
    }
    if (pathname.endsWith('/fpo/pools') && method === 'GET') return respond(route, { items: pools, total: pools.length });
    if (pathname.endsWith('/fpo/pools') && method === 'POST') {
      const pool = { id: poolId, pool_id: 'KL-POOL-08A', crop: 'Onion', grade: 'A', quantity_qtl: '10.000', status: 'READY', contribution_count: 1 };
      pools = [pool]; intakes = intakes.map((item) => ({ ...item, available_quantity_qtl: '0' }));
      return respond(route, pool, 201);
    }
    if (pathname.endsWith(`/fpo/pools/${poolId}/publish`) && method === 'POST') {
      pools = pools.map((pool) => ({ ...pool, status: 'PUBLISHED', lot_id: lotId }));
      lots = [{ id: lotId, public_id: 'KL-LOT-08A', crop: 'Onion', quantity: '10.00', unit: 'quintal', status: 'PUBLISHED' }];
      return respond(route, lots[0], 201);
    }
    if (pathname.endsWith('/fpo/lots')) return respond(route, { items: lots, total: lots.length });
    if (pathname.endsWith('/fpo/trades')) return respond(route, { items: trades, total: trades.length });
    if (pathname.endsWith('/offers') && method === 'GET') return respond(route, { items: offerRows, total: offerRows.length });
    if (pathname.endsWith(`/offers/${offerId}/counter`) && method === 'POST') {
      counterCreated = true;
      offerRows = [
        { ...offerRows[0], status: 'COUNTERED' },
        { ...offerRows[0], id: counterId, parent_offer_id: offerId, price_per_unit: payload().price_per_unit, total_value: '10500.00', status: 'PENDING', message: 'Counter sent' },
      ];
      return respond(route, { id: counterId, status: 'PENDING', parent_offer_id: offerId });
    }
    if (pathname.endsWith(`/trades/${tradeId}/room`)) return respond(route, {
      id: tradeId, public_id: 'KL-TRD-08A', status: 'CREATED', created_at: new Date().toISOString(), buyer: { role: 'buyer', business_name: 'Nashik Buyers Cooperative' }, seller: { role: 'fpo', full_name: 'Nashik Farmers Collective' },
      terms: { crop_name: 'Onion', grade: 'A', quantity: 5, unit: 'quintal', price_per_unit: 2100, gross_value: 10500, created_at: new Date().toISOString() },
      payment: { status: 'UNAVAILABLE', gross_value: 10500 }, logistics: { status: 'PENDING' }, quality: { agreed_grade: 'A', verification_status: 'UNVERIFIED' },
      next_action: { action_required: false, responsible_role: 'none', action_title: 'Trade recorded', action_description: 'No action is waiting.', action_type: 'NONE', is_current_user_action: false }, timeline: [],
    });
    if (pathname.endsWith(`/fpo/trades/${tradeId}/trace`)) return respond(route, {
      trade_id: tradeId, trade_reference: 'KL-TRD-08A', quantity_qtl: '5.000', gross: '10500.00', allocations: [
        { member_id: memberId, member_name: 'Asha Member', intake_receipt_id: 'KL-INT-08A', pool_id: 'KL-POOL-08A', contribution_id: 'contribution-08a', sold_quantity_qtl: '5.000', gross_allocation: '10500.00', payout_status: 'PROJECTED' },
      ],
    });
    if (pathname.endsWith('/transactions')) return respond(route, { items: [], total: 0 });
    if (pathname.endsWith('/notifications')) return respond(route, { items: [], total: 0 });
    if (pathname.endsWith('/auth/logout')) return respond(route, {});
    if (pathname.endsWith('/requirements/discover/lots')) return respond(route, { items: [], total: 0 });
    if (pathname.endsWith('/offers') && method === 'POST') return respond(route, {}, 201);
    if (pathname.endsWith('/users/me')) return respond(route, { id: fpoId, full_name: 'Nashik Farmers Collective', role: 'fpo' });
    if (pathname.endsWith('/offers') && method === 'GET') return respond(route, { items: offerRows, total: offerRows.length });
    return respond(route, { items: [], total: 0 });
  });

  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('/login');
  await page.getByLabel(/mobile number or email/i).fill('fpo@example.test');
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/fpo\/dashboard$/);
  await expect(page.getByRole('heading', { level: 1, name: 'Nashik Farmers Collective' })).toBeVisible();

  const memberForm = page.locator('#fpo-members-heading').locator('..').locator('form');
  await memberForm.getByLabel('Member name').fill('Asha Member');
  await memberForm.getByLabel('Primary crop').selectOption('Onion');
  await memberForm.getByRole('button', { name: 'Add member' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#fpo-members-heading').locator('..').getByText('Asha Member', { exact: true })).toBeVisible();
  const memberSection = page.locator('#fpo-members-heading').locator('..');
  await memberSection.locator('summary').click();
  const rosterCsv = 'member_code,farmer_name,phone,village,district,primary_crop,grade,land_acres\nF-02,Imported Member,9876543218,Nashik,Nashik,Onion,A,1\n';
  await memberSection.getByLabel(/Choose a CSV file/).setInputFiles({
    name: 'members.csv', mimeType: 'text/csv', buffer: Buffer.from(rosterCsv),
  });
  await memberSection.getByRole('button', { name: 'Preview import' }).click();
  await expect(memberSection.getByText(/Accepted rows: 1/)).toBeVisible();
  await memberSection.getByRole('button', { name: 'Import accepted members' }).click();
  await expect(memberSection.getByText('Imported Member', { exact: true })).toBeVisible();

  const intakeForm = page.locator('#fpo-intake-heading').locator('..').locator('form');
  await intakeForm.getByLabel('Members').selectOption(memberId);
  await intakeForm.getByLabel('Crop').selectOption(cropId);
  await intakeForm.getByLabel('Gross quantity').fill('1000');
  await intakeForm.getByLabel('Tare quantity').fill('0');
  await intakeForm.getByRole('button', { name: 'Intake receipt' }).click();
  const intakeSection = page.locator('#fpo-intake-heading').locator('..');
  await expect(intakeSection.getByText('Receipt number: KL-INT-08A', { exact: true })).toBeVisible();
  await expect(intakeSection.getByText(/10\.000 Quintal/)).toBeVisible();

  await page.getByLabel(/Contribution quantity/).fill('10');
  await page.getByRole('button', { name: 'Create pool' }).click();
  await expect(page.locator('#fpo-pool-heading').locator('..').getByText('KL-POOL-08A', { exact: true })).toBeVisible();
  await page.getByLabel(/Asking price per quintal/).fill('2100');
  await page.getByLabel(/Lot location/).fill('Nashik District');
  await page.getByRole('button', { name: 'Publish pool' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('KL-LOT-08A')).toBeVisible();

  offerRows = [{ id: offerId, lot_id: lotId, quantity: '5', unit: 'quintal', price_per_unit: '2000.00', total_value: '10000.00', status: 'PENDING', created_at: new Date().toISOString(), expires_at: new Date(Date.now() + 3600000).toISOString(), crop_name: 'Onion', location: 'Nashik District', buyer_name: 'Nashik Buyers Cooperative', buyer_verification_status: 'UNVERIFIED', transaction_id: null }];
  await page.getByRole('link', { name: 'Offers' }).first().click();
  await expect(page.getByText('Nashik Buyers Cooperative')).toBeVisible();
  await page.getByRole('button', { name: 'Counter offer', exact: true }).click();
  await page.getByLabel(/Your price/).fill('2100');
  await page.getByRole('button', { name: /Send counter offer/ }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText(/Your counter offer was sent/)).toBeVisible();
  expect(counterCreated).toBe(true);

  // The browser fixture models the buyer accepting the persisted counter; the API contract
  // test exercises the real buyer-authenticated acceptance path.
  trades = [{ id: tradeId, trade_reference: 'KL-TRD-08A', crop: 'Onion', status: 'CREATED', gross: '10500.00' }];
  await page.locator('.app-mobile-nav a[href="/fpo/dashboard"]').click();
  await expect(page.getByText('KL-TRD-08A')).toBeVisible();
  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `${language} at ${viewport.width}px`).toBe(true);
    }
  }
  await page.getByLabel(/language|भाषा/i).selectOption('en');
  const dashboardA11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
  expect(dashboardA11y.violations).toEqual([]);
  await page.getByRole('button', { name: 'View member allocation' }).click();
  await expect(page.getByText(/Projected allocation · 5\.000 Quintal/)).toBeVisible();
  await expect(page.getByText(/Asha Member · KL-INT-08A/)).toBeVisible();
  const allocationA11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
  expect(allocationA11y.violations).toEqual([]);
  await page.getByRole('link', { name: 'Open Trade Room' }).click();
  await expect(page.getByRole('heading', { name: /Trade Room/i })).toBeVisible();
  const tradeA11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
  expect(tradeA11y.violations).toEqual([]);
});

test('Trade Room records participant operations, pending storage and uploaded evidence', async ({ page }) => {
  test.setTimeout(120_000);
  const tradeId = 'd10a6f5b-4c32-4d10-a6f5-b4c32d10a6f5';
  const facilityId = 'd10a6f5b-4c32-4d10-a6f5-b4c32d10faci';
  const buyerId = 'buyer-packet10';
  const evidenceId = 'evidence-packet10';
  const paymentId = 'payment-packet10';
  const event = (id, event_type, title, metadata = null) => ({
    id,
    transaction_id: tradeId,
    actor_id: buyerId,
    actor_role: 'buyer',
    event_type,
    from_status: 'CREATED',
    to_status: 'CREATED',
    title,
    description: null,
    source_kind: 'PARTICIPANT_REPORTED',
    metadata,
    created_at: new Date().toISOString(),
  });
  const room = {
    id: tradeId,
    public_id: 'KL-TRD-PACKET10',
    status: 'CREATED',
    created_at: new Date().toISOString(),
    buyer: { role: 'buyer', business_name: 'Nashik Buyers Cooperative' },
    seller: { role: 'farmer', full_name: 'Ramesh Patil' },
    terms: { crop_name: 'Onion', grade: 'A', quantity: '20.000', unit: 'quintal', price_per_unit: '2100.00', gross_value: '42000.00', created_at: new Date().toISOString() },
    payment: { status: 'NO_PROVIDER_DATA', gross_value: '42000.00', provider_connected: false, provider_verified: false, reports: [], legacy_unverified_count: 0 },
    logistics: { status: 'NOT_PROVIDER_CONNECTED', provider_connected: false },
    quality: { agreed_grade: 'A', verification_status: 'NOT_VERIFIED' },
    next_action: { action_required: false, responsible_role: 'none', action_title: '', action_description: '', action_type: 'NONE', is_current_user_action: false },
    storage_requests: [],
    evidence: [],
    viewer_party: 'buyer',
    timeline: [],
  };
  const operationPaths = [];
  const respond = (route, data, status = 200) => route.fulfill({ status, json: { success: true, data } });

  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const { pathname } = url;
    const method = route.request().method();
    if (pathname.endsWith('/auth/login')) {
      return respond(route, { access_token: 'buyer-packet10-token', user: { id: buyerId, full_name: 'Nashik Buyers Cooperative', role: 'buyer' } });
    }
    if (pathname.endsWith('/users/me')) return respond(route, { id: buyerId, full_name: 'Nashik Buyers Cooperative', role: 'buyer' });
    if (pathname.endsWith('/storage')) {
      return respond(route, { items: [{ id: facilityId, name: 'Reviewed facility', is_demo: false, source_kind: 'REVIEWED_PARTNER', availability: 'NOT_CURRENTLY_CONFIRMED', rate: 'NOT_CURRENTLY_CONFIRMED' }] });
    }
    if (pathname.endsWith(`/trades/${tradeId}/room`)) return respond(route, room);
    if (pathname.endsWith(`/trades/${tradeId}/payment-reports`) && method === 'POST') {
      operationPaths.push('payment');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      const payload = route.request().postDataJSON();
      room.payment.reports = [{ id: paymentId, amount: payload.amount, currency: 'INR', reference: payload.reference, status: 'BUYER_REPORTED_SENT', source_kind: 'PARTICIPANT_REPORTED', reported_at: new Date().toISOString(), reported_by_role: 'buyer', seller_acknowledged: false }];
      room.payment.status = 'PARTICIPANT_REPORTED';
      room.timeline.push(event('event-payment-packet10', 'PAYMENT_REPORTED_SENT', 'Buyer reported payment sent'));
      return respond(route, { id: 'event-payment-packet10', event_type: 'PAYMENT_REPORTED_SENT', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (pathname.endsWith(`/trades/${tradeId}/quality-reports`) && method === 'POST') {
      operationPaths.push('quality');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      room.quality.verification_status = 'PARTICIPANT_REPORTED';
      room.timeline.push(event('event-quality-packet10', 'QUALITY_CLAIM', 'Participant quality statement'));
      return respond(route, { id: 'event-quality-packet10', event_type: 'QUALITY_CLAIM', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (pathname.endsWith(`/trades/${tradeId}/weighments`) && method === 'POST') {
      operationPaths.push('weighment');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      room.timeline.push(event('event-weighment-packet10', 'WEIGHMENT_REPORTED', 'Participant reported weighment', { net_quantity: '19.500', gross_quantity: '20.000', tare_quantity: '0.500', difference_quantity: '0.500', unit: 'quintal' }));
      return respond(route, { id: 'event-weighment-packet10', event_type: 'WEIGHMENT_REPORTED', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (pathname.endsWith(`/trades/${tradeId}/logistics-updates`) && method === 'POST') {
      operationPaths.push('logistics');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      room.timeline.push(event('event-logistics-packet10', 'LOGISTICS_RECEIPT_CONFIRMED', 'Buyer confirmed receipt'));
      return respond(route, { id: 'event-logistics-packet10', event_type: 'LOGISTICS_RECEIPT_CONFIRMED', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (pathname.endsWith(`/trades/${tradeId}/storage-requests`) && method === 'POST') {
      operationPaths.push('storage');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      room.storage_requests = [{ id: 'storage-request-packet10', facility_name: 'Reviewed facility', quantity: '20.000', unit: 'quintal', status: 'REQUESTED', confirmation_status: 'PENDING_FACILITY_CONFIRMATION' }];
      room.timeline.push(event('event-storage-packet10', 'STORAGE_REQUESTED', 'Storage request sent; confirmation pending'));
      return respond(route, { id: 'event-storage-packet10', event_type: 'STORAGE_REQUESTED', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    if (pathname.endsWith(`/trades/${tradeId}/evidence`) && method === 'POST') {
      operationPaths.push('evidence');
      expect(route.request().headers()['idempotency-key']).toBeTruthy();
      room.evidence = [{ id: evidenceId, classification: 'QUALITY_PHOTO', provenance_status: 'PARTICIPANT_SUBMITTED', mime_type: 'image/png', file_size_bytes: 27, original_filename: 'quality.png', url: null }];
      room.timeline.push(event('event-evidence-packet10', 'EVIDENCE_SUBMITTED', 'Participant submitted evidence'));
      return respond(route, { id: 'event-evidence-packet10', evidence_id: evidenceId, event_type: 'EVIDENCE_SUBMITTED', source_kind: 'PARTICIPANT_REPORTED' }, 201);
    }
    return respond(route, { items: [], total: 0 });
  });

  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto(`/login?next=${encodeURIComponent(`/trades/${tradeId}`)}`);
  await page.getByLabel(/mobile number or email/i).fill('buyer@example.test');
  await page.getByLabel(/^password$/i).fill('test-password');
  await page.getByRole('button', { name: /^log in/i }).click();
  await expect(page).toHaveURL(/\/buyer\/dashboard$/);
  await page.goto(`/trades/${tradeId}`);
  await expect(page).toHaveURL(`/trades/${tradeId}`);
  await expect(page.getByText(/reference or seller acknowledgement is not bank verification/i)).toBeVisible();

  await page.getByLabel(/Payment reference entered by buyer/i).fill('BUYER-REPORTED-REF');
  await page.getByRole('button', { name: /I sent this payment/i }).click();
  await expect(page.getByText(/BUYER-REPORTED-REF/)).toBeVisible();
  await expect(page.getByText(/Seller has not acknowledged/i)).toBeVisible();

  const qualityPanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Quality statements' });
  await qualityPanel.locator('summary').click();
  await qualityPanel.getByLabel(/My quality statement/i).fill('Produce was checked visually before pickup.');
  await qualityPanel.getByRole('button', { name: /Record statement/i }).click();

  const weighmentPanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Weighment record' });
  await weighmentPanel.locator('summary').click();
  await weighmentPanel.getByLabel(/Gross quantity/i).fill('20');
  await weighmentPanel.getByLabel(/Tare quantity/i).fill('0.5');
  await weighmentPanel.getByRole('button', { name: /Record weighment/i }).click();

  const logisticsPanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Pickup and delivery updates' });
  await logisticsPanel.locator('summary').click();
  await logisticsPanel.getByLabel(/Pickup and delivery updates/i).selectOption('RECEIPT_CONFIRMED');
  await logisticsPanel.getByRole('button', { name: /Record update/i }).click();

  const storagePanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Storage request' });
  await storagePanel.locator('summary').click();
  await storagePanel.getByLabel(/Choose a facility/i).selectOption(facilityId);
  await storagePanel.getByRole('button', { name: /Send storage request/i }).click();
  await storagePanel.locator('summary').click();
  await expect(storagePanel.getByText(/Waiting for facility confirmation/i)).toBeVisible();

  const evidencePanel = page.locator('details.trade-operations-panel').filter({ hasText: 'Trade evidence' });
  await evidencePanel.locator('summary').click();
  await evidencePanel.getByLabel(/upload evidence/i).setInputFiles({ name: 'quality.png', mimeType: 'image/png', buffer: Buffer.from([137, 80, 78, 71, 13, 10, 26, 10, ...Array(19).fill(1)]) });
  await evidencePanel.getByRole('button', { name: /Upload evidence/i }).last().click();
  await evidencePanel.locator('summary').click();
  await expect(evidencePanel.getByText(/quality\.png/)).toBeVisible();
  await expect(evidencePanel.getByText(/Participant-submitted/i)).toBeVisible();
  await qualityPanel.locator('summary').click();
  await expect(qualityPanel.getByText(/not a verified assay/i)).toBeVisible();
  expect(operationPaths).toEqual(['payment', 'quality', 'weighment', 'logistics', 'storage', 'evidence']);
  await expect(page.getByRole('link', { name: /report a problem/i })).toHaveAttribute('href', new RegExp(`/grievances\\?trade=${tradeId}`));

  for (const viewport of [{ width: 360, height: 640 }, { width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
    await page.setViewportSize(viewport);
    for (const language of ['en', 'hi', 'mr']) {
      await page.getByLabel(/language|भाषा/i).selectOption(language);
      await expect(page.locator('html')).toHaveAttribute('lang', language);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `Trade Room overflow at ${viewport.width}px in ${language}`).toBe(true);
      if (viewport.width === 360) {
        const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
        expect(results.violations, `Trade Room ${language}`).toEqual([]);
      }
    }
  }
});
