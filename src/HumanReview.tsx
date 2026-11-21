import { useState, useEffect, useMemo } from "react";
import {
  RefreshCw,
  AlertCircle,
  Check,
  X,
  Clock,
  ShieldCheck,
  Info,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type ReviewItem = {
  id: number;
  detection_id: number;
  ai_prediction: string;
  reviewer_decision: string | null;
  created_at: string;
  image_path?: string | null;
  confidence?: number | null;
  station_id?: string | null;
  tiger_code?: string | null;
};

export default function HumanReview() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);

  const loadReviews = (setRefresh = false) => {
    if (setRefresh) setRefreshing(true);
    return fetch(`${API}/api/reviews`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setReviews(data);
        setError("");
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load human review queue from backend.");
      })
      .finally(() => {
        if (setRefresh) setRefreshing(false);
      });
  };

  useEffect(() => {
    let ignore = false;
    loadReviews()
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, []);

  const handleDecision = async (id: number, decision: "CONFIRMED" | "REJECTED") => {
    setSavingId(id);
    try {
      const res = await fetch(`${API}/api/reviews/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      // Optimistic update
      setReviews((prev) =>
        prev.map((r) => (r.id === id ? { ...r, reviewer_decision: decision } : r))
      );
      setActionMessage(`Review #${id} saved: ${decision}`);
    } catch (err) {
      console.error(err);
      setActionMessage(`Error saving decision — backend may be offline. (Decision shown locally only.)`);
      // Still update locally so the UI is usable offline
      setReviews((prev) =>
        prev.map((r) => (r.id === id ? { ...r, reviewer_decision: decision } : r))
      );
    } finally {
      setSavingId(null);
      setTimeout(() => setActionMessage(""), 4000);
    }
  };

  const pendingReviews = useMemo(
    () => reviews.filter((r) => !r.reviewer_decision),
    [reviews]
  );

  const completedReviews = useMemo(
    () => reviews.filter((r) => !!r.reviewer_decision),
    [reviews]
  );

  const displayReviews = showCompleted ? completedReviews : pendingReviews;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-amber-400">
            HUMAN-IN-THE-LOOP QUALITY ASSURANCE
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Verification Queue</h1>
          <p className="mt-1 text-sm text-white/40">
            Review AI classifications where confidence is below threshold. Decisions are saved to the database.
          </p>
        </div>

        <button
          onClick={() => loadReviews(true)}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/70 transition hover:bg-white/[0.07] disabled:opacity-50"
        >
          <RefreshCw size={15} className={refreshing ? "animate-spin text-emerald-400" : ""} />
          Refresh
        </button>
      </div>

      {/* DEMO LABEL */}
      <div className="flex items-start gap-2 rounded-xl border border-blue-400/15 bg-blue-400/5 p-3 text-xs text-blue-300/60">
        <Info size={14} className="shrink-0 mt-0.5" />
        <span>
          Pending reviews shown below are populated from DEMO data. Real reviews are automatically queued 
          when a tiger is detected with confidence &lt; 80% via the Image Processing page.
        </span>
      </div>

      {/* TOAST */}
      {actionMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-xs text-emerald-300">
          <Check size={14} />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* ERROR */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TABS */}
      {!loading && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCompleted(false)}
            className={`rounded-xl px-4 py-1.5 text-xs font-medium transition ${
              !showCompleted
                ? "bg-amber-400/10 text-amber-300 border border-amber-400/20"
                : "text-white/50 hover:bg-white/5 hover:text-white"
            }`}
          >
            Pending ({pendingReviews.length})
          </button>
          <button
            onClick={() => setShowCompleted(true)}
            className={`rounded-xl px-4 py-1.5 text-xs font-medium transition ${
              showCompleted
                ? "bg-emerald-400/10 text-emerald-300 border border-emerald-400/20"
                : "text-white/50 hover:bg-white/5 hover:text-white"
            }`}
          >
            Completed ({completedReviews.length})
          </button>
        </div>
      )}

      {/* CONTENT */}
      {loading ? (
        <div className="py-20 text-center text-sm text-white/40 animate-pulse">
          Loading audit queue…
        </div>
      ) : displayReviews.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02] p-12 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-400/10 text-emerald-400 mb-4">
            <ShieldCheck size={28} />
          </div>
          <h2 className="text-lg font-medium text-white">
            {showCompleted ? "No completed reviews yet" : "Review Queue is Empty"}
          </h2>
          <p className="mt-2 max-w-sm text-xs text-white/40">
            {showCompleted
              ? "Decisions will appear here once you review pending detections."
              : "All AI detections meet the confidence threshold. No images are pending human review."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {displayReviews.map((item) => {
            const isCompleted = !!item.reviewer_decision;
            const isConfirmed = item.reviewer_decision === "CONFIRMED";
            const isSaving = savingId === item.id;

            return (
              <div
                key={item.id}
                className={`rounded-2xl border p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 transition ${
                  isCompleted
                    ? isConfirmed
                      ? "border-emerald-400/20 bg-emerald-400/5"
                      : "border-white/10 bg-white/[0.02] opacity-70"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-semibold text-amber-300">
                      Detection #{item.detection_id}
                    </span>
                    {isCompleted ? (
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                          isConfirmed
                            ? "bg-emerald-400/10 text-emerald-300"
                            : "bg-white/10 text-white/50"
                        }`}
                      >
                        {item.reviewer_decision}
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-400/10 border border-amber-400/20 px-2.5 py-0.5 text-[11px] text-amber-400">
                        Audit Pending
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-sm text-white/80">
                    AI Prediction:{" "}
                    <span className="font-semibold text-emerald-400">
                      {item.ai_prediction}
                    </span>
                    {item.tiger_code ? ` — candidate: ${item.tiger_code}` : ""}
                  </p>

                  <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-white/40">
                    <div className="flex items-center gap-1">
                      <Clock size={12} />
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>
                    {item.station_id && <span>Station: {item.station_id}</span>}
                    {item.confidence !== null && item.confidence !== undefined && (
                      <span>Confidence: {(item.confidence * 100).toFixed(1)}%</span>
                    )}
                  </div>
                </div>

                {!isCompleted && (
                  <div className="flex items-center gap-2 self-start md:self-center">
                    <button
                      onClick={() => handleDecision(item.id, "CONFIRMED")}
                      disabled={isSaving}
                      className="flex items-center gap-1.5 rounded-xl bg-emerald-500 px-4 py-2 text-xs font-semibold text-black hover:bg-emerald-400 transition disabled:opacity-50"
                    >
                      {isSaving ? (
                        <RefreshCw size={14} className="animate-spin" />
                      ) : (
                        <Check size={14} />
                      )}
                      Confirm Tiger
                    </button>
                    <button
                      onClick={() => handleDecision(item.id, "REJECTED")}
                      disabled={isSaving}
                      className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white/70 hover:bg-white/10 hover:text-white transition disabled:opacity-50"
                    >
                      <X size={14} />
                      False Alarm
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
