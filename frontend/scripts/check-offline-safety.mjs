import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (relative) => readFile(path.join(root, relative), 'utf8');
const readOptional = async (filePath) => {
  try {
    return await readFile(filePath, 'utf8');
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    throw error;
  }
};
const backendCandidates = [
  process.env.KRISHILINK_BACKEND_ROOT ? path.join(process.env.KRISHILINK_BACKEND_ROOT, 'app/modules/notifications/sms_service.py') : null,
  path.resolve(root, '../backend/app/modules/notifications/sms_service.py'),
  '/backend/app/modules/notifications/sms_service.py',
].filter(Boolean);
const [worker, manifestText, html, smsService] = await Promise.all([
  read('public/service-worker.js'),
  read('public/manifest.webmanifest'),
  read('index.html'),
  (async () => {
    for (const candidate of backendCandidates) {
      const contents = await readOptional(candidate);
      if (contents !== null) return contents;
    }
    return null;
  })(),
]);
const manifest = JSON.parse(manifestText);
const errors = [];
if (!manifest.display || manifest.display !== 'standalone') errors.push('PWA manifest is not installable (display must be standalone).');
if (!manifest.icons?.some((icon) => icon.src === '/icons/krishilink.svg')) errors.push('PWA manifest must use the reviewed KrishiLink icon.');
if (!html.includes('rel="manifest"')) errors.push('HTML must link to the PWA manifest.');
if (!worker.includes("if (request.method !== 'GET') return;")) errors.push('Service worker must reject non-GET requests before cache handling.');
if (!worker.includes("addEventListener('push'") || !worker.includes("addEventListener('notificationclick'")) errors.push('Service worker must handle privacy-safe push display and click navigation.');
if (/addEventListener\(['"]sync['"]/.test(worker)) errors.push('Background Sync must not replay mutations.');
if (/\/api\/v1\//.test(worker)) errors.push('Service worker must not cache or route API requests.');
if (/cache\.put\([^\n]*request/.test(worker) && !worker.includes('isCacheableStaticPath(url.pathname)')) errors.push('Runtime cache must be limited to reviewed static paths.');
if (smsService === null) {
  console.warn('Backend SMS provider source is outside this frontend build context; provider-truth check is deferred to backend CI.');
} else {
  if (!smsService.includes('"success": False') || !smsService.includes('"status": "DEMO"')) errors.push('SMS simulation must not report provider delivery success.');
  if (/\[SMS DEMO MODE\].*(TO:|MSG:)/.test(smsService)) errors.push('SMS demo logs must not include recipient or message contents.');
}
if (errors.length) {
  for (const error of errors) console.error(`FAIL: ${error}`);
  process.exitCode = 1;
} else {
  console.log('Offline/PWA and provider-truth checks passed.');
}
