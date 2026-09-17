import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { MapPin, ArrowUpRight, RefreshCw } from 'lucide-react';
import { getLivePrices } from '../services/api';
import { useLanguage } from '../hooks/useLanguage';
import { Field, DataState, useResource } from './Experience';
import { CROPS, dateLabel } from '../lib/produce';
export default function RateLookup({compact=false}) {
 const {t,cropT,money,language}=useLanguage(); const [params,setParams]=useSearchParams();
 const [choice,setChoice]=useState(()=>{try{return JSON.parse(localStorage.getItem('krishilink_price_choice'))||{crop:'Onion',district:''};}catch{return {crop:'Onion',district:''};}});
 const crop=compact?choice.crop:(params.get('crop')||'Onion');
 const district=compact?choice.district:(params.get('district')||'');
 const market=compact?'':(params.get('market')||'');
 const state=compact?'':(params.get('state')||'');
 const page=compact?1:Math.max(1,Number(params.get('page'))||1);
 const [draftDistrict,setDraftDistrict]=useState(district);
 useEffect(()=>{setDraftDistrict(district);},[district]);
 const resource=useResource(()=>getLivePrices({crop,district,market,state,page,limit:compact?3:12}),[crop,district,market,state,page,compact]);
 function update(values){if(compact){const next={...choice,...values};setChoice(next);localStorage.setItem('krishilink_price_choice',JSON.stringify(next));}else{const next=new URLSearchParams(params);Object.entries(values).forEach(([k,v])=>v?next.set(k,v):next.delete(k));next.delete('page');setParams(next);}}
 return <div className="rate-lookup"><form className="rate-filters" onSubmit={e=>{e.preventDefault();update({district:draftDistrict.trim()});}}><Field label={t('crop')} as="select" value={crop} onChange={e=>update({crop:e.target.value})}>{[...new Set([...CROPS,crop])].map(c=><option key={c} value={c}>{cropT(c)}</option>)}</Field><Field label={t('district')} value={draftDistrict} onChange={e=>setDraftDistrict(e.target.value)} placeholder={t('all')} autoComplete="address-level2"/><button className="button" type="submit">{t('search')}<ArrowUpRight size={18}/></button><button className="icon-button" type="button" aria-label={t('refresh')} onClick={resource.retry}><RefreshCw size={20}/></button></form>
 <DataState loading={resource.loading} error={resource.error} empty={resource.data.length===0?t('rateEmpty'):false} onRetry={resource.retry}><div className="price-grid">{resource.data.map((p,i)=><article className="price-result" key={p.id||i}><div className="price-top"><span className="crop-dot"/><strong>{cropT(p.crop||p.commodity)}</strong></div><div className="price-number">{p.modal_price!=null?money(p.modal_price):'—'}</div><p className="unit-label">{t('perQuintal')}</p><p className="market-line"><MapPin size={16}/>{p.market}{p.district?' · '+p.district:''}</p><p className="date-line">{t('reportedOn')}: {dateLabel(p.price_date||p.arrival_date,language)||t('noDate')}</p><Link className="text-link" to={'/sell?'+new URLSearchParams({crop:p.crop||p.commodity,price:p.modal_price||'',market:p.market||'',district:p.district||'',unit:'quintal'})}>{t('listCrop')}<ArrowUpRight size={18}/></Link></article>)}</div></DataState>
 <p className="rate-disclaimer">{t('referenceOnly')}</p>{!compact && resource.pages>1 && <div className="pagination"><button className="button secondary" disabled={page<=1} onClick={()=>{const n=new URLSearchParams(params);n.set('page',page-1);setParams(n);}}>{t('previous')}</button><span>{page} / {resource.pages}</span><button className="button secondary" disabled={page>=resource.pages} onClick={()=>{const n=new URLSearchParams(params);n.set('page',page+1);setParams(n);}}>{t('next')}</button></div>}
 </div>;
}
