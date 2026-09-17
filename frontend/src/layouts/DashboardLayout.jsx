import { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Sprout, ChartColumn, FileText, Wallet, CircleHelp } from 'lucide-react';
import { Brand, LanguagePicker } from '../components/Navbar';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { dashboardFor } from '../lib/session';
export default function DashboardLayout({children}) {
 const {user,logout}=useAuth();const {t}=useLanguage();const navigate=useNavigate();const [offline,setOffline]=useState(!navigator.onLine);
 useEffect(()=>{const update=()=>setOffline(!navigator.onLine);window.addEventListener('online',update);window.addEventListener('offline',update);return()=>{window.removeEventListener('online',update);window.removeEventListener('offline',update);};},[]);
 const nav=[[dashboardFor(user.role),'dashboard',LayoutDashboard],['/prices','prices',ChartColumn],...(user.role!=='buyer'?[['/sell','listCrop',Sprout]]:[]),['/offers','offers',FileText],['/transactions','orders',Wallet],['/grievances','support',CircleHelp],['/help','help',CircleHelp]];
 const mobile=[nav[0],nav[1],nav.find(x=>x[0]==='/offers'),nav.find(x=>x[0]==='/transactions'),nav.find(x=>x[0]==='/help')];
 const links=(items)=>items.map(([path,label,Icon])=><NavLink key={path} to={path}><Icon size={21}/><span>{t(label)}</span></NavLink>);
 return <div className="app-shell"><aside className="app-sidebar"><Brand/><nav aria-label={t('menu')}>{links(nav)}</nav><button className="button secondary" onClick={()=>{logout();navigate('/');}}>{t('logout')}</button></aside><div className="app-content"><header className="app-header"><span className="mobile-brand"><Brand/></span><div className="user-label"><strong>{user.name}</strong><small>{t(user.role+'Role')}</small></div><LanguagePicker/><button className="text-link" onClick={()=>{logout();navigate('/');}}>{t('logout')}</button></header>{offline&&<div className="offline-strip" role="status">{t('offline')}</div>}<main id="main" className="app-main">{children||<Outlet/>}</main></div><nav className="app-mobile-nav" aria-label={t('menu')}>{links(mobile)}</nav></div>;
}
