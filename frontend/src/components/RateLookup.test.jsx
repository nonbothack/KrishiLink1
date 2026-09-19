import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '../hooks/useLanguage';
import RateLookup from './RateLookup';

vi.mock('../services/api', () => ({
  getCrops: vi.fn(),
  getReportedPrices: vi.fn(),
}));

import { getCrops, getReportedPrices } from '../services/api';

describe('RateLookup canonical crop registry', () => {
  beforeEach(() => {
    getCrops.mockResolvedValue({
      success: true,
      data: [
        {
          id: 'crop-wheat',
          name: 'Wheat',
          name_hindi: 'गेहूँ',
          name_marathi: 'गहू',
          aliases: ['Gehun'],
          valid_units: ['quintal', 'kg'],
          default_unit: 'quintal',
        },
      ],
      pages: 1,
    });
    getReportedPrices.mockResolvedValue({ success: true, data: [] });
  });

  it('gets selectable crops and localized labels from the backend registry', async () => {
    window.localStorage.setItem('krishilink_lang', 'mr');
    render(
      <MemoryRouter>
        <LanguageProvider>
          <RateLookup />
        </LanguageProvider>
      </MemoryRouter>,
    );

    const select = await screen.findByRole('combobox', { name: 'पीक' });
    expect(select).toHaveValue('Wheat');
    expect(screen.getByRole('option', { name: 'गहू' })).toHaveValue('Wheat');
    await waitFor(() => expect(getReportedPrices).toHaveBeenCalledWith(expect.objectContaining({ crop: 'Wheat' })));
  });

  it('labels old official reports with their source unit and does not turn them into a sell price', async () => {
    getReportedPrices.mockResolvedValueOnce({
      success: true,
      data: [{
        id: 'reported-price-1', crop: 'Wheat', market: 'Lasalgaon', district: 'Nashik',
        modal_price: '2100.00', unit: 'INR/number', price_date: '2026-09-01',
        freshness_state: 'stale', source: 'AGMARKNET daily reported mandi prices', location_verified: false,
      }],
    });
    window.localStorage.setItem('krishilink_lang', 'en');
    render(
      <MemoryRouter>
        <LanguageProvider>
          <RateLookup />
        </LanguageProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText('per item')).toBeInTheDocument();
    expect(screen.getByText('Older reported price')).toBeInTheDocument();
    expect(screen.getByText(/AGMARKNET daily reported mandi prices/)).toBeInTheDocument();
    expect(screen.getByText('Market location not verified')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /List crop/ })).not.toBeInTheDocument();
  });
});
