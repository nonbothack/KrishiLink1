import type { ReactNode } from 'react';

export type SupportedLanguage = 'en' | 'hi' | 'mr';

export interface LanguageContextValue {
  language: SupportedLanguage;
  changeLanguage: (language: SupportedLanguage) => void;
  setLanguage: (language: SupportedLanguage) => void;
  t: (key: string, fallback?: string) => string;
  cropT: (crop: string) => string;
  money: (value: number | string) => string;
  greeting: string;
}

export declare function LanguageProvider(props: { children: ReactNode }): ReactNode;
export declare function useLanguage(): LanguageContextValue;
