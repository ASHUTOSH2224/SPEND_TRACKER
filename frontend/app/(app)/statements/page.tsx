import { StatementActions } from "@/components/forms/statement-actions";
import { EmptyState } from "@/components/shared/empty-state";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { StatusPill } from "@/components/shared/status-pill";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";
import { getSearchParam, type ResolvedSearchParams } from "@/lib/search-params";
import { formatDate } from "@/lib/utils";

export default async function StatementsPage({
  searchParams,
}: {
  searchParams: Promise<ResolvedSearchParams>;
}) {
  const resolved = await searchParams;
  const filters = {
    card_id: getSearchParam(resolved, "card_id"),
    status: getSearchParam(resolved, "status"),
    month: getSearchParam(resolved, "month"),
    page: Number(getSearchParam(resolved, "page") || 1),
    page_size: 20,
  };

  const [statements, cards] = await Promise.all([
    serverApi.statements.list(filters),
    serverApi.cards.list(),
  ]);
  const page = Number(statements.meta.page || 1);
  const totalPages = Number(statements.meta.total_pages || 1);

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Statements"
        description="Audit uploaded files and retry or delete upload metadata when needed."
      >
        <form className="grid gap-3 md:grid-cols-[220px_220px_180px_auto]">
          <select className="app-select" name="card_id" defaultValue={filters.card_id || ""}>
            <option value="">All cards</option>
            {cards.data.map((card) => (
              <option key={card.id} value={card.id}>
                {card.nickname}
              </option>
            ))}
          </select>
          <select className="app-select" name="status" defaultValue={filters.status || ""}>
            <option value="">All statuses</option>
            <option value="uploaded">Uploaded</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <input className="app-input" name="month" placeholder="YYYY-MM" defaultValue={filters.month} />
          <button className="app-button" type="submit">
            Apply filters
          </button>
        </form>
      </TopFilterBar>

      {statements.data.length ? (
        <>
          <div className="text-sm text-muted">
            Showing {statements.data.length} statements on page {page} of {totalPages}
          </div>
          <div className="app-panel overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead className="border-b border-line bg-white/60 text-left text-xs uppercase tracking-[0.18em] text-muted">
                  <tr>
                    <th className="px-4 py-3">Card</th>
                    <th className="px-4 py-3">Period</th>
                    <th className="px-4 py-3">File</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Transactions</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {statements.data.map((statement) => {
                    const card = cards.data.find((item) => item.id === statement.card_id);
                    return (
                      <tr key={statement.id} className="border-b border-line/70 last:border-b-0">
                        <td className="px-4 py-4 align-top">{card?.nickname || "Unknown card"}</td>
                        <td className="px-4 py-4 align-top">
                          {formatDate(statement.statement_period_start)} to {formatDate(statement.statement_period_end)}
                        </td>
                        <td className="px-4 py-4 align-top">
                          <p>{statement.file_name}</p>
                          {statement.processing_error ? (
                            <p className="mt-1 text-xs text-danger">{statement.processing_error}</p>
                          ) : null}
                        </td>
                        <td className="px-4 py-4 align-top">
                          <div className="grid gap-2">
                            <StatusPill status={statement.upload_status} />
                            <div className="flex flex-wrap gap-2">
                              <StatusPill status={statement.extraction_status} />
                              <StatusPill status={statement.categorization_status} />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 align-top">{statement.transaction_count}</td>
                        <td className="px-4 py-4 align-top">
                          <StatementActions statementId={statement.id} uploadStatus={statement.upload_status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <PaginationControls pathname="/statements" searchParams={resolved} page={page} totalPages={totalPages} />
        </>
      ) : (
        <EmptyState
          title="No statements found"
          description="Upload history will appear here after you create your first statement metadata row."
          actionHref="/upload"
          actionLabel="Upload statement"
        />
      )}
    </div>
  );
}
