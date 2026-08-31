"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, askQuestion, deleteDocument, getHealth, listDocuments, uploadDocument } from "@/lib/api";
import type { DocumentRecord, HealthResponse, QueryResponse } from "@/types";
import { Hero } from "@/components/Hero";
import { StatusBanner } from "@/components/StatusBanner";
import { UploadDropzone } from "@/components/UploadDropzone";
import { DocumentList } from "@/components/DocumentList";
import { QuestionForm } from "@/components/QuestionForm";
import { AnswerPanel } from "@/components/AnswerPanel";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/components/Toast";

export default function Home() {
  const { notify } = useToast();

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [queryLoading, setQueryLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);

  const refreshDocuments = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocuments(res.documents);
    } catch (err) {
      notify("error", err instanceof ApiError ? err.message : "Could not load documents.");
    } finally {
      setDocumentsLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
    refreshDocuments();
  }, [refreshDocuments]);

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      setUploading(true);
      for (const file of files) {
        try {
          const res = await uploadDocument(file);
          notify(res.document.status === "indexed" ? "success" : "error", res.message);
        } catch (err) {
          notify(
            "error",
            err instanceof ApiError ? err.message : `Failed to upload ${file.name}.`
          );
        }
      }
      setUploading(false);
      refreshDocuments();
    },
    [notify, refreshDocuments]
  );

  const handleDelete = useCallback(
    async (id: string) => {
      setDeletingId(id);
      try {
        await deleteDocument(id);
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        if (selectedId === id) setSelectedId(null);
        notify("info", "Document removed.");
      } catch (err) {
        notify("error", err instanceof ApiError ? err.message : "Failed to remove document.");
      } finally {
        setDeletingId(null);
      }
    },
    [notify, selectedId]
  );

  const handleAsk = useCallback(
    async (question: string) => {
      setQueryLoading(true);
      setResult(null);
      try {
        const res = await askQuestion(question, { documentId: selectedId ?? undefined });
        setResult(res);
      } catch (err) {
        notify("error", err instanceof ApiError ? err.message : "Failed to get an answer.");
      } finally {
        setQueryLoading(false);
      }
    },
    [notify, selectedId]
  );

  const indexedDocuments = documents.filter((d) => d.status === "indexed");
  const hasIndexedDocuments = indexedDocuments.length > 0;
  const selectedDoc = documents.find((d) => d.id === selectedId) ?? null;
  const scopeLabel = selectedDoc ? `Scope: ${selectedDoc.filename}` : "Scope: all documents";

  return (
    <div className="flex min-h-screen flex-col bg-slate-950">
      <StatusBanner health={health} />
      <Hero health={health} />

      <main className="mx-auto grid w-full max-w-5xl flex-1 grid-cols-1 gap-6 px-6 py-10 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-4">
          <UploadDropzone onFilesSelected={handleFilesSelected} disabled={uploading} />
          <DocumentList
            documents={documents}
            loading={documentsLoading}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDelete={handleDelete}
            deletingId={deletingId}
          />
        </aside>

        <section className="space-y-6">
          {hasIndexedDocuments ? (
            <>
              <QuestionForm
                onSubmit={handleAsk}
                loading={queryLoading}
                disabled={!health?.llm_configured}
                scopeLabel={scopeLabel}
              />
              <AnswerPanel result={result} loading={queryLoading} />
            </>
          ) : (
            <EmptyState />
          )}
        </section>
      </main>

      <footer className="border-t border-slate-900 px-6 py-6 text-center text-xs text-slate-600">
        RAG Document QA &middot; Retrieval-Augmented Generation over your uploaded PDFs
      </footer>
    </div>
  );
}
