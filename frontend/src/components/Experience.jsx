import { useId, useEffect, useState, useCallback } from 'react';
import { AlertCircle, RefreshCw, PackageOpen } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';
export function Field({ label, hint, error, as: Tag = 'input', children, id: supplied, ...props }) {
  const generated = useId(); const id = supplied || generated;
  return <div className="field"><label htmlFor={id}>{label}</label><Tag id={id} aria-invalid={!!error} aria-describedby={hint || error ? id+'-hint' : undefined} autoComplete="off" {...props}>{children}</Tag>{(hint || error) && <p id={id+'-hint'} className={error ? 'field-error' : 'field-hint'}>{error || hint}</p>}</div>;
}
export function Notice({ children, error = false }) { return <div className={error ? 'notice notice-error' : 'notice'} role={error ? 'alert' : 'status'}><AlertCircle size={20}/><div>{children}</div></div>; }
export function DataState({ loading, error, empty, onRetry, children }) {
  const {t} = useLanguage();
  if (loading) return <div className="data-state" role="status"><RefreshCw className="loading-icon" size={24}/><p>{t('loading')}</p></div>;
  if (error) return <div className="data-state" role="alert"><AlertCircle size={28}/><p>{t(error,'Could not load this information.')}</p>{onRetry && <button className="button secondary" onClick={onRetry}>{t('retry')}</button>}</div>;
  if (empty) return <div className="data-state"><PackageOpen size={32}/><p>{typeof empty === 'string' ? empty : t('empty')}</p></div>;
  return children;
}
export function useResource(loader, dependencies = []) {
  const [revision, setRevision] = useState(0);
  const [resource, setResource] = useState({loading:true,error:null,data:[],total:0});
  useEffect(() => {
    let active = true;
    setResource(prev => ({...prev, loading:true, error:null}));
    Promise.resolve().then(loader).then(res => { if (active) setResource({ ...res, loading:false,error:res.success ? null : (res.error || 'server'),data:res.data ?? [] }); }).catch(() => {if(active) setResource({loading:false,error:'network',data:[]});});
    return () => {active = false;};
  // Dependencies are supplied explicitly by the calling resource.
  }, [...dependencies,revision]);
  const retry = useCallback(() => setRevision(n=>n+1),[]);
  return {...resource,retry};
}
export function PageHeading({eyebrow,title,description,action}) {return <div className="page-heading"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action}</div>;}
