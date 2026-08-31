import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QuestionForm } from "../QuestionForm";

describe("QuestionForm", () => {
  it("disables the submit button when the question is empty", () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={false} disabled={false} scopeLabel="all" />);
    expect(screen.getByRole("button", { name: /ask question/i })).toBeDisabled();
  });

  it("calls onSubmit with the trimmed question on submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<QuestionForm onSubmit={onSubmit} loading={false} disabled={false} scopeLabel="all" />);

    const textarea = screen.getByLabelText(/ask a question/i);
    await user.type(textarea, "  What is RAG?  ");
    await user.click(screen.getByRole("button", { name: /ask question/i }));

    expect(onSubmit).toHaveBeenCalledWith("What is RAG?");
  });

  it("submits on Enter but inserts a newline on Shift+Enter", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<QuestionForm onSubmit={onSubmit} loading={false} disabled={false} scopeLabel="all" />);

    const textarea = screen.getByLabelText(/ask a question/i);
    await user.type(textarea, "Question one{Shift>}{Enter}{/Shift}Question two{Enter}");

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith("Question one\nQuestion two");
  });

  it("disables the textarea and button when disabled prop is true", () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={false} disabled scopeLabel="all" />);
    expect(screen.getByLabelText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /ask question/i })).toBeDisabled();
  });
});
