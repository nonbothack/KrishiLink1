import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

async function loadWorker() {
  const source = await readFile('public/service-worker.js', 'utf8');
  const handlers = {};
  const shown = [];
  const opened = [];
  const workerSelf = {
    location: { origin: 'https://krishilink.example' },
    addEventListener: (name, handler) => { handlers[name] = handler; },
    registration: { showNotification: async (title, options) => shown.push({ title, options }) },
    clients: {
      matchAll: async () => [],
      openWindow: async (url) => { opened.push(url); },
      claim: async () => undefined,
    },
    skipWaiting: async () => undefined,
  };
  const context = {
    self: workerSelf,
    URL,
    Request,
    caches: { open: async () => ({ addAll: async () => undefined }), keys: async () => [], match: async () => null },
    fetch: async () => new Response(''),
    Promise,
    RegExp,
  };
  vm.runInNewContext(source, context);
  return { handlers, shown, opened, self: workerSelf };
}

describe('service worker push safety', () => {
  it('shows only the safe summary and clicks through to same-origin authorized app route', async () => {
    const worker = await loadWorker();
    let pushDone;
    worker.handlers.push({
      data: { json: () => ({ schema_version: 1, notification_id: '5c1dbadb-847d-47f2-9a4d-065c03bf02e8', category: 'offer', title: 'Offer update', body: 'Open the app.', path: '/offers' }) },
      waitUntil: (promise) => { pushDone = promise; },
    });
    await pushDone;
    expect(worker.shown[0].title).toBe('Offer update');
    expect(worker.shown[0].options.data.path).toBe('/offers');
    expect(worker.shown[0].options.actions).toBeUndefined();

    let clickDone;
    worker.handlers.notificationclick({
      notification: { data: { path: '/offers' }, close: () => undefined },
      waitUntil: (promise) => { clickDone = promise; },
    });
    await clickDone;
    expect(worker.opened[0]).toBe('https://krishilink.example/offers');
  });

  it('falls back safely for malformed payloads and external click destinations', async () => {
    const worker = await loadWorker();
    let pushDone;
    worker.handlers.push({ data: { json: () => { throw new Error('bad json'); } }, waitUntil: (promise) => { pushDone = promise; } });
    await pushDone;
    expect(worker.shown[0].title).toBe('KrishiLink update');
    expect(worker.shown[0].options.data.path).toBe('/');

    let clickDone;
    worker.handlers.notificationclick({
      notification: { data: { path: 'https://evil.example/steal' }, close: () => undefined },
      waitUntil: (promise) => { clickDone = promise; },
    });
    await clickDone;
    expect(worker.opened.at(-1)).toBe('https://krishilink.example/');
  });
});
