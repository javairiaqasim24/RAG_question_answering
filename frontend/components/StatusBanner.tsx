import type { HealthResponse } from "@/types";

export function StatusBanner({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return (
      <div className="border-b border-rose-900/40 bg-rose-950/60 px-6 py-2.5 text-center text-sm text-rose-200">
        Backend is unreachable. Make sure the API server is running.
      </div>
    );
  }

  if (!health.llm_configured) {
    const detail =
      health.llm_message ??
      (health.llm_status === "model_not_found"
        ? `The configured AI model (${health.llm_model}) is not installed.`
        : "The local AI service is unavailable. Make sure Ollama is running.");
    return (
      <div className="border-b border-amber-900/40 bg-amber-950/50 px-6 py-2.5 text-center text-sm text-amber-200">
        {detail} Document upload and search still work, but answer generation
        is disabled.
      </div>
    );
  }

  if (health.database !== "ok") {
    return (
      <div className="border-b border-rose-900/40 bg-rose-950/60 px-6 py-2.5 text-center text-sm text-rose-200">
        Vector database is unavailable. Check that PostgreSQL/pgvector is running.
      </div>
    );
  }

  return null;
}
