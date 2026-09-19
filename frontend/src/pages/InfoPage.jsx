import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowUpRight, CircleHelp, ShieldCheck } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';
import { apiCall } from '../lib/http';
import { POLICY_CONTENT } from '../content/policies';
import { PageHeading, Notice } from '../components/Experience';
import { usePageMetadata } from '../lib/metadata';

const GUIDE_COPY = {
  prices: ['priceTerms', 'priceTermsText', '/prices'],
  sell: ['listCrop', 'sellIntro', '/register?role=farmer&next=%2Fsell'],
  offers: ['offers', 'tradeTermsText', '/login?next=%2Foffers'],
  support: ['support', 'supportAvailability', '/login?next=%2Fgrievances'],
};

const PAGE_METADATA = {
  help: ['Help for using KrishiLink', 'Task-based information about reported market prices, produce listings, offers and support.'],
  'how-it-works': ['How KrishiLink works', 'A simple guide to checking reported prices, listing produce and reviewing offers.'],
  about: ['About KrishiLink', 'Learn what KrishiLink currently helps farmers, buyers and farmer groups do.'],
  contact: ['Contact and support | KrishiLink', 'See the support channels configured for KrishiLink and the available grievance workflow.'],
  terms: ['Terms of service draft | KrishiLink', 'Draft service terms pending legal review. Not approved for production use.'],
  privacy: ['Privacy notice draft | KrishiLink', 'Draft privacy notice pending legal review. Not approved for production use.'],
  'refunds-and-cancellations': ['Refunds and cancellations draft | KrishiLink', 'Draft refund and cancellation policy pending legal review.'],
  'grievance-policy': ['Grievance policy draft | KrishiLink', 'Draft grievance information pending legal review and operating contact details.'],
  accuracy: ['Evidence and published measurements | KrishiLink', 'No forecast accuracy or platform outcome statistics are published without a validated evidence set.'],
  security: ['Security and data handling | KrishiLink', 'A factual overview of account safeguards and current security limitations.'],
  '404': ['Page not found | KrishiLink', 'This address does not match a public KrishiLink page.'],
};
const GUIDE_METADATA = {
  prices: ['How to read reported market prices | KrishiLink', 'Learn how crop, market, report date, source and unit describe an official daily reported price.'],
  sell: ['How to list produce | KrishiLink', 'Review crop, quantity, location and asking price before publishing a produce lot.'],
  offers: ['How to review buyer offers | KrishiLink', 'Check an offer’s quantity, unit, price and terms before accepting or countering.'],
  support: ['How to reach support | KrishiLink', 'Sign in to raise or track a support request. Public contact details appear only when configured.'],
};

function configuredSupport() {
  const rawPhone = String(import.meta.env.VITE_PUBLIC_SUPPORT_PHONE || '').trim();
  const phone = /^[+0-9() .-]{7,24}$/.test(rawPhone) ? rawPhone : '';
  const rawEmail = String(import.meta.env.VITE_PUBLIC_SUPPORT_EMAIL || '').trim();
  const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(rawEmail) ? rawEmail : '';
  return { phone, email };
}

