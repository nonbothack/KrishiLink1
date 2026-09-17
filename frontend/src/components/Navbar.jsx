import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Sprout, Menu, X, ArrowUpRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { dashboardFor } from '../lib/session';
export function LanguagePicker() {
  const {language,changeLanguage,t}=useLanguage();
  return <select className="language-picker" aria-label={t('language')} value={language} onChange={e=>changeLanguage(e.target.value)}><option value="en">English</option><option value="mr">मराठी</option><option value="hi">हिंदी</option></select>;
}
export function Brand() {return <Link className="brand" to="/" aria-label="KrishiLink"><span className="brand-icon"><Sprout size={25}/></span><span>Krishi<span className="brand-light">Link</span><small>GROW. CONNECT. THRIVE.</small></span></Link>;}
export default function Navbar() {
  const [open,setOpen]=useState(false); const {isLoggedIn,user}=useAuth(); const {t}=useLanguage();
  return <header className="site-header"><a className="skip-link" href="#main">{t('skip')}</a><div className="site-container header-inner"><Brand/><nav className="desktop-nav" aria-label={t('menu')}><NavLink to="/prices">{t('prices')}</NavLink><Link to="/#how-it-works">{t('howItWorks')}</Link><NavLink to="/help">{t('help')}</NavLink></nav><div className="header-actions"><LanguagePicker/><Link className="button small secondary desktop-auth" to={isLoggedIn?dashboardFor(user.role):'/login'}>{t(isLoggedIn?'dashboard':'login')}<ArrowUpRight size={17}/></Link><button className="icon-button menu-toggle" aria-label={t('menu')} aria-expanded={open} aria-controls="mobile-menu" onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button></div></div>{open && <nav id="mobile-menu" className="mobile-menu" aria-label={t('menu')}>{[['/prices','prices'],['/#how-it-works','howItWorks'],['/help','help'],[isLoggedIn?dashboardFor(user.role):'/login',isLoggedIn?'dashboard':'login']].map(([path,label])=><Link onClick={()=>setOpen(false)} key={path} to={path}>{t(label)}</Link>)}</nav>}</header>;
}
