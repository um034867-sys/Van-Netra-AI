import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  PawPrint,
  Search,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  Calendar,
  Activity,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type Tiger = {
  id: number;
  tiger_code: string;
  first_seen: string;
  last_seen: string;
  status: string;
};

export default function TigerDatabase() {
  const [tigers, setTigers] = useState<Tiger[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let ignore = false;
    fetch(`${API}/api/tigers`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          setTigers(data);
          setError("");
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (!ignore) {
          setError("Unable to load tiger records. Verify the FastAPI backend is running.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetch(`${API}/api/tigers`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setTigers(data);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load tiger records. Verify the FastAPI backend is running.");
      })
      .finally(() => {
        setRefreshing(false);
      });
  };

  const filteredTigers = useMemo(() => {
    return tigers.filter((t) =>
      t.tiger_code.toLowerCase().includes(searchQuery.toLowerCase().trim())
    );
  }, [tigers, searchQuery]);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-emerald-400">
            INDIVIDUAL TIGER INTELLIGENCE
          </p>

          <h1 className="mt-2 text-3xl font-semibold">
            Tiger Database & Registry
          </h1>

          <p className="mt-1 text-sm text-white/40">
            Persistent identification catalog of individual tigers in Pench Reserve.
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

      {/* ERROR */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SEARCH AND STATS BAR */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-80">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            type="text"
            placeholder="Search by Tiger ID (e.g. PENCH-TGR-001)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/[0.03] pl-10 pr-4 py-2 text-sm text-white placeholder-white/30 focus:border-emerald-400 focus:outline-none"
          />
        </div>

        <div className="text-xs text-white/40">
          Showing {filteredTigers.length} of {tigers.length} registered individual{tigers.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* CONTENT */}
      {loading ? (
        <div className="py-20 text-center text-sm text-white/40 animate-pulse">
          Loading tiger catalog from database...
        </div>
      ) : tigers.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02] p-12 text-center">
          <PawPrint size={36} className="text-white/20 mb-3" />
          <h2 className="text-lg font-medium text-white">No Tigers Cataloged Yet</h2>
          <p className="mt-1 max-w-sm text-xs text-white/40">
            Registered tigers will appear here with capture history and encounter profiles.
          </p>
        </div>
      ) : filteredTigers.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 text-center text-sm text-white/40">
          No tigers match query &ldquo;{searchQuery}&rdquo;.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTigers.map((tiger) => (
            <div
              key={tiger.id}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 flex flex-col justify-between hover:border-emerald-400/40 transition"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-base font-semibold text-emerald-400">
                    {tiger.tiger_code}
                  </span>
                  <span className="rounded-full bg-emerald-400/10 px-2.5 py-0.5 text-xs text-emerald-300 font-medium">
                    {tiger.status}
                  </span>
                </div>

                <div className="mt-4 space-y-2 text-xs text-white/60">
                  <div className="flex items-center gap-2">
                    <Calendar size={13} className="text-white/40 shrink-0" />
                    <span>First seen: {new Date(tiger.first_seen).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity size={13} className="text-white/40 shrink-0" />
                    <span>Last seen: {new Date(tiger.last_seen).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 border-t border-white/5 pt-3">
                <Link
                  to={`/tigers/${tiger.tiger_code}`}
                  className="flex items-center justify-between text-xs text-emerald-400 hover:text-emerald-300 font-medium"
                >
                  <span>View Telemetry & Profile</span>
                  <ExternalLink size={13} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
