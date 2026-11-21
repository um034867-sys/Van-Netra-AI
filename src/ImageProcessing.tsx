import { useState } from "react";
import {
  Upload,
  Image as ImageIcon,
  Play,
  CheckCircle2,
  Clock,
  HardDrive,
  X,
  RotateCcw,
  AlertTriangle,
  Loader2,
  Users,
} from "lucide-react";

const API = "http://127.0.0.1:8001";

type ImageStatus =
  | "pending"
  | "processing"
  | "blank"
  | "tiger"
  | "other"
  | "error";

type Detection = {
  class: string;
  confidence: number;
  box: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
};

type CameraImage = {
  id: number;
  name: string;
  url: string;
  file: File;
  status: ImageStatus;
  confidence?: number;
  detections?: Detection[];
  imageWidth?: number;
  imageHeight?: number;
  error?: string;
};

export default function ImageProcessing() {
  const [images, setImages] = useState<CameraImage[]>([]);
  const [processing, setProcessing] = useState(false);
  const [processed, setProcessed] = useState(false);

  const handleUpload = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files;

    if (!files) return;

    const imageFiles = Array.from(files).filter((file) =>
      file.type.startsWith("image/")
    );

    const newImages: CameraImage[] = imageFiles.map(
      (file, index) => ({
        id: Date.now() + index,
        name: file.name,
        url: URL.createObjectURL(file),
        file,
        status: "pending",
      })
    );

    setImages((previous) => [...previous, ...newImages]);
    setProcessed(false);

    // Allow selecting the same file again
    event.target.value = "";
  };

  /*
   * REAL AI PROCESSING
   * Sends every image to: POST http://127.0.0.1:8000/detect
   */
  const processImages = async () => {
    if (images.length === 0 || processing) return;

    setProcessing(true);
    setProcessed(false);

    // Mark pending images as processing
    setImages((current) =>
      current.map((image) => ({
        ...image,
        status: "processing",
        error: undefined,
      }))
    );

    for (const image of images) {
      try {
        const formData = new FormData();
        formData.append("file", image.file);

        const response = await fetch(`${API}/detect`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(
            `Backend returned ${response.status}: ${response.statusText}`
          );
        }

        const result = await response.json();
        const detections: Detection[] = result.detections || [];
        const hasTiger = detections.some((d) => d.class === "tiger");
        const hasDetections = detections.length > 0;

        let status: ImageStatus = "blank";
        let confidence: number | undefined;

        if (hasTiger) {
          status = "tiger";
          const tigerDetections = detections.filter((d) => d.class === "tiger");
          const strongest = tigerDetections.reduce((best, curr) =>
            curr.confidence > best.confidence ? curr : best
          );
          confidence = Math.round(strongest.confidence * 100);
        } else if (hasDetections) {
          status = "other";
          const strongest = detections.reduce((best, curr) =>
            curr.confidence > best.confidence ? curr : best
          );
          confidence = Math.round(strongest.confidence * 100);
        }

        setImages((current) =>
          current.map((item) =>
            item.id === image.id
              ? {
                  ...item,
                  status,
                  confidence,
                  detections,
                  imageWidth: result.image_width,
                  imageHeight: result.image_height,
                }
              : item
          )
        );
      } catch (error) {
        console.error(`Error processing ${image.name}:`, error);

        setImages((current) =>
          current.map((item) =>
            item.id === image.id
              ? {
                  ...item,
                  status: "error",
                  error:
                    error instanceof Error
                      ? error.message
                      : "Unknown processing error",
                }
              : item
          )
        );
      }
    }

    setProcessing(false);
    setProcessed(true);
  };

  const removeImage = (id: number) => {
    setImages((currentImages) => {
      const image = currentImages.find((item) => item.id === id);
      if (image) {
        URL.revokeObjectURL(image.url);
      }
      return currentImages.filter((item) => item.id !== id);
    });
  };

  const restoreBlank = (id: number) => {
    setImages((currentImages) =>
      currentImages.map((image) =>
        image.id === id
          ? {
              ...image,
              status: "pending",
              confidence: undefined,
              detections: undefined,
            }
          : image
      )
    );
  };

  const clearAllImages = () => {
    images.forEach((img) => URL.revokeObjectURL(img.url));
    setImages([]);
    setProcessed(false);
  };

  const totalImages = images.length;
  const blankImages = images.filter((image) => image.status === "blank").length;
  const tigerImages = images.filter((image) => image.status === "tiger").length;
  const otherImages = images.filter((image) => image.status === "other").length;
  const errorImages = images.filter((image) => image.status === "error").length;

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div>
        <p className="text-sm font-medium text-emerald-400">
          CAMERA TRAP DATA
        </p>

        <h1 className="mt-2 text-3xl font-semibold">
          Image Processing & Triage
        </h1>

        <p className="mt-2 text-white/40">
          Analyze raw camera-trap frames using fine-tuned YOLO computer vision.
        </p>
      </div>

      {/* BACKEND STATUS */}
      <div className="flex items-center gap-2 text-xs text-white/40">
        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        Connected to Pench AI YOLO detection engine
      </div>

      {/* UPLOAD BOX */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8">
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/15 bg-black/10 px-6 py-12 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-400/10">
            <Upload className="text-emerald-400" size={25} />
          </div>

          <h2 className="mt-5 text-lg font-medium">
            Import Camera Trap Images
          </h2>

          <p className="mt-2 max-w-md text-sm text-white/40">
            Select JPG, PNG or WebP images from camera trap SD card deployments.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <label className="cursor-pointer rounded-xl bg-emerald-500 px-6 py-3 text-sm font-medium text-black transition hover:bg-emerald-400">
              Select Images
              <input
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleUpload}
              />
            </label>

            {images.length > 0 && (
              <button
                onClick={clearAllImages}
                disabled={processing}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white/70 transition hover:bg-white/10 disabled:opacity-50"
              >
                Clear All
              </button>
            )}
          </div>

          {images.length > 0 && (
            <p className="mt-4 text-xs text-white/40">
              {images.length} image{images.length !== 1 ? "s" : ""} in queue
            </p>
          )}
        </div>
      </div>

      {/* STATISTICS */}
      {images.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard
              icon={<ImageIcon size={19} />}
              title="Total Images"
              value={totalImages}
            />

            <StatCard
              icon={<CheckCircle2 size={19} className="text-emerald-400" />}
              title="Tiger Detections"
              value={tigerImages}
            />

            <StatCard
              icon={<Users size={19} className="text-blue-400" />}
              title="Other Subjects"
              value={otherImages}
            />

            <StatCard
              icon={<Clock size={19} className="text-amber-400" />}
              title="Blanks / Empty"
              value={blankImages}
            />

            <StatCard
              icon={<HardDrive size={19} className="text-red-400" />}
              title="Errors"
              value={errorImages}
            />
          </div>

          {/* CONTROL BAR */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <h2 className="font-medium">AI Inference Queue</h2>
                <p className="mt-1 text-sm text-white/40">
                  Runs local dual-model YOLO inference with human-override suppression.
                </p>
              </div>

              <button
                onClick={processImages}
                disabled={processing}
                className="flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-6 py-3 text-sm font-medium text-black transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {processing ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Play size={16} />
                )}

                {processing
                  ? "Running YOLO Inference..."
                  : processed
                  ? "Re-run Inference"
                  : "Start AI Detection"}
              </button>
            </div>

            {/* PROGRESS BAR */}
            {processing && (
              <div className="mt-6">
                <div className="mb-2 flex justify-between text-xs text-white/40">
                  <span>Running model inference...</span>
                  <span>
                    {images.filter((img) => img.status !== "processing" && img.status !== "pending").length} / {totalImages} completed
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-emerald-400 transition-all duration-300"
                    style={{
                      width: `${Math.max(
                        5,
                        ((images.filter(
                          (image) =>
                            image.status !== "processing" &&
                            image.status !== "pending"
                        ).length /
                          totalImages) *
                          100)
                      )}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* RESULTS GRID */}
          <div>
            <div className="mb-4">
              <h2 className="text-xl font-medium">Image Results</h2>
              <p className="mt-1 text-sm text-white/40">
                Visual inspection cards with detected bounding box overlays.
              </p>
            </div>

            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {images.map((image) => (
                <ImageCard
                  key={image.id}
                  image={image}
                  onRemove={removeImage}
                  onRestore={restoreBlank}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ============================================================
   STAT CARD
============================================================ */

function StatCard({
  icon,
  title,
  value,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/40">{title}</p>
        <span className="text-emerald-400">{icon}</span>
      </div>

      <p className="mt-4 text-3xl font-semibold">{value}</p>
    </div>
  );
}

/* ============================================================
   IMAGE CARD WITH BOUNDING BOX OVERLAYS
============================================================ */

function ImageCard({
  image,
  onRemove,
  onRestore,
}: {
  image: CameraImage;
  onRemove: (id: number) => void;
  onRestore: (id: number) => void;
}) {
  const statusConfig = {
    pending: {
      label: "Pending",
      className: "bg-white/10 text-white/70",
    },
    processing: {
      label: "AI Processing",
      className: "bg-blue-400/10 text-blue-300",
    },
    blank: {
      label: "No Subject",
      className: "bg-amber-400/10 text-amber-300",
    },
    tiger: {
      label: "Tiger Confirmed",
      className: "bg-emerald-400/10 text-emerald-300",
    },
    other: {
      label: "Other Subject",
      className: "bg-blue-400/10 text-blue-300",
    },
    error: {
      label: "Error",
      className: "bg-red-400/10 text-red-300",
    },
  };

  const status = statusConfig[image.status];

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
      {/* IMAGE CONTAINER WITH BOUNDING BOX OVERLAYS */}
      <div className="relative aspect-[4/3] bg-black/40 overflow-hidden flex items-center justify-center">
        <div className="relative inline-block max-h-full max-w-full">
          <img
            src={image.url}
            alt={image.name}
            className="max-h-64 w-full object-contain block"
          />

          {/* BOUNDING BOXES OVERLAY */}
          {image.detections &&
            image.imageWidth &&
            image.imageHeight &&
            image.detections.map((det, idx) => {
              const left = `${(det.box.x1 / image.imageWidth!) * 100}%`;
              const top = `${(det.box.y1 / image.imageHeight!) * 100}%`;
              const width = `${
                ((det.box.x2 - det.box.x1) / image.imageWidth!) * 100
              }%`;
              const height = `${
                ((det.box.y2 - det.box.y1) / image.imageHeight!) * 100
              }%`;
              const isTiger = det.class === "tiger";

              return (
                <div
                  key={idx}
                  className={`absolute pointer-events-none border-2 transition-all ${
                    isTiger
                      ? "border-emerald-400 bg-emerald-400/15"
                      : "border-amber-400 bg-amber-400/15"
                  }`}
                  style={{ left, top, width, height }}
                >
                  <span
                    className={`absolute -top-5 left-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider shadow ${
                      isTiger
                        ? "bg-emerald-500 text-black"
                        : "bg-amber-500 text-black"
                    }`}
                  >
                    {det.class} {Math.round(det.confidence * 100)}%
                  </span>
                </div>
              );
            })}
        </div>

        {/* Processing overlay */}
        {image.status === "processing" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <Loader2 size={32} className="animate-spin text-emerald-400" />
          </div>
        )}

        {/* Status Badge Tag */}
        {image.status === "tiger" && (
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-lg bg-emerald-500/95 px-2.5 py-1 text-xs font-semibold text-black shadow">
            <CheckCircle2 size={13} />
            TIGER
          </div>
        )}

        {image.status === "other" && (
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-lg bg-blue-500/95 px-2.5 py-1 text-xs font-semibold text-white shadow">
            <Users size={13} />
            NON-TIGER
          </div>
        )}

        {image.status === "error" && (
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-lg bg-red-500/95 px-2.5 py-1 text-xs font-semibold text-white shadow">
            <AlertTriangle size={13} />
            ERROR
          </div>
        )}

        {/* Remove Button */}
        <button
          onClick={() => onRemove(image.id)}
          className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white/70 backdrop-blur transition hover:bg-black/90 hover:text-white"
          title="Remove image"
        >
          <X size={14} />
        </button>
      </div>

      {/* DETAILS */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <p
            className="truncate text-xs font-medium text-white/70"
            title={image.name}
          >
            {image.name}
          </p>

          <div className="mt-2.5 flex items-center justify-between gap-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${status.className}`}
            >
              {status.label}
            </span>

            {image.confidence !== undefined && (
              <span className="text-xs font-mono text-emerald-400">
                {image.confidence}% conf
              </span>
            )}
          </div>

          {/* Detection summary list */}
          {image.detections && image.detections.length > 0 && (
            <div className="mt-3 rounded-lg bg-white/[0.02] border border-white/5 p-2.5 text-[11px]">
              <span className="text-white/40 block mb-1">
                Detected Objects ({image.detections.length}):
              </span>
              <div className="flex flex-wrap gap-1">
                {image.detections.map((d, i) => (
                  <span
                    key={i}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                      d.class === "tiger"
                        ? "bg-emerald-400/10 text-emerald-300"
                        : "bg-white/10 text-white/70"
                    }`}
                  >
                    {d.class} ({(d.confidence * 100).toFixed(0)}%)
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {image.status === "error" && image.error && (
            <p className="mt-2.5 rounded bg-red-400/10 p-2 text-xs text-red-300">
              {image.error}
            </p>
          )}
        </div>

        {/* Restore Blank Option */}
        {image.status === "blank" && (
          <button
            onClick={() => onRestore(image.id)}
            className="mt-3 flex items-center gap-1.5 text-xs text-amber-300 hover:text-amber-200"
          >
            <RotateCcw size={12} />
            Re-queue image
          </button>
        )}
      </div>
    </div>
  );
}
