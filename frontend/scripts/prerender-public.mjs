import { createServer, loadEnv } from 'vite';
import React from 'react';
import { renderToPipeableStream } from 'react-dom/server';
import { PassThrough } from 'node:stream';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(scriptDir, '..');
const distDir = path.join(appDir, 'dist');
const manifestPath = path.join(distDir, 'prerender-manifest.json');
const viteEnv = loadEnv('production', appDir, '');
const siteOrigin = normalizeOrigin(process.env.PUBLIC_SITE_URL || viteEnv.PUBLIC_SITE_URL || process.env.VITE_PUBLIC_SITE_URL || viteEnv.VITE_PUBLIC_SITE_URL || '');
const apiOrigin = normalizeOrigin(process.env.PUBLIC_PRERENDER_API_BASE_URL || viteEnv.PUBLIC_PRERENDER_API_BASE_URL || process.env.VITE_API_BASE_URL || viteEnv.VITE_API_BASE_URL || 'http://127.0.0.1:8000');
const requestTimeoutMs = Number(process.env.PUBLIC_PRERENDER_TIMEOUT_MS || 1800);

function normalizeOrigin(value) {
  if (!value) return '';
  const parsed = new URL(value);
  if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('Public origins must use HTTP or HTTPS.');
  if (parsed.username || parsed.password || parsed.search || parsed.hash) throw new Error('Public origins cannot contain credentials, query strings or fragments.');
  return parsed.origin;
}

