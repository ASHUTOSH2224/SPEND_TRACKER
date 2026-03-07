import { CategoryCreateForm } from "@/components/forms/category-create-form";
import { RuleCreateForm } from "@/components/forms/rule-create-form";
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
          <div className="mt-4 grid gap-3">
            {categories.data.map((category) => (
              <div key={category.id} className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/70 px-4 py-3">
                <div>
                  <p className="font-medium">{category.name}</p>
                  <p className="text-sm text-muted">{category.group_name}</p>
                </div>
                <StatusPill status={category.is_archived ? "archived" : category.is_default ? "completed" : "active"} />
              </div>
            ))}
          </div>
        </div>

        <div className="app-panel p-5">
          <h3 className="font-display text-lg font-semibold">Rules</h3>
          <p className="mt-1 text-sm text-muted">Rule create is wired to the backend; edit and disable flows can follow next.</p>
          <div className="mt-4">
            <RuleCreateForm categories={categories.data} />
          </div>
          <div className="mt-4 grid gap-3">
            {rules.data.map((rule) => (
              <div key={rule.id} className="rounded-2xl border border-line bg-white/70 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{rule.rule_name}</p>
                  <StatusPill status={rule.is_active ? "active" : "archived"} />
                </div>
                <p className="mt-2 text-sm text-muted">
                  {rule.match_type} • {rule.match_value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
