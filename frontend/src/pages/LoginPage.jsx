// =============================================================
// Login Page
// Has demo login buttons + real login form
// =============================================================

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sprout, Tractor, ShoppingBag, Building2, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';

export default function LoginPage() {
  const { login, demoLogin } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDemoLogin = (role) => {
    demoLogin(role);
    if (role === 'farmer') navigate('/farmer/dashboard');
    else if (role === 'buyer') navigate('/buyer/dashboard');
    else if (role === 'fpo') navigate('/fpo/dashboard');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const result = await login(email, password);
    setLoading(false);
    if (result.success) {
      // Redirect based on the role returned by the API
      const role = result.user?.role;
      if (role === 'buyer') navigate('/buyer/dashboard');
      else if (role === 'fpo') navigate('/fpo/dashboard');
      else navigate('/farmer/dashboard');
    } else {
      setError(result.message || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-green-800 rounded-xl flex items-center justify-center">
              <Sprout className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-green-900">KrishiLink</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{t('welcomeBack') || 'Welcome back'}</h1>
          <p className="text-gray-500 text-sm mt-1">{t('loginToYourAccount') || 'Login to your account'}</p>
        </div>

        {/* Demo Login Box */}
        <div className="card mb-6 border-2 border-amber-200 bg-amber-50">
          <div className="flex items-center gap-2 mb-4">
            <span className="badge-yellow">{t('demoMode')}</span>
            <p className="text-sm text-amber-700">{t('tryWithoutAccount') || 'Try without creating an account'}</p>
          </div>
          <div className="grid grid-cols-1 gap-2">
            <button
              onClick={() => handleDemoLogin('farmer')}
              className="flex items-center gap-3 w-full bg-green-800 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-xl transition-all"
            >
              <Tractor className="w-5 h-5" />
              <div className="text-left">
                <div className="text-sm">{t('continueAsFarmer')}</div>
                <div className="text-green-200 text-xs">Ramesh Patil, Lasalgaon</div>
              </div>
            </button>
            <button
              onClick={() => handleDemoLogin('buyer')}
              className="flex items-center gap-3 w-full bg-blue-700 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-xl transition-all"
            >
              <ShoppingBag className="w-5 h-5" />
              <div className="text-left">
                <div className="text-sm">{t('continueAsBuyer')}</div>
                <div className="text-blue-200 text-xs">Mehta Traders, Nashik</div>
              </div>
            </button>
            <button
              onClick={() => handleDemoLogin('fpo')}
              className="flex items-center gap-3 w-full bg-purple-700 hover:bg-purple-600 text-white font-semibold py-3 px-4 rounded-xl transition-all"
            >
              <Building2 className="w-5 h-5" />
              <div className="text-left">
                <div className="text-sm">{t('continueAsFPO')}</div>
                <div className="text-purple-200 text-xs">Nashik Farmer Collective FPO</div>
              </div>
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-[#FAFAF7] px-4 text-sm text-gray-400">{t('orLoginWithAccount') || 'or login with account'}</span>
          </div>
        </div>

        {/* Real login form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">{t('emailOrPhone') || 'Email or Phone'}</label>
              <input
                type="text"
                className="input"
                placeholder="yourname@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label">{t('password') || 'Password'}</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  className="input pr-12"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (t('loading') || 'Logging in...') : (t('login') || 'Login')}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            {t('dontHaveAccount') || "Don't have an account?"}{' '}
            <Link to="/register" className="text-green-700 font-semibold hover:underline">
              {t('signUp') || 'Sign Up'}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
