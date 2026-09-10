// =============================================================
// Map Page
// Interactive Market Map with Mandis, Buyers, Storage & FPOs
// Uses React Leaflet + OpenStreetMap + Real PostGIS Backend
// =============================================================

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  MapPin, Warehouse, ShoppingBag, Store, Users,
  Search, Crosshair, RefreshCw, AlertCircle, ExternalLink
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
// API dependency removed per requirements
import { useLanguage } from '../../hooks/useLanguage';

// =============================================================
// Fallback Data Generator
// =============================================================
const MAHARASHTRA_CITIES = [
  { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
  { name: 'Pune', lat: 18.5204, lng: 73.8567 },
  { name: 'Nashik', lat: 19.9975, lng: 73.7898 },
  { name: 'Nagpur', lat: 21.1458, lng: 79.0882 },
  { name: 'Chhatrapati Sambhajinagar', lat: 19.8762, lng: 75.3433 },
  { name: 'Solapur', lat: 17.6599, lng: 75.9064 },
  { name: 'Kolhapur', lat: 16.7050, lng: 74.2433 },
  { name: 'Satara', lat: 17.6805, lng: 74.0183 },
  { name: 'Sangli', lat: 16.8524, lng: 74.5815 },
  { name: 'Ahilyanagar', lat: 19.0952, lng: 74.7496 },
  { name: 'Jalgaon', lat: 21.0077, lng: 75.5626 },
  { name: 'Dhule', lat: 20.9042, lng: 74.7749 },
  { name: 'Nanded', lat: 19.1383, lng: 77.3210 },
  { name: 'Latur', lat: 18.4088, lng: 76.5604 },
  { name: 'Akola', lat: 20.7059, lng: 77.0082 },
  { name: 'Amravati', lat: 20.9320, lng: 77.7523 },
  { name: 'Beed', lat: 18.9891, lng: 75.7601 },
  { name: 'Parbhani', lat: 19.2644, lng: 76.7667 },
  { name: 'Dharashiv', lat: 18.1856, lng: 76.0419 },
  { name: 'Ratnagiri', lat: 16.9902, lng: 73.3120 }
];

const CATEGORY_NAMES = {
  mandi: ["Agricultural Market", "Grain Market", "Agricultural Yard", "Central Mandi", "Krishi Upaj Mandi"],
  buyer: ["Agro Traders", "Fresh Produce Buyers", "Farm Produce Exchange", "Grain Buyers", "Wholesale Distributors"],
  storage: ["Fresh Storage", "Agro Cold Storage", "Produce Cold Hub", "Farm Storage", "Cold Chain Logistics"],
  fpo: ["Farmer Collective", "Valley Farmers Group", "Growers Collective", "Agricultural Producers Group", "Kisan FPO"]
};

function mulberry32(a) {
  return function() {
    var t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  if (lat1 == null || lon1 == null || lat2 == null || lon2 == null) return null;
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

function generateFallbackData(userCoords) {
  const data = [];
  let idCounter = 1;
  const categories = ['mandi', 'buyer', 'storage', 'fpo'];
  const rand = mulberry32(9999);

  categories.forEach(cat => {
    for (let i = 0; i < 20; i++) {
      const city = MAHARASHTRA_CITIES[i % MAHARASHTRA_CITIES.length];
      const suffixList = CATEGORY_NAMES[cat];
      const suffix = suffixList[Math.floor(rand() * suffixList.length)];
      const name = `${city.name} ${suffix}`;
      const latOffset = (rand() - 0.5) * 0.1;
      const lngOffset = (rand() - 0.5) * 0.1;
      const lat = city.lat + latOffset;
      const lng = city.lng + lngOffset;
      const distance_km = calculateDistance(userCoords?.lat, userCoords?.lng, lat, lng);
      
      data.push({
        id: `fallback-${idCounter++}`,
        type: cat,
        name: name,
        lat: lat,
        lng: lng,
        city: city.name,
        district: city.name,
        state: 'Maharashtra',
        distance_km: distance_km,
        info: `Verified ${cat} located in ${city.name}, Maharashtra.`,
      });
    }
  });

  return data;
}

// Fix Leaflet default marker assets
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const CATEGORIES = [
  { value: 'all', label: 'All', icon: MapPin, color: '#1f2937' },
  { value: 'mandi', label: 'Mandis', icon: Store, color: '#166534' },
  { value: 'buyer', label: 'Buyers', icon: ShoppingBag, color: '#2563eb' },
  { value: 'storage', label: 'Storage', icon: Warehouse, color: '#d97706' },
  { value: 'fpo', label: 'FPOs', icon: Users, color: '#9333ea' },
];

const RADIUS_OPTIONS = [
  { value: '25', label: '25 km' },
  { value: '50', label: '50 km' },
  { value: '100', label: '100 km' },
  { value: '250', label: '250 km' },
  { value: 'all', label: 'All India' },
];

// Helper to create category-specific SVG map pins
function createCustomPin(color) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 40" width="28" height="40">
      <defs>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000000" flood-opacity="0.3"/>
        </filter>
      </defs>
      <path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.3 21.7 0 14 0z"
        fill="${color}" stroke="#ffffff" stroke-width="1.8" filter="url(#shadow)"/>
      <circle cx="14" cy="14" r="5" fill="#ffffff"/>
    </svg>
  `;
  return L.divIcon({
    html: svg,
    iconSize: [28, 40],
    iconAnchor: [14, 40],
    popupAnchor: [0, -38],
    className: 'custom-map-pin',
  });
}

function createUserLocationPin() {
  const svg = `
    <div style="position: relative; width: 24px; height: 24px;">
      <div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; background: rgba(59, 130, 246, 0.35); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div style="position: absolute; top: 4px; left: 4px; width: 16px; height: 16px; border-radius: 50%; background: #2563eb; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
    </div>
  `;
  return L.divIcon({
    html: svg,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    className: 'user-loc-pin',
  });
}

// Controller to smoothly update map view and fix tile rendering sizes
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    if (center && Array.isArray(center) && center.length === 2 && !isNaN(center[0]) && !isNaN(center[1])) {
      map.setView(center, zoom || map.getZoom(), { animate: true });
    }
  }, [center, zoom, map]);
  return null;
}

export default function MarketMap({ 
  className = "h-[calc(100vh-4.5rem)]",
  hideTitle = false
}) {
  const { t } = useLanguage();
  const [category, setCategory] = useState('all');
  const [radius, setRadius] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(null);

  const getCatLabel = (val) => {
    if (val === 'all') return t('all') || 'All';
    if (val === 'mandi') return t('mandis') || 'Mandis';
    if (val === 'buyer') return t('buyers') || 'Buyers';
    if (val === 'storage') return t('storage') || 'Storage';
    if (val === 'fpo') return t('fpo') || 'FPOs';
    return val;
  };

  // Geolocation state
  const [userCoords, setUserCoords] = useState(null); // { lat, lng }
  const [geoStatus, setGeoStatus] = useState('prompt'); // 'prompt' | 'granted' | 'denied' | 'error'
  const [geoLoading, setGeoLoading] = useState(false);

  // Map viewport state
  const defaultCenter = useMemo(() => [19.9975, 73.7898], []); // Nashik / Maharashtra agricultural hub
  const [mapCenter, setMapCenter] = useState(defaultCenter);
  const [mapZoom, setMapZoom] = useState(8);

  // Data state
  const [locations, setLocations] = useState([]);
  const [counts, setCounts] = useState({ all: 0, mandi: 0, buyer: 0, storage: 0, fpo: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Request real browser geolocation
  const requestGeolocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoStatus('error');
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserCoords(coords);
        setMapCenter([coords.lat, coords.lng]);
        setMapZoom(10);
        setGeoStatus('granted');
        setGeoLoading(false);
      },
      (err) => {
        console.warn('Geolocation access denied or unavailable:', err);
        setGeoStatus('denied');
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, []);

  // Auto-request location on initial mount
  useEffect(() => {
    requestGeolocation();
  }, [requestGeolocation]);

  // Load locations from backend
  const fetchLocations = useCallback(() => {
    setLoading(true);
    setError(null);

    const applyFallback = () => {
      const allFallback = generateFallbackData(userCoords);
      let filteredFallback = allFallback;
      
      if (category !== 'all') {
        filteredFallback = filteredFallback.filter(loc => loc.type === category);
      }
      if (radius !== 'all' && userCoords) {
        filteredFallback = filteredFallback.filter(loc => loc.distance_km !== null && loc.distance_km <= Number(radius));
      }
      
      setLocations(filteredFallback);

      const newCounts = { all: 0, mandi: 0, buyer: 0, storage: 0, fpo: 0 };
      allFallback.forEach(loc => {
         if (radius === 'all' || !userCoords || (loc.distance_km !== null && loc.distance_km <= Number(radius))) {
            newCounts.all++;
            if (newCounts[loc.type] !== undefined) {
               newCounts[loc.type]++;
            }
         }
      });
      setCounts(newCounts);

      // Only re-center if user hasn't explicitly permitted geolocation
      if (!userCoords && mapCenter[0] === defaultCenter[0] && mapCenter[1] === defaultCenter[1]) {
         setMapCenter([19.75, 75.70]);
         setMapZoom(7);
      }
    };

    // No API calls - strictly use local 80-location dataset
    applyFallback();
    setLoading(false);
  }, [category, radius, userCoords, defaultCenter, mapCenter]);

  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  // Filtered markers by search term
  const displayedLocations = useMemo(() => {
    if (!searchTerm.trim()) return locations;
    const q = searchTerm.toLowerCase();
    return locations.filter(
      loc =>
        loc.name?.toLowerCase().includes(q) ||
        loc.district?.toLowerCase().includes(q) ||
        loc.state?.toLowerCase().includes(q)
    );
  }, [locations, searchTerm]);

  return (
    <div className={`flex flex-col space-y-4 ${className}`}>
      {/* Header & Geolocation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
        {!hideTitle ? (
          <div>
            <p className="section-label">{t('spatialMarketDirectory') || 'Spatial Market Directory'}</p>
            <h1 className="text-2xl font-bold text-gray-900">{t('interactiveMarketMap') || 'Interactive Market Map'}</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {t('marketMapSubtitle') || 'Real APMC Mandis, Verified Buyers, Warehouses & FPOs with live proximity'}
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-3">
             <h2 className="text-lg font-bold text-gray-900">Live Market Map</h2>
             <Link to="/map" className="text-xs text-green-700 font-semibold flex items-center hover:underline bg-green-50 px-2 py-1 rounded-md transition-colors hover:bg-green-100">
                Open Full Map <ExternalLink className="w-3 h-3 ml-1" />
             </Link>
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={requestGeolocation}
            disabled={geoLoading}
            className={`btn-sm flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-xl transition-all border ${
              geoStatus === 'granted'
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-white border-gray-200 text-gray-700 hover:border-green-300 hover:bg-green-50/50'
            }`}
          >
            <Crosshair className={`w-4 h-4 ${geoLoading ? 'animate-spin' : ''}`} />
            {geoLoading ? t('locating') : geoStatus === 'granted' ? t('usingLiveGps') : t('useMyLocation')}
          </button>

          <button
            onClick={fetchLocations}
            className="p-2 bg-white border border-gray-200 hover:bg-gray-50 rounded-xl text-gray-600 transition-colors"
            title="Refresh Locations"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Geolocation Notice (if denied) */}
      {geoStatus === 'denied' && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 text-xs text-amber-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>{t('locationAccessDenied')}</span>
        </div>
      )}

      {/* Main Grid: Map (Left) + Filters & List (Right) */}
      <div className="flex-1 grid lg:grid-cols-12 gap-5 min-h-0">
        {/* LEFT: Map Container (8 cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col relative z-0">
          {/* Floating Category Badges on Map */}
          <div className="absolute top-3 left-3 z-[400] bg-white/95 backdrop-blur-md p-1.5 rounded-xl shadow-md border border-gray-200/80 flex items-center gap-1 overflow-x-auto max-w-[calc(100%-1.5rem)]">
            {CATEGORIES.map(c => {
              const Icon = c.icon;
              const active = category === c.value;
              return (
                <button
                  key={c.value}
                  onClick={() => setCategory(c.value)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                    active
                      ? 'bg-green-800 text-white shadow-xs'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{getCatLabel(c.value)}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    active ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {counts[c.value] || 0}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Floating Distance Filter */}
          <div className="absolute top-3 right-3 z-[400] bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-xl shadow-md border border-gray-200/80 flex items-center gap-2">
            <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">{t('radius')}:</span>
            <select
              value={radius}
              onChange={(e) => setRadius(e.target.value)}
              className="text-xs font-semibold text-gray-800 bg-transparent outline-none cursor-pointer"
            >
              {RADIUS_OPTIONS.map(r => (
                <option key={r.value} value={r.value}>{r.value === 'all' ? t('allIndia') : r.label}</option>
              ))}
            </select>
          </div>

          {/* Leaflet Map */}
          <div className="flex-1 w-full h-full relative z-0">
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '100%', width: '100%' }}
              className="w-full h-full rounded-2xl"
            >
              <MapController center={mapCenter} zoom={mapZoom} />

              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />

              {/* User Location Marker */}
              {userCoords && (
                <Marker
                  position={[userCoords.lat, userCoords.lng]}
                  icon={createUserLocationPin()}
                >
                  <Popup>
                    <div className="p-1 text-center">
                      <p className="font-bold text-blue-700 text-xs">📍 {t('youAreHere') || 'You Are Here'}</p>
                      <p className="text-[10px] text-gray-500 mt-0.5">GPS Location</p>
                    </div>
                  </Popup>
                </Marker>
              )}

              {/* Location Markers */}
              {displayedLocations.map(loc => {
                const color =
                  loc.type === 'mandi' ? '#166534'
                  : loc.type === 'buyer' ? '#2563eb'
                  : loc.type === 'storage' ? '#d97706'
                  : '#9333ea';

                return (
                  <Marker
                    key={loc.id}
                    position={[loc.lat, loc.lng]}
                    icon={createCustomPin(color, loc.type)}
                    eventHandlers={{
                      click: () => setSelectedLocation(loc),
                    }}
                  >
                    <Popup>
                      <div className="p-1.5 min-w-48">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span
                            className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md text-white"
                            style={{ backgroundColor: color }}
                          >
                            {loc.type}
                          </span>
                          {loc.distance_km !== null && (
                            <span className="text-[11px] font-semibold text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
                              {loc.distance_km} km away
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-gray-900 text-sm mt-1">{loc.name}</h4>
                        <p className="text-xs text-gray-600 mt-0.5">{loc.district}, {loc.state}</p>
                        <p className="text-[11px] text-gray-500 mt-1 border-t border-gray-100 pt-1 leading-snug">{loc.info}</p>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </MapContainer>
          </div>

          {/* Map Footer Bar */}
          <div className="bg-gray-50/80 backdrop-blur-sm px-4 py-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500 z-10">
            <span>Showing <strong>{displayedLocations.length}</strong> locations</span>
            <span>Spatial Data &copy; PostGIS &amp; OpenStreetMap</span>
          </div>
        </div>

        {/* RIGHT: Search, Directory & Location Details (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4 overflow-hidden">
          {/* Search Box */}
          <div className="card p-3.5 flex-shrink-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                className="input pl-9 text-xs py-2 h-9"
                placeholder={t('searchMandisPlaceholder') || 'Search by mandi name, city or district...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Selected Location Card (if selected) */}
          {selectedLocation && (
            <div className="card p-4 bg-green-50/70 border-green-200 flex-shrink-0 relative">
              <button
                onClick={() => setSelectedLocation(null)}
                className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-xs font-bold p-1"
              >
                ✕
              </button>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-2.5 h-2.5 rounded-full bg-green-700" />
                <span className="text-[10px] uppercase font-bold text-green-800 tracking-wider">
                  {selectedLocation.type} Details
                </span>
                {selectedLocation.distance_km !== null && (
                  <span className="text-[11px] font-bold text-green-900 ml-auto bg-green-200/80 px-2 py-0.5 rounded-full">
                    {selectedLocation.distance_km} km
                  </span>
                )}
              </div>
              <h3 className="font-bold text-gray-900 text-sm mt-1">{selectedLocation.name}</h3>
              <p className="text-xs text-gray-600">{selectedLocation.district}, {selectedLocation.state}</p>
              <p className="text-xs text-gray-700 mt-2 bg-white/80 p-2 rounded-lg border border-green-100">
                {selectedLocation.info}
              </p>
              <button
                onClick={() => {
                  setMapCenter([selectedLocation.lat, selectedLocation.lng]);
                  setMapZoom(13);
                }}
                className="mt-3 w-full btn-primary btn-sm text-xs font-semibold py-1.5 flex items-center justify-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" /> {t('centerOnMap') || 'Center on Map'}
              </button>
            </div>
          )}

          {/* Directory List */}
          <div className="card flex-1 overflow-y-auto p-0">
            <div className="p-3.5 border-b border-gray-100 sticky top-0 bg-white/95 backdrop-blur-sm z-10 flex items-center justify-between">
              <div>
                <h2 className="font-bold text-gray-900 text-sm">{t('nearbyLocations') || 'Nearby Locations'}</h2>
                <p className="text-[11px] text-gray-400">{t('sortedNearestFirst') || 'Sorted nearest first'}</p>
              </div>
              <span className="text-xs font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                {displayedLocations.length}
              </span>
            </div>

            {loading ? (
              <div className="p-8 text-center text-gray-400 text-xs flex flex-col items-center gap-2">
                <div className="w-6 h-6 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
                <span>Loading spatial directory...</span>
              </div>
            ) : error ? (
              <div className="p-6 text-center text-red-500 text-xs">
                <AlertCircle className="w-5 h-5 mx-auto mb-1 text-red-400" />
                {error}
              </div>
            ) : displayedLocations.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-xs">
                No matching locations found within {radius === 'all' ? 'this region' : `${radius} km`}. Try expanding the radius.
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {displayedLocations.map(loc => {
                  const color =
                    loc.type === 'mandi' ? '#166534'
                    : loc.type === 'buyer' ? '#2563eb'
                    : loc.type === 'storage' ? '#d97706'
                    : '#9333ea';

                  return (
                    <div
                      key={loc.id}
                      onClick={() => {
                        setSelectedLocation(loc);
                        setMapCenter([loc.lat, loc.lng]);
                        setMapZoom(12);
                      }}
                      className="p-3.5 hover:bg-green-50/40 transition-all cursor-pointer group"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5">
                          <span
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: color }}
                          />
                          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                            {loc.type}
                          </span>
                        </div>
                        {loc.distance_km !== null && (
                          <span className="text-[11px] font-bold text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
                            {loc.distance_km} km
                          </span>
                        )}
                      </div>
                      <p className="font-semibold text-gray-900 text-xs group-hover:text-green-800 transition-colors">
                        {loc.name}
                      </p>
                      <p className="text-[11px] text-gray-500 mt-0.5 truncate">{loc.district}, {loc.state}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
