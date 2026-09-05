// =============================================================
// Navbar Component
// Shows on all public pages. Has logo, nav links, login button.
// =============================================================

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, X, Sprout } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { isLoggedIn, user, logout } = useAuth();
  const { t, language, changeLanguage } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getDashboardLink = () => {
    if (user?.role === 'farmer') return '/farmer/dashboard';
    if (user?.role === 'buyer') return '/buyer/dashboard';
    if (user?.role === 'fpo') return '/fpo/dashboard';
    return '/';
  };

  const navLinks = [
    { label: t('home'), href: '/' },
    { label: t('howItWorks'), href: '/#how-it-works' },
    { label: t('marketPrices'), href: '/prices' },
    { label: t('map'), href: '/map' },
  ];

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 bg-green-800 rounded-xl flex items-center justify-center group-hover:bg-green-700 transition-colors">
              <Sprout className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-green-900">KrishiLink</span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map(link => (
              <Link
                key={link.href}
                to={link.href}
                className="text-gray-600 hover:text-green-800 font-medium transition-colors text-sm"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side: Language selector + Auth buttons */}
          <div className="hidden md:flex items-center gap-3">
            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => changeLanguage(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 cursor-pointer bg-white"
            >
              <option value="en">English</option>
              <option value="mr">मराठी</option>
              <option value="hi">हिंदी</option>
              <option value="bn">বাংলা</option>
              <option value="ta">தமிழ்</option>
              <option value="te">తెలుగు</option>
              <option value="kn">ಕನ್ನಡ</option>
            </select>

            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <Link
                  to={getDashboardLink()}
                  className="text-sm font-semibold text-green-800 hover:text-green-900"
                >
                  {user?.name?.split(' ')[0]}
                </Link>
                <button
                  onClick={handleLogout}
                  className="btn-secondary btn-sm text-sm"
                >
                  {t('logout')}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login" className="btn-secondary btn-sm text-sm">
                  {t('login')}
                </Link>
                <Link to="/register" className="btn-primary btn-sm text-sm">
                  {t('getStarted')}
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-4 py-4 space-y-3">
          {navLinks.map(link => (
            <Link
              key={link.href}
              to={link.href}
              onClick={() => setMenuOpen(false)}
              className="block py-2 text-gray-700 font-medium hover:text-green-800"
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
            {/* Language selector mobile */}
            <select
              value={language}
              onChange={(e) => changeLanguage(e.target.value)}
              className="input text-sm"
            >
              <option value="en">English</option>
              <option value="mr">मराठी</option>
              <option value="hi">हिंदी</option>
              <option value="bn">বাংলা</option>
              <option value="ta">தமிழ்</option>
              <option value="te">తెలుగు</option>
              <option value="kn">ಕನ್ನಡ</option>
            </select>
            {isLoggedIn ? (
              <>
                <Link
                  to={getDashboardLink()}
                  onClick={() => setMenuOpen(false)}
                  className="btn-primary w-full text-center"
                >
                  {t('dashboard') || 'My Dashboard'}
                </Link>
                <button onClick={handleLogout} className="btn-secondary w-full">
                  {t('logout')}
                </button>
              </>
            ) : (
              <>
                <Link to="/login" onClick={() => setMenuOpen(false)} className="btn-secondary w-full text-center">
                  {t('login')}
                </Link>
                <Link to="/register" onClick={() => setMenuOpen(false)} className="btn-primary w-full text-center">
                  {t('getStarted')}
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
