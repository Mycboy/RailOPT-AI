import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Wrench, Shield, AlertTriangle, Train, Layers } from 'lucide-react';

// Fix default Leaflet icon paths in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Station coordinates along Northern Railway mainline corridor
const STATIONS = [
  { id: 'ST001', name: 'Shakti Nagar', code: 'SHN', km: 0, lat: 28.6250, lng: 77.2100 },
  { id: 'ST002', name: 'Vijaypur', code: 'VJP', km: 25, lat: 28.7800, lng: 77.3600 },
  { id: 'ST003', name: 'Rajgarh', code: 'RGR', km: 52, lat: 28.9500, lng: 77.5200 },
  { id: 'ST004', name: 'Lakshmi Nagar', code: 'LKN', km: 78, lat: 29.1300, lng: 77.6900 },
  { id: 'ST005', name: 'Devgarh', code: 'DVG', km: 105, lat: 29.3100, lng: 77.8500 },
];

// Sections connecting stations
const SECTIONS = [
  { id: 'SEC001', from: 'ST001', to: 'ST002', length: 25, traffic: 'High', color: '#f59e0b' },
  { id: 'SEC002', from: 'ST002', to: 'ST003', length: 27, traffic: 'High', color: '#ef4444' },
  { id: 'SEC003', from: 'ST003', to: 'ST004', length: 26, traffic: 'Medium', color: '#3b82f6' },
  { id: 'SEC004', from: 'ST004', to: 'ST005', length: 27, traffic: 'Medium', color: '#10b981' },
];

export default function NetworkMapView({ assets, blocks, schedule }) {
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [filterType, setFilterType] = useState('ALL');

  // Compute geographical coordinates for an asset based on its location_km
  const getAssetCoordinates = (locationKm) => {
    // Total line km = 105
    const ratio = Math.max(0, Math.min(1, locationKm / 105));
    const startStation = STATIONS[0];
    const endStation = STATIONS[STATIONS.length - 1];

    const lat = startStation.lat + ratio * (endStation.lat - startStation.lat) + (Math.sin(ratio * 10) * 0.015);
    const lng = startStation.lng + ratio * (endStation.lng - startStation.lng) + (Math.cos(ratio * 8) * 0.015);

    return [lat, lng];
  };

  // Station custom Leaflet icon
  const stationIcon = L.divIcon({
    className: 'custom-station-icon',
    html: `<div style="background-color: #2563eb; width: 14px; height: 14px; border: 2.5px solid #ffffff; border-radius: 50%; box-shadow: 0 0 10px #3b82f6;"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  // Asset custom Leaflet icon based on criticality & condition
  const createAssetIcon = (asset) => {
    const isCritical = asset.criticality === 'Critical';
    const isFailed = asset.status !== 'Operational';
    let color = '#3b82f6'; // blue
    if (isFailed) color = '#f43f5e'; // red
    else if (isCritical) color = '#f97316'; // orange
    else if (asset.condition_score < 70) color = '#eab308'; // yellow

    return L.divIcon({
      className: 'custom-asset-icon',
      html: `<div style="background-color: ${color}; width: 10px; height: 10px; border: 1.5px solid #0f172a; border-radius: 2px; box-shadow: 0 0 6px ${color};"></div>`,
      iconSize: [10, 10],
      iconAnchor: [5, 5],
    });
  };

  const linePositions = STATIONS.map((s) => [s.lat, s.lng]);

  const filteredAssets = (assets || []).filter((a) => {
    if (filterType === 'ALL') return true;
    return a.asset_type === filterType;
  });

  return (
    <div className="space-y-4">
      {/* Map Control Bar */}
      <div className="glass-panel p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Train className="w-4 h-4 text-blue-400" />
          <span className="font-heading font-bold text-sm text-white">
            Northern Railway Corridor (SEC001–SEC004, 105 km)
          </span>
          <span className="text-xs text-slate-400">
            • 5 Junction Stations • 12 Monitored Assets
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1">
          {['ALL', 'Track', 'OHE', 'Signal'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                filterType === type
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-900'
              }`}
            >
              {type === 'ALL' ? 'All Asset Types' : type}
            </button>
          ))}
        </div>
      </div>

      {/* Map Container */}
      <div className="glass-panel rounded-2xl p-2 border border-slate-800 h-[520px] relative overflow-hidden shadow-2xl">
        <MapContainer
          center={[28.9500, 77.5200]}
          zoom={9}
          scrollWheelZoom={false}
          className="w-full h-full rounded-xl"
        >
          {/* Dark CartoDB Tiles */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Main Track Section Polyline */}
          <Polyline
            positions={linePositions}
            pathOptions={{ color: '#3b82f6', weight: 4, opacity: 0.85, dashArray: '8, 8' }}
          >
            <Tooltip permanent={false}>Mainline Rail Corridor (105 km)</Tooltip>
          </Polyline>

          {/* Station Markers */}
          {STATIONS.map((station) => (
            <Marker
              key={station.id}
              position={[station.lat, station.lng]}
              icon={stationIcon}
            >
              <Popup>
                <div className="text-xs p-1">
                  <div className="flex items-center space-x-1.5 font-bold text-sm text-blue-400 mb-1">
                    <Train className="w-3.5 h-3.5" />
                    <span>{station.name} ({station.code})</span>
                  </div>
                  <p className="text-slate-300">Station ID: <strong className="text-white">{station.id}</strong></p>
                  <p className="text-slate-300">Corridor Origin: <strong className="text-white">{station.km} km</strong></p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Asset Markers */}
          {filteredAssets.map((asset) => {
            const coords = getAssetCoordinates(asset.location_km);
            const icon = createAssetIcon(asset);

            return (
              <Marker
                key={asset.asset_id}
                position={coords}
                icon={icon}
                eventHandlers={{
                  click: () => setSelectedAsset(asset),
                }}
              >
                <Popup>
                  <div className="text-xs p-1 space-y-1">
                    <div className="flex items-center justify-between border-b border-slate-700 pb-1">
                      <strong className="text-white font-mono">{asset.asset_id}</strong>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                        asset.criticality === 'Critical' ? 'bg-rose-500/20 text-rose-400' : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {asset.criticality}
                      </span>
                    </div>
                    <p className="text-slate-300 font-semibold">{asset.asset_code}</p>
                    <p className="text-slate-400">Type: <span className="text-slate-200">{asset.asset_type}</span></p>
                    <p className="text-slate-400">Section: <span className="text-slate-200">{asset.section_id} (km {asset.location_km})</span></p>
                    <p className="text-slate-400">
                      Condition Score: <strong className={asset.condition_score < 70 ? 'text-amber-400' : 'text-emerald-400'}>{asset.condition_score}/100</strong>
                    </p>
                    <p className="text-slate-400">Status: <span className="text-emerald-400">{asset.status}</span></p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* Floating Legend */}
        <div className="absolute bottom-4 right-4 z-[1000] glass-panel p-3 rounded-xl border border-slate-800 bg-slate-950/90 text-xs text-slate-300 space-y-1.5 shadow-xl">
          <p className="font-bold text-[11px] uppercase tracking-wider text-slate-400 mb-1">Corridor Map Legend</p>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 border border-white"></span>
            <span>Station Junctions (ST01–ST05)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded bg-emerald-500"></span>
            <span>Optimal Assets (Health &gt; 70)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded bg-amber-500"></span>
            <span>Degraded Assets (Health &le; 70)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded bg-rose-500"></span>
            <span>Critical / Failed Assets</span>
          </div>
        </div>
      </div>
    </div>
  );
}
