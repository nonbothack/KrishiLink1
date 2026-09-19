import { clearSession } from './session';
const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
let accessToken = null;
let refreshPending;
export const setAccessToken = (token) => {
  accessToken = token;
};
function csrfHeader(endpoint) {
  if (
    typeof document === 'undefined' ||
    !endpoint.startsWith('/api/v1/auth/') ||
    !['/api/v1/auth/refresh', '/api/v1/auth/logout'].includes(endpoint)
  )
    return {};
  const match = document.cookie.match(/(?:^|;\s*)krishilink_csrf=([^;]+)/);
  return match ? { 'X-KrishiLink-CSRF': decodeURIComponent(match[1]) } : {};
}
export class ApiError extends Error {
  constructor(message, status, code, requestId) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}
async function request(endpoint, options = {}) {
  const { timeout = 20000, auth = true, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const formBody = typeof FormData !== 'undefined' && init.body instanceof FormData;
  try {
    const response = await fetch(base + endpoint, {
      ...init,
      credentials: 'include',
      signal: controller.signal,
      headers: {
        ...(formBody ? {} : { 'Content-Type': 'application/json' }),
        'X-KrishiLink-Client': 'web',
        ...csrfHeader(endpoint),
        ...(auth && accessToken ? { Authorization: 'Bearer ' + accessToken } : {}),
        ...init.headers,
      },
    });
    const json = await response.json().catch(() => null);
    if (!response.ok || !json || json.success === false) {
      const status = response.status;
      const code =
        status === 401
          ? 'auth'
          : status === 409
            ? 'conflict'
            : status === 422
              ? 'validation'
              : status === 429
                ? 'rateLimited'
                : status === 403
                  ? 'forbidden'
                  : 'server';
      throw new ApiError(code, status, code, json?.request_id);
    }
    return json;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      'Connection unavailable',
      0,
      error.name === 'AbortError' ? 'timeout' : 'network',
    );
  } finally {
    clearTimeout(timer);
  }
}
export function restoreSession() {
  if (!refreshPending)
    refreshPending = request('/api/v1/auth/refresh', { method: 'POST', auth: false })
      .then((res) => {
        accessToken = res.data.access_token;
        return res;
      })
      .finally(() => {
        refreshPending = null;
      });
  return refreshPending;
}
export async function apiCall(endpoint, options = {}) {
  try {
    try {
      return await request(endpoint, options);
    } catch (error) {
      if (error.status !== 401 || options.auth === false || endpoint.startsWith('/api/v1/auth/'))
        throw error;
      await restoreSession();
      return await request(endpoint, options);
    }
  } catch (error) {
    if (error.status === 401 && options.auth !== false) {
      accessToken = null;
      clearSession();
      window.dispatchEvent(new Event('session-expired'));
    }
    return {
      success: false,
      data: null,
      error: error.code || 'server',
      status: error.status || 0,
      request_id: error.requestId,
    };
  }
}
