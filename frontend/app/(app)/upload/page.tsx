import { UploadStatementForm } from "@/components/forms/upload-statement-form";
import { StatusPill } from "@/components/shared/status-pill";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";
import { formatDate } from "@/lib/utils";

export default async function UploadPage() {
  const [cards, statements] = await Promise.all([
    serverApi.cards.list(),
    serverApi.statements.list({ page: 1, page_size: 10 }),
  ]);

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Upload statements"
        description="Create statement upload metadata tied to a specific card and statement period."
      >
        <UploadStatementForm cards={cards.data} />
      </TopFilterBar>

      <section className="app-panel p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="font-display text-lg font-semibold">Recent uploads</h3>
            <p className="mt-1 text-sm text-muted">Most recent statement metadata rows across your cards.</p>
          </div>
        </div>

        <div className="mt-4 grid gap-3">
          {statements.data.map((statement) => {
            const card = cards.data.find((item) => item.id === statement.card_id);
            return (
              <div key={statement.id} className="flex flex-col gap-3 rounded-2xl border border-line bg-white/70 p-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-medium">{card?.nickname || "Unknown card"}</p>
                  <p className="mt-1 text-sm text-muted">
                    {statement.file_name} • {formatDate(statement.statement_period_start)} to {formatDate(statement.statement_period_end)}
                  </p>
                </div>
                <StatusPill status={statement.upload_status} />
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
