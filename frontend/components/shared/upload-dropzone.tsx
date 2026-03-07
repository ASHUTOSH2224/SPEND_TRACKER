"use client";

import { useRef, useState } from "react";

import { cn } from "@/lib/utils";

export function UploadDropzone({
  file,
  accept = ".pdf,.csv,.xls,.xlsx",
  onFileChange,
}: {
  file: File | null;
  accept?: string;
  onFileChange: (file: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const getFirstFile = (files: FileList | File[] | null | undefined) => {
    if (!files || files.length === 0) {
      return null;
    }
    return files[0] ?? null;
  };

  return (
    <div
      className={cn(
        "rounded-[1.25rem] border border-dashed border-line bg-white/70 p-6 text-center transition",
        dragActive && "border-accent bg-accent-soft/60",
      )}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragActive(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragActive(false);
        onFileChange(getFirstFile(event.dataTransfer.files));
      }}
    >
      <input
        ref={inputRef}
        className="hidden"
        type="file"
        accept={accept}
        onChange={(event) => onFileChange(getFirstFile(event.target.files))}
      />
      <p className="font-display text-lg font-semibold">Drag statement files here</p>
      <p className="mt-2 text-sm text-muted">PDF, CSV, XLS, and XLSX are accepted in the current MVP.</p>
      {file ? (
        <div className="mt-4 rounded-2xl border border-line bg-white px-4 py-3 text-left">
          <p className="font-medium">{file.name}</p>
          <p className="text-sm text-muted">{Math.max(1, Math.round(file.size / 1024))} KB selected</p>
        </div>
      ) : null}
      <button
        type="button"
        className="app-button mt-5"
        onClick={() => inputRef.current?.click()}
      >
        Choose file
      </button>
    </div>
  );
}
