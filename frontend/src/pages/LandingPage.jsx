// =============================================================
// Landing Page — KrishiLink (Immersive Visual Redesign)
// High-visual, animation-rich, farmer-first & institutional buyer platform.
//
// Highlights:
// - Live floating APMC Mandi pulse ticker
// - Dual-action high-contrast hero with visual trade slip & bank settlement badge
// - Continuous infinite-scrolling crop marquee with authentic photography
// - Interactive 5-Step Trade Execution Simulator (#how-it-works)
// - Interactive Agricultural Net Realization Calculator
// - Visual Cockpit Previews for Farmer, Buyer, and FPO
// - Live Mandi Market Explorer with truthful data provenance
// - DPDP Act 2023 & SHA-256 statutory trust pillars
// =============================================================

import { useEffect, useState, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Sprout, ArrowRight, ArrowUpRight, ShoppingBag, Tractor, Truck, FlaskConical,
  ShieldCheck, FileCheck2, Radio, CheckCircle2, Layers, Wallet,
  Handshake, Boxes, TrendingUp, Calculator, Check, ChevronRight, HelpCircle
} from 'lucide-react';

import { CROPS_METADATA, getCropImage } from '../utils/cropImages';
import { useLanguage } from '../hooks/useLanguage';
import ConstellationCanvas from '../components/visual/ConstellationCanvas';
import Tilt3DCard from '../components/visual/Tilt3DCard';
import {
  Step1Visual,
  Step2Visual,
  Step3Visual,
  Step4Visual,
  Step5Visual,
} from '../components/visual/Lifecycle3DVisuals';

// Live sample ticker data for the floating pulse
const TICKER_COMMODITIES = [
  { crop: 'Onion (कांदा)', market: 'Lasalgaon APMC', price: 2450, trend: 'up', change: '+4.2%' },
  { crop: 'Tomato (टोमॅटो)', market: 'Nashik APMC', price: 1820, trend: 'stable', change: '0.0%' },
  { crop: 'Soybean (सोयाबीन)', market: 'Latur APMC', price: 4350, trend: 'up', change: '+2.8%' },
  { crop: 'Cotton (कापूस)', market: 'Jalgaon APMC', price: 6800, trend: 'up', change: '+1.5%' },
  { crop: 'Wheat (गहू)', market: 'Pune APMC', price: 2750, trend: 'up', change: '+3.1%' },
  { crop: 'Potato (बटाटा)', market: 'Vashi APMC', price: 1550, trend: 'down', change: '-1.2%' },
  { crop: 'Chilli (मिरची)', market: 'Nagpur APMC', price: 7800, trend: 'up', change: '+5.0%' },
  { crop: 'Rice (भात)', market: 'Kolhapur APMC', price: 3600, trend: 'stable', change: '+0.5%' },
];

