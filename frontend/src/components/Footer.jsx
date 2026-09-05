// =============================================================
// Footer Component
// =============================================================

import { Link } from 'react-router-dom';
import { Sprout, GitBranch, Mail } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="bg-green-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-white/20 rounded-xl flex items-center justify-center">
                <Sprout className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">KrishiLink</span>
            </div>

            <p className="text-green-200 text-sm leading-relaxed">
              {t('tagline')}
            </p>

            <p className="text-green-300 text-xs mt-3">
              Smart India Hackathon 2026 Project
            </p>
          </div>

          {/* Features */}
          <div>
            <h4 className="font-semibold mb-3 text-green-100">{t('features')}</h4>

            <ul className="space-y-2 text-sm text-green-300">
              <li>
                <Link
                  to="/prices"
                  className="hover:text-white transition-colors"
                >
                  {t('marketPrices')}
                </Link>
              </li>

              <li>
                <Link
                  to="/sell"
                  className="hover:text-white transition-colors"
                >
                  {t('sellProduce')}
                </Link>
              </li>

              <li>
                <Link
                  to="/matches"
                  className="hover:text-white transition-colors"
                >
                  {t('buyerMatching')}
                </Link>
              </li>

              <li>
                <Link
                  to="/map"
                  className="hover:text-white transition-colors"
                >
                  {t('map')}
                </Link>
              </li>

              <li>
                <Link
                  to="/transactions"
                  className="hover:text-white transition-colors"
                >
                  {t('transactions')}
                </Link>
              </li>
            </ul>
          </div>

          {/* About */}
          <div>
            <h4 className="font-semibold mb-3 text-green-100">{t('about')}</h4>

            <ul className="space-y-2 text-sm text-green-300">
              <li>
                <a
                  href="#how-it-works"
                  className="hover:text-white transition-colors"
                >
                  {t('howItWorks')}
                </a>
              </li>

              <li>
                <Link
                  to="/farmer/dashboard"
                  className="hover:text-white transition-colors"
                >
                  {t('farmer')}
                </Link>
              </li>

              <li>
                <Link
                  to="/buyer/dashboard"
                  className="hover:text-white transition-colors"
                >
                  {t('buyer')}
                </Link>
              </li>

              <li>
                <Link
                  to="/fpo/dashboard"
                  className="hover:text-white transition-colors"
                >
                  {t('fpo')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-3 text-green-100">Contact</h4>

            <div className="flex items-center gap-2 text-sm text-green-300 mb-2">
              <Mail className="w-4 h-4" />
              <span>team@krishilink.in</span>
            </div>

            <div className="flex items-center gap-2 text-sm text-green-300">
              <GitBranch className="w-4 h-4" />
              <span>github.com/krishilink</span>
            </div>
          </div>
        </div>

        <div className="border-t border-green-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-green-400">
          <p>© 2026 KrishiLink. {t('allRightsReserved')}</p>

          <p className="text-xs">
            Smart India Hackathon 2026 · Ministry of Agriculture &amp; Farmers Welfare
          </p>
        </div>
      </div>
    </footer>
  );
}