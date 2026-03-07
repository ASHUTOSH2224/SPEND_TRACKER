import Link from "next/link";

import { ChartCard } from "@/components/shared/chart-card";
import { KpiCard } from "@/components/shared/kpi-card";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";
import { getSearchParam, type ResolvedSearchParams } from "@/lib/search-params";
import { formatCurrency, formatMonthLabel, formatPercent, toBarWidth, toNumber } from "@/lib/utils";

function BarList({
  items,
  valueKey,
  labelKey,
}: {
  items: Array<Record<string, string | number | null>>;
  valueKey: string;
  labelKey: string;
}) {
  const maxValue = Math.max(0, ...items.map((item) => toNumber(item[valueKey] as number | string | null)));

  return (
    <div className="grid gap-3">
      {items.map((item, index) => (
        <div key={`${String(item[labelKey])}-${index}`} className="grid gap-2">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate font-medium">{String(item[labelKey])}</span>
            <span className="text-muted">{formatCurrency(item[valueKey] as number | string | null)}</span>
          </div>
          <div className="h-2 rounded-full bg-[#eadfce]">
            <div
              className="h-full rounded-full bg-accent"
              style={{ width: toBarWidth(item[valueKey] as number | string | null, maxValue) }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<ResolvedSearchParams>;
}) {
  const resolved = await searchParams;
  const filters = {
    from_date: getSearchParam(resolved, "from_date"),
    to_date: getSearchParam(resolved, "to_date"),
    card_id: getSearchParam(resolved, "card_id"),
    category_id: getSearchParam(resolved, "category_id"),
  };

  const [
    summary,
    spendByCategory,
    spendByCard,
    rewardsVsCharges,
    monthlyTrend,
    topMerchants,
    cards,
    categories,
  ] = await Promise.all([
    serverApi.dashboard.summary(filters),
    serverApi.dashboard.spendByCategory(filters),
    serverApi.dashboard.spendByCard(filters),
    serverApi.dashboard.rewardsVsCharges(filters),
    serverApi.dashboard.monthlyTrend(filters),
    serverApi.dashboard.topMerchants(filters),
    serverApi.cards.list(),
    serverApi.categories.list(),
  ]);

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Dashboard"
        description="Monthly spend, reward, and charge visibility across your cards."
      >
        <form className="grid gap-3 md:grid-cols-[180px_180px_220px_220px_auto]">
          <input className="app-input" name="from_date" type="date" defaultValue={filters.from_date} />
          <input className="app-input" name="to_date" type="date" defaultValue={filters.to_date} />
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
          <button className="app-button" type="submit">
            Apply filters
          </button>
        </form>
      </TopFilterBar>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total Spend" value={formatCurrency(summary.data.total_spend)} helper={`Previous period ${formatCurrency(summary.data.previous_period_spend)}`} />
        <KpiCard label="Rewards Value" value={formatCurrency(summary.data.total_rewards_value)} helper={`MoM change ${formatPercent(summary.data.spend_change_pct)}`} tone="accent" />
        <KpiCard label="Charges Paid" value={formatCurrency(summary.data.total_charges)} helper={`${summary.data.transaction_count} tracked transactions`} />
        <KpiCard label="Net Card Value" value={formatCurrency(summary.data.net_card_value)} helper={`${summary.data.needs_review_count} transactions need review`} tone={toNumber(summary.data.net_card_value) < 0 ? "danger" : "accent"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Spend by Category" subtitle="Duplicate transactions are excluded from financial summaries.">
          <BarList
            items={spendByCategory.data.map((item) => ({
              category_name: item.category_name,
              amount: item.amount,
            }))}
            labelKey="category_name"
            valueKey="amount"
          />
        </ChartCard>

        <ChartCard title="Spend by Card" subtitle={summary.data.top_card ? `Top card: ${summary.data.top_card.name}` : "No spend in range"}>
          <BarList
            items={spendByCard.data.map((item) => ({
              card_name: item.card_name,
              amount: item.amount,
            }))}
            labelKey="card_name"
            valueKey="amount"
          />
        </ChartCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Rewards vs Charges" subtitle="Net value = reward value minus charges.">
          <div className="grid gap-3">
            {rewardsVsCharges.data.map((item) => (
              <div key={item.card_id} className="rounded-2xl border border-line bg-white/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{item.card_name}</p>
                  <p className="text-sm text-muted">{formatCurrency(item.net_value)} net</p>
                </div>
                <div className="mt-3 grid gap-2 text-sm text-muted md:grid-cols-3">
                  <span>Spend {formatCurrency(item.total_spend)}</span>
                  <span>Rewards {formatCurrency(item.reward_value)}</span>
                  <span>Charges {formatCurrency(item.charges)}</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Monthly Trend" subtitle="Persisted transactions and reward ledger events only.">
          <div className="grid gap-3">
            {monthlyTrend.data.map((item) => (
              <div key={item.month} className="rounded-2xl border border-line bg-white/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{formatMonthLabel(item.month)}</p>
                  <p className="text-sm text-muted">{formatCurrency(item.net_value)} net</p>
                </div>
                <div className="mt-3 grid gap-2 text-sm text-muted md:grid-cols-3">
                  <span>Spend {formatCurrency(item.total_spend)}</span>
                  <span>Rewards {formatCurrency(item.reward_value)}</span>
                  <span>Charges {formatCurrency(item.charges)}</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <ChartCard title="Top Merchants" subtitle="Based on non-charge spend only.">
          <div className="grid gap-3">
            {topMerchants.data.map((merchant) => (
              <div key={merchant.merchant_name} className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
                <div>
                  <p className="font-medium">{merchant.merchant_name}</p>
                  <p className="text-sm text-muted">{merchant.transaction_count} transactions</p>
                </div>
                <p className="font-medium">{formatCurrency(merchant.amount)}</p>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Needs Review" subtitle="Jump into the transactions explorer to clear manual review items.">
          <div className="flex h-full flex-col justify-between gap-4 rounded-[1.25rem] border border-line bg-white/70 p-5">
            <div>
              <p className="font-display text-5xl font-semibold tracking-tight">{summary.data.needs_review_count}</p>
              <p className="mt-2 text-sm text-muted">
                Low-confidence or manually flagged transactions in the current result set.
              </p>
            </div>
            <Link href="/transactions?review_required=true" className="app-button w-fit">
              Review now
            </Link>
          </div>
        </ChartCard>
      </div>
    </div>
  );
}
