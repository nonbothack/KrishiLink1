import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { LanguageProvider,useLanguage } from './hooks/useLanguage';
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';
import LandingPage from './pages/LandingPage';
import ErrorBoundary from './components/ErrorBoundary';
import { DataState } from './components/Experience';
import { dashboardFor } from './lib/session';
const LoginPage=lazy(()=>import('./pages/LoginPage'));
const RegisterPage=lazy(()=>import('./pages/RegisterPage'));
const PricesPage=lazy(()=>import('./pages/PricesPage'));
const InfoPage=lazy(()=>import('./pages/InfoPage'));
const MapPage=lazy(()=>import('./pages/MapPage'));
const FarmerDashboard=lazy(()=>import('./pages/FarmerDashboard'));
const BuyerDashboard=lazy(()=>import('./pages/BuyerDashboard'));
const FPODashboard=lazy(()=>import('./pages/FPODashboard'));
const SellPage=lazy(()=>import('./pages/SellPage'));
const OffersPage=lazy(()=>import('./pages/OffersPage'));
const MatchesPage=lazy(()=>import('./pages/MatchesPage'));
const TransactionsPage=lazy(()=>import('./pages/TransactionsPage'));
const GrievancesPage=lazy(()=>import('./pages/GrievancesPage'));
export function ProtectedRoute({roles,children}){
 const {user,loading}=useAuth();const location=useLocation();
 if(loading)return <DataState loading/>;
 if(!user)return <Navigate replace to={'/login?'+new URLSearchParams({next:location.pathname+location.search})} state={{from:location}}/>;
 if(roles&&!roles.includes(user.role))return <Navigate replace to={dashboardFor(user.role)}/>;
 return children;
}
function RouteContent(){
 const location=useLocation();const {t}=useLanguage();
 useEffect(()=>{if(location.hash){requestAnimationFrame(()=>document.getElementById(location.hash.slice(1))?.scrollIntoView());}else window.scrollTo(0,0);},[location.pathname,location.hash]);
 return <ErrorBoundary resetKey={location.pathname} title={t('server')} retry={t('retry')} home={t('returnHome')}><Suspense fallback={<DataState loading/>}><Routes>
 <Route element={<PublicLayout/>}><Route path="/" element={<LandingPage/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/><Route path="/prices" element={<PricesPage/>}/><Route path="/map" element={<MapPage/>}/>{['help','terms','privacy','about'].map(path=><Route key={path} path={'/'+path} element={<InfoPage/>}/>)}<Route path="*" element={<InfoPage/>}/></Route>
 <Route element={<ProtectedRoute><DashboardLayout/></ProtectedRoute>}><Route path="/farmer/dashboard" element={<ProtectedRoute roles={['farmer']}><FarmerDashboard/></ProtectedRoute>}/><Route path="/buyer/dashboard" element={<ProtectedRoute roles={['buyer']}><BuyerDashboard/></ProtectedRoute>}/><Route path="/fpo/dashboard" element={<ProtectedRoute roles={['fpo']}><FPODashboard/></ProtectedRoute>}/><Route path="/sell" element={<ProtectedRoute roles={['farmer','fpo']}><SellPage/></ProtectedRoute>}/><Route path="/matches" element={<ProtectedRoute roles={['farmer','fpo']}><MatchesPage/></ProtectedRoute>}/><Route path="/offers" element={<OffersPage/>}/><Route path="/transactions" element={<TransactionsPage/>}/><Route path="/grievances" element={<GrievancesPage/>}/></Route>
 </Routes></Suspense></ErrorBoundary>;
}
export default function App(){return <LanguageProvider><AuthProvider><BrowserRouter><RouteContent/></BrowserRouter></AuthProvider></LanguageProvider>;}
