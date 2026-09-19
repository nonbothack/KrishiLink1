const SIMPLE_MODE_PREFIX = 'farmer-simple-mode-';

export function getSimpleMode(ownerId) {
  if (!ownerId) return false;
  try {
    return localStorage.getItem(`${SIMPLE_MODE_PREFIX}${ownerId}`) === 'true';
  } catch {
    return false;
  }
}

export function setSimpleMode(ownerId, enabled) {
  if (!ownerId) return;
  try {
    localStorage.setItem(`${SIMPLE_MODE_PREFIX}${ownerId}`, enabled ? 'true' : 'false');
  } catch {
    // Keep the preference local to this view if browser storage is unavailable.
  }
  window.dispatchEvent(new CustomEvent('krishilink:experience-preference', { detail: { ownerId } }));
}
