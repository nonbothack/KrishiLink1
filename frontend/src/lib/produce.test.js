import { describe, expect, it } from 'vitest';
import { canonicalLot, convertUnit, dateLabel } from './produce';

describe('produce units', () => {
  it('converts user-entered units to the API quintal contract', () => {
    expect(canonicalLot(250, 30, 'kg')).toEqual({ quantity: 2.5, asking_price: 3000, unit: 'quintal' });
    expect(canonicalLot(2, 30000, 'tonne')).toEqual({ quantity: 20, asking_price: 3000, unit: 'quintal' });
  });

  it('preserves value while switching display units', () => {
    expect(convertUnit(1, 3000, 'quintal', 'kg')).toEqual({ quantity: 100, price: 30 });
  });

  it('rejects invalid lots and invalid dates', () => {
    expect(() => canonicalLot(0, 100, 'kg')).toThrow();
    expect(dateLabel('not-a-date')).toBeNull();
  });
});
