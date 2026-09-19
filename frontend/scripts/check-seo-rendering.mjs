import assert from 'node:assert/strict';
import { readFile, access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const distDir = path.join(appDir, 'dist');
const manifest = JSON.parse(await readFile(path.join(distDir, 'prerender-manifest.json'), 'utf8'));
const staticPaths = [
  '/', '/prices', '/mandis', '/map', '/buyers', '/help', '/help/prices', '/help/sell', '/help/offers', '/help/support', '/how-it-works', '/about', '/contact',
  '/terms', '/privacy', '/refunds-and-cancellations', '/grievance-policy', '/accuracy', '/security', '/404',
];
const generated = new Set(manifest.generated_routes);
const titles = new Set();

function fileFor(route) {
  return path.join(distDir, route === '/' ? 'index.html' : `${route.slice(1)}/index.html`);
}

function decoded(html) {
  return html.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
}

for (const route of staticPaths) {
  assert(generated.has(route), `Missing pre-rendered public route ${route}`);
  const html = await readFile(fileFor(route), 'utf8');
  const title = html.match(/<title>(.*?)<\/title>/is)?.[1];
  const description = html.match(/<meta name="description" content="([^"]+)"\s*\/?\s*>/i)?.[1];
  assert(title && title !== 'KrishiLink', `${route} has no route-specific HTML title`);
  assert(description && description.length >= 40, `${route} has no useful HTML description`);
  assert(!titles.has(title), `Duplicate page title: ${title}`);
  titles.add(title);
  const canonical = html.match(/<link rel="canonical" href="([^"]+)"\s*\/?\s*>/i)?.[1];
  if (manifest.site_origin_configured) {
    const expected = new URL(route === '/' ? '/' : route.replace(/\/+$/, ''), `${process.env.PUBLIC_SITE_URL || process.env.VITE_PUBLIC_SITE_URL}/`).toString();
    assert(canonical === expected, `${route} canonical URL does not match the deployment slash policy`);
  } else {
    assert(!canonical, `${route} must omit absolute canonical metadata without a verified public origin`);
  }
  assert(html.includes('data-prerendered="true"'), `${route} is only a client-rendered shell`);
  assert(!/Switched to client rendering|data-msg="Switched to client rendering/i.test(html), `${route} contains an aborted React server-render boundary`);
  assert(/<h1\b/i.test(html), `${route} has no pre-rendered primary heading`);
  const bodyText = decoded(html.slice(html.indexOf('<div id="root"'), html.indexOf('<script id="krishilink-public-snapshot"')));
  assert(bodyText.length > 250, `${route} has no meaningful initial HTML content`);
  if (['/terms', '/privacy', '/refunds-and-cancellations', '/grievance-policy'].includes(route)) {
    assert(/DRAFT|draft|मसुदा|मसौदा/i.test(bodyText), `${route} lost its visible draft warning`);
    assert(/noindex,follow/.test(html), `${route} must remain out of the index until legal review`);
  }
  assert(!/3,?000\+?\s*(markets|mandis)|best price|live (mandi )?prices|1800-[X0-9]+/i.test(bodyText), `${route} includes an unsupported public claim`);
  assert(!/<link[^>]+hreflang=/i.test(html), `${route} must not claim language-specific URLs before they exist`);
}

for (const route of manifest.generated_routes.filter((item) => item.startsWith('/prices/') || item.startsWith('/mandis/'))) {
  const html = await readFile(fileFor(route), 'utf8');
  assert(html.includes('data-prerendered="true"'), `${route} has no route-specific rendered HTML`);
  assert(/<h1\b/i.test(html), `${route} has no rendered heading`);
  const snapshotText = html.match(/<script id="krishilink-public-snapshot" type="application\/json">([\s\S]*?)<\/script>/)?.[1];
  assert(snapshotText, `${route} is missing its public data snapshot`);
  const snapshot = JSON.parse(snapshotText);
  const content = decoded(html.slice(html.indexOf('<div id="root"'), html.indexOf('<script id="krishilink-public-snapshot"')));
  if (route.startsWith('/prices/')) {
    assert(snapshot.crop?.slug && route === `/prices/${snapshot.crop.slug}`, `${route} is not based on a canonical crop registry entry`);
    assert(content.toLocaleLowerCase().includes(snapshot.crop.name.toLocaleLowerCase()), `${route} does not render its crop name in HTML`);
    if (snapshot.prices.items.length) {
      assert(content.includes(snapshot.prices.items[0].source), `${route} omits its actual reported-price source`);
      const reportDate = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(snapshot.prices.items[0].price_date));
      assert(content.includes(reportDate), `${route} omits its actual reported-price date`);
    }
    assert(!/"@type"\s*:\s*"(?:Product|Offer)"/.test(html), `${route} must not turn a reference price into a product offer`);
  } else {
    assert(snapshot.market?.slug && route === `/mandis/${snapshot.market.slug}`, `${route} is not based on the reviewed outlet registry`);
    assert(content.toLocaleLowerCase().includes(snapshot.market.name.toLocaleLowerCase()), `${route} does not render its outlet name in HTML`);
  }
}

for (const route of generated) {
  if (!route.startsWith('/buyers')) continue;
  const html = await readFile(fileFor(route), 'utf8');
  const serialized = html.match(/<script id="krishilink-public-snapshot" type="application\/json">([\s\S]*?)<\/script>/)?.[1];
  assert(serialized, `${route} is missing its public snapshot`);
  const snapshot = JSON.parse(serialized);
  for (const buyer of snapshot.buyers || []) {
    for (const privateField of ['id', 'user_id', 'full_name', 'name', 'phone', 'email', 'location', 'latitude', 'longitude', 'rating']) {
      assert(!(privateField in buyer), `${route} snapshot leaks buyer field ${privateField}`);
    }
  }
}

const robots = await readFile(path.join(distDir, 'robots.txt'), 'utf8');
for (const pathPrefix of ['/login', '/register', '/farmer/', '/buyer/', '/fpo/', '/admin/', '/trades/', '/grievances']) {
  assert(robots.includes(`Disallow: ${pathPrefix}`), `robots.txt does not disallow ${pathPrefix}`);
}

const sitemapPath = path.join(distDir, 'sitemap.xml');
try {
  await access(path.join(distDir, 'data/live_mandi_prices.json'));
  assert.fail('An unprovenanced legacy live-price dataset must not be published as a static asset.');
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
try {
  await access(sitemapPath);
  const sitemap = await readFile(sitemapPath, 'utf8');
  assert(manifest.site_origin_configured, 'A sitemap must not be emitted without a configured canonical origin');
  assert(sitemap.startsWith('<?xml'), 'sitemap.xml is malformed');
  assert(!/\/(?:login|register|farmer|buyer|fpo|admin|trades|grievances|terms|privacy)(?:\/|<)/i.test(sitemap), 'Sitemap contains protected or draft legal pages');
  for (const route of manifest.sitemap_routes) {
    assert(generated.has(route), `Sitemap path ${route} has no pre-rendered HTML`);
    assert(sitemap.includes(new URL(route === '/' ? '/' : route.replace(/\/+$/, ''), `${process.env.PUBLIC_SITE_URL || process.env.VITE_PUBLIC_SITE_URL}/`).toString()), `Sitemap is missing ${route}`);
  }
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
  assert(!manifest.site_origin_configured, 'Configured canonical origin requires a sitemap');
}

console.log(`SEO rendering check passed: ${manifest.generated_routes.length} rendered routes, ${manifest.sitemap_routes.length} sitemap routes, ${manifest.dynamic_crop_routes} crop pages and ${manifest.dynamic_outlet_routes} outlet pages.`);
