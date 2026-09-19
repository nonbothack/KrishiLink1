import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LanguageProvider } from '../hooks/useLanguage';
import { DictationButton } from './VoiceControls';

describe('browser dictation', () => {
  beforeEach(() => {
    class FakeRecognition {
      start() {
        this.onresult?.({ results: [[{ transcript: 'Nashik district' }]] });
        this.onend?.();
      }
      stop() { this.onend?.(); }
    }
    window.SpeechRecognition = FakeRecognition;
  });

  it('only fills the field and never submits a form or accepts an action', () => {
    const onTranscript = vi.fn();
    const onSubmit = vi.fn((event) => event.preventDefault());
    render(
      <LanguageProvider>
        <form onSubmit={onSubmit}>
          <DictationButton onTranscript={onTranscript} />
          <button type="submit">Publish lot</button>
        </form>
      </LanguageProvider>,
    );
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: /speak location/i }));
    expect(onTranscript).toHaveBeenCalledWith('Nashik district');
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent(/check and edit/i);
  });
});
