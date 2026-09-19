import { useState, useEffect } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Sprout, ChartColumn, FileText, Wallet, CircleHelp, Menu, BellRing } from 'lucide-react';
import { Brand, LanguagePicker } from '../components/Navbar';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { dashboardFor } from '../lib/session';
import { getSimpleMode } from '../lib/experiencePreferences';
export default function DashboardLayout({ children }) {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [offline, setOffline] = useState(!navigator.onLine);
  const [simpleMode, setSimpleMode] = useState(() => user.role === 'farmer' && getSimpleMode(user.id));
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);
  useEffect(() => {
    const refreshPreference = (event) => {
      if (!event?.detail?.ownerId || event.detail.ownerId === user.id) {
        setSimpleMode(user.role === 'farmer' && getSimpleMode(user.id));
      }
    };
    window.addEventListener('krishilink:experience-preference', refreshPreference);
    window.addEventListener('storage', refreshPreference);
    return () => {
      window.removeEventListener('krishilink:experience-preference', refreshPreference);
      window.removeEventListener('storage', refreshPreference);
    };
  }, [user.id, user.role]);
  const nav = ['admin', 'operator', 'support', 'reviewer', 'fraud_reviewer'].includes(user.role) ? [
    ['/admin/operations', 'Operations', LayoutDashboard],
    ['/help', 'Help', CircleHelp],
  ] : user.role === 'buyer' ? [
    [dashboardFor(user.role), 'home', LayoutDashboard],
    ['/buyer/discover', 'discoverSupply', Sprout],
    ['/buyer/requirements', 'buyerRequirements', FileText],
    ['/offers', 'offers', FileText],
    ['/transactions', 'orders', Wallet],
    ['/help', 'more', CircleHelp],
  ] : [
    [dashboardFor(user.role), 'dashboard', LayoutDashboard],
    ['/prices', 'prices', ChartColumn],
    ...(user.role !== 'buyer' ? [['/sell', 'listCrop', Sprout]] : []),
    ['/offers', 'offers', FileText],
    ['/transactions', 'orders', Wallet],
    ['/grievances', 'support', CircleHelp],
    ['/help', 'help', CircleHelp],
  ];
  const mobile = ['admin', 'operator', 'support', 'reviewer', 'fraud_reviewer'].includes(user.role)
    ? nav
    : user.role === 'farmer'
    ? [
        [dashboardFor(user.role), 'home', LayoutDashboard],
        ['/prices', 'prices', ChartColumn],
        ['/sell', 'sellProduce', Sprout],
        ['/offers', 'offers', FileText],
        ['/farmer/more', 'more', Menu],
      ]
    : user.role === 'buyer'
      ? [nav[0], nav[1], nav[2], nav[3], nav[5]]
      : [nav[0], nav[1], nav.find((x) => x[0] === '/offers'), nav.find((x) => x[0] === '/transactions'), nav.find((x) => x[0] === '/help')];
  const links = (items) =>
    items.map(([path, label, Icon]) => (
      <NavLink key={path} to={path}>
        <Icon size={21} />
        <span>{t(label)}</span>
      </NavLink>
    ));
  return (
    <div className={`app-shell${simpleMode ? ' simple-mode' : ''}`}>
      <a className="skip-link" href="#main">
        {t('skip')}
      </a>
      <aside className="app-sidebar">
        <Brand />
        <nav aria-label={t('menu')}>{links(nav)}</nav>
        <button
          className="button secondary"
          onClick={() => {
            logout();
            navigate('/');
          }}
        >
          {t('logout')}
        </button>
      </aside>
      <div className="app-content">
        <header className="app-header">
          <span className="mobile-brand">
            <Brand />
          </span>
          <div className="user-label">
            <strong>{user.name}</strong>
            <small>{t(user.role + 'Role')}</small>
          </div>
          <Link className="notification-settings-link" to="/notification-settings" aria-label={t('notificationSettings')} title={t('notificationSettings')}>
            <BellRing size={20} aria-hidden="true" />
            <span className="visually-hidden">{t('notificationSettings')}</span>
          </Link>
          <LanguagePicker />
          <button
            className="text-link"
            onClick={() => {
              logout();
              navigate('/');
            }}
          >
            {t('logout')}
          </button>
        </header>
        {offline && (
          <div className="offline-strip" role="status">
            {t('offline')}
          </div>
        )}
        <main id="main" className="app-main" tabIndex={-1}>
          {children || <Outlet />}
        </main>
      </div>
      <nav className="app-mobile-nav" aria-label={t('menu')}>
        {links(mobile)}
      </nav>
    </div>
  );
}
