export type DocumentStatus = "processing" | "indexed" | "failed";

export interface DocumentRecord {
  id: string;
  filename: string;
  content_type: string;
  file_size_bytes: number;
  page_count: number;
  chunk_count: number;
  status: DocumentStatus;
  error_message: string | null;
  uploaded_at: string;
}

export interface DocumentListResponse {
  documents: DocumentRecord[];
  total: number;
}

export interface DocumentUploadResponse {
  document: DocumentRecord;
  message: string;
}

export interface RetrievedSource {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number | null;
  chunk_index: number;
  text: string;
  similarity_score: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  grounded: boolean;
  sources: RetrievedSource[];
  model: string;
  retrieved_chunk_count: number;
}

export interface HealthResponse {
  status: string;
  database: string;
  embedding_model: string;
  embedding_model_loaded: boolean;
  llm_provider: string;
  llm_model: string;
  llm_configured: boolean;
  llm_status: "ready" | "model_not_found" | "unreachable" | string;
  llm_message: string | null;
}

export interface ApiErrorBody {
  detail?: string;
}
