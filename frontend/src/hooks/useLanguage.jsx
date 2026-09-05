// =============================================================
// Language Context
// Manages the active language: 'en', 'mr', or 'hi'
// =============================================================

import { createContext, useContext, useState } from 'react';
import { getTranslation, getGreeting, getCropTranslation } from '../utils/translations';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  // Default language is English
  const [language, setLanguage] = useState(
    localStorage.getItem('krishilink_lang') || 'en'
  );

  const changeLanguage = (lang) => {
    setLanguage(lang);
    localStorage.setItem('krishilink_lang', lang);
  };

  // t('key') gives the translation for the current language
  const t = (key) => getTranslation(language, key);
  const cropT = (cropName) => getCropTranslation(cropName, language);

  const value = {
    language,
    changeLanguage,
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
