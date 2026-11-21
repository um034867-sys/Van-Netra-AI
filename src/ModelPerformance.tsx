import { useEffect, useState } from "react";
import {
  BarChart2,
  CheckCircle2,
  Target,
  AlertCircle,
  RefreshCw,
  Info,
  FileText,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type Metrics = {
  precision: number;
  recall: number;
  map50: number;
  map50_95: number;
};

type ModelData = {
  model_name: string;
  model_file: string;
  base_architecture: string;
  dataset_class: string;
  test_images: number;
  annotated_instances: number;
  metrics: Metrics;
  evaluation_dir: string;
  graphs: string[];
  note: string;
};

const EVAL_GRAPH_BASE = `${API}/static/evaluation`;

const metricCards = (m: Metrics) => [
  {
    label: "Precision",
    value: (m.precision * 100).toFixed(2) + "%",
    description: "Of all tiger detections the model fired, this fraction were correct (true positives ÷ all positives).",
    color: "emerald",
  },
  {
    label: "Recall",
    value: (m.recall * 100).toFixed(2) + "%",
    description: "Of all actual tigers in the test set, this fraction were successfully detected.",
    color: "blue",
  },
  {
    label: "mAP@50",
    value: (m.map50 * 100).toFixed(2) + "%",
    description: "Mean Average Precision at IoU ≥ 0.50 — the primary YOLO accuracy benchmark.",
    color: "amber",
  },
  {
    label: "mAP@50-95",
    value: (m.map50_95 * 100).toFixed(2) + "%",
    description: "Mean Average Precision averaged across IoU thresholds 0.50–0.95 (stricter localisation criterion).",
    color: "violet",
  },
];

export default function ModelPerformance() {
  const [data, setData] = useState<ModelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = () => {
    setLoading(true);
    fetch(`${API}/api/model-performance`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        setData(d);
        setError("");
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load model performance data. Ensure the backend is running.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-emerald-400">AI MODEL EVALUATION</p>
          <h1 className="mt-2 text-3xl font-semibold">Model Performance</h1>
          <p className="mt-1 text-sm text-white/40">
            Verified evaluation results for Van Netra V2 on the held-out test split.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/70 transition hover:bg-white/[0.07] disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? "animate-spin text-emerald-400" : ""} />
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

      {loading && !data ? (
        <div className="py-20 text-center text-sm text-white/40 animate-pulse">
          Loading evaluation metrics…
        </div>
      ) : data ? (
        <>
          {/* MODEL INFO BANNER */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 text-sm">
              <div>
                <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Model</p>
                <p className="font-semibold text-emerald-400">{data.model_name}</p>
              </div>
              <div>
                <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Architecture</p>
                <p className="font-mono text-white/80">{data.base_architecture}</p>
              </div>
              <div>
                <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Test Images</p>
                <p className="font-semibold text-white">{data.test_images.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Annotated Instances</p>
                <p className="font-semibold text-white">{data.annotated_instances.toLocaleString()}</p>
              </div>
            </div>

            <div className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-400/10 bg-emerald-400/5 p-3">
              <Info size={14} className="text-emerald-400 mt-0.5 shrink-0" />
              <p className="text-xs text-white/50 leading-relaxed">{data.note}</p>
            </div>
          </div>

          {/* METRIC CARDS */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metricCards(data.metrics).map((card) => {
              const colorMap: Record<string, string> = {
                emerald: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
                blue:    "text-blue-400 bg-blue-400/10 border-blue-400/20",
                amber:   "text-amber-400 bg-amber-400/10 border-amber-400/20",
                violet:  "text-violet-400 bg-violet-400/10 border-violet-400/20",
              };
              const cls = colorMap[card.color] || colorMap.emerald;

              return (
                <div
                  key={card.label}
                  className={`rounded-2xl border p-5 flex flex-col gap-3 ${cls}`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs uppercase tracking-wider opacity-70">{card.label}</p>
                    <Target size={16} className="opacity-70" />
                  </div>
                  <p className="text-4xl font-bold">{card.value}</p>
                  <p className="text-xs opacity-60 leading-relaxed">{card.description}</p>
                </div>
              );
            })}
          </div>

          {/* PRECISION-RECALL VISUAL BAR */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="flex items-center gap-2 mb-5">
              <BarChart2 size={18} className="text-emerald-400" />
              <h2 className="text-lg font-medium">Metric Summary</h2>
            </div>

            <div className="space-y-4">
              {[
                { label: "Precision", value: data.metrics.precision, color: "bg-emerald-400" },
                { label: "Recall", value: data.metrics.recall, color: "bg-blue-400" },
                { label: "mAP@50", value: data.metrics.map50, color: "bg-amber-400" },
                { label: "mAP@50-95", value: data.metrics.map50_95, color: "bg-violet-400" },
              ].map((m) => (
                <div key={m.label} className="flex items-center gap-4">
                  <span className="w-28 text-sm text-white/50 shrink-0">{m.label}</span>
                  <div className="flex-1 h-3 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${m.color}`}
                      style={{ width: `${(m.value * 100).toFixed(1)}%` }}
                    />
                  </div>
                  <span className="w-16 text-right text-sm font-mono font-medium text-white/80">
                    {(m.value * 100).toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* EVALUATION GRAPHS */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-emerald-400" />
                <h2 className="text-lg font-medium">Evaluation Graphs</h2>
              </div>
              <span className="text-xs text-white/30">{data.evaluation_dir}</span>
            </div>

            <div className="mb-4 flex items-start gap-2 rounded-lg border border-amber-400/10 bg-amber-400/5 p-3">
              <Info size={14} className="text-amber-400 mt-0.5 shrink-0" />
              <p className="text-xs text-white/40 leading-relaxed">
                Graphs are served from the backend static files directory. If images don't load, the backend 
                static-file serving for <code className="text-white/60">/static/evaluation/</code> must be enabled.
                The raw image files are at <code className="text-white/60">{data.evaluation_dir}/</code>.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.graphs.map((graph) => {
                const label = graph
                  .replace(".png", "")
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase());

                return (
                  <div
                    key={graph}
                    className="rounded-xl border border-white/10 bg-black/20 overflow-hidden"
                  >
                    <img
                      src={`${EVAL_GRAPH_BASE}/${graph}`}
                      alt={label}
                      className="w-full h-48 object-contain bg-white/5"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                        const parent = (e.target as HTMLImageElement).parentElement;
                        if (parent) {
                          parent.innerHTML = `<div class="h-48 flex flex-col items-center justify-center gap-2 text-white/20">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="m3 9 4-4 4 4 4-4 4 4"/><path d="M3 15h18"/></svg>
                            <span class="text-xs">${label}</span>
                            <span class="text-[10px]">${graph}</span>
                          </div>`;
                        }
                      }}
                    />
                    <div className="px-3 py-2 border-t border-white/5">
                      <p className="text-xs text-white/50">{label}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* WHAT THIS MEANS */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 size={18} className="text-emerald-400" />
              <h2 className="text-lg font-medium">Interpretation</h2>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 text-sm text-white/60 leading-relaxed">
              <div className="space-y-2">
                <p>
                  <span className="text-emerald-400 font-medium">Precision 92.66%</span> — The model is highly 
                  reliable. When it fires an alert, it is correct more than 9 times out of 10. This minimises 
                  wasted ranger effort on false alarms.
                </p>
                <p>
                  <span className="text-blue-400 font-medium">Recall 86.32%</span> — The model detects 
                  roughly 86 out of every 100 actual tiger appearances in camera-trap images, which is strong 
                  performance for a naturally camouflaged animal in variable lighting conditions.
                </p>
              </div>
              <div className="space-y-2">
                <p>
                  <span className="text-amber-400 font-medium">mAP@50 91.89%</span> — The primary industry 
                  benchmark for object detection. A score above 90% is considered production-ready for 
                  conservation monitoring applications.
                </p>
                <p>
                  <span className="text-violet-400 font-medium">mAP@50-95 55.30%</span> — Measures how 
                  accurately the bounding box is localised at stricter overlap thresholds. The gap to mAP@50 
                  is typical for wildlife images where animals are partially occluded by vegetation.
                </p>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
