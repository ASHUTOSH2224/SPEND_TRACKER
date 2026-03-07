import { TopFilterBar } from "@/components/shared/top-filter-bar";
import { serverApi } from "@/lib/api/server";
import { getMockSettingsPreferences } from "@/lib/mocks/settings";

export default async function SettingsPage() {
  const user = await serverApi.auth.me();
  const preferences = getMockSettingsPreferences();

  return (
    <div className="grid gap-4">
      <TopFilterBar
        title="Settings"
        description="Authenticated user details plus temporary local-only frontend preferences."
      />

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="app-panel p-5">
          <h3 className="font-display text-lg font-semibold">Account</h3>
          <div className="mt-4 grid gap-3 text-sm">
            <div className="rounded-2xl border border-line bg-white/70 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.18em] text-muted">Full name</p>
              <p className="mt-2 font-medium">{user.data.full_name}</p>
            </div>
            <div className="rounded-2xl border border-line bg-white/70 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.18em] text-muted">Email</p>
              <p className="mt-2 font-medium">{user.data.email}</p>
            </div>
          </div>
        </div>

        <div className="app-panel p-5">
          <h3 className="font-display text-lg font-semibold">Frontend MVP adapter notes</h3>
          <p className="mt-1 text-sm text-muted">
            These preferences are temporary and intentionally isolated until backend settings APIs exist.
          </p>
          <div className="mt-4 grid gap-3">
            {preferences.map((preference) => (
              <div key={preference.id} className="rounded-2xl border border-line bg-white/70 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{preference.label}</p>
                  <p className="text-sm text-muted">{preference.value}</p>
                </div>
                <p className="mt-2 text-sm text-muted">{preference.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
