import React, { useState } from 'react';
import { ShieldCheck, Copy, Check } from 'lucide-react';

/**
 * Standardized cryptographic evidence pill displaying SHA-256 integrity with copy-to-clipboard.
 */
export function EvidenceLabel({
  hash,
  label = 'SHA-256 Verified',
  showHash = true,
  className = '',
}) {
  const [copied, setCopied] = useState(false);

  if (!hash) return null;

  const shortHash = hash.length > 16 ? `${hash.slice(0, 8)}...${hash.slice(-8)}` : hash;

  const handleCopy = () => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 bg-emerald-50/80 border border-emerald-200/80 text-emerald-800 text-[11px] px-2.5 py-1 rounded-md ${className}`}
    >
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
      <span className="font-semibold">{label}</span>
      {showHash && (
        <span className="font-mono text-[10px] text-emerald-900/70 bg-emerald-100/60 px-1 py-0.5 rounded">
          {shortHash}
        </span>
      )}
      <button
        type="button"
        onClick={handleCopy}
        className="text-emerald-700 hover:text-emerald-950 p-0.5 rounded hover:bg-emerald-200/50 transition"
        title="Copy full cryptographic hash"
      >
        {copied ? <Check className="w-3 h-3 text-emerald-700" /> : <Copy className="w-3 h-3" />}
      </button>
    </div>
  );
}

export default EvidenceLabel;