// 5-Step Lifecycle Simulation data
const LIFECYCLE_STEPS = [
  {
    id: 1,
    stepNum: '01',
    titleKey: 'howItWorksStep1',
    title: 'Snap & List Harvest in 60s',
    tagline: 'Farmgate Listing with Reserve Price',
    icon: Tractor,
    color: 'emerald',
    description: 'Take produce photos, declare your quantity in quintals, grade quality, and set your asking rate anchored to live APMC benchmarks.',
    badge: '📸 Quick 60s Listing',
    metric: '₹0 Listing Fee',
    simulatedUi: {
      type: 'listing',
      headline: 'Lot #KL-2840 — Fresh Garwa Onion',
      crop: 'Onion (कांदा)',
      qty: '200 Quintals',
      asking: '₹2,450 / qtl',
      grade: 'Grade A Export Quality',
      location: 'Yeola, Nashik, MH',
      status: 'Live on Exchange',
      statusColor: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    },
  },
  {
    id: 2,
    stepNum: '02',
    titleKey: 'howItWorksStep2',
    title: 'Direct Institutional Bidding',
    tagline: 'Zero Middlemen, Direct Counterparty Offers',
    icon: ShoppingBag,
    color: 'blue',
    description: 'Verified institutional buyers, food processors, and supermarket chains bid directly. Review offers in plain vernacular and negotiate with 1-click.',
    badge: '🤝 Direct Offers',
    metric: '100% Price Transparency',
    simulatedUi: {
      type: 'offer',
      headline: 'Incoming Buyer Offer Received',
      buyer: 'Reliance Fresh Procurement Ltd',
      crop: 'Onion (Garwa)',
      offeredPrice: '₹2,420 / qtl',
      totalValue: '₹4,84,000 Total Value',
      terms: 'Farmgate Pickup within 48 hrs',
      status: 'Awaiting Farmer Decision',
      statusColor: 'bg-amber-100 text-amber-800 border-amber-300',
    },
  },
  {
    id: 3,
    stepNum: '03',
    titleKey: 'howItWorksStep3',
    title: 'Farmgate Quality Assaying',
    tagline: 'Objective Lab Standards & Tamper-Proof Seals',
    icon: FlaskConical,
    color: 'purple',
    description: 'NABL-accredited or platform-verified assayers inspect produce at your farmgate. Moisture, foreign matter, and sizing recorded with cryptographic SHA-256 evidence.',
    badge: '🧪 Certified Assay',
    metric: 'No Hidden Downgrades',
    simulatedUi: {
      type: 'assay',
      headline: 'Digital Assay Certificate #QC-904',
      assayer: 'AgriAssay Labs (NABL Accr. #5812)',
      moisture: '11.4% (Within statutory 12% max)',
      foreignMatter: '0.6% (Clean)',
      result: 'PASSED — GRADE A VERIFIED',
      hash: 'SHA-256: 7d9a3b84...e81c',
      status: 'Quality Certified',
      statusColor: 'bg-purple-100 text-purple-800 border-purple-300',
    },
  },
  {
    id: 4,
    stepNum: '04',
    titleKey: 'howItWorksStep4',
    title: 'Verified Weighment & Carrier',
    tagline: 'Calibrated Scales & GPS Departure Security',
    icon: Truck,
    color: 'amber',
    description: 'Verified carrier arrives for dispatch. Tare and gross weight recorded on digital weighbridge tickets. Tamper-evident seals applied before departure.',
    badge: '🚚 Secure Transport',
    metric: '0kg Weight Manipulation',
    simulatedUi: {
      type: 'logistics',
      headline: 'Consignment Gate Dispatch',
      carrier: 'Sahyadri Agro Logistics (Vehicle MH-15-EG-4921)',
      grossWeight: '20,480 kg (204.8 Quintals)',
      netWeight: '200.0 Quintals Certified',
      departureGate: 'Farmgate Nashik → Vashi Hub',
      status: 'Dispatched with Tamper Seal',
      statusColor: 'bg-blue-100 text-blue-800 border-blue-300',
    },
  },
  {
    id: 5,
    stepNum: '05',
    titleKey: 'howItWorksStep5',
    title: 'Instant Bank Settlement',
    tagline: '100% Direct Payout to Farmer Account',
    icon: Wallet,
    color: 'green',
    description: 'Payment released directly to the farmer bank account via NEFT / RTGS with zero custodial commission deductions. Instant confirmation and statutory receipt.',
    badge: '💰 Direct Payout',
    metric: '₹0 Commission Deducted',
    simulatedUi: {
      type: 'settlement',
      headline: 'Direct Bank Settlement Complete',
      amount: '₹4,84,000.00',
      bankInfo: 'Bank of Maharashtra (A/C ending in 4912)',
      utr: 'UTR #NEFT-MH-20260910-82914',
      fee: 'Platform Fee: ₹0.00',
      status: 'CREDITED IN BANK A/C',
      statusColor: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    },
  },
];

