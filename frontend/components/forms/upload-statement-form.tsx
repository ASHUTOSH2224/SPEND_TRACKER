"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import type { CardRead } from "@/lib/api/types";
import { browserApi } from "@/lib/api/browser";
import { uploadBinary } from "@/lib/api/http";
import { UploadDropzone } from "@/components/shared/upload-dropzone";
import { inferContentType, inferStatementFileType } from "@/lib/utils";

export function UploadStatementForm({ cards }: { cards: CardRead[] }) {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  return (
    <form
      className="grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const formData = new FormData(event.currentTarget);
        const cardId = String(formData.get("card_id") || "");
        const statementPeriodStart = String(formData.get("statement_period_start") || "");
        const statementPeriodEnd = String(formData.get("statement_period_end") || "");

        if (!selectedFile || !cardId || !statementPeriodStart || !statementPeriodEnd) {
          setMessage("Select a card, a file, and a statement period.");
          return;
        }

        setPending(true);
        setMessage(null);

        startTransition(async () => {
          try {
            const contentType = inferContentType(selectedFile.name);
            const presign = await browserApi.uploads.presign({
              file_name: selectedFile.name,
              content_type: contentType,
            });

            await uploadBinary(presign.data.upload_url, selectedFile, {
              contentType,
            });

            await browserApi.statements.create({
              card_id: cardId,
              file_name: selectedFile.name,
              file_storage_key: presign.data.file_storage_key,
              file_type: inferStatementFileType(selectedFile.name),
              statement_period_start: statementPeriodStart,
              statement_period_end: statementPeriodEnd,
            });

            setSelectedFile(null);
            form.reset();
            setMessage("Statement uploaded and queued successfully.");
            router.refresh();
          } catch (submissionError) {
            setMessage(submissionError instanceof Error ? submissionError.message : "Upload failed");
          } finally {
            setPending(false);
          }
        });
      }}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <label className="grid gap-2">
          <span className="text-sm font-medium">Card</span>
          <select className="app-select" name="card_id" defaultValue="" required>
            <option value="" disabled>
              Select card
            </option>
            {cards.map((card) => (
              <option key={card.id} value={card.id}>
                {card.nickname} •••• {card.last4}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium">Statement period start</span>
          <input className="app-input" name="statement_period_start" type="date" required />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium">Statement period end</span>
          <input className="app-input" name="statement_period_end" type="date" required />
        </label>
      </div>

      <UploadDropzone file={selectedFile} onFileChange={setSelectedFile} />

      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-muted">
          Local development storage writes the uploaded file before creating statement metadata.
        </p>
        <button className="app-button" type="submit" disabled={pending}>
          {pending ? "Uploading..." : "Upload statement"}
        </button>
      </div>

      {message ? <p className="text-sm text-muted">{message}</p> : null}
    </form>
  );
}
