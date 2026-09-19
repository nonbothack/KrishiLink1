import { useEffect, useRef } from 'react';

export default function OtpInput({ value, onChange, label, disabled = false }) {
  const inputs = useRef([]);
  const changeRef = useRef(onChange);
  useEffect(() => {
    changeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!window.isSecureContext || !('OTPCredential' in window) || !navigator.credentials?.get)
      return undefined;
    const controller = new AbortController();
    navigator.credentials
      .get({ otp: { transport: ['sms'] }, signal: controller.signal })
      .then((credential) => {
        if (credential?.code) changeRef.current(String(credential.code).replace(/\D/g, '').slice(0, 6));
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  const digits = String(value || '').replace(/\D/g, '').slice(0, 6).split('');
  while (digits.length < 6) digits.push('');

  function updateFrom(index, raw) {
    const incoming = raw.replace(/\D/g, '').slice(0, 6 - index);
    const next = digits.slice();
    if (incoming.length > 1) {
      incoming.split('').forEach((digit, offset) => {
        next[index + offset] = digit;
      });
    } else {
      next[index] = incoming;
    }
    changeRef.current(next.join(''));
    const nextIndex = Math.min(index + Math.max(1, incoming.length), 5);
    if (incoming) inputs.current[nextIndex]?.focus();
  }

  function paste(event, index) {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '');
    if (!pasted) return;
    event.preventDefault();
    updateFrom(index, pasted);
  }

  return (
    <div className="otp-inputs" role="group" aria-label={label}>
      {digits.map((digit, index) => (
        <input
          key={index}
          ref={(element) => {
            inputs.current[index] = element;
          }}
          aria-label={`${label}, ${index + 1} of 6`}
          type="text"
          inputMode="numeric"
          autoComplete={index === 0 ? 'one-time-code' : 'off'}
          pattern="[0-9]*"
          maxLength={6}
          value={digit}
          disabled={disabled}
          onChange={(event) => updateFrom(index, event.target.value)}
          onPaste={(event) => paste(event, index)}
          onKeyDown={(event) => {
            if (event.key === 'Backspace' && !digit && index > 0) inputs.current[index - 1]?.focus();
            if (event.key === 'ArrowLeft' && index > 0) inputs.current[index - 1]?.focus();
            if (event.key === 'ArrowRight' && index < 5) inputs.current[index + 1]?.focus();
          }}
        />
      ))}
    </div>
  );
}
