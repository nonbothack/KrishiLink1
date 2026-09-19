import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import OtpInput from './OtpInput';

describe('OTP input', () => {
  it('labels each digit, supports numeric typing, and accepts a pasted code', () => {
    const onChange = vi.fn();
    render(<OtpInput label="Verification code" value="" onChange={onChange} />);

    const digits = screen.getAllByRole('textbox');
    expect(digits).toHaveLength(6);
    expect(digits[0]).toHaveAccessibleName('Verification code, 1 of 6');
    expect(digits[0]).toHaveAttribute('inputmode', 'numeric');
    expect(digits[0]).toHaveAttribute('autocomplete', 'one-time-code');

    fireEvent.change(digits[0], { target: { value: '4' } });
    expect(onChange).toHaveBeenLastCalledWith('4');
    fireEvent.paste(digits[0], { clipboardData: { getData: () => '65-4321' } });
    expect(onChange).toHaveBeenLastCalledWith('654321');
  });
});
