import Link from "next/link";
import { notFound } from "next/navigation";

import { CardArchiveButton } from "@/components/forms/card-archive-button";
import { RewardLedgerManager } from "@/components/forms/reward-ledger-manager";
import { ChartCard } from "@/components/shared/chart-card";
import { EmptyState } from "@/components/shared/empty-state";
import { KpiCard } from "@/components/shared/kpi-card";
import { StatusPill } from "@/components/shared/status-pill";
import { ApiClientError } from "@/lib/api/http";
import { serverApi } from "@/lib/api/server";
import { formatCurrency, formatDate, formatDecimal, formatMonthLabel, toNumber } from "@/lib/utils";

function TrendRows({
  rows,
  valueKey,
  label,
}: {
  rows: Array<{ month: string; total_spend: number | string; reward_value: number | string }>;
  valueKey: "total_spend" | "reward_value";
  label: string;
}) {
  if (!rows.length) {
    return (
      <EmptyState
        title={`No ${label.toLowerCase()} trend yet`}
        description="This trend appears after at least one statement month has persisted activity."
        compact
      />
    );
  }

  return (
    <div className="grid gap-3">
      {rows.map((row) => (
        <div key={`${valueKey}-${row.month}`} className="rounded-2xl border border-line bg-white/70 px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <p className="font-medium">{formatMonthLabel(row.month)}</p>
            <p className="text-sm text-muted">{formatCurrency(row[valueKey])}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function CardDetailPage({
  params,
}: {
  params: Promise<{ cardId: string }>;
}) {
  const { cardId } = await params;

  let card;
  try {
    card = await serverApi.cards.get(cardId);
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  const [summary, rewards, charges, monthlyTrend, recentTransactions, rewardEvents] = await Promise.all([
    serverApi.cards.summary(cardId),
    serverApi.cards.rewards(cardId),
    serverApi.cards.charges(cardId),
    serverApi.cards.monthlyTrend(cardId),
    serverApi.cards.transactions(cardId, { page: 1, page_size: 6, sort_by: "txn_date", sort_order: "desc" }),
    serverApi.rewardLedgers.list({ card_id: cardId }),
  ]);

  const groupedOtherCharges =
    toNumber(charges.data.late_fee_amount) +
    toNumber(charges.data.emi_processing_fee_amount) +
    toNumber(charges.data.cash_advance_fee_amount) +
    toNumber(charges.data.forex_markup_amount) +
    toNumber(charges.data.tax_amount) +
    toNumber(charges.data.other_charge_amount);

  return (
    <div className="grid gap-4">
      <section className="app-panel p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="font-display text-3xl font-semibold tracking-tight">{card.data.nickname}</h2>
              <StatusPill status={card.data.status} />
            </div>
            <p className="mt-2 text-sm text-muted">
              Last 4: {card.data.last4} | Issuer: {card.data.issuer_name} | Reward type: {card.data.reward_type} | Annual fee:{" "}
              {formatCurrency(card.data.annual_fee_expected)}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className="app-button app-button-secondary" href={`/transactions?card_id=${card.data.id}`}>
              View all transactions
            </Link>
            <CardArchiveButton cardId={card.data.id} disabled={card.data.status === "archived"} />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <KpiCard label="Total Spend" value={formatCurrency(summary.data.total_spend)} />
        <KpiCard label="Eligible Spend" value={formatCurrency(summary.data.eligible_spend)} />
        <KpiCard
          label="Reward Points"
          value={`${formatDecimal(summary.data.reward_points, 0)} pts`}
          helper={`Balance ${formatDecimal(rewards.data.current_balance, 0)} pts`}
          tone="accent"
        />
        <KpiCard label="Reward Value" value={formatCurrency(summary.data.reward_value)} />
        <KpiCard label="Charges" value={formatCurrency(summary.data.charges)} tone={toNumber(summary.data.charges) > 0 ? "danger" : "default"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Monthly Spend Trend" subtitle="Persisted spend for this card across imported months.">
          <TrendRows rows={monthlyTrend.data} valueKey="total_spend" label="Spend" />
        </ChartCard>

        <ChartCard title="Rewards Trend" subtitle="Monthly reward value derived from persisted reward data.">
          <TrendRows rows={monthlyTrend.data} valueKey="reward_value" label="Rewards" />
        </ChartCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <ChartCard title="Charges Breakdown" subtitle={`Source: ${charges.data.source}`}>
          <div className="grid gap-3">
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
              <span>Annual Fee</span>
              <span className="font-medium">{formatCurrency(charges.data.annual_fee_amount)}</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
              <span>Joining Fee</span>
              <span className="font-medium">{formatCurrency(charges.data.joining_fee_amount)}</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
              <span>Finance Charges</span>
              <span className="font-medium">{formatCurrency(charges.data.finance_charge_amount)}</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
              <span>Other Charges</span>
              <span className="font-medium">{formatCurrency(groupedOtherCharges)}</span>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Recent Transactions" subtitle={`${Number(recentTransactions.meta.total || 0)} total transactions on this card`}>
          {recentTransactions.data.length ? (
            <div className="grid gap-3">
              {recentTransactions.data.map((transaction) => (
                <div key={transaction.id} className="grid gap-2 rounded-2xl border border-line bg-white/70 px-4 py-3 md:grid-cols-[110px_minmax(0,1fr)_auto] md:items-center">
                  <p className="text-sm text-muted">{formatDate(transaction.txn_date)}</p>
                  <div className="min-w-0">
                    <p className="truncate font-medium">{transaction.normalized_merchant}</p>
                    <p className="truncate text-sm text-muted">
                      {transaction.category?.name || "Unassigned"} {transaction.is_card_charge ? "• Charge" : ""}
                    </p>
                  </div>
                  <p className="font-medium">{formatCurrency(transaction.amount)}</p>
                </div>
              ))}
              <Link className="app-button app-button-secondary w-fit" href={`/transactions?card_id=${card.data.id}`}>
                View all
              </Link>
            </div>
          ) : (
            <EmptyState
              title="No recent transactions"
              description="Transactions for this card will appear once a statement is imported."
              compact
            />
          )}
        </ChartCard>
      </div>

      <ChartCard title="Reward Events" subtitle="Manual and imported reward ledger rows for this card.">
        <RewardLedgerManager cardId={card.data.id} rewardEvents={rewardEvents.data} />
      </ChartCard>
    </div>
  );
}
