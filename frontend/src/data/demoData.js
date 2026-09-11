// =============================================================
// KrishiLink Demo Data (Frontend)
// All realistic Indian agricultural data used when backend is unavailable
// =============================================================

// Helper to get a date string N days ago
const daysAgo = (n) => {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
};

// =============================================================
// PRICE DATA
// Realistic prices in INR per quintal (calibrated to live Agmarknet benchmark data)
// =============================================================
export const DEMO_PRICES = [
  // Onion
  { id: 1, crop: 'Onion',   market: 'Lasalgaon',   modal_price: 6125, min_price: 5700, max_price: 6550, change_pct: 3.2,  trend: 'RISING',  volume: 680 },
  { id: 2, crop: 'Onion',   market: 'Nashik',      modal_price: 6250, min_price: 5800, max_price: 6680, change_pct: 2.5,  trend: 'RISING',  volume: 420 },
  { id: 3, crop: 'Onion',   market: 'Pune',        modal_price: 6500, min_price: 6050, max_price: 6950, change_pct: 1.8,  trend: 'STABLE',  volume: 310 },
  { id: 4, crop: 'Onion',   market: 'Mumbai',      modal_price: 6750, min_price: 6280, max_price: 7220, change_pct: 2.1,  trend: 'RISING',  volume: 510 },
  // Tomato
  { id: 5, crop: 'Tomato',  market: 'Lasalgaon',   modal_price: 2420, min_price: 2250, max_price: 2590, change_pct: 4.1,  trend: 'RISING',  volume: 240 },
  { id: 6, crop: 'Tomato',  market: 'Nashik',      modal_price: 2470, min_price: 2300, max_price: 2640, change_pct: 3.5,  trend: 'RISING',  volume: 280 },
  { id: 7, crop: 'Tomato',  market: 'Pune',        modal_price: 2570, min_price: 2390, max_price: 2750, change_pct: 1.9,  trend: 'STABLE',  volume: 350 },
  // Soybean
  { id: 8, crop: 'Soybean', market: 'Nashik',      modal_price: 9020, min_price: 8390, max_price: 9650, change_pct: 1.2,  trend: 'STABLE',  volume: 520 },
  { id: 9, crop: 'Soybean', market: 'Aurangabad',  modal_price: 8930, min_price: 8300, max_price: 9550, change_pct: 1.5,  trend: 'STABLE',  volume: 780 },
  // Cotton
  { id: 10, crop: 'Cotton', market: 'Nashik',      modal_price: 7650, min_price: 7110, max_price: 8180, change_pct: 2.1,  trend: 'RISING',  volume: 310 },
  { id: 11, crop: 'Cotton', market: 'Aurangabad',  modal_price: 7570, min_price: 7040, max_price: 8100, change_pct: 1.8,  trend: 'STABLE',  volume: 450 },
  // Wheat
  { id: 12, crop: 'Wheat',  market: 'Pune',        modal_price: 2630, min_price: 2450, max_price: 2810, change_pct: 0.8,  trend: 'STABLE',  volume: 890 },
  { id: 13, crop: 'Wheat',  market: 'Nashik',      modal_price: 2530, min_price: 2350, max_price: 2710, change_pct: 1.1,  trend: 'STABLE',  volume: 640 },
  // Potato
  { id: 14, crop: 'Potato', market: 'Pune',        modal_price: 3440, min_price: 3200, max_price: 3680, change_pct: 2.4,  trend: 'RISING',  volume: 410 },
  { id: 15, crop: 'Potato', market: 'Nashik',      modal_price: 3310, min_price: 3080, max_price: 3540, change_pct: 1.9,  trend: 'STABLE',  volume: 380 },
  // Chilli
  { id: 16, crop: 'Chilli', market: 'Nashik',      modal_price: 4640, min_price: 4315, max_price: 4965, change_pct: -1.2, trend: 'STABLE',  volume: 180 },
  // Rice
  { id: 17, crop: 'Rice',   market: 'Pune',        modal_price: 2800, min_price: 2600, max_price: 3000, change_pct: 1.4,  trend: 'STABLE',  volume: 520 },
];

// =============================================================
// PRICE HISTORY (15 days, for chart across all 8 crops & markets)
// =============================================================
const BENCHMARKS = {
  Onion: 6050,
  Tomato: 2450,
  Soybean: 8050,
  Soyabean: 8050,
  Cotton: 7850,
  Wheat: 2540,
  Potato: 3250,
  Chilli: 4720,
  Rice: 2700,
};