function text(value) {
  return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function attribute(value) {
  return text(value).replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

function safeJson(value) {
  return JSON.stringify(value)
    .replaceAll('<', '\\u003c')
    .replaceAll('>', '\\u003e')
    .replaceAll('&', '\\u0026')
    .replaceAll('\u2028', '\\u2028')
    .replaceAll('\u2029', '\\u2029');
}

function sanitizePrice(item) {
  const allowed = ['id', 'crop', 'commodity', 'market', 'district', 'state', 'modal_price', 'unit', 'price_date', 'arrival_date', 'source', 'freshness_state', 'location_verified'];
  return Object.fromEntries(allowed.filter((key) => item?.[key] !== undefined).map((key) => [key, item[key]]));
}

function safeHttpUrl(value) {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return ['https:', 'http:'].includes(parsed.protocol) && !parsed.username && !parsed.password ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function hasConfiguredSupport() {
  const phone = String(process.env.VITE_PUBLIC_SUPPORT_PHONE || viteEnv.VITE_PUBLIC_SUPPORT_PHONE || '').trim();
  const email = String(process.env.VITE_PUBLIC_SUPPORT_EMAIL || viteEnv.VITE_PUBLIC_SUPPORT_EMAIL || '').trim();
  return /^[+0-9() .-]{7,24}$/.test(phone) || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function sanitizeMarket(item) {
  const allowed = ['id', 'slug', 'name', 'district', 'state', 'latitude', 'longitude', 'market_type', 'outlet_type', 'verification_status', 'coordinate_source', 'coordinate_confidence', 'source_confidence', 'source_name', 'source_url', 'source_license_status', 'last_reviewed_at'];
  return Object.fromEntries(allowed.filter((key) => item?.[key] !== undefined).map((key) => [key, key === 'source_url' ? safeHttpUrl(item[key]) : item[key]]));
}

function sanitizeBuyer(item) {
  const allowed = ['business_name', 'type', 'crops', 'district', 'state', 'business_verification'];
  return Object.fromEntries(allowed.filter((key) => item?.[key] !== undefined).map((key) => [key, item[key]]));
}

async function fetchPublic(pathname) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs);
  try {
    const response = await fetch(new URL(pathname, `${apiOrigin}/`), {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    if (!response.ok) return { ok: false, reason: `HTTP ${response.status}` };
    const body = await response.json();
    if (!body || body.success !== true) return { ok: false, reason: 'API returned an unsuccessful response' };
    return { ok: true, data: body.data };
  } catch (error) {
    return { ok: false, reason: error.name === 'AbortError' ? 'request timed out' : 'public API unavailable' };
  } finally {
    clearTimeout(timer);
  }
}

async function fetchAllItems(endpoint, limit, maxItems = 10000) {
  const first = await fetchPublic(`/api/v1/${endpoint}?page=1&limit=${limit}`);
  if (!first.ok) return first;
  const declaredPages = Math.max(Number(first.data.pages) || 1, 1);
  const pages = Math.min(declaredPages, 200, Math.ceil(maxItems / limit));
  const items = [...(first.data.items || [])];
  const pageResults = await mapLimit(Array.from({ length: Math.max(pages - 1, 0) }, (_, index) => index + 2), 6,
    (page) => fetchPublic(`/api/v1/${endpoint}?page=${page}&limit=${limit}`));
  const failedPage = pageResults.find((result) => !result.ok);
  if (failedPage) return failedPage;
  for (const result of pageResults) items.push(...(result.data.items || []));
  const total = first.data.total ?? items.length;
  return { ok: true, truncated: declaredPages > pages || total > maxItems, data: { ...first.data, items: items.slice(0, maxItems), pages, total } };
}

async function mapLimit(items, concurrency, worker) {
  const results = Array.from({ length: items.length });
  let cursor = 0;
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (cursor < items.length) {
      const index = cursor++;
      results[index] = await worker(items[index]);
    }
  }));
  return results;
}

function addMeta(html, { title, description, canonical, robots, schema = [] }) {
  let output = html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${text(title)}</title>`);
  output = output.replace(/<html([^>]*)lang="[^"]*"/i, '<html$1lang="en"');
  output = output.replace(/\s*<meta\s+(?:name="description"|name="robots"|property="og:[^"]+"|name="twitter:[^"]+"|name="theme-color"|property="og:image:[^"]+")[^>]*>/gi, '');
  output = output.replace(/\s*<link\s+rel="canonical"[^>]*>/gi, '');
  output = output.replace(/\s*<script\s+id="krishilink-structured-data"[\s\S]*?<\/script>/gi, '');
  const meta = [
    `<meta name="description" content="${attribute(description)}" />`,
    `<meta name="robots" content="${robots}" />`,
    '<meta name="theme-color" content="#244b38" />',
    '<meta property="og:site_name" content="KrishiLink" />',
    `<meta property="og:title" content="${attribute(title)}" />`,
    `<meta property="og:description" content="${attribute(description)}" />`,
    '<meta property="og:type" content="website" />',
    `<meta property="og:image" content="${attribute(siteOrigin ? `${siteOrigin}/og-default.svg` : '/og-default.svg')}" />`,
    '<meta property="og:image:type" content="image/svg+xml" />',
    canonical ? `<meta property="og:url" content="${attribute(canonical)}" />` : '',
    '<meta name="twitter:card" content="summary_large_image" />',
    `<meta name="twitter:title" content="${attribute(title)}" />`,
    `<meta name="twitter:description" content="${attribute(description)}" />`,
    `<meta name="twitter:image" content="${attribute(siteOrigin ? `${siteOrigin}/og-default.svg` : '/og-default.svg')}" />`,
    canonical ? `<link rel="canonical" href="${attribute(canonical)}" />` : '',
    schema.length ? `<script id="krishilink-structured-data" type="application/ld+json">${safeJson(schema.length === 1 ? schema[0] : schema)}</script>` : '',
  ].filter(Boolean).join('\n    ');
  return output.replace('</head>', `    ${meta}\n  </head>`);
}

function localizedSiteSchemas(faqRows) {
  if (!siteOrigin) return [];
  return [
    {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'KrishiLink',
      url: siteOrigin,
      potentialAction: {
        '@type': 'SearchAction',
        target: `${siteOrigin}/prices?crop={search_term_string}`,
        'query-input': 'required name=search_term_string',
      },
    },
    {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqRows.map(([question, answer]) => ({
        '@type': 'Question',
        name: question,
        acceptedAnswer: { '@type': 'Answer', text: answer },
      })),
    },
  ];
}

function breadcrumbSchema(path, currentName) {
  if (!siteOrigin) return null;
  const base = [{ '@type': 'ListItem', position: 1, name: 'Home', item: `${siteOrigin}/` }];
  if (path.startsWith('/prices/')) base.push({ '@type': 'ListItem', position: 2, name: 'Reported prices', item: `${siteOrigin}/prices` });
  if (path.startsWith('/mandis/')) base.push({ '@type': 'ListItem', position: 2, name: 'Market directory', item: `${siteOrigin}/mandis` });
  base.push({ '@type': 'ListItem', position: base.length + 1, name: currentName });
  return { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: base };
}

function pageInfo(path, snapshot, { hasSupport, hasPriceData, hasOutletData, hasBuyerData } = {}) {
  const definitions = {
    '/': { title: 'KrishiLink | Reported market prices and produce trading', description: 'Check dated agricultural market price reports, browse reviewed market records, list produce and review buyer offers.', indexable: true },
    '/prices': { title: 'Reported agricultural market prices | KrishiLink', description: 'Compare official reported market price observations by crop, district and market, with report date, source and unit.', indexable: Boolean(hasPriceData) },
    '/mandis': { title: 'Agricultural market directory | KrishiLink', description: 'Browse public agricultural outlet records with their district and review status. Price observations are shown separately with their report date and source.', indexable: Boolean(hasOutletData) },
    '/map': { title: 'Reviewed agricultural markets on the map | KrishiLink', description: 'View public agricultural market records that meet the current outlet and location review checks. Buyer and member locations are not shown.', indexable: Boolean(hasOutletData) },
    '/buyers': { title: 'Buyer businesses | KrishiLink', description: 'Browse public business profiles whose business review is complete. Personal contact details are not published in this directory.', indexable: Boolean(hasBuyerData) },
    '/help': { title: 'Help for using KrishiLink | Reported prices, produce and offers', description: 'Task-based information about reported market prices, produce listings, offers and the available support path.', indexable: true },
    '/help/prices': { title: 'How to read reported market prices | KrishiLink', description: 'Learn how crop, market, report date, source and unit describe an official daily reported price.', indexable: true },
    '/help/sell': { title: 'How to list produce | KrishiLink', description: 'Review crop, quantity, location and asking price before publishing a produce lot.', indexable: true },
    '/help/offers': { title: 'How to review buyer offers | KrishiLink', description: 'Check an offer’s quantity, unit, price and terms before accepting or countering.', indexable: true },
    '/help/support': { title: 'How to reach support | KrishiLink', description: 'Sign in to raise or track a support request. Public contact details appear only when configured.', indexable: true },
    '/how-it-works': { title: 'How KrishiLink works | Reported prices and produce trading', description: 'A simple guide to checking reported prices, listing produce and reviewing offers.', indexable: true },
    '/about': { title: 'About KrishiLink | Agricultural market information', description: 'Learn what KrishiLink currently helps farmers, buyers and farmer groups do.', indexable: true },
    '/contact': { title: 'Contact and support | KrishiLink', description: 'See configured support channels and the available grievance workflow.', indexable: Boolean(hasSupport) },
    '/terms': { title: 'Terms of service draft | KrishiLink', description: 'Draft service terms pending legal review. Not approved for production use.', indexable: false },
    '/privacy': { title: 'Privacy notice draft | KrishiLink', description: 'Draft privacy notice pending legal review. Not approved for production use.', indexable: false },
    '/refunds-and-cancellations': { title: 'Refunds and cancellations draft | KrishiLink', description: 'Draft refund and cancellation policy pending legal review.', indexable: false },
    '/grievance-policy': { title: 'Grievance policy draft | KrishiLink', description: 'Draft grievance information pending legal review and operating contact details.', indexable: false },
    '/accuracy': { title: 'Evidence and published measurements | KrishiLink', description: 'No forecast accuracy or platform outcome statistics are published without a validated evidence set.', indexable: false },
    '/security': { title: 'Security and data handling | KrishiLink', description: 'A factual overview of account safeguards and current security limitations.', indexable: false },
    '/404': { title: 'Page not found | KrishiLink', description: 'This address does not match a public KrishiLink page.', indexable: false },
  };
  if (definitions[path]) return definitions[path];
  if (path.startsWith('/prices/')) {
    const crop = snapshot.crop;
    return {
      title: crop ? `${crop.name}: reported market prices | KrishiLink` : 'Reported crop prices | KrishiLink',
      description: crop ? `See dated official reported market price observations for ${crop.name}, with market, source and unit.` : 'Browse dated official reported agricultural market price observations with their source and unit.',
      indexable: Boolean(crop && hasPriceData),
    };
  }
  if (path.startsWith('/mandis/')) {
    const outlet = snapshot.market;
    return {
      title: outlet ? `${outlet.name}, ${outlet.district || outlet.state || ''} | KrishiLink` : 'Agricultural outlet details | KrishiLink',
      description: outlet ? `${outlet.name} in ${[outlet.district, outlet.state].filter(Boolean).join(', ')}. View its public outlet record and review information.` : 'Public agricultural outlet details from the reviewed registry.',
      indexable: Boolean(outlet),
    };
  }
  return { title: 'Page not found | KrishiLink', description: 'This address does not match a public KrishiLink page.', indexable: false };
}

function staticSitemap(paths) {
  if (!siteOrigin) return '';
  const urls = paths.map((pathname) => {
    const normalizedPath = pathname === '/' ? '/' : pathname.replace(/\/+$/, '');
    return `  <url><loc>${text(new URL(normalizedPath, `${siteOrigin}/`).toString())}</loc></url>`;
  }).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
}

function renderReactToString(element) {
  return new Promise((resolve, reject) => {
    const output = new PassThrough();
    const chunks = [];
    let renderError = null;
    output.on('data', (chunk) => chunks.push(chunk));
    output.on('error', reject);
    output.on('end', () => {
      if (renderError) reject(renderError);
      else resolve(Buffer.concat(chunks).toString('utf8'));
    });

    const stream = renderToPipeableStream(element, {
      onAllReady() {
        stream.pipe(output);
      },
      onShellError(error) {
        reject(error);
      },
      onError(error) {
        renderError ||= error;
      },
    });
    const timeout = setTimeout(() => stream.abort(), 10_000);
    output.once('end', () => clearTimeout(timeout));
  });
}

async function removePreviousGeneratedPages() {
  try {
    const previous = JSON.parse(await readFile(manifestPath, 'utf8'));
    for (const pathname of previous.generated_routes || []) {
      const file = path.resolve(distDir, `.${pathname === '/' ? '/index.html' : `${pathname}/index.html`}`);
      if (file.startsWith(`${distDir}${path.sep}`) || file === path.join(distDir, 'index.html')) await rm(file, { force: true });
    }
  } catch {
    // First build or a malformed old manifest; Vite's build already emptied dist.
  }
}

async function main() {
  const baseHtml = await readFile(path.join(distDir, 'index.html'), 'utf8');
  await removePreviousGeneratedPages();

  const cropsResult = await fetchAllItems('crops', 100);
  const crops = cropsResult.ok ? cropsResult.data.items || [] : [];
  const priceResults = await mapLimit(crops.slice(0, 100), 6, async (crop) => {
    const query = new URLSearchParams({ crop: crop.name, limit: '12' });
    return [crop.slug, await fetchPublic(`/api/v1/prices?${query}`)];
  });
  const priceByCrop = Object.fromEntries(priceResults.map(([slug, result]) => [slug, result.ok
    ? { ...result, data: { ...result.data, items: (result.data.items || []).map(sanitizePrice) } }
    : result]));
  const selectedCrop = crops[0] || null;
  const defaultPriceResult = selectedCrop ? priceByCrop[selectedCrop.slug] : null;
  const maxOutletPages = Math.min(50000, Math.max(1, Number(process.env.PUBLIC_PRERENDER_MAX_OUTLETS || viteEnv.PUBLIC_PRERENDER_MAX_OUTLETS || 10000)));
  const marketsResult = await fetchAllItems('markets', 500, maxOutletPages);
  const markets = marketsResult.ok ? (marketsResult.data.items || []).map(sanitizeMarket) : [];
  const buyersResult = await fetchPublic('/api/v1/users/buyers?limit=20');
  const buyers = buyersResult.ok ? (buyersResult.data || []).map(sanitizeBuyer) : [];

  const faqRows = [1, 2, 3, 4].map((number) => [
    `publicFaqQuestion${number}`,
    `publicFaqAnswer${number}`,
  ]);

  const vite = await createServer({
    configFile: path.join(appDir, 'vite.config.js'),
    root: appDir,
    appType: 'custom',
    logLevel: 'error',
    server: { middlewareMode: true },
  });
  try {
    const appModule = await vite.ssrLoadModule('/src/App.jsx');
    const copyModule = await vite.ssrLoadModule('/src/utils/copy.js');
    await appModule.preloadPrerenderRoutes();
    const faqData = faqRows.map(([questionKey, answerKey]) => [copyModule.copy.en[questionKey], copyModule.copy.en[answerKey]]);
    const staticPaths = [
      '/', '/prices', '/mandis', '/map', '/buyers', '/help', '/help/prices', '/help/sell', '/help/offers', '/help/support', '/how-it-works', '/about', '/contact',
      '/terms', '/privacy', '/refunds-and-cancellations', '/grievance-policy', '/accuracy', '/security', '/404',
    ];
    const dynamicSnapshots = [];
    for (const crop of crops) {
      if (!crop.slug) continue;
      dynamicSnapshots.push({ path: `/prices/${crop.slug}`, crop, prices: priceByCrop[crop.slug]?.ok ? {
        items: priceByCrop[crop.slug].data.items || [],
        total: priceByCrop[crop.slug].data.total || 0,
        pages: priceByCrop[crop.slug].data.pages || 1,
      } : { items: [], total: 0, pages: 1 }, priceStatus: priceByCrop[crop.slug]?.ok ? 'ok' : 'error' });
    }
    for (const market of markets) {
      if (market.slug) dynamicSnapshots.push({ path: `/mandis/${market.slug}`, market });
    }
    const routeSnapshots = [
      ...staticPaths.map((pathname) => ({ path: pathname })),
      ...dynamicSnapshots,
    ];
    const indexablePaths = [];
    const generatedRoutes = [];

    for (const route of routeSnapshots) {
      const pathname = route.path;
      const snapshot = {
        ...route,
        language: 'en',
        crops,
        selectedCrop: selectedCrop?.name || '',
        priceCrop: selectedCrop?.name || '',
        prices: route.prices || (defaultPriceResult?.ok ? {
          items: defaultPriceResult.data.items || [],
          total: defaultPriceResult.data.total || 0,
          pages: defaultPriceResult.data.pages || 1,
        } : { items: [], total: 0, pages: 1 }),
        cropStatus: cropsResult.ok ? 'ok' : 'error',
        priceStatus: route.priceStatus || (defaultPriceResult?.ok ? 'ok' : 'error'),
        markets: marketsResult.ok ? { ...marketsResult.data, items: markets } : { items: [], total: 0, pages: 1 },
        marketsStatus: marketsResult.ok ? 'ok' : 'error',
        buyers,
        buyersStatus: buyersResult.ok ? 'ok' : 'error',
      };
      globalThis.__KRISHILINK_PUBLIC_SNAPSHOT__ = snapshot;
      const markup = await renderReactToString(React.createElement(appModule.PrerenderApp, { path: pathname }));
      const info = pageInfo(pathname, snapshot, {
        hasSupport: hasConfiguredSupport(),
        hasPriceData: (snapshot.prices.items || []).length > 0 && snapshot.priceStatus === 'ok',
        hasOutletData: marketsResult.ok && markets.length > 0,
        hasBuyerData: buyersResult.ok && buyers.length > 0,
      });
      const canonical = siteOrigin ? new URL(pathname === '/' ? '/' : pathname.replace(/\/+$/, ''), `${siteOrigin}/`).toString() : '';
      const schema = [];
      if (pathname === '/') schema.push(...localizedSiteSchemas(faqData));
      if (pathname.startsWith('/prices/') && snapshot.crop) {
        const breadcrumb = breadcrumbSchema(pathname, snapshot.crop.name);
        if (breadcrumb) schema.push(breadcrumb);
      }
      if (pathname.startsWith('/mandis/') && snapshot.market) {
        const breadcrumb = breadcrumbSchema(pathname, snapshot.market.name);
        if (breadcrumb) schema.push(breadcrumb);
        if (siteOrigin) schema.push({
          '@context': 'https://schema.org',
          '@type': 'Place',
          name: snapshot.market.name,
          address: {
            '@type': 'PostalAddress',
            addressLocality: snapshot.market.district || undefined,
            addressRegion: snapshot.market.state || undefined,
            addressCountry: 'IN',
          },
          geo: snapshot.market.latitude != null && snapshot.market.longitude != null ? {
            '@type': 'GeoCoordinates', latitude: snapshot.market.latitude, longitude: snapshot.market.longitude,
          } : undefined,
          url: canonical || undefined,
        });
      }
      const html = addMeta(baseHtml, {
        title: info.title,
        description: info.description,
        canonical,
        robots: info.indexable ? 'index,follow' : 'noindex,follow',
        schema,
      });
      const withRoot = html.replace(
        '<div id="root"></div>',
        `<div id="root" data-prerendered="true">${markup}</div><script id="krishilink-public-snapshot" type="application/json">${safeJson(snapshot)}</script>`,
      );
      const relative = pathname === '/' ? 'index.html' : `${pathname.slice(1)}/index.html`;
      const outputPath = path.join(distDir, relative);
      await mkdir(path.dirname(outputPath), { recursive: true });
      await writeFile(outputPath, withRoot, 'utf8');
      generatedRoutes.push(pathname);
      if (info.indexable) indexablePaths.push(pathname);
    }

    const manifest = {
      strategy: 'vite-react-build-time-ssg',
      site_origin_configured: Boolean(siteOrigin),
      public_api_available: cropsResult.ok || marketsResult.ok || buyersResult.ok,
      dynamic_crop_routes: dynamicSnapshots.filter((item) => item.path.startsWith('/prices/')).length,
      dynamic_outlet_routes: dynamicSnapshots.filter((item) => item.path.startsWith('/mandis/')).length,
      outlet_routes_truncated: Boolean(marketsResult.ok && marketsResult.truncated),
      indexed_crop_routes: dynamicSnapshots.filter((item) => item.path.startsWith('/prices/') && item.priceStatus === 'ok' && item.prices.items.length > 0).length,
      generated_routes: generatedRoutes,
      sitemap_routes: indexablePaths,
      api_status: { crops: cropsResult.ok ? 'available' : 'unavailable', prices: selectedCrop && defaultPriceResult?.ok ? 'available' : 'unavailable', outlets: marketsResult.ok ? 'available' : 'unavailable', buyers: buyersResult.ok ? 'available' : 'unavailable' },
    };
    await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
    if (siteOrigin) await writeFile(path.join(distDir, 'sitemap.xml'), staticSitemap(indexablePaths), 'utf8');
    else await rm(path.join(distDir, 'sitemap.xml'), { force: true });
    const robots = [
      'User-agent: *',
      'Allow: /',
      'Disallow: /api/',
      'Disallow: /login',
      'Disallow: /register',
      'Disallow: /forgot-password',
      'Disallow: /reset-password',
      'Disallow: /verify-otp',
      'Disallow: /farmer/',
      'Disallow: /buyer/',
      'Disallow: /fpo/',
      'Disallow: /admin/',
      'Disallow: /offers',
      'Disallow: /trades/',
      'Disallow: /transactions',
      'Disallow: /grievances',
      ...(siteOrigin ? [`Sitemap: ${siteOrigin}/sitemap.xml`] : []),
      '',
    ].join('\n');
    await writeFile(path.join(distDir, 'robots.txt'), robots, 'utf8');
    console.log(`Pre-rendered ${generatedRoutes.length} public routes; sitemap has ${indexablePaths.length}. API: ${manifest.api_status.crops}/${manifest.api_status.outlets}/${manifest.api_status.buyers}; canonical origin: ${siteOrigin ? 'configured' : 'not configured'}.`);
    if (!siteOrigin) console.warn('PUBLIC_SITE_URL is unset: absolute canonical, sitemap, and URL-based structured data were omitted.');
    if (!manifest.public_api_available) console.warn('Public API is unavailable during build: dynamic crop/outlet pages were not generated; no sample data was substituted.');
  } finally {
    delete globalThis.__KRISHILINK_PUBLIC_SNAPSHOT__;
    await vite.close();
  }
}

main().catch((error) => {
  console.error(`Public pre-render failed: ${error.stack || error.message || error}`);
  process.exitCode = 1;
});
