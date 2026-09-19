import { spawn } from 'node:child_process';
import path from 'node:path';
import { chromium } from '@playwright/test';

const url = 'http://127.0.0.1:4174/';
const vite = spawn(process.execPath, [path.resolve('node_modules/vite/bin/vite.js'), 'preview', '--host', '127.0.0.1', '--port', '4174', '--strictPort'], {
  cwd: process.cwd(),
  stdio: 'ignore',
  windowsHide: true,
});
let browser;

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      if ((await fetch(url)).ok) return;
    } catch { /* The preview server is still starting. */ }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error('Production preview did not start within 20 seconds.');
}

try {
  await waitForServer();
  browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ serviceWorkers: 'allow' });
  const page = await context.newPage();
  page.on('pageerror', (error) => console.error(`PWA page error: ${error.message}`));
  page.on('requestfailed', (request) => console.error(`PWA request failed: ${request.url()} ${request.failure()?.errorText}`));
  await page.goto(url);
  await page.waitForFunction(() => Boolean(navigator.serviceWorker?.controller), undefined, { timeout: 15000 });
  const evidence = await page.evaluate(async () => {
    const response = await fetch('/manifest.webmanifest');
    const manifest = await response.json();
    const cacheNames = await caches.keys();
    const requests = (await Promise.all(cacheNames.map(async (name) => (await caches.open(name)).keys()))).flat();
    return {
      manifest: { display: manifest.display, icon: manifest.icons?.[0]?.src },
      shell: requests.some((request) => new URL(request.url).pathname === '/app-shell.html'),
      entryAssets: requests.filter((request) => new URL(request.url).pathname.startsWith('/assets/')).length,
      cachedPaths: requests.map((request) => new URL(request.url).pathname),
      apiCached: requests.some((request) => new URL(request.url).pathname.startsWith('/api/')),
    };
  });
  if (evidence.manifest.display !== 'standalone' || evidence.manifest.icon !== '/icons/krishilink.svg') throw new Error('Install manifest is missing expected display or icon metadata.');
  if (!evidence.shell || evidence.entryAssets < 1 || evidence.apiCached) throw new Error(`Unsafe/incomplete shell cache: ${JSON.stringify(evidence)}`);
  console.log(`Installed shell cache: ${JSON.stringify(evidence)}`);

  await context.setOffline(true);
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  const offlineBody = await page.locator('body').innerText();
  if (!await page.getByRole('heading', { level: 1 }).count()) throw new Error(`Offline shell did not render application content: ${offlineBody.slice(0, 300)}`);
  console.log(`Production PWA browser check passed: ${JSON.stringify(evidence)}; offline shell rendered.`);
  await context.close();
} finally {
  await browser?.close();
  vite.kill();
  vite.unref();
}