const MARKET_FACTORS = {
  Mumbai: 1.08,
  Pune: 1.04,
  Nashik: 1.00,
  Lasalgaon: 0.98,
  Ahmednagar: 0.97,
  Aurangabad: 0.99,
  Solapur: 0.96,
  Nagpur: 1.01,
  All: 1.00,
};

export const DEMO_PRICE_HISTORY = {};
const TARGET_CROPS_LIST = ['Onion', 'Tomato', 'Soybean', 'Soyabean', 'Cotton', 'Wheat', 'Potato', 'Chilli', 'Rice'];
const TARGET_MARKETS_LIST = ['All', 'Lasalgaon', 'Nashik', 'Pune', 'Mumbai', 'Ahmednagar', 'Solapur', 'Aurangabad', 'Nagpur'];

TARGET_CROPS_LIST.forEach(crop => {
  DEMO_PRICE_HISTORY[crop] = {};
  const baseRate = BENCHMARKS[crop] || 2500;
  TARGET_MARKETS_LIST.forEach(market => {
    const factor = MARKET_FACTORS[market] || 1.0;
    const targetPrice = Math.round(baseRate * factor);
    let prevModal = null;
    DEMO_PRICE_HISTORY[crop][market] = Array.from({ length: 15 }, (_, i) => {
      const daysFromToday = 14 - i;
      const h = Math.abs(Math.sin(crop.length * 37 + market.length * 19 + (i + 1) * 73.13)) * 10000;
      const jitter = ((h % 41) - 20) / 1000.0;
      const trend = daysFromToday > 0 ? (1.0 - (daysFromToday * 0.0025) + jitter) : 1.0;
      let modal = Math.round(targetPrice * trend);
      if (daysFromToday > 0 && prevModal !== null && modal === prevModal) {
        modal += (i % 2 === 0 ? 18 : -18);
      }
      prevModal = modal;
      return {
        date: daysAgo(daysFromToday),
        price: modal,
        modal_price: modal,
        min_price: Math.round(modal * 0.93),
        max_price: Math.round(modal * 1.07),
        market: market === 'All' ? 'All Mandis (Average)' : `${market} APMC`,
      };
    });
    if (market !== 'All') {
      DEMO_PRICE_HISTORY[crop][`${market} APMC`] = DEMO_PRICE_HISTORY[crop][market];
    }
  });
});


// =============================================================
// BUYERS
// =============================================================
export const DEMO_BUYERS = [
  {
    id: 'b1',
    name: 'Mehta Traders Pvt Ltd',
    type: 'Trader',
    crops: ['Onion', 'Tomato'],
    min_qty: 50,
    max_qty: 500,
    location: 'Nashik',
    distance_km: 12,
    verified: true,
    rating: 4.5,
    reviews: 48,
    offer_price: 1800,
  },
  {
    id: 'b2',
    name: 'Pune Agro Exports',
    type: 'Exporter',
    crops: ['Onion', 'Soybean'],
    min_qty: 200,
    max_qty: 2000,
    location: 'Pune',
    distance_km: 45,
    verified: true,
    rating: 4.8,
    reviews: 112,
    offer_price: 1870,
  },
  {
    id: 'b3',
    name: 'FreshMart Retail Chain',
    type: 'Retailer',
    crops: ['Tomato', 'Potato', 'Onion'],
    min_qty: 10,
    max_qty: 100,
    location: 'Mumbai',
    distance_km: 165,
    verified: true,
    rating: 4.2,
    reviews: 31,
    offer_price: 1750,
  },
  {
    id: 'b4',
    name: 'Maharashtra Cotton Corp',
    type: 'Processor',
    crops: ['Cotton'],
    min_qty: 100,
    max_qty: 1000,
    location: 'Aurangabad',
    distance_km: 120,
    verified: false,
    rating: 3.9,
    reviews: 17,
    offer_price: 6900,
  },
];

// =============================================================
// LOTS (produce listings)
// =============================================================
export const DEMO_LOTS = [
  {
    id: 'l1',
    farmer: 'Ramesh Patil',
    crop: 'Onion',
    quantity: 500,
    unit: 'quintal',
    grade: 'A',
    location: 'Lasalgaon',
    expected_price: 1800,
    available_date: daysAgo(-4),
    status: 'active',
    created_at: daysAgo(1),
  },
  {
    id: 'l2',
    farmer: 'Sunita Deshpande',
    crop: 'Tomato',
    quantity: 200,
    unit: 'quintal',
    grade: 'A',
    location: 'Pune',
    expected_price: 1200,
    available_date: daysAgo(-2),
    status: 'matched',
    created_at: daysAgo(3),
  },
  {
    id: 'l3',
    farmer: 'Nashik Farmer Collective FPO',
    crop: 'Onion',
    quantity: 1200,
    unit: 'quintal',
    grade: 'A',
    location: 'Nashik',
    expected_price: 1850,
    available_date: daysAgo(-5),
    status: 'active',
    created_at: daysAgo(2),
  },
];

