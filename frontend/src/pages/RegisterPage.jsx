import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Sprout, Store, Users } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { apiCall } from '../lib/http';
import { roles, safeNext, normalizePhone } from '../lib/session';
import { Field, Notice } from '../components/Experience';
import OtpInput from '../components/OtpInput';

const roleOptions = [
  ['farmer', Sprout],
  ['buyer', Store],
  ['fpo', Users],
];

function versionValues(documents) {
  return Object.fromEntries(Object.entries(documents || {}).map(([key, item]) => [key, item.version]));
}

export default function RegisterPage() {
  const { requestOtp, verifyOtp, register } = useAuth();
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const verified = location.state?.verificationTicket
    ? {
        ticket: location.state.verificationTicket,
        phone: normalizePhone(location.state.verifiedPhone || ''),
        documents: location.state.policyVersions || {},
      }
    : null;
  const [step, setStep] = useState(verified ? 2 : 0);
  const [form, setForm] = useState(() => ({
    role: roles.includes(params.get('role')) ? params.get('role') : 'farmer',
    phone: verified?.phone || '',
    name: '',
    email: '',
    password: '',
    businessName: '',
    organizationName: '',
    primaryCropsText: '',
    procurementCategoriesText: '',
    location: '',
    state: '',
    district: '',
    stateId: '',
    districtId: '',
    subdistrictId: '',
  }));
  const [ticket, setTicket] = useState(verified?.ticket || '');
  const [policyDocuments, setPolicyDocuments] = useState(verified?.documents || {});
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [subdistricts, setSubdistricts] = useState([]);
  const [geoLoaded, setGeoLoaded] = useState(false);
  const [otp, setOtp] = useState('');
  const [developmentCode, setDevelopmentCode] = useState('');
  const [resendSeconds, setResendSeconds] = useState(0);
  const [locationConsent, setLocationConsent] = useState(false);
  const [coordinates, setCoordinates] = useState(null);
  const [locationMessage, setLocationMessage] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const headingRef = useRef(null);
  const next = params.get('next') || '';
  const displayName = (place) =>
    language === 'hi' ? place.name_hindi || place.name : language === 'mr' ? place.name_marathi || place.name : place.name;
  const policyVersions = useMemo(() => versionValues(policyDocuments), [policyDocuments]);

  useEffect(() => {
    headingRef.current?.focus();
  }, [step]);

  useEffect(() => {
    if (resendSeconds > 0) {
      const timer = window.setTimeout(() => setResendSeconds((seconds) => seconds - 1), 1000);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [resendSeconds]);

  useEffect(() => {
    let active = true;
    apiCall('/api/v1/geo/states', { auth: false })
      .then((res) => {
        if (active && res.success) setStates(res.data?.items || []);
      })
      .finally(() => {
        if (active) setGeoLoaded(true);
      });
    apiCall('/api/v1/auth/policy-versions', { auth: false }).then((res) => {
      if (active && res.success) setPolicyDocuments(res.data || {});
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setDistricts([]);
    setSubdistricts([]);
    if (!form.stateId) return undefined;
    apiCall(`/api/v1/geo/districts?state_id=${encodeURIComponent(form.stateId)}`, { auth: false }).then((res) => {
      if (active && res.success) setDistricts(res.data?.items || []);
    });
    return () => {
      active = false;
    };
  }, [form.stateId]);

  useEffect(() => {
    let active = true;
    setSubdistricts([]);
    if (!form.districtId) return undefined;
    apiCall(`/api/v1/geo/subdistricts?district_id=${encodeURIComponent(form.districtId)}`, { auth: false }).then((res) => {
      if (active && res.success) setSubdistricts(res.data?.items || []);
    });
    return () => {
      active = false;
    };
  }, [form.districtId]);

  function change(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function sendCode(e) {
    e.preventDefault();
    setError('');
    const phone = normalizePhone(form.phone);
    if (!/^[6-9]\d{9}$/.test(phone)) {
      setError('validation');
      return;
    }
    setBusy(true);
    const res = await requestOtp(phone);
    setBusy(false);
    if (!res.success) {
      setError('otpRequestFailed');
      return;
    }
    change('phone', phone);
    setDevelopmentCode(res.data?.development_code || '');
    setResendSeconds(res.data?.resend_after_seconds || 30);
    setStep(1);
  }

  async function checkCode(e) {
    e.preventDefault();
    if (otp.length !== 6) return;
    setError('');
    setBusy(true);
    const res = await verifyOtp(form.phone, otp);
    setBusy(false);
    if (res.success && res.user) {
      navigate(safeNext(next, res.user.role), { replace: true });
      return;
    }
    if (res.success && res.registrationTicket) {
      setTicket(res.registrationTicket);
      setForm((current) => ({ ...current, phone: res.phone || current.phone }));
      if (res.policyVersions) setPolicyDocuments(res.policyVersions);
      setStep(2);
      return;
    }
    setError('otpVerifyFailed');
  }

  async function resendCode() {
    if (busy || resendSeconds > 0) return;
    setBusy(true);
    setError('');
    const res = await requestOtp(form.phone);
    setBusy(false);
    if (res.success) {
      setOtp('');
      setDevelopmentCode(res.data?.development_code || '');
      setResendSeconds(res.data?.resend_after_seconds || 30);
    } else setError('otpRequestFailed');
  }

  function requestGpsLocation() {
    setLocationConsent(true);
    setLocationMessage('');
    if (!navigator.geolocation) {
      setLocationMessage('gpsUnavailable');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoordinates({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setLocationMessage('gpsSaved');
      },
      (failure) => {
        setCoordinates(null);
        setLocationMessage(failure.code === 1 ? 'gpsDenied' : 'gpsUnavailable');
      },
      { enableHighAccuracy: false, maximumAge: 60_000, timeout: 12_000 },
    );
  }

  async function finishRegistration(e) {
    e.preventDefault();
    setError('');
    if (!termsAccepted || !privacyAccepted) {
      setError('consentRequired');
      return;
    }
    if (form.role === 'buyer' && form.businessName.trim().length < 2) {
      setError('organizationRequired');
      return;
    }
    if (form.role === 'fpo' && form.organizationName.trim().length < 2) {
      setError('organizationRequired');
      return;
    }
    if (form.password && form.password.length < 10) {
      setError('passwordHint');
      return;
    }
    setBusy(true);
    const result = await register({
      ...form,
      verificationTicket: ticket,
      policyVersions,
      marketingConsent,
      locationConsent: locationConsent && Boolean(coordinates),
      coordinates,
      primaryCrops: form.primaryCropsText.split(',').map((crop) => crop.trim()).filter(Boolean),
      procurementCategories: form.procurementCategoriesText.split(',').map((crop) => crop.trim()).filter(Boolean),
    });
    setBusy(false);
    if (result.success) navigate(safeNext(next, result.user.role), { replace: true });
    else setError(result.error === 'conflict' ? 'conflict' : 'server');
  }

  const stepLabel = [t('identityStep'), t('otpStep'), t('profileStep')][step];
  const title = step === 0 ? t('registerTitle') : step === 1 ? t('verifyOtp') : t('profileStep');

  return (
    <div className="site-container narrow page-section registration-page">
      <p className="eyebrow">{t('register')}</p>
      <h1 ref={headingRef} tabIndex={-1}>{title}</h1>
      <div className="registration-progress" aria-label={t('registerProgress')}>
        {[t('identityStep'), t('otpStep'), t('profileStep')].map((label, index) => (
          <span key={label} aria-current={step === index ? 'step' : undefined} className={step === index ? 'current' : ''}>
            {index + 1}. {label}
          </span>
        ))}
      </div>

      {step === 0 && (
        <form className="panel form-stack" onSubmit={sendCode}>
          <fieldset>
            <legend>{t('chooseRole')}</legend>
            <div className="role-options">
              {roleOptions.map(([role, Icon]) => (
                <label key={role} className={form.role === role ? 'selected' : ''}>
                  <input type="radio" name="role" value={role} checked={form.role === role} onChange={() => change('role', role)} />
                  <Icon size={24} aria-hidden="true" />
                  <span>{t(role + 'Role')}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <Field
            label={t('phone')}
            hint={t('phoneHint')}
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            required
            value={form.phone}
            onChange={(event) => change('phone', event.target.value)}
          />
          {error && <Notice error>{t(error)}</Notice>}
          <button className="button wide" disabled={busy}>
            {t(busy ? 'loading' : 'getOtp')} <ArrowRight size={19} />
          </button>
        </form>
      )}

      {step === 1 && (
        <form className="panel form-stack" onSubmit={checkCode}>
          <p className="muted" aria-live="polite">{t('otpSent')}</p>
          <OtpInput value={otp} onChange={setOtp} label={t('otpCode')} disabled={busy} />
          {developmentCode && <Notice>{t('otpDevelopmentCode')}: <strong>{developmentCode}</strong></Notice>}
          <div className="otp-resend-row">
            {resendSeconds > 0 ? <span className="muted">{t('resendIn')} {resendSeconds}s</span> : (
              <button type="button" className="text-button" onClick={resendCode} disabled={busy}>{t('otpResend')}</button>
            )}
            <button type="button" className="text-button" onClick={() => { setStep(0); setOtp(''); }}>{t('changePhone')}</button>
          </div>
          {error && <Notice error>{t(error)}</Notice>}
          <button className="button wide" disabled={busy || otp.length !== 6}>
            {t(busy ? 'loading' : 'verifyOtp')} <ArrowRight size={19} />
          </button>
        </form>
      )}

      {step === 2 && (
        <form className="panel form-stack" onSubmit={finishRegistration}>
          <p className="muted">{stepLabel} · {t('phoneVerified')}</p>
          <Field label={t('name')} autoComplete="name" required minLength={2} value={form.name} onChange={(event) => change('name', event.target.value)} />
          {form.role === 'buyer' && (
            <>
              <Field label={t('businessName')} autoComplete="organization" required value={form.businessName} onChange={(event) => change('businessName', event.target.value)} />
              <Field label={`${t('email')} (${t('optional')})`} type="email" autoComplete="email" value={form.email} onChange={(event) => change('email', event.target.value)} />
              <Field label={t('procurementCategories')} hint={t('commaSeparated')} value={form.procurementCategoriesText} onChange={(event) => change('procurementCategoriesText', event.target.value)} />
            </>
          )}
          {form.role === 'fpo' && (
            <>
              <Field label={t('organizationName')} autoComplete="organization" required value={form.organizationName} onChange={(event) => change('organizationName', event.target.value)} />
              <Field label={`${t('email')} (${t('optional')})`} type="email" autoComplete="email" value={form.email} onChange={(event) => change('email', event.target.value)} />
            </>
          )}
          {form.role === 'farmer' && (
            <>
              <Field label={`${t('email')} (${t('optional')})`} type="email" autoComplete="email" value={form.email} onChange={(event) => change('email', event.target.value)} />
              <Field label={`${t('primaryCrops')} (${t('optional')})`} hint={t('commaSeparated')} value={form.primaryCropsText} onChange={(event) => change('primaryCropsText', event.target.value)} />
            </>
          )}
          <details className="optional-password">
            <summary>{t('addPasswordOptional')}</summary>
            <Field label={t('password')} type="password" autoComplete="new-password" minLength={10} maxLength={72} hint={t('passwordHint')} value={form.password} onChange={(event) => change('password', event.target.value)} />
          </details>

          <section className="onboarding-location" aria-labelledby="location-heading">
            <h2 id="location-heading">{t('locationStep')}</h2>
            <p className="muted">{t('locationPurpose')}</p>
            {!geoLoaded || states.length === 0 ? (
              <>
                {geoLoaded && <p className="muted">{t('noGeographyData')}</p>}
                <Field label={t('state')} autoComplete="address-level1" value={form.state} onChange={(event) => change('state', event.target.value)} />
                <Field label={t('district')} autoComplete="address-level2" value={form.district} onChange={(event) => change('district', event.target.value)} />
                <Field label={t('manualLocation')} autoComplete="address-line1" value={form.location} onChange={(event) => change('location', event.target.value)} />
              </>
            ) : (
              <div className="form-stack">
                <label className="field-label">
                  <span>{t('selectState')}</span>
                  <select value={form.stateId} onChange={(event) => {
                    const state = states.find((item) => item.id === event.target.value);
                    setForm((current) => ({ ...current, stateId: event.target.value, state: state?.name || '', districtId: '', district: '', subdistrictId: '' }));
                  }}>
                    <option value="">{t('optional')}</option>
                    {states.map((place) => <option key={place.id} value={place.id}>{displayName(place)}</option>)}
                  </select>
                </label>
                {form.stateId && districts.length > 0 && (
                  <label className="field-label">
                    <span>{t('selectDistrict')}</span>
                    <select value={form.districtId} onChange={(event) => {
                      const district = districts.find((item) => item.id === event.target.value);
                      setForm((current) => ({ ...current, districtId: event.target.value, district: district?.name || '', subdistrictId: '' }));
                    }}>
                      <option value="">{t('optional')}</option>
                      {districts.map((place) => <option key={place.id} value={place.id}>{displayName(place)}</option>)}
                    </select>
                  </label>
                )}
                {form.districtId && subdistricts.length > 0 && (
                  <label className="field-label">
                    <span>{t('selectSubdistrict')}</span>
                    <select value={form.subdistrictId} onChange={(event) => change('subdistrictId', event.target.value)}>
                      <option value="">{t('optional')}</option>
                      {subdistricts.map((place) => <option key={place.id} value={place.id}>{displayName(place)}</option>)}
                    </select>
                  </label>
                )}
              </div>
            )}
            <button type="button" className="button secondary location-button" onClick={requestGpsLocation}>
              {t('useMyLocation')}
            </button>
            {coordinates && <p className="muted">{t('gpsSaved')} · {Math.round(coordinates.accuracy)}m</p>}
            {locationMessage && !coordinates && <Notice>{t(locationMessage)}</Notice>}
            <p className="muted">{t('locationNotRequired')}</p>
          </section>

          <section className="consent-section" aria-labelledby="consent-heading">
            <h2 id="consent-heading">{t('consentStep')}</h2>
            <label className="check-label">
              <input type="checkbox" required checked={termsAccepted} onChange={(event) => setTermsAccepted(event.target.checked)} />
              <span>{t('termsAck')} <Link to="/terms" target="_blank" rel="noreferrer">{t('terms')}</Link></span>
            </label>
            <p className="muted policy-version">{t('policyVersion')}: {policyDocuments.terms?.version || t('pendingLegal')}</p>
            <label className="check-label">
              <input type="checkbox" required checked={privacyAccepted} onChange={(event) => setPrivacyAccepted(event.target.checked)} />
              <span>{t('privacyAck')} <Link to="/privacy" target="_blank" rel="noreferrer">{t('privacy')}</Link></span>
            </label>
            <p className="muted policy-version">{t('policyVersion')}: {policyDocuments.privacy_notice?.version || t('pendingLegal')}</p>
            <label className="check-label optional-consent">
              <input type="checkbox" checked={marketingConsent} onChange={(event) => setMarketingConsent(event.target.checked)} />
              <span>{t('marketingConsent')}<small>{t('marketingExplanation')}</small></span>
            </label>
          </section>

          {error && <Notice error>{t(error)}</Notice>}
          <div className="form-actions">
            <button type="button" className="button secondary" onClick={() => setStep(1)}>{t('back')}</button>
            <button className="button" disabled={busy}>
              {t(busy ? 'loading' : 'register')} <ArrowRight size={19} />
            </button>
          </div>
        </form>
      )}

      {step !== 0 && step !== 1 && !ticket && <Notice error>{t('otpVerifyFailed')}</Notice>}
      {step === 0 && <p className="muted registration-no-location">{t('locationNotRequired')}</p>}
      <p className="auth-switch">
        {t('existing')} <Link to={'/login?' + new URLSearchParams({ next })}>{t('login')}</Link>
      </p>
    </div>
  );
}
