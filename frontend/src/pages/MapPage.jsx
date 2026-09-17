import { useState } from 'react';
import { Link,useSearchParams } from 'react-router-dom';
import { MapContainer,TileLayer,CircleMarker,Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { apiCall } from '../services/api';
import { Field,DataState,PageHeading,useResource } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';
export default function MapPage(){
 const {t}=useLanguage();const [params]=useSearchParams();const [search,setSearch]=useState('');
 const markets=useResource(async()=>{const r=await apiCall('/api/v1/markets?limit=500');return {...r,data:r.data?.items||[]};});
 const visible=markets.data.filter(m=>(m.name+' '+m.district+' '+m.state).toLowerCase().includes(search.toLowerCase()));
 const located=visible.filter(m=>Number.isFinite(m.latitude)&&Number.isFinite(m.longitude));
 return <div className="site-container page-section"><PageHeading title={t('map')}/><Field label={t('search')} type="search" value={search} onChange={e=>setSearch(e.target.value)}/><DataState loading={markets.loading} error={markets.error} empty={!visible.length} onRetry={markets.retry}>{located.length>0&&<div style={{height:360,marginBlock:24,borderRadius:18,overflow:'hidden'}}><MapContainer center={[located[0].latitude,located[0].longitude]} zoom={7} style={{height:'100%',width:'100%'}} scrollWheelZoom={false}><TileLayer attribution='© OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>{located.map(m=><CircleMarker key={m.id} center={[m.latitude,m.longitude]} radius={7} pathOptions={{color:'#244b38'}}><Popup>{m.name}</Popup></CircleMarker>)}</MapContainer></div>}<div className="card-grid" style={{marginTop:24}}>{visible.map(m=><article className="panel" key={m.id}><h2>{m.name}</h2><p className="muted">{m.district} · {m.state}</p><Link className="text-link" to={'/prices?'+new URLSearchParams({market:m.name,crop:params.get('crop')||'Onion'})}>{t('checkPrices')} →</Link></article>)}</div></DataState></div>;
}
