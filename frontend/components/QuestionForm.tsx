"use client";

import { useState } from "react";

interface QuestionFormProps {
  onSubmit: (question: string) => void;
  loading: boolean;
  disabled: boolean;
  scopeLabel: string;
}

export function QuestionForm({ onSubmit, loading, disabled, scopeLabel }: QuestionFormProps) {
  const [question, setQuestion] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const trimmed = question.trim();
        if (trimmed) onSubmit(trimmed);
      }}
      className="rounded-xl border border-slate-800 bg-slate-900/30 p-4"
    >
      <div className="mb-2 flex items-center justify-between">
        <label htmlFor="question" className="text-sm font-semibold text-slate-200">
          Ask a question
        </label>
        <span className="truncate text-xs text-slate-500">{scopeLabel}</span>
      </div>
      <textarea
        id="question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const trimmed = question.trim();
            if (trimmed && !disabled && !loading) onSubmit(trimmed);
          }
        }}
        disabled={disabled}
        placeholder="Ask something about your uploaded documents…"
        rows={3}
        className="w-full resize-none rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
      />
      <div className="mt-3 flex items-center justify-between">
        <p className="text-xs text-slate-600">Enter to ask &middot; Shift+Enter for a new line</p>
        <button
          type="submit"
          disabled={disabled || loading || question.trim().length === 0}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading && (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
          )}
          {loading ? "Thinking…" : "Ask Question"}
        </button>
      </div>
    </form>
  );
}
