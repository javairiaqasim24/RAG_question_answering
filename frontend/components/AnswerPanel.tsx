"use client";

import type { QueryResponse } from "@/types";
import { SourceCard } from "./SourceCard";

function AnswerSkeleton() {
  return (
    <div className="animate-pulse space-y-3 rounded-xl border border-slate-800 bg-slate-900/30 p-5">
      <div className="h-4 w-1/4 rounded bg-slate-800" />
      <div className="h-3 w-full rounded bg-slate-800" />
      <div className="h-3 w-5/6 rounded bg-slate-800" />
      <div className="h-3 w-2/3 rounded bg-slate-800" />
    </div>
  );
}

interface AnswerPanelProps {
  result: QueryResponse | null;
  loading: boolean;
}

export function AnswerPanel({ result, loading }: AnswerPanelProps) {
  if (loading) return <AnswerSkeleton />;
  if (!result) return null;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-slate-200">Answer</h3>
        {result.grounded ? (
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
            ✓ Grounded in sources
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-300">
            Not found in documents
          </span>
        )}
        <span className="ml-auto text-[11px] text-slate-600">{result.model}</span>
      </div>

      <p className="whitespace-pre-wrap text-sm leading-7 text-slate-100">{result.answer}</p>

      {result.sources.length > 0 && (
        <div className="mt-5">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Sources ({result.sources.length})
          </h4>
          <div className="space-y-2">
            {result.sources.map((source, i) => (
              <SourceCard key={source.chunk_id} source={source} index={i + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
