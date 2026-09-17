import { useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Sprout } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { safeNext } from '../lib/session';
import { Field, Notice } from '../components/Experience';
export default function LoginPage(){
 const {login}=useAuth();const {t}=useLanguage();const navigate=useNavigate();const location=useLocation();const [params]=useSearchParams();
 const next=params.get('next')||(location.state?.from?.pathname||'')+(location.state?.from?.search||'');
 const [identifier,setIdentifier]=useState('');const [password,setPassword]=useState('');const [show,setShow]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function submit(e){e.preventDefault();setBusy(true);setError('');const res=await login(identifier,password);setBusy(false);if(res.success)navigate(safeNext(next,res.user.role),{replace:true});else setError(res.error);}
 return <div className="auth-section"><aside className="auth-aside"><Sprout size={48}/><h2>{t('heroTitle')}</h2><p>{t('heroText')}</p></aside><div className="auth-card"><p className="eyebrow">KRISHILINK</p><h1>{t('loginTitle')}</h1><p className="muted">{t('loginIntro')}</p>{next&&<Notice>{t('intentNotice')}</Notice>}<form onSubmit={submit} className="form-stack"><Field label={t('identifier')} autoComplete="username" required value={identifier} onChange={e=>setIdentifier(e.target.value)}/><Field label={t('password')} type={show?'text':'password'} autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)}/><label className="check-label"><input type="checkbox" checked={show} onChange={e=>setShow(e.target.checked)}/>{t('showPassword')}</label>{error&&<Notice error>{t(error)}</Notice>}<button className="button wide" disabled={busy}>{t(busy?'loading':'login')}<ArrowRight size={19}/></button></form><p className="auth-switch">{t('newHere')} <Link to={'/register?'+new URLSearchParams({next})}>{t('register')}</Link></p><Link className="text-link" to="/help#account">{t('help')}</Link></div></div>;
}
