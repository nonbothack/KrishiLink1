import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import {
  canProcessLotQueueEntry,
  isSafeOfflineCacheRequest,
  storedSessionMatches,
  validateLotCreateQueueEntry,
} from './offlineStore';
import { getSimpleMode, setSimpleMode } from './experiencePreferences';

const validPayload = {
  crop: 'crop-canonical-id',
  variety_id: null,
  quantity: '12.500',
  unit: 'quintal',
  asking_price: '2400.00',
  grade: 'UNSPECIFIED',
  location_text: 'Nashik district',
  district: 'Nashik',
};

describe('offline lot queue boundaries', () => {
  it('accepts only a current farmer and the exact owner of a queued lot-create operation', () => {
    const entry = { ownerId: 'farmer-a', operation: 'LOT_CREATE', schemaVersion: 1, state: 'QUEUED', createdAt: new Date().toISOString(), idempotencyKey: 'retry-key', payload: validPayload };
    expect(canProcessLotQueueEntry(entry, { id: 'farmer-a', role: 'farmer' })).toBe(true);
    expect(canProcessLotQueueEntry(entry, { id: 'farmer-b', role: 'farmer' })).toBe(false);
    expect(canProcessLotQueueEntry(entry, { id: 'farmer-a', role: 'fpo' })).toBe(false);
    expect(canProcessLotQueueEntry({ ...entry, state: 'NEEDS_REVIEW' }, { id: 'farmer-a', role: 'farmer' })).toBe(false);
    expect(canProcessLotQueueEntry({ ...entry, operation: 'OFFER_ACCEPT' }, { id: 'farmer-a', role: 'farmer' })).toBe(false);
  });

  it('rejects generic, financial, unitless and malformed queued requests', () => {
    expect(() => validateLotCreateQueueEntry({ ownerId: 'farmer-a', payload: { ...validPayload, method: 'POST' }, idempotencyKey: 'k' })).toThrow('unsupportedOperation');
    expect(() => validateLotCreateQueueEntry({ ownerId: 'farmer-a', payload: { ...validPayload, unit: 'bag' }, idempotencyKey: 'k' })).toThrow('invalidPayload');
    expect(() => validateLotCreateQueueEntry({ ownerId: 'farmer-a', payload: { ...validPayload, quantity: '0' }, idempotencyKey: 'k' })).toThrow('invalidPayload');
    expect(() => validateLotCreateQueueEntry({ ownerId: 'farmer-a', payload: validPayload, idempotencyKey: '' })).toThrow('invalidIdempotencyKey');
  });

  it('limits service-worker caching to same-origin static GET files without credentials or query strings', () => {
    const request = (url, method = 'GET') => ({ url, method });
    expect(isSafeOfflineCacheRequest(request(`${location.origin}/assets/app-A1.js`))).toBe(true);
    expect(isSafeOfflineCacheRequest(request(`${location.origin}/api/v1/offers`))).toBe(false);
    expect(isSafeOfflineCacheRequest(request(`${location.origin}/evidence/file-A1.png`))).toBe(false);
    expect(isSafeOfflineCacheRequest(request(`${location.origin}/assets/app-A1.js?token=secret`))).toBe(false);
    expect(isSafeOfflineCacheRequest(request(`${location.origin}/assets/app-A1.js`, 'POST'))).toBe(false);
  });

  it('ships a GET-only static worker with no background sync or mutation replay handler', () => {
    const worker = readFileSync('public/service-worker.js', 'utf8');
    expect(worker).toMatch(/request\.method !== 'GET'\) return/);
    expect(worker).not.toMatch(/addEventListener\(['"]sync['"]/);
    expect(worker).not.toMatch(/fetch\([^\n]*method\s*:/);
    expect(worker).not.toMatch(/\/api\/v1\/(?:offers|trades|payments|fpo)/);
  });

  it('keeps simple-mode preference isolated by account ID', () => {
    setSimpleMode('farmer-a', true);
    expect(getSimpleMode('farmer-a')).toBe(true);
    expect(getSimpleMode('farmer-b')).toBe(false);
  });

  it('requires the active local farmer session to match before foreground queue processing', () => {
    localStorage.setItem('krishilink_user', JSON.stringify({ id: 'farmer-a', role: 'farmer' }));
    expect(storedSessionMatches('farmer-a')).toBe(true);
    expect(storedSessionMatches('farmer-b')).toBe(false);
    localStorage.setItem('krishilink_user', JSON.stringify({ id: 'fpo-a', role: 'fpo' }));
    expect(storedSessionMatches('fpo-a')).toBe(false);
  });
});
