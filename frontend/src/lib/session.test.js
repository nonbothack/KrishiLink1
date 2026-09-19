import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearSession,
  dashboardFor,
  normalizeIdentifier,
  normalizePhone,
  readSession,
  safeNext,
} from './session';

describe('session helpers', () => {
  beforeEach(() => localStorage.clear());

  it('normalizes common Indian phone formats', () => {
    expect(normalizePhone('+91 98765-43210')).toBe('9876543210');
    expect(normalizePhone('09876543210')).toBe('9876543210');
    expect(normalizeIdentifier(' FARMER@EXAMPLE.COM ')).toBe('farmer@example.com');
  });

  it('keeps post-login navigation inside known application routes', () => {
    expect(dashboardFor('farmer')).toBe('/farmer/dashboard');
    expect(safeNext('/sell?crop=Onion', 'farmer')).toBe('/sell?crop=Onion');
    expect(safeNext('/farmer/price-alerts', 'farmer')).toBe('/farmer/price-alerts');
    expect(safeNext('/farmer/price-alerts', 'buyer')).toBe('/buyer/dashboard');
    expect(safeNext('//malicious.example', 'farmer')).toBe('/farmer/dashboard');
    expect(safeNext('/admin', 'buyer')).toBe('/buyer/dashboard');
  });

  it('only restores a valid local user record', () => {
    localStorage.setItem('krishilink_user', JSON.stringify({ id: '1', role: 'farmer' }));
    expect(readSession()).toMatchObject({ id: '1', role: 'farmer' });
    localStorage.setItem('krishilink_access_token', 'legacy-token');
    clearSession();
    expect(readSession()).toBeNull();
    expect(localStorage.getItem('krishilink_access_token')).toBeNull();
  });
});
