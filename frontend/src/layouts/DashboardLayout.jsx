// =============================================================
// Dashboard Layout (Farmer, Buyer, FPO)
// Sidebar navigation + Top bar with user profile & live notifications
// =============================================================

import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Sprout, LayoutDashboard, ShoppingBag, ArrowLeftRight,
  TrendingUp, FileText, AlertCircle, LogOut,
  Menu, Bell, CheckCheck
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api';


function SidebarContent({ user, navItems, location, setSidebarOpen, handleLogout, t, mobile = false }) {
  return (
    <div className={`flex flex-col h-full ${mobile ? 'w-full' : 'w-64'}`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-green-700/50">
        <div className="w-9 h-9 bg-white/15 rounded-xl flex items-center justify-center shadow-inner">
          <Sprout className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="text-white font-bold text-lg leading-none">KrishiLink</span>
          <p className="text-green-300 text-[10px] font-medium tracking-wide mt-0.5">Agri Marketplace</p>
        </div>
      </div>

      {/* User info */}
      <div className="px-4 py-4 border-b border-green-700/50">
        <div className="flex items-center gap-3 bg-white/10 rounded-xl px-3 py-2.5">
          <div className="w-9 h-9 bg-gradient-to-br from-green-300 to-green-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
            <span className="text-green-900 font-bold text-sm">
              {(user?.name || user?.full_name || 'U')[0]}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-white font-semibold text-sm truncate leading-tight">{user?.name || user?.full_name || 'User'}</p>
            <span className="inline-block bg-green-600/40 text-green-200 text-[10px] font-bold px-1.5 py-0.5 rounded-full capitalize mt-0.5">
              {user?.role || 'Member'}
            </span>
          </div>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href + item.label}
              to={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-white text-green-800 shadow-sm'
                  : 'text-green-100 hover:bg-white/10 hover:text-white'
              }`}
            >
              <Icon className={`w-4.5 h-4.5 flex-shrink-0 ${isActive ? 'text-green-700' : 'text-green-300 group-hover:text-white'}`} />
              <span className="flex-1">{item.label}</span>
              {isActive && <div className="w-1.5 h-1.5 bg-green-600 rounded-full" />}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-green-700/50">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-green-200 hover:bg-white/10 hover:text-white text-sm font-medium transition-all"
        >
          <LogOut className="w-4.5 h-4.5" />
          {t('logout') || 'Logout'}
        </button>
      </div>
    </div>
  );
}

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const { user, logout } = useAuth();
  const { t, language, changeLanguage } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const farmerNav = [
    { href: '/farmer/dashboard', label: t('dashboard') || 'Dashboard', icon: LayoutDashboard },
    { href: '/sell',             label: t('listProduce') || 'List Produce', icon: ShoppingBag },
    { href: '/matches',          label: t('findBuyers') || 'Find Buyers', icon: ArrowLeftRight },
    { href: '/offers',           label: t('offers') || 'Offers', icon: FileText },
    { href: '/transactions',     label: t('transactions') || 'Orders', icon: TrendingUp },
    { href: '/grievances',       label: t('grievances') || 'Support & Help', icon: AlertCircle },
  ];

  const buyerNav = [
    { href: '/buyer/dashboard',  label: t('marketplace') || 'Marketplace', icon: ShoppingBag },
    { href: '/offers',           label: t('myOffers') || 'My Offers', icon: FileText },
    { href: '/transactions',     label: t('myOrders') || 'My Orders', icon: TrendingUp },
    { href: '/grievances',       label: t('grievances') || 'Support & Help', icon: AlertCircle },
  ];

  const fpoNav = [
    { href: '/fpo/dashboard',    label: t('dashboard') || 'Dashboard', icon: LayoutDashboard },
    { href: '/sell',             label: t('aggregateLot') || 'Aggregate Lot', icon: ShoppingBag },
    { href: '/matches',          label: t('findBuyers') || 'Find Buyers', icon: ArrowLeftRight },
    { href: '/offers',           label: t('offers') || 'Offers', icon: FileText },
    { href: '/transactions',     label: t('transactions') || 'Transactions', icon: TrendingUp },
    { href: '/grievances',       label: t('grievances') || 'Support & Help', icon: AlertCircle },
  ];

  const navItems = user?.role === 'buyer' ? buyerNav
    : user?.role === 'fpo' ? fpoNav
    : farmerNav;

  const fetchNotifs = async () => {
    try {
      const res = await getNotifications();
      if (res && res.success && Array.isArray(res.data)) {
        setNotifications(res.data);
      }
    } catch {
      // Ignore network errors in polling
    }
  };

  useEffect(() => {
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 15000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleMarkRead = async (id) => {
    await markNotificationRead(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#FAFAF7] flex">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex flex-col w-64 bg-gradient-to-b from-green-900 to-green-800 fixed top-0 left-0 h-screen z-30 shadow-xl">
        <SidebarContent
          user={user}
          navItems={navItems}
          location={location}
          setSidebarOpen={setSidebarOpen}
          handleLogout={handleLogout}
          t={t}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div className={`fixed top-0 left-0 h-screen w-72 bg-gradient-to-b from-green-900 to-green-800 z-50 transition-transform duration-300 lg:hidden shadow-2xl ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <SidebarContent
          user={user}
          navItems={navItems}
          location={location}
          setSidebarOpen={setSidebarOpen}
          handleLogout={handleLogout}
          t={t}
          mobile
        />
      </div>

      {/* Main content area */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-100 sticky top-0 z-20 shadow-sm">
          <div className="flex items-center justify-between px-4 lg:px-6 py-3">
            {/* Mobile menu toggle */}
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5 text-gray-600" />
            </button>

            {/* Page info — desktop */}
            <div className="hidden lg:flex items-center gap-3">
              <div className="h-5 w-0.5 bg-green-200 rounded-full" />
              <div>
                <p className="text-sm font-semibold text-gray-800">
                  {t('welcomeBack') || 'Welcome back'}, <span className="text-green-700">{(user?.name || user?.full_name || 'Farmer').split(' ')[0]}</span>
                </p>
                <p className="text-xs text-gray-400">
                  {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
                </p>
              </div>
            </div>

            {/* Right: Language Selector + Notifications */}
            <div className="flex items-center gap-3 ml-auto">
              <select
                value={language}
                onChange={(e) => changeLanguage(e.target.value)}
                className="text-xs sm:text-sm border border-gray-200 rounded-xl px-2.5 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500 cursor-pointer bg-white shadow-2xs font-medium"
                aria-label="Change language"
              >
                <option value="en">English</option>
                <option value="mr">मराठी</option>
                <option value="hi">हिंदी</option>
                <option value="bn">বাংলা</option>
                <option value="ta">தமிழ்</option>
                <option value="te">తెలుగు</option>
                <option value="kn">ಕನ್ನಡ</option>
              </select>

              <div className="relative">
                <button
                  onClick={() => setNotifOpen(!notifOpen)}
                  className="relative p-2 rounded-xl hover:bg-gray-100 transition-colors"
                  aria-label="View notifications"
                >
                  <Bell className="w-5 h-5 text-gray-600" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

              {/* Notification dropdown */}
              {notifOpen && (
                <div className="absolute right-0 top-12 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                    <span className="font-bold text-gray-800 text-sm">Notifications</span>
                    {unreadCount > 0 ? (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-xs text-green-700 font-semibold hover:underline flex items-center gap-1"
                      >
                        <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">All caught up</span>
                    )}
                  </div>
                  <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-6 text-center text-gray-400 text-xs">
                        No notifications yet.
                      </div>
                    ) : (
                      notifications.map(n => (
                        <div
                          key={n.id}
                          onClick={() => handleMarkRead(n.id)}
                          className={`px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer ${!n.is_read ? 'bg-green-50/60' : ''}`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-semibold text-xs text-gray-800 leading-snug">{n.title}</p>
                            {!n.is_read && <span className="w-2 h-2 rounded-full bg-green-600 flex-shrink-0 mt-1" />}
                          </div>
                          <p className="text-xs text-gray-600 mt-1 leading-relaxed">{n.message}</p>
                          {n.created_at && (
                            <span className="text-[10px] text-gray-400 mt-1.5 block">
                              {new Date(n.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-6 xl:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
