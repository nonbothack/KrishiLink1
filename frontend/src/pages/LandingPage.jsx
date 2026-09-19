import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ArrowUpRight,
  Sprout,
  Store,
  Users,
  Search,
  ClipboardList,
  Handshake,
  ShieldCheck,
} from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';
import RateLookup from '../components/RateLookup';
import { usePageMetadata } from '../lib/metadata';
export default function LandingPage() {
  const { t } = useLanguage();
  usePageMetadata({ title: 'KrishiLink | Reported market prices and produce trading', description: 'Check dated agricultural market price reports, browse reviewed market records, list produce and review buyer offers.', path: '/' });
  return (
    <>
      <section className="hero-section">
        <div className="site-container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="tiny-leaf" /> {t('heroTag')}
            </p>
            <h1>
              {t('heroTitle')
                .split('\n')
                .map((line, i) => (
                  <span key={line} className={i ? 'accent-text' : ''}>
                    {line}
                  </span>
                ))}
            </h1>
            <p className="hero-description">{t('heroText')}</p>
            <div className="hero-buttons">
              <a href="#rates" className="button">
                {t('checkPrices')}
                <ArrowRight size={20} />
              </a>
              <Link to="/register?role=farmer&next=%2Fsell" className="button secondary">
                {t('listCrop')}
                <ArrowUpRight size={20} />
              </Link>
            </div>
            <p className="hero-footnote">
              <ShieldCheck size={17} />
              {t('noAccount')}
            </p>
          </div>
          <div className="hero-photo">
            <img
              src="/images/harvest-800.webp"
              srcSet="/images/harvest-480.webp 480w, /images/harvest-800.webp 800w"
              sizes="(max-width: 760px) 100vw, 48vw"
              width="800"
              height="800"
              fetchPriority="high"
              alt=""
            />
            <div className="photo-caption">
              <Sprout size={21} />
              <span>{t('brandLine')}</span>
            </div>
            <span className="photo-index" aria-hidden="true">
              01 / KRISHILINK
            </span>
          </div>
        </div>
      </section>
      <section id="rates" className="site-container rate-section" aria-labelledby="rate-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t('step1')}</p>
            <h2 id="rate-title">{t('checkPrices')}</h2>
          </div>
          <Link className="text-link" to="/prices">
            {t('prices')}
            <ArrowUpRight size={18} />
          </Link>
        </div>
        <RateLookup compact />
      </section>
      <section className="how-section" id="how-it-works" aria-labelledby="how-title">
        <div className="site-container">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{t('howItWorks')}</p>
              <h2 id="how-title">{t('howTitle')}</h2>
              <p className="muted">{t('howText')}</p>
            </div>
          </div>
          <div className="steps-grid">
            {[Search, ClipboardList, Handshake].map((Icon, i) => (
              <article className="step-card" key={i}>
                <div className="step-top">
                  <Icon size={26} />
                  <span>0{i + 1}</span>
                </div>
                <h3>{t('step' + (i + 1))}</h3>
                <p>{t('step' + (i + 1) + 'Text')}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
      <section className="site-container audience-section" aria-labelledby="audience-title">
        <div className="section-heading">
          <h2 id="audience-title">{t('together')}</h2>
        </div>
        <div className="audience-grid">
          {[
            ['farmer', Sprout],
            ['buyer', Store],
            ['fpo', Users],
          ].map(([role, Icon]) => (
            <Link className={'audience-card ' + role} to={'/register?role=' + role} key={role}>
              <Icon size={30} />
              <h3>{t(role + 'Role')}</h3>
              <p>{t(role + 'Benefit')}</p>
              <span className="text-link">
                {t('register')}
                <ArrowUpRight size={19} />
              </span>
            </Link>
          ))}
        </div>
      </section>
      <section className="site-container trust-section">
        <div className="trust-panel">
          <ShieldCheck size={34} />
          <div>
            <h2>{t('trustTitle')}</h2>
            <p>{t('trustText')}</p>
          </div>
          <Link className="button secondary" to="/help">
            {t('help')}
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>
      <section className="site-container public-faq-section" id="common-questions" aria-labelledby="faq-title">
        <div className="section-heading"><h2 id="faq-title">{t('publicFaqTitle')}</h2></div>
        <div className="public-faq-list">
          {[1, 2, 3, 4].map((number) => (
            <details className="panel public-faq-item" key={number}>
              <summary>{t(`publicFaqQuestion${number}`)}</summary>
              <p>{t(`publicFaqAnswer${number}`)}</p>
            </details>
          ))}
        </div>
      </section>
    </>
  );
}
