import { createContext, useContext, useState, useEffect } from 'react';
import { getTranslation, getGreeting, getCropTranslation } from '../utils/translations';
import { copy } from '../utils/copy';
const LanguageContext = createContext(null);
export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => { try { const l = localStorage.getItem('krishilink_lang'); return ['en','mr','hi'].includes(l) ? l : 'en'; } catch { return 'en'; } });
  const changeLanguage = (lang) => { if (!copy[lang]) return; setLanguage(lang); try { localStorage.setItem('krishilink_lang', lang); } catch { /* Preference remains available in memory. */ } };
  useEffect(() => { document.documentElement.lang = language; }, [language]);
  const t = (key, fallback) => copy[language][key] ?? getTranslation(language,key) ?? fallback ?? key;
  const cropT = (crop) => crop === 'Maize' ? ({en:'Maize',mr:'मका',hi:'मक्का'}[language]) : getCropTranslation(crop,language);
  const money = (value) => new Intl.NumberFormat(`${language}-IN`, {style:'currency',currency:'INR',maximumFractionDigits:2}).format(Number(value));
  return <LanguageContext.Provider value={{ language, changeLanguage, setLanguage:changeLanguage, t, cropT, money, greeting:getGreeting(language) }}>{children}</LanguageContext.Provider>;
}
export function useLanguage() { return useContext(LanguageContext); }
