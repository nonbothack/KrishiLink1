import { createContext,useContext,useEffect,useState } from 'react';
import { apiCall,restoreSession,setAccessToken } from '../lib/http';
import { clearSession,normalizeIdentifier,normalizePhone,readSession } from '../lib/session';
const AuthContext=createContext(null);
export function AuthProvider({children}){
 const [user,setUser]=useState(readSession);const [loading,setLoading]=useState(()=>!!readSession());
 useEffect(()=>{
  let active=true;
  localStorage.removeItem('krishilink_access_token');localStorage.removeItem('krishilink_refresh_token');
  if(readSession())restoreSession().then(()=>apiCall('/api/v1/auth/me')).then(res=>{
   if(active){if(res.success){const normal={...res.data,name:res.data.full_name};setUser(normal);localStorage.setItem('krishilink_user',JSON.stringify(normal));}else{setUser(null);clearSession();}setLoading(false);}
  }).catch(error=>{if(active){setUser(null);if(error.status===401)clearSession();setLoading(false);}});
  const expired=()=>{setUser(null);setLoading(false);};
  const changed=event=>{if(event.key==='krishilink_user'&&!event.newValue){setAccessToken(null);setUser(null);}};
  window.addEventListener('session-expired',expired);window.addEventListener('storage',changed);
  return()=>{active=false;window.removeEventListener('session-expired',expired);window.removeEventListener('storage',changed);};
 },[]);
 async function authenticate(path,payload){
  const res=await apiCall('/api/v1/auth/'+path,{method:'POST',auth:false,body:JSON.stringify(payload)});
  if(!res.success)return res;
  const normal={...res.data.user,name:res.data.user.full_name};
  setAccessToken(res.data.access_token);localStorage.setItem('krishilink_user',JSON.stringify(normal));setUser(normal);
  return {success:true,user:normal};
 }
 const login=(identifier,password)=>authenticate('login',{email:normalizeIdentifier(identifier),password});
 const register=data=>authenticate('register',{full_name:data.name.trim(),email:data.email?.trim()||null,phone:normalizePhone(data.phone)||null,password:data.password,role:data.role,location:data.location?.trim()||null,district:data.district?.trim()||null,state:data.state||null});
 const logout=async()=>{const pending=apiCall('/api/v1/auth/logout',{method:'POST'});clearSession();setUser(null);await pending;setAccessToken(null);};
 return <AuthContext.Provider value={{user,loading,isLoggedIn:!!user,isFarmer:user?.role==='farmer',isBuyer:user?.role==='buyer',isFPO:user?.role==='fpo',login,register,logout}}>{children}</AuthContext.Provider>;
}
export function useAuth(){return useContext(AuthContext);}
