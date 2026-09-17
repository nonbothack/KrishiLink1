import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../hooks/useLanguage';
import { PageHeading, Notice } from '../components/Experience';
export default function InfoPage(){
 const {pathname}=useLocation();const {t}=useLanguage();const type=pathname.slice(1)||'help';
 if(type==='help')return <div className="site-container page-section"><PageHeading title={t('helpTitle')} description={t('helpIntro')}/><div className="help-grid">{[['checkPrices','step1Text','/prices'],['listCrop','step2Text','/sell'],['offers','step3Text','/offers'],['orders','paymentNote','/transactions']].map(([title,body,link])=><article className="panel help-guide" key={title}><h2>{t(title)}</h2><p>{t(body)}</p><Link className="text-link" to={link}>{t(title)} →</Link></article>)}</div><section id="account" className="panel legal-copy" style={{marginTop:24}}><h2>{t('accountHelp')}</h2><p>{t('accountHelpText')}</p><p>{t('supportAvailability')}</p><Link className="button" to="/grievances">{t('raiseIssue')}</Link></section></div>;
 if(type==='about')return <div className="site-container narrow page-section legal-copy"><PageHeading title={t('about')}/><p>{t('aboutText')}</p><Link className="text-link" to="/help">{t('help')}</Link></div>;
 if(type==='privacy'||type==='terms')return <div className="site-container narrow page-section legal-copy"><PageHeading title={t(type)}/><Notice>{t('policyStatus')}</Notice>{(type==='privacy'?['dataCollected','dataUse','deviceStorage','privacyContact']:['tradeTerms','priceTerms','paymentTerms']).map(key=><section key={key}><h2>{t(key)}</h2><p>{t(key+'Text')}</p></section>)}<Link className="text-link" to="/help">{t('help')}</Link></div>;
 return <div className="site-container narrow page-section"><PageHeading title={t('notFound')}/><Link className="button" to="/">{t('returnHome')}</Link><Link className="text-link" style={{marginLeft:20}} to="/prices">{t('prices')}</Link></div>;
}
