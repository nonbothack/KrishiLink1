import { useEffect, useRef, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Sprout, Menu, X, ArrowUpRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { dashboardFor } from '../lib/session';
export function LanguagePicker() {
  const { language, changeLanguage, t } = useLanguage();
  return (
    <select
      className="language-picker"
      aria-label={t('language')}
      value={language}
      onChange={(e) => changeLanguage(e.target.value)}
    >
      <option value="en">English</option>
      <option value="mr">मराठी</option>
      <option value="hi">हिंदी</option>
    </select>
  );
}
export function Brand() {
  return (
    <Link className="brand" to="/" aria-label="KrishiLink">
      <span className="brand-icon">
        <Sprout size={25} />
      </span>
      <span>
        Krishi<span className="brand-light">Link</span>
        <small>GROW. CONNECT. THRIVE.</small>
      </span>
    </Link>
  );
}
export default function Navbar() {
  const [open, setOpen] = useState(false);
  const menuToggle = useRef(null);
  const { isLoggedIn, user } = useAuth();
  const { t } = useLanguage();
  useEffect(() => {
    if (!open) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const firstItem = document.querySelector('#mobile-menu a, #mobile-menu button');
    firstItem?.focus();

    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
        menuToggle.current?.focus();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = [...document.querySelectorAll('#mobile-menu a[href], #mobile-menu button:not([disabled]), #mobile-menu select:not([disabled])')];
      if (!items.length) return;
      const first = items[0];
      const last = items.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  return (
    <header className="site-header">
      <a className="skip-link" href="#main">
        {t('skip')}
      </a>
      <div className="site-container header-inner">
        <Brand />
        <nav className="desktop-nav" aria-label={t('menu')}>
          <NavLink to="/prices">{t('prices')}</NavLink>
          <NavLink to="/mandis">{t('publicMandis')}</NavLink>
          <NavLink to="/buyers">{t('publicBuyers')}</NavLink>
          <Link to="/#how-it-works">{t('howItWorks')}</Link>
          <NavLink to="/help">{t('help')}</NavLink>
        </nav>
        <div className="header-actions">
          <LanguagePicker />
          <Link
            className="button small secondary desktop-auth"
            to={isLoggedIn ? dashboardFor(user.role) : '/login'}
          >
            {t(isLoggedIn ? 'dashboard' : 'login')}
            <ArrowUpRight size={17} />
          </Link>
          {!isLoggedIn && <Link className="button small desktop-register" to="/register?role=farmer">{t('register')}</Link>}
          <button
            ref={menuToggle}
            className="icon-button menu-toggle"
            aria-label={t('menu')}
            aria-expanded={open}
            aria-controls="mobile-menu"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>
      {open && (
        <div className="mobile-menu-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}>
          <nav id="mobile-menu" className="mobile-menu" role="dialog" aria-modal="true" aria-label={t('menu')}>
            <Link className="mobile-menu-primary" onClick={() => setOpen(false)} to="/prices">{t('checkPrices')}<ArrowUpRight size={18} /></Link>
            <button className="mobile-menu-close" type="button" onClick={() => { setOpen(false); menuToggle.current?.focus(); }}>{t('close')}<X size={18} /></button>
            {[
              ['/prices', 'prices'],
              ['/mandis', 'publicMandis'],
              ['/buyers', 'publicBuyers'],
              ['/#how-it-works', 'howItWorks'],
              ['/help', 'help'],
              ['/contact', 'publicContact'],
              [isLoggedIn ? dashboardFor(user.role) : '/login', isLoggedIn ? 'dashboard' : 'login'],
              ...(!isLoggedIn ? [['/register?role=farmer', 'register']] : []),
            ].map(([path, label]) => <Link onClick={() => setOpen(false)} key={path} to={path}>{t(label)}</Link>)}
            <div className="mobile-menu-language"><span>{t('language')}</span><LanguagePicker /></div>
            {import.meta.env.VITE_PUBLIC_SUPPORT_PHONE && <a className="mobile-support-link" href={`tel:${String(import.meta.env.VITE_PUBLIC_SUPPORT_PHONE).replace(/[^+\d]/g, '')}`}>{import.meta.env.VITE_PUBLIC_SUPPORT_PHONE}</a>}
          </nav>
        </div>
      )}
    </header>
  );
}
