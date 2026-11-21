import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  RefreshCw,
  AlertTriangle,
  AlertCircle,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type Alert = {
  id: number;
  tiger_code: string | null;
  alert_type: string;
  message: string;
  evidence: string | null;
  confidence: number | null;
  created_at: string;
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<string>("ALL");

  useEffect(() => {
    let ignore = false;
    fetch(`${API}/api/alerts`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          setAlerts(data);
          setError("");
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (!ignore) {
          setError("Unable to load alerts. Ensure the backend service is running.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetch(`${API}/api/alerts`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setAlerts(data);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load alerts. Ensure the backend service is running.");
      })
      .finally(() => {
        setRefreshing(false);
      });
  };

  const filteredAlerts = useMemo(() => {
    if (filter === "ALL") return alerts;
    return alerts.filter((a) =>
      a.alert_type.toUpperCase().includes(filter.toUpperCase())
    );
  }, [alerts, filter]);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-red-400">
            ACTION REQUIRED
          </p>

          <h1 className="mt-2 text-3xl font-semibold">
            Security & Movement Alerts
          </h1>

          <p className="mt-1 text-sm text-white/40">
            Real-time notifications for territorial shifts, buffer-zone breaches, and anomalous movements.
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

      {/* FILTER BUTTONS */}
      <div className="flex flex-wrap items-center gap-2">
        {["ALL", "MOVEMENT", "TERRITORY", "BUFFER"].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`rounded-xl px-4 py-1.5 text-xs font-medium transition ${
              filter === cat
                ? "bg-white/15 text-white border border-white/20"
                : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
            }`}
          >
            {cat} {cat === "ALL" ? `(${alerts.length})` : ""}
          </button>
        ))}
      </div>

      {/* ALERT CONTENT */}
      {loading ? (
        <div className="py-20 text-center text-sm text-white/40 animate-pulse">
          Querying active alert events...
        </div>
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02] p-12 text-center">
          <ShieldAlert size={36} className="text-emerald-400/50 mb-3" />
          <h2 className="text-lg font-medium text-emerald-300">All Clear — No Active Alerts</h2>
          <p className="mt-1 max-w-sm text-xs text-white/40">
            No anomalous territory incursions, absence warnings, or movement deviations detected.
          </p>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 text-center text-sm text-white/40">
          No alerts match category &ldquo;{filter}&rdquo;.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => {
            const isHigh =
              alert.alert_type.toUpperCase().includes("HIGH") ||
              alert.alert_type.toUpperCase().includes("CONFLICT") ||
              alert.alert_type.toUpperCase().includes("BREACH");

            return (
              <div
                key={alert.id}
                className={`rounded-2xl border p-5 flex flex-col justify-between transition ${
                  isHigh
                    ? "border-red-400/30 bg-red-400/10"
                    : "border-amber-400/30 bg-amber-400/10"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle
                      size={18}
                      className={isHigh ? "text-red-400" : "text-amber-400"}
                    />
                    <span
                      className={`text-sm font-semibold tracking-wide ${
                        isHigh ? "text-red-300" : "text-amber-300"
                      }`}
                    >
                      {alert.alert_type}
                    </span>
                  </div>

                  <span className="text-xs text-white/40">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>

                <p className="mt-3 text-sm text-white/80 leading-relaxed">
                  {alert.message}
                </p>

                {alert.evidence && (
                  <p className="mt-2 text-xs text-white/40 italic">
                    Evidence: {alert.evidence}
                  </p>
                )}

                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                  {alert.tiger_code ? (
                    <Link
                      to={`/tigers/${alert.tiger_code}`}
                      className="inline-flex items-center gap-1 font-mono text-emerald-400 hover:text-emerald-300"
                    >
                      Target: {alert.tiger_code} <ExternalLink size={12} />
                    </Link>
                  ) : (
                    <span className="text-white/40">Unidentified Individual</span>
                  )}

                  {alert.confidence !== null && (
                    <span className="text-white/50 font-mono">
                      Confidence: {(alert.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
