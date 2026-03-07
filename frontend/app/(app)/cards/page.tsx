import Link from "next/link";

import { CardArchiveButton } from "@/components/forms/card-archive-button";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { CardCreateForm } from "@/components/forms/card-create-form";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";
import { getSearchParam, type ResolvedSearchParams } from "@/lib/search-params";
import { formatCurrency, formatDecimal } from "@/lib/utils";

export default async function CardsPage({
  searchParams,
}: {
  searchParams: Promise<ResolvedSearchParams>;
}) {
  const resolved = await searchParams;
  const query = getSearchParam(resolved, "q")?.toLowerCase().trim() || "";
  const cards = await serverApi.cards.list();

  const filteredCards = cards.data.filter((card) => {
    if (!query) {
      return true;
    }
    return [card.nickname, card.issuer_name, card.last4].some((value) => value.toLowerCase().includes(query));
  });

  const cardSummaries = await Promise.all(
    filteredCards.map(async (card) => ({
      card,
      summary: (await serverApi.cards.summary(card.id)).data,
    })),
  );

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Cards"
        description="Manage your cards and review their current spend, reward, and charge posture."
      >
        <form className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
          <input className="app-input" name="q" placeholder="Search by nickname, issuer, or last four" defaultValue={query} />
          <button className="app-button" type="submit">
            Search
          </button>
        </form>
        <CardCreateForm />
      </TopFilterBar>

      {!cards.data.length ? (
        <EmptyState
          title="No cards yet"
          description="Add your first card to unlock dashboard, statements, and transaction analytics."
        />
      ) : !cardSummaries.length ? (
        <EmptyState
          title="No cards match this search"
          description="Adjust the current search term or clear it to see all cards."
          actionHref="/cards"
          actionLabel="Clear search"
        />
      ) : (
        <div className="grid gap-4">
          {cardSummaries.map(({ card, summary }) => (
            <article key={card.id} className="app-panel p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="font-display text-2xl font-semibold tracking-tight">{card.nickname}</h3>
                    <StatusPill status={card.status} />
                  </div>
                  <p className="mt-1 text-sm text-muted">
                    {card.issuer_name} •••• {card.last4} • {card.reward_type}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-muted">
                  Expected annual fee {formatCurrency(card.annual_fee_expected)}
                </div>
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-4">
                <div className="rounded-2xl border border-line bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">Spend</p>
                  <p className="mt-2 font-display text-2xl font-semibold">{formatCurrency(summary.total_spend)}</p>
                </div>
                <div className="rounded-2xl border border-line bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">Rewards</p>
                  <p className="mt-2 font-display text-2xl font-semibold">{formatDecimal(summary.reward_points, 0)} pts</p>
                </div>
                <div className="rounded-2xl border border-line bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">Charges</p>
                  <p className="mt-2 font-display text-2xl font-semibold">{formatCurrency(summary.charges)}</p>
                </div>
                <div className="rounded-2xl border border-line bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">Net Value</p>
                  <p className="mt-2 font-display text-2xl font-semibold">{formatCurrency(summary.net_value)}</p>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <Link className="app-button app-button-secondary" href={`/cards/${card.id}`}>
                  View
                </Link>
                <CardArchiveButton cardId={card.id} disabled={card.status === "archived"} />
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
