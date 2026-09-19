const DATABASE_NAME = 'krishilink-offline-v1';
const DATABASE_VERSION = 1;
const QUEUE_STORE = 'lot-create-queue';
const SNAPSHOT_STORE = 'public-snapshots';
export const MAX_QUEUED_LOTS_PER_ACCOUNT = 5;
export const MAX_QUEUED_LOTS_TOTAL = 25;
export const MAX_QUEUED_LOT_BYTES = 16 * 1024;
export const LOT_QUEUE_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;
const MAX_PUBLIC_SNAPSHOTS = 40;
const MAX_PUBLIC_SNAPSHOT_BYTES = 2 * 1024 * 1024;

const LOT_FIELDS = new Set([
  'crop',
  'variety_id',
  'quantity',
  'unit',
  'asking_price',
  'grade',
  'location_text',
  'district',
]);
const QUEUE_STATES = new Set(['QUEUED', 'NEEDS_REVIEW']);

export class OfflineStoreError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

export function validateLotCreateQueueEntry({ ownerId, payload, idempotencyKey }) {
  if (typeof ownerId !== 'string' || !ownerId.trim() || ownerId.length > 128) {
    throw new OfflineStoreError('invalidOwner');
  }
  if (typeof idempotencyKey !== 'string' || !idempotencyKey.trim() || idempotencyKey.length > 128) {
    throw new OfflineStoreError('invalidIdempotencyKey');
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new OfflineStoreError('invalidPayload');
  }
  if (Object.keys(payload).some((key) => !LOT_FIELDS.has(key))) {
    throw new OfflineStoreError('unsupportedOperation');
  }
  if (
    typeof payload.crop !== 'string' ||
    !payload.crop.trim() ||
    typeof payload.quantity !== 'string' ||
    !/^\d+(?:\.\d{1,3})?$/.test(payload.quantity) ||
    Number(payload.quantity) <= 0 ||
    Number(payload.quantity) > 100_000_000 ||
    !['kg', 'quintal', 'tonne'].includes(payload.unit) ||
    typeof payload.location_text !== 'string' ||
    payload.location_text.trim().length < 2 ||
    payload.location_text.length > 300 ||
    (payload.asking_price != null &&
      (typeof payload.asking_price !== 'string' || !/^\d+(?:\.\d{1,2})?$/.test(payload.asking_price) || Number(payload.asking_price) <= 0 || Number(payload.asking_price) > 10_000_000))
  ) {
    throw new OfflineStoreError('invalidPayload');
  }
  const encoded = JSON.stringify(payload);
  if (new TextEncoder().encode(encoded).byteLength > MAX_QUEUED_LOT_BYTES) {
    throw new OfflineStoreError('payloadTooLarge');
  }
  return { ownerId: ownerId.trim(), payload: JSON.parse(encoded), idempotencyKey: idempotencyKey.trim() };
}

export function canProcessLotQueueEntry(entry, user) {
  try {
    return Boolean(
      entry &&
        user?.role === 'farmer' &&
        typeof user.id === 'string' &&
        entry.ownerId === user.id &&
      entry.operation === 'LOT_CREATE' &&
      entry.schemaVersion === 1 &&
      entry.state === 'QUEUED' &&
      Number.isFinite(Date.parse(entry.createdAt)) &&
      Date.now() - Date.parse(entry.createdAt) < LOT_QUEUE_MAX_AGE_MS &&
      (entry.attempts || 0) < 5 &&
        validateLotCreateQueueEntry({
          ownerId: entry.ownerId,
          payload: entry.payload,
          idempotencyKey: entry.idempotencyKey,
        }),
    );
  } catch {
    return false;
  }
}

export function lotQueueReviewReason(entry) {
  if (entry?.createdAt && Date.now() - Date.parse(entry.createdAt) >= LOT_QUEUE_MAX_AGE_MS) return 'offlineQueueExpired';
  if ((entry?.attempts || 0) >= 5) return 'offlineQueueRetryLimit';
  return 'unsupportedOperation';
}

export function storedSessionMatches(ownerId) {
  try {
    const session = JSON.parse(localStorage.getItem('krishilink_user') || 'null');
    return Boolean(session?.id === ownerId && session?.role === 'farmer');
  } catch {
    return false;
  }
}

export function isSafeOfflineCacheRequest(request) {
  if (!request || request.method !== 'GET') return false;
  const url = new URL(request.url);
  if (url.origin !== globalThis.location?.origin || url.username || url.password || url.search) return false;
  const shellPaths = new Set(['/app-shell.html', '/offline.html', '/manifest.webmanifest', '/favicon.svg', '/icons/krishilink.svg']);
  return shellPaths.has(url.pathname) || /^\/assets\/[A-Za-z0-9_-]+\.(?:js|css|svg|png|webp|woff2?)$/.test(url.pathname);
}

function openDatabase() {
  if (!globalThis.indexedDB) return Promise.reject(new OfflineStoreError('storageUnavailable'));
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        const queue = db.createObjectStore(QUEUE_STORE, { keyPath: 'key' });
        queue.createIndex('ownerId', 'ownerId', { unique: false });
      }
      if (!db.objectStoreNames.contains(SNAPSHOT_STORE)) {
        db.createObjectStore(SNAPSHOT_STORE, { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new OfflineStoreError('storageUnavailable'));
    request.onblocked = () => reject(new OfflineStoreError('storageUnavailable'));
  });
}

