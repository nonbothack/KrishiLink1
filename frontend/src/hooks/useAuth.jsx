import { createContext, useContext, useEffect, useState } from 'react';
import { apiCall, restoreSession, setAccessToken } from '../lib/http';
import { clearSession, normalizeIdentifier, normalizePhone, readSession } from '../lib/session';
import { getPublicSnapshot } from '../lib/publicSnapshot';
import { cleanupPushOnLogout } from '../services/webPush';

const AuthContext = createContext(null);
const publicSessionUser = (user) => ({
  id: user.id,
  full_name: user.full_name,
  name: user.full_name,
  role: user.role,
});
const clearUserScopedDrafts = (userId) => {
  if (!userId) return;
  try {
    for (const key of [`listing-draft-${userId}`, `listing-key-${userId}`, `farmer-crops-${userId}`, `farmer-last-lot-${userId}`]) {
      localStorage.removeItem(key);
    }
    const prefixes = [`offer-accept-key-${userId}-`, `offer-counter-key-${userId}-`];
    for (let index = localStorage.length - 1; index >= 0; index -= 1) {
      const key = localStorage.key(index);
      if (prefixes.some((prefix) => key?.startsWith(prefix))) localStorage.removeItem(key);
    }
  } catch { /* Local storage can be disabled by the browser. */ }
};

export function AuthProvider({ children }) {
  const prerenderedPublicPage = Boolean(getPublicSnapshot());
  const [user, setUser] = useState(() => (prerenderedPublicPage ? null : readSession()));
  const [loading, setLoading] = useState(() => prerenderedPublicPage || !!readSession());

  useEffect(() => {
    let active = true;
    localStorage.removeItem('krishilink_access_token');
    localStorage.removeItem('krishilink_refresh_token');
    const savedSession = readSession();
    if (savedSession) {
      if (prerenderedPublicPage) setUser(savedSession);
      restoreSession()
        .then(() => apiCall('/api/v1/auth/me'))
        .then((res) => {
          if (!active) return;
          if (res.success) {
            const normal = { ...res.data, name: res.data.full_name };
            setUser(normal);
            localStorage.setItem('krishilink_user', JSON.stringify(publicSessionUser(normal)));
          } else {
            setUser(null);
            clearSession();
          }
          setLoading(false);
        })
        .catch((error) => {
          if (!active) return;
          setUser(null);
          if (error.status === 401) clearSession();
          setLoading(false);
        });
    } else setLoading(false);
    const expired = () => {
      setUser(null);
      setLoading(false);
    };
    const changed = (event) => {
      if (event.key === 'krishilink_user' && !event.newValue) {
        setAccessToken(null);
        setUser(null);
      }
    };
    window.addEventListener('session-expired', expired);
    window.addEventListener('storage', changed);
    return () => {
      active = false;
      window.removeEventListener('session-expired', expired);
      window.removeEventListener('storage', changed);
    };
  }, [prerenderedPublicPage]);

  function acceptSession(data) {
    const normal = { ...data.user, name: data.user.full_name };
    if (user?.id && user.id !== normal.id) clearUserScopedDrafts(user.id);
    setAccessToken(data.access_token);
    localStorage.setItem('krishilink_user', JSON.stringify(publicSessionUser(normal)));
    setUser(normal);
    return { success: true, user: normal };
  }

  async function authenticate(path, payload) {
    const res = await apiCall('/api/v1/auth/' + path, {
      method: 'POST',
      auth: false,
      body: JSON.stringify(payload),
    });
    if (!res.success) return res;
    return acceptSession(res.data);
  }

  const login = (identifier, password) =>
    authenticate('login', { email: normalizeIdentifier(identifier), password });

  const requestOtp = async (phone) =>
    apiCall('/api/v1/auth/otp/request', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ phone: normalizePhone(phone) }),
    });

  const verifyOtp = async (phone, code) => {
    const res = await apiCall('/api/v1/auth/otp/verify', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ phone: normalizePhone(phone), code }),
    });
    if (!res.success) return res;
    if (res.data.user) return acceptSession(res.data);
    return {
      success: true,
      registrationTicket: res.data.registration_ticket,
      phone: res.data.phone,
      policyVersions: res.data.policy_versions,
    };
  };

  const register = async (data) => {
    const payload = {
      full_name: data.name.trim(),
      email: data.email?.trim() || null,
      phone: normalizePhone(data.phone),
      password: data.password || null,
      role: data.role,
      business_name: data.businessName?.trim() || null,
      organization_name: data.organizationName?.trim() || null,
      procurement_categories: data.procurementCategories || [],
      primary_crops: data.primaryCrops || [],
      verification_ticket: data.verificationTicket,
      policy_versions: data.policyVersions || {},
      marketing_consent: data.marketingConsent === true,
      location: data.location?.trim() || null,
      district: data.district?.trim() || null,
      state: data.state?.trim() || null,
      state_id: data.stateId || null,
      district_id: data.districtId || null,
      subdistrict_id: data.subdistrictId || null,
      location_consent: Boolean(data.locationConsent),
      latitude: data.coordinates?.latitude ?? null,
      longitude: data.coordinates?.longitude ?? null,
      coordinate_accuracy_m: data.coordinates?.accuracy ?? null,
    };
    const res = await apiCall('/api/v1/auth/register', {
      method: 'POST',
      auth: false,
      body: JSON.stringify(payload),
    });
    if (!res.success) return res;
    return acceptSession(res.data);
  };

  const logout = async () => {
    await cleanupPushOnLogout();
    const pending = apiCall('/api/v1/auth/logout', { method: 'POST' });
    clearUserScopedDrafts(user?.id);
    clearSession();
    setUser(null);
    await pending;
    setAccessToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isLoggedIn: !!user,
        isFarmer: user?.role === 'farmer',
        isBuyer: user?.role === 'buyer',
        isFPO: user?.role === 'fpo',
        login,
        requestOtp,
        verifyOtp,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
