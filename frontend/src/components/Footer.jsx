import { Link } from 'react-router-dom';
import { Brand } from './Navbar';
import { useLanguage } from '../hooks/useLanguage';
export default function Footer(){const {t}=useLanguage();return <footer className="site-footer"><div className="site-container footer-top"><div><Brand/><p>{t('footerText')}</p></div><nav aria-label={t('help')}>{[['/about','about'],['/help','help'],['/terms','terms'],['/privacy','privacy']].map(([path,key])=><Link key={path} to={path}>{t(key)}</Link>)}</nav></div><div className="site-container footer-bottom"><span>© {new Date().getFullYear()} KrishiLink</span><span>{t('brandLine')}</span></div></footer>;}
