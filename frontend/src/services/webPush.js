import { apiCall } from '../lib/http';

export function decodeApplicationServerKey(encoded) {
  const padding = '='.repeat((4 - (encoded.length % 4)) % 4);
  const base64 = (encoded + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from(raw, (character) => character.charCodeAt(0));
}

export function isPushSupported() {
  return typeof window !== 'undefined'
    && 'Notification' in window
    && 'serviceWorker' in navigator
    && 'PushManager' in window;
}

async function currentSubscription() {
  if (!('serviceWorker' in navigator)) return null;
  const registration = await navigator.serviceWorker.getRegistration('/');
  return registration?.pushManager?.getSubscription?.() || null;
}

export async function reconcileGrantedSubscription() {
  if (!isPushSupported() || Notification.permission !== 'granted') return { status: 'NOT_REQUESTED' };
  const subscription = await currentSubscription();
  if (!subscription) return { status: 'NOT_REGISTERED' };
  const result = await apiCall('/api/v1/notifications/push/reconcile', {
    method: 'POST',
    body: JSON.stringify({ endpoint: subscription.endpoint }),
  });
  return result.success ? result.data : { status: 'UNAVAILABLE' };
}

export async function enableWebPush(language) {
  if (!isPushSupported()) return { status: 'UNSUPPORTED' };
  const capability = await apiCall('/api/v1/notifications/push/capability');
  if (!capability.success || capability.data?.status !== 'AVAILABLE' || !capability.data?.application_server_key) {
    return { status: 'UNAVAILABLE' };
  }
  let permission = Notification.permission;
  if (permission === 'default') permission = await Notification.requestPermission();
  if (permission !== 'granted') return { status: permission === 'denied' ? 'DENIED' : 'NOT_GRANTED' };
  const registration = await navigator.serviceWorker.register('/service-worker.js');
  await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (subscription) {
    const association = await apiCall('/api/v1/notifications/push/reconcile', {
      method: 'POST',
      body: JSON.stringify({ endpoint: subscription.endpoint }),
    });
    if (association.success && association.data?.status === 'NOT_REGISTERED') {
      await subscription.unsubscribe().catch(() => false);
      subscription = null;
    }
  }
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: decodeApplicationServerKey(capability.data.application_server_key),
    });
  }
  const result = await apiCall('/api/v1/notifications/push/subscriptions', {
    method: 'POST',
    body: JSON.stringify({ endpoint: subscription.endpoint, keys: subscription.toJSON().keys, language }),
  });
  if (!result.success) {
    if (subscription) await subscription.unsubscribe().catch(() => undefined);
    return { status: result.status === 409 ? 'CONFLICT' : 'UNAVAILABLE' };
  }
  return { status: 'ACTIVE' };
}

export async function disableWebPush() {
  const subscription = await currentSubscription();
  if (!subscription) return { status: 'DISABLED' };
  const serverResult = await apiCall('/api/v1/notifications/push/subscriptions/current', {
    method: 'DELETE',
    body: JSON.stringify({ endpoint: subscription.endpoint }),
    timeout: 1200,
  });
  const localResult = await subscription.unsubscribe().catch(() => false);
  return { status: localResult ? 'DISABLED' : 'UNSUBSCRIBE_INCOMPLETE', serverRevoked: serverResult.success };
}

export async function cleanupPushOnLogout() {
  try {
    const subscription = await currentSubscription();
    if (!subscription) return;
    const revoke = apiCall('/api/v1/notifications/push/subscriptions/current', {
      method: 'DELETE',
      body: JSON.stringify({ endpoint: subscription.endpoint }),
      timeout: 700,
    });
    // Remove the local device association even when network revocation is offline.
    await subscription.unsubscribe().catch(() => false);
    await Promise.race([revoke, new Promise((resolve) => setTimeout(resolve, 750))]);
  } catch {
    // Logout must remain usable when PushManager or the network is unavailable.
  }
}
