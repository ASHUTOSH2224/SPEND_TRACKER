import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { UploadDropzone } from "@/components/shared/upload-dropzone";

describe("UploadDropzone", () => {
  it("surfaces the selected file details", () => {
    const handleFileChange = vi.fn();
    const file = new File(["statement"], "march.pdf", { type: "application/pdf" });

    const { container } = render(<UploadDropzone file={null} onFileChange={handleFileChange} />);
    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();

    fireEvent.change(input as HTMLInputElement, {
      target: {
        files: [file],
      },
    });

    expect(handleFileChange).toHaveBeenCalledWith(file);
  });

  it("renders the current file summary when a file is already selected", () => {
    const file = new File(["statement"], "april.pdf", { type: "application/pdf" });
    render(<UploadDropzone file={file} onFileChange={vi.fn()} />);

    expect(screen.getByText("april.pdf")).toBeInTheDocument();
  });
});