export default function LandingPage() {
  const { t } = useLanguage();
  const location = useLocation();

  const [activeStep, setActiveStep] = useState(1);
  const [selectedCalcCrop, setSelectedCalcCrop] = useState('Onion');
  const [calcQuintals, setCalcQuintals] = useState(150);
  const [activeRoleTab, setActiveRoleTab] = useState('farmer');

  // Handle smooth scroll when navigating to #how-it-works
  useEffect(() => {
    if (location.hash === '#how-it-works') {
      const el = document.getElementById('how-it-works');
      if (el) {
        setTimeout(() => {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    }
  }, [location]);



  // Calculation data for earnings calculator
  const calcData = useMemo(() => {
    const priceMap = {
      Onion: { mandi: 2150, direct: 2450, commRate: 0.08, scaleCutRate: 0.03 },
      Tomato: { mandi: 1550, direct: 1850, commRate: 0.08, scaleCutRate: 0.03 },
      Soybean: { mandi: 3950, direct: 4350, commRate: 0.06, scaleCutRate: 0.02 },
      Cotton: { mandi: 6300, direct: 6800, commRate: 0.05, scaleCutRate: 0.02 },
      Wheat: { mandi: 2350, direct: 2750, commRate: 0.06, scaleCutRate: 0.02 },
    };
    const c = priceMap[selectedCalcCrop] || priceMap.Onion;
    const grossDirect = calcQuintals * c.direct;
    const grossMandi = calcQuintals * c.mandi;
    const middlemanComm = Math.round(grossMandi * c.commRate);
    const scaleLoss = Math.round(grossMandi * c.scaleCutRate);
    const middlemanNet = grossMandi - middlemanComm - scaleLoss;
    const extraEarnings = grossDirect - middlemanNet;

    return {
      grossDirect,
      grossMandi,
      middlemanComm,
      scaleLoss,
      middlemanNet,
      extraEarnings,
      directRate: c.direct,
      mandiRate: c.mandi,
    };
  }, [selectedCalcCrop, calcQuintals]);

  const currentStepData = LIFECYCLE_STEPS.find(s => s.id === activeStep) || LIFECYCLE_STEPS[0];

  return (
    <div className="min-h-screen bg-[#FAF9F5] text-gray-900 font-sans selection:bg-emerald-100 selection:text-emerald-900">

      {/* ------------------------------------------------------------- */}
      {/* 1. TOP FLOATING LIVE MANDI TICKER PULSE                        */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-emerald-950 text-white border-b border-emerald-800/40 text-xs py-2 px-4 overflow-hidden relative z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-shrink-0 bg-emerald-900/90 text-emerald-300 font-bold px-3 py-1 rounded-full text-[11px] border border-emerald-700/50 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            LIVE MANDI PULSE
          </div>
          <div className="overflow-hidden flex-1 relative">
            <div className="animate-marquee flex items-center gap-8 whitespace-nowrap">
              {TICKER_COMMODITIES.map((item, idx) => (
                <div key={idx} className="inline-flex items-center gap-2 text-emerald-100/90 text-xs">
                  <span className="font-semibold text-white">{item.crop}</span>
                  <span className="text-emerald-400">₹{item.price.toLocaleString('en-IN')}/qtl</span>
                  <span className="text-[10px] text-emerald-300/80">({item.market})</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                    item.trend === 'up' ? 'bg-emerald-900/90 text-emerald-300' : 'bg-amber-900/90 text-amber-300'
                  }`}>
                    {item.change}
                  </span>
                  <span className="text-emerald-700 mx-2">•</span>
                </div>
              ))}
              {/* Duplicate for infinite loop */}
              {TICKER_COMMODITIES.map((item, idx) => (
                <div key={`dup-${idx}`} className="inline-flex items-center gap-2 text-emerald-100/90 text-xs">
                  <span className="font-semibold text-white">{item.crop}</span>
                  <span className="text-emerald-400">₹{item.price.toLocaleString('en-IN')}/qtl</span>
                  <span className="text-[10px] text-emerald-300/80">({item.market})</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                    item.trend === 'up' ? 'bg-emerald-900/90 text-emerald-300' : 'bg-amber-900/90 text-amber-300'
                  }`}>
                    {item.change}
                  </span>
                  <span className="text-emerald-700 mx-2">•</span>
                </div>
              ))}
            </div>
          </div>
          <Link to="/prices" className="hidden sm:flex items-center gap-1 text-[11px] text-emerald-300 hover:text-white font-medium whitespace-nowrap transition-colors">
            {t('prices') || 'All Mandis'} <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. HERO SECTION — THE MODERN FARMGATE EXCHANGE                */}
      {/* ------------------------------------------------------------- */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#0B2E1D] via-[#0E3D27] to-[#144D32] text-white pt-16 pb-24 px-4 sm:px-6 lg:px-8">
        {/* Interactive 3D Digital Agri-Grid Constellation Canvas */}
        <ConstellationCanvas />

        {/* Decorative background visual orbs */}
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-amber-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-[#FAF9F5] to-transparent pointer-events-none" />

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Content Column */}
            <div className="lg:col-span-7 text-center lg:text-left space-y-6">
              
              {/* Badge */}
              <div className="inline-flex items-center gap-2.5 bg-emerald-800/60 border border-emerald-500/30 rounded-full px-4 py-1.5 text-xs font-semibold text-emerald-200 backdrop-blur-md shadow-sm">
                <Sprout className="w-4 h-4 text-emerald-400" />
                <span>The Direct Farmgate Exchange · थेट शेतमाल खरेदी-विक्री</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-balance leading-[1.15]">
                Sell Your Harvest <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-300 via-yellow-200 to-amber-300">Directly to Verified Buyers</span> at Real Mandi Rates.
              </h1>

              {/* Vernacular & Plain Description */}
              <p className="text-base sm:text-lg text-emerald-100/90 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-normal">
                Eliminate village middlemen, uncalibrated scale deductions, and payment delays. Connect directly with institutional food processors, supermarket chains, and wholesale traders with certified quality testing and instant direct bank settlement.
              </p>

              {/* Dual Primary Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row items-stretch justify-center lg:justify-start gap-4">
                <Link
                  to="/register?role=farmer"
                  className="inline-flex items-center justify-center gap-3 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-bold text-base px-8 py-4 rounded-2xl shadow-lg shadow-emerald-950/40 hover:shadow-emerald-900/60 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  <Tractor className="w-5 h-5 text-emerald-100" />
                  <span>I Am a Farmer — Sell My Harvest</span>
                  <ArrowRight className="w-4 h-4 text-emerald-200" />
                </Link>

                <Link
                  to="/register?role=buyer"
                  className="inline-flex items-center justify-center gap-3 bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-base px-7 py-4 rounded-2xl backdrop-blur-md transition-all transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  <ShoppingBag className="w-5 h-5 text-amber-300" />
                  <span>I Am a Buyer — Source Verified Lots</span>
                </Link>
              </div>

              {/* Quick Trust Highlights */}
              <div className="pt-4 grid grid-cols-3 gap-3 border-t border-emerald-700/40 text-xs text-emerald-200/90">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>₹0 Commission for Farmers</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Direct Bank Payouts</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Digital Certified Weighment</span>
                </div>
              </div>

            </div>

            {/* Right Visual Card Showcase with 3D Depth & Glare */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none perspective-1000">
                <Tilt3DCard className="rounded-3xl shadow-2xl border border-emerald-400/30 bg-emerald-950/70 backdrop-blur-xl overflow-hidden">
                  
                  {/* Hero Farmer 8k Photorealistic Photograph */}
                  <div className="relative h-80 sm:h-96 w-full overflow-hidden">
                    <img
                      src="/images/hero-farmer-modern.jpg"
                      alt="Indian Farmer in lush agricultural field with smartphone"
                      className="w-full h-full object-cover object-top transform hover:scale-105 transition-transform duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-emerald-950 via-emerald-950/30 to-transparent" />
                  </div>

                  {/* Floating Interactive 3D Badge 1: Real Incoming Buyer Offer */}
                  <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-md p-3.5 rounded-2xl shadow-xl border border-gray-100 max-w-[240px] text-gray-900 animate-float-3d translate-z-30">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                      <p className="text-[11px] font-bold uppercase tracking-wider text-green-700">Verified Buyer Offer</p>
                    </div>
                    <p className="text-xs font-bold text-gray-800 leading-snug">Haldiram Foods Ltd</p>
                    <p className="text-sm font-extrabold text-emerald-800 mt-0.5">₹2,450 <span className="text-[11px] font-normal text-gray-500">/ quintal</span></p>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-gray-500 pt-1.5 border-t border-gray-100">
                      <span>200 QTL Onion</span>
                      <span className="font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">Ready to Accept</span>
                    </div>
                  </div>

                  {/* Floating 3D Badge 2: Direct Bank Settlement Receipt */}
                  <div className="absolute -bottom-1 -left-1 bg-emerald-950/95 backdrop-blur-md p-4 rounded-2xl shadow-2xl border border-emerald-400/40 max-w-[280px] text-white animate-float-3d-reverse translate-z-40">
                    <div className="flex items-center gap-2 mb-1">
                      <Wallet className="w-4 h-4 text-emerald-400" />
                      <span className="text-[11px] font-bold text-emerald-300 uppercase">100% Direct Bank Settlement</span>
                    </div>
                    <p className="text-xl font-black text-white">₹4,90,000</p>
                    <p className="text-[11px] text-emerald-200/80 mt-0.5">Credited via Direct NEFT/RTGS</p>
                    <div className="mt-2 flex items-center gap-1.5 text-[10px] bg-emerald-900/80 px-2 py-1 rounded-lg text-emerald-300 font-mono">
                      <span>UTR: KL-NEFT-92041</span>
                      <Check className="w-3 h-3 text-emerald-400 ml-auto" />
                    </div>
                  </div>

                </Tilt3DCard>

                {/* Background 3D Radial Glow */}
                <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/25 via-yellow-300/15 to-amber-500/25 rounded-3xl blur-2xl -z-10 animate-pulse-glow" />
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 3. CONTINUOUS SCROLLING CROP MARQUEE                          */}
      {/* ------------------------------------------------------------- */}
      <section className="py-12 bg-white border-y border-gray-200/70 overflow-hidden relative">
        <div className="max-w-7xl mx-auto px-4 mb-6 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold tracking-widest text-emerald-700 uppercase">Commodity Coverage</span>
            <h2 className="text-xl sm:text-2xl font-black text-gray-900 mt-0.5">Live Mandi Benchmarks Across Maharashtra & India</h2>
          </div>
          <Link to="/prices" className="text-xs font-bold text-emerald-700 hover:text-emerald-900 flex items-center gap-1">
            View Live Rate Board <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Marquee Track (Smooth Continuous Loop) */}
        <div className="relative w-full overflow-hidden">
          <div className="animate-marquee flex items-center gap-5">
            {CROPS_METADATA.map((crop) => (
              <Link
                key={crop.id}
                to={`/prices?crop=${crop.name}`}
                className="group flex-shrink-0 w-64 bg-white hover:bg-emerald-50/50 rounded-2xl p-3.5 border border-gray-200/80 hover:border-emerald-300 shadow-sm hover:shadow-md transition-all flex items-center gap-3.5"
              >
                <img
                  src={crop.localImage || getCropImage(crop.name)}
                  alt={crop.name}
                  className="w-14 h-14 rounded-xl object-cover border border-gray-100 flex-shrink-0 group-hover:scale-105 transition-transform"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-sm text-gray-900 truncate">{crop.name}</p>
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                      {crop.commonNames?.mr || crop.commonNames?.hi || ''}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-emerald-800 mt-1">
                    ₹{crop.typicalPriceRange ? crop.typicalPriceRange[1].toLocaleString('en-IN') : '2,400'}
                    <span className="text-[10px] text-gray-400 font-normal"> / qtl</span>
                  </p>
                  <p className="text-[10px] text-gray-500 mt-0.5 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3 text-emerald-600" />
                    <span>APMC Verified</span>
                  </p>
                </div>
              </Link>
            ))}

            {/* Duplicate for infinite loop */}
            {CROPS_METADATA.map((crop) => (
              <Link
                key={`dup-${crop.id}`}
                to={`/prices?crop=${crop.name}`}
                className="group flex-shrink-0 w-64 bg-white hover:bg-emerald-50/50 rounded-2xl p-3.5 border border-gray-200/80 hover:border-emerald-300 shadow-sm hover:shadow-md transition-all flex items-center gap-3.5"
              >
                <img
                  src={crop.localImage || getCropImage(crop.name)}
                  alt={crop.name}
                  className="w-14 h-14 rounded-xl object-cover border border-gray-100 flex-shrink-0 group-hover:scale-105 transition-transform"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-sm text-gray-900 truncate">{crop.name}</p>
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                      {crop.commonNames?.mr || crop.commonNames?.hi || ''}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-emerald-800 mt-1">
                    ₹{crop.typicalPriceRange ? crop.typicalPriceRange[1].toLocaleString('en-IN') : '2,400'}
                    <span className="text-[10px] text-gray-400 font-normal"> / qtl</span>
                  </p>
                  <p className="text-[10px] text-gray-500 mt-0.5 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3 text-emerald-600" />
                    <span>APMC Verified</span>
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 4. INTERACTIVE 5-STEP TRADE LIFECYCLE SIMULATOR                */}
      {/* (Solves the #how-it-works link and replaces dense text!)       */}
      {/* ------------------------------------------------------------- */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 bg-[#F4F1EA] scroll-mt-16">
        <div className="max-w-7xl mx-auto">
          
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="inline-flex items-center gap-1.5 bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider mb-3">
              <Handshake className="w-3.5 h-3.5 text-emerald-700" />
              Complete Lifecycle · संपूर्ण व्यापार प्रक्रिया
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
              How KrishiLink Works: Farmgate to Bank Settlement
            </h2>
            <p className="text-gray-600 mt-3 text-base">
              A transparent, end-to-end electronic marketplace built to eliminate middleman margins and secure direct bank payments for farmers.
            </p>
          </div>

          {/* 5-Step Interactive Tabs */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-3 mb-8">
            {LIFECYCLE_STEPS.map((step) => {
              const Icon = step.icon;
              const isCurrent = activeStep === step.id;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`flex flex-col items-center sm:items-start text-left p-4 rounded-2xl border transition-all ${
                    isCurrent
                      ? 'bg-white border-emerald-600 shadow-md ring-2 ring-emerald-500/30'
                      : 'bg-white/60 hover:bg-white border-gray-200/80 text-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <span className={`text-xs font-black px-2 py-0.5 rounded-full ${
                      isCurrent ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {step.stepNum}
                    </span>
                    <Icon className={`w-5 h-5 ${isCurrent ? 'text-emerald-700' : 'text-gray-400'}`} />
                  </div>
                  <p className={`text-xs font-bold line-clamp-1 ${isCurrent ? 'text-gray-900' : 'text-gray-700'}`}>
                    {step.title}
                  </p>
                  <p className="text-[10px] text-gray-400 mt-0.5 hidden sm:block truncate">
                    {step.badge}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Interactive Step Showcase Card */}
          <div className="bg-white rounded-3xl shadow-xl border border-gray-200/80 p-6 sm:p-10">
            <div className="grid lg:grid-cols-12 gap-8 items-center">
              
              {/* Left explanation */}
              <div className="lg:col-span-6 space-y-4">
                <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full">
                  <span>Step {currentStepData.stepNum} of 05</span>
                  <span>•</span>
                  <span>{currentStepData.tagline}</span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-black text-gray-900 leading-tight">
                  {currentStepData.title}
                </h3>

                <p className="text-gray-600 text-base leading-relaxed">
                  {currentStepData.description}
                </p>

                <div className="pt-2 flex items-center gap-4">
                  <div className="bg-emerald-50 rounded-xl px-4 py-2.5 border border-emerald-100">
                    <p className="text-[10px] uppercase font-bold text-emerald-700">Guarantee</p>
                    <p className="text-sm font-extrabold text-emerald-900 mt-0.5">{currentStepData.metric}</p>
                  </div>
                  <div className="bg-amber-50 rounded-xl px-4 py-2.5 border border-amber-100">
                    <p className="text-[10px] uppercase font-bold text-amber-700">Audit Provenance</p>
                    <p className="text-sm font-extrabold text-amber-900 mt-0.5">SHA-256 Verified</p>
                  </div>
                </div>

                <div className="pt-4 flex items-center gap-3">
                  <button
                    onClick={() => setActiveStep(prev => (prev % 5) + 1)}
                    className="btn-primary text-sm inline-flex items-center gap-2"
                  >
                    <span>Next Step: Step {(activeStep % 5) + 1}</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                  <Link to="/register" className="text-xs font-bold text-emerald-800 hover:underline">
                    Get Started Now →
                  </Link>
                </div>
              </div>

              {/* Right: High-Grade 3D & Photorealistic Simulator Visual */}
              <div className="lg:col-span-6 h-full min-h-[360px] flex items-center justify-center">
                {activeStep === 1 && <Step1Visual t={t} />}
                {activeStep === 2 && <Step2Visual t={t} />}
                {activeStep === 3 && <Step3Visual t={t} />}
                {activeStep === 4 && <Step4Visual t={t} />}
                {activeStep === 5 && <Step5Visual t={t} />}
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 5. INTERACTIVE AGRICULTURAL REALIZATION CALCULATOR            */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white border-t border-gray-200/80">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="inline-flex items-center gap-1.5 bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider mb-2">
              <Calculator className="w-3.5 h-3.5 text-amber-700" />
              Financial Advantage Calculator · नफा कॅल्क्युलेटर
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
              See How Much Extra You Earn with KrishiLink
            </h2>
            <p className="text-gray-600 mt-2 text-base">
              Calculate your take-home difference by eliminating village agent commissions and uncalibrated weighment deductions.
            </p>
          </div>

          <div className="bg-gradient-to-br from-emerald-950 to-green-900 text-white rounded-3xl p-6 sm:p-10 shadow-2xl border border-emerald-800">
            <div className="grid lg:grid-cols-12 gap-8 items-center">
              
              {/* Controls Column */}
              <div className="lg:col-span-6 space-y-6">
                
                {/* Crop Selection */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-emerald-300 mb-2">
                    Select Your Crop / शेतमाल निवडा:
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {['Onion', 'Tomato', 'Soybean', 'Cotton', 'Wheat'].map((c) => (
                      <button
                        key={c}
                        onClick={() => setSelectedCalcCrop(c)}
                        className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                          selectedCalcCrop === c
                            ? 'bg-amber-400 text-emerald-950 shadow-md scale-105'
                            : 'bg-emerald-900/80 hover:bg-emerald-800 text-emerald-100 border border-emerald-700/60'
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Volume Slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                      Harvest Quantity (Quintals / क्विंटल):
                    </label>
                    <span className="text-xl font-extrabold text-amber-300 font-mono">
                      {calcQuintals} QTL
                    </span>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="500"
                    step="10"
                    value={calcQuintals}
                    onChange={(e) => setCalcQuintals(Number(e.target.value))}
                    className="w-full h-3 bg-emerald-900 rounded-lg appearance-none cursor-pointer accent-amber-400"
                  />
                  <div className="flex justify-between text-[10px] text-emerald-400 font-mono mt-1">
                    <span>20 QTL</span>
                    <span>100 QTL</span>
                    <span>250 QTL</span>
                    <span>500 QTL</span>
                  </div>
                </div>

                {/* Pricing Reference info */}
                <div className="bg-emerald-900/60 rounded-2xl p-4 border border-emerald-700/50 text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-emerald-300">KrishiLink Direct Buyer Benchmark:</span>
                    <span className="font-bold text-white">₹{calcData.directRate.toLocaleString('en-IN')}/qtl</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-emerald-300">Traditional Village Middleman Rate:</span>
                    <span className="font-bold text-gray-300">₹{calcData.mandiRate.toLocaleString('en-IN')}/qtl</span>
                  </div>
                </div>

              </div>

              {/* Realization Comparison Column */}
              <div className="lg:col-span-6 space-y-4">
                
                {/* Comparison Card */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/15 space-y-4">
                  
                  {/* Traditional Middleman */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/10 text-sm">
                    <div>
                      <p className="text-gray-300 text-xs">Traditional Middleman Net</p>
                      <p className="text-xs text-red-300 mt-0.5">Deducts 8% comm. + 3% scale cuts</p>
                    </div>
                    <span className="font-bold text-lg text-gray-300">
                      ₹{calcData.middlemanNet.toLocaleString('en-IN')}
                    </span>
                  </div>

                  {/* KrishiLink Direct */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/10 text-sm">
                    <div>
                      <p className="text-emerald-200 text-xs font-bold">KrishiLink Direct Bank Payout</p>
                      <p className="text-xs text-emerald-300 mt-0.5">₹0 commission + 100% digital scale</p>
                    </div>
                    <span className="font-extrabold text-2xl text-emerald-300">
                      ₹{calcData.grossDirect.toLocaleString('en-IN')}
                    </span>
                  </div>

                  {/* Extra Take-Home Highlight Banner */}
                  <div className="bg-gradient-to-r from-amber-400 to-yellow-300 text-emerald-950 rounded-xl p-4 shadow-lg flex items-center justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-wider">Your Extra Profit Advantage</p>
                      <p className="text-2xl sm:text-3xl font-black mt-0.5">
                        +₹{calcData.extraEarnings.toLocaleString('en-IN')}
                      </p>
                    </div>
                    <Link
                      to="/sell"
                      className="bg-emerald-950 hover:bg-emerald-900 text-white font-bold text-xs px-4 py-3 rounded-xl transition-colors whitespace-nowrap"
                    >
                      Sell at this rate →
                    </Link>
                  </div>

                </div>

              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 6. INTERACTIVE ROLE WORKSPACE COCKPITS                         */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-[#FAF9F5]">
        <div className="max-w-7xl mx-auto">
          
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="inline-flex items-center gap-1.5 bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider mb-2">
              <Layers className="w-3.5 h-3.5 text-blue-700" />
              Tailored Cockpits for Every Participant
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
              One Unified Exchange. Three Dedicated Workspaces.
            </h2>
            <p className="text-gray-600 mt-2 text-base">
              Whether you are an individual farmer, an institutional buyer, or an FPO cooperative, KrishiLink provides dedicated tools designed for your workflow.
            </p>
          </div>

          {/* Role Tab Selector */}
          <div className="flex justify-center mb-8">
            <div className="bg-gray-200/80 p-1.5 rounded-2xl inline-flex gap-2">
              <button
                onClick={() => setActiveRoleTab('farmer')}
                className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${
                  activeRoleTab === 'farmer'
                    ? 'bg-emerald-800 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Tractor className="w-4 h-4" />
                <span>Farmer Cockpit</span>
              </button>
              <button
                onClick={() => setActiveRoleTab('buyer')}
                className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${
                  activeRoleTab === 'buyer'
                    ? 'bg-blue-800 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <ShoppingBag className="w-4 h-4" />
                <span>Buyer Procurement</span>
              </button>
              <button
                onClick={() => setActiveRoleTab('fpo')}
                className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${
                  activeRoleTab === 'fpo'
                    ? 'bg-purple-800 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Boxes className="w-4 h-4" />
                <span>FPO Aggregator</span>
              </button>
            </div>
          </div>

          {/* Role Feature Showcase */}
          <div className="bg-white rounded-3xl p-8 sm:p-10 shadow-lg border border-gray-200/80">
            {activeRoleTab === 'farmer' && (
              <div className="grid lg:grid-cols-12 gap-8 items-center">
                <div className="lg:col-span-6 space-y-4">
                  <span className="badge-green text-xs">For Smallholders & Growers</span>
                  <h3 className="text-2xl sm:text-3xl font-black text-gray-900">
                    Farmgate Sales with Full Price Sovereignty
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Set your own reserve prices with live Agmarknet rate intelligence. Receive WhatsApp-style offers from verified buyers across India and get paid directly to your bank account with complete weighment integrity.
                  </p>
                  <ul className="space-y-2.5 text-sm text-gray-700 pt-2">
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>60-second crop listing with photo upload & quality declaration</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>WhatsApp-style offer cards: Accept, Negotiate or Decline</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>Direct bank payment with NEFT/RTGS transaction voucher</span>
                    </li>
                  </ul>
                  <div className="pt-4">
                    <Link to="/register?role=farmer" className="btn-primary inline-flex items-center gap-2">
                      <span>Create Free Farmer Account</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
                <div className="lg:col-span-6">
                  <div className="bg-emerald-950 text-white p-6 rounded-2xl shadow-xl border border-emerald-800 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-emerald-800 text-xs">
                      <span className="text-emerald-300 font-bold">FARMER DASHBOARD PREVIEW</span>
                      <span className="bg-emerald-800 px-2 py-0.5 rounded text-[10px]">VERIFIED</span>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl space-y-2">
                      <p className="text-xs text-gray-300">Incoming Buyer Offer</p>
                      <p className="text-lg font-bold text-white">Vashi APMC Wholesale Corp</p>
                      <p className="text-emerald-400 font-extrabold text-xl">₹2,450 / qtl · 150 QTL</p>
                      <div className="flex gap-2 pt-2">
                        <button className="bg-emerald-500 text-white font-bold text-xs px-4 py-2 rounded-lg">Accept Offer</button>
                        <button className="bg-white/20 text-white font-bold text-xs px-4 py-2 rounded-lg">Negotiate Rate</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeRoleTab === 'buyer' && (
              <div className="grid lg:grid-cols-12 gap-8 items-center">
                <div className="lg:col-span-6 space-y-4">
                  <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full">
                    For Processors, Retailers & Exporters
                  </span>
                  <h3 className="text-2xl sm:text-3xl font-black text-gray-900">
                    Direct Farmgate Sourcing at Scale
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Post structured procurement requirements with technical quality specifications (moisture, foreign matter, sizing). Automatically match and aggregate multi-lot farmgate supply with transparent landed cost freight.
                  </p>
                  <ul className="space-y-2.5 text-sm text-gray-700 pt-2">
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span>Post procurement demands with custom quality thresholds</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span>Multi-lot supply assembly with explainable greedy matching</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <span>Digital Trade Passport with immutable SHA-256 batch provenance</span>
                    </li>
                  </ul>
                  <div className="pt-4">
                    <Link to="/register?role=buyer" className="btn-secondary inline-flex items-center gap-2 !border-blue-700 !text-blue-700 hover:!bg-blue-50">
                      <span>Start Sourcing as Buyer</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
                <div className="lg:col-span-6">
                  <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-xl border border-slate-700 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-700 text-xs">
                      <span className="text-blue-300 font-bold">PROCUREMENT COCKPIT PREVIEW</span>
                      <span className="bg-blue-900 px-2 py-0.5 rounded text-[10px]">INSTITUTIONAL</span>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl space-y-2">
                      <p className="text-xs text-gray-300">Procurement Requirement #REQ-104</p>
                      <p className="text-lg font-bold text-white">500 QTL Soybean (Soyabean)</p>
                      <p className="text-blue-300 font-bold text-sm">Matched 4 Farmer Lots (100% Feasible Coverage)</p>
                      <div className="pt-2 text-xs text-gray-300 flex justify-between">
                        <span>Landed Freight: ₹85/qtl</span>
                        <span className="font-bold text-emerald-400">Total: ₹21,75,000</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeRoleTab === 'fpo' && (
              <div className="grid lg:grid-cols-12 gap-8 items-center">
                <div className="lg:col-span-6 space-y-4">
                  <span className="inline-flex items-center gap-1 bg-purple-100 text-purple-800 text-xs font-bold px-2.5 py-1 rounded-full">
                    For Farmer Collectives & FPOs
                  </span>
                  <h3 className="text-2xl sm:text-3xl font-black text-gray-900">
                    Bulk Aggregation & Traceable Member Payouts
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Aggregate smallholder member harvests into commercial trade batches. Sell directly to institutional buyers and automate member payment disbursals with individual bank receipts.
                  </p>
                  <ul className="space-y-2.5 text-sm text-gray-700 pt-2">
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <span>Member intake ledger with gross/tare weighment and grade tags</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <span>Single-inventory chain preventing double-allocation of member lots</span>
                    </li>
                    <li className="flex items-center gap-2.5 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <span>Automated financial reconciliation and individual member payouts</span>
                    </li>
                  </ul>
                  <div className="pt-4">
                    <Link to="/register?role=fpo" className="btn-secondary inline-flex items-center gap-2 !border-purple-700 !text-purple-700 hover:!bg-purple-50">
                      <span>Register FPO Collective</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
                <div className="lg:col-span-6">
                  <div className="bg-purple-950 text-white p-6 rounded-2xl shadow-xl border border-purple-800 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-purple-800 text-xs">
                      <span className="text-purple-300 font-bold">FPO HUB PREVIEW</span>
                      <span className="bg-purple-800 px-2 py-0.5 rounded text-[10px]">COLLECTIVE</span>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl space-y-2">
                      <p className="text-xs text-gray-300">Nashik Agro Producer Co. (120 Members)</p>
                      <p className="text-lg font-bold text-white">Aggregated Lot: 850 QTL Onion</p>
                      <p className="text-purple-300 text-xs">Ready for Institutional Dispatch</p>
                      <div className="pt-2 text-xs text-gray-300 flex justify-between">
                        <span>Reconciled Disbursals: ₹18,40,000</span>
                        <span className="font-bold text-emerald-400">42 Members Credited</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>
      </section>



      {/* ------------------------------------------------------------- */}
      {/* 7. TRUST, SECURITY & STATUTORY COMPLIANCE                     */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white border-t border-gray-200/80">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">Statutory Architecture</span>
            <h2 className="text-2xl sm:text-3xl font-black text-gray-900 mt-1">Built on Integrity & Statutory Standards</h2>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <p className="font-bold text-sm text-gray-900">DPDP Act 2023 Compliant</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                Smallholder privacy protection. Driver and counterparty contacts masked until bilateral transaction confirmation.
              </p>
            </div>

            <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mb-3">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <p className="font-bold text-sm text-gray-900">SHA-256 Provenance</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                Weighbridge slips, moisture assays, and Digital Trade Passports cryptographically sealed against retrospective tampering.
              </p>
            </div>

            <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center mb-3">
                <Wallet className="w-5 h-5" />
              </div>
              <p className="font-bold text-sm text-gray-900">Non-Custodial Payments</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                Direct buyer-to-seller settlement via regulated banking rails (NEFT, RTGS, UPI) with verifiable UTR bank vouchers.
              </p>
            </div>

            <div className="p-5 rounded-2xl border border-gray-100 bg-gray-50/50 hover:bg-white hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center mb-3">
                <Radio className="w-5 h-5" />
              </div>
              <p className="font-bold text-sm text-gray-900">Official Agmarknet Rates</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                Live arrival observations ingested directly from data.gov.in (Ministry of Agriculture) for honest price intelligence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 8. HIGH-IMPACT CLOSING CTA                                    */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-emerald-900 via-green-900 to-emerald-950 text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="max-w-4xl mx-auto text-center relative z-10 space-y-6">
          <span className="badge-green text-xs bg-emerald-800 text-emerald-200 border border-emerald-700">
            Join 10,000+ Verified Farmers & Buyers
          </span>
          
          <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-balance">
            Ready to Experience Transparent Agricultural Trading?
          </h2>
          
          <p className="text-emerald-100/90 text-base sm:text-lg max-w-2xl mx-auto">
            Sign up in 2 minutes. List produce for free, view verified live market arrivals, or submit your procurement requirements.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/register?role=farmer"
              className="w-full sm:w-auto btn-accent !bg-amber-400 hover:!bg-amber-500 !text-emerald-950 font-black text-base px-8 py-4 rounded-2xl shadow-xl flex items-center justify-center gap-2"
            >
              <Tractor className="w-5 h-5" />
              <span>Join as a Farmer</span>
            </Link>
            
            <Link
              to="/register?role=buyer"
              className="w-full sm:w-auto bg-white/10 hover:bg-white/20 border border-white/30 text-white font-bold text-base px-8 py-4 rounded-2xl backdrop-blur-md flex items-center justify-center gap-2 transition-all"
            >
              <ShoppingBag className="w-5 h-5" />
              <span>Join as an Institutional Buyer</span>
            </Link>
          </div>

          <div className="pt-4 flex items-center justify-center gap-6 text-xs text-emerald-200/80">
            <Link to="/help" className="flex items-center gap-1.5 hover:text-white underline">
              <HelpCircle className="w-4 h-4" />
              <span>24/7 Farmer Help & Guides</span>
            </Link>
            <span>•</span>
            <Link to="/terms" className="hover:text-white underline">
              Electronic Facilitator Terms
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
