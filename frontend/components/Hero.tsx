import type { HealthResponse } from "@/types";

function LlmStatusBadge({ health }: { health: HealthResponse | null }) {
  if (!health) return null;
  const ready = health.llm_status === "ready";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${
        ready
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
          : "border-amber-500/30 bg-amber-500/10 text-amber-300"
      }`}
      title={health.llm_message ?? undefined}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ready ? "bg-emerald-400" : "bg-amber-400"}`} />
      {ready ? "Local AI Ready" : "Local AI Offline"}
    </span>
  );
}

export function Hero({ health }: { health?: HealthResponse | null }) {
  return (
    <section className="relative overflow-hidden border-b border-slate-800/60 bg-slate-950">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(60% 60% at 20% 10%, rgba(99,102,241,0.25) 0%, transparent 60%), radial-gradient(50% 50% at 85% 20%, rgba(56,189,248,0.18) 0%, transparent 60%)",
        }}
      />
      <div className="absolute right-6 top-6">
        <LlmStatusBadge health={health ?? null} />
      </div>
      <div className="relative mx-auto max-w-5xl px-6 py-16 sm:py-20">
        <span className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          Retrieval-Augmented Generation
        </span>
        <h1 className="mt-5 max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
          Ask Questions About Your Documents
        </h1>
        <p className="mt-4 max-w-xl text-base leading-7 text-slate-400 sm:text-lg">
          Upload PDFs and ask natural-language questions. Answers are generated
          only from passages retrieved by vector similarity search over your
          documents &mdash; with citations back to the exact page, and an
          explicit &ldquo;not found&rdquo; when the answer isn&apos;t there.
        </p>
      </div>
    </section>
  );
}
