export const roles = ['farmer', 'buyer', 'fpo', 'admin', 'operator', 'support', 'reviewer', 'fraud_reviewer'];
export function dashboardFor(role) {
  return ['admin', 'operator', 'support', 'reviewer', 'fraud_reviewer'].includes(role)
    ? '/admin/operations'
    : roles.includes(role) ? `/${role}/dashboard` : '/';
}
export function safeNext(value, role) {
  if (!value || !value.startsWith('/') || value.startsWith('//') || /[\\\r\n]/.test(value))
    return dashboardFor(role);
  const path = value.split(/[?#]/)[0];
  const shared = ['/prices', '/map', '/offers', '/transactions', '/grievances', '/help'];
  return [
    ...shared,
    dashboardFor(role),
    ...(role !== 'buyer' ? ['/sell', '/matches'] : []),
    ...(role === 'farmer' ? ['/farmer/price-alerts'] : []),
  ].includes(path)
    ? value
    : dashboardFor(role);
}
export function normalizePhone(value) {
  let digits = String(value || '').replace(/[\s()+-]/g, '');
  if (digits.length === 12 && digits.startsWith('91')) digits = digits.slice(2);
  if (digits.length === 11 && digits.startsWith('0')) digits = digits.slice(1);
  return digits;
}
export function normalizeIdentifier(value) {
  return value.includes('@') ? value.trim().toLowerCase() : normalizePhone(value);
}
export function readSession() {
  try {
    const user = JSON.parse(localStorage.getItem('krishilink_user'));
    return user?.id && roles.includes(user.role) ? user : null;
  } catch {
    return null;
  }
}
export function clearSession() {
  for (const key of ['user', 'access_token', 'refresh_token'])
    localStorage.removeItem(`krishilink_${key}`);
}
