import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Camera,
  Image as ImageIcon,
  PawPrint,
  Bell,
  RefreshCw,
  Activity,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type DashboardData = {
  tigers: number;
  detections: number;
  stations: number;
  alerts: number;
};

type Tiger = {
  id: number;
  tiger_code: string;
  first_seen: string;
  last_seen: string;
  status: string;
};

type Detection = {
  id: number;
  tiger_code: string | null;
  station_id: string | null;
  timestamp: string;
  latitude: number | null;
  longitude: number | null;
  confidence: number | null;
  image_path: string | null;
};

type Alert = {
  id: number;
  tiger_code: string | null;
  alert_type: string;
  message: string;
  evidence: string | null;
  confidence: number | null;
  created_at: string;
};

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData>({
    tigers: 0,
    detections: 0,
    stations: 0,
    alerts: 0,
  });

  const [tigers, setTigers] = useState<Tiger[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    const fetchAll = () => {
      Promise.all([
        fetch(`${API}/api/dashboard`).then((r) => {
          if (!r.ok) throw new Error("Dashboard summary failed");
          return r.json();
        }),
        fetch(`${API}/api/tigers`).then((r) => {
          if (!r.ok) throw new Error("Tigers failed");
          return r.json();
        }),
        fetch(`${API}/api/detections`).then((r) => {
          if (!r.ok) throw new Error("Detections failed");
          return r.json();
        }),
        fetch(`${API}/api/alerts`).then((r) => {
          if (!r.ok) throw new Error("Alerts failed");
          return r.json();
        }),
      ])
        .then(([dashData, tigData, detData, altData]) => {
          if (!ignore) {
            setDashboard(dashData);
            setTigers(tigData);
            setDetections(detData);
            setAlerts(altData);
            setError("");
            setLoading(false);
          }
        })
        .catch((err) => {
          console.error(err);
          if (!ignore) {
            setError(
              "Unable to connect to Pench AI backend. Make sure the FastAPI service is running on port 8001."
            );
            setLoading(false);
          }
        });
    };

    fetchAll();
    const interval = setInterval(fetchAll, 10000);

    return () => {
      ignore = true;
      clearInterval(interval);
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    Promise.all([
      fetch(`${API}/api/dashboard`).then((r) => {
        if (!r.ok) throw new Error("Dashboard summary failed");
        return r.json();
      }),
      fetch(`${API}/api/tigers`).then((r) => {
        if (!r.ok) throw new Error("Tigers failed");
        return r.json();
      }),
      fetch(`${API}/api/detections`).then((r) => {
        if (!r.ok) throw new Error("Detections failed");
        return r.json();
      }),
      fetch(`${API}/api/alerts`).then((r) => {
        if (!r.ok) throw new Error("Alerts failed");
        return r.json();
      }),
    ])
      .then(([dashData, tigData, detData, altData]) => {
        setDashboard(dashData);
        setTigers(tigData);
        setDetections(detData);
        setAlerts(altData);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setError(
          "Unable to connect to Pench AI backend. Make sure the FastAPI service is running on port 8001."
        );
      })
      .finally(() => {
        setRefreshing(false);
      });
  };

  const stats = [
    {
      title: "Detection Records",
      value: dashboard.detections,
      icon: ImageIcon,
    },
    {
      title: "Tiger Detections",
      value: dashboard.tigers,
      icon: PawPrint,
    },
    {
      title: "Camera Stations",
      value: dashboard.stations,
      icon: Camera,
    },
    {
      title: "Active Alerts",
      value: dashboard.alerts,
      icon: Bell,
    },
  ];

  // Compute real activity distribution by grouping detections by date
  const activityData = useMemo(() => {
    if (detections.length === 0) return [];

    const dateCounts: Record<string, number> = {};
    for (const d of detections) {
      const dateKey = d.timestamp ? d.timestamp.split("T")[0] : "Recent";
      dateCounts[dateKey] = (dateCounts[dateKey] || 0) + 1;
    }

    const sortedDates = Object.keys(dateCounts).sort();
    const maxCount = Math.max(...Object.values(dateCounts), 1);

    return sortedDates.slice(-12).map((date) => ({
      date: date.length > 5 ? date.slice(5) : date, // MM-DD format
      fullDate: date,
      count: dateCounts[date],
      heightPercent: Math.max(12, Math.round((dateCounts[date] / maxCount) * 100)),
    }));
  }, [detections]);

  return (
    <div>
      {/* HEADER */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-emerald-400">
            PENCH TIGER RESERVE
          </p>

          <h1 className="mt-2 text-3xl font-semibold">
            Intelligence Dashboard
          </h1>

          <p className="mt-2 text-sm text-white/40">
            Camera-trap monitoring and individual tiger intelligence.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/70 transition hover:bg-white/[0.07] disabled:opacity-50"
        >
          <RefreshCw
            size={15}
            className={refreshing ? "animate-spin text-emerald-400" : ""}
          />
          Refresh
        </button>
      </div>

      {/* ERROR BANNER */}
      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-400/20 bg-red-400/10 p-4">
          <AlertCircle size={18} className="text-red-400 shrink-0" />
          <p className="text-sm text-red-300">
            {error}
          </p>
        </div>
      )}

      {/* LIVE STATUS */}
      <div className="mb-5 flex items-center gap-2 text-xs text-white/40">
        <span className={`h-2 w-2 rounded-full ${error ? "bg-red-400" : "bg-emerald-400 animate-pulse"}`} />
        <span>{error ? "Backend offline" : "Live backend connection"}</span>
        <span className="text-white/20">•</span>
        <span>Auto-refreshing every 10 seconds</span>
      </div>

      {/* STATS */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.title}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm text-white/40">
                  {stat.title}
                </p>

                <Icon
                  size={19}
                  className="text-emerald-400"
                />
              </div>

              <p className="mt-4 text-3xl font-semibold">
                {loading ? (
                  <span className="inline-block h-8 w-12 animate-pulse rounded bg-white/10" />
                ) : (
                  stat.value
                )}
              </p>
            </div>
          );
        })}
      </div>

      {/* MAIN CONTENT */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">

        {/* ACTIVITY */}
        <div className="min-h-[300px] rounded-2xl border border-white/10 bg-white/[0.03] p-6 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium">
                  Camera Trap Activity
                </h2>

                <p className="mt-1 text-sm text-white/40">
                  Detection frequency over time across connected stations.
                </p>
              </div>

              <Activity
                size={20}
                className="text-emerald-400"
              />
            </div>

            {loading ? (
              <div className="mt-8 flex h-48 items-center justify-center">
                <p className="text-sm text-white/40 animate-pulse">Loading activity data...</p>
              </div>
            ) : activityData.length > 0 ? (
              <div className="mt-8 flex h-48 items-end gap-3">
                {activityData.map((item, index) => (
                  <div
                    key={index}
                    className="group relative flex-1 flex flex-col items-center justify-end h-full"
                  >
                    <div
                      className="w-full rounded-t-md bg-emerald-400/40 transition-all hover:bg-emerald-400/70"
                      style={{
                        height: `${item.heightPercent}%`,
                      }}
                    />
                    <span className="mt-2 text-[10px] text-white/40 truncate w-full text-center">
                      {item.date}
                    </span>
                    {/* Tooltip on hover */}
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 whitespace-nowrap rounded bg-[#0c1914] border border-white/10 px-2 py-1 text-[11px] text-white shadow-lg pointer-events-none">
                      {item.count} detection{item.count !== 1 ? "s" : ""} on {item.fullDate}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-8 flex flex-col items-center justify-center rounded-xl border border-dashed border-white/10 bg-black/20 p-8 text-center min-h-[192px]">
                <Activity size={28} className="text-white/20 mb-2" />
                <p className="text-sm font-medium text-white/70">No activity data recorded yet</p>
                <p className="mt-1 text-xs text-white/40 max-w-sm">
                  Historical detection frequency and encounter patterns will be calculated here once camera-trap records are logged.
                </p>
              </div>
            )}
          </div>

          {activityData.length > 0 && (
            <div className="mt-3 flex justify-between text-[10px] text-white/30 border-t border-white/5 pt-2">
              <span>Earlier sightings</span>
              <span>Recent sightings</span>
            </div>
          )}
        </div>

        {/* ALERTS */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 flex flex-col">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">
              Recent Alerts
            </h2>

            <Bell
              size={18}
              className="text-emerald-400"
            />
          </div>

          <div className="mt-5 space-y-3 overflow-y-auto max-h-[340px]">
            {loading ? (
              <div className="py-8 text-center text-sm text-white/40 animate-pulse">
                Checking alerts...
              </div>
            ) : alerts.length === 0 ? (
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 text-center">
                <Bell size={24} className="mx-auto text-emerald-400/50 mb-2" />
                <p className="text-sm font-medium text-emerald-300">
                  All Clear
                </p>
                <p className="mt-1 text-xs text-white/40">
                  No movement or conflict alerts have been triggered.
                </p>
              </div>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className="rounded-xl border border-red-400/20 bg-red-400/10 p-4"
                >
                  <p className="text-sm font-medium text-red-300">
                    {alert.alert_type}
                  </p>

                  <p className="mt-1 text-xs text-white/70">
                    {alert.message}
                  </p>

                  <div className="mt-2 flex items-center justify-between text-[11px] text-white/40">
                    {alert.tiger_code ? (
                      <span className="font-mono text-emerald-400">{alert.tiger_code}</span>
                    ) : (
                      <span>Unidentified</span>
                    )}
                    <span>{new Date(alert.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {alerts.length > 5 && (
            <Link
              to="/alerts"
              className="mt-auto pt-4 text-center text-xs text-emerald-400 hover:text-emerald-300 flex items-center justify-center gap-1"
            >
              View all {alerts.length} alerts <ExternalLink size={12} />
            </Link>
          )}
        </div>
      </div>

      {/* TIGER DATABASE */}
      <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">
              Individual Tiger Intelligence
            </h2>

            <p className="mt-1 text-sm text-white/40">
              Tigers currently cataloged in the Pench AI database.
            </p>
          </div>

          <PawPrint
            size={20}
            className="text-emerald-400"
          />
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/40">
                <th className="px-3 py-3 font-normal">
                  Tiger ID
                </th>

                <th className="px-3 py-3 font-normal">
                  First Seen
                </th>

                <th className="px-3 py-3 font-normal">
                  Last Seen
                </th>

                <th className="px-3 py-3 font-normal">
                  Status
                </th>

                <th className="px-3 py-3 font-normal text-right">
                  Profile
                </th>
              </tr>
            </thead>

            <tbody>
              {tigers.map((tiger) => (
                <tr
                  key={tiger.id}
                  className="border-b border-white/5 transition hover:bg-white/[0.03]"
                >
                  <td className="px-3 py-4 font-mono font-medium text-emerald-300">
                    {tiger.tiger_code}
                  </td>

                  <td className="px-3 py-4 text-white/50">
                    {new Date(tiger.first_seen).toLocaleString()}
                  </td>

                  <td className="px-3 py-4 text-white/50">
                    {new Date(tiger.last_seen).toLocaleString()}
                  </td>

                  <td className="px-3 py-4">
                    <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">
                      {tiger.status}
                    </span>
                  </td>

                  <td className="px-3 py-4 text-right">
                    <Link
                      to={`/tigers/${tiger.tiger_code}`}
                      className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
                    >
                      View <ExternalLink size={12} />
                    </Link>
                  </td>
                </tr>
              ))}

              {tigers.length === 0 && !loading && (
                <tr>
                  <td
                    colSpan={5}
                    className="py-10 text-center text-white/30"
                  >
                    No tiger records cataloged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* RECENT DETECTIONS */}
      <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">
              Recent Detections
            </h2>

            <p className="mt-1 text-sm text-white/40">
              Latest camera-trap observations.
            </p>
          </div>

          <Camera
            size={20}
            className="text-emerald-400"
          />
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-white/40">
                <th className="px-3 py-3 font-normal">
                  Tiger
                </th>

                <th className="px-3 py-3 font-normal">
                  Station
                </th>

                <th className="px-3 py-3 font-normal">
                  Confidence
                </th>

                <th className="px-3 py-3 font-normal">
                  Time
                </th>
              </tr>
            </thead>

            <tbody>
              {detections.slice(0, 10).map((detection) => (
                <tr
                  key={detection.id}
                  className="border-b border-white/5"
                >
                  <td className="px-3 py-4 font-mono">
                    {detection.tiger_code || "Unknown Subject"}
                  </td>

                  <td className="px-3 py-4 text-white/50">
                    {detection.station_id || "—"}
                  </td>

                  <td className="px-3 py-4">
                    {detection.confidence !== null
                      ? `${(detection.confidence * 100).toFixed(1)}%`
                      : "—"}
                  </td>

                  <td className="px-3 py-4 text-white/50">
                    {new Date(detection.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}

              {detections.length === 0 && !loading && (
                <tr>
                  <td
                    colSpan={4}
                    className="py-10 text-center text-white/30"
                  >
                    No detections recorded yet.
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
