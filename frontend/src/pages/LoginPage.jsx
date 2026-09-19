import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Sprout } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { safeNext } from '../lib/session';
import { Field, Notice } from '../components/Experience';
import OtpInput from '../components/OtpInput';

export default function LoginPage() {
  const { login, requestOtp, verifyOtp } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const next =
    params.get('next') ||
    (location.state?.from?.pathname || '') + (location.state?.from?.search || '');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [mode, setMode] = useState('otp');
  const [otpSent, setOtpSent] = useState(false);
  const [resendSeconds, setResendSeconds] = useState(0);
  const [developmentCode, setDevelopmentCode] = useState('');
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const headingRef = useRef(null);

  useEffect(() => {
    if (otpSent && resendSeconds > 0) {
      const timer = window.setTimeout(() => setResendSeconds((seconds) => seconds - 1), 1000);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [otpSent, resendSeconds]);

  useEffect(() => {
    headingRef.current?.focus();
  }, [mode, otpSent]);

  function finishLogin(user) {
    navigate(safeNext(next, user.role), { replace: true });
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    if (mode === 'password') {
      const res = await login(identifier, password);
      setBusy(false);
      if (res.success) finishLogin(res.user);
      else setError(res.error || 'server');
      return;
    }
    if (!otpSent) {
      const res = await requestOtp(identifier);
      setBusy(false);
      if (res.success) {
        setOtpSent(true);
        setResendSeconds(res.data?.resend_after_seconds || 30);
        setDevelopmentCode(res.data?.development_code || '');
        setOtp('');
      } else setError('otpRequestFailed');
      return;
    }
    const res = await verifyOtp(identifier, otp);
    setBusy(false);
    if (res.success && res.user) finishLogin(res.user);
    else if (res.success && res.registrationTicket) {
      const query = new URLSearchParams({ next });
      const role = params.get('role');
      if (role) query.set('role', role);
      navigate('/register?' + query.toString(), {
        state: {
          verifiedPhone: res.phone,
          verificationTicket: res.registrationTicket,
          policyVersions: res.policyVersions,
        },
      });
    } else setError('otpVerifyFailed');
  }

  async function resend() {
    if (busy || resendSeconds > 0) return;
    setBusy(true);
    setError('');
    const res = await requestOtp(identifier);
    setBusy(false);
    if (res.success) {
      setOtp('');
      setDevelopmentCode(res.data?.development_code || '');
      setResendSeconds(res.data?.resend_after_seconds || 30);
    } else setError('otpRequestFailed');
  }

  return (
    <div className="auth-section">
      <aside className="auth-aside">
        <Sprout size={48} />
        <h2>{t('heroTitle')}</h2>
        <p>{t('heroText')}</p>
      </aside>
      <div className="auth-card">
        <p className="eyebrow">KRISHILINK</p>
        <h1 ref={headingRef} tabIndex={-1}>{t('loginTitle')}</h1>
        <p className="muted">{t(mode === 'otp' ? 'loginOtpIntro' : 'loginPasswordIntro')}</p>
        {next && <Notice>{t('intentNotice')}</Notice>}
        <form onSubmit={submit} className="form-stack">
          <Field
            label={t('identifier')}
            autoComplete="username"
            type="text"
            inputMode="tel"
            required
            value={identifier}
            disabled={otpSent}
            onChange={(e) => {
              setIdentifier(e.target.value);
              if (e.target.value.includes('@')) setMode('password');
            }}
          />
          {mode === 'password' ? (
            <>
              <Field
                label={t('password')}
                type={show ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <label className="check-label">
                <input type="checkbox" checked={show} onChange={(e) => setShow(e.target.checked)} />
                {t('showPassword')}
              </label>
              <Link className="text-link" to="/help#account">{t('forgotPassword')}</Link>
            </>
          ) : null}
          {otpSent && mode === 'otp' ? (
            <>
              <p className="muted" aria-live="polite">{t('otpSent')}</p>
              <OtpInput value={otp} onChange={setOtp} label={t('otpCode')} disabled={busy} />
              {developmentCode && (
                <Notice>
                  {t('otpDevelopmentCode')}: <strong>{developmentCode}</strong>
                </Notice>
              )}
              <div className="otp-resend-row">
                {resendSeconds > 0 ? (
                  <span className="muted">{t('resendIn')} {resendSeconds}s</span>
                ) : (
                  <button type="button" className="text-button" onClick={resend} disabled={busy}>
                    {t('otpResend')}
                  </button>
                )}
                <button type="button" className="text-button" onClick={() => { setOtpSent(false); setOtp(''); }}>
                  {t('changePhone')}
                </button>
              </div>
            </>
          ) : null}
          {error && <Notice error role="alert">{t(error)}</Notice>}
          <button className="button wide" disabled={busy || (otpSent && mode === 'otp' && otp.length !== 6)}>
            {t(busy ? 'loading' : mode === 'password' ? 'login' : otpSent ? 'verifyOtp' : 'getOtp')}
            <ArrowRight size={19} />
          </button>
        </form>
        <p className="auth-switch">
          {mode === 'otp' ? (
            <button type="button" className="text-button" onClick={() => { setMode('password'); setOtpSent(false); }}>
              {t('usePassword')}
            </button>
          ) : (
            <button type="button" className="text-button" onClick={() => { setMode('otp'); setPassword(''); }}>
              {t('getOtp')}
            </button>
          )}
          {' · '}
          {t('newHere')}{' '}
          <Link to={'/register?' + new URLSearchParams({ next })}>{t('register')}</Link>
        </p>
        <Link className="text-link" to="/help#account">{t('help')}</Link>
      </div>
    </div>
  );
}