// =============================================================
// OFFERS
// =============================================================
export const DEMO_OFFERS = [
  {
    id: 'o1',
    buyer: 'Mehta Traders Pvt Ltd',
    crop: 'Onion',
    quantity: 300,
    offered_price: 1780,
    total_value: 534000,
    status: 'pending',
    created_at: daysAgo(1),
    valid_until: daysAgo(-2),
    lot_id: 'l1',
  },
  {
    id: 'o2',
    buyer: 'Pune Agro Exports',
    crop: 'Onion',
    quantity: 150,
    offered_price: 1720,
    total_value: 258000,
    status: 'accepted',
    created_at: daysAgo(5),
    valid_until: daysAgo(-1),
    lot_id: 'l1',
  },
  {
    id: 'o3',
    buyer: 'FreshMart Retail Chain',
    crop: 'Tomato',
    quantity: 200,
    offered_price: 1150,
    total_value: 230000,
    status: 'pending',
    created_at: daysAgo(2),
    valid_until: daysAgo(-3),
    lot_id: 'l2',
  },
  {
    id: 'o4',
    buyer: 'Maharashtra Cotton Corp',
    crop: 'Soybean',
    quantity: 300,
    offered_price: 4450,
    total_value: 1335000,
    status: 'rejected',
    created_at: daysAgo(7),
    valid_until: daysAgo(-1),
    lot_id: 'l3',
  },
];

// =============================================================
// TRANSACTIONS
// =============================================================
export const DEMO_TRANSACTIONS = [
  {
    id: 'txn001',
    buyer: 'Pune Agro Exports',
    crop: 'Onion',
    quantity: 150,
    agreed_price: 1720,
    total_amount: 258000,
    current_stage: 'payment_received',
    payment_status: 'received',
    stages_completed: ['offer_created', 'offer_accepted', 'produce_dispatched', 'payment_pending', 'payment_received'],
    created_at: daysAgo(8),
    payment_date: daysAgo(2),
  },
  {
    id: 'txn002',
    buyer: 'FreshMart Retail Chain',
    crop: 'Tomato',
    quantity: 200,
    agreed_price: 1150,
    total_amount: 230000,
    current_stage: 'produce_dispatched',
    payment_status: 'pending',
    stages_completed: ['offer_created', 'offer_accepted', 'produce_dispatched'],
    created_at: daysAgo(4),
    dispatch_date: daysAgo(1),
  },
];

// =============================================================
// STORAGE LOCATIONS
// =============================================================
export const DEMO_STORAGE = [
  {
    id: 's1',
    name: 'Nashik Cold Storage',
    type: 'Cold Storage',
    location: 'Nashik',
    distance_km: 8,
    capacity: 500,
    available: 200,
    price_per_day: 2.50,
    lat: 19.9975,
    lng: 73.7898,
  },
  {
    id: 's2',
    name: 'Lasalgaon Agri Warehouse',
    type: 'Warehouse',
    location: 'Lasalgaon',
    distance_km: 3,
    capacity: 1000,
    available: 650,
    price_per_day: 1.20,
    lat: 20.1224,
    lng: 73.9698,
  },
  {
    id: 's3',
    name: 'Pune Agri Godown',
    type: 'Godown',
    location: 'Pune',
    distance_km: 45,
    capacity: 300,
    available: 50,
    price_per_day: 1.80,
    lat: 18.5204,
    lng: 73.8567,
  },
  {
    id: 's4',
    name: 'Ahmednagar Silo',
    type: 'Silo',
    location: 'Ahmednagar',
    distance_km: 78,
    capacity: 2000,
    available: 1200,
    price_per_day: 0.90,
    lat: 19.0948,
    lng: 74.7480,
  },
];

