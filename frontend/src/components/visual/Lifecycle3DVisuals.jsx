// =============================================================
// Lifecycle3DVisuals — High-Grade 3D & Photorealistic Visuals
// for the 5-Step Farmgate to Bank Settlement Simulator
// =============================================================

import { useState } from 'react';
import {
  ShieldCheck, CheckCircle2, Lock, Radio,
  Award, Building2,
  Scan, Check, Sparkles, Navigation
} from 'lucide-react';
import Tilt3DCard from './Tilt3DCard';

// -------------------------------------------------------------
// STEP 1: Farmgate Inspection & Quality Scanner
// -------------------------------------------------------------
export function Step1Visual({ t }) {
  const [scanActive, setScanActive] = useState(true);
  const tr = (k, def) => (t ? t(k, def) : def);

  return (
    <Tilt3DCard className="w-full h-full rounded-3xl overflow-hidden shadow-2xl border border-emerald-500/20 bg-emerald-950">
      <div className="relative h-80 sm:h-96 w-full overflow-hidden">
        {/* Photorealistic Farmer & Crates Image */}
        <img
          src="/images/farmgate-crop-inspection.jpg"
          alt="Farmer with fresh produce crates"
          className="w-full h-full object-cover object-center transform scale-105 hover:scale-110 transition-transform duration-700"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-black/20" />

        {/* 3D Holographic Quality Scanner Overlay */}
        <div className="absolute inset-6 border-2 border-emerald-400/40 rounded-2xl pointer-events-none flex flex-col justify-between p-4">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setScanActive(!scanActive)}
              className="pointer-events-auto flex items-center gap-2 bg-emerald-950/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-emerald-400/50 text-emerald-300 text-xs font-bold shadow-lg hover:bg-emerald-900/90 transition-colors cursor-pointer"
              title="Click to toggle scanner"
            >
              <Scan className={`w-4 h-4 text-emerald-400 ${scanActive ? 'animate-pulse' : ''}`} />
              <span>{tr('ai_quality_assayer', 'AI QUALITY ASSAYER ACTIVE')}</span>
            </button>
            <span className="text-[11px] font-mono bg-black/60 text-emerald-300 px-2.5 py-1 rounded-lg border border-emerald-500/30">
              FRAME #4829
            </span>
          </div>

          {/* Scanner Grid Line */}
          {scanActive && (
            <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_15px_#10b981] animate-pulse" />
          )}

          {/* Telemetry Chips */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-black/75 backdrop-blur-md p-2 rounded-xl border border-white/10 text-center">
              <p className="text-[10px] text-gray-400 uppercase font-semibold">{tr('moisture', 'Moisture')}</p>
              <p className="text-xs font-extrabold text-emerald-400">11.8% ({tr('optimal', 'Optimal')})</p>
            </div>
            <div className="bg-black/75 backdrop-blur-md p-2 rounded-xl border border-white/10 text-center">
              <p className="text-[10px] text-gray-400 uppercase font-semibold">{tr('diameter', 'Diameter')}</p>
              <p className="text-xs font-extrabold text-white">55-65 mm</p>
            </div>
            <div className="bg-black/75 backdrop-blur-md p-2 rounded-xl border border-white/10 text-center">
              <p className="text-[10px] text-gray-400 uppercase font-semibold">{tr('grade_result', 'Grade Result')}</p>
              <p className="text-xs font-extrabold text-amber-300">Grade A ({tr('export_grade', 'Export')})</p>
            </div>
          </div>
        </div>

        {/* Floating Certification Badge */}
        <div className="absolute top-8 right-8 z-20 bg-emerald-600/90 backdrop-blur-md text-white px-3 py-1.5 rounded-xl text-xs font-bold shadow-xl border border-emerald-300/40 flex items-center gap-1.5 animate-float-3d">
          <Award className="w-4 h-4 text-yellow-300" />
          <span>{tr('verified_lot', 'Verified Lot')} #LOT-ON-9902</span>
        </div>
      </div>
    </Tilt3DCard>
  );
}

