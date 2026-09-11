// =============================================================
// Language Context
// Manages the active language: 'en', 'mr', or 'hi'
// =============================================================

import { createContext, useContext, useState, useEffect } from 'react';
import { getTranslation, getGreeting, getCropTranslation } from '../utils/translations';
import { translateDOMTree } from '../utils/universalTranslator';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  // Default language is English, with saved choice from localStorage
  const [language, setLanguage] = useState(
    localStorage.getItem('krishilink_lang') || 'en'
  );

  const changeLanguage = (lang) => {
    setLanguage(lang);
    localStorage.setItem('krishilink_lang', lang);
  };

  // Sync document html lang attribute and trigger universal DOM translation
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
      translateDOMTree(document.body, language);
      if (language !== 'en') {
        let timeoutId = null;
        const observer = new MutationObserver(() => {
          if (timeoutId) clearTimeout(timeoutId);
          timeoutId = setTimeout(() => {
            translateDOMTree(document.body, language);
          }, 150);
        });
        observer.observe(document.body, { childList: true, subtree: true });
        return () => {
          if (timeoutId) clearTimeout(timeoutId);
          observer.disconnect();
        };
      }
    }
  }, [language]);

  // t('key' or 'Phrase', fallback) returns translation for active language
  const t = (key, fallback) => {
    if (!key) return '';
    const res = getTranslation(language, key);
    return res !== undefined && res !== '' ? res : (fallback || key);
  };

  const cropT = (cropName) => getCropTranslation(cropName, language);

  const value = {
    language,
    changeLanguage,
    setLanguage: changeLanguage,
    t,
    cropT,
    greeting: getGreeting(language),
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

// Usage: const { t, language, changeLanguage } = useLanguage();
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be inside LanguageProvider');
  return context;
}
