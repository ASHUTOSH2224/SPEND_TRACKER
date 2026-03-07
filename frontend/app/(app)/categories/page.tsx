import { CategoryArchiveButton } from "@/components/forms/category-archive-button";
import { CategoryCreateForm } from "@/components/forms/category-create-form";
import { RuleDisableButton } from "@/components/forms/rule-disable-button";
import { RuleCreateForm } from "@/components/forms/rule-create-form";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";

export default async function CategoriesPage() {
  const [categories, rules] = await Promise.all([
    serverApi.categories.list(),
    serverApi.rules.list(),
  ]);

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Categories"
        description="Manage your taxonomy and create reusable deterministic rules."
      >
        <CategoryCreateForm />
      </TopFilterBar>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="app-panel p-5">
          <h3 className="font-display text-lg font-semibold">Categories</h3>
          {categories.data.length ? (
            <div className="mt-4 grid gap-3">
              {categories.data.map((category) => (
                <div key={category.id} className="flex flex-col gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-medium">{category.name}</p>
                    <p className="text-sm text-muted">{category.group_name}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <StatusPill status={category.is_archived ? "archived" : category.is_default ? "completed" : "active"} />
                    {!category.is_default ? (
                      <CategoryArchiveButton categoryId={category.id} disabled={category.is_archived} />
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No categories yet"
                description="Create your first custom category to organize transactions."
                compact
              />
            </div>
          )}
        </div>

        <div className="app-panel p-5">
          <h3 className="font-display text-lg font-semibold">Rules</h3>
          <p className="mt-1 text-sm text-muted">Rules are matched deterministically before any future AI fallback.</p>
          <div className="mt-4">
            <RuleCreateForm categories={categories.data} />
          </div>
          {rules.data.length ? (
            <div className="mt-4 grid gap-3">
              {rules.data.map((rule) => (
                <div key={rule.id} className="rounded-2xl border border-line bg-white/70 px-4 py-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-medium">{rule.rule_name}</p>
                      <p className="mt-2 text-sm text-muted">
                        {rule.match_type} • {rule.match_value}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusPill status={rule.is_active ? "active" : "archived"} />
                      <RuleDisableButton ruleId={rule.id} disabled={!rule.is_active} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState
                title="No rules yet"
                description="Create reusable rules for merchant or description matches."
                compact
              />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
