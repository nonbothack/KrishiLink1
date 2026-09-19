import { Link } from 'react-router-dom';
import { Brand, LanguagePicker } from './Navbar';
import { useLanguage } from '../hooks/useLanguage';

const groups = {
  product: [['prices', '/prices'], ['publicMandis', '/mandis'], ['map', '/map'], ['publicBuyers', '/buyers']],
  learn: [['howItWorks', '/how-it-works'], ['help', '/help'], ['publicAccuracyTitle', '/accuracy']],
  company: [['about', '/about'], ['publicContact', '/contact']],
  support: [['publicRaiseGrievance', '/login?next=%2Fgrievances'], ['privacy', '/privacy'], ['terms', '/terms'], ['publicRefundDraftTitle', '/refunds-and-cancellations'], ['publicGrievanceDraftTitle', '/grievance-policy'], ['publicSecurityTitle', '/security']],
};

export default function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="site-footer">
      <div className="site-container footer-top">
        <div className="footer-brand-column">
          <Brand />
          <p>{t('footerText')}</p>
        </div>
        {Object.entries(groups).map(([group, links]) => (
          <nav className="footer-link-group" aria-label={t(`footerGroup_${group}`)} key={group}>
            <h2>{t(`footerGroup_${group}`)}</h2>
            {links.map(([label, path]) => <Link key={path} to={path}>{t(label)}</Link>)}
          </nav>
        ))}
      </div>
      <div className="site-container footer-bottom">
        <span>© {new Date().getFullYear()} KrishiLink</span>
        <LanguagePicker />
        <span>{t('brandLine')}</span>
      </div>
    </footer>
  );
}
