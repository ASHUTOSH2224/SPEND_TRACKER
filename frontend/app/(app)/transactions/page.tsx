import { PaginationControls } from "@/components/shared/pagination-controls";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { TransactionTable } from "@/components/shared/transaction-table";
import { serverApi } from "@/lib/api/server";
import { getBooleanSearchParam, getSearchParam, type ResolvedSearchParams } from "@/lib/search-params";

export default async function TransactionsPage({
  searchParams,
}: {
  searchParams: Promise<ResolvedSearchParams>;
}) {
  const resolved = await searchParams;
  const filters = {
    search: getSearchParam(resolved, "search"),
    card_id: getSearchParam(resolved, "card_id"),
    category_id: getSearchParam(resolved, "category_id"),
    from_date: getSearchParam(resolved, "from_date"),
    to_date: getSearchParam(resolved, "to_date"),
    review_required: getBooleanSearchParam(resolved, "review_required"),
    is_card_charge: getBooleanSearchParam(resolved, "is_card_charge"),
    page: Number(getSearchParam(resolved, "page") || 1),
    page_size: Number(getSearchParam(resolved, "page_size") || 25),
    sort_by: getSearchParam(resolved, "sort_by") || "txn_date",
    sort_order: getSearchParam(resolved, "sort_order") || "desc",
  };

  const [transactions, categories, cards] = await Promise.all([
    serverApi.transactions.list(filters),
    serverApi.categories.list(),
    serverApi.cards.list(),
  ]);

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Transactions"
        description="Search, filter, and manually correct categorized transactions."
      >
        <form className="grid gap-3 md:grid-cols-6">
          <input className="app-input md:col-span-2" name="search" placeholder="Merchant or description" defaultValue={filters.search} />
          <select className="app-select" name="card_id" defaultValue={filters.card_id || ""}>
            <option value="">All cards</option>
            {cards.data.map((card) => (
              <option key={card.id} value={card.id}>
                {card.nickname}
              </option>
            ))}
          </select>
          <select className="app-select" name="category_id" defaultValue={filters.category_id || ""}>
            <option value="">All categories</option>
            {categories.data.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <input className="app-input" name="from_date" type="date" defaultValue={filters.from_date} />
          <input className="app-input" name="to_date" type="date" defaultValue={filters.to_date} />
          <select className="app-select" name="sort_by" defaultValue={filters.sort_by}>
            <option value="txn_date">Transaction date</option>
            <option value="posted_date">Posted date</option>
            <option value="amount">Amount</option>
            <option value="created_at">Created at</option>
            <option value="updated_at">Updated at</option>
          </select>
          <select className="app-select" name="sort_order" defaultValue={filters.sort_order}>
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
          <select className="app-select" name="page_size" defaultValue={String(filters.page_size)}>
            <option value="25">25 rows</option>
            <option value="50">50 rows</option>
            <option value="100">100 rows</option>
          </select>
          <label className="flex items-center gap-2 rounded-2xl border border-line bg-white/70 px-4 py-3 text-sm">
            <input name="review_required" type="checkbox" value="true" defaultChecked={Boolean(filters.review_required)} />
            Needs review
          </label>
          <label className="flex items-center gap-2 rounded-2xl border border-line bg-white/70 px-4 py-3 text-sm">
            <input name="is_card_charge" type="checkbox" value="true" defaultChecked={Boolean(filters.is_card_charge)} />
            Charges only
          </label>
          <button className="app-button" type="submit">
            Apply filters
          </button>
        </form>
      </TopFilterBar>

      <div className="flex items-center justify-between gap-3 text-sm text-muted">
        <p>
          Showing {transactions.data.length} transactions on page {transactions.meta.page as number} of{" "}
          {transactions.meta.total_pages as number}
        </p>
        <p>{transactions.meta.total as number} total rows</p>
      </div>

      <TransactionTable transactions={transactions.data} categories={categories.data} />
      <PaginationControls
        pathname="/transactions"
        searchParams={resolved}
        page={Number(transactions.meta.page || 1)}
        totalPages={Number(transactions.meta.total_pages || 1)}
      />
    </div>
  );
}
