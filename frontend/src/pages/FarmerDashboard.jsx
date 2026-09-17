import { Link } from 'react-router-dom';
import { Sprout, ChartColumn, FileText, Wallet, ArrowUpRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { getLots } from '../services/api';
import { DataState, PageHeading, useResource } from '../components/Experience';
export default function FarmerDashboard(){
 const {user}=useAuth();const {t,cropT,money,greeting}=useLanguage();const lots=useResource(()=>getLots(user.id),[user.id]);
 return <><PageHeading eyebrow={greeting} title={user.name}/><div className="quick-grid">{[['/sell','listCrop',Sprout],['/prices','checkPrices',ChartColumn],['/offers','offers',FileText],['/transactions','orders',Wallet]].map(([path,key,Icon])=><Link className="quick-card" key={path} to={path}><Icon size={26}/>{t(key)}</Link>)}</div><div className="section-heading"><h2>{t('listings')}</h2><button className="text-link" onClick={lots.retry}>{t('refresh')}</button></div><DataState loading={lots.loading} error={lots.error} empty={lots.data.length===0?t('noListings'):false} onRetry={lots.retry}><div className="list-stack">{lots.data.map(l=><article className="panel listing-row" key={l.id}><div><span className="status-pill">{t('status_'+l.status,l.status)}</span><h3>{cropT(l.crop)}</h3><p>{l.quantity} {t(l.unit||'quintal')} · {l.location}</p><p>{l.asking_price!=null?money(l.asking_price)+' / '+t(l.unit||'quintal'):'—'}</p></div><Link to={'/matches?lot='+l.id} className="button secondary">{t('findBuyers')}<ArrowUpRight size={18}/></Link></article>)}</div></DataState></>;
}
