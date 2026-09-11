// =============================================================
// MobileBottomNav — Role-Aware Mobile Touch Navigation (§27)
// Provides 5 essential mobile touch targets:
// Home | Primary Action | Trades | Market | More
// Includes safe-area spacing and active indicator.
// =============================================================

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingBag, ListChecks, Layers, Truck,
  TrendingUp, LineChart, HelpCircle, MoreHorizontal, Globe, LogOut, X
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useLanguage } from '../../hooks/useLanguage';

const getRoleHome = (role) => {
  if (role === 'buyer') return '/buyer/dashboard';
  if (role === 'fpo') return '/fpo/dashboard';
  return '/farmer/dashboard';
};

const formatRoleLabel = (role) => {
  if (!role) return 'Farmer';
  return role.charAt(0).toUpperCase() + role.slice(1);
};

export default function MobileBottomNav() {
  const { user, logout } = useAuth();
  const { t, language, changeLanguage } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  const pathname = location.pathname;
  const role = user?.role || 'farmer';
  const roleHome = getRoleHome(role);

  const [showMoreSheet, setShowMoreSheet] = useState(false);

  // Role-specific Primary Action definition
  const PRIMARY_ACTION_BY_ROLE = {
    farmer: { href: '/sell', label: t('sell') || 'Sell', icon: ShoppingBag },
    buyer: { href: '/buyer/dashboard', label: t('marketplace') || 'Market', icon: ListChecks },
    fpo: { href: '/sell', label: t('aggregate') || 'Intake', icon: Layers },
    transporter: { href: '/transactions', label: 'Jobs', icon: Truck },
    admin: { href: '/transactions', label: 'Orders', icon: TrendingUp },
  };

  const primaryAction = PRIMARY_ACTION_BY_ROLE[role] || PRIMARY_ACTION_BY_ROLE.farmer;
  const PrimaryIcon = primaryAction.icon;

  const isHomeActive = pathname === roleHome;
  const isActionActive = pathname === primaryAction.href.split('?')[0];
  const isTradesActive = pathname === '/transactions' || pathname.startsWith('/trades');
  const isMarketActive = pathname === '/prices' || pathname === '/map';
  const isHelpActive = pathname === '/grievances';

  const handleLogout = () => {
    setShowMoreSheet(false);
    logout();
    navigate('/');
  };

  return (
    <>
      <nav
        aria-label="Mobile Navigation"
        className="fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur-md border-t border-gray-200 lg:hidden shadow-lg pb-[env(safe-area-inset-bottom,0px)]"
      >
        <div className="grid grid-cols-5 h-14 max-w-md mx-auto">
          {/* 1. Home */}
          <Link
            to={roleHome}
            className={`flex flex-col items-center justify-center py-1 text-[11px] font-semibold transition ${
              isHomeActive
                ? 'text-emerald-700'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <LayoutDashboard className={`w-5 h-5 mb-0.5 ${isHomeActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
            <span className="truncate max-w-[60px]">{t('home') || 'Home'}</span>
          </Link>

          {/* 2. Primary Action */}
          <Link
            to={primaryAction.href}
            className={`flex flex-col items-center justify-center py-1 text-[11px] font-semibold transition ${
              isActionActive
                ? 'text-emerald-700'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <div className="relative">
              <PrimaryIcon className={`w-5 h-5 mb-0.5 ${isActionActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
            </div>
            <span className="truncate max-w-[60px]">{primaryAction.label}</span>
          </Link>

          {/* 3. Trades */}
          <Link
            to="/transactions"
            className={`flex flex-col items-center justify-center py-1 text-[11px] font-semibold transition ${
              isTradesActive
                ? 'text-emerald-700'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <TrendingUp className={`w-5 h-5 mb-0.5 ${isTradesActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
            <span className="truncate max-w-[60px]">{t('trades') || 'Trades'}</span>
          </Link>

          {/* 4. Market */}
          <Link
            to="/prices"
            className={`flex flex-col items-center justify-center py-1 text-[11px] font-semibold transition ${
              isMarketActive
                ? 'text-emerald-700'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <LineChart className={`w-5 h-5 mb-0.5 ${isMarketActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
            <span className="truncate max-w-[60px]">{t('market') || 'Market'}</span>
          </Link>

          {/* 5. More / Menu */}
          <button
            type="button"
            onClick={() => setShowMoreSheet(true)}
            className={`flex flex-col items-center justify-center py-1 text-[11px] font-semibold transition ${
              isHelpActive || showMoreSheet
                ? 'text-emerald-700'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            <MoreHorizontal className="w-5 h-5 mb-0.5 stroke-2" />
            <span className="truncate max-w-[60px]">{t('more') || 'More'}</span>
          </button>
        </div>
      </nav>

      {/* Mobile More Sheet / Drawer */}
      {showMoreSheet && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/50 lg:hidden animate-fade-in">
          <div
            className="fixed inset-0"
            onClick={() => setShowMoreSheet(false)}
            aria-hidden="true"
          />
          <div className="relative bg-white rounded-t-2xl p-5 space-y-4 shadow-2xl max-w-md mx-auto w-full z-10 pb-[calc(1.5rem+env(safe-area-inset-bottom,0px))]">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs uppercase">
                  {user?.name ? user.name.slice(0, 2) : 'KL'}
                </span>
                <div>
                  <p className="text-sm font-bold text-gray-900 leading-none">{user?.name || user?.full_name || 'KrishiLink User'}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{formatRoleLabel(role)}</p>
                </div>
              </div>
              <button
                type="button"
                aria-label="Close menu"
                onClick={() => setShowMoreSheet(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <Link
                to="/grievances"
                onClick={() => setShowMoreSheet(false)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 font-semibold text-gray-800 transition"
              >
                <HelpCircle className="w-4 h-4 text-emerald-600" />
                <span>{t('supportHelp') || 'Support & Help'}</span>
              </Link>
              <Link
                to="/map"
                onClick={() => setShowMoreSheet(false)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 font-semibold text-gray-800 transition"
              >
                <Globe className="w-4 h-4 text-amber-600" />
                <span>{t('marketMap') || 'Market Map'}</span>
              </Link>
              <Link
                to="/prices"
                onClick={() => setShowMoreSheet(false)}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 font-semibold text-gray-800 transition"
              >
                <LineChart className="w-4 h-4 text-blue-600" />
                <span>{t('mandiPrices') || 'Mandi Prices'}</span>
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-2.5 p-3 rounded-xl bg-red-50 hover:bg-red-100 font-semibold text-red-700 transition text-left"
              >
                <LogOut className="w-4 h-4 text-red-600" />
                <span>{t('logout') || 'Logout'}</span>
              </button>
            </div>

            <div className="pt-2 border-t border-gray-100 flex flex-col gap-2 text-xs">
              <span className="text-gray-500 font-medium">{t('language') || 'Language'}:</span>
              <div className="grid grid-cols-4 gap-1 bg-gray-100 p-1.5 rounded-lg text-center font-bold">
                <button
                  type="button"
                  onClick={() => changeLanguage('en')}
                  className={`py-1 rounded-md text-xs transition ${
                    language === 'en' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => changeLanguage('hi')}
                  className={`py-1 rounded-md text-xs transition ${
                    language === 'hi' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  हिन्दी
                </button>
                <button
                  type="button"
                  onClick={() => changeLanguage('mr')}
                  className={`py-1 rounded-md text-xs transition ${
                    language === 'mr' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  मराठी
                </button>
                <button
                  type="button"
                  onClick={() => changeLanguage('bn')}
                  className={`py-1 rounded-md text-xs transition ${
                    language === 'bn' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  বাংলা
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
