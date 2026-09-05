import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sprout, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';

const ROLES = [
  { value: 'farmer', label: 'Farmer', emoji: '🌾', desc: 'I grow crops and want to sell at better prices' },
  { value: 'buyer',  label: 'Buyer',  emoji: '🏪', desc: 'I want to buy produce directly from farmers' },
  { value: 'fpo',    label: 'FPO / Farmer Group', emoji: '🤝', desc: 'I represent a group of farmers' },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '', email: '', phone: '', password: '', role: 'farmer', location: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const getRoleLabel = (val) => {
    if (val === 'farmer') return t('farmer');
    if (val === 'buyer') return t('buyer');
    if (val === 'fpo') return t('fpo');
    return val;
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.role) {
      setError('Please select your role (Farmer, Buyer, or FPO).');
      return;
    }

    // Validate phone number format (must be 10 digits)
    const phoneClean = formData.phone.trim();
    if (!/^[0-9]{10}$/.test(phoneClean)) {
      setError('Please enter a valid 10-digit mobile number (e.g. 9876543210).');
      return;
    }

    // Validate email format if provided
    const emailClean = formData.email.trim();
    if (emailClean && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailClean)) {
      setError('Please enter a valid email address with a domain (e.g. yourname@gmail.com).');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    setError('');

    const result = await register({
      ...formData,
      phone: phoneClean,
      email: emailClean || null,
    });
    setLoading(false);

    if (result.success) {
      const role = result.user?.role || formData.role;
      if (role === 'buyer') navigate('/buyer/dashboard');
      else if (role === 'fpo') navigate('/fpo/dashboard');
      else navigate('/farmer/dashboard');
    } else {
      setError(result.message || 'Registration failed. Please check your details.');
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-green-800 rounded-xl flex items-center justify-center">
              <Sprout className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-green-900">KrishiLink</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{t('register')}</h1>
          <p className="text-gray-500 text-sm mt-1">Join KrishiLink to access better prices and verified buyers</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Role Selection */}
            <div>
              <label className="label">{t('role')} *</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {ROLES.map(r => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => handleChange('role', r.value)}
                    className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all text-center ${
                      formData.role === r.value
                        ? 'border-green-600 bg-green-50'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                  >
                    <span className="text-2xl mb-1">{r.emoji}</span>
                    <span className="font-semibold text-sm text-gray-800">{getRoleLabel(r.value)}</span>
                    <span className="text-xs text-gray-500 mt-1 leading-tight">{r.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="label">{t('name')} *</label>
                <input
                  className="input"
                  placeholder="e.g. Ramesh Patil"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="label">{t('phone')} *</label>
                <input
                  className="input"
                  placeholder="10-digit mobile number"
                  type="tel"
                  maxLength={10}
                  value={formData.phone}
                  onChange={(e) => handleChange('phone', e.target.value.replace(/\D/g, ''))}
                  required
                />
                <span className="text-[11px] text-gray-400 mt-0.5 block">e.g. 9876543210</span>
              </div>

              <div>
                <label className="label">{t('email')}</label>
                <input
                  className="input"
                  placeholder="e.g. name@gmail.com"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                />
                <span className="text-[11px] text-gray-400 mt-0.5 block">Include @ and .com</span>
              </div>

              <div className="sm:col-span-2">
                <label className="label">{t('location')} *</label>
                <input
                  className="input"
                  placeholder="e.g. Ratnagiri or Lasalgaon, Nashik"
                  value={formData.location}
                  onChange={(e) => handleChange('location', e.target.value)}
                  required
                />
              </div>

              <div className="sm:col-span-2">
                <label className="label">{t('password')} *</label>
                <input
                  className="input"
                  type="password"
                  placeholder="Minimum 6 characters"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  required
                  minLength={6}
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-red-800">Registration Notice</p>
                  <p className="text-red-700 mt-0.5">{error}</p>
                </div>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading ? (t('loading') || 'Creating account...') : t('register')}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            {t('alreadyHaveAccount') || 'Already have an account?'}{' '}
            <Link to="/login" className="text-green-700 font-semibold hover:underline">{t('login')}</Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          Your account credentials will be saved to the database.
        </p>
      </div>
    </div>
  );
}

