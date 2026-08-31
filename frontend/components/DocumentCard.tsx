"use client";

import type { DocumentRecord } from "@/types";

interface DocumentCardProps {
  document: DocumentRecord;
  selected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  deleting: boolean;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_CONFIG: Record<DocumentRecord["status"], { label: string; className: string }> = {
  processing: { label: "Processing…", className: "bg-amber-500/15 text-amber-300 border-amber-500/30" },
  indexed: { label: "Processed", className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" },
  failed: { label: "Failed", className: "bg-rose-500/15 text-rose-300 border-rose-500/30" },
};

export function DocumentCard({ document, selected, onSelect, onDelete, deleting }: DocumentCardProps) {
  const status = STATUS_CONFIG[document.status];

  return (
    <div
      className={`group relative rounded-lg border px-4 py-3 transition-colors ${
        selected
          ? "border-indigo-500/60 bg-indigo-500/10"
          : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
      }`}
    >
      <button
        type="button"
        onClick={onSelect}
        className="flex w-full flex-col items-start gap-1.5 text-left"
        aria-pressed={selected}
      >
        <div className="flex w-full items-center justify-between gap-2">
          <span className="truncate text-sm font-medium text-slate-100" title={document.filename}>
            {document.filename}
          </span>
        </div>
        <span
          className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${status.className}`}
        >
          {document.status === "indexed" ? "✓" : document.status === "failed" ? "✕" : "●"} {status.label}
        </span>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-500">
          {document.status === "indexed" && (
            <span>
              {document.chunk_count} chunks indexed · {document.page_count} pages
            </span>
          )}
          {document.status === "failed" && document.error_message && (
            <span className="text-rose-400/80">{document.error_message}</span>
          )}
          <span>{formatSize(document.file_size_bytes)}</span>
        </div>
      </button>

      <button
        type="button"
        onClick={onDelete}
        disabled={deleting}
        aria-label={`Remove ${document.filename}`}
        className="absolute right-2 top-2 rounded p-1 text-slate-600 opacity-0 transition-opacity hover:bg-rose-500/10 hover:text-rose-400 focus-visible:opacity-100 group-hover:opacity-100 disabled:opacity-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-4 w-4">
          <path
            d="M6 18 18 6M6 6l12 12"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      </button>
    </div>
  );
}

export function DocumentCardSkeleton() {
  return (
    <div className="animate-pulse rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
      <div className="h-4 w-2/3 rounded bg-slate-800" />
      <div className="mt-2 h-3 w-1/3 rounded bg-slate-800" />
      <div className="mt-2 h-3 w-1/2 rounded bg-slate-800" />
    </div>
  );
}
