"use client";

import type { DocumentRecord } from "@/types";
import { DocumentCard, DocumentCardSkeleton } from "./DocumentCard";

interface DocumentListProps {
  documents: DocumentRecord[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function DocumentList({
  documents,
  loading,
  selectedId,
  onSelect,
  onDelete,
  deletingId,
}: DocumentListProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Documents</h2>
        {documents.length > 0 && (
          <span className="text-xs text-slate-500">{documents.length} uploaded</span>
        )}
      </div>

      {loading && documents.length === 0 && (
        <div className="space-y-2">
          <DocumentCardSkeleton />
          <DocumentCardSkeleton />
        </div>
      )}

      {!loading && documents.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-800 px-3 py-6 text-center text-sm text-slate-500">
          No documents yet. Upload a PDF to get started.
        </p>
      )}

      {documents.length > 0 && (
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => onSelect(null)}
            className={`w-full rounded-lg border px-3 py-2 text-left text-xs font-medium transition-colors ${
              selectedId === null
                ? "border-indigo-500/60 bg-indigo-500/10 text-indigo-200"
                : "border-slate-800 text-slate-400 hover:border-slate-700"
            }`}
          >
            Search across all documents
          </button>
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              selected={selectedId === doc.id}
              onSelect={() => onSelect(doc.id)}
              onDelete={() => onDelete(doc.id)}
              deleting={deletingId === doc.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
