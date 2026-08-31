"use client";

import { createContext, useCallback, useContext, useState } from "react";

type ToastKind = "success" | "error" | "info";

interface ToastMessage {
  id: number;
  kind: ToastKind;
  text: string;
}

interface ToastContextValue {
  notify: (kind: ToastKind, text: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const KIND_STYLES: Record<ToastKind, string> = {
  success: "border-emerald-400/40 bg-emerald-950/90 text-emerald-100",
  error: "border-rose-400/40 bg-rose-950/90 text-rose-100",
  info: "border-sky-400/40 bg-sky-950/90 text-sky-100",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const notify = useCallback((kind: ToastKind, text: string) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, kind, text }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4"
        aria-live="polite"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto w-full max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg backdrop-blur ${KIND_STYLES[t.kind]}`}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
