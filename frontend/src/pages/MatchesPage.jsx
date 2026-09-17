import { Link, useSearchParams } from 'react-router-dom';
import { getMatches } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { DataState, Notice, PageHeading, useResource } from '../components/Experience';
export default function MatchesPage(){
 const {t}=useLanguage();const [params]=useSearchParams();const lot=params.get('lot');const matches=useResource(()=>lot?getMatches({id:lot}):Promise.resolve({success:true,data:[]}),[lot]);
 return <><PageHeading title={t('findBuyers')} description={t('farmerBenefit')}/>{!lot&&<Link className="button" to="/farmer/dashboard">{t('listings')}</Link>}<DataState loading={matches.loading} error={matches.error} empty={!matches.data.length} onRetry={matches.retry}><div className="list-stack">{matches.data.map(m=><article className="panel" key={m.buyer_id}><h2>{m.buyer_name||t('buyerRole')}</h2><p className="muted">{t('status')}: {Math.round(m.score??m.final_score??0)} / 100</p></article>)}</div></DataState><Notice>{t('noOffers')}</Notice><Link className="button secondary" to="/offers">{t('offers')}</Link></>;
}
