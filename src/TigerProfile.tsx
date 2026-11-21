import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  Activity,
  Camera,
  AlertCircle,
  Clock,
  Compass,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type DetectionItem = {
  id: number;
  station_id: string | null;
  timestamp: string;
  latitude: number | null;
  longitude: number | null;
  confidence: number | null;
  image_path: string | null;
};

type TigerDetail = {
  id: number;
  tiger_code: string;
  first_seen: string;
  last_seen: string;
  status: string;
  detections: DetectionItem[];
};

export default function TigerProfile() {
  const { id } = useParams<{ id: string }>();
  const [tiger, setTiger] = useState<TigerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    let isMounted = true;
    fetch(`${API}/api/tigers/${encodeURIComponent(id)}`)
      .then((res) => {
        if (res.status === 404) throw new Error(`Tiger "${id}" not found in database`);
        if (!res.ok) throw new Error(`Failed to load profile (${res.status})`);
        return res.json();
      })
      .then((data) => {
        if (isMounted) {
          setTiger(data);
          setError("");
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load tiger profile");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center">
        <p className="text-sm text-white/40 animate-pulse">Loading individual tiger telemetry...</p>
      </div>
    );
  }

  if (error || !tiger) {
    return (
      <div className="space-y-4">
        <Link
          to="/tigers"
          className="inline-flex items-center gap-2 text-xs text-emerald-400 hover:text-emerald-300"
        >
          <ArrowLeft size={14} /> Back to Tiger Database
        </Link>
        <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-8 text-center">
          <AlertCircle size={32} className="mx-auto text-red-400 mb-2" />
          <h2 className="text-lg font-medium text-red-200">{error || "Tiger record not found"}</h2>
          <p className="mt-1 text-xs text-white/40">
            Please check the tiger identifier or verify if the individual is enrolled in the registry.
          </p>
        </div>
      </div>
    );
  }

  const detectionCount = tiger.detections ? tiger.detections.length : 0;
  const avgConfidence =
    detectionCount > 0
      ? (
          (tiger.detections.reduce((acc, d) => acc + (d.confidence || 0), 0) /
            detectionCount) *
          100
        ).toFixed(1)
      : null;

  return (
    <div className="space-y-6">
      {/* NAVIGATION */}
      <Link
        to="/tigers"
        className="inline-flex items-center gap-2 text-xs text-emerald-400 hover:text-emerald-300 font-medium"
      >
        <ArrowLeft size={14} /> Back to Tiger Registry
      </Link>

      {/* HEADER */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">
            Individual Tiger Telemetry
          </p>
          <h1 className="mt-1 text-3xl font-bold font-mono tracking-wide text-white">
            {tiger.tiger_code}
          </h1>
        </div>

        <span className="self-start rounded-full bg-emerald-400/10 border border-emerald-400/30 px-3 py-1 text-xs font-medium text-emerald-300">
          Status: {tiger.status}
        </span>
      </div>

      {/* STATS STRIP */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/40">Total Sighting Events</span>
            <Camera size={16} className="text-emerald-400" />
          </div>
          <p className="mt-3 text-3xl font-semibold text-white">{detectionCount}</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/40">First Observed</span>
            <Calendar size={16} className="text-emerald-400" />
          </div>
          <p className="mt-3 text-lg font-medium text-white truncate">
            {new Date(tiger.first_seen).toLocaleDateString()}
          </p>
          <p className="text-[11px] text-white/40 mt-1">
            {new Date(tiger.first_seen).toLocaleTimeString()}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/40">Mean AI Confidence</span>
            <Activity size={16} className="text-emerald-400" />
          </div>
          <p className="mt-3 text-3xl font-semibold text-white">
            {avgConfidence !== null ? `${avgConfidence}%` : "—"}
          </p>
        </div>
      </div>

      {/* OBSERVATION HISTORY TABLE */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-medium text-white">Capture History</h2>
            <p className="text-xs text-white/40 mt-0.5">
              Chronological camera-trap encounters recorded for this individual.
            </p>
          </div>
          <span className="text-xs text-white/40">{detectionCount} record{detectionCount !== 1 ? "s" : ""}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/40 text-xs">
                <th className="px-3 py-3 font-normal">Timestamp</th>
                <th className="px-3 py-3 font-normal">Station ID</th>
                <th className="px-3 py-3 font-normal">Coordinates</th>
                <th className="px-3 py-3 font-normal text-right">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {tiger.detections && tiger.detections.length > 0 ? (
                tiger.detections.map((det) => (
                  <tr key={det.id} className="border-b border-white/5 transition hover:bg-white/[0.02]">
                    <td className="px-3 py-3.5 text-xs text-white/80">
                      <div className="flex items-center gap-1.5">
                        <Clock size={12} className="text-white/40" />
                        <span>{new Date(det.timestamp).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="px-3 py-3.5 font-mono text-xs text-emerald-300">
                      {det.station_id || "—"}
                    </td>
                    <td className="px-3 py-3.5 text-xs text-white/60">
                      {det.latitude !== null && det.longitude !== null ? (
                        <div className="flex items-center gap-1">
                          <Compass size={12} className="text-white/40" />
                          <span>{det.latitude.toFixed(4)}, {det.longitude.toFixed(4)}</span>
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-3.5 text-xs font-mono text-right text-emerald-400">
                      {det.confidence !== null ? `${(det.confidence * 100).toFixed(1)}%` : "—"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-xs text-white/30">
                    No detections recorded for this individual.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
