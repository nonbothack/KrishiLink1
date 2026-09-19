import { useEffect, useRef, useState } from 'react';
import { Mic, Volume2, VolumeX } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

const VOICE_LOCALE = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' };

function speechApi() {
  if (typeof window === 'undefined') return null;
  return window.speechSynthesis || null;
}

function recognitionConstructor() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export function ReadAloudButton({ text }) {
  const { t, language } = useLanguage();
  const [available, setAvailable] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    const api = speechApi();
    if (!api) return undefined;
    const update = () => setAvailable(api.getVoices().some((voice) => voice.lang?.toLowerCase().startsWith(language)));
    update();
    api.addEventListener?.('voiceschanged', update);
    return () => api.removeEventListener?.('voiceschanged', update);
  }, [language]);

  function toggle() {
    const api = speechApi();
    if (!api || !available) return;
    if (speaking) {
      api.cancel();
      setSpeaking(false);
      return;
    }
    const voice = api.getVoices().find((item) => item.lang?.toLowerCase().startsWith(language));
    if (!voice) return;
    const Utterance = window.SpeechSynthesisUtterance || globalThis.SpeechSynthesisUtterance;
    if (!Utterance) return;
    const utterance = new Utterance(text);
    utterance.voice = voice;
    utterance.lang = VOICE_LOCALE[language];
    utterance.onend = utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    api.speak(utterance);
  }

  return available ? (
    <button className="button secondary" type="button" onClick={toggle}>
      {speaking ? <VolumeX size={18} aria-hidden="true" /> : <Volume2 size={18} aria-hidden="true" />}
      {t(speaking ? 'stopReading' : 'readAloud')}
    </button>
  ) : <p className="field-hint">{t('voiceOutputUnavailable')}</p>;
}

export function DictationButton({ onTranscript }) {
  const { t, language } = useLanguage();
  const [consented, setConsented] = useState(false);
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState('');
  const recognitionRef = useRef(null);
  const SupportedRecognition = recognitionConstructor();

  useEffect(() => () => recognitionRef.current?.stop(), []);

  function start() {
    if (!SupportedRecognition || !consented || listening) return;
    const recognition = new SupportedRecognition();
    recognitionRef.current = recognition;
    recognition.lang = VOICE_LOCALE[language];
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = String(event.results?.[0]?.[0]?.transcript || '').trim();
      if (transcript) {
        onTranscript(transcript);
        setMessage(t('voiceTranscriptReview'));
      }
    };
    recognition.onerror = () => setMessage(t('voiceInputFailed'));
    recognition.onend = () => { setListening(false); recognitionRef.current = null; };
    setMessage('');
    setListening(true);
    try {
      recognition.start();
    } catch {
      setListening(false);
      recognitionRef.current = null;
      setMessage(t('voiceInputFailed'));
    }
  }

  if (!SupportedRecognition) return <p className="field-hint">{t('voiceInputUnavailable')}</p>;
  return (
    <div className="voice-dictation">
      <label className="checkbox-row">
        <input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />
        <span>{t('voicePrivacyConsent')}</span>
      </label>
      <p className="field-hint">{t('voicePrivacyNote')}</p>
      <button className="button secondary" type="button" disabled={!consented} onClick={() => {
        if (listening) { recognitionRef.current?.stop(); setListening(false); }
        else start();
      }}>
        <Mic size={18} aria-hidden="true" />{t(listening ? 'voiceStop' : 'dictateLocation')}
      </button>
      {message && <p role="status" className="field-hint">{message}</p>}
    </div>
  );
}
