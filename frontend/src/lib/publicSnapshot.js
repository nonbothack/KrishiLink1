const SNAPSHOT_ID = 'krishilink-public-snapshot';

export function getPublicSnapshot() {
  if (globalThis.__KRISHILINK_PUBLIC_SNAPSHOT__) return globalThis.__KRISHILINK_PUBLIC_SNAPSHOT__;
  if (typeof document === 'undefined') return null;
  const node = document.getElementById(SNAPSHOT_ID);
  if (!node?.textContent) return null;
  try {
    return JSON.parse(node.textContent);
  } catch {
    return null;
  }
}

export function setPublicSnapshot(snapshot) {
  globalThis.__KRISHILINK_PUBLIC_SNAPSHOT__ = snapshot;
}

export { SNAPSHOT_ID };
