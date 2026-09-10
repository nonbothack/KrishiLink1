// =============================================================
// Map Page
// Interactive Market Map with Mandis, Buyers, Storage & FPOs
// Uses React Leaflet + OpenStreetMap + Real PostGIS Backend
// =============================================================

import MarketMap from '../components/map/MarketMap';

export default function MapPage() {
  return (
    <MarketMap className="max-w-7xl mx-auto px-4 py-6 h-[calc(100vh-4.5rem)]" />
  );
}
