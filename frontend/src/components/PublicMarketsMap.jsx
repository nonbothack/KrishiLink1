import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function PublicMarketsMap({ markets, ariaLabel }) {
  const located = markets.filter(
    (market) => Number.isFinite(market.latitude) && Number.isFinite(market.longitude),
  );
  if (!located.length) return null;
  return (
    <div className="map-preview public-map-preview" aria-label={ariaLabel}>
      <MapContainer
        className="map-canvas"
        center={[located[0].latitude, located[0].longitude]}
        zoom={7}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution="© OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {located.map((market) => (
          <CircleMarker
            key={market.id}
            center={[market.latitude, market.longitude]}
            radius={7}
            pathOptions={{ color: 'var(--brand-600)' }}
          >
            <Popup>{market.name}</Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
