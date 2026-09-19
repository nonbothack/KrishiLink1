import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const dist = path.resolve('dist');
const manifestPath = path.join(dist, '.vite', 'manifest.json');
const manifestText = await readFile(manifestPath, 'utf8');
const manifest = JSON.parse(manifestText);
const entry = Object.values(manifest).find((item) => item.isEntry && item.src === 'index.html');
if (!entry) throw new Error('Vite entry for index.html was not found; cannot build an offline shell.');

const assets = new Set();
const visit = (item) => {
  if (!item) return;
  if (item.file) assets.add(`/${item.file}`);
  for (const css of item.css || []) assets.add(`/${css}`);
  for (const imported of item.imports || []) visit(manifest[imported]);
};
visit(entry);

const shellSource = await readFile(path.join(dist, 'index.html'), 'utf8');
await writeFile(path.join(dist, 'app-shell.html'), shellSource, 'utf8');
const cacheVersion = createHash('sha256').update(manifestText).digest('hex').slice(0, 12);
const workerPath = path.join(dist, 'service-worker.js');
let worker = await readFile(workerPath, 'utf8');
worker = worker
  .replace("const CACHE_NAME = 'krishilink-shell-v1';", `const CACHE_NAME = 'krishilink-shell-${cacheVersion}';`)
  .replace('];\n\nfunction isCacheableStaticPath', `  ...${JSON.stringify([...assets].sort())},\n];\n\nfunction isCacheableStaticPath`)
  .replace("(await caches.match('/index.html')) || caches.match('/offline.html')", "(await caches.match('/app-shell.html')) || caches.match('/offline.html')");
await writeFile(workerPath, worker, 'utf8');

// Vite copies this source worker unchanged. The generated worker is versioned
// from the exact Vite manifest and precaches only the entry graph, not lazy routes.
if (assets.size === 0) throw new Error('Vite entry graph had no assets to precache.');
console.log(`Prepared installable shell with ${assets.size} entry assets (cache ${cacheVersion}).`);
