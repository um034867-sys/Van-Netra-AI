import { useState, useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  MapPin,
  Camera,
  PawPrint,
  Route,
  RefreshCw,
  AlertCircle,
  Layers,
  Info,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

// Pench Tiger Reserve coordinates (Madhya Pradesh / Maharashtra boundary)
const PENCH_CENTER: [number, number] = [21.71, 79.27];
const DEFAULT_ZOOM = 12;

type Station = {
  id?: number;
  station_code: string;
  latitude: number;
  longitude: number;
  deployment_start?: string | null;
  deployment_end?: string | null;
};

type Detection = {
  id: number;
  tiger_code: string | null;
  station_id: string | null;
  timestamp: string;
  latitude: number | null;
  longitude: number | null;
  confidence: number | null;
  image_path?: string | null;
};

// Custom Leaflet Icons for clean rendering without missing asset bugs
const stationIcon = L.divIcon({
  className: "custom-map-pin",
  html: `
    <div style="
      background-color: #059669;
      color: white;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid #ffffff;
      box-shadow: 0 4px 10px rgba(0,0,0,0.5);
      font-size: 15px;
    ">📷</div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -18],
});

const tigerIcon = L.divIcon({
  className: "custom-map-pin",
  html: `
    <div style="
      background-color: #d97706;
      color: white;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid #ffffff;
      box-shadow: 0 4px 10px rgba(0,0,0,0.5);
      font-size: 14px;
    ">🐅</div>
  `,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
  popupAnchor: [0, -16],
});

export default function MovementMap() {
  const [stations, setStations] = useState<Station[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [showStations, setShowStations] = useState(true);
  const [showSightings, setShowSightings] = useState(true);
  const [showCorridors, setShowCorridors] = useState(true);
  const [showBaseMapAnyway, setShowBaseMapAnyway] = useState(false);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      fetch(`${API}/api/stations`).then((r) => {
        if (!r.ok) throw new Error("Stations fetch failed");
        return r.json();
      }),
      fetch(`${API}/api/detections`).then((r) => {
        if (!r.ok) throw new Error("Detections fetch failed");
        return r.json();
      }),
    ])
      .then(([stationsData, detectionsData]) => {
        if (!ignore) {
          setStations(stationsData);
          setDetections(detectionsData);
          setError("");
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Map data fetch error:", err);
        if (!ignore) {
          setError(
            "Unable to load map data. Ensure the FastAPI backend is operational on port 8000."
          );
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    Promise.all([
      fetch(`${API}/api/stations`).then((r) => {
        if (!r.ok) throw new Error("Stations fetch failed");
        return r.json();
      }),
      fetch(`${API}/api/detections`).then((r) => {
        if (!r.ok) throw new Error("Detections fetch failed");
        return r.json();
      }),
    ])
      .then(([stationsData, detectionsData]) => {
        setStations(stationsData);
        setDetections(detectionsData);
        setError("");
      })
      .catch((err) => {
        console.error("Map data fetch error:", err);
        setError(
          "Unable to load map data. Ensure the FastAPI backend is operational on port 8000."
        );
      })
      .finally(() => {
        setRefreshing(false);
      });
  };

  // Valid geo-referenced stations
  const validStations = useMemo(() => {
    return stations.filter(
      (s) =>
        typeof s.latitude === "number" &&
        typeof s.longitude === "number" &&
        !isNaN(s.latitude) &&
        !isNaN(s.longitude)
    );
  }, [stations]);

  // Valid geo-referenced detections
  const validSightings = useMemo(() => {
    return detections.filter(
      (d) =>
        typeof d.latitude === "number" &&
        typeof d.longitude === "number" &&
        !isNaN(d.latitude) &&
        !isNaN(d.longitude)
    );
  }, [detections]);

  // Chronological trajectories grouped by tiger (at least 2 valid coordinates required)
  const tigerCorridors = useMemo(() => {
    const grouped: Record<string, Detection[]> = {};

    for (const d of validSightings) {
      const code = d.tiger_code || "Unknown";
      if (!grouped[code]) grouped[code] = [];
      grouped[code].push(d);
    }

    const corridors: {
      tigerCode: string;
      positions: [number, number][];
      detections: Detection[];
      color: string;
    }[] = [];

    const palette = ["#10b981", "#f59e0b", "#38bdf8", "#ec4899", "#a855f7"];
    let colorIdx = 0;

    for (const [code, items] of Object.entries(grouped)) {
      if (items.length >= 2) {
        // Sort chronologically
        const sorted = [...items].sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );

        corridors.push({
          tigerCode: code,
          positions: sorted.map((item) => [item.latitude!, item.longitude!]),
          detections: sorted,
          color: palette[colorIdx % palette.length],
        });
        colorIdx++;
      }
    }

    return corridors;
  }, [validSightings]);

  // Determine initial center
  const mapCenter: [number, number] = useMemo(() => {
    if (validStations.length > 0) {
      return [validStations[0].latitude, validStations[0].longitude];
    }
    if (validSightings.length > 0) {
      return [validSightings[0].latitude!, validSightings[0].longitude!];
    }
    return PENCH_CENTER;
  }, [validStations, validSightings]);

  const hasGeoData = validStations.length > 0 || validSightings.length > 0;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-emerald-400">
            SPATIAL INTELLIGENCE
          </p>

          <h1 className="mt-2 text-3xl font-semibold">
            Movement & Occupancy Map
          </h1>

          <p className="mt-1 text-sm text-white/40">
            Geospatial tracking of camera-trap stations, telemetry, and confirmed tiger corridors.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/70 transition hover:bg-white/[0.07] disabled:opacity-50"
        >
          <RefreshCw size={15} className={refreshing ? "animate-spin text-emerald-400" : ""} />
          Refresh
        </button>
      </div>

      {/* ERROR BANNER */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* METRIC STRIP */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-wider">Camera Stations</p>
            <p className="mt-1 text-2xl font-semibold text-white">{validStations.length}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400/10 text-emerald-400">
            <Camera size={20} />
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-wider">Geotagged Sightings</p>
            <p className="mt-1 text-2xl font-semibold text-white">{validSightings.length}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400/10 text-amber-400">
            <PawPrint size={20} />
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 flex items-center justify-between">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-wider">Active Corridors</p>
            <p className="mt-1 text-2xl font-semibold text-white">{tigerCorridors.length}</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-400/10 text-blue-400">
            <Route size={20} />
          </div>
        </div>
      </div>

      {/* EMPTY STATE (When no coordinates exist and user hasn't toggled base map) */}
      {!hasGeoData && !loading && !showBaseMapAnyway ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02] p-12 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-400/10 text-emerald-400 mb-4">
            <MapPin size={32} />
          </div>

          <h2 className="text-xl font-medium text-white">No Spatial Coordinates Recorded</h2>

          <p className="mt-2 max-w-md text-sm text-white/40">
            Camera trap deployment stations or geotagged detections have not yet been registered in the database.
            Coordinates will appear automatically on this map once station locations or sighting data are added.
          </p>

          <button
            onClick={() => setShowBaseMapAnyway(true)}
            className="mt-6 rounded-xl bg-emerald-500 px-6 py-2.5 text-sm font-medium text-black transition hover:bg-emerald-400"
          >
            Explore Pench Reserve Base Map
          </button>
        </div>
      ) : (
        /* MAP VIEW CONTAINER */
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#0c1914] flex flex-col">
          {/* MAP CONTROLS TOOLBAR */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-[#0c1914] px-5 py-3 text-xs">
            <div className="flex items-center gap-2 text-white/70">
              <Layers size={14} className="text-emerald-400" />
              <span className="font-medium">Map Layers:</span>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer text-white/70 hover:text-white">
                <input
                  type="checkbox"
                  checked={showStations}
                  onChange={(e) => setShowStations(e.target.checked)}
                  className="rounded border-white/20 bg-white/10 text-emerald-500 focus:ring-0"
                />
                <span>Stations ({validStations.length})</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-white/70 hover:text-white">
                <input
                  type="checkbox"
                  checked={showSightings}
                  onChange={(e) => setShowSightings(e.target.checked)}
                  className="rounded border-white/20 bg-white/10 text-amber-500 focus:ring-0"
                />
                <span>Sightings ({validSightings.length})</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-white/70 hover:text-white">
                <input
                  type="checkbox"
                  checked={showCorridors}
                  onChange={(e) => setShowCorridors(e.target.checked)}
                  className="rounded border-white/20 bg-white/10 text-emerald-400 focus:ring-0"
                />
                <span>Corridors ({tigerCorridors.length})</span>
              </label>
            </div>

            <div className="text-white/40 flex items-center gap-1">
              <Info size={12} />
              <span>Pench Tiger Reserve Boundary</span>
            </div>
          </div>

          {/* LEAFLET MAP */}
          <div className="h-[550px] w-full relative z-0">
            <MapContainer
              center={mapCenter}
              zoom={DEFAULT_ZOOM}
              scrollWheelZoom={true}
              style={{ height: "100%", width: "100%", background: "#0c1914" }}
            >
              {/* OpenStreetMap Tile Layer */}
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* CAMERA STATIONS */}
              {showStations &&
                validStations.map((station, index) => (
                  <Marker
                    key={`station-${station.station_code || index}`}
                    position={[station.latitude, station.longitude]}
                    icon={stationIcon}
                  >
                    <Popup>
                      <div className="p-1 text-black">
                        <div className="flex items-center gap-1 font-bold text-sm text-emerald-700">
                          <Camera size={14} />
                          Station {station.station_code}
                        </div>
                        <p className="mt-1 text-xs text-gray-600">
                          Coordinates: {station.latitude.toFixed(4)}, {station.longitude.toFixed(4)}
                        </p>
                        {station.deployment_start && (
                          <p className="mt-1 text-xs text-gray-500">
                            Deployed: {new Date(station.deployment_start).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                ))}

              {/* SIGHTING MARKERS */}
              {showSightings &&
                validSightings.map((sighting) => (
                  <Marker
                    key={`sighting-${sighting.id}`}
                    position={[sighting.latitude!, sighting.longitude!]}
                    icon={tigerIcon}
                  >
                    <Popup>
                      <div className="p-1 text-black">
                        <div className="flex items-center gap-1 font-bold text-sm text-amber-700">
                          <PawPrint size={14} />
                          {sighting.tiger_code || "Tiger Sighting"}
                        </div>
                        <p className="mt-1 text-xs text-gray-600">
                          Station: {sighting.station_id || "Unspecified"}
                        </p>
                        <p className="text-xs text-gray-600">
                          Confidence:{" "}
                          {sighting.confidence !== null
                            ? `${(sighting.confidence * 100).toFixed(1)}%`
                            : "N/A"}
                        </p>
                        <p className="text-xs text-gray-500">
                          Time: {new Date(sighting.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                ))}

              {/* CHRONOLOGICAL TIGER MOVEMENT CORRIDORS */}
              {showCorridors &&
                tigerCorridors.map((corridor) => (
                  <Polyline
                    key={`corridor-${corridor.tigerCode}`}
                    positions={corridor.positions}
                    pathOptions={{
                      color: corridor.color,
                      weight: 3,
                      dashArray: "6, 6",
                      opacity: 0.85,
                    }}
                  >
                    <Popup>
                      <div className="p-1 text-black">
                        <div className="font-bold text-sm" style={{ color: corridor.color }}>
                          Movement Corridor: {corridor.tigerCode}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          Connected {corridor.positions.length} chronological sightings.
                        </p>
                      </div>
                    </Popup>
                  </Polyline>
                ))}
            </MapContainer>
          </div>
        </div>
      )}
    </div>
  );
}
