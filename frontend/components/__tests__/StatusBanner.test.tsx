import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBanner } from "../StatusBanner";
import type { HealthResponse } from "@/types";

const baseHealth: HealthResponse = {
  status: "ok",
  database: "ok",
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2",
  embedding_model_loaded: true,
  llm_provider: "ollama",
  llm_model: "gemma3:4b",
  llm_configured: true,
  llm_status: "ready",
  llm_message: null,
};

describe("StatusBanner", () => {
  it("shows an unreachable message when health is null", () => {
    render(<StatusBanner health={null} />);
    expect(screen.getByText(/backend is unreachable/i)).toBeInTheDocument();
  });

  it("warns when the local AI service is unavailable", () => {
    render(
      <StatusBanner
        health={{
          ...baseHealth,
          llm_configured: false,
          llm_status: "unreachable",
          llm_message: "Ollama is not reachable at http://localhost:11434.",
        }}
      />
    );
    expect(screen.getByText(/ollama is not reachable/i)).toBeInTheDocument();
  });

  it("warns when the configured model is not installed", () => {
    render(
      <StatusBanner
        health={{
          ...baseHealth,
          llm_configured: false,
          llm_status: "model_not_found",
          llm_message: null,
        }}
      />
    );
    expect(screen.getByText(/not installed/i)).toBeInTheDocument();
  });

  it("warns when the database is unavailable", () => {
    render(<StatusBanner health={{ ...baseHealth, database: "unavailable" }} />);
    expect(screen.getByText(/vector database is unavailable/i)).toBeInTheDocument();
  });

  it("renders nothing when everything is healthy", () => {
    const { container } = render(<StatusBanner health={baseHealth} />);
    expect(container).toBeEmptyDOMElement();
  });
});
