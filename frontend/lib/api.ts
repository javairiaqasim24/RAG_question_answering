import type {
  ApiErrorBody,
  DocumentListResponse,
  DocumentUploadResponse,
  HealthResponse,
  QueryResponse,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body: ApiErrorBody = await res.json();
      if (body.detail) message = body.detail;
    } catch {
      // response had no JSON body; keep the generic message
    }
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  return handleResponse<HealthResponse>(res);
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${API_BASE_URL}/documents`, { cache: "no-store" });
  return handleResponse<DocumentListResponse>(res);
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentUploadResponse>(res);
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, { method: "DELETE" });
  return handleResponse<void>(res);
}

export async function askQuestion(
  question: string,
  options?: { documentId?: string; topK?: number }
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      document_id: options?.documentId ?? null,
      top_k: options?.topK ?? null,
    }),
  });
  return handleResponse<QueryResponse>(res);
}

export { API_BASE_URL };
