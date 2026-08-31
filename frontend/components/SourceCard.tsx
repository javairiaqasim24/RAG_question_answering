"use client";

import { useState } from "react";
import type { RetrievedSource } from "@/types";

export function SourceCard({ source, index }: { source: RetrievedSource; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const preview = source.text.length > 220 && !expanded ? source.text.slice(0, 220) + "…" : source.text;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-[11px] font-semibold text-indigo-300">
            {index}
          </span>
          <div>
            <p className="text-sm font-medium text-slate-200">{source.filename}</p>
            <p className="text-xs text-slate-500">
              {source.page_number ? `Page ${source.page_number}` : "Page unknown"} · chunk #
              {source.chunk_index}
            </p>
          </div>
        </div>
        <span
          className="shrink-0 rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-400"
          title="Cosine similarity between question and retrieved chunk"
        >
          {(source.similarity_score * 100).toFixed(0)}% match
        </span>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-400">{preview}</p>
      {source.text.length > 220 && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 text-xs font-medium text-indigo-400 hover:text-indigo-300"
        >
          {expanded ? "Show less" : "Show full excerpt"}
        </button>
      )}
    </div>
  );
}
