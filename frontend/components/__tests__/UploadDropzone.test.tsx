import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { UploadDropzone } from "../UploadDropzone";

function makeFile(name: string, type = "application/pdf") {
  return new File(["%PDF-1.4 test"], name, { type });
}

describe("UploadDropzone", () => {
  it("calls onFilesSelected when a file is chosen via the input", async () => {
    const user = userEvent.setup();
    const onFilesSelected = vi.fn();
    render(<UploadDropzone onFilesSelected={onFilesSelected} />);

    const input = screen.getByLabelText(/upload pdf documents/i).querySelector("input")!;
    const file = makeFile("report.pdf");
    await user.upload(input, file);

    expect(onFilesSelected).toHaveBeenCalledTimes(1);
    expect(onFilesSelected.mock.calls[0][0]).toEqual([file]);
  });

  it("is not interactive when disabled", () => {
    render(<UploadDropzone onFilesSelected={vi.fn()} disabled />);
    const dropzone = screen.getByLabelText(/upload pdf documents/i);
    expect(dropzone).toHaveAttribute("aria-disabled", "true");
    expect(dropzone).toHaveAttribute("tabIndex", "-1");
  });
});
