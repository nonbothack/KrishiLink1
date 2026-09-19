import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const siteOrigin = 'https://krishilink.example.test';
const marketId = '11111111-1111-4111-8111-111111111111';
const marketSlug = 'lasalgaon-apmc-nashik-maharashtra-111111111111';
const crop = { id: 'crop-onion', name: 'Onion', name_en: 'Onion', name_hindi: 'प्याज', name_marathi: 'कांदा', slug: 'onion', default_unit: 'quintal', valid_units: ['quintal', 'kg'], aliases: [] };
const market = {
  id: marketId, slug: marketSlug, name: 'Lasalgaon APMC', district: 'Nashik', state: 'Maharashtra',
  latitude: 20.14, longitude: 74.23, market_type: 'apmc_principal', outlet_type: 'apmc_principal',
  verification_status: 'verified', coordinate_source: 'reviewed_official_source', coordinate_confidence: 0.96,
  source_confidence: 0.97, source_name: 'AGMARKNET', source_url: 'javascript:alert(1)',
  last_reviewed_at: '2026-09-10T10:00:00Z', source_ref: 'private-source-reference', private_contact: 'private@example.test',
};
const price = {
  id: 'reported-onion-price', crop: 'Onion', market: 'Lasalgaon APMC', district: 'Nashik', state: 'Maharashtra',
  modal_price: '2450.00', unit: 'INR/quintal', price_date: '2026-09-17', source: 'AGMARKNET', freshness_state: 'fresh',
  location_verified: true, user_id: 'must-not-leak', provider_key: 'must-not-leak',
};
const buyer = {
  business_name: 'Nashik Produce Cooperative', type: 'cooperative', crops: ['Onion'], district: 'Nashik', state: 'Maharashtra', business_verification: 'verified',
  id: 'private-user-id', user_id: 'private-user-id', full_name: 'Private Person', phone: '+919876543210', email: 'private@example.test',
  location: 'Private Street', latitude: 19.2, longitude: 73.1, rating: 5,
};

function response(data) {
  return { success: true, data };
}

const server = createServer((request, res) => {
  const url = new URL(request.url, 'http://localhost');
  let body;
  if (url.pathname === '/api/v1/crops') body = response({ items: [crop], total: 1, pages: 1 });
  else if (url.pathname === '/api/v1/prices') body = response({ items: [price], total: 1, pages: 1 });
  else if (url.pathname === '/api/v1/markets') body = response({ items: [market], total: 1, pages: 1 });
  else if (url.pathname === '/api/v1/users/buyers') body = response([buyer]);
  else {
    res.writeHead(404, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ success: false, message: 'Not found' }));
    return;
  }
  res.writeHead(200, { 'content-type': 'application/json' });
  res.end(JSON.stringify(body));
});

function run(command, args, env) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: frontendDir, env, stdio: 'inherit', windowsHide: true });
    child.once('error', reject);
    child.once('exit', (code) => code === 0 ? resolve() : reject(new Error(`${command} ${args.join(' ')} exited ${code}`)));
  });
}

try {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  const env = {
    ...process.env,
    PUBLIC_SITE_URL: siteOrigin,
    VITE_PUBLIC_SITE_URL: siteOrigin,
    PUBLIC_PRERENDER_API_BASE_URL: `http://127.0.0.1:${address.port}`,
  };
  await run(process.execPath, [path.join(frontendDir, 'node_modules/vite/bin/vite.js'), 'build'], env);
  await run(process.execPath, [path.join(frontendDir, 'scripts/prerender-public.mjs')], env);
  await run(process.execPath, [path.join(frontendDir, 'scripts/check-seo-rendering.mjs')], env);
  const distDir = path.join(frontendDir, 'dist');
  const cropHtml = await readFile(path.join(distDir, 'prices/onion/index.html'), 'utf8');
  const marketHtml = await readFile(path.join(distDir, 'mandis', marketSlug, 'index.html'), 'utf8');
  const buyersHtml = await readFile(path.join(distDir, 'buyers/index.html'), 'utf8');
  assert.match(cropHtml, /₹2,450|2,450/);
  assert.match(cropHtml, /AGMARKNET/);
  const visibleDate = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(price.price_date));
  assert(cropHtml.includes(visibleDate), 'The crop page must render the actual report date in its visible price record.');
  assert.match(marketHtml, /Lasalgaon APMC/);
  assert.doesNotMatch(marketHtml, /javascript:alert|private-source-reference|private_contact/);
  assert.match(buyersHtml, /Nashik Produce Cooperative/);
  for (const value of ['private-user-id', 'Private Person', '+919876543210', 'private@example.test', 'Private Street']) {
    assert(!buyersHtml.includes(value), `Buyer directory HTML leaked ${value}`);
  }
  const sitemap = await readFile(path.join(distDir, 'sitemap.xml'), 'utf8');
  assert(sitemap.includes(`${siteOrigin}/prices/onion`));
  assert(sitemap.includes(`${siteOrigin}/mandis/${marketSlug}`));
  console.log('Fixture-backed public rendering passed with real-shaped crop, reported-price, reviewed-outlet and verified-business API records.');
} finally {
  await new Promise((resolve) => server.close(resolve));
}
