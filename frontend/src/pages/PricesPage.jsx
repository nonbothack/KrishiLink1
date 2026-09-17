import RateLookup from '../components/RateLookup';
import { PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
export default function PricesPage(){const {t}=useLanguage();return <div className="site-container page-section"><PageHeading eyebrow="KRISHILINK" title={t('prices')} description={t('priceIntro')}/><RateLookup/></div>;}