async function withStore(name, mode, callback) {
  const db = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(name, mode);
      const store = tx.objectStore(name);
      let result;
      try {
        result = callback(store, tx);
      } catch (error) {
        tx.abort();
        reject(error);
        return;
      }
      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(new OfflineStoreError('storageUnavailable'));
      tx.onabort = () => reject(new OfflineStoreError('storageUnavailable'));
    });
  } finally {
    db.close();
  }
}

export async function enqueueLotCreate(entry) {
  const safe = validateLotCreateQueueEntry(entry);
  const key = `${safe.ownerId}:${safe.idempotencyKey}`;
  const record = {
    key,
    ownerId: safe.ownerId,
    operation: 'LOT_CREATE',
    schemaVersion: 1,
    payload: safe.payload,
    idempotencyKey: safe.idempotencyKey,
    createdAt: new Date().toISOString(),
    state: 'QUEUED',
  };
  const db = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(QUEUE_STORE, 'readwrite');
      const store = tx.objectStore(QUEUE_STORE);
      let result = record;
      let failure = null;
      const existingRequest = store.get(key);
      existingRequest.onsuccess = () => {
        const existing = existingRequest.result;
        if (existing) {
          if (JSON.stringify(existing.payload) !== JSON.stringify(safe.payload)) {
            failure = new OfflineStoreError('idempotencyPayloadMismatch');
            tx.abort();
            return;
          }
          result = existing;
          return;
        }
        const ownerRequest = store.index('ownerId').getAll(safe.ownerId);
        ownerRequest.onsuccess = () => {
          if (ownerRequest.result.length >= MAX_QUEUED_LOTS_PER_ACCOUNT) {
            failure = new OfflineStoreError('queueLimitReached');
            tx.abort();
            return;
          }
          const allRequest = store.getAll();
          allRequest.onsuccess = () => {
            if (allRequest.result.length >= MAX_QUEUED_LOTS_TOTAL) {
              failure = new OfflineStoreError('queueLimitReached');
              tx.abort();
              return;
            }
            store.add(record);
          };
        };
      };
      tx.oncomplete = () => resolve(result);
      tx.onerror = tx.onabort = () => reject(failure || new OfflineStoreError('storageUnavailable'));
    });
  } finally {
    db.close();
  }
}

export async function listLotQueue(ownerId) {
  if (typeof ownerId !== 'string' || !ownerId.trim()) return [];
  return withStore(QUEUE_STORE, 'readonly', (store) => {
    const request = store.index('ownerId').getAll(ownerId);
    return new Promise((resolve) => {
      request.onsuccess = () => resolve(request.result.filter((row) => row.ownerId === ownerId && QUEUE_STATES.has(row.state)).sort((a, b) => a.createdAt.localeCompare(b.createdAt)));
      request.onerror = () => resolve([]);
    });
  }).then((result) => result);
}

export async function updateLotQueueState(ownerId, idempotencyKey, state, reasonCode = null) {
  if (!QUEUE_STATES.has(state)) throw new OfflineStoreError('invalidQueueState');
  const key = `${ownerId}:${idempotencyKey}`;
  return withStore(QUEUE_STORE, 'readwrite', (store) => {
    const request = store.get(key);
    request.onsuccess = () => {
      const record = request.result;
      if (record?.ownerId === ownerId) store.put({ ...record, state, reasonCode, updatedAt: new Date().toISOString() });
    };
  });
}

export async function recordLotQueueAttempt(ownerId, idempotencyKey) {
  const key = `${ownerId}:${idempotencyKey}`;
  return withStore(QUEUE_STORE, 'readwrite', (store) => {
    const request = store.get(key);
    request.onsuccess = () => {
      const record = request.result;
      if (record?.ownerId === ownerId && record.state === 'QUEUED') {
        store.put({ ...record, attempts: (record.attempts || 0) + 1, lastAttemptAt: new Date().toISOString() });
      }
    };
  });
}

export async function removeLotQueueEntry(ownerId, idempotencyKey) {
  if (!ownerId || !idempotencyKey) return;
  const key = `${ownerId}:${idempotencyKey}`;
  return withStore(QUEUE_STORE, 'readwrite', (store) => {
    const request = store.get(key);
    request.onsuccess = () => {
      if (request.result?.ownerId === ownerId) store.delete(key);
    };
  });
}

export async function cachePublicSnapshot(key, value) {
  if (typeof key !== 'string' || !/^(prices|crops):/.test(key)) return;
  const serialized = JSON.stringify(value);
  const size = new TextEncoder().encode(serialized).byteLength;
  if (size > 256 * 1024) return;
  return withStore(SNAPSHOT_STORE, 'readwrite', (store) => {
    const record = { key, value: JSON.parse(serialized), cachedAt: new Date().toISOString(), size };
    const request = store.getAll();
    request.onsuccess = () => {
      const older = request.result.filter((item) => item.key !== key).sort((a, b) => a.cachedAt.localeCompare(b.cachedAt));
      let total = size + older.reduce((sum, item) => sum + (item.size || 0), 0);
      while (older.length + 1 > MAX_PUBLIC_SNAPSHOTS || total > MAX_PUBLIC_SNAPSHOT_BYTES) {
        const removed = older.shift();
        if (!removed) break;
        total -= removed.size || 0;
        store.delete(removed.key);
      }
      store.put(record);
    };
  });
}

export async function readPublicSnapshot(key) {
  if (typeof key !== 'string' || !/^(prices|crops):/.test(key)) return null;
  return withStore(SNAPSHOT_STORE, 'readonly', (store) => {
    const request = store.get(key);
    return new Promise((resolve) => {
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => resolve(null);
    });
  }).then((result) => result);
}
