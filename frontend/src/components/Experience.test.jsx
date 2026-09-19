import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Badge, Button, Card, DataState, Field, Skeleton, StatusPill } from './Experience';
import ErrorBoundary from './ErrorBoundary';
import { LanguageProvider } from '../hooks/useLanguage';

describe('shared experience primitives', () => {
  it('associates field labels and descriptions without disabling autocomplete by default', () => {
    render(<Field label="Mobile number" hint="Use the number on your account" />);

    const field = screen.getByRole('textbox', { name: 'Mobile number' });
    expect(field).not.toHaveAttribute('autocomplete');
    expect(field).toHaveAccessibleDescription('Use the number on your account');
  });

  it('exposes validation errors and preserves an explicit autocomplete purpose', () => {
    render(
      <Field label="Email address" type="email" autoComplete="email" error="Enter a valid email" />,
    );

    const field = screen.getByRole('textbox', { name: 'Email address' });
    expect(field).toHaveAttribute('autocomplete', 'email');
    expect(field).toHaveAttribute('aria-invalid', 'true');
    expect(field).toHaveAccessibleDescription('Enter a valid email');
  });

  it('keeps loading buttons disabled and announces the busy state', () => {
    render(<Button loading>Save listing</Button>);

    const button = screen.getByRole('button', { name: 'Save listing' });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(button).toHaveAttribute('type', 'button');
  });

  it('requires an accessible name for icon-only buttons', () => {
    expect(() => render(<Button iconOnly />)).toThrow('Icon-only buttons need an accessible name.');
  });

  it('supports native card semantics, named badges and neutral status labels', () => {
    render(
      <>
        <Card as="article" aria-label="Listing summary">
          Wheat, 20 quintals
        </Card>
        <Badge tone="success">Verified phone</Badge>
        <StatusPill tone="warning">Payment pending</StatusPill>
      </>,
    );

    expect(screen.getByRole('article', { name: 'Listing summary' })).toHaveTextContent(
      'Wheat, 20 quintals',
    );
    expect(screen.getByText('Verified phone')).toHaveClass('badge-success');
    expect(screen.getByText('Payment pending')).toHaveClass('status-pill-warning');
  });

  it('provides an announced loading state and keeps offline/stale copy caller-translated', () => {
    const { rerender } = render(
      <LanguageProvider>
        <DataState loading />
      </LanguageProvider>,
    );
    expect(screen.getByRole('status')).toHaveTextContent('Loading');

    rerender(
      <LanguageProvider>
        <DataState staleMessage="जुनी माहिती" offlineMessage="इंटरनेट जोडलेले नाही">
          <p>मंडई भाव</p>
        </DataState>
      </LanguageProvider>,
    );
    expect(screen.getByText('जुनी माहिती')).toBeInTheDocument();
    expect(screen.getByText('इंटरनेट जोडलेले नाही')).toBeInTheDocument();
    expect(screen.getByText('मंडई भाव')).toBeInTheDocument();
  });

  it('marks decorative skeletons hidden from assistive technology', () => {
    render(<Skeleton data-testid="price-skeleton" />);
    expect(screen.getByTestId('price-skeleton')).toHaveAttribute('aria-hidden', 'true');
  });

  it.each([
    ['en', 'Loading…'],
    ['hi', 'जानकारी आ रही है…'],
    ['mr', 'माहिती येत आहे…'],
  ])('announces the loading label in %s', (language, expected) => {
    window.localStorage.setItem('krishilink_lang', language);
    render(
      <LanguageProvider>
        <DataState loading />
      </LanguageProvider>,
    );

    expect(screen.getByRole('status')).toHaveTextContent(expected);
    expect(document.documentElement).toHaveAttribute('lang', language);
    window.localStorage.removeItem('krishilink_lang');
  });

  it('renders an accessible recovery boundary with local navigation', () => {
    function BrokenChild() {
      throw new Error('render failure');
    }

    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <MemoryRouter>
        <ErrorBoundary title="This page had a problem" retry="Try again" home="Go home">
          <BrokenChild />
        </ErrorBoundary>
      </MemoryRouter>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('This page had a problem');
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Go home' })).toHaveAttribute('href', '/');
    consoleError.mockRestore();
  });
});
