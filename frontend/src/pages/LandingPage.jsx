// =============================================================
// Landing Page
// The first page visitors see. Shows the product pitch.
// =============================================================

import { Link } from 'react-router-dom';
import {
  TrendingUp, Users, ShieldCheck,
  Truck, BarChart2, ArrowRight, CheckCircle2,
  Sprout, Star
} from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

// -------------------------------------------------------
// HERO SECTION
// -------------------------------------------------------
function Hero() {
  const { t } = useLanguage();
  return (
    <section className="bg-gradient-to-b from-green-900 to-green-800 text-white pt-12 pb-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column: Pitch & CTA */}
          <div className="lg:col-span-7 text-center lg:text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 text-sm font-medium mb-6">
              <Sprout className="w-4 h-4 text-green-300" />
              Smart India Hackathon 2026
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-5.5xl font-bold leading-tight mb-5 text-balance">
              {t('knowYourPrice')}<br />
              {t('findYourBuyer')}<br />
              <span className="text-green-300">{t('sellSmarter')}</span>
            </h1>

            <p className="text-base sm:text-lg text-green-100 max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
              {t('heroDescription')}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link to="/prices" className="btn-accent flex items-center gap-2 text-base w-full sm:w-auto justify-center">
                <BarChart2 className="w-5 h-5" />
                {t('exploreMarketPrices')}
              </Link>
              <Link to="/register" className="btn-secondary flex items-center gap-2 text-base w-full sm:w-auto justify-center">
                {t('getStartedFree')}
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mt-10 max-w-md mx-auto lg:mx-0 pt-6 border-t border-green-700/50">
              {[
                { value: '200+', label: t('marketsTracked') },
                { value: '8', label: t('majorCrops') },
                { value: '100%', label: t('transparent') },
              ].map(stat => (
                <div key={stat.label} className="text-center lg:text-left">
                  <div className="text-2xl font-bold text-green-300">{stat.value}</div>
                  <div className="text-xs text-green-200 mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Hero Visual Asset */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="relative w-full max-w-md lg:max-w-none">
              <div className="absolute -inset-1.5 bg-gradient-to-tr from-green-400/30 to-amber-300/30 rounded-3xl blur-md"></div>
              <div className="relative rounded-2xl overflow-hidden border border-white/20 shadow-2xl bg-green-950/40">
                <img
                  src="/images/hero-farmer.avif"
                  alt="Indian farmer in lush green agricultural field"
                  className="w-full h-72 sm:h-80 lg:h-96 object-cover object-center transform hover:scale-102 transition-transform duration-500"
                  loading="eager"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-end p-4">
                  <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-xs text-white">
                    <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                    <span>Empowering Indian Farmers</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------
// PROBLEM SECTION
// -------------------------------------------------------
function Problem() {
  const { t } = useLanguage();
  const problems = [
    {
      icon: '📊',
      title: t('priceUncertainty'),
      desc: t('priceUncertaintyDesc'),
    },
    {
      icon: '🤝',
      title: t('fragmentedBuyers'),
      desc: t('fragmentedBuyersDesc'),
    },
    {
      icon: '⚡',
      title: t('distressSales'),
      desc: t('distressSalesDesc'),
    },
    {
      icon: '📦',
      title: t('smallQuantities'),
      desc: t('smallQuantitiesDesc'),
    },
    {
      icon: '📄',
      title: t('verbalAgreements'),
      desc: t('verbalAgreementsDesc'),
    },
  ];

  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <span className="badge-red text-sm mb-3">{t('theProblem')}</span>
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mt-2">
            {t('challengesFarmersFace')}
          </h2>
          <p className="text-gray-500 mt-3 max-w-xl mx-auto">
            {t('problemDescription')}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
          {problems.map((p) => (
            <div key={p.title} className="card text-center hover:border-green-200 transition-all">
              <div className="text-4xl mb-3">{p.icon}</div>
              <h3 className="font-bold text-gray-800 mb-2">{p.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------
// SOLUTION SECTION
// -------------------------------------------------------
function Solution() {
  const { t } = useLanguage();
  const solutions = [
    {
      icon: BarChart2,
      color: 'bg-green-100 text-green-700',
      title: t('priceIntelligence'),
      desc: t('priceIntelligenceDesc'),
    },
    {
      icon: TrendingUp,
      color: 'bg-blue-100 text-blue-700',
      title: t('trendSignals'),
      desc: t('trendSignalsDesc'),
    },
    {
      icon: Users,
      color: 'bg-purple-100 text-purple-700',
      title: t('buyerMatching'),
      desc: t('buyerMatchingDesc'),
    },
    {
      icon: Truck,
      color: 'bg-orange-100 text-orange-700',
      title: t('logisticsStorage'),
      desc: t('logisticsStorageDesc'),
    },
    {
      icon: ShieldCheck,
      color: 'bg-teal-100 text-teal-700',
      title: t('transactionTrust'),
      desc: t('transactionTrustDesc'),
    },
  ];

  return (
    <section className="py-20 px-4 bg-[#FAFAF7]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <span className="badge-green text-sm mb-3">{t('theSolution')}</span>
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mt-2">
            {t('everythingFarmerNeeds')}
          </h2>
          <p className="text-gray-500 mt-3 max-w-xl mx-auto">
            {t('solutionDescription')}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
          {solutions.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.title} className="card-hover text-center">
                <div className={`w-12 h-12 ${s.color} rounded-xl flex items-center justify-center mx-auto mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-gray-800 mb-2">{s.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------
// HOW IT WORKS SECTION
// -------------------------------------------------------
function HowItWorks() {
  const { t } = useLanguage();
  const steps = [
    { step: '01', title: t('checkPrices'),     desc: t('checkPricesDesc') },
    { step: '02', title: t('listProduce'),     desc: t('listProduceDesc') },
    { step: '03', title: t('findBuyers'),      desc: t('findBuyersDesc') },
    { step: '04', title: t('receiveOffer'),    desc: t('receiveOfferDesc') },
    { step: '05', title: t('completeSale'),    desc: t('completeSaleDesc') },
  ];

  return (
    <section id="how-it-works" className="py-20 px-4 bg-white">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <span className="badge-blue text-sm mb-3">{t('howItWorksTitle')}</span>
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mt-2">
            {t('sellCropFiveSteps')}
          </h2>
        </div>

        <div className="relative">
          {/* Connector line (desktop only) */}
          <div className="hidden lg:block absolute top-10 left-[10%] right-[10%] h-0.5 bg-green-100 z-0" />

          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-6 relative z-10">
            {steps.map((s, i) => (
              <div key={s.step} className="text-center">
                <div className="w-16 h-16 bg-green-800 rounded-full flex items-center justify-center mx-auto mb-4 shadow-md">
                  <span className="text-white font-bold text-lg">{s.step}</span>
                </div>
                <h3 className="font-bold text-gray-800 mb-1">{s.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
                {i < steps.length - 1 && (
                  <div className="lg:hidden flex justify-center mt-4">
                    <ArrowRight className="w-5 h-5 text-green-300 rotate-90" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="text-center mt-10">
          <Link to="/login" className="btn-primary inline-flex items-center gap-2">
            {t('startYourJourney')}
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------
// TRUST SECTION
// -------------------------------------------------------
function TrustSection() {
  const { t } = useLanguage();
  const features = [
    { icon: ShieldCheck, title: t('verified'), desc: t('verifiedBuyersDesc') },
    { icon: CheckCircle2, title: t('transparent'), desc: t('transparentOffersDesc') },
    { icon: BarChart2, title: t('transactions'), desc: t('transactionHistoryDesc') },
    { icon: Star, title: t('grievances'), desc: t('grievanceSystemDesc') },
  ];

  return (
    <section className="py-20 px-4 bg-green-800 text-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-bold mb-3">
            {t('builtOnTrust')}
          </h2>
          <p className="text-green-200 max-w-xl mx-auto">
            {t('trustDescription')}
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="bg-white/10 rounded-2xl p-6 text-center border border-white/10">
                <Icon className="w-10 h-10 text-green-300 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">{f.title}</h3>
                <p className="text-green-200 text-sm leading-relaxed">{f.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="text-center mt-12">
          <Link to="/register" className="btn-accent inline-flex items-center gap-2 text-base">
            {t('joinKrishiLinkToday')}
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}

// -------------------------------------------------------
// MAIN LANDING PAGE
// -------------------------------------------------------
export default function LandingPage() {
  return (
    <div>
      <Hero />
      <Problem />
      <Solution />
      <HowItWorks />
      <TrustSection />
    </div>
  );
}
