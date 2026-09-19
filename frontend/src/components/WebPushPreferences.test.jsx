import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LanguageProvider } from '../hooks/useLanguage';
import WebPushPreferences from './WebPushPreferences';

const push = vi.hoisted(() => ({
  isPushSupported: vi.fn(),
  reconcileGrantedSubscription: vi.fn(),
  enableWebPush: vi.fn(),
  disableWebPush: vi.fn(),
}));
const api = vi.hoisted(() => ({ apiCall: vi.fn() }));
vi.mock('../services/webPush', () => push);
vi.mock('../lib/http', () => api);

describe('WebPushPreferences', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    push.isPushSupported.mockReturnValue(true);
    push.reconcileGrantedSubscription.mockResolvedValue({ status: 'OFF' });
    api.apiCall.mockResolvedValue({ success: true, data: { status: 'AVAILABLE' } });
    window.Notification = { permission: 'default', requestPermission: vi.fn() };
  });

  it('does not ask notification permission on mount and asks only after the user chooses enable', async () => {
    push.enableWebPush.mockResolvedValue({ status: 'ACTIVE' });
    render(<LanguageProvider><WebPushPreferences /></LanguageProvider>);
    await waitFor(() => expect(screen.getByText(/Notifications are off/)).toBeInTheDocument());
    expect(window.Notification.requestPermission).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Turn on notifications' }));
    await waitFor(() => expect(screen.getByText(/Notifications are on/)).toBeInTheDocument());
    expect(push.enableWebPush).toHaveBeenCalledWith('en');
  });

  it('shows unavailable provider state without displaying an enable action', async () => {
    api.apiCall.mockResolvedValue({ success: true, data: { status: 'UNCONFIGURED' } });
    render(<LanguageProvider><WebPushPreferences /></LanguageProvider>);
    expect(await screen.findByText(/not configured right now/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Turn on notifications' })).not.toBeInTheDocument();
    expect(window.Notification.requestPermission).not.toHaveBeenCalled();
  });

  it('requires an explicit action before a shared browser is reassociated', async () => {
    window.Notification.permission = 'granted';
    push.reconcileGrantedSubscription.mockResolvedValue({ status: 'REASSOCIATION_REQUIRED' });
    push.enableWebPush.mockResolvedValue({ status: 'ACTIVE' });
    render(<LanguageProvider><WebPushPreferences /></LanguageProvider>);
    const action = await screen.findByRole('button', { name: 'Turn on for this account' });
    expect(window.Notification.requestPermission).not.toHaveBeenCalled();
    expect(push.enableWebPush).not.toHaveBeenCalled();
    fireEvent.click(action);
    await waitFor(() => expect(push.enableWebPush).toHaveBeenCalledWith('en'));
  });
});