export default function InfoPage() {
  const location = useLocation();
  const { t, language } = useLanguage();
  const type = location.pathname.split('/').filter(Boolean)[0] || 'help';
  const slug = location.pathname.split('/').filter(Boolean)[1] || '';
  const [policyVersions, setPolicyVersions] = useState({});
  const support = useMemo(configuredSupport, []);
  const policyPage = type === 'terms' || type === 'privacy';
  const policyType = type === 'privacy' ? 'privacy_notice' : 'terms';
  const unavailableRoute = !Object.hasOwn(PAGE_METADATA, type) || (type === 'help' && Boolean(slug) && !Object.hasOwn(GUIDE_COPY, slug));

  useEffect(() => {
    if (!policyPage) return;
    apiCall('/api/v1/privacy/policies/current', { auth: false }).then((res) => {
      if (res.success) setPolicyVersions(res.data || {});
    });
  }, [policyPage, type]);

  const metadata = type === 'help' && slug && GUIDE_METADATA[slug] ? GUIDE_METADATA[slug] : PAGE_METADATA[type] || PAGE_METADATA['404'];
  usePageMetadata({ title: metadata[0], description: metadata[1], path: location.pathname, noindex: unavailableRoute || policyPage || ['refunds-and-cancellations', 'grievance-policy', 'security', '404'].includes(type) || (type === 'contact' && !support.phone && !support.email) });

  if (type === 'help' && slug) {
    const guide = GUIDE_COPY[slug];
    if (!guide) return <NotFound t={t} />;
    return (
      <div className="site-container narrow page-section public-info-page">
        <PageHeading eyebrow={t('helpTitle')} title={t(guide[0])} description={t(guide[1])} />
        <Link className="button" to={guide[2]}>{t(slug === 'support' ? 'publicRaiseGrievance' : slug === 'sell' ? 'listCrop' : slug === 'offers' ? 'offers' : 'publicTryPrices')}<ArrowUpRight size={17} /></Link>
        <p className="muted">{t('publicAvailabilityNote')}</p>
      </div>
    );
  }

  if (type === 'help') {
    return (
      <div className="site-container page-section public-info-page">
        <PageHeading title={t('helpTitle')} description={t('helpIntro')} />
        <div className="card-grid help-grid">
          {[
            ['prices', 'priceTerms', 'priceTermsText', '/help/prices'],
            ['sell', 'listCrop', 'sellIntro', '/help/sell'],
            ['offers', 'offers', 'tradeTermsText', '/help/offers'],
            ['support', 'support', 'supportAvailability', '/help/support'],
          ].map(([key, title, body, href]) => (
            <article className="panel help-guide" key={key}>
              <CircleHelp size={22} aria-hidden="true" />
              <h2>{t(title)}</h2>
              <p>{t(body)}</p>
              <Link className="text-link" to={href}>{t('publicReadMore')}<ArrowUpRight size={16} /></Link>
            </article>
          ))}
        </div>
        <section className="panel public-support-panel">
          <h2>{t('publicContactTitle')}</h2>
          <p>{t('supportAvailability')}</p>
          <Link className="button" to="/login?next=%2Fgrievances">{t('publicRaiseGrievance')}</Link>
        </section>
      </div>
    );
  }

  if (type === 'how-it-works') {
    return (
      <div className="site-container page-section public-info-page">
        <PageHeading title={t('howTitle')} description={t('howText')} />
        <div className="steps-grid">
          {[1, 2, 3].map((step) => (
            <article className="step-card" key={step}>
              <div className="step-top"><span>0{step}</span></div>
              <h2>{t(`step${step}`)}</h2>
              <p>{t(`step${step}Text`)}</p>
              {step === 1 && <Link className="text-link" to="/prices">{t('publicTryPrices')}<ArrowUpRight size={16} /></Link>}
            </article>
          ))}
        </div>
        <p className="muted">{t('publicAvailabilityNote')}</p>
      </div>
    );
  }

  if (type === 'about') {
    return (
      <div className="site-container narrow page-section public-info-page">
        <PageHeading title={t('about')} />
        <p>{t('aboutText')}</p>
        <p className="muted">{t('publicAvailabilityNote')}</p>
        <Link className="text-link" to="/help">{t('help')}</Link>
      </div>
    );
  }

  if (type === 'contact') {
    return (
      <div className="site-container narrow page-section public-info-page">
        <PageHeading title={t('publicContactTitle')} description={t('publicContactIntro')} />
        {support.phone || support.email ? (
          <section className="panel public-contact-card">
            {support.phone && <p><strong>{t('phone')}:</strong> <a href={`tel:${support.phone.replace(/[^+\d]/g, '')}`}>{support.phone}</a></p>}
            {support.email && <p><strong>{t('email')}:</strong> <a href={`mailto:${support.email}`}>{support.email}</a></p>}
          </section>
        ) : <Notice>{t('publicContactUnavailable')}</Notice>}
        <section className="panel public-support-panel">
          <h2>{t('support')}</h2>
          <p>{t('supportAvailability')}</p>
          <Link className="button" to="/login?next=%2Fgrievances">{t('publicRaiseGrievance')}</Link>
        </section>
      </div>
    );
  }

  if (type === 'terms' || type === 'privacy') {
    const document = POLICY_CONTENT[type][language] || POLICY_CONTENT[type].en;
    const metadata = policyVersions[policyType] || {};
    return (
      <div className="site-container narrow page-section legal-copy policy-document public-info-page">
        <PageHeading title={document.title} description={document.draft} />
        <Notice className="policy-draft-notice">{t('policyDraft')}</Notice>
        <dl className="policy-metadata">
          <div><dt>{t('policyVersion')}</dt><dd>{metadata.version || (type === 'privacy' ? 'privacy-2026-09-17-draft.1' : 'terms-2026-09-17-draft.1')}</dd></div>
          <div><dt>{t('effectiveDate')}</dt><dd>{metadata.effective_date || t('pendingLegal')}</dd></div>
        </dl>
        {document.sections.map(([title, body]) => <section key={title}><h2>{title}</h2><p>{body}</p></section>)}
        <p className="policy-draft-copy">{t('publicLegalDraftBody')}</p>
      </div>
    );
  }

  if (['refunds-and-cancellations', 'grievance-policy'].includes(type)) {
    return (
      <div className="site-container narrow page-section public-info-page">
        <PageHeading title={type === 'grievance-policy' ? t('publicGrievanceDraftTitle') : t('publicRefundDraftTitle')} />
        <Notice>{t('policyDraft')}</Notice>
        <p>{t('publicLegalDraftBody')}</p>
        <p>{t('supportAvailability')}</p>
        <Link className="button" to="/login?next=%2Fgrievances">{t('publicRaiseGrievance')}</Link>
      </div>
    );
  }

  if (type === 'accuracy') {
    return <div className="site-container narrow page-section public-info-page"><PageHeading title={t('publicAccuracyTitle')} description={t('publicAccuracyIntro')} /><p>{t('publicAccuracyIntro')}</p></div>;
  }

  if (type === 'security') {
    return <div className="site-container narrow page-section public-info-page"><PageHeading title={t('publicSecurityTitle')} description={t('publicSecurityIntro')} /><section className="panel public-security-card"><ShieldCheck size={24} aria-hidden="true" /><p>{t('publicSecurityIntro')}</p><Link className="text-link" to="/privacy">{t('privacy')}</Link></section></div>;
  }

  return <NotFound t={t} />;
}

function NotFound({ t }) {
  return (
    <div className="site-container narrow page-section public-info-page">
      <PageHeading title={t('public404Title')} description={t('public404Body')} />
      <div className="public-not-found-actions"><Link className="button" to="/prices">{t('publicTryPrices')}</Link><Link className="text-link" to="/">{t('returnHome')}</Link></div>
    </div>
  );
}