// -------------------------------------------------------------
// STEP 2: Buyer Trading Desk & Counter-Offer Simulator
// -------------------------------------------------------------
export function Step2Visual({ t }) {
  const [offerAccepted, setOfferAccepted] = useState(false);
  const [offerPrice, setOfferPrice] = useState(2450);
  const tr = (k, def) => (t ? t(k, def) : def);

  return (
    <Tilt3DCard className="w-full h-full rounded-3xl overflow-hidden shadow-2xl border border-blue-500/20 bg-slate-950">
      <div className="relative h-80 sm:h-96 w-full overflow-hidden">
        {/* Photorealistic Buyer Desk Image */}
        <img
          src="/images/buyer-trading-desk.jpg"
          alt="Institutional buyer desk"
          className="w-full h-full object-cover object-center transform scale-105 hover:scale-110 transition-transform duration-700"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/95 via-slate-950/40 to-slate-950/30" />

        {/* Interactive Floating Counter-Offer Card */}
        <div className="absolute inset-x-4 bottom-4 bg-slate-900/90 backdrop-blur-xl border border-blue-400/30 rounded-2xl p-4 shadow-2xl">
          <div className="flex items-center justify-between gap-3 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-blue-600/30 border border-blue-400/40 flex items-center justify-center">
                <Building2 className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">Agriflow Processing Ltd.</h4>
                <p className="text-[10px] text-blue-300">{tr('institutional_buyer', 'Institutional Buyer')} • AAA Verified</p>
              </div>
            </div>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30">
              {tr('live_counter_offer', 'Live Counter-Offer')}
            </span>
          </div>

          <div className="bg-slate-800/80 rounded-xl p-3 flex items-center justify-between border border-white/10 mb-3">
            <div>
              <p className="text-[10px] text-gray-400">{tr('offered_rate', 'Offered Rate (150 Qtl Onion)')}</p>
              <p className="text-lg font-black text-emerald-400">₹{offerPrice.toLocaleString('en-IN')}<span className="text-xs font-normal text-gray-400">/qtl</span></p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-gray-400">{tr('total_contract', 'Total Lot Contract')}</p>
              <p className="text-sm font-bold text-white">₹{(offerPrice * 150).toLocaleString('en-IN')}</p>
            </div>
          </div>

          {/* Action Simulator Buttons */}
          <div className="flex items-center gap-2">
            {offerAccepted ? (
              <div className="w-full bg-emerald-600 text-white font-bold text-xs py-2.5 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/50">
                <Check className="w-4 h-4" />
                <span>{tr('trade_locked_success', 'Trade Locked & Moving to Escrow!')}</span>
              </div>
            ) : (
              <>
                <button
                  onClick={() => setOfferAccepted(true)}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs py-2.5 rounded-xl transition-all shadow-md shadow-emerald-950/40 active:scale-95"
                >
                  {tr('accept_offer_cta', 'Accept Offer (स्वीकारा)')}
                </button>
                <button
                  onClick={() => setOfferPrice(p => p + 50)}
                  className="px-3 py-2.5 bg-white/10 hover:bg-white/20 text-blue-200 border border-white/10 font-bold text-xs rounded-xl transition-all active:scale-95"
                  title="Counter with +₹50"
                >
                  {tr('counter_add_50', 'Counter +₹50')}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </Tilt3DCard>
  );
}

// -------------------------------------------------------------
// STEP 3: 3D Holographic Escrow Vault Scene
// -------------------------------------------------------------
export function Step3Visual({ t }) {
  const tr = (k, def) => (t ? t(k, def) : def);

  return (
    <Tilt3DCard className="w-full h-full rounded-3xl overflow-hidden shadow-2xl border border-emerald-500/30 bg-gradient-to-br from-[#062c1e] via-[#093d2a] to-[#041a12]">
      <div className="relative h-80 sm:h-96 w-full flex flex-col items-center justify-center p-6 text-center">
        
        {/* Ambient Glow Aura */}
        <div className="absolute w-56 h-56 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute w-44 h-44 bg-amber-500/15 rounded-full blur-2xl pointer-events-none" />

        {/* 3D Rotating Cryptographic Ring */}
        <div className="relative w-36 h-36 flex items-center justify-center mb-6">
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-emerald-400/40 animate-spin-slow" />
          <div className="absolute inset-3 rounded-full border border-amber-300/30 animate-spin-slow" style={{ animationDirection: 'reverse', animationDuration: '14s' }} />
          <div className="absolute inset-6 rounded-full bg-emerald-900/60 backdrop-blur-xl border border-emerald-400/60 shadow-[0_0_35px_rgba(16,185,129,0.35)] flex items-center justify-center">
            <Lock className="w-10 h-10 text-emerald-300 animate-pulse" />
          </div>
        </div>

        {/* Contract Vault Details */}
        <div className="relative z-10 space-y-2 max-w-sm">
          <div className="inline-flex items-center gap-1.5 bg-emerald-500/20 border border-emerald-400/40 px-3 py-1 rounded-full text-xs font-bold text-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>{tr('non_custodial_escrow', 'NON-CUSTODIAL ESCROW ACTIVE')}</span>
          </div>

          <h4 className="text-2xl font-black text-white tracking-tight">
            ₹3,67,500 <span className="text-xs font-medium text-emerald-300">{tr('locked', 'LOCKED')}</span>
          </h4>

          <p className="text-xs text-emerald-100/80 leading-relaxed">
            {tr('escrow_desc', 'Funds deposited by Buyer into licensed banking partner escrow (HDFC Bank Node). KrishiLink never holds custody.')}
          </p>

          <div className="pt-2 flex items-center justify-center gap-2 text-[11px] font-mono text-emerald-300/90">
            <span>HASH: 9e4f...3c82</span>
            <span>•</span>
            <span className="text-emerald-400 font-bold">DPDP 2023 COMPLIANT</span>
          </div>
        </div>
      </div>
    </Tilt3DCard>
  );
}

// -------------------------------------------------------------
// STEP 4: Smart Logistics & Highway GPS Telemetry
// -------------------------------------------------------------
export function Step4Visual({ t }) {
  const tr = (k, def) => (t ? t(k, def) : def);

  return (
    <Tilt3DCard className="w-full h-full rounded-3xl overflow-hidden shadow-2xl border border-indigo-500/30 bg-gradient-to-br from-[#0c142e] via-[#111f4d] to-[#080d21]">
      <div className="relative h-80 sm:h-96 w-full flex flex-col justify-between p-6 overflow-hidden">
        
        {/* Highway Landscape Scene */}
        <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]" />

        {/* Top Telemetry Bar */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-blue-400/40 text-blue-300 text-xs font-bold">
            <Radio className="w-4 h-4 text-blue-400 animate-pulse" />
            <span>{tr('gps_telemetry_live', 'GPS SATELLITE TELEMETRY LIVE')}</span>
          </div>
          <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-500/40 px-2.5 py-1 rounded-lg">
            4.2°C REEFER OK
          </span>
        </div>

        {/* Animated Road Simulation */}
        <div className="relative z-10 my-auto py-4">
          <div className="relative w-full h-24 bg-slate-900/90 rounded-2xl border border-white/10 overflow-hidden flex items-center px-4">
            {/* Road center dash */}
            <div className="absolute inset-x-0 h-0.5 border-t border-dashed border-gray-600" />

            {/* Moving Truck Icon & Beacon */}
            <div className="relative z-10 flex items-center gap-3 bg-blue-600 text-white px-4 py-2 rounded-xl shadow-lg shadow-blue-950/60 border border-blue-300/40 animate-float-3d">
              <Navigation className="w-5 h-5 rotate-90 text-amber-300" />
              <div>
                <p className="text-xs font-black">MH-15-EG-8841</p>
                <p className="text-[10px] text-blue-100">Speed: 58 km/h • On Schedule</p>
              </div>
            </div>

            {/* Destination Marker */}
            <div className="ml-auto text-right">
              <p className="text-[10px] text-gray-400 uppercase font-semibold">{tr('route', 'Route')}</p>
              <p className="text-xs font-bold text-white">Nashik APMC → Vashi Hub</p>
              <p className="text-[10px] text-emerald-400 font-semibold">{tr('eta', 'ETA: 2h 45m')}</p>
            </div>
          </div>
        </div>

        {/* Milestone Steps Bar */}
        <div className="relative z-10 grid grid-cols-3 gap-2 text-center text-[10px]">
          <div className="bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 py-1.5 rounded-lg font-bold">
            ✓ {tr('farmgate_loaded', 'Farmgate Loaded')}
          </div>
          <div className="bg-blue-950/80 border border-blue-500/40 text-blue-300 py-1.5 rounded-lg font-bold animate-pulse">
            ● {tr('highway_transit', 'Highway Transit')}
          </div>
          <div className="bg-slate-900/80 border border-white/10 text-gray-400 py-1.5 rounded-lg">
            ○ {tr('destination_dock', 'Destination Dock')}
          </div>
        </div>
      </div>
    </Tilt3DCard>
  );
}

// -------------------------------------------------------------
// STEP 5: Instant Direct Bank Payout Notification
// -------------------------------------------------------------
export function Step5Visual({ t }) {
  const tr = (k, def) => (t ? t(k, def) : def);

  return (
    <Tilt3DCard className="w-full h-full rounded-3xl overflow-hidden shadow-2xl border border-emerald-500/30 bg-emerald-950">
      <div className="relative h-80 sm:h-96 w-full overflow-hidden">
        {/* Photorealistic Smiling Farmer Image */}
        <img
          src="/images/hero-farmer-modern.jpg"
          alt="Happy farmer receiving instant payment"
          className="w-full h-full object-cover object-top transform scale-105 hover:scale-110 transition-transform duration-700"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/95 via-emerald-950/50 to-transparent" />

        {/* Floating 3D Smartphone Notification Card */}
        <div className="absolute inset-x-4 bottom-4 bg-emerald-900/90 backdrop-blur-xl border border-emerald-400/40 rounded-2xl p-4 shadow-2xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-900/60">
              <CheckCircle2 className="w-6 h-6 text-white animate-bounce" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-emerald-300 tracking-wider">{tr('instant_settlement', 'UPI / NEFT Instant Settlement')}</p>
              <h4 className="text-xl font-black text-white">₹3,67,500.00</h4>
            </div>
            <span className="ml-auto text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300 border border-emerald-400/30">
              {tr('credited', 'CREDITED')}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] bg-emerald-950/80 p-2.5 rounded-xl border border-emerald-800/60 font-mono">
            <div>
              <span className="text-gray-400 block text-[9px]">{tr('utr_label', 'UTR TRANSACTION ID')}</span>
              <span className="text-emerald-300 font-bold">UTR-HDFC-9928114</span>
            </div>
            <div>
              <span className="text-gray-400 block text-[9px]">{tr('beneficiary_label', 'BENEFICIARY BANK')}</span>
              <span className="text-white font-bold">SBI (A/C •••• 4819)</span>
            </div>
          </div>

          <div className="mt-2 text-center">
            <span className="text-[10px] text-emerald-200/90 font-semibold flex items-center justify-center gap-1">
              <Sparkles className="w-3 h-3 text-yellow-300" />
              {tr('zero_middleman', '100% Net Realization • ₹0 Middleman Deduction')}
            </span>
          </div>
        </div>
      </div>
    </Tilt3DCard>
  );
}