// =============================================================
// GRIEVANCES
// =============================================================
export const DEMO_GRIEVANCES = [
  {
    id: 'g1',
    transaction_id: 'txn002',
    issue_type: 'Payment Delay',
    description: 'Payment was expected within 3 days but has not been received after 5 days.',
    status: 'under_review',
    created_at: daysAgo(3),
  },
  {
    id: 'g2',
    transaction_id: 'txn001',
    issue_type: 'Quality Dispute',
    description: 'Buyer claims quantity received was 140 quintals. Dispatch record shows 150 quintals.',
    status: 'resolved',
    created_at: daysAgo(10),
    resolution: 'Verified with transport bill. Payment adjusted.',
  },
];

// =============================================================
// NOTIFICATIONS
// =============================================================
export const DEMO_NOTIFICATIONS = [
  {
    id: 'n1',
    type: 'price_alert',
    title: 'Onion Prices Rising',
    message: 'Onion prices in Lasalgaon are up 8.1% today. Current modal price: ₹1,920/quintal.',
    is_read: false,
    created_at: daysAgo(0),
    icon: 'TrendingUp',
  },
  {
    id: 'n2',
    type: 'new_offer',
    title: 'New Buyer Offer Received',
    message: 'Mehta Traders has made an offer of ₹1,780/quintal for your Onion lot.',
    is_read: false,
    created_at: daysAgo(1),
    icon: 'HandShake',
  },
  {
    id: 'n3',
    type: 'offer_accepted',
    title: 'Offer Accepted',
    message: 'Your offer to Pune Agro Exports for 150 quintals of Onion has been accepted.',
    is_read: true,
    created_at: daysAgo(5),
    icon: 'CheckCircle',
  },
  {
    id: 'n4',
    type: 'payment',
    title: 'Payment Received',
    message: '₹2,58,000 received from Pune Agro Exports for Transaction #txn001.',
    is_read: true,
    created_at: daysAgo(2),
    icon: 'IndianRupee',
  },
  {
    id: 'n5',
    type: 'price_alert',
    title: 'Tomato Prices Falling',
    message: 'Tomato prices in Nashik have dropped 12.3%. Consider selling soon.',
    is_read: true,
    created_at: daysAgo(1),
    icon: 'TrendingDown',
  },
];

// =============================================================
// MAP MARKERS
// =============================================================
export const DEMO_MARKERS = [
  // Mandis
  { id: 'm1', type: 'mandi', name: 'Nashik APMC',     lat: 19.9975, lng: 73.7898, info: 'Major APMC market. 40+ crops traded daily.' },
  { id: 'm2', type: 'mandi', name: 'Lasalgaon APMC',  lat: 20.1224, lng: 73.9698, info: 'Asia\'s largest onion market.' },
  { id: 'm3', type: 'mandi', name: 'Pune APMC',       lat: 18.5204, lng: 73.8567, info: 'Regional APMC market.' },
  { id: 'm4', type: 'mandi', name: 'Ahmednagar APMC', lat: 19.0948, lng: 74.7480, info: 'Local APMC market.' },
  // Buyers
  { id: 'b1', type: 'buyer', name: 'Mehta Traders',   lat: 20.0032, lng: 73.7814, info: 'Verified Trader. Onion & Tomato.' },
  { id: 'b2', type: 'buyer', name: 'Pune Agro Exports',lat: 18.5280, lng: 73.8620, info: 'Verified Exporter. Onion & Soybean.' },
  // Storage
  { id: 's1', type: 'storage', name: 'Nashik Cold Storage',    lat: 19.9840, lng: 73.7960, info: '200 tonnes available. ₹2.50/tonne/day.' },
  { id: 's2', type: 'storage', name: 'Lasalgaon Agri Warehouse',lat: 20.1180, lng: 73.9650, info: '650 tonnes available. ₹1.20/tonne/day.' },
];

// =============================================================
// DEMO USERS (for demo login)
// =============================================================
export const DEMO_USERS = {
  farmer: {
    id: 'demo-farmer',
    name: 'Ramesh Patil',
    role: 'farmer',
    location: 'Lasalgaon, Nashik',
    phone: '9876543210',
    email: 'ramesh@demo.com',
  },
  buyer: {
    id: 'demo-buyer',
    name: 'Mehta Traders',
    role: 'buyer',
    location: 'Nashik, Maharashtra',
    phone: '9987654321',
    email: 'mehta@demo.com',
  },
  fpo: {
    id: 'demo-fpo',
    name: 'Nashik Farmer Collective FPO',
    role: 'fpo',
    location: 'Nashik, Maharashtra',
    phone: '9900112233',
    email: 'fpo1@demo.com',
  },
};
